"""MCP tools for keyword research."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors


@mcp.tool(name="keywordsresearch_has_search_volume")
@handle_cli_errors
def keywords_has_volume(keywords: str, region_id: str | None = None) -> dict:
    """Check if keywords have search volume.

    Args:
        keywords: Comma-separated keywords to check.
        region_id: Optional region ID for geo-targeted search volume.
    """
    runner = get_runner()
    args = [
        "keywordsresearch",
        "has-search-volume",
        "--keywords",
        keywords,
        "--format",
        "json",
    ]
    if region_id is not None:
        args.extend(["--region-id", region_id])
    return runner.run_json(args)


@mcp.tool(name="keywordsresearch_deduplicate")
@handle_cli_errors
def keywords_deduplicate(keywords: str) -> dict:
    """Deduplicate keywords.

    Args:
        keywords: Comma-separated keywords to deduplicate.
    """
    runner = get_runner()
    return runner.run_json(
        ["keywordsresearch", "deduplicate", "--keywords", keywords, "--format", "json"]
    )
