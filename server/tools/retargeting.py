"""MCP tools for retargeting list management."""

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
    if ids is not None:
        args.extend(["--ids", ids])
    if types is not None:
        args.extend(["--types", types])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def retargeting_add(
    name: str,
    list_type: str,
    extra_json: str | None = None,
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
        args.extend(["--json", extra_json])
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
