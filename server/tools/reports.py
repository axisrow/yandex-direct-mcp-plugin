"""MCP tools for Yandex.Direct statistics reports.

Two report tools are exposed:
- ``reports_get`` — fixed-shape "quick snapshot" (last 8 days per-campaign).
- ``reports_custom`` — full Reports API surface: arbitrary FieldNames,
  filters, ordering, pagination, file output.

Both wrap ``direct reports get`` from direct-cli but expose different
parameter sets to the LLM so the right tool is picked unambiguously.
"""

import os
import tempfile
import time
from datetime import date, timedelta
from pathlib import Path

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import tool_error_dict

DEFAULT_REPORT_TYPE = "CAMPAIGN_PERFORMANCE_REPORT"
DEFAULT_REPORT_NAME = "mcp_campaign_performance"
DEFAULT_REPORT_FIELDS = (
    "CampaignName,Impressions,Clicks,Cost,Conversions,CostPerConversion,ConversionRate"
)
DEFAULT_WINDOW_DAYS = 8

CUSTOM_REPORT_TIMEOUT_SECONDS = 120

VALID_RESPONSE_FORMATS = frozenset({"json", "tsv", "csv", "table"})

VALID_PROCESSING_MODES = frozenset({"auto", "online", "offline"})
VALID_REPORT_LANGUAGES = frozenset({"ru", "en"})
VALID_ATTRIBUTION_MODELS = frozenset(
    {"FC", "LC", "LSC", "LYDC", "FCCD", "LSCCD", "LYDCCD", "AUTO"}
)

VALID_REPORT_TYPES = frozenset(
    {
        "ACCOUNT_PERFORMANCE_REPORT",
        "CAMPAIGN_PERFORMANCE_REPORT",
        "ADGROUP_PERFORMANCE_REPORT",
        "AD_PERFORMANCE_REPORT",
        "CRITERIA_PERFORMANCE_REPORT",
        "CUSTOM_REPORT",
        "REACH_AND_FREQUENCY_PERFORMANCE_REPORT",
        "SEARCH_QUERY_PERFORMANCE_REPORT",
    }
)

VALID_DATE_RANGE_TYPES = frozenset(
    {
        "TODAY",
        "YESTERDAY",
        "CUSTOM_DATE",
        "ALL_TIME",
        "LAST_30_DAYS",
        "LAST_14_DAYS",
        "LAST_7_DAYS",
        "THIS_WEEK_MON_TODAY",
        "THIS_WEEK_MON_SUN",
        "LAST_WEEK",
        "LAST_BUSINESS_WEEK",
        "LAST_3_MONTHS",
        "LAST_5_YEARS",
        "AUTO",
    }
)


def _is_goals_filter(filter_expr: str) -> bool:
    """Return whether a raw report filter targets the API's Goals field."""
    return filter_expr.lstrip().lower().startswith("goals:")


def _invalid_date_format(field_name: str, value: str) -> ToolError:
    return ToolError(
        error="invalid_date_format",
        message=f"{field_name} must use YYYY-MM-DD format; got {value!r}.",
    )


def _parse_report_date(field_name: str, value: str) -> date | ToolError:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return _invalid_date_format(field_name, value)


def _resolve_report_dates(
    date_from: str | None, date_to: str | None
) -> tuple[str, str] | ToolError:
    """Resolve the reporting window to match Direct's default day range."""
    if date_from and date_to:
        parsed_from = _parse_report_date("date_from", date_from)
        if isinstance(parsed_from, ToolError):
            return parsed_from
        parsed_to = _parse_report_date("date_to", date_to)
        if isinstance(parsed_to, ToolError):
            return parsed_to
        return date_from, date_to

    if date_to:
        resolved_to = _parse_report_date("date_to", date_to)
        if isinstance(resolved_to, ToolError):
            return resolved_to
        resolved_from = resolved_to - timedelta(days=DEFAULT_WINDOW_DAYS)
        return resolved_from.isoformat(), date_to

    if date_from:
        parsed_from = _parse_report_date("date_from", date_from)
        if isinstance(parsed_from, ToolError):
            return parsed_from
        resolved_to = parsed_from + timedelta(days=DEFAULT_WINDOW_DAYS)
        return date_from, resolved_to.isoformat()

    today = date.today()
    return (today - timedelta(days=DEFAULT_WINDOW_DAYS)).isoformat(), today.isoformat()


@mcp.tool(
    name="reports_get",
    description="Quick per-campaign performance snapshot over a short recent window (~last 8 days, default fields). Use reports_get for a fast overview; use reports_custom for arbitrary fields, filters, or date/goal breakdowns. Call tool_help('reports_get') for parameters.",
)
@handle_cli_errors
def reports_get(
    date_from: str | None = None, date_to: str | None = None
) -> list[dict] | dict:
    """Quick campaign performance snapshot (last 8 days by default).

    Returns aggregated stats per campaign with the default field set:
    CampaignName, Impressions, Clicks, Cost, Conversions, CostPerConversion,
    ConversionRate. Underlying report is CAMPAIGN_PERFORMANCE_REPORT.

    USE THIS WHEN: the user just wants a quick overview "how are my campaigns
    doing" over a short recent window — no grouping, no filtering.

    USE `reports_custom` INSTEAD WHEN any of these apply:
    - group by month / week / date / quarter / year (timeline breakdown);
    - filter by Metrika goals (registrations, subscriptions, purchases);
    - specific campaigns or ad groups;
    - non-default fields (CTR, AvgCpc, BounceRate, AvgPageviews, etc.);
    - long timeframes (months / years), pagination, or file output.

    Args:
        date_from: Start date (YYYY-MM-DD). Defaults to today - 8 days.
        date_to: End date (YYYY-MM-DD). Defaults to today.
    """
    runner = get_runner()
    resolved_dates = _resolve_report_dates(date_from, date_to)
    if isinstance(resolved_dates, ToolError):
        return tool_error_dict(resolved_dates)
    resolved_from, resolved_to = resolved_dates
    args = [
        "reports",
        "get",
        "--type",
        DEFAULT_REPORT_TYPE,
        "--from",
        resolved_from,
        "--to",
        resolved_to,
        "--name",
        DEFAULT_REPORT_NAME,
        "--fields",
        DEFAULT_REPORT_FIELDS,
        "--format",
        "json",
    ]
    return runner.run_json(args)


@mcp.tool(
    description="List supported Yandex.Direct report types with guidance on when to pick each (use before reports_custom if unsure which report_type fits). Call tool_help('reports_list_types') for parameters.",
)
@handle_cli_errors
def reports_list_types() -> list[str] | dict:
    """List supported Yandex.Direct report types with guidance per type.

    Use this when the user is unsure which report type fits their question,
    or when you want to remind yourself what each ReportType returns before
    calling `reports_custom(report_type=...)`.

    Available types and when to pick each:
    - CUSTOM_REPORT — universal report. Supports the widest set of dimensions
      (Date, Week, Month, Quarter, Year, Device, Placement, Gender, Age, Slot,
      Criterion, …) and all metric fields including per-goal Conversions and
      Goals. This is the default for `reports_custom` and the right answer
      99% of the time when the user asks for "stats grouped by …" or
      "stats filtered by …".
    - CAMPAIGN_PERFORMANCE_REPORT — per-campaign aggregated stats.
    - ADGROUP_PERFORMANCE_REPORT — per-ad-group aggregated stats.
    - AD_PERFORMANCE_REPORT — per-ad aggregated stats.
    - CRITERIA_PERFORMANCE_REPORT — per-keyword/criterion stats. Best for
      "top N keywords by clicks/cost/CTR".
    - SEARCH_QUERY_PERFORMANCE_REPORT — actual user search queries that
      triggered the ads. Best for negative-keyword research.
    - ACCOUNT_PERFORMANCE_REPORT — totals for the whole account.
    - REACH_AND_FREQUENCY_PERFORMANCE_REPORT — reach and frequency for media
      campaigns.

    Returns the live list of report types from `direct`.
    """
    runner = get_runner()
    return runner.run_json(["reports", "list-types"])


def _allowed_output_roots() -> tuple[Path, ...]:
    roots = [
        Path(tempfile.gettempdir()),
        Path("/tmp"),
    ]
    plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA")
    if plugin_data:
        roots.append(Path(plugin_data))

    resolved_roots: list[Path] = []
    for root in roots:
        resolved = root.expanduser().resolve()
        if resolved not in resolved_roots:
            resolved_roots.append(resolved)
    return tuple(resolved_roots)


def _resolve_output_path(output_path: str) -> Path:
    resolved = Path(output_path).expanduser().resolve()
    allowed_roots = _allowed_output_roots()
    if any(resolved == root or resolved.is_relative_to(root) for root in allowed_roots):
        return resolved

    allowed = ", ".join(str(root) for root in allowed_roots)
    raise ValueError(f"output_path must be under one of: {allowed}; got {resolved}")


def _count_json_rows(path: Path) -> int | None:
    """Count top-level JSON array elements without loading the whole file."""
    depth = 0
    count = 0
    in_string = False
    escape = False
    array_started = False
    value_active = False

    with path.open(encoding="utf-8") as f:
        while chunk := f.read(1024 * 1024):
            for char in chunk:
                if not array_started:
                    if char.isspace():
                        continue
                    if char != "[":
                        return 1 if char == "{" else None
                    array_started = True
                    depth = 1
                    continue

                if in_string:
                    if escape:
                        escape = False
                    elif char == "\\":
                        escape = True
                    elif char == '"':
                        in_string = False
                    continue

                if char.isspace():
                    continue
                if char == '"':
                    if depth == 1 and not value_active:
                        count += 1
                        value_active = True
                    in_string = True
                    continue
                if char in "[{":
                    if depth == 1 and not value_active:
                        count += 1
                        value_active = True
                    depth += 1
                    continue
                if char in "]}":
                    if char == "]" and depth == 1:
                        return count
                    depth -= 1
                    if depth < 1:
                        return None
                    continue
                if char == "," and depth == 1:
                    value_active = False
                    continue
                if depth == 1 and not value_active:
                    count += 1
                    value_active = True

    return None if array_started else 0


def _resolved_skip(value: bool | None, cli_default: bool) -> bool:
    """Effective skip-flag value (plugin's None falls back to CLI default).

    CLI 0.3.10 defaults: skip_report_header=True, skip_report_summary=True,
    skip_column_header=False (column headers are emitted).
    """
    return cli_default if value is None else value


def _tsv_overhead_rows(
    *,
    skip_report_header: bool | None,
    skip_column_header: bool,
    skip_report_summary: bool | None,
) -> int:
    """Number of non-data rows a TSV/CSV report contains given skip-flag state.

    CLI 0.3.10 defaults to: report-header skipped, column-header kept,
    summary skipped. Each ``False`` adds one non-data line to the file.
    """
    overhead = 0
    if not _resolved_skip(skip_report_header, cli_default=True):
        overhead += 1
    if not skip_column_header:
        overhead += 1
    if not _resolved_skip(skip_report_summary, cli_default=True):
        overhead += 1
    return overhead


def _count_rows_written(
    output_path: str, response_format: str, overhead_rows: int = 1
) -> int | None:
    """Count data rows in a written report file.

    Returns 0 only when the file is missing; returns None when an existing file
    cannot be counted. ``overhead_rows`` is subtracted for non-JSON formats —
    callers must compute it from the resolved skip-flag state.
    """
    path = Path(output_path)
    if not path.exists():
        return 0
    try:
        if response_format == "json":
            return _count_json_rows(path)
        line_count = sum(1 for _ in path.open())
        return max(0, line_count - overhead_rows)
    except Exception:
        return None


@mcp.tool(
    name="reports_custom",
    description="Build an arbitrary Yandex.Direct statistics report: any FieldNames, filters, ordering, date/week/month/goal breakdowns, pagination, and file output. Use reports_custom for arbitrary fields & breakdowns; use reports_get for a quick recent snapshot. Call tool_help('reports_custom') for parameters.",
)
@handle_cli_errors
def reports_custom(
    field_names: str,
    date_from: str | None = None,
    date_to: str | None = None,
    report_type: str = "CUSTOM_REPORT",
    report_name: str | None = None,
    date_range_type: str | None = None,
    goal_ids: str | None = None,
    campaign_ids: str | None = None,
    adgroup_ids: str | None = None,
    filters: list[str] | None = None,
    order_by: list[str] | None = None,
    page_limit: int | None = None,
    page_offset: int | None = None,
    include_vat: bool | None = None,
    include_discount: bool | None = None,
    return_money_in_micros: bool = False,
    processing_mode: str | None = None,
    language: str | None = None,
    attribution_models: str | None = None,
    skip_report_header: bool | None = None,
    skip_column_header: bool = False,
    skip_report_summary: bool | None = None,
    output_path: str | None = None,
    response_format: str = "json",
    dry_run: bool = False,
) -> list[dict] | dict:
    """Build an arbitrary Yandex.Direct statistics report (CUSTOM_REPORT and others).

    Use this tool whenever the user asks for stats with ANY of:
    - group by Month / Week / Date / Quarter / Year (timeline breakdown);
    - filter by goals (registrations, subscriptions, purchases — anything
      from Metrika);
    - specific campaigns / ad groups;
    - non-default fields (CTR, AvgImpressionPosition, BounceRate,
      AvgPageviews, etc.);
    - long timeframes (months / years), pagination, or file output.

    For a quick "last week per-campaign" snapshot use `reports_get` instead.

    PRO TIP — validate before hitting the API: pass `dry_run=True` to get
    `{command, request_body}` back without contacting Yandex. Use this any
    time you're unsure whether `field_names`, `goal_ids`, `order_by`, or a
    raw `filters` entry will be accepted — Reports API rejects bad enums
    with an opaque `error_code=8000`, so a local dry run saves a round-trip.

    Args:
        field_names: Comma-separated FieldNames per Yandex.Direct Reports API
            spec (case-sensitive enum, scoped to `report_type`). When unsure,
            pass `dry_run=True` to inspect the request body, or check the
            spec at https://yandex.com/dev/direct/doc/reports/spec.html.
            See Examples below for working combinations.
        date_from: Start date (YYYY-MM-DD). Required unless date_range_type is set.
        date_to: End date (YYYY-MM-DD). Required unless date_range_type is set.
            For "last 2 years" pass explicit dates — date_range_type does NOT
            have a "last_2_years" option (only last_5_years is broader).
        report_type: Direct report type forwarded to `direct`. Use
            reports_list_types() for the live supported set. CUSTOM_REPORT is
            the default and recommended for any non-trivial query.
            CUSTOM_REPORT supports the widest set of dimensions and filters
            and is what a human Direct user means by "report" 99% of the time.
        report_name: Optional report name. If omitted, a unique name is
            auto-generated to avoid Yandex's name-keyed cache collisions.
        date_range_type: Alternative to date_from/date_to. One of:
            today, yesterday, custom_date, all_time, last_30_days, last_14_days,
            last_7_days, this_week_mon_today, this_week_mon_sun, last_week,
            last_business_week, last_3_months, last_5_years, auto. Cannot be
            combined with explicit dates.
        goal_ids: Comma-separated Metrika goal IDs (max 10). When set,
            conversion metrics in the output are split per goal — see Returns.
            Find goal IDs via `v4goals_get_stat_goals(campaign_ids=...)`.
        campaign_ids: Comma-separated campaign IDs (max 10). Maps to
            --campaign-ids.
        adgroup_ids: Comma-separated ad group IDs (max 10). Maps to
            --adgroup-ids.
        filters: Repeatable raw filters in `FIELD:OPERATOR:VALUES` form. The
            set of valid Field/Operator values is owned by the Reports API
            spec. For goal-based slicing use `goal_ids` (see above). When in
            doubt, run with `dry_run=True`.
            Example: ["Impressions:GREATER_THAN:0", "Device:IN:DESKTOP,MOBILE"].
        order_by: Repeatable `FIELD[:ASC|DESC]`. Example: ["Month:ASC"].
        page_limit: For paginated retrieval of large reports.
        page_offset: For paginated retrieval of large reports.
        include_vat: Whether amounts include VAT. Defaults to the account
            setting if omitted.
        include_discount: Whether amounts include discount. Defaults to the
            account setting if omitted.
        return_money_in_micros: If True, monetary values are returned in
            micro-RUB (default is RUB with 2 decimals).
        processing_mode: Reports API processingMode header — one of
            "auto", "online", "offline". Default is the CLI default (auto).
        language: Accept-Language for the report — "ru" or "en".
        attribution_models: Comma-separated conversion attribution models;
            allowed values: FC, LC, LSC, LYDC, FCCD, LSCCD, LYDCCD, AUTO.
        skip_report_header: True/False to set / clear the report-header row
            (title + date range). CLI default skips it (True).
        skip_column_header: True to omit the column-name row (off by default).
            CLI has no negative flag for this one — pass False to keep
            headers (default).
        skip_report_summary: True/False to set / clear the "Total rows: N"
            trailing line. CLI default skips it (True).
        output_path: Absolute path under $CLAUDE_PLUGIN_DATA or a system temp
            directory to write the full report to. When set, the tool returns
            `{output_path, rows_written, report_type, format}` instead of the
            data — use this for reports >5k rows or covering >6 months. Read
            the file afterwards with regular file tools. Ignored when
            `dry_run=True` (the dry run always returns the request body
            in-memory).
        response_format: json | tsv | csv | table. Honored both for file
            output (``output_path``) and for in-memory returns. When set to
            anything other than json without ``output_path``, the result is
            wrapped as ``{format, report_type, content}`` with the raw CLI
            stdout in ``content``.
        dry_run: Build and validate the command without calling Yandex.

    Examples:

        # "Stats for 2 years, by months, broken down by 2 goals"
        reports_custom(
            field_names="Month,CampaignName,Impressions,Clicks,Cost,Conversions,CostPerConversion",
            date_from="2024-04-29", date_to="2026-04-29",
            goal_ids="12345,67890",
            order_by=["Month:ASC", "CampaignName:ASC"],
            output_path="/tmp/direct_2y_by_goals.json",
        )
        # Output adds per-goal columns: Conversions_12345_LSC,
        # Conversions_67890_LSC, CostPerConversion_12345_LSC, etc.

        # "Top 50 keywords by cost last month"
        reports_custom(
            field_names="CampaignName,Criterion,Impressions,Clicks,Cost,Conversions",
            report_type="CRITERIA_PERFORMANCE_REPORT",
            date_from="2026-03-01", date_to="2026-03-31",
            order_by=["Cost:DESC"],
            page_limit=50,
        )

        # "Daily stats per campaign for last 30 days, only campaigns 111 and 222"
        reports_custom(
            field_names="Date,CampaignName,Impressions,Clicks,Cost,Conversions",
            date_range_type="last_30_days",
            campaign_ids="111,222",
            order_by=["Date:ASC", "CampaignName:ASC"],
        )

    Returns:
        list[dict] of report rows by default; OR
        {output_path, rows_written, report_type, format} when output_path is
        set; OR a ToolError dict on failure.

        With `goal_ids` set, Yandex splits conversion metrics into per-goal
        columns: `Conversions_<goal_id>_<attribution>`, and same for
        `CostPerConversion`. Default attribution code is `LSC`. To inspect
        this in advance, run with `dry_run=True`.
    """
    if response_format not in VALID_RESPONSE_FORMATS:
        return tool_error_dict(
            ToolError(
                error="invalid_response_format",
                message=(
                    f"response_format must be one of {sorted(VALID_RESPONSE_FORMATS)}; "
                    f"got {response_format!r}."
                ),
            )
        )
    if date_range_type and (date_from or date_to):
        return tool_error_dict(
            ToolError(
                error="conflicting_date_inputs",
                message="Pass either date_range_type OR explicit date_from/date_to, not both.",
            )
        )
    if not date_range_type and (not date_from or not date_to):
        return tool_error_dict(
            ToolError(
                error="missing_date_range",
                message="Pass both date_from and date_to, or use date_range_type for a preset range.",
            )
        )
    if processing_mode is not None and processing_mode not in VALID_PROCESSING_MODES:
        return tool_error_dict(
            ToolError(
                error="invalid_processing_mode",
                message=(
                    f"processing_mode must be one of {sorted(VALID_PROCESSING_MODES)}; "
                    f"got {processing_mode!r}."
                ),
            )
        )
    if language is not None and language not in VALID_REPORT_LANGUAGES:
        return tool_error_dict(
            ToolError(
                error="invalid_language",
                message=(
                    f"language must be one of {sorted(VALID_REPORT_LANGUAGES)}; "
                    f"got {language!r}."
                ),
            )
        )
    if attribution_models is not None:
        tokens = [t.strip() for t in attribution_models.split(",") if t.strip()]
        unknown = [m for m in tokens if m not in VALID_ATTRIBUTION_MODELS]
        if unknown:
            return tool_error_dict(
                ToolError(
                    error="invalid_attribution_models",
                    message=(
                        f"Unknown attribution models: {unknown}. "
                        f"Allowed: {sorted(VALID_ATTRIBUTION_MODELS)}."
                    ),
                )
            )
        # Normalize: send a whitespace-clean CSV to the CLI so what we
        # validated is bit-for-bit what reaches the CLI.
        attribution_models = ",".join(tokens)

    effective_filters: list[str] = list(filters) if filters else []
    if any(_is_goals_filter(f) for f in effective_filters):
        return tool_error_dict(
            ToolError(
                error="invalid_goals_filter",
                message=(
                    "Goals filters are not supported by Reports API Filter.Field; "
                    "pass goal IDs via goal_ids instead."
                ),
            )
        )

    # report_type / date_range_type values are enforced by the direct CLI's
    # click.Choice. Plugin-side pre-validation deliberately avoided so the
    # CLI error path (with hint "direct rejected report type") keeps working
    # — see tests/test_reports.py::test_reports_custom_unknown_report_type.

    name = report_name or f"mcp_custom_{int(time.time() * 1000)}"

    args: list[str] = ["reports", "get", "--type", report_type]

    # `direct reports get` marks --from/--to as required=True even when
    # --date-range-type is set, and always emits DateFrom/DateTo in the
    # SelectionCriteria (the API ignores them for non-CUSTOM_DATE ranges).
    # So we must ALWAYS pass a concrete date pair; otherwise Click rejects the
    # call with "Missing option '--from'" before the request is ever built and
    # every preset-range report fails. See issue #170 finding #1.
    resolved_dates = _resolve_report_dates(date_from, date_to)
    if isinstance(resolved_dates, ToolError):
        return tool_error_dict(resolved_dates)
    resolved_from, resolved_to = resolved_dates
    args.extend(["--from", resolved_from, "--to", resolved_to])

    if date_range_type:
        args.extend(["--date-range-type", date_range_type])

    args.extend(["--name", name, "--fields", field_names])

    if campaign_ids:
        args.extend(["--campaign-ids", campaign_ids])
    if adgroup_ids:
        args.extend(["--adgroup-ids", adgroup_ids])
    if goal_ids:
        args.extend(["--goals", goal_ids])

    for f in effective_filters:
        args.extend(["--filter", f])

    if order_by:
        for ob in order_by:
            args.extend(["--order-by", ob])

    if page_limit is not None:
        args.extend(["--page-limit", str(page_limit)])
    if page_offset is not None:
        args.extend(["--page-offset", str(page_offset)])

    if include_vat is True:
        args.append("--include-vat")
    elif include_vat is False:
        args.append("--no-include-vat")

    if include_discount is True:
        args.append("--include-discount")
    elif include_discount is False:
        args.append("--no-include-discount")

    if return_money_in_micros:
        args.append("--return-money-in-micros")

    if processing_mode is not None:
        args.extend(["--processing-mode", processing_mode])
    if language is not None:
        args.extend(["--language", language])
    if attribution_models is not None:
        args.extend(["--attribution-models", attribution_models])

    if skip_report_header is True:
        args.append("--skip-report-header")
    elif skip_report_header is False:
        args.append("--no-skip-report-header")

    if skip_column_header:
        args.append("--skip-column-header")

    if skip_report_summary is True:
        args.append("--skip-report-summary")
    elif skip_report_summary is False:
        args.append("--no-skip-report-summary")

    if dry_run:
        args.append("--dry-run")

    resolved_output_path: Path | None = None
    if output_path and not dry_run:
        try:
            resolved_output_path = _resolve_output_path(output_path)
        except ValueError as e:
            return tool_error_dict(
                ToolError(error="invalid_output_path", message=str(e))
            )
        args.extend(["--output", str(resolved_output_path)])
    args.extend(["--format", response_format])

    runner = get_runner()

    # Dry-run always emits JSON ({command, headers, body}) regardless of
    # response_format, so it's safe to go through run_json.
    if dry_run:
        result = runner.run_json(args, timeout=CUSTOM_REPORT_TIMEOUT_SECONDS)
        request_body: dict | list | None
        if isinstance(result, dict) and "body" in result:
            request_body = result["body"]
        else:
            request_body = result
        return {
            "dry_run": True,
            "command": ["direct", *args],
            "request_body": request_body,
        }

    overhead = _tsv_overhead_rows(
        skip_report_header=skip_report_header,
        skip_column_header=skip_column_header,
        skip_report_summary=skip_report_summary,
    )

    if resolved_output_path is not None:
        # CLI writes the file itself; stdout is irrelevant for parsing.
        # run_checked raises CliError on non-zero exit so handle_cli_errors
        # can convert it into a structured ToolError.
        runner.run_checked(args, timeout=CUSTOM_REPORT_TIMEOUT_SECONDS)
        return {
            "output_path": str(resolved_output_path),
            "rows_written": _count_rows_written(
                str(resolved_output_path), response_format, overhead_rows=overhead
            ),
            "report_type": report_type,
            "format": response_format,
        }

    if response_format == "json":
        return runner.run_json(args, timeout=CUSTOM_REPORT_TIMEOUT_SECONDS)

    # In-memory TSV / CSV / table: return the raw stdout payload — CLI
    # already strips the report-header and summary rows by default, so the
    # text is ready for downstream consumers. run_checked surfaces non-zero
    # exits as CliError instead of silently returning empty content.
    completed = runner.run_checked(args, timeout=CUSTOM_REPORT_TIMEOUT_SECONDS)
    return {
        "format": response_format,
        "report_type": report_type,
        "content": completed.stdout,
    }
