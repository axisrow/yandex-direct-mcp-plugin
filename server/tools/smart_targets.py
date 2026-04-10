"""MCP tools for smart ad targets (legacy aliases).

These tools wrap the ``smarttargets`` CLI subcommand, which is an alias
for ``smartadtargets``.  Prefer the canonical wrappers in
``smart_ad_targets.py`` — the tools here are kept for backward
compatibility with existing skill/prompt references.
"""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors

from server.tools.helpers import check_batch_limit


@mcp.tool()
@handle_cli_errors
def smart_targets_list(ad_group_ids: str | None = None) -> list[dict] | dict:
    """List smart ad targets.

    Args:
        ad_group_ids: Comma-separated ad group IDs (optional, max 10).
    """
    if ad_group_ids is not None:
        batch_error = check_batch_limit(ad_group_ids)
        if batch_error:
            return batch_error.__dict__

    args = ["smarttargets", "get", "--format", "json"]
    if ad_group_ids:
        args.extend(["--adgroup-ids", ad_group_ids])
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
        "smarttargets",
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
    args = ["smarttargets", "update", "--id", id]
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
    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(
        ["smarttargets", "delete", "--id", ids, "--format", "json"]
    )
    return result
