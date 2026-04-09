"""MCP tools for keyword bid management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors


@mcp.tool()
@handle_cli_errors
def keyword_bids_list(
    campaign_ids: str | None = None,
    ad_group_ids: str | None = None,
    keyword_ids: str | None = None,
) -> list[dict] | dict:
    """List keyword bids.

    Args:
        campaign_ids: Comma-separated campaign IDs (optional).
        ad_group_ids: Comma-separated ad group IDs (optional).
        keyword_ids: Comma-separated keyword IDs (optional).
    """
    args = ["keywordbids", "get", "--format", "json"]
    if campaign_ids:
        args.extend(["--campaign-ids", campaign_ids])
    if ad_group_ids:
        args.extend(["--adgroup-ids", ad_group_ids])
    if keyword_ids:
        args.extend(["--keyword-ids", keyword_ids])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def keyword_bids_set(
    keyword_id: str,
    search_bid: str | None = None,
    network_bid: str | None = None,
) -> dict:
    """Set keyword bids.

    Args:
        keyword_id: Keyword ID.
        search_bid: Search bid amount (optional).
        network_bid: Network bid amount (optional).
    """
    args = ["keywordbids", "set", "--keyword-id", keyword_id]
    if search_bid:
        args.extend(["--search-bid", search_bid])
    if network_bid:
        args.extend(["--network-bid", network_bid])
    args.extend(["--format", "json"])
    runner = get_runner()
    return runner.run_json(args)
