"""MCP tools for dynamic feed ad target management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit, run_single_id_batch


@mcp.tool(name="dynamicfeedadtargets_get")
@handle_cli_errors
def dynamic_feed_ad_targets_list(
    ids: str | None = None,
    ad_group_ids: str | None = None,
    campaign_ids: str | None = None,
) -> list[dict] | dict:
    """List dynamic feed ad targets.

    Args:
        ids: Comma-separated target IDs (optional, max 10).
        ad_group_ids: Comma-separated ad group IDs (optional, max 10).
        campaign_ids: Comma-separated campaign IDs (optional, max 10).
    """
    args = ["dynamicfeedadtargets", "get", "--format", "json"]
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        batch_error = check_batch_limit(normalized_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--ids", normalized_ids])
    normalized_ad_group_ids = ad_group_ids.strip() if ad_group_ids is not None else None
    if normalized_ad_group_ids:
        batch_error = check_batch_limit(normalized_ad_group_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--adgroup-ids", normalized_ad_group_ids])
    normalized_campaign_ids = campaign_ids.strip() if campaign_ids is not None else None
    if normalized_campaign_ids:
        batch_error = check_batch_limit(normalized_campaign_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--campaign-ids", normalized_campaign_ids])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(name="dynamicfeedadtargets_add")
@handle_cli_errors
def dynamic_feed_ad_targets_add(
    ad_group_id: int,
    name: str,
    condition: str | None = None,
    bid: int | None = None,
    context_bid: int | None = None,
    available_items_only: str | None = None,
) -> dict:
    """Add a dynamic feed ad target.

    Args:
        ad_group_id: Ad group ID.
        name: Target name.
        condition: Condition spec (e.g. "OPERAND:OPERATOR:ARG1|ARG2").
        bid: Optional search bid in micro-units (RUB × 1,000,000); CLI 0.2.10+
            rejects values 0 < x < 100_000 with a "did you mean × 1_000_000" hint.
        context_bid: Optional context bid in micro-units (same rules as `bid`).
        available_items_only: Restrict to currently available feed items
            ("yes" / "no").
    """
    args = [
        "dynamicfeedadtargets",
        "add",
        "--adgroup-id",
        str(ad_group_id),
        "--name",
        name,
    ]
    if condition is not None:
        args.extend(["--condition", condition])
    if bid is not None:
        args.extend(["--bid", str(bid)])
    if context_bid is not None:
        args.extend(["--context-bid", str(context_bid)])
    if available_items_only is not None:
        args.extend(["--available-items-only", available_items_only])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(name="dynamicfeedadtargets_delete")
@handle_cli_errors
def dynamic_feed_ad_targets_delete(id: int) -> dict:
    """Delete a dynamic feed ad target.

    Args:
        id: Target ID.
    """
    runner = get_runner()
    return runner.run_json(["dynamicfeedadtargets", "delete", "--id", str(id)])


@mcp.tool(name="dynamicfeedadtargets_suspend")
@handle_cli_errors
def dynamic_feed_ad_targets_suspend(ids: str) -> dict:
    """Suspend dynamic feed ad targets.

    Args:
        ids: Comma-separated target IDs (max 10).
    """
    return run_single_id_batch(get_runner(), "dynamicfeedadtargets", "suspend", ids)


@mcp.tool(name="dynamicfeedadtargets_resume")
@handle_cli_errors
def dynamic_feed_ad_targets_resume(ids: str) -> dict:
    """Resume dynamic feed ad targets.

    Args:
        ids: Comma-separated target IDs (max 10).
    """
    return run_single_id_batch(get_runner(), "dynamicfeedadtargets", "resume", ids)


@mcp.tool(name="dynamicfeedadtargets_set_bids")
@handle_cli_errors
def dynamic_feed_ad_targets_set_bids(
    id: int | None = None,
    ad_group_id: int | None = None,
    campaign_id: int | None = None,
    bid: int | None = None,
    context_bid: int | None = None,
) -> dict:
    """Set dynamic feed ad target bids.

    Args:
        id: Target ID.
        ad_group_id: Ad group ID.
        campaign_id: Campaign ID.
        bid: Optional search bid in micro-units (RUB × 1,000,000); CLI 0.2.10+
            rejects values 0 < x < 100_000 with a "did you mean × 1_000_000" hint.
        context_bid: Optional context bid in micro-units (same rules as `bid`).
    """
    if id is None and ad_group_id is None and campaign_id is None:
        return ToolError(
            error="missing_target_scope",
            message="Provide at least one of: id, ad_group_id, campaign_id",
        ).__dict__
    if bid is None and context_bid is None:
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one of: bid, context_bid",
        ).__dict__

    args = ["dynamicfeedadtargets", "set-bids"]
    if id is not None:
        args.extend(["--id", str(id)])
    if ad_group_id is not None:
        args.extend(["--adgroup-id", str(ad_group_id)])
    if campaign_id is not None:
        args.extend(["--campaign-id", str(campaign_id)])
    if bid is not None:
        args.extend(["--bid", str(bid)])
    if context_bid is not None:
        args.extend(["--context-bid", str(context_bid)])
    runner = get_runner()
    return runner.run_json(args)
