"""MCP tools for bidding strategy management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit

IS_ARCHIVED_VALUES = ("YES", "NO")
STRATEGY_TYPES = (
    "WbMaximumClicks",
    "WbMaximumConversionRate",
    "AverageCpc",
    "AverageCpcPerCampaign",
    "AverageCpcPerFilter",
    "AverageCpa",
    "AverageCpaPerCampaign",
    "AverageCpaPerFilter",
    "AverageCpaMultipleGoals",
    "AverageCrr",
    "MaxProfit",
    "PayForConversion",
    "PayForConversionPerCampaign",
    "PayForConversionPerFilter",
    "PayForConversionCrr",
    "PayForConversionMultipleGoals",
)
ATTRIBUTION_MODELS = ("LYDC", "FC", "LC", "LSC", "LYDC_WEIGHT", "CROSSTDEVICE")


@mcp.tool(name="strategies_get")
@handle_cli_errors
def strategies_list(
    ids: str | None = None,
    types: str | None = None,
    is_archived: str | None = None,
    limit: int | None = None,
    fetch_all: bool = False,
    fields: str | None = None,
) -> list[dict] | dict:
    """List bidding strategies.

    Args:
        ids: Comma-separated strategy IDs (max 10).
        types: Comma-separated strategy types.
        is_archived: Filter by archived status — "YES" or "NO".
        limit: Limit number of results.
        fetch_all: Fetch all pages.
        fields: Comma-separated field names.
    """
    if is_archived is not None and is_archived not in IS_ARCHIVED_VALUES:
        return ToolError(
            error="invalid_is_archived",
            message=(
                f"is_archived must be one of {IS_ARCHIVED_VALUES}; got '{is_archived}'"
            ),
        ).__dict__

    args = ["strategies", "get", "--format", "json"]
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        batch_error = check_batch_limit(normalized_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--ids", normalized_ids])
    if types is not None:
        args.extend(["--types", types])
    if is_archived is not None:
        args.extend(["--is-archived", is_archived])
    if limit is not None:
        args.extend(["--limit", str(limit)])
    if fetch_all:
        args.append("--fetch-all")
    if fields is not None:
        args.extend(["--fields", fields])
    return get_runner().run_json(args)


@mcp.tool(name="strategies_add")
@handle_cli_errors
def strategies_add(
    name: str,
    type: str,
    average_cpc: int | None = None,
    average_cpa: int | None = None,
    average_crr: int | None = None,
    goal_id: int | None = None,
    spend_limit: int | None = None,
    weekly_spend_limit: int | None = None,
    bid_ceiling: int | None = None,
    custom_period_spend_limit: int | None = None,
    custom_period_start_date: str | None = None,
    custom_period_end_date: str | None = None,
    custom_period_auto_continue: str | None = None,
    minimum_exploration_budget: int | None = None,
    counter_ids: str | None = None,
    priority_goals: list[str] | None = None,
    attribution_model: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Add a bidding strategy.

    CLI 0.3.8 replaced the JSON `--params` / `--priority-goals` blobs with
    typed flags. Each strategy `type` accepts its own subset of money fields
    (CLI enforces this against the WSDL schema gate).

    Args:
        name: Strategy name.
        type: Strategy type — one of WbMaximumClicks,
            WbMaximumConversionRate, AverageCpc, AverageCpcPerCampaign,
            AverageCpcPerFilter, AverageCpa, AverageCpaPerCampaign,
            AverageCpaPerFilter, AverageCpaMultipleGoals, AverageCrr,
            MaxProfit, PayForConversion, PayForConversionPerCampaign,
            PayForConversionPerFilter, PayForConversionCrr,
            PayForConversionMultipleGoals.
        average_cpc: Average CPC in micro-units (RUB × 1,000,000).
        average_cpa: Average CPA in micro-units (RUB × 1,000,000).
        average_crr: Average cost-revenue ratio (integer percent).
        goal_id: Goal ID for conversion strategies.
        spend_limit: Spend limit in micro-units.
        weekly_spend_limit: Weekly spend limit in micro-units.
        bid_ceiling: Bid ceiling in micro-units.
        custom_period_spend_limit: Custom period spend limit in micro-units.
        custom_period_start_date: Custom period start date.
        custom_period_end_date: Custom period end date.
        custom_period_auto_continue: Custom period auto-continue flag.
        minimum_exploration_budget: Minimum exploration budget in micro-units.
        counter_ids: Comma-separated Metrica counter IDs.
        priority_goals: List of "GOAL_ID:VALUE" specs (each becomes a
            repeated --priority-goal flag).
        attribution_model: Attribution model — LYDC, FC, LC, LSC, LYDC_WEIGHT,
            CROSSTDEVICE.
        dry_run: Show the direct request without sending it.
    """
    if type not in STRATEGY_TYPES:
        return ToolError(
            error="invalid_type",
            message=f"type must be one of {STRATEGY_TYPES}; got '{type}'",
        ).__dict__
    if attribution_model is not None and attribution_model not in ATTRIBUTION_MODELS:
        return ToolError(
            error="invalid_attribution_model",
            message=(
                f"attribution_model must be one of {ATTRIBUTION_MODELS}; "
                f"got '{attribution_model}'"
            ),
        ).__dict__
    args = ["strategies", "add", "--name", name, "--type", type]
    if average_cpc is not None:
        args.extend(["--average-cpc", str(average_cpc)])
    if average_cpa is not None:
        args.extend(["--average-cpa", str(average_cpa)])
    if average_crr is not None:
        args.extend(["--average-crr", str(average_crr)])
    if goal_id is not None:
        args.extend(["--goal-id", str(goal_id)])
    if spend_limit is not None:
        args.extend(["--spend-limit", str(spend_limit)])
    if weekly_spend_limit is not None:
        args.extend(["--weekly-spend-limit", str(weekly_spend_limit)])
    if bid_ceiling is not None:
        args.extend(["--bid-ceiling", str(bid_ceiling)])
    if custom_period_spend_limit is not None:
        args.extend(["--custom-period-spend-limit", str(custom_period_spend_limit)])
    if custom_period_start_date is not None:
        args.extend(["--custom-period-start-date", custom_period_start_date])
    if custom_period_end_date is not None:
        args.extend(["--custom-period-end-date", custom_period_end_date])
    if custom_period_auto_continue is not None:
        args.extend(["--custom-period-auto-continue", custom_period_auto_continue])
    if minimum_exploration_budget is not None:
        args.extend(["--minimum-exploration-budget", str(minimum_exploration_budget)])
    if counter_ids is not None:
        args.extend(["--counter-ids", counter_ids])
    if priority_goals:
        for spec in priority_goals:
            args.extend(["--priority-goal", spec])
    if attribution_model is not None:
        args.extend(["--attribution-model", attribution_model])
    if dry_run:
        args.append("--dry-run")
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(name="strategies_update")
@handle_cli_errors
def strategies_update(
    id: int,
    name: str | None = None,
    type: str | None = None,
    average_cpc: int | None = None,
    average_cpa: int | None = None,
    average_crr: int | None = None,
    goal_id: int | None = None,
    spend_limit: int | None = None,
    weekly_spend_limit: int | None = None,
    bid_ceiling: int | None = None,
    custom_period_spend_limit: int | None = None,
    custom_period_start_date: str | None = None,
    custom_period_end_date: str | None = None,
    custom_period_auto_continue: str | None = None,
    minimum_exploration_budget: int | None = None,
    counter_ids: str | None = None,
    priority_goals: list[str] | None = None,
    attribution_model: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Update a bidding strategy.

    CLI 0.3.8 replaced --params / --priority-goals JSON with typed flags.
    See `strategies_add` for argument semantics.

    Args:
        id: Strategy ID.
        name: Optional new strategy name.
        type: Optional new strategy type.
        average_cpc: Average CPC in micro-units.
        average_cpa: Average CPA in micro-units.
        average_crr: Average cost-revenue ratio (integer percent).
        goal_id: Goal ID for conversion strategies.
        spend_limit: Spend limit in micro-units.
        weekly_spend_limit: Weekly spend limit in micro-units.
        bid_ceiling: Bid ceiling in micro-units.
        counter_ids: Comma-separated Metrica counter IDs.
        priority_goals: List of "GOAL_ID:VALUE" specs.
        attribution_model: Attribution model code.
        dry_run: Show the direct request without sending it.
    """
    if (
        all(
            v is None
            for v in (
                name,
                type,
                average_cpc,
                average_cpa,
                average_crr,
                goal_id,
                spend_limit,
                weekly_spend_limit,
                bid_ceiling,
                custom_period_spend_limit,
                custom_period_start_date,
                custom_period_end_date,
                custom_period_auto_continue,
                minimum_exploration_budget,
                counter_ids,
                attribution_model,
            )
        )
        and not priority_goals
    ):
        return ToolError(
            error="missing_update_fields",
            message=(
                "Provide at least one of: name, type, average_cpc, average_cpa, "
                "average_crr, goal_id, spend_limit, weekly_spend_limit, "
                "bid_ceiling, custom_period_*, minimum_exploration_budget, "
                "counter_ids, priority_goals, attribution_model"
            ),
        ).__dict__
    if type is not None and type not in STRATEGY_TYPES:
        return ToolError(
            error="invalid_type",
            message=f"type must be one of {STRATEGY_TYPES}; got '{type}'",
        ).__dict__
    if attribution_model is not None and attribution_model not in ATTRIBUTION_MODELS:
        return ToolError(
            error="invalid_attribution_model",
            message=(
                f"attribution_model must be one of {ATTRIBUTION_MODELS}; "
                f"got '{attribution_model}'"
            ),
        ).__dict__

    args = ["strategies", "update", "--id", str(id)]
    if name is not None:
        args.extend(["--name", name])
    if type is not None:
        args.extend(["--type", type])
    if average_cpc is not None:
        args.extend(["--average-cpc", str(average_cpc)])
    if average_cpa is not None:
        args.extend(["--average-cpa", str(average_cpa)])
    if average_crr is not None:
        args.extend(["--average-crr", str(average_crr)])
    if goal_id is not None:
        args.extend(["--goal-id", str(goal_id)])
    if spend_limit is not None:
        args.extend(["--spend-limit", str(spend_limit)])
    if weekly_spend_limit is not None:
        args.extend(["--weekly-spend-limit", str(weekly_spend_limit)])
    if bid_ceiling is not None:
        args.extend(["--bid-ceiling", str(bid_ceiling)])
    if custom_period_spend_limit is not None:
        args.extend(["--custom-period-spend-limit", str(custom_period_spend_limit)])
    if custom_period_start_date is not None:
        args.extend(["--custom-period-start-date", custom_period_start_date])
    if custom_period_end_date is not None:
        args.extend(["--custom-period-end-date", custom_period_end_date])
    if custom_period_auto_continue is not None:
        args.extend(["--custom-period-auto-continue", custom_period_auto_continue])
    if minimum_exploration_budget is not None:
        args.extend(["--minimum-exploration-budget", str(minimum_exploration_budget)])
    if counter_ids is not None:
        args.extend(["--counter-ids", counter_ids])
    if priority_goals:
        for spec in priority_goals:
            args.extend(["--priority-goal", spec])
    if attribution_model is not None:
        args.extend(["--attribution-model", attribution_model])
    if dry_run:
        args.append("--dry-run")
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(name="strategies_archive")
@handle_cli_errors
def strategies_archive(id: int, dry_run: bool = False) -> dict:
    """Archive a bidding strategy.

    Args:
        id: Strategy ID to archive.
        dry_run: Show the direct request without sending it.
    """
    args = ["strategies", "archive", "--id", str(id)]
    if dry_run:
        args.append("--dry-run")
    return get_runner().run_json(args)


@mcp.tool(name="strategies_unarchive")
@handle_cli_errors
def strategies_unarchive(id: int, dry_run: bool = False) -> dict:
    """Unarchive a bidding strategy.

    Args:
        id: Strategy ID to unarchive.
        dry_run: Show the direct request without sending it.
    """
    args = ["strategies", "unarchive", "--id", str(id)]
    if dry_run:
        args.append("--dry-run")
    return get_runner().run_json(args)
