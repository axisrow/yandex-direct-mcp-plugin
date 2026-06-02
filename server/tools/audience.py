"""MCP tools for audience target management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit, run_set_bids, run_single_id_batch


@mcp.tool(name="audiencetargets_get")
@handle_cli_errors
def audience_targets_list(
    campaign_ids: str | None = None,
    ad_group_ids: str | None = None,
    ids: str | None = None,
    retargeting_list_ids: str | None = None,
    interest_ids: str | None = None,
    states: str | None = None,
    limit: int | None = None,
    fetch_all: bool = False,
    fields: str | None = None,
) -> list[dict] | dict:
    """List audience targets.

    Args:
        campaign_ids: Comma-separated campaign IDs (max 10).
        ad_group_ids: Comma-separated ad group IDs (max 10).
        ids: Comma-separated audience target IDs (max 10).
        retargeting_list_ids: Comma-separated retargeting list IDs.
        interest_ids: Comma-separated interest IDs.
        states: Comma-separated states.
        limit: Limit number of results.
        fetch_all: Fetch all pages.
        fields: Comma-separated field names.
    """
    args = ["audiencetargets", "get", "--format", "json"]
    normalized_campaign_ids = campaign_ids.strip() if campaign_ids is not None else None
    if normalized_campaign_ids:
        batch_error = check_batch_limit(normalized_campaign_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--campaign-ids", normalized_campaign_ids])
    normalized_ad_group_ids = ad_group_ids.strip() if ad_group_ids is not None else None
    if normalized_ad_group_ids:
        batch_error = check_batch_limit(normalized_ad_group_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--adgroup-ids", normalized_ad_group_ids])
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        batch_error = check_batch_limit(normalized_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--ids", normalized_ids])
    if retargeting_list_ids is not None:
        args.extend(["--retargeting-list-ids", retargeting_list_ids])
    if interest_ids is not None:
        args.extend(["--interest-ids", interest_ids])
    if states is not None:
        args.extend(["--states", states])
    if limit is not None:
        args.extend(["--limit", str(limit)])
    if fetch_all:
        args.append("--fetch-all")
    if fields is not None:
        args.extend(["--fields", fields])

    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(name="audiencetargets_add")
@handle_cli_errors
def audience_targets_add(
    ad_group_id: int,
    retargeting_list_id: int | None = None,
    interest_id: int | None = None,
    bid: int | None = None,
    priority: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Add an audience target to an ad group.

    CLI 0.3.8 dropped --json. Provide exactly one of retargeting_list_id or
    interest_id (CLI rejects both at once).

    Args:
        ad_group_id: Ad group ID to add the target to.
        retargeting_list_id: Retargeting list ID to target.
        interest_id: Interest ID to target.
        bid: Context bid in micro-units (RUB × 1,000,000); CLI 0.2.10+
            rejects values 0 < x < 100_000 with a "did you mean × 1_000_000" hint.
        priority: Strategy priority.
        dry_run: Show the direct request without sending it.
    """
    if retargeting_list_id is None and interest_id is None:
        return ToolError(
            error="missing_target",
            message="Provide retargeting_list_id or interest_id.",
        ).__dict__
    if retargeting_list_id is not None and interest_id is not None:
        return ToolError(
            error="conflicting_target",
            message="Pass retargeting_list_id or interest_id, not both.",
        ).__dict__

    args = [
        "audiencetargets",
        "add",
        "--adgroup-id",
        str(ad_group_id),
    ]
    if retargeting_list_id is not None:
        args.extend(["--retargeting-list-id", str(retargeting_list_id)])
    if interest_id is not None:
        args.extend(["--interest-id", str(interest_id)])
    if bid is not None:
        args.extend(["--bid", str(bid)])
    if priority is not None:
        args.extend(["--priority", priority])
    if dry_run:
        args.append("--dry-run")
    return get_runner().run_json(args)


@mcp.tool(name="audiencetargets_delete")
@handle_cli_errors
def audience_targets_delete(ids: str, dry_run: bool = False) -> dict:
    """Delete audience targets.

    Args:
        ids: Comma-separated audience target IDs (max 10).
    """
    return run_single_id_batch(
        get_runner(), "audiencetargets", "delete", ids, dry_run=dry_run
    )


@mcp.tool(name="audiencetargets_suspend")
@handle_cli_errors
def audience_targets_suspend(ids: str, dry_run: bool = False) -> dict:
    """Suspend audience targets.

    Args:
        ids: Comma-separated audience target IDs (max 10).
    """
    return run_single_id_batch(
        get_runner(), "audiencetargets", "suspend", ids, dry_run=dry_run
    )


@mcp.tool(name="audiencetargets_resume")
@handle_cli_errors
def audience_targets_resume(ids: str, dry_run: bool = False) -> dict:
    """Resume suspended audience targets.

    Args:
        ids: Comma-separated audience target IDs (max 10).
    """
    return run_single_id_batch(
        get_runner(), "audiencetargets", "resume", ids, dry_run=dry_run
    )


@mcp.tool(name="audiencetargets_set_bids")
@handle_cli_errors
def audience_targets_set_bids(
    id: int | None = None,
    ad_group_id: int | None = None,
    campaign_id: int | None = None,
    context_bid: int | None = None,
    priority: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Set audience target bids.

    Args:
        id: Audience target ID.
        ad_group_id: Ad group ID.
        campaign_id: Campaign ID.
        context_bid: Context bid in micro-units (RUB × 1,000,000); CLI 0.2.10+
            rejects values 0 < x < 100_000 with a "did you mean × 1_000_000" hint.
        priority: Strategy priority.
    """
    return run_set_bids(
        get_runner(),
        "audiencetargets",
        id=id,
        ad_group_id=ad_group_id,
        campaign_id=campaign_id,
        bid_fields=(("--context-bid", context_bid), ("--priority", priority)),
        missing_update_message="Provide at least one of: context_bid, priority",
        dry_run=dry_run,
    )
