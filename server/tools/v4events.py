"""MCP tools for Yandex Direct v4 Live events commands."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import finalize_json_args


@mcp.tool(
    name="v4events_get_events_log",
    description="Get v4 Live events log entries via GetEventsLog for a timestamp range. Call tool_help('v4events_get_events_log') for parameters.",
)
@handle_cli_errors
def v4events_get_events_log(
    timestamp_from: str,
    timestamp_to: str,
    currency: str = "RUB",
    limit: int | None = None,
    offset: int | None = None,
    dry_run: bool = False,
) -> dict | list[dict]:
    """Get v4 Live events log entries via GetEventsLog.

    Args:
        timestamp_from: Start timestamp in YYYY-MM-DDTHH:MM:SS format.
        timestamp_to: End timestamp in YYYY-MM-DDTHH:MM:SS format.
        currency: Currency code.
        limit: Optional result limit.
        offset: Optional result offset.
        dry_run: Show the direct request without sending it.
    """
    normalized_from = timestamp_from.strip()
    normalized_to = timestamp_to.strip()
    if not normalized_from or not normalized_to:
        return ToolError(
            error="missing_timestamp",
            message="Provide non-empty timestamp_from and timestamp_to.",
        ).__dict__

    args = [
        "v4events",
        "get-events-log",
        "--from",
        normalized_from,
        "--to",
        normalized_to,
    ]
    if currency:
        args.extend(["--currency", currency])
    if limit is not None:
        args.extend(["--limit", str(limit)])
    if offset is not None:
        args.extend(["--offset", str(offset)])
    return get_runner().run_json(finalize_json_args(args, dry_run))
