"""MCP tools for bid modifier management."""

import json

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit


@mcp.tool(name="bidmodifiers_get")
@handle_cli_errors
def bidmodifiers_list(
    campaign_ids: str | None = None,
    ad_group_ids: str | None = None,
) -> list[dict] | dict:
    """List bid modifiers.

    Args:
        campaign_ids: Comma-separated campaign IDs (optional, max 10).
        ad_group_ids: Comma-separated ad group IDs (optional, max 10).
    """
    args = ["bidmodifiers", "get", "--format", "json"]
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

    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(name="bidmodifiers_set")
@handle_cli_errors
def bidmodifiers_set(
    campaign_id: str,
    modifier_type: str,
    value: int,
    extra_json: str | dict | None = None,
) -> dict:
    """Set bid modifier for a campaign.

    Args:
        campaign_id: Campaign ID.
        modifier_type: Type of modifier (e.g., "DEMOGRAPHICS", "MOBILE").
        value: Modifier percentage integer (0–1300, e.g. 150 for +50%).
        extra_json: Optional JSON string with additional parameters.
    """
    args = [
        "bidmodifiers",
        "set",
        "--campaign-id",
        campaign_id,
        "--type",
        modifier_type,
        "--value",
        str(value),
    ]
    if extra_json is not None:
        json_str = (
            json.dumps(extra_json) if isinstance(extra_json, dict) else extra_json
        )
        args.extend(["--json", json_str])
    runner = get_runner()
    return runner.run_json(args)



@mcp.tool(name="bidmodifiers_delete")
@handle_cli_errors
def bidmodifiers_delete(ids: str) -> dict:
    """Delete bid modifiers.

    Args:
        ids: Comma-separated modifier IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "bidmodifiers", "delete", ids)


@mcp.tool(name="bidmodifiers_add")
@handle_cli_errors
def bidmodifiers_add(
    modifier_type: str,
    value: int,
    campaign_id: str | None = None,
    ad_group_id: str | None = None,
    gender: str | None = None,
    age: str | None = None,
    retargeting_condition_id: str | None = None,
    region_id: str | None = None,
    serp_layout: str | None = None,
    income_grade: str | None = None,
) -> dict:
    """Add a bid modifier."""
    if not any((campaign_id, ad_group_id)):
        return ToolError(
            error="missing_target_scope",
            message="Provide at least one of: campaign_id, ad_group_id",
        ).__dict__

    args = ["bidmodifiers", "add", "--type", modifier_type, "--value", str(value)]
    if campaign_id is not None:
        args.extend(["--campaign-id", campaign_id])
    if ad_group_id is not None:
        args.extend(["--adgroup-id", ad_group_id])
    if gender is not None:
        args.extend(["--gender", gender])
    if age is not None:
        args.extend(["--age", age])
    if retargeting_condition_id is not None:
        args.extend(["--retargeting-condition-id", retargeting_condition_id])
    if region_id is not None:
        args.extend(["--region-id", region_id])
    if serp_layout is not None:
        args.extend(["--serp-layout", serp_layout])
    if income_grade is not None:
        args.extend(["--income-grade", income_grade])

    runner = get_runner()
    return runner.run_json(args)
