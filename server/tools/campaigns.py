"""MCP tools for campaign management."""

import json

from server.cli.runner import CliAuthError, CliNotFoundError
from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit

CAMPAIGN_GET_SELECTOR_FLAGS = (
    ("text_campaign_fields", "--text-campaign-fields"),
    (
        "text_campaign_search_strategy_placement_types_fields",
        "--text-campaign-search-strategy-placement-types-fields",
    ),
    ("mobile_app_campaign_fields", "--mobile-app-campaign-fields"),
    ("dynamic_text_campaign_fields", "--dynamic-text-campaign-fields"),
    (
        "dynamic_text_campaign_search_strategy_placement_types_fields",
        "--dynamic-text-campaign-search-strategy-placement-types-fields",
    ),
    ("cpm_banner_campaign_fields", "--cpm-banner-campaign-fields"),
    ("smart_campaign_fields", "--smart-campaign-fields"),
    ("unified_campaign_fields", "--unified-campaign-fields"),
    (
        "unified_campaign_search_strategy_placement_types_fields",
        "--unified-campaign-search-strategy-placement-types-fields",
    ),
    (
        "unified_campaign_package_bidding_strategy_platforms_fields",
        "--unified-campaign-package-bidding-strategy-platforms-fields",
    ),
)


@mcp.tool(name="campaigns_get")
@handle_cli_errors
def campaigns_list(
    state: str | None = None,
    ids: str | None = None,
    status: str | None = None,
    types: str | None = None,
    fields: str | None = None,
    text_campaign_fields: str | None = None,
    text_campaign_search_strategy_placement_types_fields: str | None = None,
    mobile_app_campaign_fields: str | None = None,
    dynamic_text_campaign_fields: str | None = None,
    dynamic_text_campaign_search_strategy_placement_types_fields: str | None = None,
    cpm_banner_campaign_fields: str | None = None,
    smart_campaign_fields: str | None = None,
    unified_campaign_fields: str | None = None,
    unified_campaign_search_strategy_placement_types_fields: str | None = None,
    unified_campaign_package_bidding_strategy_platforms_fields: str | None = None,
) -> list[dict] | dict:
    """List advertising campaigns, optionally filtered.

    Args:
        state: Filter by campaign state ("ON" or "OFF"). If None,
            returns all campaigns. Applied client-side.
        ids: Comma-separated campaign IDs (optional, max 10).
        status: Filter by status, e.g. "ACTIVE", "SUSPENDED" (optional).
        types: Filter by types, e.g. "TEXT_CAMPAIGN" (optional).
        fields: Comma-separated common campaign FieldNames (optional).
        text_campaign_fields: Comma-separated TextCampaignFieldNames (optional).
        text_campaign_search_strategy_placement_types_fields: Comma-separated
            TextCampaignSearchStrategyPlacementTypesFieldNames (optional).
        mobile_app_campaign_fields: Comma-separated MobileAppCampaignFieldNames (optional).
        dynamic_text_campaign_fields: Comma-separated DynamicTextCampaignFieldNames (optional).
        dynamic_text_campaign_search_strategy_placement_types_fields: Comma-separated
            DynamicTextCampaignSearchStrategyPlacementTypesFieldNames (optional).
        cpm_banner_campaign_fields: Comma-separated CpmBannerCampaignFieldNames (optional).
        smart_campaign_fields: Comma-separated SmartCampaignFieldNames (optional).
        unified_campaign_fields: Comma-separated UnifiedCampaignFieldNames (optional).
        unified_campaign_search_strategy_placement_types_fields: Comma-separated
            UnifiedCampaignSearchStrategyPlacementTypesFieldNames (optional).
        unified_campaign_package_bidding_strategy_platforms_fields: Comma-separated
            UnifiedCampaignPackageBiddingStrategyPlatformsFieldNames (optional).
    """
    if state is not None and state not in ("ON", "OFF"):
        return ToolError(
            error="invalid_state",
            message=f"State must be 'ON' or 'OFF', got '{state}'",
        ).__dict__

    args = ["campaigns", "get", "--format", "json"]
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        batch_error = check_batch_limit(normalized_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--ids", normalized_ids])
    if status is not None:
        args.extend(["--status", status])
    if types is not None:
        args.extend(["--types", types])
    if fields is not None:
        args.extend(["--fields", fields])
    local_values = locals()
    for option_name, cli_flag in CAMPAIGN_GET_SELECTOR_FLAGS:
        value = local_values[option_name]
        if value is not None:
            args.extend([cli_flag, value])

    runner = get_runner()
    result = runner.run_json(args)

    if isinstance(result, list) and state:
        result = [c for c in result if c.get("State") == state]

    return result


@mcp.tool()
@handle_cli_errors
def campaigns_update(
    id: int,
    name: str | None = None,
    status: str | None = None,
    budget: int | None = None,
    notification: str | dict | None = None,
) -> dict:
    """Update campaign fields.

    Args:
        id: Campaign ID to update.
        name: Optional new campaign name.
        status: Optional new campaign status.
        budget: Optional new daily budget in micro-units (RUB × 1,000,000); CLI 0.2.10+
            rejects values 0 < x < 100_000 with a "did you mean × 1_000_000" hint.
        notification: Optional notification settings (e.g. {"SmsSettings": {"Events": ["MONITORING"]}}).
    """
    if name is None and status is None and budget is None and notification is None:
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one of: name, status, budget, notification",
        ).__dict__

    notification_val: dict | None = None
    if notification is not None:
        if isinstance(notification, dict):
            notification_val = notification
        else:
            try:
                notification_val = json.loads(notification)
            except json.JSONDecodeError:
                return ToolError(
                    error="invalid_json",
                    message=f"notification is not valid JSON: '{notification}'",
                ).__dict__
            if not isinstance(notification_val, dict):
                return ToolError(
                    error="invalid_json",
                    message="notification must be a JSON object",
                ).__dict__

    args = ["campaigns", "update", "--id", str(id)]
    if name:
        args.extend(["--name", name])
    if status:
        args.extend(["--status", status])
    if budget is not None:
        args.extend(["--budget", str(budget)])
    if notification_val is not None:
        args.extend(["--json", json.dumps({"Notification": notification_val})])

    runner = get_runner()
    try:
        runner.run_json(args)
    except (CliAuthError, CliNotFoundError):
        raise
    except Exception as exc:
        if "not found" in str(exc).lower():
            return ToolError(
                error="not_found", message=f"Campaign '{id}' not found"
            ).__dict__
        raise
    result: dict[str, object] = {"success": True, "id": id}
    if name:
        result["name"] = name
    if status:
        result["status"] = status
    if budget is not None:
        result["budget"] = budget
    if notification_val is not None:
        result["notification"] = notification_val
    return result


@mcp.tool()
@handle_cli_errors
def campaigns_add(
    name: str,
    start_date: str,
    campaign_type: str | None = None,
    budget: int | None = None,
    end_date: str | None = None,
    bidding_strategy: str | dict | None = None,
    filter_average_cpc: int | None = None,
    counter_id: int | None = None,
) -> dict:
    """Create a new campaign.

    Args:
        name: Campaign name.
        start_date: Campaign start date in YYYY-MM-DD format.
        campaign_type: Campaign type (optional).
        budget: Optional daily budget in micro-units (RUB × 1,000,000); CLI 0.2.10+
            rejects values 0 < x < 100_000 with a "did you mean × 1_000_000" hint.
        end_date: Optional campaign end date in YYYY-MM-DD format.
        bidding_strategy: Optional bidding strategy (e.g. {"Search": {"BiddingStrategyType": "HIGHEST_POSITION"}}).
        filter_average_cpc: Optional Smart campaign filter average CPC in micro-units
            (RUB × 1,000,000); CLI 0.2.10+ rejects values 0 < x < 100_000.
        counter_id: Optional Smart campaign Metrica counter ID.
    """
    bs_val: dict | None = None
    if bidding_strategy is not None:
        if isinstance(bidding_strategy, dict):
            bs_val = bidding_strategy
        else:
            try:
                bs_val = json.loads(bidding_strategy)
            except json.JSONDecodeError:
                return ToolError(
                    error="invalid_json",
                    message=f"bidding_strategy is not valid JSON: '{bidding_strategy}'",
                ).__dict__
            if not isinstance(bs_val, dict):
                return ToolError(
                    error="invalid_json",
                    message="bidding_strategy must be a JSON object",
                ).__dict__

    args = ["campaigns", "add", "--name", name, "--start-date", start_date]
    if campaign_type:
        args.extend(["--type", campaign_type])
    if budget is not None:
        args.extend(["--budget", str(budget)])
    if end_date:
        args.extend(["--end-date", end_date])
    if filter_average_cpc is not None:
        args.extend(["--filter-average-cpc", str(filter_average_cpc)])
    if counter_id is not None:
        args.extend(["--counter-id", str(counter_id)])
    if bs_val is not None:
        args.extend(["--json", json.dumps({"BiddingStrategy": bs_val})])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def campaigns_delete(ids: str) -> dict:
    """Delete campaigns.

    Args:
        ids: Comma-separated campaign IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "campaigns", "delete", ids)


@mcp.tool()
@handle_cli_errors
def campaigns_archive(ids: str) -> dict:
    """Archive campaigns.

    Args:
        ids: Comma-separated campaign IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "campaigns", "archive", ids)


@mcp.tool()
@handle_cli_errors
def campaigns_unarchive(ids: str) -> dict:
    """Unarchive campaigns.

    Args:
        ids: Comma-separated campaign IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "campaigns", "unarchive", ids)


@mcp.tool()
@handle_cli_errors
def campaigns_suspend(ids: str) -> dict:
    """Suspend campaigns.

    Args:
        ids: Comma-separated campaign IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "campaigns", "suspend", ids)


@mcp.tool()
@handle_cli_errors
def campaigns_resume(ids: str) -> dict:
    """Resume suspended campaigns.

    Args:
        ids: Comma-separated campaign IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "campaigns", "resume", ids)
