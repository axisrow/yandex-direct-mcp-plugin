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
def keywords_update(
    id: str,
    bid: str | None = None,
    context_bid: str | None = None,
    status: str | None = None,
    extra_json: str | None = None,
) -> dict:
    """Update keyword fields.

    Args:
        id: Keyword ID.
        bid: Optional new search bid in micro-units. Must be a positive integer.
        context_bid: Optional new context bid in micro-units. Must be a positive integer.
        status: Optional new keyword status.
        extra_json: Optional JSON string forwarded to direct-cli --json.
    """
    if not any((bid, context_bid, status, extra_json)):
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one of: bid, context_bid, status, extra_json",
        ).__dict__

    def _parse_bid(raw_bid: str | None, field_name: str) -> int | None:
        if raw_bid is None:
            return None
        try:
            bid_value = int(raw_bid)
            if bid_value <= 0:
                raise ValueError("Bid must be positive")
        except (ValueError, TypeError):
            raise ValueError(
                f"{field_name} must be a positive integer in micro-units. Got: '{raw_bid}'"
            ) from None
        return bid_value

    try:
        bid_value = _parse_bid(bid, "bid")
        context_bid_value = _parse_bid(context_bid, "context_bid")
    except ValueError as exc:
        return ToolError(error="invalid_bid", message=str(exc)).__dict__

    runner = get_runner()
    args = ["keywords", "update", "--id", id]
    if bid_value is not None:
        args.extend(["--bid", str(bid_value)])
    if context_bid_value is not None:
        args.extend(["--context-bid", str(context_bid_value)])
    if status:
        args.extend(["--status", status])
    if extra_json:
        args.extend(["--json", extra_json])
    args.extend(["--format", "json"])
    runner.run_json(args)

    result: dict[str, object] = {"success": True, "id": id}
    if bid_value is not None:
        result["bid"] = bid_value
    if context_bid_value is not None:
        result["context_bid"] = context_bid_value
    if status:
        result["status"] = status
    if extra_json:
        result["extra_json"] = extra_json
    return result


@mcp.tool()
@handle_cli_errors
def keywords_add(ad_group_id: str, keyword: str, bid: str | None = None) -> dict:
    """Add a keyword to an ad group.

    Args:
        ad_group_id: Ad group ID to add the keyword to.
        keyword: Keyword text.
        bid: Optional bid (will be converted to micro-units if numeric, e.g. 15 → 15000000).
    """
    args = ["keywords", "add", "--adgroup-id", ad_group_id, "--keyword", keyword]
    if bid is not None:
        args.extend(["--bid", bid])
    args.extend(["--format", "json"])
    runner = get_runner()
    return runner.run_json(args)


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


@mcp.tool()
@handle_cli_errors
def keywords_archive(ids: str) -> dict:
    """Archive keywords.

    Args:
        ids: Comma-separated keyword IDs (max 10).
    """
    from server.tools.helpers import check_batch_limit

    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(["keywords", "archive", "--ids", ids, "--format", "json"])
    return result


@mcp.tool()
@handle_cli_errors
def keywords_unarchive(ids: str) -> dict:
    """Unarchive keywords.

    Args:
        ids: Comma-separated keyword IDs (max 10).
    """
    from server.tools.helpers import check_batch_limit

    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(["keywords", "unarchive", "--ids", ids, "--format", "json"])
    return result
