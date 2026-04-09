"""MCP tool for listing ads."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors

MAX_BATCH_SIZE = 10
FOREIGN_CAMPAIGN_MIN = 73_000_000
FOREIGN_CAMPAIGN_MAX = 77_999_999


def _parse_ids(ids_str: str) -> list[str]:
    """Parse and clean comma-separated IDs."""
    return [id.strip() for id in ids_str.split(",") if id.strip()]


def _check_batch_limit(ids_str: str) -> ToolError | None:
    """Validate batch size of comma-separated IDs."""
    ids = _parse_ids(ids_str)
    if len(ids) > MAX_BATCH_SIZE:
        return ToolError(
            error="batch_limit",
            message=f"Maximum {MAX_BATCH_SIZE} IDs per request. Got: {len(ids)}",
        )
    return None


def _get_foreign_campaign_id(ids_str: str) -> str | None:
    """Return the first campaign ID in the foreign account range (73M-77M), or None."""
    for id_str in _parse_ids(ids_str):
        try:
            cid = int(id_str)
            if FOREIGN_CAMPAIGN_MIN <= cid <= FOREIGN_CAMPAIGN_MAX:
                return id_str
        except ValueError:
            continue
    return None


@mcp.tool()
@handle_cli_errors
def ads_list(campaign_ids: str) -> list[dict] | dict:
    """List ads in specified campaigns.

    Args:
        campaign_ids: Comma-separated campaign IDs (max 10).
    """
    batch_error = _check_batch_limit(campaign_ids)
    if batch_error:
        return batch_error.__dict__

    foreign_id = _get_foreign_campaign_id(campaign_ids)
    if foreign_id:
        return ToolError(
            error="foreign_campaign",
            message=f"Campaign {foreign_id} is unavailable — belongs to another account",
        ).__dict__

    runner = get_runner()
    return runner.run_json(
        ["ads", "get", "--campaign-ids", campaign_ids, "--format", "json"]
    )


@mcp.tool()
@handle_cli_errors
def ads_add(ad_group_id: str, title: str | None = None, text: str | None = None, href: str | None = None) -> dict:
    """Create a new ad.

    Args:
        ad_group_id: Ad group ID to add the ad to.
        title: Ad title (optional).
        text: Ad text content (optional).
        href: Ad URL (optional).
    """
    args = ["ads", "add", "--adgroup-id", ad_group_id]
    if title:
        args.extend(["--title", title])
    if text:
        args.extend(["--text", text])
    if href:
        args.extend(["--href", href])
    args.extend(["--format", "json"])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def ads_update(id: str, extra_json: str | None = None) -> dict:
    """Update an ad.

    Args:
        id: Ad ID to update.
        extra_json: JSON string with fields to update (e.g. '{"TextAd": {"Title": "New"}}').
    """
    args = ["ads", "update", "--id", id]
    if extra_json:
        args.extend(["--json", extra_json])
    args.extend(["--format", "json"])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def ads_delete(ids: str) -> dict:
    """Delete ads.

    Args:
        ids: Comma-separated ad IDs (max 10).
    """
    from server.tools.helpers import check_batch_limit

    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(["ads", "delete", "--ids", ids, "--format", "json"])
    return result


@mcp.tool()
@handle_cli_errors
def ads_moderate(ids: str) -> dict:
    """Submit ads for moderation.

    Args:
        ids: Comma-separated ad IDs (max 10).
    """
    from server.tools.helpers import check_batch_limit

    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(["ads", "moderate", "--ids", ids, "--format", "json"])
    return result


@mcp.tool()
@handle_cli_errors
def ads_suspend(ids: str) -> dict:
    """Suspend ads.

    Args:
        ids: Comma-separated ad IDs (max 10).
    """
    from server.tools.helpers import check_batch_limit

    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(["ads", "suspend", "--ids", ids, "--format", "json"])
    return result


@mcp.tool()
@handle_cli_errors
def ads_resume(ids: str) -> dict:
    """Resume suspended ads.

    Args:
        ids: Comma-separated ad IDs (max 10).
    """
    from server.tools.helpers import check_batch_limit

    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(["ads", "resume", "--ids", ids, "--format", "json"])
    return result


@mcp.tool()
@handle_cli_errors
def ads_archive(ids: str) -> dict:
    """Archive ads.

    Args:
        ids: Comma-separated ad IDs (max 10).
    """
    from server.tools.helpers import check_batch_limit

    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(["ads", "archive", "--ids", ids, "--format", "json"])
    return result


@mcp.tool()
@handle_cli_errors
def ads_unarchive(ids: str) -> dict:
    """Unarchive ads.

    Args:
        ids: Comma-separated ad IDs (max 10).
    """
    from server.tools.helpers import check_batch_limit

    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(["ads", "unarchive", "--ids", ids, "--format", "json"])
    return result
