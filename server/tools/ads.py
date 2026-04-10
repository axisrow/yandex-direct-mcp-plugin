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
def ads_list(
    campaign_ids: str | None = None,
    ids: str | None = None,
    ad_group_ids: str | None = None,
    status: str | None = None,
) -> list[dict] | dict:
    """List ads.

    Args:
        campaign_ids: Comma-separated campaign IDs (optional, max 10).
        ids: Comma-separated ad IDs (optional, max 10).
        ad_group_ids: Comma-separated ad group IDs (optional, max 10).
        status: Filter by status (optional).
    """
    if campaign_ids is not None:
        batch_error = _check_batch_limit(campaign_ids)
        if batch_error:
            return batch_error.__dict__
        foreign_id = _get_foreign_campaign_id(campaign_ids)
        if foreign_id:
            return ToolError(
                error="foreign_campaign",
                message=(
                    f"Campaign {foreign_id} is unavailable — belongs to another account"
                ),
            ).__dict__

    args = ["ads", "get", "--format", "json"]
    if campaign_ids is not None:
        args.extend(["--campaign-ids", campaign_ids])
    if ids is not None:
        batch_error = _check_batch_limit(ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--ids", ids])
    if ad_group_ids is not None:
        batch_error = _check_batch_limit(ad_group_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--adgroup-ids", ad_group_ids])
    if status is not None:
        args.extend(["--status", status])

    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def ads_add(
    ad_group_id: str,
    ad_type: str | None = None,
    title: str | None = None,
    text: str | None = None,
    href: str | None = None,
    extra_json: str | None = None,
) -> dict:
    """Create a new ad.

    Args:
        ad_group_id: Ad group ID to add the ad to.
        ad_type: Ad type (optional).
        title: Ad title (optional).
        text: Ad text content (optional).
        href: Ad URL (optional).
        extra_json: JSON string with additional parameters (optional).
    """
    args = ["ads", "add", "--adgroup-id", ad_group_id]
    if ad_type:
        args.extend(["--type", ad_type])
    if title:
        args.extend(["--title", title])
    if text:
        args.extend(["--text", text])
    if href:
        args.extend(["--href", href])
    if extra_json:
        args.extend(["--json", extra_json])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def ads_update(
    id: str, status: str | None = None, extra_json: str | None = None
) -> dict:
    """Update an ad.

    Args:
        id: Ad ID to update.
        status: Optional new ad status.
        extra_json: JSON string with fields to update (e.g. '{"TextAd": {"Title": "New"}}').
    """
    if not status and not extra_json:
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one of: status, extra_json",
        ).__dict__

    args = ["ads", "update", "--id", id]
    if status:
        args.extend(["--status", status])
    if extra_json:
        args.extend(["--json", extra_json])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def ads_delete(ids: str) -> dict:
    """Delete ads.

    Args:
        ids: Comma-separated ad IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "ads", "delete", ids)


@mcp.tool()
@handle_cli_errors
def ads_moderate(ids: str) -> dict:
    """Submit ads for moderation.

    Args:
        ids: Comma-separated ad IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "ads", "moderate", ids)


@mcp.tool()
@handle_cli_errors
def ads_suspend(ids: str) -> dict:
    """Suspend ads.

    Args:
        ids: Comma-separated ad IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "ads", "suspend", ids)


@mcp.tool()
@handle_cli_errors
def ads_resume(ids: str) -> dict:
    """Resume suspended ads.

    Args:
        ids: Comma-separated ad IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "ads", "resume", ids)


@mcp.tool()
@handle_cli_errors
def ads_archive(ids: str) -> dict:
    """Archive ads.

    Args:
        ids: Comma-separated ad IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "ads", "archive", ids)


@mcp.tool()
@handle_cli_errors
def ads_unarchive(ids: str) -> dict:
    """Unarchive ads.

    Args:
        ids: Comma-separated ad IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "ads", "unarchive", ids)
