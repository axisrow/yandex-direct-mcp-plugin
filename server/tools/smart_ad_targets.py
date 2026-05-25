"""MCP tools for smart ad target management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import run_single_id_batch

_YES_NO = ("YES", "NO")


@mcp.tool(name="smartadtargets_get")
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


@mcp.tool(name="smartadtargets_add")
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
    if conditions:
        for spec in conditions:
            args.extend(["--condition", spec])
    if average_cpc is not None:
        args.extend(["--average-cpc", str(average_cpc)])
    if average_cpa is not None:
        args.extend(["--average-cpa", str(average_cpa)])
    if priority is not None:
        args.extend(["--priority", priority])
    if available_items_only is not None:
        if available_items_only not in _YES_NO:
            return ToolError(
                error="invalid_available_items_only",
                message=(
                    f"available_items_only must be YES or NO; "
                    f"got '{available_items_only}'"
                ),
            ).__dict__
        args.extend(["--available-items-only", available_items_only])
    if dry_run:
        args.append("--dry-run")
    return get_runner().run_json(args)


@mcp.tool(name="smartadtargets_update")
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
    if not any(
        (
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
        return ToolError(
            error="missing_update_fields",
            message=(
                "Provide at least one of: name, audience, condition, average_cpc, "
                "average_cpa, priority, available_items_only"
            ),
        ).__dict__

    args = ["smartadtargets", "update", "--id", str(id)]
    if name is not None:
        args.extend(["--name", name])
    if audience is not None:
        args.extend(["--audience", audience])
    if condition is not None:
        args.extend(["--condition", condition])
    if conditions:
        for spec in conditions:
            args.extend(["--condition", spec])
    if average_cpc is not None:
        args.extend(["--average-cpc", str(average_cpc)])
    if average_cpa is not None:
        args.extend(["--average-cpa", str(average_cpa)])
    if priority is not None:
        args.extend(["--priority", priority])
    if available_items_only is not None:
        if available_items_only not in _YES_NO:
            return ToolError(
                error="invalid_available_items_only",
                message=(
                    f"available_items_only must be YES or NO; "
                    f"got '{available_items_only}'"
                ),
            ).__dict__
        args.extend(["--available-items-only", available_items_only])
    if dry_run:
        args.append("--dry-run")
    return get_runner().run_json(args)


@mcp.tool(name="smartadtargets_delete")
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


@mcp.tool(name="smartadtargets_suspend")
@handle_cli_errors
def smart_ad_targets_suspend(ids: str, dry_run: bool = False) -> dict:
    """Suspend smart ad targets."""
    return run_single_id_batch(
        get_runner(), "smartadtargets", "suspend", ids, dry_run=dry_run
    )


@mcp.tool(name="smartadtargets_resume")
@handle_cli_errors
def smart_ad_targets_resume(ids: str, dry_run: bool = False) -> dict:
    """Resume smart ad targets."""
    return run_single_id_batch(
        get_runner(), "smartadtargets", "resume", ids, dry_run=dry_run
    )


@mcp.tool(name="smartadtargets_set_bids")
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
    if id is None and ad_group_id is None and campaign_id is None:
        return ToolError(
            error="missing_target_scope",
            message="Provide at least one of: id, ad_group_id, campaign_id",
        ).__dict__
    if average_cpc is None and average_cpa is None and priority is None:
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one of: average_cpc, average_cpa, priority",
        ).__dict__

    args = ["smartadtargets", "set-bids"]
    if id is not None:
        args.extend(["--id", str(id)])
    if ad_group_id is not None:
        args.extend(["--adgroup-id", str(ad_group_id)])
    if campaign_id is not None:
        args.extend(["--campaign-id", str(campaign_id)])
    if average_cpc is not None:
        args.extend(["--average-cpc", str(average_cpc)])
    if average_cpa is not None:
        args.extend(["--average-cpa", str(average_cpa)])
    if priority is not None:
        args.extend(["--priority", priority])
    if dry_run:
        args.append("--dry-run")

    runner = get_runner()
    return runner.run_json(args)
