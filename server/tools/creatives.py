"""MCP tools for creatives management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors


@mcp.tool(name="creatives_get")
@handle_cli_errors
def creatives_list(ids: str | None = None, campaign_ids: str | None = None) -> dict:
    """List creatives.

    Args:
        ids: Comma-separated creative IDs (optional).
        campaign_ids: Comma-separated campaign IDs (optional).
    """
    args = ["creatives", "get", "--format", "json"]
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        args.extend(["--ids", normalized_ids])
    normalized_campaign_ids = campaign_ids.strip() if campaign_ids is not None else None
    if normalized_campaign_ids:
        args.extend(["--campaign-ids", normalized_campaign_ids])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(name="creatives_add")
@handle_cli_errors
def creatives_add(video_id: str) -> dict:
    """Add a creative.

    Args:
        video_id: Video extension creative video ID.
    """
    runner = get_runner()
    return runner.run_json(["creatives", "add", "--video-id", video_id])
