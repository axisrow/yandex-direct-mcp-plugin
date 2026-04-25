"""MCP tools for bid management."""

import json

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit


@mcp.tool(name="bids_get")
@handle_cli_errors
def bids_list(
    campaign_ids: str | None = None,
    ad_group_ids: str | None = None,
    keyword_ids: str | None = None,
) -> list[dict] | dict:
    """List bids.

    Args:
        campaign_ids: Comma-separated campaign IDs (optional, max 10).
        ad_group_ids: Comma-separated ad group IDs (optional, max 10).
        keyword_ids: Comma-separated keyword IDs (optional, max 10).
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

    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(name="bids_set")
@handle_cli_errors
def bids_set(
    campaign_id: int,
    bid: int | None = None,
    extra_json: str | dict | None = None,
) -> dict:
    """Set bid for a campaign.

    Args:
        campaign_id: Campaign ID.
        bid: Bid in micro-units (RUB × 1,000,000); CLI 0.2.10+ rejects values
            0 < x < 100_000 with a "did you mean × 1_000_000" hint.
        extra_json: Optional JSON string with additional parameters.
    """
    if bid is None and extra_json is None:
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one of: bid, extra_json",
        ).__dict__

    args = ["bids", "set", "--campaign-id", str(campaign_id)]
    if bid is not None:
        args.extend(["--bid", str(bid)])
    if extra_json is not None:
        json_str = (
            json.dumps(extra_json) if isinstance(extra_json, dict) else extra_json
        )
        args.extend(["--json", json_str])
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
    increase_percent: str | None = None,
    calculate_by: str | None = None,
    context_coverage: str | None = None,
    scope: str | None = None,
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
    """
    if not any((campaign_id, ad_group_id, keyword_id)):
        return ToolError(
            error="missing_target_scope",
            message="Provide at least one of: campaign_id, ad_group_id, keyword_id",
        ).__dict__
    if not any(
        (
            max_bid,
            position,
            increase_percent,
            calculate_by,
            context_coverage,
            scope,
        )
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
        args.extend(["--increase-percent", increase_percent])
    if calculate_by is not None:
        args.extend(["--calculate-by", calculate_by])
    if context_coverage is not None:
        args.extend(["--context-coverage", context_coverage])
    if scope is not None:
        args.extend(["--scope", scope])

    runner = get_runner()
    return runner.run_json(args)
