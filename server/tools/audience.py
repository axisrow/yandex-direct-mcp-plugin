"""MCP tools for audience target management."""

import json

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit, run_single_id_batch


@mcp.tool(name="audiencetargets_get")
@handle_cli_errors
def audience_targets_list(
    campaign_ids: str | None = None,
    ad_group_ids: str | None = None,
    ids: str | None = None,
) -> list[dict] | dict:
    """List audience targets.

    Args:
        campaign_ids: Comma-separated campaign IDs (optional, max 10).
        ad_group_ids: Comma-separated ad group IDs (optional, max 10).
        ids: Comma-separated audience target IDs (optional, max 10).
    """
    args = ["audiencetargets", "get", "--format", "json"]
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
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        batch_error = check_batch_limit(normalized_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--ids", normalized_ids])

    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(name="audiencetargets_add")
@handle_cli_errors
def audience_targets_add(
    ad_group_id: int,
    retargeting_list_id: int,
    bid: int | None = None,
    extra_json: str | dict | None = None,
) -> dict:
    """Add an audience target to an ad group.

    Args:
        ad_group_id: Ad group ID to add target to.
        retargeting_list_id: Retargeting list ID to target.
        bid: Optional context bid in micro-units (RUB × 1,000,000); CLI 0.2.10+
            rejects values 0 < x < 100_000 with a "did you mean × 1_000_000" hint.
        extra_json: Optional JSON string with additional parameters.
    """
    args = [
        "audiencetargets",
        "add",
        "--adgroup-id",
        str(ad_group_id),
        "--retargeting-list-id",
        str(retargeting_list_id),
    ]
    if bid is not None:
        args.extend(["--bid", str(bid)])
    if extra_json is not None:
        json_str = (
            json.dumps(extra_json) if isinstance(extra_json, dict) else extra_json
        )
        args.extend(["--json", json_str])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(name="audiencetargets_delete")
@handle_cli_errors
def audience_targets_delete(ids: str) -> dict:
    """Delete audience targets.

    Args:
        ids: Comma-separated audience target IDs (max 10).
    """
    return run_single_id_batch(get_runner(), "audiencetargets", "delete", ids)


@mcp.tool(name="audiencetargets_suspend")
@handle_cli_errors
def audience_targets_suspend(ids: str) -> dict:
    """Suspend audience targets.

    Args:
        ids: Comma-separated audience target IDs (max 10).
    """
    return run_single_id_batch(get_runner(), "audiencetargets", "suspend", ids)


@mcp.tool(name="audiencetargets_resume")
@handle_cli_errors
def audience_targets_resume(ids: str) -> dict:
    """Resume suspended audience targets.

    Args:
        ids: Comma-separated audience target IDs (max 10).
    """
    return run_single_id_batch(get_runner(), "audiencetargets", "resume", ids)


@mcp.tool(name="audiencetargets_set_bids")
@handle_cli_errors
def audience_targets_set_bids(
    id: int | None = None,
    ad_group_id: int | None = None,
    campaign_id: int | None = None,
    context_bid: int | None = None,
    priority: str | None = None,
) -> dict:
    """Set audience target bids.

    Args:
        id: Audience target ID.
        ad_group_id: Ad group ID.
        campaign_id: Campaign ID.
        context_bid: Context bid in micro-units (RUB × 1,000,000); CLI 0.2.10+
            rejects values 0 < x < 100_000 with a "did you mean × 1_000_000" hint.
        priority: Strategy priority.
    """
    if not any((id, ad_group_id, campaign_id)):
        return ToolError(
            error="missing_target_scope",
            message="Provide at least one of: id, ad_group_id, campaign_id",
        ).__dict__
    if not any((context_bid, priority)):
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one of: context_bid, priority",
        ).__dict__

    args = ["audiencetargets", "set-bids"]
    if id is not None:
        args.extend(["--id", str(id)])
    if ad_group_id is not None:
        args.extend(["--adgroup-id", str(ad_group_id)])
    if campaign_id is not None:
        args.extend(["--campaign-id", str(campaign_id)])
    if context_bid is not None:
        args.extend(["--context-bid", str(context_bid)])
    if priority is not None:
        args.extend(["--priority", priority])

    runner = get_runner()
    return runner.run_json(args)
