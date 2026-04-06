"""MCP tools for keyword management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors


@mcp.tool()
@handle_cli_errors
def keywords_list(campaign_ids: str) -> list[dict] | dict:
    """List keywords in specified campaigns.

    Args:
        campaign_ids: Comma-separated campaign IDs (max 10).
    """
    runner = get_runner()
    return runner.run_json(["keywords", "get", "--campaign-ids", campaign_ids, "--format", "json"])


@mcp.tool()
@handle_cli_errors
def keywords_update(id: str, bid: str) -> dict:
    """Update keyword bid.

    Args:
        id: Keyword ID.
        bid: New bid in micro-units (e.g., 15 RUB = 15000000). Must be a positive integer.
    """
    try:
        bid_value = int(bid)
        if bid_value <= 0:
            raise ValueError("Bid must be positive")
    except (ValueError, TypeError):
        return ToolError(
            error="invalid_bid",
            message=f"Bid must be a positive integer in micro-units. Got: '{bid}'",
        ).__dict__

    runner = get_runner()
    runner.run_json(["keywords", "update", "--id", id, "--bid", str(bid_value), "--format", "json"])
    return {"success": True, "id": id, "bid": bid_value}
