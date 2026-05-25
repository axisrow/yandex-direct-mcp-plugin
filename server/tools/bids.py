"""MCP tools for bid management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit


@mcp.tool(name="bids_get")
@handle_cli_errors
def bids_list(
    campaign_ids: str | None = None,
    ad_group_ids: str | None = None,
    keyword_ids: str | None = None,
    serving_statuses: str | None = None,
    limit: int | None = None,
    fetch_all: bool = False,
    fields: str | None = None,
) -> list[dict] | dict:
    """List bids.

    Args:
        campaign_ids: Comma-separated campaign IDs (max 10).
        ad_group_ids: Comma-separated ad group IDs (max 10).
        keyword_ids: Comma-separated keyword IDs (max 10).
        serving_statuses: Comma-separated serving statuses.
        limit: Limit number of results.
        fetch_all: Fetch all pages.
        fields: Comma-separated field names.
    """
    args = ["bids", "get", "--format", "json"]
    normalized_campaign_ids = campaign_ids.strip() if campaign_ids is not None else None
    if normalized_campaign_ids:
        batch_error = check_batch_limit(normalized_campaign_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--campaign-ids", normalized_campaign_ids])
    normalized_ad_group_ids = ad_group_ids.strip() if ad_group_ids is not None else None
    if normalized_ad_group_ids:
        batch_error = check_batch_limit(normalized_ad_group_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--adgroup-ids", normalized_ad_group_ids])
    normalized_keyword_ids = keyword_ids.strip() if keyword_ids is not None else None
    if normalized_keyword_ids:
        batch_error = check_batch_limit(normalized_keyword_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--keyword-ids", normalized_keyword_ids])
    if serving_statuses is not None:
        args.extend(["--serving-statuses", serving_statuses])
    if limit is not None:
        args.extend(["--limit", str(limit)])
    if fetch_all:
        args.append("--fetch-all")
    if fields is not None:
        args.extend(["--fields", fields])

    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(name="bids_set")
@handle_cli_errors
def bids_set(
    keyword_id: int | None = None,
    campaign_id: int | None = None,
    ad_group_id: int | None = None,
    bid: int | None = None,
    context_bid: int | None = None,
    autotargeting_search_bid_is_auto: str | None = None,
    priority: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Set a keyword bid.

    CLI 0.3.12 supports keyword-, campaign-, and ad-group-scoped bid updates
    with typed search/context bid, autotargeting, and priority fields.

    Args:
        keyword_id: Keyword ID selector.
        campaign_id: Campaign ID selector.
        ad_group_id: Ad group ID selector.
        bid: Bid in micro-units (RUB × 1,000,000); CLI 0.2.10+ rejects values
            0 < x < 100_000 with a "did you mean × 1_000_000" hint.
        context_bid: Context bid in micro-units.
        autotargeting_search_bid_is_auto: Autotargeting search bid auto flag.
        priority: Strategy priority.
        dry_run: Show the direct request without sending it.
    """
    if keyword_id is None and campaign_id is None and ad_group_id is None:
        return ToolError(
            error="missing_target_scope",
            message="Provide at least one of: keyword_id, campaign_id, ad_group_id",
        ).__dict__
    if (
        bid is None
        and context_bid is None
        and autotargeting_search_bid_is_auto is None
        and priority is None
    ):
        return ToolError(
            error="missing_update_fields",
            message=(
                "Provide at least one of: bid, context_bid, "
                "autotargeting_search_bid_is_auto, priority"
            ),
        ).__dict__

    args = ["bids", "set"]
    if campaign_id is not None:
        args.extend(["--campaign-id", str(campaign_id)])
    if ad_group_id is not None:
        args.extend(["--adgroup-id", str(ad_group_id)])
    if keyword_id is not None:
        args.extend(["--keyword-id", str(keyword_id)])
    if bid is not None:
        args.extend(["--bid", str(bid)])
    if context_bid is not None:
        args.extend(["--context-bid", str(context_bid)])
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


@mcp.tool(name="bids_set_auto")
@handle_cli_errors
def bids_set_auto(
    campaign_id: int | None = None,
    ad_group_id: int | None = None,
    keyword_id: int | None = None,
    max_bid: int | None = None,
    position: str | None = None,
    increase_percent: int | None = None,
    calculate_by: str | None = None,
    context_coverage: int | None = None,
    scope: list[str] | None = None,
    dry_run: bool = False,
) -> dict:
    """Configure automatic bidding.

    Args:
        campaign_id: Campaign ID.
        ad_group_id: Ad group ID.
        keyword_id: Keyword ID.
        max_bid: Optional maximum bid in micro-units (RUB × 1,000,000); CLI 0.2.10+
            rejects values 0 < x < 100_000 with a "did you mean × 1_000_000" hint.
        position: Strategy position.
        increase_percent: Bid increase percent.
        calculate_by: Bid calculation method.
        context_coverage: Network coverage value.
        scope: Bidding scope.
        dry_run: Show the direct request without sending it.
    """
    if campaign_id is None and ad_group_id is None and keyword_id is None:
        return ToolError(
            error="missing_target_scope",
            message="Provide at least one of: campaign_id, ad_group_id, keyword_id",
        ).__dict__
    if (
        max_bid is None
        and position is None
        and increase_percent is None
        and calculate_by is None
        and context_coverage is None
        and scope is None
    ):
        return ToolError(
            error="missing_update_fields",
            message=(
                "Provide at least one of: max_bid, position, increase_percent, "
                "calculate_by, context_coverage, scope"
            ),
        ).__dict__

    args = ["bids", "set-auto"]
    if campaign_id is not None:
        args.extend(["--campaign-id", str(campaign_id)])
    if ad_group_id is not None:
        args.extend(["--adgroup-id", str(ad_group_id)])
    if keyword_id is not None:
        args.extend(["--keyword-id", str(keyword_id)])
    if max_bid is not None:
        args.extend(["--max-bid", str(max_bid)])
    if position is not None:
        args.extend(["--position", position])
    if increase_percent is not None:
        args.extend(["--increase-percent", str(increase_percent)])
    if calculate_by is not None:
        args.extend(["--calculate-by", calculate_by])
    if context_coverage is not None:
        args.extend(["--context-coverage", str(context_coverage)])
    if scope:
        for spec in scope:
            args.extend(["--scope", spec])
    if dry_run:
        args.append("--dry-run")

    runner = get_runner()
    return runner.run_json(args)
