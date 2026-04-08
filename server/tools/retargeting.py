"""MCP tools for retargeting list management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors


@mcp.tool()
@handle_cli_errors
def retargeting_list(ids: str) -> list[dict]:
    """List retargeting lists.

    Args:
        ids: Comma-separated retargeting list IDs.
    """
    runner = get_runner()
    result = runner.run_json(["retargeting", "get", "--ids", ids, "--format", "json"])
    return result


@mcp.tool()
@handle_cli_errors
def retargeting_add(name: str, rule: str) -> dict:
    """Add a retargeting list.

    Args:
        name: Name for the retargeting list.
        rule: JSON string with retargeting conditions.
    """
    runner = get_runner()
    result = runner.run_json(
        ["retargeting", "add", "--name", name, "--rule", rule, "--format", "json"]
    )
    return result


@mcp.tool()
@handle_cli_errors
def retargeting_delete(ids: str) -> dict:
    """Delete retargeting lists.

    Args:
        ids: Comma-separated retargeting list IDs (max 10).
    """
    from server.tools.helpers import check_batch_limit

    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(["retargeting", "delete", "--ids", ids, "--format", "json"])
    return result
