"""MCP tools for Yandex Direct v4 Live goals commands."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors


def _run_goals_command(method: str, campaign_ids: str) -> dict | list[dict]:
    normalized_ids = campaign_ids.strip()
    if not normalized_ids:
        return ToolError(
            error="missing_campaign_ids",
            message="Provide at least one campaign ID.",
        ).__dict__
    return get_runner().run_json(
        ["v4goals", method, "--campaign-ids", normalized_ids, "--format", "json"]
    )


@mcp.tool(name="v4goals_get_stat_goals")
@handle_cli_errors
def v4goals_get_stat_goals(campaign_ids: str) -> dict | list[dict]:
    """Get Yandex Metrica goals available for campaigns.

    Args:
        campaign_ids: Comma-separated campaign IDs.
    """
    return _run_goals_command("get-stat-goals", campaign_ids)


@mcp.tool(name="v4goals_get_retargeting_goals")
@handle_cli_errors
def v4goals_get_retargeting_goals(campaign_ids: str) -> dict | list[dict]:
    """Get retargeting goals for campaigns.

    Args:
        campaign_ids: Comma-separated campaign IDs.
    """
    return _run_goals_command("get-retargeting-goals", campaign_ids)
