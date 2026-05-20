"""MCP tools for creatives management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors


@mcp.tool(name="creatives_get")
@handle_cli_errors
def creatives_list(
    ids: str | None = None,
    types: str | None = None,
    limit: int | None = None,
    fetch_all: bool = False,
    fields: str | None = None,
) -> dict:
    """List creatives.

    CLI 0.3.8 `creatives get` accepts `--ids`, `--types`, pagination flags;
    there is no `--campaign-ids` filter.

    Args:
        ids: Comma-separated creative IDs.
        types: Comma-separated creative types.
        limit: Limit number of results.
        fetch_all: Fetch all pages.
        fields: Comma-separated field names.
    """
    args = ["creatives", "get", "--format", "json"]
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        args.extend(["--ids", normalized_ids])
    if types is not None:
        args.extend(["--types", types])
    if limit is not None:
        args.extend(["--limit", str(limit)])
    if fetch_all:
        args.append("--fetch-all")
    if fields is not None:
        args.extend(["--fields", fields])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(name="creatives_add")
@handle_cli_errors
def creatives_add(video_id: str, dry_run: bool = False) -> dict:
    """Add a creative.

    Args:
        video_id: Video extension creative video ID.
        dry_run: Show the direct-cli request without sending it.
    """
    args = ["creatives", "add", "--video-id", video_id]
    if dry_run:
        args.append("--dry-run")
    return get_runner().run_json(args)
