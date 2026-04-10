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
def adgroups_list(
    campaign_ids: str | None = None,
    ids: str | None = None,
    status: str | None = None,
    types: str | None = None,
) -> list[dict] | dict:
    """List ad groups.

    Args:
        campaign_ids: Comma-separated campaign IDs (optional, max 10).
        ids: Comma-separated ad group IDs (optional, max 10).
        status: Filter by status (optional).
        types: Filter by types (optional).
    """
    args = ["adgroups", "get", "--format", "json"]
    if campaign_ids is not None:
        batch_error = _check_batch_limit(campaign_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--campaign-ids", campaign_ids])
    if ids is not None and ids.strip():
        batch_error = _check_batch_limit(ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--ids", ids])
    if status is not None:
        args.extend(["--status", status])
    if types is not None:
        args.extend(["--types", types])

    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def adgroups_add(
    campaign_id: str,
    name: str,
    region_ids: str | None = None,
    type: str | None = None,
    extra_json: str | None = None,
) -> dict:
    """Create a new ad group.

    Args:
        campaign_id: Campaign ID to add the ad group to.
        name: Ad group name.
        region_ids: Comma-separated region IDs for targeting (optional).
        type: Ad group type (optional, default TEXT_AD_GROUP).
        extra_json: JSON string with additional parameters (optional).
    """
    args = [
        "adgroups",
        "add",
        "--campaign-id",
        campaign_id,
        "--name",
        name,
    ]
    if type is not None:
        args.extend(["--type", type])
    if region_ids is not None:
        args.extend(["--region-ids", region_ids])
    if extra_json is not None:
        args.extend(["--json", extra_json])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def adgroups_update(
    id: str,
    name: str | None = None,
    status: str | None = None,
    extra_json: str | None = None,
) -> dict:
    """Update an ad group.

    Args:
        id: Ad group ID to update.
        name: New name for the ad group (optional).
        status: New status (optional).
        extra_json: JSON string with additional parameters (optional).
    """
    if not any((name, status, extra_json)):
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one of: name, status, extra_json",
        ).__dict__

    args = ["adgroups", "update", "--id", id]
    if name is not None:
        args.extend(["--name", name])
    if status is not None:
        args.extend(["--status", status])
    if extra_json is not None:
        args.extend(["--json", extra_json])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def adgroups_delete(ids: str) -> dict:
    """Delete ad groups.

    Args:
        ids: Comma-separated ad group IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "adgroups", "delete", ids)
