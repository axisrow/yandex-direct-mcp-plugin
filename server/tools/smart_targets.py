"""MCP tools for smart target management."""

import json

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors

from server.tools.helpers import check_batch_limit


@mcp.tool()
@handle_cli_errors
def smart_targets_list(ad_group_ids: str) -> list[dict] | dict:
    """List smart targets in specified ad groups.

    Args:
        ad_group_ids: Comma-separated ad group IDs (max 10).
    """
    batch_error = check_batch_limit(ad_group_ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    return runner.run_json(
        ["smarttargets", "get", "--ad-group-ids", ad_group_ids, "--format", "json"]
    )


@mcp.tool()
@handle_cli_errors
def smart_targets_add(ad_group_id: str, conditions: str) -> dict:
    """Add smart target to an ad group.

    Args:
        ad_group_id: Ad group ID.
        conditions: JSON string of conditions for the smart target.
    """
    # Validate JSON format
    try:
        json.loads(conditions)
    except json.JSONDecodeError as e:
        return ToolError(
            error="invalid_json",
            message=f"Conditions must be valid JSON. Got: '{conditions}'. Error: {e}",
        ).__dict__

    runner = get_runner()
    result = runner.run_json(
        [
            "smarttargets",
            "add",
            "--ad-group-id",
            ad_group_id,
            "--conditions",
            conditions,
            "--format",
            "json",
        ]
    )
    return result


@mcp.tool()
@handle_cli_errors
def smart_targets_update(id: str, conditions: str | None = None) -> dict:
    """Update smart target.

    Args:
        id: Smart target ID.
        conditions: JSON string of conditions for the smart target (optional).
    """
    if conditions is not None:
        # Validate JSON format
        try:
            json.loads(conditions)
        except json.JSONDecodeError as e:
            return ToolError(
                error="invalid_json",
                message=f"Conditions must be valid JSON. Got: '{conditions}'. Error: {e}",
            ).__dict__

    if conditions is None:
        # Return error if no conditions provided
        return ToolError(
            error="missing_conditions",
            message="Conditions parameter is required for update",
        ).__dict__

    runner = get_runner()
    result = runner.run_json(
        [
            "smarttargets",
            "update",
            "--id",
            id,
            "--conditions",
            conditions,
            "--format",
            "json",
        ]
    )
    return result


@mcp.tool()
@handle_cli_errors
def smart_targets_delete(ids: str) -> dict:
    """Delete smart targets.

    Args:
        ids: Comma-separated smart target IDs (max 10).
    """
    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(["smarttargets", "delete", "--ids", ids, "--format", "json"])
    return result
