"""MCP tools for turbo pages management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors


@mcp.tool(
    name="turbopages_get",
    description="List turbo pages (fast mobile landing pages built in Yandex.Direct), optionally filtered by IDs or bound hrefs. Read-only. Call tool_help('turbopages_get') for parameters.",
)
@handle_cli_errors
def turbo_pages_list(
    ids: str | None = None,
    bound_with_hrefs: str | None = None,
    limit: int | None = None,
    fetch_all: bool = False,
    fields: str | None = None,
    dry_run: bool = False,
) -> dict:
    """List turbo pages.

    Args:
        ids: Comma-separated turbo page IDs.
        bound_with_hrefs: Comma-separated hrefs bound with Turbo Pages.
        limit: Limit number of results.
        fetch_all: Fetch all pages.
        fields: Comma-separated field names.
        dry_run: Show the direct request without sending it.
    """
    args = ["turbopages", "get", "--format", "json"]
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        args.extend(["--ids", normalized_ids])
    if bound_with_hrefs is not None:
        normalized = bound_with_hrefs.strip()
        if normalized:
            args.extend(["--bound-with-hrefs", normalized])
    if limit is not None:
        args.extend(["--limit", str(limit)])
    if fetch_all:
        args.append("--fetch-all")
    if fields is not None:
        args.extend(["--fields", fields])
    if dry_run:
        args.append("--dry-run")
    return get_runner().run_json(args)
