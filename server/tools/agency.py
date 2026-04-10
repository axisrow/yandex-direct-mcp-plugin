"""MCP tools for agency client management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors


@mcp.tool()
@handle_cli_errors
def agency_clients_list(ids: str | None = None) -> list[dict] | dict:
    """List agency clients.

    Args:
        ids: Comma-separated client IDs to filter by (optional).
    """
    runner = get_runner()
    cmd = ["agencyclients", "get", "--format", "json"]
    if ids is not None and ids.strip():
        cmd.extend(["--ids", ids])

    result = runner.run_json(cmd)
    return result


@mcp.tool()
@handle_cli_errors
def agency_clients_add(client_json: str) -> dict:
    """Add a client to an agency.

    Args:
        client_json: JSON string containing client information.
    """
    runner = get_runner()
    result = runner.run_json(["agencyclients", "add", "--json", client_json])
    return result


@mcp.tool()
@handle_cli_errors
def agency_clients_delete(id: str) -> dict:
    """Remove a client from an agency.

    Note: The Yandex Direct API does not actually support deleting
    agency clients. This tool is kept for completeness.

    Args:
        id: Client ID to remove.
    """
    runner = get_runner()
    result = runner.run_json(["agencyclients", "delete", "--id", id])
    return result
