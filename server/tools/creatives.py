"""MCP tools for creatives management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors


@mcp.tool()
@handle_cli_errors
def creatives_list(ids: str) -> dict:
    """List creatives by IDs.

    Args:
        ids: Comma-separated creative IDs.
    """
    runner = get_runner()
    return runner.run_json(["creatives", "get", "--ids", ids, "--format", "json"])
