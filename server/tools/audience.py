"""MCP tools for audience target management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors


@mcp.tool()
@handle_cli_errors
def audience_targets_list(campaign_ids: str) -> list[dict]:
    """List audience targets for specified campaigns.

    Args:
        campaign_ids: Comma-separated campaign IDs (max 10).
    """
    from server.tools.helpers import check_batch_limit

    batch_error = check_batch_limit(campaign_ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(
        ["audiencetargets", "get", "--campaign-ids", campaign_ids, "--format", "json"]
    )
    return result


@mcp.tool()
@handle_cli_errors
def audience_targets_add(campaign_id: str, ad_group_id: str, audience_id: str) -> dict:
    """Add an audience target to a campaign ad group.

    Args:
        campaign_id: Campaign ID to add target to.
        ad_group_id: Ad group ID to add target to.
        audience_id: Audience segment ID to target.
    """
    runner = get_runner()
    result = runner.run_json(
        [
            "audiencetargets",
            "add",
            "--campaign-id",
            campaign_id,
            "--ad-group-id",
            ad_group_id,
            "--audience-id",
            audience_id,
            "--format",
            "json",
        ]
    )
    return result


@mcp.tool()
@handle_cli_errors
def audience_targets_delete(ids: str) -> dict:
    """Delete audience targets.

    Args:
        ids: Comma-separated audience target IDs (max 10).
    """
    from server.tools.helpers import check_batch_limit

    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(
        ["audiencetargets", "delete", "--ids", ids, "--format", "json"]
    )
    return result


@mcp.tool()
@handle_cli_errors
def audience_targets_suspend(ids: str) -> dict:
    """Suspend audience targets.

    Args:
        ids: Comma-separated audience target IDs (max 10).
    """
    from server.tools.helpers import check_batch_limit

    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(
        ["audiencetargets", "suspend", "--ids", ids, "--format", "json"]
    )
    return result


@mcp.tool()
@handle_cli_errors
def audience_targets_resume(ids: str) -> dict:
    """Resume suspended audience targets.

    Args:
        ids: Comma-separated audience target IDs (max 10).
    """
    from server.tools.helpers import check_batch_limit

    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(
        ["audiencetargets", "resume", "--ids", ids, "--format", "json"]
    )
    return result
