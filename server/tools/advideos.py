"""MCP tools for ad video management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import (
    append_pagination,
    normalize_optional_str,
    tool_error_dict,
)


@mcp.tool(
    name="advideos_get",
    description="Get ad videos (video assets used in video/multimedia ads) by required IDs. Use advideos_add to upload a new video. Call tool_help('advideos_get') for parameters.",
)
@handle_cli_errors
def advideos_get(
    ids: str,
    limit: int | None = None,
    fetch_all: bool = False,
    fields: str | None = None,
) -> dict:
    """Get ad videos.

    CLI 0.3.8 `advideos get` requires `--ids` (there is no full-list mode).

    Args:
        ids: Comma-separated video IDs (required).
        limit: Limit number of results.
        fetch_all: Fetch all pages.
        fields: Comma-separated field names.
    """
    normalized_ids = ids.strip()
    if not normalized_ids:
        return tool_error_dict(
            ToolError(
                error="missing_ids",
                message="Provide at least one video ID.",
            )
        )

    args = ["advideos", "get", "--format", "json", "--ids", normalized_ids]
    append_pagination(args, limit, fetch_all, fields)
    return get_runner().run_json(args)


@mcp.tool(
    name="advideos_add",
    description="Add an ad video from a URL, base64 data, or local file (exactly one source). Use advideos_get to list existing videos. Call tool_help('advideos_add') for parameters.",
)
@handle_cli_errors
def advideos_add(
    url: str | None = None,
    video_data: str | None = None,
    video_file: str | None = None,
    name: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Add an ad video.

    Args:
        url: Video URL (mutually exclusive with video_data / video_file).
        video_data: Base64-encoded video binary.
        video_file: Path to a video file (CLI base64-encodes it).
        name: Optional video name.
        dry_run: Show the direct request without sending it.
    """
    # Match the CLI's truthiness semantics: it selects the source with
    # `if url: ... elif video_data: ...`, treating blank strings as absent.
    # Normalize blanks to None first so an LLM filling unused optional params
    # with "" doesn't trip a spurious conflict or emit `--url ""`. (#170-15)
    url = normalize_optional_str(url)
    video_data = normalize_optional_str(video_data)
    video_file = normalize_optional_str(video_file)
    sources = [s for s in (url, video_data, video_file) if s is not None]
    if len(sources) != 1:
        return tool_error_dict(
            ToolError(
                error="invalid_video_source",
                message="Provide exactly one of: url, video_data, video_file",
            )
        )

    args = ["advideos", "add"]
    if url is not None:
        args.extend(["--url", url])
    if video_data is not None:
        args.extend(["--video-data", video_data])
    if video_file is not None:
        args.extend(["--video-file", video_file])
    if name is not None:
        args.extend(["--name", name])
    if dry_run:
        args.append("--dry-run")

    runner = get_runner()
    return runner.run_json(args)
