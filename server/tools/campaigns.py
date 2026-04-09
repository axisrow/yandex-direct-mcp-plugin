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
def campaigns_update(id: str, state: str) -> dict:
    """Update campaign state (enable or disable).

    Args:
        id: Campaign ID to update.
        state: New state ("ON" to enable, "OFF" to disable).
    """
    if state not in ("ON", "OFF"):
        return ToolError(
            error="invalid_state",
            message=f"State must be 'ON' or 'OFF', got '{state}'",
        ).__dict__

    runner = get_runner()
    try:
        runner.run_json(
            ["campaigns", "update", "--id", id, "--state", state, "--format", "json"]
        )
    except (CliAuthError, CliNotFoundError):
        raise
    except Exception as exc:
        if "not found" in str(exc).lower():
            return ToolError(
                error="not_found", message=f"Campaign '{id}' not found"
            ).__dict__
        raise
    return {"success": True, "id": id, "state": state}


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
