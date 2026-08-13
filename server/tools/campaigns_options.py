"""Declarative CLI-option tables and grouped-dict registries for campaign tools.

Split out of campaigns.py (issue #263): this module holds only immutable data —
no tool bodies — so campaigns.py stays focused on the tool logic that consumes
these tables via server.tools.helpers.append_cli_options / expand_grouped_dicts.
"""

from server.tools.helpers import CliOption

CAMPAIGN_GET_SELECTOR_FLAGS = (
    ("text_campaign_fields", "--text-campaign-field-names"),
    (
        "text_campaign_search_strategy_placement_types_fields",
        "--text-campaign-search-strategy-placement-types-field-names",
    ),
    ("mobile_app_campaign_fields", "--mobile-app-campaign-field-names"),
    ("dynamic_text_campaign_fields", "--dynamic-text-campaign-field-names"),
    (
        "dynamic_text_campaign_search_strategy_placement_types_fields",
        "--dynamic-text-campaign-search-strategy-placement-types-field-names",
    ),
    ("cpm_banner_campaign_fields", "--cpm-banner-campaign-field-names"),
    ("smart_campaign_fields", "--smart-campaign-field-names"),
    ("unified_campaign_fields", "--unified-campaign-field-names"),
    (
        "unified_campaign_search_strategy_placement_types_fields",
        "--unified-campaign-search-strategy-placement-types-field-names",
    ),
    (
        "unified_campaign_package_bidding_strategy_platforms_fields",
        "--unified-campaign-package-bidding-strategy-platforms-field-names",
    ),
)

CAMPAIGN_GET_OPTIONS = (
    CliOption("status", "--status"),
    CliOption("statuses", "--statuses"),
    CliOption("states", "--states"),
    CliOption("types", "--types"),
    CliOption("payment_statuses", "--payment-statuses"),
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
    # --- CpmBannerCampaign bidding strategy (7 flags) ---
    CliOption("average_cpm", "--average-cpm"),
    CliOption("average_cpv", "--average-cpv"),
    CliOption("strategy_auto_continue", "--strategy-auto-continue"),
    CliOption("strategy_end_date", "--strategy-end-date"),
    CliOption("strategy_spend_limit", "--strategy-spend-limit"),
    CliOption("strategy_start_date", "--strategy-start-date"),
    CliOption("strategy_weekly_spend_limit", "--strategy-weekly-spend-limit"),
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


# --- Grouped bidding-strategy parameters ---------------------------------
# The per-campaign-type strategy flags (~147 of them) are exposed to the model
# as 10 nested dict params instead of 147 flat `int|None`/`str|None` params.
# This collapses the JSON-Schema that FastMCP broadcasts at startup (each flat
# Optional emits a verbose `anyOf:[...,{"type":"null"}]`) without touching the
# generated CLI argv: incoming dicts are expanded back into the flat option
# names below before append_cli_options runs, so the `direct` call is identical.
#
# Each registry entry is derived from CAMPAIGN_MUTATION_OPTIONS by name prefix,
# so the grouping stays in sync automatically if options are added/removed.
_STRATEGY_PREFIXES: tuple[str, ...] = (
    "text_search",
    "text_network",
    "dyn_search",
    "dyn_network",
    "smart_search",
    "smart_network",
    "unified_search",
    "unified_network",
    "mobile_search",
    "mobile_network",
)

# (dict_param_name, CliOptions absorbed). Order matches the signatures below.
STRATEGY_DICT_REGISTRY: tuple[tuple[str, tuple[CliOption, ...]], ...] = tuple(
    (
        f"{prefix}_options",
        tuple(o for o in CAMPAIGN_MUTATION_OPTIONS if o.name.startswith(f"{prefix}_")),
    )
    for prefix in _STRATEGY_PREFIXES
)

# Update-only budget-type opts keyed by their strategy prefix.
BUDGET_TYPE_BY_PREFIX: dict[str, CliOption] = {
    o.name.replace("_budget_type", ""): o for o in CAMPAIGN_UPDATE_ONLY_OPTIONS
}


# --- Grouped flat (non-strategy) families (#220-B) -----------------------
# Same dict-grouping technique as the bidding strategies above, applied to the
# remaining flat families (≥3 params). Members are the original flat option
# names; helpers.expand_grouped_dicts restores them before append_cli_options,
# so the generated argv is byte-identical. Families of <3 params
# (attribution_model, package_strategy_*, dynamic_placement_*) stay flat —
# grouping them would not pay for the dict's own schema cost.
CAMPAIGN_FAMILY_DICT_REGISTRY: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "notification_options",
        (
            "notification_email",
            "notification_check_position_interval",
            "notification_warning_balance",
            "notification_send_account_news",
            "notification_send_warnings",
        ),
    ),
    (
        "time_targeting_options",
        (
            "time_targeting_schedule",
            "consider_working_weekends",
            "holidays_suspend_on_holidays",
            "holidays_bid_percent",
            "holidays_start_hour",
            "holidays_end_hour",
        ),
    ),
    (
        "frequency_cap_options",
        (
            "frequency_cap_impressions",
            "frequency_cap_period_days",
            "frequency_cap_period_all",
        ),
    ),
    (
        "relevant_keywords_options",
        (
            "relevant_keywords_budget_percent",
            "relevant_keywords_mode",
            "relevant_keywords_optimize_goal_id",
        ),
    ),
    (
        "package_platform_options",
        (
            "package_platform_search",
            "package_platform_search_result",
            "package_platform_product_gallery",
            "package_platform_maps",
            "package_platform_search_organization_list",
            "package_platform_network",
            "package_platform_dynamic_places",
        ),
    ),
    ("sms_options", ("sms_events", "sms_time_from", "sms_time_to")),
    (
        "search_placement_options",
        (
            "search_placement_dynamic_places",
            "search_placement_product_gallery",
            "search_placement_search_results",
        ),
    ),
    (
        "cpm_strategy_options",
        (
            "strategy_auto_continue",
            "strategy_end_date",
            "strategy_spend_limit",
            "strategy_start_date",
            "strategy_weekly_spend_limit",
        ),
    ),
)
