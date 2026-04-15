"""MCP tools for keyword bid management."""

import json

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors


@mcp.tool(name="keywordbids_get")
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


@mcp.tool(name="keywordbids_set")
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


@mcp.tool(name="keywordbids_set_auto")
@handle_cli_errors
def keyword_bids_set_auto(
    campaign_id: str | None = None,
    ad_group_id: str | None = None,
    keyword_id: str | None = None,
    target_traffic_volume: str | None = None,
    target_coverage: str | None = None,
    increase_percent: str | None = None,
    bid_ceiling: str | None = None,
) -> dict:
    """Configure automatic keyword bidding."""
    if not any((campaign_id, ad_group_id, keyword_id)):
        return ToolError(
            error="missing_target_scope",
            message="Provide at least one of: campaign_id, ad_group_id, keyword_id",
        ).__dict__
    if not any((target_traffic_volume, target_coverage, increase_percent, bid_ceiling)):
        return ToolError(
            error="missing_update_fields",
            message=(
                "Provide at least one of: target_traffic_volume, "
                "target_coverage, increase_percent, bid_ceiling"
            ),
        ).__dict__

    args = ["keywordbids", "set-auto"]
    if campaign_id is not None:
        args.extend(["--campaign-id", campaign_id])
    if ad_group_id is not None:
        args.extend(["--adgroup-id", ad_group_id])
    if keyword_id is not None:
        args.extend(["--keyword-id", keyword_id])
    if target_traffic_volume is not None:
        args.extend(["--target-traffic-volume", target_traffic_volume])
    if target_coverage is not None:
        args.extend(["--target-coverage", target_coverage])
    if increase_percent is not None:
        args.extend(["--increase-percent", increase_percent])
    if bid_ceiling is not None:
        args.extend(["--bid-ceiling", bid_ceiling])

    runner = get_runner()
    return runner.run_json(args)
