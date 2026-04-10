"""Legacy compatibility wrappers for smart ad target MCP tools.

These tools preserve historical MCP names used by prompts and skills.
The audited direct-cli surface does not guarantee a working
``smarttargets`` subcommand, so callers should prefer the canonical
wrappers in ``smart_ad_targets.py``.
"""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors

from server.tools.helpers import check_batch_limit, run_single_id_batch


@mcp.tool()
@handle_cli_errors
def smart_targets_list(ad_group_ids: str | None = None) -> list[dict] | dict:
    """List smart ad targets.

    Args:
        ad_group_ids: Comma-separated ad group IDs (optional, max 10).
    """
    normalized_ad_group_ids = ad_group_ids.strip() if ad_group_ids is not None else None
    if normalized_ad_group_ids:
        batch_error = check_batch_limit(normalized_ad_group_ids)
        if batch_error:
            return batch_error.__dict__

    args = ["smartadtargets", "get", "--format", "json"]
    if normalized_ad_group_ids:
        args.extend(["--adgroup-ids", normalized_ad_group_ids])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def smart_targets_add(
    ad_group_id: str, target_type: str, extra_json: str | None = None
) -> dict:
    """Add a smart ad target.

    Args:
        ad_group_id: Ad group ID.
        target_type: Target type (e.g. RETARGETING).
        extra_json: Additional JSON parameters (optional).
    """
    args = [
        "smartadtargets",
        "add",
        "--adgroup-id",
        ad_group_id,
        "--type",
        target_type,
    ]
    if extra_json:
        args.extend(["--json", extra_json])
    args.extend(["--format", "json"])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def smart_targets_update(
    id: str, target_type: str | None = None, extra_json: str | None = None
) -> dict:
    """Update a smart ad target.

    Args:
        id: Target ID.
        target_type: New target type (optional).
        extra_json: JSON string with fields to update (optional).
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
        args.extend(["--json", extra_json])
    args.extend(["--format", "json"])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def smart_targets_delete(ids: str) -> dict:
    """Delete smart ad targets.

    Args:
        ids: Comma-separated target IDs (max 10).
    """
    return run_single_id_batch(get_runner(), "smartadtargets", "delete", ids)
