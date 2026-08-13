"""MCP tools for campaign management."""

from server.cli.runner import CliAuthError, CliNotFoundError
from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.campaigns_options import (
    BUDGET_TYPE_BY_PREFIX,
    CAMPAIGN_FAMILY_DICT_REGISTRY,
    CAMPAIGN_GET_OPTIONS,
    CAMPAIGN_GET_SELECTOR_FLAGS,
    CAMPAIGN_MUTATION_OPTIONS,
    CAMPAIGN_UPDATE_ONLY_OPTIONS,
    STRATEGY_DICT_REGISTRY,
)
from server.tools.helpers import (
    append_cli_options,
    append_pagination,
    expand_grouped_dicts,
    require_update_fields,
    run_single_id_batch,
    tool_error_dict,
)


def _expand_strategy_dicts(
    values: dict,
    strategy_dicts: dict[str, dict | None],
    *,
    include_budget_types: bool,
) -> ToolError | None:
    """Expand grouped strategy dict params into flat keys in *values*.

    Mutates *values* in place so that ``append_cli_options`` sees the individual
    option names it expects, keeping the generated CLI argv byte-for-byte
    identical to the old flat signature. Returns a ToolError on a type mismatch
    (non-dict value), or None on success.

    Unknown keys inside a strategy dict are silently ignored — they never reach
    the CLI. This is intentional forward-compatibility: a new CLI flag does not
    require a plugin release to be passable.
    """
    for dict_name, incoming in strategy_dicts.items():
        if incoming is None:
            continue
        if not isinstance(incoming, dict):
            return ToolError(
                error="invalid_param",
                message=(
                    f"'{dict_name}' must be a dict or null, "
                    f"got {type(incoming).__name__}"
                ),
            )
        for reg_name, opts in STRATEGY_DICT_REGISTRY:
            if reg_name == dict_name:
                for opt in opts:
                    if opt.name in incoming:
                        values[opt.name] = incoming[opt.name]
                break
        if include_budget_types:
            prefix = dict_name.removesuffix("_options")
            bt_opt = BUDGET_TYPE_BY_PREFIX.get(prefix)
            if bt_opt is not None and bt_opt.name in incoming:
                values[bt_opt.name] = incoming[bt_opt.name]
    return None


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

    Limits: Ids≤1000; all other filters unlimited.
    Enforced by direct-cli 0.4.3 (#571).

    Args:
        state: Filter by campaign state ("ON" or "OFF"). If None,
            returns all campaigns. Applied client-side.
        ids: Comma-separated campaign IDs (optional).
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
        return tool_error_dict(
            ToolError(
                error="invalid_state",
                message=f"State must be 'ON' or 'OFF', got '{state}'",
            )
        )

    args = ["campaigns", "get", "--format", "json"]
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        args.extend(["--ids", normalized_ids])
    append_cli_options(args, locals(), CAMPAIGN_GET_OPTIONS)
    append_pagination(args, limit, fetch_all, fields)
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


def _expand_campaign_update_dicts(values: dict) -> ToolError | None:
    """Expand campaigns_update's grouped strategy + family dicts in place."""
    expansion_error = _expand_strategy_dicts(
        values,
        {name: values[name] for name, _ in STRATEGY_DICT_REGISTRY},
        include_budget_types=True,
    )
    if expansion_error is not None:
        return expansion_error
    return expand_grouped_dicts(values, CAMPAIGN_FAMILY_DICT_REGISTRY)


def _build_campaign_update_argv(
    values: dict,
    *,
    id: str,
    name: str | None,
    status: str | None,
    budget: int | None,
    start_date: str | None,
    end_date: str | None,
    campaign_type: str | None,
    dry_run: bool,
) -> list[str]:
    """Assemble the `campaigns update` argv from manual flags + option tables."""
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
    return args


class _CampaignNotFound(Exception):
    """Internal signal: the CLI reported the campaign id as not found."""


def _run_campaign_update(runner, args: list[str]):
    """Invoke `campaigns update`, raising _CampaignNotFound on a CLI "not found"."""
    try:
        return runner.run_json(args)
    except (CliAuthError, CliNotFoundError):
        raise
    except Exception as exc:
        if "not found" in str(exc).lower():
            raise _CampaignNotFound from exc
        raise


def _campaign_update_result(
    *,
    id: str,
    name: str | None,
    status: str | None,
    budget: int | None,
    start_date: str | None,
    end_date: str | None,
) -> dict:
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
    description="Update fields of an existing campaign identified by id (name, budget, status, bidding strategy, etc.). Use campaigns_add to create a new campaign instead. Call tool_help('campaigns_update') for parameters.",
)
@handle_cli_errors
def campaigns_update(
    id: str,
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
    attribution_model: str | None = None,
    package_strategy_id: str | None = None,
    package_strategy_from_campaign_id: str | None = None,
    negative_keyword_shared_set_ids: str | None = None,
    video_target: str | None = None,
    client_info: str | None = None,
    time_zone: str | None = None,
    negative_keywords: str | None = None,
    blocked_ips: str | None = None,
    excluded_sites: str | None = None,
    campaign_type: str | None = None,
    tracking_params: str | None = None,
    search_strategy: str | None = None,
    network_strategy: str | None = None,
    goal_id: int | None = None,
    average_cpa: int | None = None,
    crr: int | None = None,
    bid_ceiling: int | None = None,
    # --- CpmBannerCampaign bidding strategy ---
    average_cpm: int | None = None,
    average_cpv: int | None = None,
    # --- Grouped flat families (#220-B); keys = original flat option names ---
    notification_options: dict | None = None,
    time_targeting_options: dict | None = None,
    frequency_cap_options: dict | None = None,
    relevant_keywords_options: dict | None = None,
    package_platform_options: dict | None = None,
    sms_options: dict | None = None,
    search_placement_options: dict | None = None,
    cpm_strategy_options: dict | None = None,
    # --- Grouped bidding-strategy dicts (replace ~147 flat params) ---
    # Keys = the original flat option names (e.g. text_search_average_cpc).
    # update-only *_budget_type keys also go inside the matching dict.
    text_search_options: dict | None = None,
    text_network_options: dict | None = None,
    dyn_search_options: dict | None = None,
    dyn_network_options: dict | None = None,
    smart_search_options: dict | None = None,
    smart_network_options: dict | None = None,
    unified_search_options: dict | None = None,
    unified_network_options: dict | None = None,
    mobile_search_options: dict | None = None,
    mobile_network_options: dict | None = None,
    dry_run: bool = False,
) -> dict:
    """Update campaign fields.

    Money parameters (anything ending in *_spend_limit, *_cpc, *_cpa, *_cpi,
    *_cpm, *_cpv, *_pay_cpa, *_bid_ceiling, *_exploration_budget,
    *_exploration_min, *_exploration_min_budget, *_filter_average_cpa,
    *_filter_average_cpc, plus top-level budget, average_cpa, bid_ceiling,
    average_cpm, average_cpv, strategy_spend_limit, strategy_weekly_spend_limit)
    are in **micro-units**:
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

    CLI enforces strict WSDL parity: strategy-detail flags on the wrong
    campaign type are rejected with `UsageError` before any API call — the
    plugin does not duplicate these checks. In particular, `cpm_strategy_options`
    requires both `campaign_type="CPM_BANNER_CAMPAIGN"` and
    `network_strategy="MANUAL_CPM"` on the same call; CLI rejects the
    strategy-detail flags otherwise.

    Args:
        id: Campaign ID to update.
        name: Optional new campaign name.
        status: Optional new campaign status.
        budget: Optional new daily budget in micro-units (RUB × 1_000_000).
        start_date: Optional new start date (YYYY-MM-DD).
        end_date: Optional new end date (YYYY-MM-DD).
        text_search_options / text_network_options / dyn_search_options /
            dyn_network_options / smart_search_options / smart_network_options /
            unified_search_options / unified_network_options /
            mobile_search_options / mobile_network_options: Optional dicts
            grouping the per-campaign-type bidding-strategy detail flags. Each
            dict key is the original flat option name, e.g.
            text_search_options={"text_search_average_cpc": 15_000_000,
            "text_search_weekly_spend_limit": 500_000_000}. The micro-unit and
            plain-integer rules above apply to the dict values. Key names must
            exactly match the original flat option names. Unknown keys,
            including typos, are ignored; if all keys are unknown, no strategy
            flags are sent and the call may still return success without
            changing bidding settings. The update-only "*_budget_type" key
            (switch a strategy between WEEKLY_BUDGET and CUSTOM_PERIOD_BUDGET)
            goes inside the matching dict, e.g.
            text_search_options={"text_search_budget_type": "WEEKLY_BUDGET"};
            it is accepted here but ignored by campaigns_add.
        dry_run: Show the direct request without sending it.
    """
    values = locals()
    fields_error = require_update_fields(
        values,
        message="Provide at least one typed campaign field to update.",
        exclude={"id", "dry_run"},
    )
    if fields_error:
        return tool_error_dict(fields_error)

    # Expand grouped strategy/family dicts into the flat option names
    # append_cli_options expects. Runs after the guard (a non-empty dict already
    # satisfies it) and before argv assembly, so the generated CLI call is
    # byte-identical to the old flat signature.
    expansion_error = _expand_campaign_update_dicts(values)
    if expansion_error is not None:
        return tool_error_dict(expansion_error)

    args = _build_campaign_update_argv(
        values,
        id=id,
        name=name,
        status=status,
        budget=budget,
        start_date=start_date,
        end_date=end_date,
        campaign_type=campaign_type,
        dry_run=dry_run,
    )

    runner = get_runner()
    try:
        cli_output = _run_campaign_update(runner, args)
    except _CampaignNotFound:
        return tool_error_dict(
            ToolError(error="not_found", message=f"Campaign '{id}' not found")
        )
    if dry_run:
        return {
            "dry_run": True,
            "command": ["direct", *args],
            "request_body": cli_output,
        }
    return _campaign_update_result(
        id=id,
        name=name,
        status=status,
        budget=budget,
        start_date=start_date,
        end_date=end_date,
    )


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
    attribution_model: str | None = None,
    package_strategy_id: str | None = None,
    package_strategy_from_campaign_id: str | None = None,
    negative_keyword_shared_set_ids: str | None = None,
    video_target: str | None = None,
    client_info: str | None = None,
    time_zone: str | None = None,
    negative_keywords: str | None = None,
    blocked_ips: str | None = None,
    excluded_sites: str | None = None,
    tracking_params: str | None = None,
    # --- CpmBannerCampaign bidding strategy ---
    average_cpm: int | None = None,
    average_cpv: int | None = None,
    # --- Grouped flat families (#220-B); keys = original flat option names ---
    notification_options: dict | None = None,
    time_targeting_options: dict | None = None,
    frequency_cap_options: dict | None = None,
    relevant_keywords_options: dict | None = None,
    package_platform_options: dict | None = None,
    sms_options: dict | None = None,
    search_placement_options: dict | None = None,
    cpm_strategy_options: dict | None = None,
    # --- Grouped bidding-strategy dicts (replace ~138 flat params) ---
    # Keys = the original flat option names (e.g. text_search_average_cpc).
    text_search_options: dict | None = None,
    text_network_options: dict | None = None,
    dyn_search_options: dict | None = None,
    dyn_network_options: dict | None = None,
    smart_search_options: dict | None = None,
    smart_network_options: dict | None = None,
    unified_search_options: dict | None = None,
    unified_network_options: dict | None = None,
    mobile_search_options: dict | None = None,
    mobile_network_options: dict | None = None,
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
        average_cpm / average_cpv / strategy_spend_limit /
            strategy_weekly_spend_limit / strategy_start_date / strategy_end_date /
            strategy_auto_continue: CpmBannerCampaign bidding strategy flags
            (money in micro-units).
        text_search_options / text_network_options / dyn_search_options /
            dyn_network_options / smart_search_options / smart_network_options /
            unified_search_options / unified_network_options /
            mobile_search_options / mobile_network_options: Optional dicts
            grouping the per-campaign-type bidding-strategy detail flags (WSDL
            parity). Each dict key is the original flat option name, e.g.
            text_search_options={"text_search_average_cpc": 15_000_000}. The
            micro-unit / plain-integer rules above apply to the dict values.
            Smart `*_filter_average_*` keys are per-filter, others per-campaign.
            Key names must exactly match the original flat option names.
            Unknown keys, including typos, are ignored; if all keys are
            unknown, no strategy flags are sent and the call may still return
            success without changing bidding settings. The update-only
            "*_budget_type" key is not used by campaigns_add (use
            campaigns_update).
        search_placement_search_results / search_placement_product_gallery /
            search_placement_dynamic_places: TextCampaign / Unified /
            DynamicText Search PlacementTypes (YES/NO).
        Notification settings use the typed flags notification_email,
            notification_warning_balance, notification_send_account_news,
            notification_send_warnings, notification_check_position_interval.
        TimeTargeting uses time_targeting_schedule, consider_working_weekends,
            holidays_suspend_on_holidays, holidays_bid_percent,
            holidays_start_hour, holidays_end_hour. (The free-form
            notification/time_targeting blob flags were removed in direct-cli
            0.4.2.)
        dry_run: Show the direct request without sending it.
    """
    args = ["campaigns", "add", "--name", name, "--start-date", start_date]
    # Only campaign_type/budget/end_date are emitted manually here (they are not
    # in CAMPAIGN_MUTATION_OPTIONS); every other flat param is driven by the
    # shared option table below — same as campaigns_update.
    if campaign_type:
        args.extend(["--type", campaign_type])
    if budget is not None:
        args.extend(["--budget", str(budget)])
    if end_date:
        args.extend(["--end-date", end_date])
    values = locals()
    # Expand grouped strategy/family dicts into their flat option names.
    # *_budget_type keys are update-only; include_budget_types=False ignores them.
    expansion_error = _expand_strategy_dicts(
        values,
        {name: values[name] for name, _ in STRATEGY_DICT_REGISTRY},
        include_budget_types=False,
    )
    if expansion_error is not None:
        return tool_error_dict(expansion_error)
    family_error = expand_grouped_dicts(values, CAMPAIGN_FAMILY_DICT_REGISTRY)
    if family_error is not None:
        return tool_error_dict(family_error)
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
    return run_single_id_batch(
        get_runner(), "campaigns", "resume", ids, dry_run=dry_run
    )
