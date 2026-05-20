"""MCP tools for leads management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors


@mcp.tool(name="leads_get")
@handle_cli_errors
def leads_list(
    turbo_page_ids: str,
    datetime_from: str | None = None,
    datetime_to: str | None = None,
    limit: int | None = None,
    fetch_all: bool = False,
    fields: str | None = None,
) -> dict:
    """List leads for the given turbo pages.

    CLI 0.3.8 `leads get` requires `--turbo-page-ids` (there is no
    `--campaign-ids` selector — leads are scoped to Turbo pages, not campaigns).

    Args:
        turbo_page_ids: Comma-separated turbo page IDs (required).
        datetime_from: DateTimeFrom in YYYY-MM-DDTHH:MM:SS format.
        datetime_to: DateTimeTo in YYYY-MM-DDTHH:MM:SS format.
        limit: Limit number of results.
        fetch_all: Fetch all pages.
        fields: Comma-separated field names.
    """
    normalized = turbo_page_ids.strip()
    if not normalized:
        return ToolError(
            error="missing_turbo_page_ids",
            message="Provide at least one turbo page ID.",
        ).__dict__

    args = [
        "leads",
        "get",
        "--format",
        "json",
        "--turbo-page-ids",
        normalized,
    ]
    if datetime_from is not None:
        args.extend(["--datetime-from", datetime_from])
    if datetime_to is not None:
        args.extend(["--datetime-to", datetime_to])
    if limit is not None:
        args.extend(["--limit", str(limit)])
    if fetch_all:
        args.append("--fetch-all")
    if fields is not None:
        args.extend(["--fields", fields])
    return get_runner().run_json(args)
