"""MCP tools for retargeting list management."""

import json

from server.main import mcp
from server.tools import get_runner, handle_cli_errors
from server.tools.helpers import run_single_id_batch


@mcp.tool()
@handle_cli_errors
def retargeting_list(
    ids: str | None = None, types: str | None = None
) -> list[dict] | dict:
    """List retargeting lists.

    Args:
        ids: Comma-separated retargeting list IDs (optional).
        types: Comma-separated types to filter by (optional).
    """
    args = ["retargeting", "get", "--format", "json"]
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        args.extend(["--ids", normalized_ids])
    normalized_types = types.strip() if types is not None else None
    if normalized_types:
        args.extend(["--types", normalized_types])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def retargeting_add(
    name: str,
    list_type: str,
    extra_json: str | dict | None = None,
) -> dict:
    """Add a retargeting list.

    Args:
        name: Name for the retargeting list.
        list_type: List type (e.g. "AUDIENCE_SEGMENT").
        extra_json: Optional JSON string with additional parameters.
    """
    args = [
        "retargeting",
        "add",
        "--name",
        name,
        "--type",
        list_type,
    ]
    if extra_json is not None:
        json_str = (
            json.dumps(extra_json) if isinstance(extra_json, dict) else extra_json
        )
        args.extend(["--json", json_str])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def retargeting_delete(ids: str) -> dict:
    """Delete retargeting lists.

    Args:
        ids: Comma-separated retargeting list IDs (max 10).
    """
    return run_single_id_batch(get_runner(), "retargeting", "delete", ids)
