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
