"""Legacy compatibility wrappers for dynamic ad target MCP tools.

These tools preserve historical MCP names used by prompts and skills.
The audited direct-cli surface does not guarantee a working
``dynamictargets`` subcommand, so callers should prefer the canonical
wrappers in ``dynamic_ads.py``.
"""

import json

from server.main import mcp
from server.tools import get_runner, handle_cli_errors

from server.tools.helpers import check_batch_limit, run_single_id_batch


@mcp.tool()
@handle_cli_errors
def dynamic_targets_list(ad_group_ids: str | None = None) -> list[dict] | dict:
    """List dynamic ad targets.

    Args:
        ad_group_ids: Comma-separated ad group IDs (optional, max 10).
    """
    normalized_ad_group_ids = ad_group_ids.strip() if ad_group_ids is not None else None
    if normalized_ad_group_ids:
        batch_error = check_batch_limit(normalized_ad_group_ids)
        if batch_error:
            return batch_error.__dict__

    args = ["dynamicads", "get", "--format", "json"]
    if normalized_ad_group_ids:
        args.extend(["--adgroup-ids", normalized_ad_group_ids])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def dynamic_targets_add(ad_group_id: str, target_data: str | dict) -> dict:
    """Add a dynamic ad target.

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
            "--format",
            "json",
        ]
    )


@mcp.tool()
@handle_cli_errors
def dynamic_targets_update(id: str, extra_json: str | dict) -> dict:
    """Update a dynamic ad target.

    Args:
        id: Target ID.
        extra_json: JSON string with fields to update.
    """
    runner = get_runner()
    json_str = json.dumps(extra_json) if isinstance(extra_json, dict) else extra_json
    return runner.run_json(
        [
            "dynamicads",
            "update",
            "--id",
            id,
            "--json",
            json_str,
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
    return run_single_id_batch(get_runner(), "dynamicads", "delete", ids)
