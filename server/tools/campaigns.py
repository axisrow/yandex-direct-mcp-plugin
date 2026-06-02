"""MCP tools for campaign management."""

from server.cli.runner import CliAuthError, CliNotFoundError
from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import (
    CliOption,
    append_cli_options,
    check_batch_limit,
    provided_update_value,
)

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
    # --- TextCampaign Search PlacementTypes (3 flags) ---
    CliOption("search_placement_dynamic_places", "--search-placement-dynamic-places"),
    CliOption("search_placement_product_gallery", "--search-placement-product-gallery"),
    CliOption("search_placement_search_results", "--search-placement-search-results"),
    # --- CpmBannerCampaign bidding strategy (6 flags) ---
    CliOption("average_cpm", "--average-cpm"),
    CliOption("average_cpv", "--average-cpv"),
    CliOption("strategy_auto_continue", "--strategy-auto-continue"),
    CliOption("strategy_end_date", "--strategy-end-date"),
    CliOption("strategy_spend_limit", "--strategy-spend-limit"),
    CliOption("strategy_start_date", "--strategy-start-date"),
    # --- TextCampaign.BiddingStrategy.Search (13 flags) ---
    CliOption("text_search_average_cpc", "--text-search-average-cpc"),
    CliOption("text_search_clicks_per_week", "--text-search-clicks-per-week"),
    CliOption(
        "text_search_custom_period_auto_continue",
        "--text-search-custom-period-auto-continue",
    ),
    CliOption(
        "text_search_custom_period_end_date", "--text-search-custom-period-end-date"
    ),
    CliOption(
        "text_search_custom_period_spend_limit",
        "--text-search-custom-period-spend-limit",
    ),
    CliOption(
        "text_search_custom_period_start_date", "--text-search-custom-period-start-date"
    ),
    CliOption(
        "text_search_exploration_is_custom", "--text-search-exploration-is-custom"
    ),
    CliOption(
        "text_search_exploration_min_budget", "--text-search-exploration-min-budget"
    ),
    CliOption("text_search_pay_cpa", "--text-search-pay-cpa"),
    CliOption("text_search_profitability", "--text-search-profitability"),
    CliOption("text_search_reserve_return", "--text-search-reserve-return"),
    CliOption("text_search_roi_coef", "--text-search-roi-coef"),
    CliOption("text_search_weekly_spend_limit", "--text-search-weekly-spend-limit"),
    # --- TextCampaign.BiddingStrategy.Network (14 flags) ---
    CliOption("text_network_average_cpc", "--text-network-average-cpc"),
    CliOption("text_network_clicks_per_week", "--text-network-clicks-per-week"),
    CliOption(
        "text_network_custom_period_auto_continue",
        "--text-network-custom-period-auto-continue",
    ),
    CliOption(
        "text_network_custom_period_end_date", "--text-network-custom-period-end-date"
    ),
    CliOption(
        "text_network_custom_period_spend_limit",
        "--text-network-custom-period-spend-limit",
    ),
    CliOption(
        "text_network_custom_period_start_date",
        "--text-network-custom-period-start-date",
    ),
    CliOption(
        "text_network_exploration_is_custom", "--text-network-exploration-is-custom"
    ),
    CliOption(
        "text_network_exploration_min_budget", "--text-network-exploration-min-budget"
    ),
    CliOption("text_network_limit_percent", "--text-network-limit-percent"),
    CliOption("text_network_pay_cpa", "--text-network-pay-cpa"),
    CliOption("text_network_profitability", "--text-network-profitability"),
    CliOption("text_network_reserve_return", "--text-network-reserve-return"),
    CliOption("text_network_roi_coef", "--text-network-roi-coef"),
    CliOption("text_network_weekly_spend_limit", "--text-network-weekly-spend-limit"),
    # --- DynamicTextCampaign.BiddingStrategy.Search (17 flags) ---
    CliOption("dyn_search_average_cpa", "--dyn-search-average-cpa"),
    CliOption("dyn_search_average_cpc", "--dyn-search-average-cpc"),
    CliOption("dyn_search_bid_ceiling", "--dyn-search-bid-ceiling"),
    CliOption("dyn_search_clicks_per_week", "--dyn-search-clicks-per-week"),
    CliOption("dyn_search_cpa", "--dyn-search-cpa"),
    CliOption("dyn_search_crr", "--dyn-search-crr"),
    CliOption(
        "dyn_search_custom_period_auto_continue",
        "--dyn-search-custom-period-auto-continue",
    ),
    CliOption(
        "dyn_search_custom_period_end_date", "--dyn-search-custom-period-end-date"
    ),
    CliOption(
        "dyn_search_custom_period_spend_limit", "--dyn-search-custom-period-spend-limit"
    ),
    CliOption(
        "dyn_search_custom_period_start_date", "--dyn-search-custom-period-start-date"
    ),
    CliOption("dyn_search_exploration_budget", "--dyn-search-exploration-budget"),
    CliOption(
        "dyn_search_exploration_budget_custom", "--dyn-search-exploration-budget-custom"
    ),
    CliOption("dyn_search_goal_id", "--dyn-search-goal-id"),
    CliOption("dyn_search_profitability", "--dyn-search-profitability"),
    CliOption("dyn_search_reserve_return", "--dyn-search-reserve-return"),
    CliOption("dyn_search_roi_coef", "--dyn-search-roi-coef"),
    CliOption("dyn_search_weekly_spend_limit", "--dyn-search-weekly-spend-limit"),
    # --- DynamicTextCampaign.BiddingStrategy.Network (18 flags) ---
    CliOption("dyn_network_average_cpa", "--dyn-network-average-cpa"),
    CliOption("dyn_network_average_cpc", "--dyn-network-average-cpc"),
    CliOption("dyn_network_bid_ceiling", "--dyn-network-bid-ceiling"),
    CliOption("dyn_network_clicks_per_week", "--dyn-network-clicks-per-week"),
    CliOption("dyn_network_cpa", "--dyn-network-cpa"),
    CliOption("dyn_network_crr", "--dyn-network-crr"),
    CliOption(
        "dyn_network_custom_period_auto_continue",
        "--dyn-network-custom-period-auto-continue",
    ),
    CliOption(
        "dyn_network_custom_period_end_date", "--dyn-network-custom-period-end-date"
    ),
    CliOption(
        "dyn_network_custom_period_spend_limit",
        "--dyn-network-custom-period-spend-limit",
    ),
    CliOption(
        "dyn_network_custom_period_start_date", "--dyn-network-custom-period-start-date"
    ),
    CliOption("dyn_network_exploration_budget", "--dyn-network-exploration-budget"),
    CliOption(
        "dyn_network_exploration_budget_custom",
        "--dyn-network-exploration-budget-custom",
    ),
    CliOption("dyn_network_goal_id", "--dyn-network-goal-id"),
    CliOption("dyn_network_limit_percent", "--dyn-network-limit-percent"),
    CliOption("dyn_network_profitability", "--dyn-network-profitability"),
    CliOption("dyn_network_reserve_return", "--dyn-network-reserve-return"),
    CliOption("dyn_network_roi_coef", "--dyn-network-roi-coef"),
    CliOption("dyn_network_weekly_spend_limit", "--dyn-network-weekly-spend-limit"),
    # --- SmartCampaign.BiddingStrategy.Search (18 flags) ---
    CliOption("smart_search_average_cpa", "--smart-search-average-cpa"),
    CliOption("smart_search_average_cpc", "--smart-search-average-cpc"),
    CliOption("smart_search_bid_ceiling", "--smart-search-bid-ceiling"),
    CliOption("smart_search_cp_auto_continue", "--smart-search-cp-auto-continue"),
    CliOption("smart_search_cp_end_date", "--smart-search-cp-end-date"),
    CliOption("smart_search_cp_spend_limit", "--smart-search-cp-spend-limit"),
    CliOption("smart_search_cp_start_date", "--smart-search-cp-start-date"),
    CliOption("smart_search_cpa", "--smart-search-cpa"),
    CliOption("smart_search_crr", "--smart-search-crr"),
    CliOption("smart_search_exploration_min", "--smart-search-exploration-min"),
    CliOption(
        "smart_search_exploration_min_custom", "--smart-search-exploration-min-custom"
    ),
    CliOption("smart_search_filter_average_cpa", "--smart-search-filter-average-cpa"),
    CliOption("smart_search_filter_average_cpc", "--smart-search-filter-average-cpc"),
    CliOption("smart_search_goal_id", "--smart-search-goal-id"),
    CliOption("smart_search_profitability", "--smart-search-profitability"),
    CliOption("smart_search_reserve_return", "--smart-search-reserve-return"),
    CliOption("smart_search_roi_coef", "--smart-search-roi-coef"),
    CliOption("smart_search_weekly_spend_limit", "--smart-search-weekly-spend-limit"),
    # --- SmartCampaign.BiddingStrategy.Network (19 flags) ---
    CliOption("smart_network_average_cpa", "--smart-network-average-cpa"),
    CliOption("smart_network_average_cpc", "--smart-network-average-cpc"),
    CliOption("smart_network_bid_ceiling", "--smart-network-bid-ceiling"),
    CliOption("smart_network_cp_auto_continue", "--smart-network-cp-auto-continue"),
    CliOption("smart_network_cp_end_date", "--smart-network-cp-end-date"),
    CliOption("smart_network_cp_spend_limit", "--smart-network-cp-spend-limit"),
    CliOption("smart_network_cp_start_date", "--smart-network-cp-start-date"),
    CliOption("smart_network_cpa", "--smart-network-cpa"),
    CliOption("smart_network_crr", "--smart-network-crr"),
    CliOption("smart_network_exploration_min", "--smart-network-exploration-min"),
    CliOption(
        "smart_network_exploration_min_custom", "--smart-network-exploration-min-custom"
    ),
    CliOption("smart_network_filter_average_cpa", "--smart-network-filter-average-cpa"),
    CliOption("smart_network_filter_average_cpc", "--smart-network-filter-average-cpc"),
    CliOption("smart_network_goal_id", "--smart-network-goal-id"),
    CliOption("smart_network_limit_percent", "--smart-network-limit-percent"),
    CliOption("smart_network_profitability", "--smart-network-profitability"),
    CliOption("smart_network_reserve_return", "--smart-network-reserve-return"),
    CliOption("smart_network_roi_coef", "--smart-network-roi-coef"),
    CliOption("smart_network_weekly_spend_limit", "--smart-network-weekly-spend-limit"),
    # --- UnifiedCampaign.BiddingStrategy.Search (11 flags) ---
    CliOption("unified_search_average_cpc", "--unified-search-average-cpc"),
    CliOption(
        "unified_search_custom_period_auto_continue",
        "--unified-search-custom-period-auto-continue",
    ),
    CliOption(
        "unified_search_custom_period_end_date",
        "--unified-search-custom-period-end-date",
    ),
    CliOption(
        "unified_search_custom_period_spend_limit",
        "--unified-search-custom-period-spend-limit",
    ),
    CliOption(
        "unified_search_custom_period_start_date",
        "--unified-search-custom-period-start-date",
    ),
    CliOption(
        "unified_search_exploration_is_custom", "--unified-search-exploration-is-custom"
    ),
    CliOption(
        "unified_search_exploration_min_budget",
        "--unified-search-exploration-min-budget",
    ),
    CliOption("unified_search_pay_cpa", "--unified-search-pay-cpa"),
    CliOption("unified_search_placement_maps", "--unified-search-placement-maps"),
    CliOption(
        "unified_search_placement_search_organization_list",
        "--unified-search-placement-search-organization-list",
    ),
    CliOption(
        "unified_search_weekly_spend_limit", "--unified-search-weekly-spend-limit"
    ),
    # --- UnifiedCampaign.BiddingStrategy.Network (9 flags) ---
    CliOption("unified_network_average_cpc", "--unified-network-average-cpc"),
    CliOption("unified_network_cpa", "--unified-network-cpa"),
    CliOption(
        "unified_network_custom_period_auto_continue",
        "--unified-network-custom-period-auto-continue",
    ),
    CliOption(
        "unified_network_custom_period_end_date",
        "--unified-network-custom-period-end-date",
    ),
    CliOption(
        "unified_network_custom_period_spend_limit",
        "--unified-network-custom-period-spend-limit",
    ),
    CliOption(
        "unified_network_custom_period_start_date",
        "--unified-network-custom-period-start-date",
    ),
    CliOption(
        "unified_network_exploration_is_custom",
        "--unified-network-exploration-is-custom",
    ),
    CliOption(
        "unified_network_exploration_min_budget",
        "--unified-network-exploration-min-budget",
    ),
    CliOption(
        "unified_network_weekly_spend_limit", "--unified-network-weekly-spend-limit"
    ),
    # --- MobileAppCampaign.BiddingStrategy.Search (9 flags) ---
    CliOption("mobile_search_average_cpc", "--mobile-search-average-cpc"),
    CliOption("mobile_search_average_cpi", "--mobile-search-average-cpi"),
    CliOption("mobile_search_bid_ceiling", "--mobile-search-bid-ceiling"),
    CliOption("mobile_search_clicks_per_week", "--mobile-search-clicks-per-week"),
    CliOption(
        "mobile_search_custom_period_auto_continue",
        "--mobile-search-custom-period-auto-continue",
    ),
    CliOption(
        "mobile_search_custom_period_end_date", "--mobile-search-custom-period-end-date"
    ),
    CliOption(
        "mobile_search_custom_period_spend_limit",
        "--mobile-search-custom-period-spend-limit",
    ),
    CliOption(
        "mobile_search_custom_period_start_date",
        "--mobile-search-custom-period-start-date",
    ),
    CliOption("mobile_search_weekly_spend_limit", "--mobile-search-weekly-spend-limit"),
    # --- MobileAppCampaign.BiddingStrategy.Network (10 flags) ---
    CliOption("mobile_network_average_cpc", "--mobile-network-average-cpc"),
    CliOption("mobile_network_average_cpi", "--mobile-network-average-cpi"),
    CliOption("mobile_network_bid_ceiling", "--mobile-network-bid-ceiling"),
    CliOption("mobile_network_clicks_per_week", "--mobile-network-clicks-per-week"),
    CliOption(
        "mobile_network_custom_period_auto_continue",
        "--mobile-network-custom-period-auto-continue",
    ),
    CliOption(
        "mobile_network_custom_period_end_date",
        "--mobile-network-custom-period-end-date",
    ),
    CliOption(
        "mobile_network_custom_period_spend_limit",
        "--mobile-network-custom-period-spend-limit",
    ),
    CliOption(
        "mobile_network_custom_period_start_date",
        "--mobile-network-custom-period-start-date",
    ),
    CliOption("mobile_network_limit_percent", "--mobile-network-limit-percent"),
    CliOption(
        "mobile_network_weekly_spend_limit", "--mobile-network-weekly-spend-limit"
    ),
)

# Update-only flags: CLI exposes `--*-budget-type` only on `campaigns update`,
# letting callers switch a strategy between WEEKLY_BUDGET and CUSTOM_PERIOD_BUDGET
# without re-sending the rest of the strategy. Values are validated by CLI.
CAMPAIGN_UPDATE_ONLY_OPTIONS = (
    CliOption("text_search_budget_type", "--text-search-budget-type"),
    CliOption("text_network_budget_type", "--text-network-budget-type"),
    CliOption("dyn_search_budget_type", "--dyn-search-budget-type"),
    CliOption("dyn_network_budget_type", "--dyn-network-budget-type"),
    CliOption("smart_search_budget_type", "--smart-search-budget-type"),
    CliOption("smart_network_budget_type", "--smart-network-budget-type"),
    CliOption("unified_search_budget_type", "--unified-search-budget-type"),
    CliOption("unified_network_budget_type", "--unified-network-budget-type"),
    CliOption("mobile_search_budget_type", "--mobile-search-budget-type"),
    CliOption("mobile_network_budget_type", "--mobile-network-budget-type"),
)


@mcp.tool(
    name="campaigns_get",
    description="List advertising campaigns, with optional state/status/type/ID filters. Read-only; use campaigns_add to create or campaigns_update to modify. Call tool_help('campaigns_get') for parameters.",
)
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


@mcp.tool(
    description="Update fields of an existing campaign identified by id (name, budget, status, bidding strategy, etc.). Use campaigns_add to create a new campaign instead. Call tool_help('campaigns_update') for parameters.",
)
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
    search_strategy: str | None = None,
    network_strategy: str | None = None,
    goal_id: int | None = None,
    average_cpa: int | None = None,
    crr: int | None = None,
    bid_ceiling: int | None = None,
    # --- TextCampaign Search PlacementTypes (3 flags) ---
    search_placement_dynamic_places: str | None = None,
    search_placement_product_gallery: str | None = None,
    search_placement_search_results: str | None = None,
    # --- CpmBannerCampaign bidding strategy (6 flags) ---
    average_cpm: int | None = None,
    average_cpv: int | None = None,
    strategy_auto_continue: str | None = None,
    strategy_end_date: str | None = None,
    strategy_spend_limit: int | None = None,
    strategy_start_date: str | None = None,
    # --- TextCampaign.BiddingStrategy.Search (13 flags) ---
    text_search_average_cpc: int | None = None,
    text_search_clicks_per_week: int | None = None,
    text_search_custom_period_auto_continue: str | None = None,
    text_search_custom_period_end_date: str | None = None,
    text_search_custom_period_spend_limit: int | None = None,
    text_search_custom_period_start_date: str | None = None,
    text_search_exploration_is_custom: str | None = None,
    text_search_exploration_min_budget: int | None = None,
    text_search_pay_cpa: int | None = None,
    text_search_profitability: int | None = None,
    text_search_reserve_return: int | None = None,
    text_search_roi_coef: int | None = None,
    text_search_weekly_spend_limit: int | None = None,
    # --- TextCampaign.BiddingStrategy.Network (14 flags) ---
    text_network_average_cpc: int | None = None,
    text_network_clicks_per_week: int | None = None,
    text_network_custom_period_auto_continue: str | None = None,
    text_network_custom_period_end_date: str | None = None,
    text_network_custom_period_spend_limit: int | None = None,
    text_network_custom_period_start_date: str | None = None,
    text_network_exploration_is_custom: str | None = None,
    text_network_exploration_min_budget: int | None = None,
    text_network_limit_percent: int | None = None,
    text_network_pay_cpa: int | None = None,
    text_network_profitability: int | None = None,
    text_network_reserve_return: int | None = None,
    text_network_roi_coef: int | None = None,
    text_network_weekly_spend_limit: int | None = None,
    # --- DynamicTextCampaign.BiddingStrategy.Search (17 flags) ---
    dyn_search_average_cpa: int | None = None,
    dyn_search_average_cpc: int | None = None,
    dyn_search_bid_ceiling: int | None = None,
    dyn_search_clicks_per_week: int | None = None,
    dyn_search_cpa: int | None = None,
    dyn_search_crr: int | None = None,
    dyn_search_custom_period_auto_continue: str | None = None,
    dyn_search_custom_period_end_date: str | None = None,
    dyn_search_custom_period_spend_limit: int | None = None,
    dyn_search_custom_period_start_date: str | None = None,
    dyn_search_exploration_budget: int | None = None,
    dyn_search_exploration_budget_custom: str | None = None,
    dyn_search_goal_id: int | None = None,
    dyn_search_profitability: int | None = None,
    dyn_search_reserve_return: int | None = None,
    dyn_search_roi_coef: int | None = None,
    dyn_search_weekly_spend_limit: int | None = None,
    # --- DynamicTextCampaign.BiddingStrategy.Network (18 flags) ---
    dyn_network_average_cpa: int | None = None,
    dyn_network_average_cpc: int | None = None,
    dyn_network_bid_ceiling: int | None = None,
    dyn_network_clicks_per_week: int | None = None,
    dyn_network_cpa: int | None = None,
    dyn_network_crr: int | None = None,
    dyn_network_custom_period_auto_continue: str | None = None,
    dyn_network_custom_period_end_date: str | None = None,
    dyn_network_custom_period_spend_limit: int | None = None,
    dyn_network_custom_period_start_date: str | None = None,
    dyn_network_exploration_budget: int | None = None,
    dyn_network_exploration_budget_custom: str | None = None,
    dyn_network_goal_id: int | None = None,
    dyn_network_limit_percent: int | None = None,
    dyn_network_profitability: int | None = None,
    dyn_network_reserve_return: int | None = None,
    dyn_network_roi_coef: int | None = None,
    dyn_network_weekly_spend_limit: int | None = None,
    # --- SmartCampaign.BiddingStrategy.Search (18 flags) ---
    smart_search_average_cpa: int | None = None,
    smart_search_average_cpc: int | None = None,
    smart_search_bid_ceiling: int | None = None,
    smart_search_cp_auto_continue: str | None = None,
    smart_search_cp_end_date: str | None = None,
    smart_search_cp_spend_limit: int | None = None,
    smart_search_cp_start_date: str | None = None,
    smart_search_cpa: int | None = None,
    smart_search_crr: int | None = None,
    smart_search_exploration_min: int | None = None,
    smart_search_exploration_min_custom: str | None = None,
    smart_search_filter_average_cpa: int | None = None,
    smart_search_filter_average_cpc: int | None = None,
    smart_search_goal_id: int | None = None,
    smart_search_profitability: int | None = None,
    smart_search_reserve_return: int | None = None,
    smart_search_roi_coef: int | None = None,
    smart_search_weekly_spend_limit: int | None = None,
    # --- SmartCampaign.BiddingStrategy.Network (19 flags) ---
    smart_network_average_cpa: int | None = None,
    smart_network_average_cpc: int | None = None,
    smart_network_bid_ceiling: int | None = None,
    smart_network_cp_auto_continue: str | None = None,
    smart_network_cp_end_date: str | None = None,
    smart_network_cp_spend_limit: int | None = None,
    smart_network_cp_start_date: str | None = None,
    smart_network_cpa: int | None = None,
    smart_network_crr: int | None = None,
    smart_network_exploration_min: int | None = None,
    smart_network_exploration_min_custom: str | None = None,
    smart_network_filter_average_cpa: int | None = None,
    smart_network_filter_average_cpc: int | None = None,
    smart_network_goal_id: int | None = None,
    smart_network_limit_percent: int | None = None,
    smart_network_profitability: int | None = None,
    smart_network_reserve_return: int | None = None,
    smart_network_roi_coef: int | None = None,
    smart_network_weekly_spend_limit: int | None = None,
    # --- UnifiedCampaign.BiddingStrategy.Search (11 flags) ---
    unified_search_average_cpc: int | None = None,
    unified_search_custom_period_auto_continue: str | None = None,
    unified_search_custom_period_end_date: str | None = None,
    unified_search_custom_period_spend_limit: int | None = None,
    unified_search_custom_period_start_date: str | None = None,
    unified_search_exploration_is_custom: str | None = None,
    unified_search_exploration_min_budget: int | None = None,
    unified_search_pay_cpa: int | None = None,
    unified_search_placement_maps: str | None = None,
    unified_search_placement_search_organization_list: str | None = None,
    unified_search_weekly_spend_limit: int | None = None,
    # --- UnifiedCampaign.BiddingStrategy.Network (9 flags) ---
    unified_network_average_cpc: int | None = None,
    unified_network_cpa: int | None = None,
    unified_network_custom_period_auto_continue: str | None = None,
    unified_network_custom_period_end_date: str | None = None,
    unified_network_custom_period_spend_limit: int | None = None,
    unified_network_custom_period_start_date: str | None = None,
    unified_network_exploration_is_custom: str | None = None,
    unified_network_exploration_min_budget: int | None = None,
    unified_network_weekly_spend_limit: int | None = None,
    # --- MobileAppCampaign.BiddingStrategy.Search (9 flags) ---
    mobile_search_average_cpc: int | None = None,
    mobile_search_average_cpi: int | None = None,
    mobile_search_bid_ceiling: int | None = None,
    mobile_search_clicks_per_week: int | None = None,
    mobile_search_custom_period_auto_continue: str | None = None,
    mobile_search_custom_period_end_date: str | None = None,
    mobile_search_custom_period_spend_limit: int | None = None,
    mobile_search_custom_period_start_date: str | None = None,
    mobile_search_weekly_spend_limit: int | None = None,
    # --- MobileAppCampaign.BiddingStrategy.Network (10 flags) ---
    mobile_network_average_cpc: int | None = None,
    mobile_network_average_cpi: int | None = None,
    mobile_network_bid_ceiling: int | None = None,
    mobile_network_clicks_per_week: int | None = None,
    mobile_network_custom_period_auto_continue: str | None = None,
    mobile_network_custom_period_end_date: str | None = None,
    mobile_network_custom_period_spend_limit: int | None = None,
    mobile_network_custom_period_start_date: str | None = None,
    mobile_network_limit_percent: int | None = None,
    mobile_network_weekly_spend_limit: int | None = None,
    # --- update-only: switch between WEEKLY_BUDGET / CUSTOM_PERIOD_BUDGET (10 flags) ---
    text_search_budget_type: str | None = None,
    text_network_budget_type: str | None = None,
    dyn_search_budget_type: str | None = None,
    dyn_network_budget_type: str | None = None,
    smart_search_budget_type: str | None = None,
    smart_network_budget_type: str | None = None,
    unified_search_budget_type: str | None = None,
    unified_network_budget_type: str | None = None,
    mobile_search_budget_type: str | None = None,
    mobile_network_budget_type: str | None = None,
    notification_json: str | None = None,
    time_targeting_json: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Update campaign fields.

    Money parameters (anything ending in *_spend_limit, *_cpc, *_cpa, *_cpi,
    *_cpm, *_cpv, *_pay_cpa, *_bid_ceiling, *_exploration_budget,
    *_exploration_min, *_exploration_min_budget, *_filter_average_cpa,
    *_filter_average_cpc, plus top-level budget, average_cpa, bid_ceiling,
    average_cpm, average_cpv, strategy_spend_limit) are in **micro-units**:
    15 RUB = 15_000_000. The agent must convert user-supplied rubles before
    calling this tool — never ask the user to multiply by 1_000_000. CLI
    rejects 0 < x < 100_000 with a "did you mean × 1_000_000" hint.

    Encoded-ratio parameters in micro-units (NOT rubles, but the same
    × 1_000_000 scale per Yandex Direct WSDL): `text_search_profitability`,
    `text_search_roi_coef`, `text_network_profitability`,
    `text_network_roi_coef`, `smart_search_profitability`,
    `smart_search_roi_coef`, `smart_network_profitability`,
    `smart_network_roi_coef`. Pass 20% as 20_000_000, ratio 1.0 as 1_000_000.

    Plain integer parameters (NOT micro-units): `*_reserve_return` (percent
    0-100), `*_limit_percent` (percent 10-100), `*_clicks_per_week` (count),
    `*_crr` (percent 1-1000 for dyn_*; same for smart_*), `*_goal_id`,
    `dyn_search_profitability`, `dyn_search_roi_coef`,
    `dyn_network_profitability`, `dyn_network_roi_coef` (these dyn_* four
    are plain integers per CLI, unlike their text_*/smart_* siblings).
    Pass these as-is — do NOT multiply by 1_000_000.

    Args:
        id: Campaign ID to update.
        name: Optional new campaign name.
        status: Optional new campaign status.
        budget: Optional new daily budget in micro-units (RUB × 1_000_000).
        start_date: Optional new start date (YYYY-MM-DD).
        end_date: Optional new end date (YYYY-MM-DD).
        text_search_budget_type / text_network_budget_type / dyn_*_budget_type /
            smart_*_budget_type / unified_*_budget_type / mobile_*_budget_type:
            Switch the existing strategy between WEEKLY_BUDGET and
            CUSTOM_PERIOD_BUDGET. Update-only; not accepted by campaigns_add.
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
    if not any(provided_update_value(value) for value in optional_values):
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
    append_cli_options(args, values, CAMPAIGN_UPDATE_ONLY_OPTIONS)
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


@mcp.tool(
    description="Create a new advertising campaign of any type (Text/Dynamic/Smart/Unified/MobileApp/Cpm). Use campaigns_update to change an existing campaign instead. Call tool_help('campaigns_add') for parameters.",
)
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
    # --- TextCampaign Search PlacementTypes (3 flags) ---
    search_placement_dynamic_places: str | None = None,
    search_placement_product_gallery: str | None = None,
    search_placement_search_results: str | None = None,
    # --- CpmBannerCampaign bidding strategy (6 flags) ---
    average_cpm: int | None = None,
    average_cpv: int | None = None,
    strategy_auto_continue: str | None = None,
    strategy_end_date: str | None = None,
    strategy_spend_limit: int | None = None,
    strategy_start_date: str | None = None,
    # --- TextCampaign.BiddingStrategy.Search (13 flags) ---
    text_search_average_cpc: int | None = None,
    text_search_clicks_per_week: int | None = None,
    text_search_custom_period_auto_continue: str | None = None,
    text_search_custom_period_end_date: str | None = None,
    text_search_custom_period_spend_limit: int | None = None,
    text_search_custom_period_start_date: str | None = None,
    text_search_exploration_is_custom: str | None = None,
    text_search_exploration_min_budget: int | None = None,
    text_search_pay_cpa: int | None = None,
    text_search_profitability: int | None = None,
    text_search_reserve_return: int | None = None,
    text_search_roi_coef: int | None = None,
    text_search_weekly_spend_limit: int | None = None,
    # --- TextCampaign.BiddingStrategy.Network (14 flags) ---
    text_network_average_cpc: int | None = None,
    text_network_clicks_per_week: int | None = None,
    text_network_custom_period_auto_continue: str | None = None,
    text_network_custom_period_end_date: str | None = None,
    text_network_custom_period_spend_limit: int | None = None,
    text_network_custom_period_start_date: str | None = None,
    text_network_exploration_is_custom: str | None = None,
    text_network_exploration_min_budget: int | None = None,
    text_network_limit_percent: int | None = None,
    text_network_pay_cpa: int | None = None,
    text_network_profitability: int | None = None,
    text_network_reserve_return: int | None = None,
    text_network_roi_coef: int | None = None,
    text_network_weekly_spend_limit: int | None = None,
    # --- DynamicTextCampaign.BiddingStrategy.Search (17 flags) ---
    dyn_search_average_cpa: int | None = None,
    dyn_search_average_cpc: int | None = None,
    dyn_search_bid_ceiling: int | None = None,
    dyn_search_clicks_per_week: int | None = None,
    dyn_search_cpa: int | None = None,
    dyn_search_crr: int | None = None,
    dyn_search_custom_period_auto_continue: str | None = None,
    dyn_search_custom_period_end_date: str | None = None,
    dyn_search_custom_period_spend_limit: int | None = None,
    dyn_search_custom_period_start_date: str | None = None,
    dyn_search_exploration_budget: int | None = None,
    dyn_search_exploration_budget_custom: str | None = None,
    dyn_search_goal_id: int | None = None,
    dyn_search_profitability: int | None = None,
    dyn_search_reserve_return: int | None = None,
    dyn_search_roi_coef: int | None = None,
    dyn_search_weekly_spend_limit: int | None = None,
    # --- DynamicTextCampaign.BiddingStrategy.Network (18 flags) ---
    dyn_network_average_cpa: int | None = None,
    dyn_network_average_cpc: int | None = None,
    dyn_network_bid_ceiling: int | None = None,
    dyn_network_clicks_per_week: int | None = None,
    dyn_network_cpa: int | None = None,
    dyn_network_crr: int | None = None,
    dyn_network_custom_period_auto_continue: str | None = None,
    dyn_network_custom_period_end_date: str | None = None,
    dyn_network_custom_period_spend_limit: int | None = None,
    dyn_network_custom_period_start_date: str | None = None,
    dyn_network_exploration_budget: int | None = None,
    dyn_network_exploration_budget_custom: str | None = None,
    dyn_network_goal_id: int | None = None,
    dyn_network_limit_percent: int | None = None,
    dyn_network_profitability: int | None = None,
    dyn_network_reserve_return: int | None = None,
    dyn_network_roi_coef: int | None = None,
    dyn_network_weekly_spend_limit: int | None = None,
    # --- SmartCampaign.BiddingStrategy.Search (18 flags) ---
    smart_search_average_cpa: int | None = None,
    smart_search_average_cpc: int | None = None,
    smart_search_bid_ceiling: int | None = None,
    smart_search_cp_auto_continue: str | None = None,
    smart_search_cp_end_date: str | None = None,
    smart_search_cp_spend_limit: int | None = None,
    smart_search_cp_start_date: str | None = None,
    smart_search_cpa: int | None = None,
    smart_search_crr: int | None = None,
    smart_search_exploration_min: int | None = None,
    smart_search_exploration_min_custom: str | None = None,
    smart_search_filter_average_cpa: int | None = None,
    smart_search_filter_average_cpc: int | None = None,
    smart_search_goal_id: int | None = None,
    smart_search_profitability: int | None = None,
    smart_search_reserve_return: int | None = None,
    smart_search_roi_coef: int | None = None,
    smart_search_weekly_spend_limit: int | None = None,
    # --- SmartCampaign.BiddingStrategy.Network (19 flags) ---
    smart_network_average_cpa: int | None = None,
    smart_network_average_cpc: int | None = None,
    smart_network_bid_ceiling: int | None = None,
    smart_network_cp_auto_continue: str | None = None,
    smart_network_cp_end_date: str | None = None,
    smart_network_cp_spend_limit: int | None = None,
    smart_network_cp_start_date: str | None = None,
    smart_network_cpa: int | None = None,
    smart_network_crr: int | None = None,
    smart_network_exploration_min: int | None = None,
    smart_network_exploration_min_custom: str | None = None,
    smart_network_filter_average_cpa: int | None = None,
    smart_network_filter_average_cpc: int | None = None,
    smart_network_goal_id: int | None = None,
    smart_network_limit_percent: int | None = None,
    smart_network_profitability: int | None = None,
    smart_network_reserve_return: int | None = None,
    smart_network_roi_coef: int | None = None,
    smart_network_weekly_spend_limit: int | None = None,
    # --- UnifiedCampaign.BiddingStrategy.Search (11 flags) ---
    unified_search_average_cpc: int | None = None,
    unified_search_custom_period_auto_continue: str | None = None,
    unified_search_custom_period_end_date: str | None = None,
    unified_search_custom_period_spend_limit: int | None = None,
    unified_search_custom_period_start_date: str | None = None,
    unified_search_exploration_is_custom: str | None = None,
    unified_search_exploration_min_budget: int | None = None,
    unified_search_pay_cpa: int | None = None,
    unified_search_placement_maps: str | None = None,
    unified_search_placement_search_organization_list: str | None = None,
    unified_search_weekly_spend_limit: int | None = None,
    # --- UnifiedCampaign.BiddingStrategy.Network (9 flags) ---
    unified_network_average_cpc: int | None = None,
    unified_network_cpa: int | None = None,
    unified_network_custom_period_auto_continue: str | None = None,
    unified_network_custom_period_end_date: str | None = None,
    unified_network_custom_period_spend_limit: int | None = None,
    unified_network_custom_period_start_date: str | None = None,
    unified_network_exploration_is_custom: str | None = None,
    unified_network_exploration_min_budget: int | None = None,
    unified_network_weekly_spend_limit: int | None = None,
    # --- MobileAppCampaign.BiddingStrategy.Search (9 flags) ---
    mobile_search_average_cpc: int | None = None,
    mobile_search_average_cpi: int | None = None,
    mobile_search_bid_ceiling: int | None = None,
    mobile_search_clicks_per_week: int | None = None,
    mobile_search_custom_period_auto_continue: str | None = None,
    mobile_search_custom_period_end_date: str | None = None,
    mobile_search_custom_period_spend_limit: int | None = None,
    mobile_search_custom_period_start_date: str | None = None,
    mobile_search_weekly_spend_limit: int | None = None,
    # --- MobileAppCampaign.BiddingStrategy.Network (10 flags) ---
    mobile_network_average_cpc: int | None = None,
    mobile_network_average_cpi: int | None = None,
    mobile_network_bid_ceiling: int | None = None,
    mobile_network_clicks_per_week: int | None = None,
    mobile_network_custom_period_auto_continue: str | None = None,
    mobile_network_custom_period_end_date: str | None = None,
    mobile_network_custom_period_spend_limit: int | None = None,
    mobile_network_custom_period_start_date: str | None = None,
    mobile_network_limit_percent: int | None = None,
    mobile_network_weekly_spend_limit: int | None = None,
    notification_json: str | None = None,
    time_targeting_json: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Create a new campaign.

    Money parameters (budget, average_cpa, bid_ceiling, average_cpm,
    average_cpv, strategy_spend_limit, and every strategy-detail parameter
    ending in *_spend_limit, *_cpc, *_cpa, *_cpi, *_pay_cpa, *_bid_ceiling,
    *_exploration_budget, *_exploration_min, *_exploration_min_budget,
    *_filter_average_cpa, *_filter_average_cpc) are in **micro-units**:
    15 RUB = 15_000_000. The agent must convert user-supplied rubles before
    calling this tool — never ask the user to multiply by 1_000_000. CLI
    rejects 0 < x < 100_000 with a "did you mean × 1_000_000" hint.

    Encoded-ratio parameters in micro-units (NOT rubles, but the same
    × 1_000_000 scale per Yandex Direct WSDL): `text_search_profitability`,
    `text_search_roi_coef`, `text_network_profitability`,
    `text_network_roi_coef`, `smart_search_profitability`,
    `smart_search_roi_coef`, `smart_network_profitability`,
    `smart_network_roi_coef`. Pass 20% as 20_000_000, ratio 1.0 as 1_000_000.

    Plain integer parameters (NOT micro-units): `*_reserve_return` (percent
    0-100), `*_limit_percent` (percent 10-100), `*_clicks_per_week` (count),
    `*_crr` (percent 1-1000 for dyn_*; same for smart_*), `*_goal_id`,
    `dyn_search_profitability`, `dyn_search_roi_coef`,
    `dyn_network_profitability`, `dyn_network_roi_coef` (these dyn_* four
    are plain integers per CLI, unlike their text_*/smart_* siblings).
    Pass these as-is — do NOT multiply by 1_000_000.

    CLI 0.3.9+ enforces strict WSDL parity. Incompatible combinations (e.g.
    `crr` on AVERAGE_CPA, `priority_goals` without a `*_MULTIPLE_GOALS`
    strategy, `counter_ids` on Smart, strategy-detail flags on the wrong
    campaign type, mutex of `*_weekly_spend_limit` with
    `*_custom_period_spend_limit`) are rejected by CLI with `UsageError`
    before any API call — the plugin does not duplicate these checks.

    Args:
        name: Campaign name.
        start_date: Campaign start date in YYYY-MM-DD format.
        campaign_type: Campaign type (TEXT_CAMPAIGN, DYNAMIC_TEXT_CAMPAIGN,
            SMART_CAMPAIGN, UNIFIED_CAMPAIGN, MOBILE_APP_CAMPAIGN, CPM_BANNER_CAMPAIGN).
        budget: Optional daily budget in micro-units (RUB × 1_000_000).
        end_date: Optional campaign end date in YYYY-MM-DD format.
        search_strategy: Optional search bidding strategy type
            (e.g. "HIGHEST_POSITION", "WB_MAXIMUM_CLICKS").
        network_strategy: Optional network bidding strategy type
            (e.g. "MAXIMUM_COVERAGE", "WB_MAXIMUM_CLICKS").
        settings: Optional list of campaign settings as OPTION=VALUE strings
            (e.g. ["EnableEmailNotification=YES", "RequireServicing=NO"]).
        filter_average_cpc: Optional Smart campaign filter average CPC
            (micro-units).
        counter_id: Optional Smart campaign Metrika counter ID (single).
        counter_ids: Optional comma-separated Metrika counter IDs for
            TextCampaign / DynamicTextCampaign (`CounterIds`).
        goal_id: Optional single Metrika goal ID for AVERAGE_CPA /
            PAY_FOR_CONVERSION_CRR / AVERAGE_CPA_PER_CAMPAIGN /
            AVERAGE_CPA_PER_FILTER strategies.
        priority_goals: Optional comma-separated 'goal_id:value' pairs for
            AVERAGE_CPA_MULTIPLE_GOALS / PAY_FOR_CONVERSION_MULTIPLE_GOALS
            (and Smart / Unified PriorityGoals).
        average_cpa: Optional target CPA in micro-units.
        crr: Optional cost-revenue-ratio percentage for PAY_FOR_CONVERSION_CRR.
        bid_ceiling: Optional bid ceiling in micro-units for the chosen
            CPA strategy.
        average_cpm / average_cpv / strategy_spend_limit / strategy_start_date /
            strategy_end_date / strategy_auto_continue: CpmBannerCampaign bidding
            strategy flags (money in micro-units).
        text_search_* / text_network_*: TextCampaign Search/Network bidding
            strategy detail flags (WSDL parity).
        dyn_search_* / dyn_network_*: DynamicTextCampaign Search/Network.
        smart_search_* / smart_network_*: SmartCampaign Search/Network
            (per-campaign / per-filter variants — `*_filter_average_*` are
            per-filter, others per-campaign).
        unified_search_* / unified_network_*: UnifiedCampaign Search/Network.
        mobile_search_* / mobile_network_*: MobileAppCampaign Search/Network.
        search_placement_search_results / search_placement_product_gallery /
            search_placement_dynamic_places: TextCampaign / Unified /
            DynamicText Search PlacementTypes (YES/NO).
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


@mcp.tool(
    description="Permanently delete campaigns by ID (max 10). Call tool_help('campaigns_delete') for parameters.",
)
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


@mcp.tool(
    description="Archive campaigns by ID (max 10); reverse with campaigns_unarchive. Call tool_help('campaigns_archive') for parameters.",
)
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


@mcp.tool(
    description="Unarchive previously archived campaigns by ID (max 10). Call tool_help('campaigns_unarchive') for parameters.",
)
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


@mcp.tool(
    description="Suspend (pause) running campaigns by ID (max 10); reverse with campaigns_resume. Call tool_help('campaigns_suspend') for parameters.",
)
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


@mcp.tool(
    description="Resume previously suspended campaigns by ID (max 10). Call tool_help('campaigns_resume') for parameters.",
)
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
