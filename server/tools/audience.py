"""MCP tools for audience target management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit, run_single_id_batch


@mcp.tool()
@handle_cli_errors
def audience_targets_list(
    campaign_ids: str | None = None,
    ad_group_ids: str | None = None,
    ids: str | None = None,
) -> list[dict] | dict:
    """List audience targets.

    Args:
        campaign_ids: Comma-separated campaign IDs (optional, max 10).
        ad_group_ids: Comma-separated ad group IDs (optional, max 10).
        ids: Comma-separated audience target IDs (optional, max 10).
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

    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def audience_targets_add(
    ad_group_id: str,
    retargeting_list_id: str,
    bid: str | None = None,
    extra_json: str | None = None,
) -> dict:
    """Add an audience target to an ad group.

    Args:
        ad_group_id: Ad group ID to add target to.
        retargeting_list_id: Retargeting list ID to target.
        bid: Optional bid amount passed directly to the CLI.
        extra_json: Optional JSON string with additional parameters.
    """
    args = [
        "audiencetargets",
        "add",
        "--adgroup-id",
        ad_group_id,
        "--retargeting-list-id",
        retargeting_list_id,
    ]
    if bid is not None:
        args.extend(["--bid", bid])
    if extra_json is not None:
        args.extend(["--json", extra_json])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def audience_targets_delete(ids: str) -> dict:
    """Delete audience targets.

    Args:
        ids: Comma-separated audience target IDs (max 10).
    """
    return run_single_id_batch(get_runner(), "audiencetargets", "delete", ids)


@mcp.tool()
@handle_cli_errors
def audience_targets_suspend(ids: str) -> dict:
    """Suspend audience targets.

    Args:
        ids: Comma-separated audience target IDs (max 10).
    """
    return run_single_id_batch(get_runner(), "audiencetargets", "suspend", ids)


@mcp.tool()
@handle_cli_errors
def audience_targets_resume(ids: str) -> dict:
    """Resume suspended audience targets.

    Args:
        ids: Comma-separated audience target IDs (max 10).
    """
    return run_single_id_batch(get_runner(), "audiencetargets", "resume", ids)
