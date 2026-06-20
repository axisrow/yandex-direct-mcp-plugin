"""MCP tools for ad extensions management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors
from server.tools.helpers import (
    append_pagination,
    check_batch_limit,
    run_single_id_batch,
    tool_error_dict,
)


@mcp.tool(
    name="adextensions_get",
    description="List ad extensions (callouts/clarifications shown with ads), optionally filtered by IDs/types/states. Use adextensions_add to create, adextensions_delete to remove. Call tool_help('adextensions_get') for parameters.",
)
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
            return tool_error_dict(batch_error)
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
    append_pagination(cmd, limit, fetch_all, fields)
    if callout_field_names is not None:
        cmd.extend(["--callout-field-names", callout_field_names])
    return get_runner().run_json(cmd)


@mcp.tool(
    description="Add an ad extension (callout type only; for sitelinks use sitelinks_add). Use adextensions_get to list existing extensions. Call tool_help('adextensions_add') for parameters.",
)
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


@mcp.tool(
    description="Delete ad extensions by ID (max 10 per call). Use adextensions_get to find IDs. Call tool_help('adextensions_delete') for parameters.",
)
@handle_cli_errors
def adextensions_delete(ids: str, dry_run: bool = False) -> dict:
    """Delete ad extensions.

    Args:
        ids: Comma-separated extension IDs (max 10).
    """
    return run_single_id_batch(
        get_runner(), "adextensions", "delete", ids, dry_run=dry_run
    )
