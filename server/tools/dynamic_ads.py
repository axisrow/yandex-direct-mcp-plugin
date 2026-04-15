"""MCP tools for dynamic ad (webpage) management."""

import json

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import run_single_id_batch


@mcp.tool(name="dynamicads_get")
@handle_cli_errors
def dynamic_ads_list(ad_group_ids: str) -> list[dict] | dict:
    """List dynamic ad targets (webpages).

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
            "dynamicads",
            "get",
            "--adgroup-ids",
            normalized_ad_group_ids,
            "--format",
            "json",
        ]
    )


@mcp.tool(name="dynamicads_add")
@handle_cli_errors
def dynamic_ads_add(ad_group_id: str, target_data: str | dict) -> dict:
    """Add a dynamic ad target (webpage).

    Args:
        ad_group_id: Ad group ID.
        target_data: JSON string with target data (must include Name and Conditions).
    """
    runner = get_runner()
    json_str = json.dumps(target_data) if isinstance(target_data, dict) else target_data
    return runner.run_json(
        [
            "dynamicads",
            "add",
            "--adgroup-id",
            ad_group_id,
            "--json",
            json_str,
        ]
    )


@handle_cli_errors
def dynamic_ads_update(id: str, extra_json: str | dict) -> dict:
    """Internal-only legacy helper for dynamic ad target updates.

    Kept for direct Python callers/tests-only compatibility and still wrapped
    in ``handle_cli_errors`` so those internal callers get the same structured
    error payloads as public tools. It is intentionally not registered as a
    public MCP tool because the current direct-cli contract does not expose
    the ``direct dynamicads update`` subcommand.

    Args:
        id: Target ID.
        extra_json: JSON string with fields to update.
    """
    runner = get_runner()
    json_str = json.dumps(extra_json) if isinstance(extra_json, dict) else extra_json
    return runner.run_json(["dynamicads", "update", "--id", id, "--json", json_str])


@mcp.tool(name="dynamicads_delete")
@handle_cli_errors
def dynamic_ads_delete(id: str) -> dict:
    """Delete a dynamic ad target (webpage).

    Args:
        id: Target ID.
    """
    runner = get_runner()
    return runner.run_json(["dynamicads", "delete", "--id", id])


@mcp.tool(name="dynamicads_suspend")
@handle_cli_errors
def dynamic_ads_suspend(ids: str) -> dict:
    """Suspend dynamic ad targets."""
    return run_single_id_batch(get_runner(), "dynamicads", "suspend", ids)


@mcp.tool(name="dynamicads_resume")
@handle_cli_errors
def dynamic_ads_resume(ids: str) -> dict:
    """Resume dynamic ad targets."""
    return run_single_id_batch(get_runner(), "dynamicads", "resume", ids)


@mcp.tool(name="dynamicads_set_bids")
@handle_cli_errors
def dynamic_ads_set_bids(
    id: str | None = None,
    ad_group_id: str | None = None,
    campaign_id: str | None = None,
    bid: str | None = None,
    context_bid: str | None = None,
    priority: str | None = None,
) -> dict:
    """Set dynamic ad target bids."""
    if not any((id, ad_group_id, campaign_id)):
        return ToolError(
            error="missing_target_scope",
            message="Provide at least one of: id, ad_group_id, campaign_id",
        ).__dict__
    if not any((bid, context_bid, priority)):
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one of: bid, context_bid, priority",
        ).__dict__

    args = ["dynamicads", "set-bids"]
    if id is not None:
        args.extend(["--id", id])
    if ad_group_id is not None:
        args.extend(["--adgroup-id", ad_group_id])
    if campaign_id is not None:
        args.extend(["--campaign-id", campaign_id])
    if bid is not None:
        args.extend(["--bid", bid])
    if context_bid is not None:
        args.extend(["--context-bid", context_bid])
    if priority is not None:
        args.extend(["--priority", priority])

    runner = get_runner()
    return runner.run_json(args)
