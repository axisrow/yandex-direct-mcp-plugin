"""MCP tools for dynamic ad targets (legacy aliases).

These tools wrap the ``dynamictargets`` CLI subcommand, which is an alias
for ``dynamicads``.  Prefer the canonical wrappers in ``dynamic_ads.py``
— the tools here are kept for backward compatibility with existing
skill/prompt references.
"""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors

from server.tools.helpers import check_batch_limit


@mcp.tool()
@handle_cli_errors
def dynamic_targets_list(ad_group_ids: str | None = None) -> list[dict] | dict:
    """List dynamic ad targets.

    Args:
        ad_group_ids: Comma-separated ad group IDs (optional, max 10).
    """
    if ad_group_ids is not None:
        batch_error = check_batch_limit(ad_group_ids)
        if batch_error:
            return batch_error.__dict__

    args = ["dynamictargets", "get", "--format", "json"]
    if ad_group_ids:
        args.extend(["--adgroup-ids", ad_group_ids])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def dynamic_targets_add(ad_group_id: str, target_data: str) -> dict:
    """Add a dynamic ad target.

    Args:
        ad_group_id: Ad group ID.
        target_data: JSON string with target data (must include Name and Conditions).
    """
    runner = get_runner()
    return runner.run_json(
        [
            "dynamictargets",
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
def dynamic_targets_update(id: str, extra_json: str) -> dict:
    """Update a dynamic ad target.

    Args:
        id: Target ID.
        extra_json: JSON string with fields to update.
    """
    runner = get_runner()
    return runner.run_json(
        [
            "dynamictargets",
            "update",
            "--id",
            id,
            "--json",
            extra_json,
            "--format",
            "json",
        ]
    )


@mcp.tool()
@handle_cli_errors
def dynamic_targets_delete(ids: str) -> dict:
    """Delete dynamic ad targets.

    Args:
        ids: Comma-separated target IDs (max 10).
    """
    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(
        ["dynamictargets", "delete", "--id", ids, "--format", "json"]
    )
    return result
