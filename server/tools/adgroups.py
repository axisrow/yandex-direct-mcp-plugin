"""MCP tools for ad group management."""

import json

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit

MAX_BATCH_SIZE = 10


def _check_batch_limit(ids_str: str) -> ToolError | None:
    """Validate batch size of comma-separated IDs."""
    return check_batch_limit(ids_str, MAX_BATCH_SIZE)


@mcp.tool(name="adgroups_get")
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
    normalized_campaign_ids = campaign_ids.strip() if campaign_ids is not None else None
    if normalized_campaign_ids:
        batch_error = _check_batch_limit(normalized_campaign_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--campaign-ids", normalized_campaign_ids])
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        batch_error = _check_batch_limit(normalized_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--ids", normalized_ids])
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
    extra_json: str | dict | None = None,
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
        json_str = (
            json.dumps(extra_json) if isinstance(extra_json, dict) else extra_json
        )
        args.extend(["--json", json_str])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def adgroups_update(
    id: str,
    name: str | None = None,
    status: str | None = None,
    extra_json: str | dict | None = None,
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
        json_str = (
            json.dumps(extra_json) if isinstance(extra_json, dict) else extra_json
        )
        args.extend(["--json", json_str])
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
