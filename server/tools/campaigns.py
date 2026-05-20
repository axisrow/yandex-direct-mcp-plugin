"""MCP tools for campaign management."""

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
    start_date: str | None = None,
    end_date: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Update campaign fields.

    CLI 0.3.8 removed the free-form `--json` flag from `campaigns update`;
    only the typed flags listed below are accepted. Notification / strategy
    changes are not yet typed in CLI — file an upstream issue if needed.

    Args:
        id: Campaign ID to update.
        name: Optional new campaign name.
        status: Optional new campaign status.
        budget: Optional new daily budget in micro-units (RUB × 1,000,000); CLI 0.2.10+
            rejects values 0 < x < 100_000 with a "did you mean × 1_000_000" hint.
        start_date: Optional new start date (YYYY-MM-DD).
        end_date: Optional new end date (YYYY-MM-DD).
        dry_run: Show the direct-cli request without sending it.
    """
    if (
        name is None
        and status is None
        and budget is None
        and start_date is None
        and end_date is None
    ):
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one of: name, status, budget, start_date, end_date",
        ).__dict__

    args = ["campaigns", "update", "--id", str(id)]
    if name:
        args.extend(["--name", name])
    if status:
        args.extend(["--status", status])
    if budget is not None:
        args.extend(["--budget", str(budget)])
    if start_date:
        args.extend(["--start-date", start_date])
    if end_date:
        args.extend(["--end-date", end_date])
    if dry_run:
        args.append("--dry-run")

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
    if start_date:
        result["start_date"] = start_date
    if end_date:
        result["end_date"] = end_date
    return result


@mcp.tool()
@handle_cli_errors
def campaigns_add(
    name: str,
    start_date: str,
    campaign_type: str | None = None,
    budget: int | None = None,
    end_date: str | None = None,
    search_strategy: str | None = None,
    network_strategy: str | None = None,
    settings: list[str] | None = None,
    filter_average_cpc: int | None = None,
    counter_id: int | None = None,
    dry_run: bool = False,
) -> dict:
    """Create a new campaign.

    CLI 0.3.8 removed the free-form `--json` flag from `campaigns add`. Use
    `--search-strategy` / `--network-strategy` / `--setting` typed flags.

    Note: CLI 0.3.8 does not yet expose Goals (CPA pay-for-conversion),
    Notification, NetworkSettings or TimeTargeting — these have to be set
    via the Direct web UI after `campaigns_add` until a future CLI release.

    Args:
        name: Campaign name.
        start_date: Campaign start date in YYYY-MM-DD format.
        campaign_type: Campaign type (optional).
        budget: Optional daily budget in micro-units (RUB × 1,000,000); CLI 0.2.10+
            rejects values 0 < x < 100_000 with a "did you mean × 1_000_000" hint.
        end_date: Optional campaign end date in YYYY-MM-DD format.
        search_strategy: Optional search bidding strategy type
            (e.g. "HIGHEST_POSITION", "WB_MAXIMUM_CLICKS").
        network_strategy: Optional network bidding strategy type
            (e.g. "MAXIMUM_COVERAGE", "WB_MAXIMUM_CLICKS").
        settings: Optional list of campaign settings as OPTION=VALUE strings
            (e.g. ["EnableEmailNotification=YES", "RequireServicing=NO"]).
        filter_average_cpc: Optional Smart campaign filter average CPC in micro-units
            (RUB × 1,000,000); CLI 0.2.10+ rejects values 0 < x < 100_000.
        counter_id: Optional Smart campaign Metrica counter ID.
        dry_run: Show the direct-cli request without sending it.
    """
    args = ["campaigns", "add", "--name", name, "--start-date", start_date]
    if campaign_type:
        args.extend(["--type", campaign_type])
    if budget is not None:
        args.extend(["--budget", str(budget)])
    if end_date:
        args.extend(["--end-date", end_date])
    if search_strategy:
        args.extend(["--search-strategy", search_strategy])
    if network_strategy:
        args.extend(["--network-strategy", network_strategy])
    if settings:
        for setting in settings:
            args.extend(["--setting", setting])
    if filter_average_cpc is not None:
        args.extend(["--filter-average-cpc", str(filter_average_cpc)])
    if counter_id is not None:
        args.extend(["--counter-id", str(counter_id)])
    if dry_run:
        args.append("--dry-run")
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
