"""MCP tools for smart ad target management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import (
    CliOption,
    append_cli_options,
    provided_update_value,
    run_set_bids,
    run_single_id_batch,
    tool_error_dict,
    validate_yes_no,
)

SMART_TARGET_CONDITION_OPTIONS = (CliOption("conditions", "--condition", repeat=True),)


@mcp.tool(
    name="smartadtargets_get",
    description="List smart ad targets (audience filters for smart banner / dynamic feed campaigns). Call tool_help('smartadtargets_get') for parameters.",
)
@handle_cli_errors
def smart_ad_targets_list(
    ids: str | None = None,
    ad_group_ids: str | None = None,
    campaign_ids: str | None = None,
    states: str | None = None,
    limit: int | None = None,
    fetch_all: bool = False,
    fields: str | None = None,
) -> list[dict] | dict:
    """List smart ad targets.

    Args:
        ids: Comma-separated target IDs.
        ad_group_ids: Comma-separated ad group IDs.
        campaign_ids: Comma-separated campaign IDs.
        states: Comma-separated states.
        limit: Limit number of results.
        fetch_all: Fetch all pages.
        fields: Comma-separated field names.
    """
    args = ["smartadtargets", "get", "--format", "json"]
    if ids is not None:
        normalized = ids.strip()
        if normalized:
            args.extend(["--ids", normalized])
    if ad_group_ids is not None:
        normalized = ad_group_ids.strip()
        if normalized:
            args.extend(["--adgroup-ids", normalized])
    if campaign_ids is not None:
        normalized = campaign_ids.strip()
        if normalized:
            args.extend(["--campaign-ids", normalized])
    if states is not None:
        args.extend(["--states", states])
    if limit is not None:
        args.extend(["--limit", str(limit)])
    if fetch_all:
        args.append("--fetch-all")
    if fields is not None:
        args.extend(["--fields", fields])
    return get_runner().run_json(args)


@mcp.tool(
    name="smartadtargets_add",
    description="Create a smart ad target (filter/audience condition for smart banners). Call tool_help('smartadtargets_add') for parameters.",
)
@handle_cli_errors
def smart_ad_targets_add(
    ad_group_id: int,
    name: str,
    audience: str,
    conditions: list[str] | None = None,
    condition: str | None = None,
    average_cpc: int | None = None,
    average_cpa: int | None = None,
    priority: str | None = None,
    available_items_only: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Add a smart ad target.

    CLI 0.3.8 dropped --json and replaced --type with typed flags (name,
    audience, condition). Mirrors WSDL SmartAdTargetAddItem.

    Args:
        ad_group_id: Ad group ID.
        name: Target name.
        audience: Audience value.
        condition: Single condition spec (OPERAND:OPERATOR:ARG1|ARG2).
        conditions: Additional condition specs; each item is forwarded as
            repeated ``--condition``.
        average_cpc: Average CPC in micro-units (RUB × 1,000,000).
        average_cpa: Average CPA in micro-units (RUB × 1,000,000).
        priority: Strategy priority.
        available_items_only: "YES" or "NO" — whether only available items
            are targeted.
        dry_run: Show the direct request without sending it.
    """
    args = [
        "smartadtargets",
        "add",
        "--adgroup-id",
        str(ad_group_id),
        "--name",
        name,
        "--audience",
        audience,
    ]
    if condition is not None:
        args.extend(["--condition", condition])
    append_cli_options(args, locals(), SMART_TARGET_CONDITION_OPTIONS)
    if average_cpc is not None:
        args.extend(["--average-cpc", str(average_cpc)])
    if average_cpa is not None:
        args.extend(["--average-cpa", str(average_cpa)])
    if priority is not None:
        args.extend(["--priority", priority])
    if available_items_only is not None:
        err = validate_yes_no(
            available_items_only,
            field="available_items_only",
            error="invalid_available_items_only",
        )
        if err is not None:
            return tool_error_dict(err)
        args.extend(["--available-items-only", available_items_only])
    if dry_run:
        args.append("--dry-run")
    return get_runner().run_json(args)


@mcp.tool(
    name="smartadtargets_update",
    description="Update an existing smart ad target's name, audience, conditions, or bids. Call tool_help('smartadtargets_update') for parameters.",
)
@handle_cli_errors
def smart_ad_targets_update(
    id: int,
    name: str | None = None,
    audience: str | None = None,
    conditions: list[str] | None = None,
    condition: str | None = None,
    average_cpc: int | None = None,
    average_cpa: int | None = None,
    priority: str | None = None,
    available_items_only: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Update a smart ad target.

    CLI 0.3.8 dropped --json and replaced --type with typed flags.

    Args:
        id: Target ID.
        name: New target name.
        audience: New audience value.
        condition: Single new condition spec.
        conditions: Additional new condition specs; each item is forwarded as
            repeated ``--condition``.
        average_cpc: New average CPC in micro-units (RUB × 1,000,000).
        average_cpa: New average CPA in micro-units (RUB × 1,000,000).
        priority: New strategy priority.
        available_items_only: "YES" or "NO".
        dry_run: Show the direct request without sending it.
    """
    # Use provided_update_value (None-aware) instead of raw truthiness so a
    # legitimate zero bid (average_cpc=0 / average_cpa=0) is treated as a
    # provided field; the CLI's MICRO_RUBLES type accepts 0. (#170-22)
    if not any(
        provided_update_value(v)
        for v in (
            name,
            audience,
            conditions,
            condition,
            average_cpc,
            average_cpa,
            priority,
            available_items_only,
        )
    ):
        return tool_error_dict(
            ToolError(
                error="missing_update_fields",
                message=(
                    "Provide at least one of: name, audience, condition, average_cpc, "
                    "average_cpa, priority, available_items_only"
                ),
            )
        )

    args = ["smartadtargets", "update", "--id", str(id)]
    if name is not None:
        args.extend(["--name", name])
    if audience is not None:
        args.extend(["--audience", audience])
    if condition is not None:
        args.extend(["--condition", condition])
    append_cli_options(args, locals(), SMART_TARGET_CONDITION_OPTIONS)
    if average_cpc is not None:
        args.extend(["--average-cpc", str(average_cpc)])
    if average_cpa is not None:
        args.extend(["--average-cpa", str(average_cpa)])
    if priority is not None:
        args.extend(["--priority", priority])
    if available_items_only is not None:
        err = validate_yes_no(
            available_items_only,
            field="available_items_only",
            error="invalid_available_items_only",
        )
        if err is not None:
            return tool_error_dict(err)
        args.extend(["--available-items-only", available_items_only])
    if dry_run:
        args.append("--dry-run")
    return get_runner().run_json(args)


@mcp.tool(
    name="smartadtargets_delete",
    description="Delete a smart ad target by ID. Call tool_help('smartadtargets_delete') for parameters.",
)
@handle_cli_errors
def smart_ad_targets_delete(id: int, dry_run: bool = False) -> dict:
    """Delete a smart ad target.

    Args:
        id: Target ID.
        dry_run: Show the direct request without sending it.
    """
    args = ["smartadtargets", "delete", "--id", str(id)]
    if dry_run:
        args.append("--dry-run")
    return get_runner().run_json(args)


@mcp.tool(
    name="smartadtargets_suspend",
    description="Pause smart ad targets by ID. Call tool_help('smartadtargets_suspend') for parameters.",
)
@handle_cli_errors
def smart_ad_targets_suspend(ids: str, dry_run: bool = False) -> dict:
    """Suspend smart ad targets."""
    return run_single_id_batch(
        get_runner(), "smartadtargets", "suspend", ids, dry_run=dry_run
    )


@mcp.tool(
    name="smartadtargets_resume",
    description="Resume suspended smart ad targets by ID. Call tool_help('smartadtargets_resume') for parameters.",
)
@handle_cli_errors
def smart_ad_targets_resume(ids: str, dry_run: bool = False) -> dict:
    """Resume smart ad targets."""
    return run_single_id_batch(
        get_runner(), "smartadtargets", "resume", ids, dry_run=dry_run
    )


@mcp.tool(
    name="smartadtargets_set_bids",
    description="Set average CPC/CPA or priority for smart ad targets. Call tool_help('smartadtargets_set_bids') for parameters.",
)
@handle_cli_errors
def smart_ad_targets_set_bids(
    id: int | None = None,
    ad_group_id: int | None = None,
    campaign_id: int | None = None,
    average_cpc: int | None = None,
    average_cpa: int | None = None,
    priority: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Set smart ad target bids.

    Args:
        id: Target ID.
        ad_group_id: Ad group ID.
        campaign_id: Campaign ID.
        average_cpc: Optional average CPC in micro-units (RUB × 1,000,000); CLI 0.2.10+
            rejects values 0 < x < 100_000 with a "did you mean × 1_000_000" hint.
        average_cpa: Optional average CPA in micro-units (same rules as `average_cpc`).
        priority: Strategy priority.
    """
    return run_set_bids(
        get_runner(),
        "smartadtargets",
        id=id,
        ad_group_id=ad_group_id,
        campaign_id=campaign_id,
        bid_fields=(
            ("--average-cpc", average_cpc),
            ("--average-cpa", average_cpa),
            ("--priority", priority),
        ),
        missing_update_message=(
            "Provide at least one of: average_cpc, average_cpa, priority"
        ),
        dry_run=dry_run,
    )
