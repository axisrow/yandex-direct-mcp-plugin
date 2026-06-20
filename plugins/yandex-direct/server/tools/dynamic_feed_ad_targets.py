"""MCP tools for dynamic feed ad target management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors
from server.tools.helpers import (
    append_id_filters,
    append_pagination,
    run_set_bids,
    run_single_id_batch,
    tool_error_dict,
    validate_yes_no,
)


@mcp.tool(
    name="dynamicfeedadtargets_get",
    description="List dynamic feed ad targets (filters over product-feed items for dynamic ads). Call tool_help('dynamicfeedadtargets_get') for parameters.",
)
@handle_cli_errors
def dynamic_feed_ad_targets_list(
    ids: str | None = None,
    ad_group_ids: str | None = None,
    campaign_ids: str | None = None,
    states: str | None = None,
    limit: int | None = None,
    fetch_all: bool = False,
    fields: str | None = None,
) -> list[dict] | dict:
    """List dynamic feed ad targets.

    Limits: CampaignIds≤2, AdGroupIds≤1000;
    Ids unlimited. Enforced by direct-cli 0.4.3 (#571).

    Args:
        ids: Comma-separated target IDs.
        ad_group_ids: Comma-separated ad group IDs.
        campaign_ids: Comma-separated campaign IDs.
        states: Comma-separated states.
        limit: Limit number of results.
        fetch_all: Fetch all pages.
        fields: Comma-separated field names.
    """
    args = ["dynamicfeedadtargets", "get", "--format", "json"]
    append_id_filters(
        args,
        [
            (ids, "--ids"),
            (ad_group_ids, "--adgroup-ids"),
            (campaign_ids, "--campaign-ids"),
        ],
    )
    if states is not None:
        args.extend(["--states", states])
    append_pagination(args, limit, fetch_all, fields)
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(
    name="dynamicfeedadtargets_add",
    description="Create a dynamic feed ad target (filter over product-feed items). Call tool_help('dynamicfeedadtargets_add') for parameters.",
)
@handle_cli_errors
def dynamic_feed_ad_targets_add(
    ad_group_id: int,
    name: str,
    conditions: list[str] | None = None,
    condition: str | None = None,
    bid: int | None = None,
    context_bid: int | None = None,
    available_items_only: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Add a dynamic feed ad target.

    Args:
        ad_group_id: Ad group ID.
        name: Target name.
        condition: Single condition spec (e.g. "OPERAND:OPERATOR:ARG1|ARG2").
        conditions: Additional condition specs; each item is forwarded as
            repeated ``--condition``.
        bid: Optional search bid in micro-units (RUB × 1,000,000); CLI 0.2.10+
            rejects values 0 < x < 100_000 with a "did you mean × 1_000_000" hint.
        context_bid: Optional context bid in micro-units (same rules as `bid`).
        available_items_only: "YES" or "NO" — restrict to currently available
            feed items.
        dry_run: Show the direct request without sending it.
    """
    args = [
        "dynamicfeedadtargets",
        "add",
        "--adgroup-id",
        str(ad_group_id),
        "--name",
        name,
    ]
    if condition is not None:
        args.extend(["--condition", condition])
    if conditions:
        for spec in conditions:
            args.extend(["--condition", spec])
    if bid is not None:
        args.extend(["--bid", str(bid)])
    if context_bid is not None:
        args.extend(["--context-bid", str(context_bid)])
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
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(
    name="dynamicfeedadtargets_delete",
    description="Delete a dynamic feed ad target by ID. Call tool_help('dynamicfeedadtargets_delete') for parameters.",
)
@handle_cli_errors
def dynamic_feed_ad_targets_delete(id: int, dry_run: bool = False) -> dict:
    """Delete a dynamic feed ad target.

    Args:
        id: Target ID.
        dry_run: Show the direct request without sending it.
    """
    args = ["dynamicfeedadtargets", "delete", "--id", str(id)]
    if dry_run:
        args.append("--dry-run")
    return get_runner().run_json(args)


@mcp.tool(
    name="dynamicfeedadtargets_suspend",
    description="Pause dynamic feed ad targets by ID. Call tool_help('dynamicfeedadtargets_suspend') for parameters.",
)
@handle_cli_errors
def dynamic_feed_ad_targets_suspend(ids: str, dry_run: bool = False) -> dict:
    """Suspend dynamic feed ad targets.

    Args:
        ids: Comma-separated target IDs (max 10).
    """
    return run_single_id_batch(
        get_runner(), "dynamicfeedadtargets", "suspend", ids, dry_run=dry_run
    )


@mcp.tool(
    name="dynamicfeedadtargets_resume",
    description="Resume suspended dynamic feed ad targets by ID. Call tool_help('dynamicfeedadtargets_resume') for parameters.",
)
@handle_cli_errors
def dynamic_feed_ad_targets_resume(ids: str, dry_run: bool = False) -> dict:
    """Resume dynamic feed ad targets.

    Args:
        ids: Comma-separated target IDs (max 10).
    """
    return run_single_id_batch(
        get_runner(), "dynamicfeedadtargets", "resume", ids, dry_run=dry_run
    )


@mcp.tool(
    name="dynamicfeedadtargets_set_bids",
    description="Set search/context bids for dynamic feed ad targets. Call tool_help('dynamicfeedadtargets_set_bids') for parameters.",
)
@handle_cli_errors
def dynamic_feed_ad_targets_set_bids(
    id: int | None = None,
    ad_group_id: int | None = None,
    campaign_id: int | None = None,
    bid: int | None = None,
    context_bid: int | None = None,
    dry_run: bool = False,
) -> dict:
    """Set dynamic feed ad target bids.

    Args:
        id: Target ID.
        ad_group_id: Ad group ID.
        campaign_id: Campaign ID.
        bid: Optional search bid in micro-units (RUB × 1,000,000); CLI 0.2.10+
            rejects values 0 < x < 100_000 with a "did you mean × 1_000_000" hint.
        context_bid: Optional context bid in micro-units (same rules as `bid`).
    """
    return run_set_bids(
        get_runner(),
        "dynamicfeedadtargets",
        id=id,
        ad_group_id=ad_group_id,
        campaign_id=campaign_id,
        bid_fields=(("--bid", bid), ("--context-bid", context_bid)),
        missing_update_message="Provide at least one of: bid, context_bid",
        dry_run=dry_run,
    )
