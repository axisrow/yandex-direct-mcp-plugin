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
    ad_group_id: int,
    ad_type: str | None = None,
    title: str | None = None,
    text: str | None = None,
    href: str | None = None,
    image_hash: str | None = None,
    tracking_url: str | None = None,
    action: str | None = None,
    age_label: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Create a new ad.

    CLI 0.3.8 enforces strict WSDL parity — invalid field/type combinations
    (e.g. TEXT_IMAGE_AD + title, MOBILE_APP_AD + href) are rejected by the CLI,
    not by this tool. Field/type compatibility:

    - TEXT_AD: title, text, href.
    - TEXT_IMAGE_AD: href, image_hash.
    - MOBILE_APP_AD: title, text, image_hash, tracking_url, action, age_label.

    Note: fields not yet covered by typed CLI flags (Title2, SitelinkSetId,
    AdExtensions, VCardId, TurboPageId, DisplayUrlPath, Mobile) must be filled
    in via the Direct web UI after `ads_add` — see direct-cli upstream issue.

    Args:
        ad_group_id: Ad group ID to add the ad to.
        ad_type: Ad type (TEXT_AD | TEXT_IMAGE_AD | MOBILE_APP_AD).
        title: Ad title (TEXT_AD / MOBILE_APP_AD).
        text: Ad text content (TEXT_AD / MOBILE_APP_AD).
        href: Ad URL (TEXT_AD / TEXT_IMAGE_AD).
        image_hash: Ad image hash (TEXT_IMAGE_AD / MOBILE_APP_AD).
        tracking_url: MOBILE_APP_AD tracking URL.
        action: MOBILE_APP_AD call-to-action (MobileAppAdActionEnum, e.g. INSTALL).
        age_label: MOBILE_APP_AD age label (MobAppAgeLabelEnum).
        dry_run: Show the direct-cli request without sending it.
    """
    args = ["ads", "add", "--adgroup-id", str(ad_group_id)]
    if ad_type:
        args.extend(["--type", ad_type])
    if title:
        args.extend(["--title", title])
    if text:
        args.extend(["--text", text])
    if href:
        args.extend(["--href", href])
    if image_hash:
        args.extend(["--image-hash", image_hash])
    if tracking_url:
        args.extend(["--tracking-url", tracking_url])
    if action:
        args.extend(["--action", action])
    if age_label:
        args.extend(["--age-label", age_label])
    if dry_run:
        args.append("--dry-run")
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def ads_update(
    id: int,
    type: str,
    title: str | None = None,
    text: str | None = None,
    href: str | None = None,
    image_hash: str | None = None,
    tracking_url: str | None = None,
    action: str | None = None,
    age_label: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Update an ad.

    CLI 0.3.8 made `--type` required for `ads update` and removed the
    `--status` flag (use `ads_suspend / ads_resume / ads_archive /
    ads_unarchive` for status changes). Field/type compatibility:

    - TEXT_AD: title, text, href.
    - TEXT_IMAGE_AD: href, image_hash.
    - MOBILE_APP_AD: title, text, image_hash, tracking_url, action, age_label.

    Args:
        id: Ad ID to update.
        type: Ad subtype (TEXT_AD | TEXT_IMAGE_AD | MOBILE_APP_AD). Required.
        title: Optional new title (TEXT_AD / MOBILE_APP_AD).
        text: Optional new text (TEXT_AD / MOBILE_APP_AD).
        href: Optional new URL (TEXT_AD / TEXT_IMAGE_AD).
        image_hash: Optional new image hash (TEXT_IMAGE_AD / MOBILE_APP_AD).
        tracking_url: Optional MOBILE_APP_AD tracking URL.
        action: Optional MOBILE_APP_AD call-to-action.
        age_label: Optional MOBILE_APP_AD age label.
        dry_run: Show the direct-cli request without sending it.
    """
    if not any((title, text, href, image_hash, tracking_url, action, age_label)):
        return ToolError(
            error="missing_update_fields",
            message=(
                "Provide at least one of: title, text, href, image_hash, "
                "tracking_url, action, age_label. For status changes use "
                "ads_suspend / ads_resume / ads_archive / ads_unarchive."
            ),
        ).__dict__

    args = ["ads", "update", "--id", str(id), "--type", type]
    if title:
        args.extend(["--title", title])
    if text:
        args.extend(["--text", text])
    if href:
        args.extend(["--href", href])
    if image_hash:
        args.extend(["--image-hash", image_hash])
    if tracking_url:
        args.extend(["--tracking-url", tracking_url])
    if action:
        args.extend(["--action", action])
    if age_label:
        args.extend(["--age-label", age_label])
    if dry_run:
        args.append("--dry-run")
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
