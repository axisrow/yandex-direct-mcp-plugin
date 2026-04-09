"""MCP tools for bid management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit, validate_positive_int


@mcp.tool()
@handle_cli_errors
def bids_list(campaign_ids: str) -> list[dict] | dict:
    """List bids for specified campaigns.

    Args:
        campaign_ids: Comma-separated campaign IDs (max 10).
    """
    batch_error = check_batch_limit(campaign_ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    return runner.run_json(
        ["bids", "get", "--campaign-ids", campaign_ids, "--format", "json"]
    )


@mcp.tool()
@handle_cli_errors
def bids_set(campaign_id: str, bid: str, context_bid: str | None = None) -> dict:
    """Set bid for a campaign.

    Args:
        campaign_id: Campaign ID.
        bid: Bid amount in micro-units (e.g., 15 RUB = 15000000). Must be a positive integer.
        context_bid: Optional context bid amount in micro-units. Must be a positive integer if provided.
    """
    bid_result = validate_positive_int(bid, "bid")
    if isinstance(bid_result, ToolError):
        return bid_result.__dict__
    bid_value = bid_result

    cmd = [
        "bids",
        "set",
        "--campaign-id",
        campaign_id,
        "--bid",
        str(bid_value),
        "--format",
        "json",
    ]

    if context_bid is not None:
        context_result = validate_positive_int(context_bid, "context_bid")
        if isinstance(context_result, ToolError):
            return context_result.__dict__
        cmd.extend(["--context-bid", str(context_result)])

    runner = get_runner()
    result = runner.run_json(cmd)
    return result
