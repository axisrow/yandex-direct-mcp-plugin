"""MCP tools for keyword bid management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import require_single_selector


@mcp.tool(
    name="keywordbids_get",
    description="List bids for individual keywords. Call tool_help('keywordbids_get') for parameters.",
)
@handle_cli_errors
def keyword_bids_list(
    campaign_ids: str | None = None,
    ad_group_ids: str | None = None,
    keyword_ids: str | None = None,
    serving_statuses: str | None = None,
    limit: int | None = None,
    fetch_all: bool = False,
) -> list[dict] | dict:
    """List keyword bids.

    Args:
        campaign_ids: Comma-separated campaign IDs.
        ad_group_ids: Comma-separated ad group IDs.
        keyword_ids: Comma-separated keyword IDs.
        serving_statuses: Comma-separated serving statuses.
        limit: Limit number of results.
        fetch_all: Fetch all pages.
    """
    normalized_campaign_ids = campaign_ids.strip() if campaign_ids is not None else None
    normalized_ad_group_ids = ad_group_ids.strip() if ad_group_ids is not None else None
    normalized_keyword_ids = keyword_ids.strip() if keyword_ids is not None else None
    normalized_serving = (
        serving_statuses.strip() if serving_statuses is not None else None
    )
    if not (
        normalized_campaign_ids
        or normalized_ad_group_ids
        or normalized_keyword_ids
        or normalized_serving
    ):
        # direct-cli rejects an empty SelectionCriteria; fetch_all is not a
        # filter. Surface a clear ToolError like keywords_get does (#170-18).
        return ToolError(
            error="missing_selector",
            message=(
                "keywordbids_get requires at least one filter: campaign_ids, "
                "ad_group_ids, keyword_ids, or serving_statuses."
            ),
        ).__dict__

    args = ["keywordbids", "get", "--format", "json"]
    if normalized_campaign_ids:
        args.extend(["--campaign-ids", normalized_campaign_ids])
    if normalized_ad_group_ids:
        args.extend(["--adgroup-ids", normalized_ad_group_ids])
    if normalized_keyword_ids:
        args.extend(["--keyword-ids", normalized_keyword_ids])
    if normalized_serving:
        args.extend(["--serving-statuses", normalized_serving])
    if limit is not None:
        args.extend(["--limit", str(limit)])
    if fetch_all:
        args.append("--fetch-all")
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(
    name="keywordbids_set",
    description="Set fixed bids for keywords; use bids_set for campaign/group-level bids and bidmodifiers_set for adjustments. Call tool_help('keywordbids_set') for parameters.",
)
@handle_cli_errors
def keyword_bids_set(
    keyword_id: int | None = None,
    campaign_id: int | None = None,
    ad_group_id: int | None = None,
    search_bid: int | None = None,
    network_bid: int | None = None,
    autotargeting_search_bid_is_auto: str | None = None,
    priority: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Set keyword bids.

    Provide EXACTLY ONE selector (keyword_id, campaign_id, or ad_group_id).

    Args:
        keyword_id: Keyword ID selector (provide exactly one selector).
        campaign_id: Campaign ID selector (provide exactly one selector).
        ad_group_id: Ad group ID selector (provide exactly one selector).
        search_bid: Optional search bid in micro-units (RUB × 1,000,000); CLI 0.2.10+
            rejects values 0 < x < 100_000 with a "did you mean × 1_000_000" hint.
        network_bid: Optional network bid in micro-units (same rules as `search_bid`).
        autotargeting_search_bid_is_auto: Autotargeting search bid auto flag.
        priority: Strategy priority.
        dry_run: Show the direct request without sending it.
    """
    selector_error = require_single_selector(
        {
            "keyword_id": keyword_id,
            "campaign_id": campaign_id,
            "ad_group_id": ad_group_id,
        },
        "keywordbids_set",
    )
    if selector_error:
        return selector_error.__dict__
    if (
        search_bid is None
        and network_bid is None
        and autotargeting_search_bid_is_auto is None
        and priority is None
    ):
        return ToolError(
            error="missing_update_fields",
            message=(
                "Provide at least one of: search_bid, network_bid, "
                "autotargeting_search_bid_is_auto, priority"
            ),
        ).__dict__

    args = ["keywordbids", "set"]
    if campaign_id is not None:
        args.extend(["--campaign-id", str(campaign_id)])
    if ad_group_id is not None:
        args.extend(["--adgroup-id", str(ad_group_id)])
    if keyword_id is not None:
        args.extend(["--keyword-id", str(keyword_id)])
    if search_bid is not None:
        args.extend(["--search-bid", str(search_bid)])
    if network_bid is not None:
        args.extend(["--network-bid", str(network_bid)])
    if autotargeting_search_bid_is_auto is not None:
        args.extend(
            [
                "--autotargeting-search-bid-is-auto",
                autotargeting_search_bid_is_auto,
            ]
        )
    if priority is not None:
        args.extend(["--priority", priority])
    if dry_run:
        args.append("--dry-run")
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(
    name="keywordbids_set_auto",
    description="Switch keyword bids to an automatic bidding strategy. Call tool_help('keywordbids_set_auto') for parameters.",
)
@handle_cli_errors
def keyword_bids_set_auto(
    campaign_id: int | None = None,
    ad_group_id: int | None = None,
    keyword_id: int | None = None,
    target_traffic_volume: int | None = None,
    target_coverage: int | None = None,
    increase_percent: int | None = None,
    bid_ceiling: int | None = None,
    dry_run: bool = False,
) -> dict:
    """Configure automatic keyword bidding.

    Provide EXACTLY ONE of target_traffic_volume or target_coverage (the
    bidding-rule root); increase_percent and bid_ceiling are optional modifiers.

    Args:
        campaign_id: Campaign ID.
        ad_group_id: Ad group ID.
        keyword_id: Keyword ID.
        target_traffic_volume: WbMaximumClicks target traffic volume (provide
            exactly one of target_traffic_volume/target_coverage).
        target_coverage: NetworkByCoverage target coverage value (provide
            exactly one of target_traffic_volume/target_coverage).
        increase_percent: Bidding rule IncreasePercent.
        bid_ceiling: Optional bidding rule bid ceiling in micro-units (RUB × 1,000,000);
            CLI 0.2.10+ rejects values 0 < x < 100_000 with a "did you mean × 1_000_000" hint.
    """
    if campaign_id is None and ad_group_id is None and keyword_id is None:
        return ToolError(
            error="missing_target_scope",
            message="Provide at least one of: campaign_id, ad_group_id, keyword_id",
        ).__dict__
    if (target_traffic_volume is None) == (target_coverage is None):
        # direct-cli requires EXACTLY ONE of --target-traffic-volume or
        # --target-coverage (the bidding-rule root). increase_percent and
        # bid_ceiling are optional modifiers of the chosen target. (#170-9)
        return ToolError(
            error="invalid_bidding_rule",
            message=(
                "Provide exactly one of target_traffic_volume or "
                "target_coverage. increase_percent and bid_ceiling are "
                "optional modifiers of the chosen target."
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
    if dry_run:
        args.append("--dry-run")

    runner = get_runner()
    return runner.run_json(args)
