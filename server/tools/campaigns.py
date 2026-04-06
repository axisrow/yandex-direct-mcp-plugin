<<<<<<< HEAD
"""MCP tools for campaign management."""

from server.main import mcp
from server.tools import ToolError
from server.cli.runner import DirectCliRunner, CliAuthError, CliNotFoundError, CliTimeoutError

from collections.abc import Callable

# These will be injected by main.py when OAuth is ready
_token_getter: Callable[[], str] | None = None


def set_token_getter(getter: Callable[[], str]) -> None:
    """Set the function that returns a valid OAuth token."""
    global _token_getter
    _token_getter = getter


def _get_runner() -> DirectCliRunner:
    """Get a CLI runner with a valid token."""
    if _token_getter is None:
        return ToolError(
            error="misconfigured",
            message="Token getter not configured. Call set_token_getter() first.",
        ).to_dict()  # type: ignore[return-value]
    token = _token_getter()
    return DirectCliRunner(token=token)


@mcp.tool()
def campaigns_list(state: str | None = None) -> list[dict] | dict:
    """List advertising campaigns, optionally filtered by state.

    Args:
        state: Filter by campaign state ("ON" or "OFF"). If None, returns all campaigns.
    """
    try:
        runner = _get_runner()
        args = ["campaigns", "get", "--format", "json"]
        result = runner.run_json(args)

        if isinstance(result, list) and state:
            result = [c for c in result if c.get("State") == state]

        return result
    except CliAuthError:
        return ToolError(
            error="auth_expired",
            message="Token expired. Re-authorization required.",
        ).to_dict()
    except CliNotFoundError as e:
        return ToolError(error="cli_not_found", message=str(e)).to_dict()
    except CliTimeoutError as e:
        return ToolError(error="timeout", message=str(e)).to_dict()
    except Exception as e:
        return ToolError(error="unknown", message=str(e)).to_dict()


@mcp.tool()
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
        ).to_dict()

    try:
        runner = _get_runner()
        args = ["campaigns", "update", "--id", id, "--state", state, "--format", "json"]
        runner.run_json(args)
        return {"success": True, "id": id, "state": state}
    except CliAuthError:
        return ToolError(
            error="auth_expired",
            message="Token expired. Re-authorization required.",
        ).to_dict()
    except CliNotFoundError as e:
        return ToolError(error="cli_not_found", message=str(e)).to_dict()
    except CliTimeoutError as e:
        return ToolError(error="timeout", message=str(e)).to_dict()
    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower() or "404" in error_msg:
            return ToolError(error="not_found", message=f"Campaign {id} not found").to_dict()
        return ToolError(error="unknown", message=error_msg).to_dict()
=======
"""MCP tools for campaigns."""
# Implementation coming in separate units
>>>>>>> origin/main
