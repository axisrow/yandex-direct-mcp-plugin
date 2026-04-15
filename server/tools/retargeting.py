"""MCP tools for retargeting list management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import run_single_id_batch


@mcp.tool(name="retargeting_get")
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


@mcp.tool(name="retargeting_add")
@handle_cli_errors
def retargeting_add(
    name: str,
    list_type: str,
    rule: str | None = None,
) -> dict:
    """Add a retargeting list.

    Args:
        name: Name for the retargeting list.
        list_type: List type (e.g. "AUDIENCE_SEGMENT").
        rule: JSON string with targeting rule conditions (e.g. {"conditions": [...]}).
    """
    args = [
        "retargeting",
        "add",
        "--name",
        name,
        "--type",
        list_type,
    ]
    if rule is not None:
        args.extend(["--rule", rule])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(name="retargeting_delete")
@handle_cli_errors
def retargeting_delete(ids: str) -> dict:
    """Delete retargeting lists.

    Args:
        ids: Comma-separated retargeting list IDs (max 10).
    """
    return run_single_id_batch(get_runner(), "retargeting", "delete", ids)


@mcp.tool(name="retargeting_update")
@handle_cli_errors
def retargeting_update(
    id: str,
    name: str | None = None,
    list_type: str | None = None,
    rule: str | None = None,
) -> dict:
    """Update a retargeting list.

    Args:
        id: Retargeting list ID to update.
        name: New name for the list (optional).
        list_type: New list type, e.g. "AUDIENCE_SEGMENT" (optional).
        rule: JSON string with updated targeting rule conditions (optional).
    """
    if not any((name, list_type, rule)):
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one of: name, list_type, rule",
        ).__dict__

    args = ["retargeting", "update", "--id", id]
    if name is not None:
        args.extend(["--name", name])
    if list_type is not None:
        args.extend(["--type", list_type])
    if rule is not None:
        args.extend(["--rule", rule])

    runner = get_runner()
    return runner.run_json(args)
