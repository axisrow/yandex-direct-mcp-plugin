"""MCP tools for keyword management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors

MAX_BATCH_SIZE = 10


def _check_batch_limit(ids_str: str) -> ToolError | None:
    """Validate batch size of comma-separated IDs."""
    ids = [id.strip() for id in ids_str.split(",") if id.strip()]
    if len(ids) > MAX_BATCH_SIZE:
        return ToolError(
            error="batch_limit",
            message=f"Maximum {MAX_BATCH_SIZE} IDs per request. Got: {len(ids)}",
        )
    return None


@mcp.tool()
@handle_cli_errors
def keywords_list(campaign_ids: str) -> list[dict] | dict:
    """List keywords in specified campaigns.

    Args:
        campaign_ids: Comma-separated campaign IDs (max 10).
    """
    batch_error = _check_batch_limit(campaign_ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    return runner.run_json(
        ["keywords", "get", "--campaign-ids", campaign_ids, "--format", "json"]
    )


@mcp.tool()
@handle_cli_errors
def keywords_update(id: str, bid: str) -> dict:
    """Update keyword bid.

    Args:
        id: Keyword ID.
        bid: New bid in micro-units (e.g., 15 RUB = 15000000). Must be a positive integer.
    """
    try:
        bid_value = int(bid)
        if bid_value <= 0:
            raise ValueError("Bid must be positive")
    except (ValueError, TypeError):
        return ToolError(
            error="invalid_bid",
            message=f"Bid must be a positive integer in micro-units. Got: '{bid}'",
        ).__dict__

    runner = get_runner()
    runner.run_json(
        ["keywords", "update", "--id", id, "--bid", str(bid_value), "--format", "json"]
    )
    return {"success": True, "id": id, "bid": bid_value}


@mcp.tool()
@handle_cli_errors
def keywords_add(campaign_id: str, ad_group_id: str, keywords: str) -> dict:
    """Add keywords to an ad group.

    Args:
        campaign_id: Campaign ID.
        ad_group_id: Ad group ID to add keywords to.
        keywords: Comma-separated keyword list.
    """
    runner = get_runner()
    result = runner.run_json(
        [
            "keywords",
            "add",
            "--campaign-id",
            campaign_id,
            "--ad-group-id",
            ad_group_id,
            "--keywords",
            keywords,
            "--format",
            "json",
        ]
    )
    return result


@mcp.tool()
@handle_cli_errors
def keywords_delete(ids: str) -> dict:
    """Delete keywords.

    Args:
        ids: Comma-separated keyword IDs (max 10).
    """
    from server.tools.helpers import check_batch_limit

    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(["keywords", "delete", "--ids", ids, "--format", "json"])
    return result


@mcp.tool()
@handle_cli_errors
def keywords_suspend(ids: str) -> dict:
    """Suspend keywords.

    Args:
        ids: Comma-separated keyword IDs (max 10).
    """
    from server.tools.helpers import check_batch_limit

    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(["keywords", "suspend", "--ids", ids, "--format", "json"])
    return result


@mcp.tool()
@handle_cli_errors
def keywords_resume(ids: str) -> dict:
    """Resume suspended keywords.

    Args:
        ids: Comma-separated keyword IDs (max 10).
    """
    from server.tools.helpers import check_batch_limit

    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(["keywords", "resume", "--ids", ids, "--format", "json"])
    return result
