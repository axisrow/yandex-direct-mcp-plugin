"""MCP tools for turbo pages management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors


@mcp.tool()
@handle_cli_errors
def turbo_pages_list(ids: str) -> dict:
    """List turbo pages by IDs.

    Args:
        ids: Comma-separated turbo page IDs.
    """
    runner = get_runner()
    return runner.run_json(["turbopages", "get", "--ids", ids, "--format", "json"])
