"""MCP tools for retargeting list management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import run_single_id_batch

_LIST_TYPES = ("RETARGETING", "AUDIENCE")


@mcp.tool(name="retargeting_get")
@handle_cli_errors
def retargeting_list(
    ids: str | None = None,
    types: str | None = None,
    limit: int | None = None,
    fetch_all: bool = False,
    fields: str | None = None,
) -> list[dict] | dict:
    """List retargeting lists.

    Args:
        ids: Comma-separated retargeting list IDs.
        types: Comma-separated types to filter by.
        limit: Limit number of results.
        fetch_all: Fetch all pages.
        fields: Comma-separated field names.
    """
    args = ["retargeting", "get", "--format", "json"]
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        args.extend(["--ids", normalized_ids])
    normalized_types = types.strip() if types is not None else None
    if normalized_types:
        args.extend(["--types", normalized_types])
    if limit is not None:
        args.extend(["--limit", str(limit)])
    if fetch_all:
        args.append("--fetch-all")
    if fields is not None:
        args.extend(["--fields", fields])
    return get_runner().run_json(args)


@mcp.tool(name="retargeting_add")
@handle_cli_errors
def retargeting_add(
    name: str,
    list_type: str = "RETARGETING",
    description: str | None = None,
    rules: list[str] | None = None,
    rule: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Add a retargeting list.

    CLI 0.3.8 expects --rule as a CLI-DSL string:
    ``OPERATOR:EXTERNAL_ID[:LIFESPAN][|EXTERNAL_ID[:LIFESPAN]]``
    where OPERATOR is one of ALL, ANY, NONE; EXTERNAL_ID refers to a Metrica
    goal or Audience segment ID; LIFESPAN is the lookback window in days.

    Args:
        name: Name for the retargeting list.
        list_type: List type — RETARGETING (default, text & image / mobile
            campaigns) or AUDIENCE (display campaigns).
        rule: Rule spec (CLI DSL form, see above).
        dry_run: Show the direct request without sending it.
    """
    if list_type not in _LIST_TYPES:
        return ToolError(
            error="invalid_list_type",
            message=f"list_type must be one of {_LIST_TYPES}; got '{list_type}'",
        ).__dict__
    args = [
        "retargeting",
        "add",
        "--name",
        name,
        "--type",
        list_type,
    ]
    if rule is not None:
        args.extend(["--rule", rule])
    if description is not None:
        args.extend(["--description", description])
    if rules:
        for spec in rules:
            args.extend(["--rule", spec])
    if dry_run:
        args.append("--dry-run")
    return get_runner().run_json(args)


@mcp.tool(name="retargeting_delete")
@handle_cli_errors
def retargeting_delete(ids: str, dry_run: bool = False) -> dict:
    """Delete retargeting lists.

    Args:
        ids: Comma-separated retargeting list IDs (max 10).
    """
    return run_single_id_batch(
        get_runner(), "retargeting", "delete", ids, dry_run=dry_run
    )


@mcp.tool(name="retargeting_update")
@handle_cli_errors
def retargeting_update(
    id: int,
    name: str | None = None,
    description: str | None = None,
    list_type: str | None = None,
    rules: list[str] | None = None,
    rule: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Update a retargeting list.

    CLI 0.3.8 expects --rule as a CLI-DSL string (see retargeting_add).

    Args:
        id: Retargeting list ID to update.
        name: New name for the list.
        list_type: New list type (RETARGETING | AUDIENCE).
        rule: New rule spec in CLI DSL form.
        dry_run: Show the direct request without sending it.
    """
    if not any((name, description, list_type, rules, rule)):
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one of: name, description, list_type, rule",
        ).__dict__
    if list_type is not None and list_type not in _LIST_TYPES:
        return ToolError(
            error="invalid_list_type",
            message=f"list_type must be one of {_LIST_TYPES}; got '{list_type}'",
        ).__dict__

    args = ["retargeting", "update", "--id", str(id)]
    if name is not None:
        args.extend(["--name", name])
    if description is not None:
        args.extend(["--description", description])
    if list_type is not None:
        args.extend(["--type", list_type])
    if rule is not None:
        args.extend(["--rule", rule])
    if rules:
        for spec in rules:
            args.extend(["--rule", spec])
    if dry_run:
        args.append("--dry-run")
    return get_runner().run_json(args)
