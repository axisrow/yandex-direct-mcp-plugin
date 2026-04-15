"""MCP tools for ad video management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors


@mcp.tool(name="advideos_get")
@handle_cli_errors
def advideos_get(ids: str | None = None) -> dict:
    """Get ad videos.

    Args:
        ids: Comma-separated video IDs (optional).
    """
    args = ["advideos", "get", "--format", "json"]
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        args.extend(["--ids", normalized_ids])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(name="advideos_add")
@handle_cli_errors
def advideos_add(
    url: str | None = None,
    video_data: str | None = None,
    name: str | None = None,
) -> dict:
    """Add an ad video.

    Args:
        url: Video URL.
        video_data: Base64-encoded video payload.
        name: Optional video name.
    """
    args = ["advideos", "add"]
    if bool(url) == bool(video_data):
        return ToolError(
            error="invalid_video_source",
            message="Provide exactly one of: url, video_data",
        ).__dict__

    if url is not None:
        args.extend(["--url", url])
    if video_data is not None:
        args.extend(["--video-data", video_data])
    if name is not None:
        args.extend(["--name", name])

    runner = get_runner()
    return runner.run_json(args)
