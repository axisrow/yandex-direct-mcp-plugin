"""MCP tools for ad group management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit

MAX_BATCH_SIZE = 10


def _check_batch_limit(ids_str: str) -> ToolError | None:
    """Validate batch size of comma-separated IDs."""
    return check_batch_limit(ids_str, MAX_BATCH_SIZE)


@mcp.tool()
@handle_cli_errors
def adgroups_list(campaign_ids: str) -> list[dict] | dict:
    """List ad groups in specified campaigns.

    Args:
        campaign_ids: Comma-separated campaign IDs (max 10).
    """
    batch_error = _check_batch_limit(campaign_ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    return runner.run_json(
        ["adgroups", "get", "--campaign-ids", campaign_ids, "--format", "json"]
    )


@mcp.tool()
@handle_cli_errors
def adgroups_add(campaign_id: str, name: str, region_ids: str) -> dict:
    """Create a new ad group.

    Args:
        campaign_id: Campaign ID to add the ad group to.
        name: Ad group name.
        region_ids: Comma-separated region IDs for targeting.
    """
    runner = get_runner()
    result = runner.run_json(
        [
            "adgroups",
            "add",
            "--campaign-id",
            campaign_id,
            "--name",
            name,
            "--region-ids",
            region_ids,
            "--format",
            "json",
        ]
    )
    return result


@mcp.tool()
@handle_cli_errors
def adgroups_update(id: str, name: str | None = None) -> dict:
    """Update an ad group.

    Args:
        id: Ad group ID to update.
        name: New name for the ad group. If None, only updates other fields.
    """
    runner = get_runner()
    result = runner.run_json(
        ["adgroups", "update", "--id", id, "--name", name, "--format", "json"]
    )
    return result


@mcp.tool()
@handle_cli_errors
def adgroups_delete(ids: str) -> dict:
    """Delete ad groups.

    Args:
        ids: Comma-separated ad group IDs (max 10).
    """
    batch_error = _check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(["adgroups", "delete", "--ids", ids, "--format", "json"])
    return result
