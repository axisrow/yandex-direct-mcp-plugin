"""MCP tools for bid management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit


@mcp.tool()
@handle_cli_errors
def bids_list(
    campaign_ids: str | None = None,
    ad_group_ids: str | None = None,
    keyword_ids: str | None = None,
) -> list[dict] | dict:
    """List bids.

    Args:
        campaign_ids: Comma-separated campaign IDs (optional, max 10).
        ad_group_ids: Comma-separated ad group IDs (optional, max 10).
        keyword_ids: Comma-separated keyword IDs (optional, max 10).
    """
    args = ["bids", "get", "--format", "json"]
    normalized_campaign_ids = (
        campaign_ids.strip() if campaign_ids is not None else None
    )
    if normalized_campaign_ids:
        batch_error = check_batch_limit(normalized_campaign_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--campaign-ids", normalized_campaign_ids])
    normalized_ad_group_ids = ad_group_ids.strip() if ad_group_ids is not None else None
    if normalized_ad_group_ids:
        batch_error = check_batch_limit(normalized_ad_group_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--adgroup-ids", normalized_ad_group_ids])
    normalized_keyword_ids = keyword_ids.strip() if keyword_ids is not None else None
    if normalized_keyword_ids:
        batch_error = check_batch_limit(normalized_keyword_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--keyword-ids", normalized_keyword_ids])

    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def bids_set(
    campaign_id: str,
    bid: str | None = None,
    extra_json: str | None = None,
) -> dict:
    """Set bid for a campaign.

    Args:
        campaign_id: Campaign ID.
        bid: Bid value passed directly to the CLI. Use the units and
            format expected by the underlying command.
        extra_json: Optional JSON string with additional parameters.
    """
    if bid is None and extra_json is None:
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one of: bid, extra_json",
        ).__dict__

    args = ["bids", "set", "--campaign-id", campaign_id]
    if bid is not None:
        args.extend(["--bid", bid])
    if extra_json is not None:
        args.extend(["--json", extra_json])
    runner = get_runner()
    return runner.run_json(args)
