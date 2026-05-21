"""MCP tools for sitelinks management."""

import json

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit, run_single_id_batch

_SITELINK_FIELD_MAP = {
    "title": "Title",
    "href": "Href",
    "description": "Description",
    "turbo_page_id": "TurboPageId",
}


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


def _to_wsdl_sitelink(item: dict) -> dict | ToolError:
    """Convert snake_case dict to WSDL CamelCase keys.

    Unknown keys are rejected to surface typos early.
    """
    result: dict = {}
    for key, value in item.items():
        wsdl_key = _SITELINK_FIELD_MAP.get(key)
        if wsdl_key is None:
            return ToolError(
                error="unknown_field",
                message=(
                    f"Unknown sitelink field {key!r}. "
                    f"Allowed: {sorted(_SITELINK_FIELD_MAP)}."
                ),
            )
        result[wsdl_key] = value
    return result


@mcp.tool()
@handle_cli_errors
def sitelinks_add(
    sitelinks: list[str] | None = None,
    items: list[dict] | None = None,
    from_file: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Add a sitelinks set.

    CLI 0.3.10 accepts three mutually exclusive input modes:

    - ``sitelinks`` — list of pipe-delimited specs ``TITLE|HREF[|DESCRIPTION]``,
      forwarded via repeatable ``--sitelink``. Escape literal ``|`` as ``\\|``
      (for example, UTM templates with ``cid|{campaign_id}``).
    - ``items`` — list of dicts with snake_case keys ``title`` / ``href`` /
      ``description`` / ``turbo_page_id``. The plugin re-keys to WSDL CamelCase
      and sends them as ``--sitelink-json`` (no pipe escaping needed).
    - ``from_file`` — path to a JSONL file with one sitelink object per line,
      forwarded as ``--sitelinks-from-file``.

    Args:
        sitelinks: Pipe-delimited specs. Example: ``["About|https://x.com/a|Info"]``.
        items: Structured objects. Example:
            ``[{"title": "Главная", "href": "https://x.com/?utm=cid|{cid}"}]``.
        from_file: Filesystem path passed to direct-cli unchanged.
        dry_run: Show the direct-cli request without sending it.
    """
    provided = [
        name
        for name, value in (
            ("sitelinks", sitelinks),
            ("items", items),
            ("from_file", from_file),
        )
        if value is not None
    ]
    if not provided:
        return ToolError(
            error="missing_mode",
            message=(
                "Provide exactly one of: sitelinks (list[str]), "
                "items (list[dict]), or from_file (path)."
            ),
        ).__dict__
    if len(provided) > 1:
        return ToolError(
            error="conflicting_modes",
            message=(
                "Pass exactly one of sitelinks, items, or from_file — "
                f"got: {', '.join(provided)}."
            ),
        ).__dict__
    if sitelinks is not None and not sitelinks:
        return ToolError(
            error="empty_mode",
            message="sitelinks must contain at least one spec.",
        ).__dict__
    if items is not None and not items:
        return ToolError(
            error="empty_mode",
            message="items must contain at least one sitelink object.",
        ).__dict__
    if from_file is not None and not from_file:
        return ToolError(
            error="empty_mode",
            message="from_file must be a non-empty path.",
        ).__dict__

    args = ["sitelinks", "add"]
    if sitelinks is not None:
        for spec in sitelinks:
            args.extend(["--sitelink", spec])
    elif items is not None:
        wsdl_items: list[dict] = []
        for item in items:
            converted = _to_wsdl_sitelink(item)
            if isinstance(converted, ToolError):
                return converted.__dict__
            wsdl_items.append(converted)
        args.extend(["--sitelink-json", json.dumps(wsdl_items, ensure_ascii=False)])
    else:
        assert from_file is not None
        args.extend(["--sitelinks-from-file", from_file])

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
