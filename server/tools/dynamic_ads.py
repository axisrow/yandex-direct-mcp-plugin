"""MCP tools for dynamic ad (webpage) management."""

import json

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
@handle_cli_errors
def dynamic_ads_update(id: str, extra_json: str | dict) -> dict:
    """Update a dynamic ad target (webpage).

    Args:
        id: Target ID.
        extra_json: JSON string with fields to update.
    """
    runner = get_runner()
    json_str = json.dumps(extra_json) if isinstance(extra_json, dict) else extra_json
    return runner.run_json(["dynamicads", "update", "--id", id, "--json", json_str])


@mcp.tool()
@handle_cli_errors
def dynamic_ads_delete(id: str) -> dict:
    """Delete a dynamic ad target (webpage).

    Args:
        id: Target ID.
    """
    runner = get_runner()
    return runner.run_json(["dynamicads", "delete", "--id", id])
