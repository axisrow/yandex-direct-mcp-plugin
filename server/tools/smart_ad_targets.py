"""MCP tools for smart ad target management."""

import json

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors


@mcp.tool()
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


@mcp.tool()
@handle_cli_errors
def smart_ad_targets_add(
    ad_group_id: str, target_type: str, extra_json: str | dict | None = None
) -> dict:
    """Add a smart ad target.

    Args:
        ad_group_id: Ad group ID.
        target_type: Target type.
        extra_json: Optional JSON string with additional parameters.
    """
    args = ["smartadtargets", "add", "--adgroup-id", ad_group_id, "--type", target_type]
    if extra_json:
        json_str = (
            json.dumps(extra_json) if isinstance(extra_json, dict) else extra_json
        )
        args.extend(["--json", json_str])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def smart_ad_targets_update(
    id: str, target_type: str | None = None, extra_json: str | dict | None = None
) -> dict:
    """Update a smart ad target.

    Args:
        id: Target ID.
        target_type: Optional target type.
        extra_json: JSON string with fields to update.
    """
    if not any((target_type, extra_json)):
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one of: target_type, extra_json",
        ).__dict__

    args = ["smartadtargets", "update", "--id", id]
    if target_type:
        args.extend(["--type", target_type])
    if extra_json:
        json_str = (
            json.dumps(extra_json) if isinstance(extra_json, dict) else extra_json
        )
        args.extend(["--json", json_str])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def smart_ad_targets_delete(id: str) -> dict:
    """Delete a smart ad target.

    Args:
        id: Target ID.
    """
    runner = get_runner()
    return runner.run_json(["smartadtargets", "delete", "--id", id])
