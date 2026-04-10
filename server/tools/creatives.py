"""MCP tools for creatives management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors


@mcp.tool()
@handle_cli_errors
def creatives_list(ids: str | None = None, campaign_ids: str | None = None) -> dict:
    """List creatives.

    Args:
        ids: Comma-separated creative IDs (optional).
        campaign_ids: Comma-separated campaign IDs (optional).
    """
    args = ["creatives", "get", "--format", "json"]
    if ids is not None and ids.strip():
        args.extend(["--ids", ids])
    if campaign_ids is not None and campaign_ids.strip():
        args.extend(["--campaign-ids", campaign_ids])
    runner = get_runner()
    return runner.run_json(args)
