"""MCP tools for dynamic target management."""

import json

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors


@mcp.tool()
@handle_cli_errors
def dynamic_targets_list(ad_group_ids: str) -> list[dict] | dict:
    """List dynamic targets for specified ad groups.

    Args:
        ad_group_ids: Comma-separated ad group IDs (max 10).
    """
    from server.tools.helpers import check_batch_limit

    batch_error = check_batch_limit(ad_group_ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(
        ["dynamictargets", "get", "--ad-group-ids", ad_group_ids, "--format", "json"]
    )
    return result


@mcp.tool()
@handle_cli_errors
def dynamic_targets_add(ad_group_id: str, conditions: str) -> dict:
    """Add a dynamic target to an ad group.

    Args:
        ad_group_id: Ad group ID to add target to.
        conditions: JSON string with dynamic target conditions.
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
            "dynamictargets",
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
def dynamic_targets_update(id: str, conditions: str | None = None) -> dict:
    """Update a dynamic target.

    Args:
        id: Dynamic target ID to update.
        conditions: JSON string with new conditions (optional).
    """
    if conditions is None:
        from server.tools import ToolError

        return ToolError(
            error="nothing_to_update",
            message="At least one field (conditions) must be provided for update",
        ).__dict__

    runner = get_runner()
    result = runner.run_json(
        [
            "dynamictargets",
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
def dynamic_targets_delete(ids: str) -> dict:
    """Delete dynamic targets.

    Args:
        ids: Comma-separated dynamic target IDs (max 10).
    """
    from server.tools.helpers import check_batch_limit

    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(
        ["dynamictargets", "delete", "--ids", ids, "--format", "json"]
    )
    return result
