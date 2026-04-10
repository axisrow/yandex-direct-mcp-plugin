"""MCP tools for business management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors


@mcp.tool()
@handle_cli_errors
def businesses_list(ids: str | None = None) -> list[dict] | dict:
    """List businesses.

    Args:
        ids: Comma-separated business IDs (optional).
    """
    args = ["businesses", "get", "--format", "json"]
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        args.extend(["--ids", normalized_ids])
    runner = get_runner()
    return runner.run_json(args)
