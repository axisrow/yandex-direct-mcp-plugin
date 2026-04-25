"""MCP tools for bidding strategy management."""

import json

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit


@mcp.tool(name="strategies_get")
@handle_cli_errors
def strategies_list(
    ids: str | None = None,
    types: str | None = None,
    is_archived: str | None = None,
) -> list[dict] | dict:
    """List bidding strategies.

    Args:
        ids: Comma-separated strategy IDs (optional, max 10).
        types: Comma-separated strategy types (optional).
        is_archived: Filter by archived status, "yes" or "no" (optional).
    """
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
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(name="strategies_add")
@handle_cli_errors
def strategies_add(
    name: str,
    type: str,
    params: str | dict | None = None,
    counter_ids: str | None = None,
    priority_goals: str | list | None = None,
    attribution_model: str | None = None,
) -> dict:
    """Add a bidding strategy.

    Args:
        name: Strategy name.
        type: Strategy type (e.g. "AverageCpc", "AverageCpa", "MaxProfit").
        params: Strategy type-specific parameters as JSON string or dict.
            Any bid/CPC/CPA fields inside this JSON are micro-units (RUB × 1,000,000).
        counter_ids: Comma-separated Metrica counter IDs (optional).
        priority_goals: Priority goals as a JSON list/string (optional).
        attribution_model: Attribution model code (optional, e.g. "LYDC").
    """
    args = ["strategies", "add", "--name", name, "--type", type]
    if params is not None:
        params_str = json.dumps(params) if isinstance(params, dict) else params
        args.extend(["--params", params_str])
    if counter_ids is not None:
        args.extend(["--counter-ids", counter_ids])
    if priority_goals is not None:
        goals_str = (
            json.dumps(priority_goals)
            if isinstance(priority_goals, list)
            else priority_goals
        )
        args.extend(["--priority-goals", goals_str])
    if attribution_model is not None:
        args.extend(["--attribution-model", attribution_model])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(name="strategies_update")
@handle_cli_errors
def strategies_update(
    id: int,
    name: str | None = None,
    type: str | None = None,
    params: str | dict | None = None,
    counter_ids: str | None = None,
    priority_goals: str | list | None = None,
    attribution_model: str | None = None,
) -> dict:
    """Update a bidding strategy.

    Args:
        id: Strategy ID.
        name: Optional new strategy name.
        type: Optional new strategy type.
        params: Optional strategy parameters as JSON string or dict.
            Any bid/CPC/CPA fields inside this JSON are micro-units (RUB × 1,000,000).
        counter_ids: Optional comma-separated Metrica counter IDs.
        priority_goals: Optional priority goals as a JSON list/string.
        attribution_model: Optional attribution model code.
    """
    if not any((name, type, params, counter_ids, priority_goals, attribution_model)):
        return ToolError(
            error="missing_update_fields",
            message=(
                "Provide at least one of: name, type, params, counter_ids, "
                "priority_goals, attribution_model"
            ),
        ).__dict__

    args = ["strategies", "update", "--id", str(id)]
    if name is not None:
        args.extend(["--name", name])
    if type is not None:
        args.extend(["--type", type])
    if params is not None:
        params_str = json.dumps(params) if isinstance(params, dict) else params
        args.extend(["--params", params_str])
    if counter_ids is not None:
        args.extend(["--counter-ids", counter_ids])
    if priority_goals is not None:
        goals_str = (
            json.dumps(priority_goals)
            if isinstance(priority_goals, list)
            else priority_goals
        )
        args.extend(["--priority-goals", goals_str])
    if attribution_model is not None:
        args.extend(["--attribution-model", attribution_model])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(name="strategies_archive")
@handle_cli_errors
def strategies_archive(id: int) -> dict:
    """Archive a bidding strategy.

    Args:
        id: Strategy ID to archive.
    """
    runner = get_runner()
    return runner.run_json(["strategies", "archive", "--id", str(id)])


@mcp.tool(name="strategies_unarchive")
@handle_cli_errors
def strategies_unarchive(id: int) -> dict:
    """Unarchive a bidding strategy.

    Args:
        id: Strategy ID to unarchive.
    """
    runner = get_runner()
    return runner.run_json(["strategies", "unarchive", "--id", str(id)])
