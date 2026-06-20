"""MCP tools for retargeting list management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors
from server.tools.helpers import (
    CliOption,
    append_cli_options,
    append_pagination,
    require_update_fields,
    run_single_id_batch,
    tool_error_dict,
    validate_enum,
)

_LIST_TYPES = ("RETARGETING", "AUDIENCE")
RETARGETING_RULE_OPTIONS = (CliOption("rules", "--rule", repeat=True),)


@mcp.tool(
    name="retargeting_get",
    description="List retargeting lists (audience/goal-based segments) for the account. Call tool_help('retargeting_get') for parameters.",
)
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
    append_pagination(args, limit, fetch_all, fields)
    return get_runner().run_json(args)


@mcp.tool(
    name="retargeting_add",
    description="Create a retargeting list from Metrica goal / Audience segment rules. Call tool_help('retargeting_add') for parameters.",
)
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
        description: Optional retargeting list description.
        rule: Single rule spec (CLI DSL form, see above).
        rules: Additional rule specs; each item is forwarded as repeated
            ``--rule``.
        dry_run: Show the direct request without sending it.
    """
    list_type_error = validate_enum(
        list_type, _LIST_TYPES, field="list_type", error="invalid_list_type"
    )
    if list_type_error:
        return tool_error_dict(list_type_error)
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
    append_cli_options(args, locals(), RETARGETING_RULE_OPTIONS)
    if dry_run:
        args.append("--dry-run")
    return get_runner().run_json(args)


@mcp.tool(
    name="retargeting_delete",
    description="Delete retargeting lists by ID. Call tool_help('retargeting_delete') for parameters.",
)
@handle_cli_errors
def retargeting_delete(ids: str, dry_run: bool = False) -> dict:
    """Delete retargeting lists.

    Args:
        ids: Comma-separated retargeting list IDs (max 10).
    """
    return run_single_id_batch(
        get_runner(), "retargeting", "delete", ids, dry_run=dry_run
    )


@mcp.tool(
    name="retargeting_update",
    description="Update an existing retargeting list's name, description, or rules (type is fixed at creation). Call tool_help('retargeting_update') for parameters.",
)
@handle_cli_errors
def retargeting_update(
    id: int,
    name: str | None = None,
    description: str | None = None,
    rules: list[str] | None = None,
    rule: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Update a retargeting list.

    CLI 0.3.8 expects --rule as a CLI-DSL string (see retargeting_add).

    The list type is fixed at creation: ``RetargetingLists.update`` in Direct
    API v5 does not accept the ``Type`` field, so this tool intentionally has
    no ``list_type`` parameter — passing it previously triggered API error 8000
    ("unknown parameter Type"). Use ``retargeting_add`` to pick a type.

    Args:
        id: Retargeting list ID to update.
        name: New name for the list.
        description: New list description.
        rule: Single new rule spec in CLI DSL form.
        rules: Additional new rule specs; each item is forwarded as repeated
            ``--rule``.
        dry_run: Show the direct request without sending it.
    """
    fields_error = require_update_fields(
        locals(),
        message=(
            "Provide at least one of: name, description, "
            "rule, rules. Use rule for one spec or rules for repeated specs."
        ),
        exclude={"id", "dry_run"},
    )
    if fields_error:
        return tool_error_dict(fields_error)

    args = ["retargeting", "update", "--id", str(id)]
    if name is not None:
        args.extend(["--name", name])
    if description is not None:
        args.extend(["--description", description])
    if rule is not None:
        args.extend(["--rule", rule])
    append_cli_options(args, locals(), RETARGETING_RULE_OPTIONS)
    if dry_run:
        args.append("--dry-run")
    return get_runner().run_json(args)
