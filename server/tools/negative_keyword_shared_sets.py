"""MCP tools for negative keyword shared sets management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors


@mcp.tool(
    name="negativekeywordsharedsets_get",
    description="List shared sets of negative keywords reusable across campaigns. Call tool_help('negativekeywordsharedsets_get') for parameters.",
)
@handle_cli_errors
def negative_keyword_shared_sets_list(
    ids: str | None = None,
    limit: int | None = None,
    fetch_all: bool = False,
    fields: str | None = None,
) -> list[dict] | dict:
    """List negative keyword shared sets.

    Args:
        ids: Comma-separated set IDs.
        limit: Limit number of results.
        fetch_all: Fetch all pages.
        fields: Comma-separated field names.
    """
    args = ["negativekeywordsharedsets", "get", "--format", "json"]
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        args.extend(["--ids", normalized_ids])
    if limit is not None:
        args.extend(["--limit", str(limit)])
    if fetch_all:
        args.append("--fetch-all")
    if fields is not None:
        args.extend(["--fields", fields])
    return get_runner().run_json(args)


@mcp.tool(
    name="negativekeywordsharedsets_add",
    description="Create a shared negative keyword set. Call tool_help('negativekeywordsharedsets_add') for parameters.",
)
@handle_cli_errors
def negative_keyword_shared_sets_add(
    name: str, keywords: str, dry_run: bool = False
) -> dict:
    """Add a negative keyword shared set.

    Args:
        name: Set name.
        keywords: Comma-separated negative keywords.
        dry_run: Show the direct request without sending it.
    """
    args = [
        "negativekeywordsharedsets",
        "add",
        "--name",
        name,
        "--keywords",
        keywords,
    ]
    if dry_run:
        args.append("--dry-run")
    return get_runner().run_json(args)


@mcp.tool(
    name="negativekeywordsharedsets_update",
    description="Update a shared negative keyword set's name or keyword list. Call tool_help('negativekeywordsharedsets_update') for parameters.",
)
@handle_cli_errors
def negative_keyword_shared_sets_update(
    id: int,
    name: str | None = None,
    keywords: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Update a negative keyword shared set.

    CLI 0.3.8 dropped --json.

    Args:
        id: Set ID.
        name: New set name.
        keywords: New comma-separated negative keywords.
        dry_run: Show the direct request without sending it.
    """
    if not any((name, keywords)):
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one of: name, keywords",
        ).__dict__

    args = ["negativekeywordsharedsets", "update", "--id", str(id)]
    if name is not None:
        args.extend(["--name", name])
    if keywords is not None:
        args.extend(["--keywords", keywords])
    if dry_run:
        args.append("--dry-run")
    return get_runner().run_json(args)


@mcp.tool(
    name="negativekeywordsharedsets_delete",
    description="Delete a shared negative keyword set by ID. Call tool_help('negativekeywordsharedsets_delete') for parameters.",
)
@handle_cli_errors
def negative_keyword_shared_sets_delete(id: int, dry_run: bool = False) -> dict:
    """Delete a negative keyword shared set.

    Args:
        id: Set ID.
        dry_run: Show the direct request without sending it.
    """
    args = ["negativekeywordsharedsets", "delete", "--id", str(id)]
    if dry_run:
        args.append("--dry-run")
    return get_runner().run_json(args)
