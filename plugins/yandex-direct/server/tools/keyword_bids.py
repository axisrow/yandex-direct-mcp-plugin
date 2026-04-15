"""MCP tools for keyword bid management."""

import json

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors


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
    normalized_campaign_ids = campaign_ids.strip() if campaign_ids is not None else None
    if normalized_campaign_ids:
        args.extend(["--campaign-ids", normalized_campaign_ids])
    normalized_ad_group_ids = ad_group_ids.strip() if ad_group_ids is not None else None
    if normalized_ad_group_ids:
        args.extend(["--adgroup-ids", normalized_ad_group_ids])
    normalized_keyword_ids = keyword_ids.strip() if keyword_ids is not None else None
    if normalized_keyword_ids:
        args.extend(["--keyword-ids", normalized_keyword_ids])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def keyword_bids_set(
    keyword_id: str,
    search_bid: str | None = None,
    network_bid: str | None = None,
    extra_json: str | dict | None = None,
) -> dict:
    """Set keyword bids.

    Args:
        keyword_id: Keyword ID.
        search_bid: Search bid amount (optional).
        network_bid: Network bid amount (optional).
        extra_json: JSON string with additional parameters (optional).
    """
    if not any((search_bid, network_bid, extra_json)):
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one of: search_bid, network_bid, extra_json",
        ).__dict__

    from server.tools.helpers import validate_positive_int

    search_bid_value: int | None = None
    if search_bid is not None:
        result = validate_positive_int(search_bid, "search_bid")
        if isinstance(result, ToolError):
            return result.__dict__
        search_bid_value = result

    network_bid_value: int | None = None
    if network_bid is not None:
        result = validate_positive_int(network_bid, "network_bid")
        if isinstance(result, ToolError):
            return result.__dict__
        network_bid_value = result

    args = ["keywordbids", "set", "--keyword-id", keyword_id]
    if search_bid_value is not None:
        args.extend(["--search-bid", str(search_bid_value)])
    if network_bid_value is not None:
        args.extend(["--network-bid", str(network_bid_value)])
    if extra_json:
        json_str = (
            json.dumps(extra_json) if isinstance(extra_json, dict) else extra_json
        )
        args.extend(["--json", json_str])
    runner = get_runner()
    return runner.run_json(args)
