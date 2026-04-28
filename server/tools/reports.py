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
from server.tools import get_runner, handle_cli_errors

DEFAULT_REPORT_TYPE = "CAMPAIGN_PERFORMANCE_REPORT"
DEFAULT_REPORT_NAME = "mcp_campaign_performance"
DEFAULT_REPORT_FIELDS = (
    "CampaignName,Impressions,Clicks,Cost,Conversions,CostPerConversion,ConversionRate"
)
DEFAULT_WINDOW_DAYS = 8

CUSTOM_REPORT_TIMEOUT_SECONDS = 120

VALID_RESPONSE_FORMATS = frozenset({"json", "tsv", "csv", "table"})


def _resolve_report_dates(
    date_from: str | None, date_to: str | None
) -> tuple[str, str]:
    """Resolve the reporting window to match Direct's default day range."""
    if date_from and date_to:
        return date_from, date_to

    if date_to:
        resolved_to = date.fromisoformat(date_to)
        resolved_from = resolved_to - timedelta(days=DEFAULT_WINDOW_DAYS)
        return resolved_from.isoformat(), date_to

    if date_from:
        resolved_from = date.fromisoformat(date_from)
        resolved_to = resolved_from + timedelta(days=DEFAULT_WINDOW_DAYS)
        return date_from, resolved_to.isoformat()

    today = date.today()
    return (today - timedelta(days=DEFAULT_WINDOW_DAYS)).isoformat(), today.isoformat()


@mcp.tool(name="reports_get")
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
    resolved_from, resolved_to = _resolve_report_dates(date_from, date_to)
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


@mcp.tool()
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

    Returns the live list of report types from direct-cli.
    """
    runner = get_runner()
    return runner.run_json(["reports", "list-types"])


def _filter_field(filter_str: str) -> str:
    """Extract FIELD from a 'FIELD:OPERATOR:VALUES' filter string."""
    return filter_str.split(":", 1)[0] if ":" in filter_str else filter_str


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


def _count_rows_written(output_path: str, response_format: str) -> int | None:
    """Count data rows in a written report file.

    Returns 0 only when the file is missing; returns None when an existing file
    cannot be counted.
    """
    path = Path(output_path)
    if not path.exists():
        return 0
    try:
        if response_format == "json":
            return _count_json_rows(path)
        line_count = sum(1 for _ in path.open())
        return max(0, line_count - 1)
    except Exception:
        return None


@mcp.tool(name="reports_custom")
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

    Args:
        field_names: Comma-separated list of report fields (dimensions + metrics).
            Common dimensions for grouping: Date, Week, Month, Quarter, Year,
            CampaignName, CampaignId, AdGroupName, AdGroupId, AdId, Criterion,
            Device, Placement, Gender, Age, Slot, TargetingLocationName.
            Common metrics: Impressions, Clicks, Cost, Ctr, AvgCpc,
            AvgClickPosition, AvgImpressionPosition, BounceRate, AvgPageviews,
            Conversions, CostPerConversion, ConversionRate, Goals, Revenue.
            Example for "stats by month with goals":
              "Month,Impressions,Clicks,Cost,Goals,Conversions"
        date_from: Start date (YYYY-MM-DD). Required unless date_range_type is set.
        date_to: End date (YYYY-MM-DD). Required unless date_range_type is set.
            For "last 2 years" pass explicit dates — date_range_type does NOT
            have a "last_2_years" option (only last_5_years is broader).
        report_type: Direct report type forwarded to direct-cli. Use
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
        goal_ids: Convenience shortcut. Comma-separated Metrika goal IDs.
            Internally translates to --filter Goals:IN:<ids>. Note: in
            CUSTOM_REPORT the field is named `Goals` (NOT `GoalsIds`).
            Find goal IDs via `v4goals_get_stat_goals(campaign_ids=...)`.
            When `Goals` is also in field_names, each row reports per-goal
            conversions for those goal IDs.
        campaign_ids: Comma-separated campaign IDs (max 10). Maps to
            --campaign-ids.
        adgroup_ids: Comma-separated ad group IDs (max 10). Maps to
            --adgroup-ids.
        filters: Repeatable raw filters in `FIELD:OPERATOR:VALUES` form.
            Operators: EQUALS, NOT_EQUALS, IN, NOT_IN, LESS_THAN, GREATER_THAN,
            STARTS_WITH_IGNORE_CASE, DOES_NOT_START_WITH_IGNORE_CASE.
            Example: ["Impressions:GREATER_THAN:0", "Device:IN:DESKTOP,MOBILE"].
            Cannot include a `Goals:` filter when `goal_ids` is also passed.
        order_by: Repeatable `FIELD[:ASC|DESC]`. Example: ["Month:ASC"].
        page_limit: For paginated retrieval of large reports.
        page_offset: For paginated retrieval of large reports.
        include_vat: Whether amounts include VAT. Defaults to the account
            setting if omitted.
        include_discount: Whether amounts include discount. Defaults to the
            account setting if omitted.
        return_money_in_micros: If True, monetary values are returned in
            micro-RUB (default is RUB with 2 decimals).
        output_path: Absolute path under $CLAUDE_PLUGIN_DATA or a system temp
            directory to write the full report to. When set, the tool returns
            `{output_path, rows_written, report_type, format}` instead of the
            data — use this for reports >5k rows or covering >6 months. Read
            the file afterwards with regular file tools.
        response_format: json | tsv | csv | table. Only meaningful with
            output_path; without it, JSON is always returned in-memory.
        dry_run: Build and validate the command without calling Yandex.

    Examples:

        # "Stats for 2 years, group by months, goals 12345 and 67890"
        reports_custom(
            field_names="Month,CampaignName,Impressions,Clicks,Cost,Goals,Conversions",
            date_from="2024-04-29", date_to="2026-04-29",
            goal_ids="12345,67890",
            order_by=["Month:ASC", "CampaignName:ASC"],
            output_path="/tmp/direct_2y_by_month.json",
        )

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
    """
    if response_format not in VALID_RESPONSE_FORMATS:
        raise ValueError(
            f"unknown response_format {response_format!r}; "
            f"expected one of {sorted(VALID_RESPONSE_FORMATS)}"
        )
    if date_range_type and (date_from or date_to):
        raise ValueError(
            "pass either date_range_type OR explicit date_from/date_to, not both"
        )
    if not date_range_type and (not date_from or not date_to):
        raise ValueError(
            "pass both date_from and date_to, or use date_range_type for a preset range"
        )

    effective_filters: list[str] = list(filters) if filters else []
    if goal_ids:
        if any(_filter_field(f).lower() == "goals" for f in effective_filters):
            raise ValueError(
                "conflicting goal filter: pass either goal_ids or "
                "filters with a 'Goals:' entry, not both"
            )
        effective_filters.append(f"Goals:IN:{goal_ids}")

    name = report_name or f"mcp_custom_{int(time.time() * 1000)}"

    args: list[str] = ["reports", "get", "--type", report_type]

    if date_range_type:
        args.extend(["--date-range-type", date_range_type])
    else:
        resolved_from, resolved_to = _resolve_report_dates(date_from, date_to)
        args.extend(["--from", resolved_from, "--to", resolved_to])

    args.extend(["--name", name, "--fields", field_names])

    if campaign_ids:
        args.extend(["--campaign-ids", campaign_ids])
    if adgroup_ids:
        args.extend(["--adgroup-ids", adgroup_ids])

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

    if dry_run:
        args.append("--dry-run")

    resolved_output_path: Path | None = None
    if output_path:
        resolved_output_path = _resolve_output_path(output_path)
        args.extend(
            ["--output", str(resolved_output_path), "--format", response_format]
        )
    else:
        args.extend(["--format", "json"])

    runner = get_runner()
    result = runner.run_json(args, timeout=CUSTOM_REPORT_TIMEOUT_SECONDS)

    if resolved_output_path is not None and not dry_run:
        return {
            "output_path": str(resolved_output_path),
            "rows_written": _count_rows_written(
                str(resolved_output_path), response_format
            ),
            "report_type": report_type,
            "format": response_format,
        }

    return result
