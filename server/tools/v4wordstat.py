"""MCP tools for Yandex Direct v4 Live Wordstat report commands."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import (
    finalize_json_args,
    normalize_optional_str,
    validate_phrase_csv,
)

MAX_WORDSTAT_PHRASES = 10


@mcp.tool(
    name="v4wordstat_create_report",
    description="Create a v4 Live Wordstat report via CreateNewWordstatReport (up to 10 phrases). Call tool_help('v4wordstat_create_report') for parameters.",
)
@handle_cli_errors
def v4wordstat_create_report(
    phrases: str,
    geo_ids: str | None = None,
    dry_run: bool = False,
) -> dict | list[dict]:
    """Create a v4 Live Wordstat report via CreateNewWordstatReport.

    Args:
        phrases: Comma-separated phrases, up to 10.
        geo_ids: Optional comma-separated geo region IDs.
        dry_run: Show the direct request without sending it.
    """
    normalized_phrases = validate_phrase_csv(
        phrases, MAX_WORDSTAT_PHRASES, subject="Wordstat report"
    )
    if isinstance(normalized_phrases, ToolError):
        return normalized_phrases.__dict__

    args = ["v4wordstat", "create-report", "--phrases", normalized_phrases]
    normalized_geo = normalize_optional_str(geo_ids)
    if normalized_geo:
        args.extend(["--geo-ids", normalized_geo])
    return get_runner().run_json(finalize_json_args(args, dry_run))


@mcp.tool(
    name="v4wordstat_list_reports",
    description="List v4 Live Wordstat reports via GetWordstatReportList. Call tool_help('v4wordstat_list_reports') for parameters.",
)
@handle_cli_errors
def v4wordstat_list_reports(dry_run: bool = False) -> dict | list[dict]:
    """List v4 Live Wordstat reports via GetWordstatReportList."""
    args = ["v4wordstat", "list-reports"]
    return get_runner().run_json(finalize_json_args(args, dry_run))


@mcp.tool(
    name="v4wordstat_get_report",
    description="Get a ready v4 Live Wordstat report by ID via GetWordstatReport. Call tool_help('v4wordstat_get_report') for parameters.",
)
@handle_cli_errors
def v4wordstat_get_report(report_id: int, dry_run: bool = False) -> dict | list[dict]:
    """Get a ready v4 Live Wordstat report via GetWordstatReport.

    Args:
        report_id: Wordstat report ID.
        dry_run: Show the direct request without sending it.
    """
    args = ["v4wordstat", "get-report", "--report-id", str(report_id)]
    return get_runner().run_json(finalize_json_args(args, dry_run))


@mcp.tool(
    name="v4wordstat_delete_report",
    description="Delete a v4 Live Wordstat report by ID via DeleteWordstatReport. Call tool_help('v4wordstat_delete_report') for parameters.",
)
@handle_cli_errors
def v4wordstat_delete_report(
    report_id: int, dry_run: bool = False
) -> dict | list[dict]:
    """Delete a v4 Live Wordstat report via DeleteWordstatReport.

    Args:
        report_id: Wordstat report ID.
        dry_run: Show the direct request without sending it.
    """
    args = ["v4wordstat", "delete-report", "--report-id", str(report_id)]
    return get_runner().run_json(finalize_json_args(args, dry_run))
