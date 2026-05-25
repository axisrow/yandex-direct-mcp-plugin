"""MCP tools for checking changes in Yandex.Direct."""

import re

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit, parse_ids

ALLOWED_FIELD_NAMES = {"CampaignIds", "AdGroupIds", "AdIds", "CampaignsStat"}

_TZ_SUFFIX_RE = re.compile(r"(Z|[+-]\d{2}:?\d{2})$")


def _normalize_timestamp(ts: str) -> str:
    """Append 'Z' (UTC) when the timestamp carries no timezone suffix.

    Yandex Direct ``Changes.check`` requires ISO 8601 with an explicit zone;
    without it the API silently treats the value as local server time, which
    shifts the change window. Strip surrounding whitespace first — a trailing
    newline would otherwise let Python's ``$`` anchor match before it and mask
    a missing zone, and a trailing space would inject an invalid character.
    """
    ts = ts.strip()
    return ts if _TZ_SUFFIX_RE.search(ts) else f"{ts}Z"


def _validate_field_names(field_names: str) -> ToolError | None:
    tokens = [t.strip() for t in field_names.split(",") if t.strip()]
    if not tokens:
        return ToolError(
            error="missing_field_names",
            message=(
                "Provide a non-empty comma-separated FieldNames; allowed: "
                f"{sorted(ALLOWED_FIELD_NAMES)}."
            ),
        )
    unknown = [t for t in tokens if t not in ALLOWED_FIELD_NAMES]
    if unknown:
        return ToolError(
            error="invalid_field_names",
            message=(
                f"Unknown FieldNames: {unknown}. Allowed: {sorted(ALLOWED_FIELD_NAMES)}."
            ),
        )
    return None


@mcp.tool()
@handle_cli_errors
def changes_check(
    timestamp: str,
    field_names: str | None = None,
    fields: str | None = None,
    campaign_ids: str | None = None,
    ad_group_ids: str | None = None,
    ad_ids: str | None = None,
) -> dict:
    """Check changes since ``timestamp`` filtered by exactly one ID set.

    Mirrors Yandex Direct API v5 ``Changes.check`` — see
    https://yandex.ru/dev/direct/doc/ref-v5/changes/check.html.

    Args:
        timestamp: ISO 8601 timestamp. A bare ``YYYY-MM-DDTHH:MM:SS`` is
            normalized to UTC (``...Z``); explicit offsets are kept as-is.
        field_names: Backward-compatible alias for ``fields``.
        fields: Optional comma-separated FieldNames. If omitted, no ``--fields``
            flag is forwarded and the CLI/API default applies. Allowed:
            ``CampaignIds``, ``AdGroupIds``, ``AdIds``, ``CampaignsStat``.
            When both aliases are passed, ``fields`` takes precedence.
        campaign_ids: Comma-separated campaign IDs (up to 3000). Mutually
            exclusive with ``ad_group_ids`` and ``ad_ids``.
        ad_group_ids: Comma-separated ad group IDs (up to 10000). Mutually
            exclusive with ``campaign_ids`` and ``ad_ids``.
        ad_ids: Comma-separated ad IDs (up to 50000). Mutually exclusive
            with ``campaign_ids`` and ``ad_group_ids``.
    """
    selected_fields = fields if fields is not None else field_names
    if selected_fields is not None:
        field_error = _validate_field_names(selected_fields)
        if field_error:
            return field_error.__dict__

    provided: list[tuple[str, str, str, int]] = []
    for cli_flag, label, value, limit in (
        ("--campaign-ids", "campaign_ids", campaign_ids, 3000),
        ("--ad-group-ids", "ad_group_ids", ad_group_ids, 10_000),
        ("--ad-ids", "ad_ids", ad_ids, 50_000),
    ):
        if value is None:
            continue
        stripped = value.strip()
        if not stripped:
            continue
        if not parse_ids(stripped):
            # Strings like "," or " , , " strip to non-empty but yield zero
            # real IDs — treat as not provided to avoid forwarding a junk
            # --campaign-ids value to the CLI.
            continue
        provided.append((cli_flag, label, stripped, limit))

    if not provided:
        return ToolError(
            error="missing_id_filter",
            message=("Provide exactly one of campaign_ids, ad_group_ids, or ad_ids."),
        ).__dict__
    if len(provided) > 1:
        return ToolError(
            error="conflicting_id_filters",
            message=(
                "Pass exactly one of campaign_ids, ad_group_ids, or ad_ids — "
                f"got: {', '.join(p[1] for p in provided)}."
            ),
        ).__dict__

    cli_flag, _label, value, limit = provided[0]
    batch_error = check_batch_limit(value, max_size=limit)
    if batch_error:
        return batch_error.__dict__

    args = [
        "changes",
        "check",
        cli_flag,
        value,
        "--timestamp",
        _normalize_timestamp(timestamp),
    ]
    if selected_fields is not None:
        args.extend(["--fields", selected_fields])
    args.extend(["--format", "json"])
    return get_runner().run_json(args)


@mcp.tool(name="changes_check_campaigns")
@handle_cli_errors
def changes_checkcamp(timestamp: str) -> dict:
    """Check account-wide campaign changes since ``timestamp``.

    Args:
        timestamp: ISO 8601 timestamp. A bare ``YYYY-MM-DDTHH:MM:SS`` is
            normalized to UTC (``...Z``).
    """
    return get_runner().run_json(
        [
            "changes",
            "check-campaigns",
            "--timestamp",
            _normalize_timestamp(timestamp),
            "--format",
            "json",
        ]
    )


@mcp.tool(name="changes_check_dictionaries")
@handle_cli_errors
def changes_checkdict() -> dict:
    """Check dictionary changes.

    CLI 0.3.8 `changes check-dictionaries` takes no parameters.
    """
    return get_runner().run_json(["changes", "check-dictionaries", "--format", "json"])
