"""MCP tools for campaign management."""

from server.cli.runner import CliAuthError, CliNotFoundError
from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors


@mcp.tool()
@handle_cli_errors
def campaigns_list(state: str | None = None) -> list[dict] | dict:
    """List advertising campaigns, optionally filtered by state.

    Args:
        state: Filter by campaign state ("ON" or "OFF"). If None, returns all campaigns.
    """
    if state is not None and state not in ("ON", "OFF"):
        return ToolError(
            error="invalid_state",
            message=f"State must be 'ON' or 'OFF', got '{state}'",
        ).__dict__

    runner = get_runner()
    result = runner.run_json(["campaigns", "get", "--format", "json"])

    if isinstance(result, list) and state:
        result = [c for c in result if c.get("State") == state]

    return result


@mcp.tool()
@handle_cli_errors
def campaigns_update(
    id: str,
    name: str | None = None,
    status: str | None = None,
    budget: str | None = None,
    extra_json: str | None = None,
) -> dict:
    """Update campaign fields.

    Args:
        id: Campaign ID to update.
        name: Optional new campaign name.
        status: Optional new campaign status.
        budget: Optional new daily budget.
        extra_json: Optional JSON string forwarded to direct-cli --json.
    """
    if not any((name, status, budget, extra_json)):
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one of: name, status, budget, extra_json",
        ).__dict__

    budget_value: str | None = None
    if budget is not None:
        try:
            if int(budget) <= 0:
                raise ValueError("Budget must be positive")
            budget_value = budget
        except (ValueError, TypeError):
            return ToolError(
                error="invalid_budget",
                message=f"Budget must be a positive integer. Got: '{budget}'",
            ).__dict__

    runner = get_runner()
    try:
        args = ["campaigns", "update", "--id", id]
        if name:
            args.extend(["--name", name])
        if status:
            args.extend(["--status", status])
        if budget_value is not None:
            args.extend(["--budget", budget_value])
        if extra_json:
            args.extend(["--json", extra_json])
        args.extend(["--format", "json"])
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
    if budget_value is not None:
        result["budget"] = int(budget_value)
    if extra_json:
        result["extra_json"] = extra_json
    return result


@mcp.tool()
@handle_cli_errors
def campaigns_add(name: str, start_date: str) -> dict:
    """Create a new campaign.

    Args:
        name: Campaign name.
        start_date: Campaign start date in YYYY-MM-DD format.
    """
    runner = get_runner()
    result = runner.run_json(
        [
            "campaigns",
            "add",
            "--name",
            name,
            "--start-date",
            start_date,
            "--format",
            "json",
        ]
    )
    return result


@mcp.tool()
@handle_cli_errors
def campaigns_delete(ids: str) -> dict:
    """Delete campaigns.

    Args:
        ids: Comma-separated campaign IDs (max 10).
    """
    from server.tools.helpers import check_batch_limit

    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(["campaigns", "delete", "--ids", ids, "--format", "json"])
    return result


@mcp.tool()
@handle_cli_errors
def campaigns_archive(ids: str) -> dict:
    """Archive campaigns.

    Args:
        ids: Comma-separated campaign IDs (max 10).
    """
    from server.tools.helpers import check_batch_limit

    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(["campaigns", "archive", "--ids", ids, "--format", "json"])
    return result


@mcp.tool()
@handle_cli_errors
def campaigns_unarchive(ids: str) -> dict:
    """Unarchive campaigns.

    Args:
        ids: Comma-separated campaign IDs (max 10).
    """
    from server.tools.helpers import check_batch_limit

    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(
        ["campaigns", "unarchive", "--ids", ids, "--format", "json"]
    )
    return result


@mcp.tool()
@handle_cli_errors
def campaigns_suspend(ids: str) -> dict:
    """Suspend campaigns.

    Args:
        ids: Comma-separated campaign IDs (max 10).
    """
    from server.tools.helpers import check_batch_limit

    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(["campaigns", "suspend", "--ids", ids, "--format", "json"])
    return result


@mcp.tool()
@handle_cli_errors
def campaigns_resume(ids: str) -> dict:
    """Resume suspended campaigns.

    Args:
        ids: Comma-separated campaign IDs (max 10).
    """
    from server.tools.helpers import check_batch_limit

    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(["campaigns", "resume", "--ids", ids, "--format", "json"])
    return result
