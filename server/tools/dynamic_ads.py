"""MCP tools for dynamic ad (webpage) management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors


@mcp.tool()
@handle_cli_errors
def dynamic_ads_list(ad_group_ids: str) -> list[dict] | dict:
    """List dynamic ad targets (webpages).

    Args:
        ad_group_ids: Comma-separated ad group IDs.
    """
    runner = get_runner()
    return runner.run_json(
        ["dynamicads", "get", "--adgroup-ids", ad_group_ids, "--format", "json"]
    )


@mcp.tool()
@handle_cli_errors
def dynamic_ads_add(ad_group_id: str, target_data: str) -> dict:
    """Add a dynamic ad target (webpage).

    Args:
        ad_group_id: Ad group ID.
        target_data: JSON string with target data (must include Name and Conditions).
    """
    runner = get_runner()
    return runner.run_json(
        [
            "dynamicads",
            "add",
            "--adgroup-id",
            ad_group_id,
            "--json",
            target_data,
            "--format",
            "json",
        ]
    )


@mcp.tool()
@handle_cli_errors
def dynamic_ads_update(id: str, extra_json: str) -> dict:
    """Update a dynamic ad target (webpage).

    Args:
        id: Target ID.
        extra_json: JSON string with fields to update.
    """
    runner = get_runner()
    return runner.run_json(
        ["dynamicads", "update", "--id", id, "--json", extra_json, "--format", "json"]
    )


@mcp.tool()
@handle_cli_errors
def dynamic_ads_delete(id: str) -> dict:
    """Delete a dynamic ad target (webpage).

    Args:
        id: Target ID.
    """
    runner = get_runner()
    return runner.run_json(
        ["dynamicads", "delete", "--id", id, "--format", "json"]
    )
