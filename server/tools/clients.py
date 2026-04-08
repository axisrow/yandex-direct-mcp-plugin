"""MCP tools for client management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors


@mcp.tool()
@handle_cli_errors
def clients_get(login: str | None = None) -> dict:
    """Get client information.

    Args:
        login: Optional client login to retrieve specific client info.
    """
    runner = get_runner()
    cmd = ["clients", "get", "--format", "json"]
    if login is not None:
        cmd.extend(["--login", login])

    result = runner.run_json(cmd)
    return result


@mcp.tool()
@handle_cli_errors
def clients_update(login: str, fields: str) -> dict:
    """Update client information.

    Args:
        login: Client login to update.
        fields: JSON string containing fields to update.
    """
    runner = get_runner()
    result = runner.run_json(
        ["clients", "update", "--login", login, "--fields", fields, "--format", "json"]
    )
    return result
