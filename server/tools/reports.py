"""MCP tool for campaign statistics reports."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors


@mcp.tool()
@handle_cli_errors
def reports_get(date_from: str | None = None, date_to: str | None = None) -> list[dict] | dict:
    """Get campaign statistics for a date range.

    Args:
        date_from: Start date (YYYY-MM-DD). Defaults to 7 days ago.
        date_to: End date (YYYY-MM-DD). Defaults to today.
    """
    runner = get_runner()
    args = ["reports", "get", "--format", "json"]
    if date_from:
        args.extend(["--date-from", date_from])
    if date_to:
        args.extend(["--date-to", date_to])
    return runner.run_json(args)
