"""MCP tools for Yandex Direct v4 Live ad-image association commands."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_associations(associations: list[str] | None) -> list[str]:
    if not associations:
        return []
    return [item.strip() for item in associations if item.strip()]


@mcp.tool(name="v4adimage_get")
@handle_cli_errors
def v4adimage_get(
    logins: str | None = None,
    ad_image_hashes: str | None = None,
    status_moderate: list[str] | None = None,
    ad_ids: str | None = None,
    campaign_ids: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
    dry_run: bool = False,
) -> dict | list[dict]:
    """Read ad-image associations via v4 Live AdImageAssociation (Action=Get).

    An empty filter returns up to 10000 associations.

    Args:
        logins: Comma-separated client logins.
        ad_image_hashes: Comma-separated ad image hashes.
        status_moderate: Moderation status filter values (yes/no/ready/sending);
            repeat for several.
        ad_ids: Comma-separated ad IDs.
        campaign_ids: Comma-separated campaign IDs.
        limit: Page size (1-10000).
        offset: Page offset (>=0).
        dry_run: Show the direct request without sending it.
    """
    args = ["v4adimage", "get"]

    normalized_logins = _normalize_optional(logins)
    if normalized_logins:
        args.extend(["--logins", normalized_logins])

    normalized_hashes = _normalize_optional(ad_image_hashes)
    if normalized_hashes:
        args.extend(["--ad-image-hashes", normalized_hashes])

    for status in status_moderate or []:
        normalized_status = status.strip()
        if normalized_status:
            args.extend(["--status-moderate", normalized_status])

    normalized_ad_ids = _normalize_optional(ad_ids)
    if normalized_ad_ids:
        args.extend(["--ad-ids", normalized_ad_ids])

    normalized_campaign_ids = _normalize_optional(campaign_ids)
    if normalized_campaign_ids:
        args.extend(["--campaign-ids", normalized_campaign_ids])

    if limit is not None:
        args.extend(["--limit", str(limit)])
    if offset is not None:
        args.extend(["--offset", str(offset)])
    if dry_run:
        args.append("--dry-run")
    args.extend(["--format", "json"])

    return get_runner().run_json(args)


@mcp.tool(name="v4adimage_set")
@handle_cli_errors
def v4adimage_set(
    associations: list[str],
    dry_run: bool = False,
) -> dict | list[dict]:
    """Link or unlink ad images via v4 Live AdImageAssociation (Action=Set).

    Up to 10000 associations per call.

    Args:
        associations: Each item is ``AD_ID`` to unlink an image, or
            ``AD_ID=HASH`` to link an image. At least one is required.
        dry_run: Show the direct request without sending it.
    """
    normalized = _normalize_associations(associations)
    if not normalized:
        return ToolError(
            error="missing_associations",
            message="Provide at least one association (AD_ID or AD_ID=HASH).",
        ).__dict__

    args = ["v4adimage", "set"]
    for item in normalized:
        args.extend(["--association", item])
    if dry_run:
        args.append("--dry-run")
    args.extend(["--format", "json"])

    return get_runner().run_json(args)
