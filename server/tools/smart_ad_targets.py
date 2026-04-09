"""MCP tools for smart ad target management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors


@mcp.tool()
@handle_cli_errors
def smart_ad_targets_list(ad_group_ids: str) -> list[dict] | dict:
    """List smart ad targets.

    Args:
        ad_group_ids: Comma-separated ad group IDs.
    """
    runner = get_runner()
    return runner.run_json(
        ["smartadtargets", "get", "--adgroup-ids", ad_group_ids, "--format", "json"]
    )


@mcp.tool()
@handle_cli_errors
def smart_ad_targets_add(ad_group_id: str, target_type: str, extra_json: str | None = None) -> dict:
    """Add a smart ad target.

    Args:
        ad_group_id: Ad group ID.
        target_type: Target type.
        extra_json: Optional JSON string with additional parameters.
    """
    args = ["smartadtargets", "add", "--adgroup-id", ad_group_id, "--type", target_type]
    if extra_json:
        args.extend(["--json", extra_json])
    args.extend(["--format", "json"])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def smart_ad_targets_update(id: str, extra_json: str | None = None) -> dict:
    """Update a smart ad target.

    Args:
        id: Target ID.
        extra_json: JSON string with fields to update.
    """
    args = ["smartadtargets", "update", "--id", id]
    if extra_json:
        args.extend(["--json", extra_json])
    args.extend(["--format", "json"])
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
    return runner.run_json(
        ["smartadtargets", "delete", "--id", id, "--format", "json"]
    )
