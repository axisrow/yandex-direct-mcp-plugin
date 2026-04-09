"""MCP tools for leads management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit


@mcp.tool()
@handle_cli_errors
def leads_list(
    campaign_ids: str, date_from: str | None = None, date_to: str | None = None
) -> dict:
    """List leads for specified campaigns.

    Args:
        campaign_ids: Comma-separated campaign IDs (max 10).
        date_from: Optional start date in YYYY-MM-DD format.
        date_to: Optional end date in YYYY-MM-DD format.
    """
    batch_error = check_batch_limit(campaign_ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    args = [
        "leads",
        "get",
        "--campaign-ids",
        campaign_ids,
        "--format",
        "json",
    ]
    if date_from is not None:
        args.extend(["--date-from", date_from])
    if date_to is not None:
        args.extend(["--date-to", date_to])
    return runner.run_json(args)
