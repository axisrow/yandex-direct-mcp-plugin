"""MCP tools for agency client management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors


@mcp.tool()
@handle_cli_errors
def agency_clients_list(login: str | None = None) -> list[dict]:
    """List agency clients.

    Args:
        login: Optional agency login to filter by.
    """
    runner = get_runner()
    cmd = ["agencyclients", "get", "--format", "json"]
    if login is not None:
        cmd.extend(["--login", login])

    result = runner.run_json(cmd)
    return result


@mcp.tool()
@handle_cli_errors
def agency_clients_add(login: str, client_info: str) -> dict:
    """Add a client to an agency.

    Args:
        login: Agency login.
        client_info: JSON string containing client information.
    """
    runner = get_runner()
    result = runner.run_json(
        [
            "agencyclients",
            "add",
            "--login",
            login,
            "--client-info",
            client_info,
            "--format",
            "json",
        ]
    )
    return result


@mcp.tool()
@handle_cli_errors
def agency_clients_delete(login: str, client_login: str) -> dict:
    """Remove a client from an agency.

    Args:
        login: Agency login.
        client_login: Client login to remove.
    """
    runner = get_runner()
    result = runner.run_json(
        [
            "agencyclients",
            "delete",
            "--login",
            login,
            "--client-login",
            client_login,
            "--format",
            "json",
        ]
    )
    return result
