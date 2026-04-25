"""MCP tools for smart ad target management."""

import json

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import run_single_id_batch


@mcp.tool(name="smartadtargets_get")
@handle_cli_errors
def smart_ad_targets_list(ad_group_ids: str) -> list[dict] | dict:
    """List smart ad targets.

    Args:
        ad_group_ids: Comma-separated ad group IDs.
    """
    normalized_ad_group_ids = ad_group_ids.strip()
    if not normalized_ad_group_ids:
        return ToolError(
            error="missing_ad_group_ids",
            message="Provide at least one ad group ID.",
        ).__dict__
    runner = get_runner()
    return runner.run_json(
        [
            "smartadtargets",
            "get",
            "--adgroup-ids",
            normalized_ad_group_ids,
            "--format",
            "json",
        ]
    )


@mcp.tool(name="smartadtargets_add")
@handle_cli_errors
def smart_ad_targets_add(
    ad_group_id: int, target_type: str, extra_json: str | dict | None = None
) -> dict:
    """Add a smart ad target.

    Args:
        ad_group_id: Ad group ID.
        target_type: Target type.
        extra_json: Optional JSON string with additional parameters. Any
            average-cpc / average-cpa fields inside this JSON are micro-units
            (RUB × 1,000,000).
    """
    args = [
        "smartadtargets",
        "add",
        "--adgroup-id",
        str(ad_group_id),
        "--type",
        target_type,
    ]
    if extra_json:
        json_str = (
            json.dumps(extra_json) if isinstance(extra_json, dict) else extra_json
        )
        args.extend(["--json", json_str])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(name="smartadtargets_update")
@handle_cli_errors
def smart_ad_targets_update(
    id: int, target_type: str | None = None, extra_json: str | dict | None = None
) -> dict:
    """Update a smart ad target.

    Args:
        id: Target ID.
        target_type: Optional target type.
        extra_json: JSON string with fields to update. Any average-cpc /
            average-cpa fields inside this JSON are micro-units (RUB × 1,000,000).
    """
    if not any((target_type, extra_json)):
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one of: target_type, extra_json",
        ).__dict__

    args = ["smartadtargets", "update", "--id", str(id)]
    if target_type:
        args.extend(["--type", target_type])
    if extra_json:
        json_str = (
            json.dumps(extra_json) if isinstance(extra_json, dict) else extra_json
        )
        args.extend(["--json", json_str])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(name="smartadtargets_delete")
@handle_cli_errors
def smart_ad_targets_delete(id: int) -> dict:
    """Delete a smart ad target.

    Args:
        id: Target ID.
    """
    runner = get_runner()
    return runner.run_json(["smartadtargets", "delete", "--id", str(id)])


@mcp.tool(name="smartadtargets_suspend")
@handle_cli_errors
def smart_ad_targets_suspend(ids: str) -> dict:
    """Suspend smart ad targets."""
    return run_single_id_batch(get_runner(), "smartadtargets", "suspend", ids)


@mcp.tool(name="smartadtargets_resume")
@handle_cli_errors
def smart_ad_targets_resume(ids: str) -> dict:
    """Resume smart ad targets."""
    return run_single_id_batch(get_runner(), "smartadtargets", "resume", ids)


@mcp.tool(name="smartadtargets_set_bids")
@handle_cli_errors
def smart_ad_targets_set_bids(
    id: int | None = None,
    ad_group_id: int | None = None,
    campaign_id: int | None = None,
    average_cpc: int | None = None,
    average_cpa: int | None = None,
    priority: str | None = None,
) -> dict:
    """Set smart ad target bids.

    Args:
        id: Target ID.
        ad_group_id: Ad group ID.
        campaign_id: Campaign ID.
        average_cpc: Optional average CPC in micro-units (RUB × 1,000,000); CLI 0.2.10+
            rejects values 0 < x < 100_000 with a "did you mean × 1_000_000" hint.
        average_cpa: Optional average CPA in micro-units (same rules as `average_cpc`).
        priority: Strategy priority.
    """
    if id is None and ad_group_id is None and campaign_id is None:
        return ToolError(
            error="missing_target_scope",
            message="Provide at least one of: id, ad_group_id, campaign_id",
        ).__dict__
    if average_cpc is None and average_cpa is None and priority is None:
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one of: average_cpc, average_cpa, priority",
        ).__dict__

    args = ["smartadtargets", "set-bids"]
    if id is not None:
        args.extend(["--id", str(id)])
    if ad_group_id is not None:
        args.extend(["--adgroup-id", str(ad_group_id)])
    if campaign_id is not None:
        args.extend(["--campaign-id", str(campaign_id)])
    if average_cpc is not None:
        args.extend(["--average-cpc", str(average_cpc)])
    if average_cpa is not None:
        args.extend(["--average-cpa", str(average_cpa)])
    if priority is not None:
        args.extend(["--priority", priority])

    runner = get_runner()
    return runner.run_json(args)
