"""MCP tools for leads management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit


@mcp.tool(name="leads_get")
@handle_cli_errors
def leads_list(campaign_ids: str | None = None) -> dict:
    """List leads for specified campaigns.

    Args:
        campaign_ids: Comma-separated campaign IDs (max 10).
            If None, returns leads for all campaigns.
    """
    args = ["leads", "get", "--format", "json"]
    normalized_campaign_ids = campaign_ids.strip() if campaign_ids is not None else None
    if normalized_campaign_ids:
        batch_error = check_batch_limit(normalized_campaign_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--campaign-ids", normalized_campaign_ids])

    runner = get_runner()
    return runner.run_json(args)
