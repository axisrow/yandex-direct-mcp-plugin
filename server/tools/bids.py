"""MCP tools for bid management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors
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
    if campaign_ids is not None:
        batch_error = check_batch_limit(campaign_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--campaign-ids", campaign_ids])
    if ad_group_ids is not None:
        batch_error = check_batch_limit(ad_group_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--adgroup-ids", ad_group_ids])
    if keyword_ids is not None:
        batch_error = check_batch_limit(keyword_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--keyword-ids", keyword_ids])

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
        bid: Bid amount in currency units (will be converted to
            micro-units). E.g. "15" for 15 RUB.
        extra_json: Optional JSON string with additional parameters.
    """
    args = ["bids", "set", "--campaign-id", campaign_id]
    if bid is not None:
        args.extend(["--bid", bid])
    if extra_json is not None:
        args.extend(["--json", extra_json])
    runner = get_runner()
    return runner.run_json(args)
