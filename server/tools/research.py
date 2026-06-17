"""MCP tools for keyword research."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import tool_error_dict


@mcp.tool(
    name="keywordsresearch_has_search_volume",
    description="Check whether keywords have search volume in given regions. Call tool_help('keywordsresearch_has_search_volume') for parameters.",
)
@handle_cli_errors
def keywords_has_volume(
    keywords: str,
    region_ids: str,
    fields: str | None = None,
) -> dict:
    """Check if keywords have search volume.

    CLI 0.3.8 requires both `--keywords` and `--region-ids` (plural). Use
    "0" for the default account-wide region or e.g. "213" for Moscow.

    Args:
        keywords: Comma-separated keywords to check.
        region_ids: Comma-separated region IDs (required by CLI).
        fields: Comma-separated field names.
    """
    if not keywords.strip():
        return tool_error_dict(
            ToolError(
                error="missing_keywords",
                message="Provide at least one keyword.",
            )
        )
    if not region_ids.strip():
        return tool_error_dict(
            ToolError(
                error="missing_region_ids",
                message="Provide at least one region ID.",
            )
        )
    args = [
        "keywordsresearch",
        "has-search-volume",
        "--keywords",
        keywords,
        "--region-ids",
        region_ids,
        "--format",
        "json",
    ]
    if fields is not None:
        args.extend(["--fields", fields])
    return get_runner().run_json(args)


@mcp.tool(
    name="keywordsresearch_deduplicate",
    description="Deduplicate a list of keywords. Call tool_help('keywordsresearch_deduplicate') for parameters.",
)
@handle_cli_errors
def keywords_deduplicate(keywords: str) -> dict:
    """Deduplicate keywords.

    Args:
        keywords: Comma-separated keywords to deduplicate.
    """
    return get_runner().run_json(
        ["keywordsresearch", "deduplicate", "--keywords", keywords, "--format", "json"]
    )
