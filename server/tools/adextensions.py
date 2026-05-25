"""MCP tools for ad extensions management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit, run_single_id_batch


@mcp.tool(name="adextensions_get")
@handle_cli_errors
def adextensions_list(
    ids: str | None = None,
    types: str | None = None,
    states: str | None = None,
    statuses: str | None = None,
    modified_since: str | None = None,
    limit: int | None = None,
    fetch_all: bool = False,
    fields: str | None = None,
    callout_field_names: str | None = None,
) -> list[dict] | dict:
    """List ad extensions.

    Args:
        ids: Comma-separated extension IDs.
        types: Comma-separated extension types.
        states: Comma-separated states.
        statuses: Comma-separated statuses.
        modified_since: ModifiedSince datetime.
        limit: Limit number of results.
        fetch_all: Fetch all pages.
        fields: Comma-separated field names.
        callout_field_names: Comma-separated CalloutFieldNames.
    """
    cmd = ["adextensions", "get", "--format", "json"]
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        batch_error = check_batch_limit(normalized_ids)
        if batch_error:
            return batch_error.__dict__
        cmd.extend(["--ids", normalized_ids])
    normalized_types = types.strip() if types is not None else None
    if normalized_types:
        cmd.extend(["--types", normalized_types])
    if states is not None:
        cmd.extend(["--states", states])
    if statuses is not None:
        cmd.extend(["--statuses", statuses])
    if modified_since is not None:
        cmd.extend(["--modified-since", modified_since])
    if limit is not None:
        cmd.extend(["--limit", str(limit)])
    if fetch_all:
        cmd.append("--fetch-all")
    if fields is not None:
        cmd.extend(["--fields", fields])
    if callout_field_names is not None:
        cmd.extend(["--callout-field-names", callout_field_names])
    return get_runner().run_json(cmd)


@mcp.tool()
@handle_cli_errors
def adextensions_add(callout_text: str, dry_run: bool = False) -> dict:
    """Add an ad extension (callout).

    CLI 0.3.8 exposes only the CALLOUT type via `--callout-text`. For SITELINK
    extensions use the `sitelinks_*` tools.

    Args:
        callout_text: Callout text (Callout extension).
        dry_run: Show the direct request without sending it.
    """
    args = ["adextensions", "add", "--callout-text", callout_text]
    if dry_run:
        args.append("--dry-run")
    return get_runner().run_json(args)


@mcp.tool()
@handle_cli_errors
def adextensions_delete(ids: str, dry_run: bool = False) -> dict:
    """Delete ad extensions.

    Args:
        ids: Comma-separated extension IDs (max 10).
    """
    return run_single_id_batch(
        get_runner(), "adextensions", "delete", ids, dry_run=dry_run
    )
