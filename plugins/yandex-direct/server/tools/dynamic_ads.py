"""MCP tools for dynamic ad (webpage) management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors
from server.tools.helpers import run_set_bids, run_single_id_batch


@mcp.tool(
    name="dynamicads_get",
    description="List dynamic ad targets (website-based webpage filters for dynamic text ads). Call tool_help('dynamicads_get') for parameters.",
)
@handle_cli_errors
def dynamic_ads_list(
    ids: str | None = None,
    ad_group_ids: str | None = None,
    campaign_ids: str | None = None,
    states: str | None = None,
    limit: int | None = None,
    fetch_all: bool = False,
    fields: str | None = None,
) -> list[dict] | dict:
    """List dynamic ad targets (webpages).

    Args:
        ids: Comma-separated target IDs.
        ad_group_ids: Comma-separated ad group IDs.
        campaign_ids: Comma-separated campaign IDs.
        states: Comma-separated states.
        limit: Limit number of results.
        fetch_all: Fetch all pages.
        fields: Comma-separated field names.
    """
    args = ["dynamicads", "get", "--format", "json"]
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
    name="dynamicads_add",
    description="Create a dynamic ad target (webpage filter) for dynamic text ads. Call tool_help('dynamicads_add') for parameters.",
)
@handle_cli_errors
def dynamic_ads_add(
    ad_group_id: int,
    name: str,
    condition: str | None = None,
    bid: int | None = None,
    context_bid: int | None = None,
    priority: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Add a dynamic ad target (webpage).

    CLI 0.3.8 dropped --json. `condition` follows the CLI's
    OPERAND:OPERATOR:ARG1|ARG2 spec — see WSDL Webpage conditions for the
    semantic.

    Args:
        ad_group_id: Ad group ID.
        name: Target name.
        condition: Condition spec (OPERAND:OPERATOR:ARG1|ARG2).
        bid: Search bid in micro-units (RUB × 1,000,000).
        context_bid: Context bid in micro-units (RUB × 1,000,000).
        priority: Strategy priority.
        dry_run: Show the direct request without sending it.
    """
    args = [
        "dynamicads",
        "add",
        "--adgroup-id",
        str(ad_group_id),
        "--name",
        name,
    ]
    if condition is not None:
        args.extend(["--condition", condition])
    if bid is not None:
        args.extend(["--bid", str(bid)])
    if context_bid is not None:
        args.extend(["--context-bid", str(context_bid)])
    if priority is not None:
        args.extend(["--priority", priority])
    if dry_run:
        args.append("--dry-run")
    return get_runner().run_json(args)


@mcp.tool(
    name="dynamicads_delete",
    description="Delete a dynamic ad target (webpage filter) by ID. Call tool_help('dynamicads_delete') for parameters.",
)
@handle_cli_errors
def dynamic_ads_delete(id: int, dry_run: bool = False) -> dict:
    """Delete a dynamic ad target (webpage).

    Args:
        id: Target ID.
        dry_run: Show the direct request without sending it.
    """
    args = ["dynamicads", "delete", "--id", str(id)]
    if dry_run:
        args.append("--dry-run")
    return get_runner().run_json(args)


@mcp.tool(
    name="dynamicads_suspend",
    description="Pause dynamic ad targets by ID. Call tool_help('dynamicads_suspend') for parameters.",
)
@handle_cli_errors
def dynamic_ads_suspend(ids: str, dry_run: bool = False) -> dict:
    """Suspend dynamic ad targets."""
    return run_single_id_batch(
        get_runner(), "dynamicads", "suspend", ids, dry_run=dry_run
    )


@mcp.tool(
    name="dynamicads_resume",
    description="Resume suspended dynamic ad targets by ID. Call tool_help('dynamicads_resume') for parameters.",
)
@handle_cli_errors
def dynamic_ads_resume(ids: str, dry_run: bool = False) -> dict:
    """Resume dynamic ad targets."""
    return run_single_id_batch(
        get_runner(), "dynamicads", "resume", ids, dry_run=dry_run
    )


@mcp.tool(
    name="dynamicads_set_bids",
    description="Set search/context bids or priority for dynamic ad targets. Call tool_help('dynamicads_set_bids') for parameters.",
)
@handle_cli_errors
def dynamic_ads_set_bids(
    id: int | None = None,
    ad_group_id: int | None = None,
    campaign_id: int | None = None,
    bid: int | None = None,
    context_bid: int | None = None,
    priority: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Set dynamic ad target bids.

    Args:
        id: Target ID.
        ad_group_id: Ad group ID.
        campaign_id: Campaign ID.
        bid: Optional search bid in micro-units (RUB × 1,000,000); CLI 0.2.10+
            rejects values 0 < x < 100_000 with a "did you mean × 1_000_000" hint.
        context_bid: Optional context bid in micro-units (same rules as `bid`).
        priority: Strategy priority.
    """
    return run_set_bids(
        get_runner(),
        "dynamicads",
        id=id,
        ad_group_id=ad_group_id,
        campaign_id=campaign_id,
        bid_fields=(
            ("--bid", bid),
            ("--context-bid", context_bid),
            ("--priority", priority),
        ),
        missing_update_message="Provide at least one of: bid, context_bid, priority",
        dry_run=dry_run,
    )
