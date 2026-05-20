"""MCP tools for sitelinks management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit, run_single_id_batch


@mcp.tool(name="sitelinks_get")
@handle_cli_errors
def sitelinks_list(
    ids: str | None = None,
    limit: int | None = None,
    fetch_all: bool = False,
    fields: str | None = None,
) -> list[dict] | dict:
    """List sitelinks sets.

    Args:
        ids: Comma-separated sitelinks set IDs (max 10).
        limit: Limit number of results.
        fetch_all: Fetch all pages.
        fields: Comma-separated field names.
    """
    cmd = ["sitelinks", "get", "--format", "json"]
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        batch_error = check_batch_limit(normalized_ids)
        if batch_error:
            return batch_error.__dict__
        cmd.extend(["--ids", normalized_ids])
    if limit is not None:
        cmd.extend(["--limit", str(limit)])
    if fetch_all:
        cmd.append("--fetch-all")
    if fields is not None:
        cmd.extend(["--fields", fields])
    return get_runner().run_json(cmd)


@mcp.tool()
@handle_cli_errors
def sitelinks_add(sitelinks: list[str], dry_run: bool = False) -> dict:
    """Add a sitelinks set.

    CLI 0.3.8 expects each sitelink as a pipe-delimited string passed via
    repeatable --sitelink: ``TITLE|HREF[|DESCRIPTION]``.

    Args:
        sitelinks: List of sitelink specs in ``TITLE|HREF[|DESCRIPTION]`` form.
            Example: ``["About|https://example.com/about|Learn more",
            "Pricing|https://example.com/pricing"]``.
        dry_run: Show the direct-cli request without sending it.
    """
    if not sitelinks:
        return ToolError(
            error="missing_sitelinks",
            message="Provide at least one sitelink spec (TITLE|HREF[|DESCRIPTION]).",
        ).__dict__

    args = ["sitelinks", "add"]
    for spec in sitelinks:
        args.extend(["--sitelink", spec])
    if dry_run:
        args.append("--dry-run")
    return get_runner().run_json(args)


@mcp.tool()
@handle_cli_errors
def sitelinks_delete(ids: str, dry_run: bool = False) -> dict:
    """Delete sitelinks sets.

    Args:
        ids: Comma-separated sitelinks set IDs (max 10).
    """
    return run_single_id_batch(
        get_runner(), "sitelinks", "delete", ids, dry_run=dry_run
    )
