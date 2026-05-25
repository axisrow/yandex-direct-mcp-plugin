"""MCP tools for campaign management."""

from server.cli.runner import CliAuthError, CliNotFoundError
from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import CliOption, append_cli_options, check_batch_limit

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

CAMPAIGN_MUTATION_OPTIONS = (
    CliOption("settings", "--setting", repeat=True),
    CliOption("search_strategy", "--search-strategy"),
    CliOption("network_strategy", "--network-strategy"),
    CliOption("filter_average_cpc", "--filter-average-cpc"),
    CliOption("counter_id", "--counter-id"),
    CliOption("counter_ids", "--counter-ids"),
    CliOption("dynamic_placement_search_results", "--dynamic-placement-search-results"),
    CliOption(
        "dynamic_placement_product_gallery",
        "--dynamic-placement-product-gallery",
    ),
    CliOption("goal_id", "--goal-id"),
    CliOption("priority_goals", "--priority-goals"),
    CliOption("relevant_keywords_budget_percent", "--relevant-keywords-budget-percent"),
    CliOption("relevant_keywords_mode", "--relevant-keywords-mode"),
    CliOption(
        "relevant_keywords_optimize_goal_id",
        "--relevant-keywords-optimize-goal-id",
    ),
    CliOption("attribution_model", "--attribution-model"),
    CliOption("package_strategy_id", "--package-strategy-id"),
    CliOption(
        "package_strategy_from_campaign_id", "--package-strategy-from-campaign-id"
    ),
    CliOption("package_platform_search", "--package-platform-search"),
    CliOption("package_platform_search_result", "--package-platform-search-result"),
    CliOption("package_platform_product_gallery", "--package-platform-product-gallery"),
    CliOption("package_platform_maps", "--package-platform-maps"),
    CliOption(
        "package_platform_search_organization_list",
        "--package-platform-search-organization-list",
    ),
    CliOption("package_platform_network", "--package-platform-network"),
    CliOption("package_platform_dynamic_places", "--package-platform-dynamic-places"),
    CliOption("negative_keyword_shared_set_ids", "--negative-keyword-shared-set-ids"),
    CliOption("frequency_cap_impressions", "--frequency-cap-impressions"),
    CliOption("frequency_cap_period_days", "--frequency-cap-period-days"),
    CliOption("frequency_cap_period_all", "--frequency-cap-period-all", is_flag=True),
    CliOption("video_target", "--video-target"),
    CliOption("average_cpa", "--average-cpa"),
    CliOption("crr", "--crr"),
    CliOption("bid_ceiling", "--bid-ceiling"),
    CliOption("notification", "--notification"),
    CliOption("time_targeting", "--time-targeting"),
    CliOption("client_info", "--client-info"),
    CliOption("sms_events", "--sms-events"),
    CliOption("sms_time_from", "--sms-time-from"),
    CliOption("sms_time_to", "--sms-time-to"),
    CliOption("notification_email", "--notification-email"),
    CliOption(
        "notification_check_position_interval",
        "--notification-check-position-interval",
    ),
    CliOption("notification_warning_balance", "--notification-warning-balance"),
    CliOption("notification_send_account_news", "--notification-send-account-news"),
    CliOption("notification_send_warnings", "--notification-send-warnings"),
    CliOption("time_zone", "--time-zone"),
    CliOption("negative_keywords", "--negative-keywords"),
    CliOption("blocked_ips", "--blocked-ips"),
    CliOption("excluded_sites", "--excluded-sites"),
    CliOption("time_targeting_schedule", "--time-targeting-schedule", repeat=True),
    CliOption("consider_working_weekends", "--consider-working-weekends"),
    CliOption("holidays_suspend_on_holidays", "--holidays-suspend-on-holidays"),
    CliOption("holidays_bid_percent", "--holidays-bid-percent"),
    CliOption("holidays_start_hour", "--holidays-start-hour"),
    CliOption("holidays_end_hour", "--holidays-end-hour"),
    CliOption("tracking_params", "--tracking-params"),
)


def _provided_update_value(value: object) -> bool:
    """Return whether an optional update value should satisfy the update guard."""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


@mcp.tool(name="campaigns_get")
@handle_cli_errors
def campaigns_list(
    state: str | None = None,
    ids: str | None = None,
    status: str | None = None,
    statuses: str | None = None,
    states: str | None = None,
    types: str | None = None,
    payment_statuses: str | None = None,
    limit: int | None = None,
    fetch_all: bool = False,
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
    if statuses is not None:
        args.extend(["--statuses", statuses])
    if states is not None:
        args.extend(["--states", states])
    if types is not None:
        args.extend(["--types", types])
    if payment_statuses is not None:
        args.extend(["--payment-statuses", payment_statuses])
    if limit is not None:
        args.extend(["--limit", str(limit)])
    if fetch_all:
        args.append("--fetch-all")
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
    settings: list[str] | None = None,
    counter_id: int | None = None,
    counter_ids: str | None = None,
    dynamic_placement_search_results: str | None = None,
    dynamic_placement_product_gallery: str | None = None,
    priority_goals: str | None = None,
    relevant_keywords_budget_percent: int | None = None,
    relevant_keywords_mode: str | None = None,
    relevant_keywords_optimize_goal_id: int | None = None,
    attribution_model: str | None = None,
    package_strategy_id: int | None = None,
    package_strategy_from_campaign_id: int | None = None,
    package_platform_search: str | None = None,
    package_platform_search_result: str | None = None,
    package_platform_product_gallery: str | None = None,
    package_platform_maps: str | None = None,
    package_platform_search_organization_list: str | None = None,
    package_platform_network: str | None = None,
    package_platform_dynamic_places: str | None = None,
    negative_keyword_shared_set_ids: str | None = None,
    frequency_cap_impressions: int | None = None,
    frequency_cap_period_days: int | None = None,
    frequency_cap_period_all: bool = False,
    video_target: str | None = None,
    notification: str | None = None,
    time_targeting: str | None = None,
    client_info: str | None = None,
    sms_events: str | None = None,
    sms_time_from: str | None = None,
    sms_time_to: str | None = None,
    notification_email: str | None = None,
    notification_check_position_interval: str | None = None,
    notification_warning_balance: int | None = None,
    notification_send_account_news: str | None = None,
    notification_send_warnings: str | None = None,
    time_zone: str | None = None,
    negative_keywords: str | None = None,
    blocked_ips: str | None = None,
    excluded_sites: str | None = None,
    time_targeting_schedule: list[str] | None = None,
    consider_working_weekends: str | None = None,
    holidays_suspend_on_holidays: str | None = None,
    holidays_bid_percent: int | None = None,
    holidays_start_hour: int | None = None,
    holidays_end_hour: int | None = None,
    campaign_type: str | None = None,
    tracking_params: str | None = None,
    notification_json: str | None = None,
    time_targeting_json: str | None = None,
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
        dry_run: Show the direct request without sending it.
    """
    values = locals()
    if notification is None and notification_json is not None:
        values["notification"] = notification_json
    if time_targeting is None and time_targeting_json is not None:
        values["time_targeting"] = time_targeting_json
    optional_values = [
        value
        for key, value in values.items()
        if key not in {"id", "dry_run", "notification_json", "time_targeting_json"}
    ]
    if not any(_provided_update_value(value) for value in optional_values):
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one typed campaign field to update.",
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
    if campaign_type is not None:
        args.extend(["--type", campaign_type])
    append_cli_options(args, values, CAMPAIGN_MUTATION_OPTIONS)
    if dry_run:
        args.append("--dry-run")

    runner = get_runner()
    try:
        cli_output = runner.run_json(args)
    except (CliAuthError, CliNotFoundError):
        raise
    except Exception as exc:
        if "not found" in str(exc).lower():
            return ToolError(
                error="not_found", message=f"Campaign '{id}' not found"
            ).__dict__
        raise
    if dry_run:
        return {
            "dry_run": True,
            "command": ["direct", *args],
            "request_body": cli_output,
        }
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
    counter_ids: str | None = None,
    goal_id: int | None = None,
    priority_goals: str | None = None,
    average_cpa: int | None = None,
    crr: int | None = None,
    bid_ceiling: int | None = None,
    dynamic_placement_search_results: str | None = None,
    dynamic_placement_product_gallery: str | None = None,
    relevant_keywords_budget_percent: int | None = None,
    relevant_keywords_mode: str | None = None,
    relevant_keywords_optimize_goal_id: int | None = None,
    attribution_model: str | None = None,
    package_strategy_id: int | None = None,
    package_strategy_from_campaign_id: int | None = None,
    package_platform_search: str | None = None,
    package_platform_search_result: str | None = None,
    package_platform_product_gallery: str | None = None,
    package_platform_maps: str | None = None,
    package_platform_search_organization_list: str | None = None,
    package_platform_network: str | None = None,
    package_platform_dynamic_places: str | None = None,
    negative_keyword_shared_set_ids: str | None = None,
    frequency_cap_impressions: int | None = None,
    frequency_cap_period_days: int | None = None,
    frequency_cap_period_all: bool = False,
    video_target: str | None = None,
    notification: str | None = None,
    time_targeting: str | None = None,
    client_info: str | None = None,
    sms_events: str | None = None,
    sms_time_from: str | None = None,
    sms_time_to: str | None = None,
    notification_email: str | None = None,
    notification_check_position_interval: str | None = None,
    notification_warning_balance: int | None = None,
    notification_send_account_news: str | None = None,
    notification_send_warnings: str | None = None,
    time_zone: str | None = None,
    negative_keywords: str | None = None,
    blocked_ips: str | None = None,
    excluded_sites: str | None = None,
    time_targeting_schedule: list[str] | None = None,
    consider_working_weekends: str | None = None,
    holidays_suspend_on_holidays: str | None = None,
    holidays_bid_percent: int | None = None,
    holidays_start_hour: int | None = None,
    holidays_end_hour: int | None = None,
    tracking_params: str | None = None,
    notification_json: str | None = None,
    time_targeting_json: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Create a new campaign.

    CLI 0.3.9 enforces strict WSDL parity for CPA strategies. Incompatible
    combinations (e.g. `--crr` on AVERAGE_CPA, `--priority-goals` without a
    `*_MULTIPLE_GOALS` strategy, `--counter-ids` on Smart) are rejected by the
    CLI with `UsageError` before any API call — the plugin does not duplicate
    these cross-field checks.

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
        counter_id: Optional Smart campaign Metrika counter ID (single).
        counter_ids: Optional comma-separated Metrika counter IDs for
            TextCampaign / DynamicTextCampaign (`CounterIds`).
        goal_id: Optional single Metrika goal ID for AVERAGE_CPA /
            PAY_FOR_CONVERSION_CRR / AVERAGE_CPA_PER_CAMPAIGN /
            AVERAGE_CPA_PER_FILTER strategies.
        priority_goals: Optional comma-separated 'goal_id:value' pairs for
            AVERAGE_CPA_MULTIPLE_GOALS / PAY_FOR_CONVERSION_MULTIPLE_GOALS.
        average_cpa: Optional target CPA in micro-units (RUB × 1,000,000)
            for AVERAGE_CPA strategies.
        crr: Optional cost-revenue-ratio percentage for PAY_FOR_CONVERSION_CRR.
        bid_ceiling: Optional bid ceiling in micro-units for the chosen
            CPA strategy.
        notification_json: Optional JSON for `CampaignBase.Notification`
            ({"SmsSettings": {...}, "EmailSettings": {...}}).
        time_targeting_json: Optional JSON for `CampaignAddItem.TimeTargeting`
            ({"Schedule": [...], "ConsiderWorkingWeekends": "YES|NO", ...}).
        dry_run: Show the direct request without sending it.
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
    if counter_ids:
        args.extend(["--counter-ids", counter_ids])
    if goal_id is not None:
        args.extend(["--goal-id", str(goal_id)])
    if priority_goals:
        args.extend(["--priority-goals", priority_goals])
    if average_cpa is not None:
        args.extend(["--average-cpa", str(average_cpa)])
    if crr is not None:
        args.extend(["--crr", str(crr)])
    if bid_ceiling is not None:
        args.extend(["--bid-ceiling", str(bid_ceiling)])
    values = locals()
    if notification is None and notification_json is not None:
        values["notification"] = notification_json
    if time_targeting is None and time_targeting_json is not None:
        values["time_targeting"] = time_targeting_json
    for already_appended in (
        "search_strategy",
        "network_strategy",
        "settings",
        "filter_average_cpc",
        "counter_id",
        "counter_ids",
        "goal_id",
        "priority_goals",
        "average_cpa",
        "crr",
        "bid_ceiling",
    ):
        values[already_appended] = None
    append_cli_options(args, values, CAMPAIGN_MUTATION_OPTIONS)
    if dry_run:
        args.append("--dry-run")
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def campaigns_delete(ids: str, dry_run: bool = False) -> dict:
    """Delete campaigns.

    Args:
        ids: Comma-separated campaign IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(
        get_runner(), "campaigns", "delete", ids, dry_run=dry_run
    )


@mcp.tool()
@handle_cli_errors
def campaigns_archive(ids: str, dry_run: bool = False) -> dict:
    """Archive campaigns.

    Args:
        ids: Comma-separated campaign IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(
        get_runner(), "campaigns", "archive", ids, dry_run=dry_run
    )


@mcp.tool()
@handle_cli_errors
def campaigns_unarchive(ids: str, dry_run: bool = False) -> dict:
    """Unarchive campaigns.

    Args:
        ids: Comma-separated campaign IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(
        get_runner(), "campaigns", "unarchive", ids, dry_run=dry_run
    )


@mcp.tool()
@handle_cli_errors
def campaigns_suspend(ids: str, dry_run: bool = False) -> dict:
    """Suspend campaigns.

    Args:
        ids: Comma-separated campaign IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(
        get_runner(), "campaigns", "suspend", ids, dry_run=dry_run
    )


@mcp.tool()
@handle_cli_errors
def campaigns_resume(ids: str, dry_run: bool = False) -> dict:
    """Resume suspended campaigns.

    Args:
        ids: Comma-separated campaign IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(
        get_runner(), "campaigns", "resume", ids, dry_run=dry_run
    )
