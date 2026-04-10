"""MCP tools for client management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors


@mcp.tool()
@handle_cli_errors
def clients_get(ids: str | None = None) -> dict:
    """Get client information.

    Args:
        ids: Comma-separated client IDs (optional).
    """
    runner = get_runner()
    cmd = ["clients", "get", "--format", "json"]
    if ids is not None:
        cmd.extend(["--ids", ids])

    result = runner.run_json(cmd)
    return result


@mcp.tool()
@handle_cli_errors
def clients_update(client_id: str, extra_json: str) -> dict:
    """Update client information.

    Args:
        client_id: Client ID to update.
        extra_json: JSON string containing fields to update.
    """
    runner = get_runner()
    result = runner.run_json(
        [
            "clients",
            "update",
            "--client-id",
            client_id,
            "--json",
            extra_json,
        ]
    )
    return result
