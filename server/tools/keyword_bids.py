"""MCP tools for keyword bid management."""

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
    keyword_id: int,
    search_bid: int | None = None,
    network_bid: int | None = None,
) -> dict:
    """Set keyword bids.

    Args:
        keyword_id: Keyword ID.
        search_bid: Optional search bid in micro-units (RUB × 1,000,000); CLI 0.2.10+
            rejects values 0 < x < 100_000 with a "did you mean × 1_000_000" hint.
        network_bid: Optional network bid in micro-units (same rules as `search_bid`).
    """
    if search_bid is None and network_bid is None:
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one of: search_bid, network_bid",
        ).__dict__

    args = ["keywordbids", "set", "--keyword-id", str(keyword_id)]
    if search_bid is not None:
        args.extend(["--search-bid", str(search_bid)])
    if network_bid is not None:
        args.extend(["--network-bid", str(network_bid)])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(name="keywordbids_set_auto")
@handle_cli_errors
def keyword_bids_set_auto(
    campaign_id: int | None = None,
    ad_group_id: int | None = None,
    keyword_id: int | None = None,
    target_traffic_volume: int | None = None,
    target_coverage: int | None = None,
    increase_percent: int | None = None,
    bid_ceiling: int | None = None,
) -> dict:
    """Configure automatic keyword bidding.

    Args:
        campaign_id: Campaign ID.
        ad_group_id: Ad group ID.
        keyword_id: Keyword ID.
        target_traffic_volume: WbMaximumClicks target traffic volume.
        target_coverage: NetworkByCoverage target coverage value.
        increase_percent: Bidding rule IncreasePercent.
        bid_ceiling: Optional bidding rule bid ceiling in micro-units (RUB × 1,000,000);
            CLI 0.2.10+ rejects values 0 < x < 100_000 with a "did you mean × 1_000_000" hint.
    """
    if campaign_id is None and ad_group_id is None and keyword_id is None:
        return ToolError(
            error="missing_target_scope",
            message="Provide at least one of: campaign_id, ad_group_id, keyword_id",
        ).__dict__
    if (
        target_traffic_volume is None
        and target_coverage is None
        and increase_percent is None
        and bid_ceiling is None
    ):
        return ToolError(
            error="missing_update_fields",
            message=(
                "Provide at least one of: target_traffic_volume, "
                "target_coverage, increase_percent, bid_ceiling"
            ),
        ).__dict__

    args = ["keywordbids", "set-auto"]
    if campaign_id is not None:
        args.extend(["--campaign-id", str(campaign_id)])
    if ad_group_id is not None:
        args.extend(["--adgroup-id", str(ad_group_id)])
    if keyword_id is not None:
        args.extend(["--keyword-id", str(keyword_id)])
    if target_traffic_volume is not None:
        args.extend(["--target-traffic-volume", str(target_traffic_volume)])
    if target_coverage is not None:
        args.extend(["--target-coverage", str(target_coverage)])
    if increase_percent is not None:
        args.extend(["--increase-percent", str(increase_percent)])
    if bid_ceiling is not None:
        args.extend(["--bid-ceiling", str(bid_ceiling)])

    runner = get_runner()
    return runner.run_json(args)
