"""MCP tools for client management."""

import json

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
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        cmd.extend(["--ids", normalized_ids])

    result = runner.run_json(cmd)
    return result


@mcp.tool()
@handle_cli_errors
def clients_update(client_id: int, extra_json: str | dict) -> dict:
    """Update client information.

    Args:
        client_id: Client ID to update.
        extra_json: JSON string containing fields to update.
    """
    runner = get_runner()
    json_str = json.dumps(extra_json) if isinstance(extra_json, dict) else extra_json
    result = runner.run_json(
        [
            "clients",
            "update",
            "--client-id",
            str(client_id),
            "--json",
            json_str,
        ]
    )
    return result
