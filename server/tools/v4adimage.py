"""MCP tools for Yandex Direct v4 Live ad-image association commands."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import (
    finalize_json_args,
    normalize_optional_str,
    normalize_str_list,
)


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

    normalized_logins = normalize_optional_str(logins)
    if normalized_logins:
        args.extend(["--logins", normalized_logins])

    normalized_hashes = normalize_optional_str(ad_image_hashes)
    if normalized_hashes:
        args.extend(["--ad-image-hashes", normalized_hashes])

    for status in normalize_str_list(status_moderate):
        args.extend(["--status-moderate", status])

    normalized_ad_ids = normalize_optional_str(ad_ids)
    if normalized_ad_ids:
        args.extend(["--ad-ids", normalized_ad_ids])

    normalized_campaign_ids = normalize_optional_str(campaign_ids)
    if normalized_campaign_ids:
        args.extend(["--campaign-ids", normalized_campaign_ids])

    if limit is not None:
        args.extend(["--limit", str(limit)])
    if offset is not None:
        args.extend(["--offset", str(offset)])

    return get_runner().run_json(finalize_json_args(args, dry_run))


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
    normalized = normalize_str_list(associations)
    if not normalized:
        return ToolError(
            error="missing_associations",
            message="Provide at least one association (AD_ID or AD_ID=HASH).",
        ).__dict__

    args = ["v4adimage", "set"]
    for item in normalized:
        args.extend(["--association", item])

    return get_runner().run_json(finalize_json_args(args, dry_run))
