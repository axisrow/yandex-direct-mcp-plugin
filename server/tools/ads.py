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


@mcp.tool(name="ads_get")
@handle_cli_errors
def ads_list(
    campaign_ids: str | None = None,
    ids: str | None = None,
    ad_group_ids: str | None = None,
    status: str | None = None,
    fields: str | None = None,
    text_ad_fields: str | None = None,
) -> list[dict] | dict:
    """List ads.

    Args:
        campaign_ids: Comma-separated campaign IDs (optional, max 10).
        ids: Comma-separated ad IDs (optional, max 10).
        ad_group_ids: Comma-separated ad group IDs (optional, max 10).
        status: Filter by status (optional).
        fields: Comma-separated WSDL FieldNames selectors (optional).
        text_ad_fields: Comma-separated WSDL TextAdFieldNames selectors (e.g. "Title,Text,Href"). Default: Title,Title2,Text,Href.
    """
    normalized_campaign_ids = campaign_ids.strip() if campaign_ids is not None else None
    if normalized_campaign_ids:
        batch_error = _check_batch_limit(normalized_campaign_ids)
        if batch_error:
            return batch_error.__dict__
        foreign_id = _get_foreign_campaign_id(normalized_campaign_ids)
        if foreign_id:
            return ToolError(
                error="foreign_campaign",
                message=(
                    f"Campaign {foreign_id} is unavailable — belongs to another account"
                ),
            ).__dict__

    args = ["ads", "get", "--format", "json"]
    if normalized_campaign_ids:
        args.extend(["--campaign-ids", normalized_campaign_ids])
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        batch_error = _check_batch_limit(normalized_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--ids", normalized_ids])
    normalized_ad_group_ids = ad_group_ids.strip() if ad_group_ids is not None else None
    if normalized_ad_group_ids:
        batch_error = _check_batch_limit(normalized_ad_group_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--adgroup-ids", normalized_ad_group_ids])
    if status is not None:
        args.extend(["--status", status])
    if fields is not None:
        args.extend(["--fields", fields])
    if text_ad_fields is not None:
        args.extend(["--text-ad-fields", text_ad_fields])

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
) -> dict:
    """Create a new ad.

    Args:
        ad_group_id: Ad group ID to add the ad to.
        ad_type: Ad type (optional).
        title: Ad title (optional).
        text: Ad text content (optional).
        href: Ad URL (optional).
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
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def ads_update(
    id: str,
    status: str | None = None,
) -> dict:
    """Update an ad.

    Args:
        id: Ad ID to update.
        status: Optional new ad status.
    """
    if not status:
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one of: status",
        ).__dict__

    args = ["ads", "update", "--id", id, "--status", status]
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
