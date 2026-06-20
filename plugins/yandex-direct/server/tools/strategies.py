"""MCP tools for bidding strategy management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors
from server.tools.helpers import (
    CliOption,
    append_cli_options,
    append_pagination,
    check_batch_limit,
    require_update_fields,
    tool_error_dict,
    validate_enum,
)

IS_ARCHIVED_VALUES = ("YES", "NO")
# Shared money/period fields for strategies add+update, in the exact emission
# order both functions used before — so the emitted argv stays byte-identical.
# name/type are handled explicitly per function (required in add, optional in
# update) and are NOT in this table.
STRATEGY_MUTATION_OPTIONS = (
    CliOption("average_cpc", "--average-cpc"),
    CliOption("average_cpa", "--average-cpa"),
    CliOption("average_crr", "--average-crr"),
    CliOption("goal_id", "--goal-id"),
    CliOption("spend_limit", "--spend-limit"),
    CliOption("weekly_spend_limit", "--weekly-spend-limit"),
    CliOption("bid_ceiling", "--bid-ceiling"),
    CliOption("custom_period_spend_limit", "--custom-period-spend-limit"),
    CliOption("custom_period_start_date", "--custom-period-start-date"),
    CliOption("custom_period_end_date", "--custom-period-end-date"),
    CliOption("custom_period_auto_continue", "--custom-period-auto-continue"),
    CliOption("minimum_exploration_budget", "--minimum-exploration-budget"),
    CliOption("counter_ids", "--counter-ids"),
    CliOption("priority_goals", "--priority-goal", repeat=True),
    CliOption("attribution_model", "--attribution-model"),
)
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


@mcp.tool(
    name="strategies_get",
    description="List bidding strategies, optionally filtered by ID, type, or archived status. Call tool_help('strategies_get') for parameters.",
)
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
    if is_archived is not None:
        enum_error = validate_enum(
            is_archived,
            IS_ARCHIVED_VALUES,
            field="is_archived",
            error="invalid_is_archived",
        )
        if enum_error:
            return tool_error_dict(enum_error)

    args = ["strategies", "get", "--format", "json"]
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        batch_error = check_batch_limit(normalized_ids)
        if batch_error:
            return tool_error_dict(batch_error)
        args.extend(["--ids", normalized_ids])
    if types is not None:
        args.extend(["--types", types])
    if is_archived is not None:
        args.extend(["--is-archived", is_archived])
    append_pagination(args, limit, fetch_all, fields)
    return get_runner().run_json(args)


@mcp.tool(
    name="strategies_add",
    description="Create a new bidding strategy of a given type with its money fields. Call tool_help('strategies_add') for parameters.",
)
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
    type_error = validate_enum(type, STRATEGY_TYPES, field="type", error="invalid_type")
    if type_error:
        return tool_error_dict(type_error)
    if attribution_model is not None:
        attribution_error = validate_enum(
            attribution_model,
            ATTRIBUTION_MODELS,
            field="attribution_model",
            error="invalid_attribution_model",
        )
        if attribution_error:
            return tool_error_dict(attribution_error)
    args = ["strategies", "add", "--name", name, "--type", type]
    append_cli_options(args, locals(), STRATEGY_MUTATION_OPTIONS)
    if dry_run:
        args.append("--dry-run")
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(
    name="strategies_update",
    description="Update an existing bidding strategy's fields by ID. Call tool_help('strategies_update') for parameters.",
)
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
        custom_period_spend_limit: Custom period spend limit in micro-units.
        custom_period_start_date: Custom period start date.
        custom_period_end_date: Custom period end date.
        custom_period_auto_continue: Custom period auto-continue flag.
        minimum_exploration_budget: Minimum exploration budget in micro-units.
        counter_ids: Comma-separated Metrica counter IDs.
        priority_goals: List of "GOAL_ID:VALUE" specs.
        attribution_model: Attribution model code.
        dry_run: Show the direct request without sending it.
    """
    fields_error = require_update_fields(
        locals(),
        message=(
            "Provide at least one of: name, type, average_cpc, average_cpa, "
            "average_crr, goal_id, spend_limit, weekly_spend_limit, "
            "bid_ceiling, custom_period_*, minimum_exploration_budget, "
            "counter_ids, priority_goals, attribution_model"
        ),
        exclude={"id", "dry_run"},
    )
    if fields_error:
        return tool_error_dict(fields_error)
    if type is not None:
        type_error = validate_enum(
            type, STRATEGY_TYPES, field="type", error="invalid_type"
        )
        if type_error:
            return tool_error_dict(type_error)
    if attribution_model is not None:
        attribution_error = validate_enum(
            attribution_model,
            ATTRIBUTION_MODELS,
            field="attribution_model",
            error="invalid_attribution_model",
        )
        if attribution_error:
            return tool_error_dict(attribution_error)

    args = ["strategies", "update", "--id", str(id)]
    if name is not None:
        args.extend(["--name", name])
    if type is not None:
        args.extend(["--type", type])
    append_cli_options(args, locals(), STRATEGY_MUTATION_OPTIONS)
    if dry_run:
        args.append("--dry-run")
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(
    name="strategies_archive",
    description="Archive a bidding strategy by ID. Call tool_help('strategies_archive') for parameters.",
)
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


@mcp.tool(
    name="strategies_unarchive",
    description="Unarchive a bidding strategy by ID. Call tool_help('strategies_unarchive') for parameters.",
)
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
