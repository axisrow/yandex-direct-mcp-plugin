"""MCP tools for bid modifier management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import (
    check_batch_limit,
    validate_positive_int,
    validate_state,
)


@mcp.tool()
@handle_cli_errors
def bidmodifiers_list(campaign_ids: str) -> list[dict] | dict:
    """List bid modifiers for specified campaigns.

    Args:
        campaign_ids: Comma-separated campaign IDs (max 10).
    """
    batch_error = check_batch_limit(campaign_ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    return runner.run_json(
        ["bidmodifiers", "get", "--campaign-ids", campaign_ids, "--format", "json"]
    )


@mcp.tool()
@handle_cli_errors
def bidmodifiers_set(campaign_id: str, modifier_type: str, value: str) -> dict:
    """Set bid modifier for a campaign.

    Args:
        campaign_id: Campaign ID.
        modifier_type: Type of modifier (e.g., "MULTIPLIER").
        value: Modifier value. Must be a positive integer.
    """
    type_error = validate_state(modifier_type, ("MULTIPLIER",))
    if type_error:
        return type_error.__dict__

    value_result = validate_positive_int(value, "value")
    if isinstance(value_result, ToolError):
        return value_result.__dict__

    runner = get_runner()
    result = runner.run_json(
        [
            "bidmodifiers",
            "set",
            "--campaign-id",
            campaign_id,
            "--type",
            modifier_type,
            "--value",
            str(value_result),
            "--format",
            "json",
        ]
    )
    return result


@mcp.tool()
@handle_cli_errors
def bidmodifiers_toggle(id: str, enabled: bool) -> dict:
    """Toggle bid modifier on/off.

    Args:
        id: Modifier ID.
        enabled: True to enable, False to disable.
    """
    runner = get_runner()
    result = runner.run_json(
        [
            "bidmodifiers",
            "toggle",
            "--id",
            id,
            "--enabled",
            str(enabled).lower(),
            "--format",
            "json",
        ]
    )
    return result


@mcp.tool()
@handle_cli_errors
def bidmodifiers_delete(ids: str) -> dict:
    """Delete bid modifiers.

    Args:
        ids: Comma-separated modifier IDs (max 10).
    """
    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(
        ["bidmodifiers", "delete", "--ids", ids, "--format", "json"]
    )
    return result
