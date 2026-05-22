"""MCP tools for Yandex Direct v4 Live tag commands."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_tags(tags: list[str] | None) -> list[str]:
    if not tags:
        return []
    return [tag.strip() for tag in tags if tag.strip()]


@mcp.tool(name="v4tags_get_campaigns")
@handle_cli_errors
def v4tags_get_campaigns(campaign_ids: str) -> dict | list[dict]:
    """Get campaign tags via v4 Live GetCampaignsTags.

    Args:
        campaign_ids: Comma-separated campaign IDs.
    """
    normalized_ids = campaign_ids.strip()
    if not normalized_ids:
        return ToolError(
            error="missing_campaign_ids",
            message="Provide at least one campaign ID.",
        ).__dict__

    return get_runner().run_json(
        [
            "v4tags",
            "get-campaigns",
            "--campaign-ids",
            normalized_ids,
            "--format",
            "json",
        ]
    )


@mcp.tool(name="v4tags_get_banners")
@handle_cli_errors
def v4tags_get_banners(
    campaign_ids: str | None = None, banner_ids: str | None = None
) -> dict | list[dict]:
    """Get banner tag IDs via v4 Live GetBannersTags.

    Args:
        campaign_ids: Comma-separated campaign IDs, up to 10.
        banner_ids: Comma-separated banner IDs, up to 2000.
    """
    normalized_campaign_ids = _normalize_optional(campaign_ids)
    normalized_banner_ids = _normalize_optional(banner_ids)
    if normalized_campaign_ids and normalized_banner_ids:
        return ToolError(
            error="conflicting_selectors",
            message="Pass either campaign_ids or banner_ids, not both.",
        ).__dict__
    if not normalized_campaign_ids and not normalized_banner_ids:
        return ToolError(
            error="missing_selector",
            message="Pass campaign_ids or banner_ids.",
        ).__dict__
    if normalized_campaign_ids:
        batch_error = check_batch_limit(normalized_campaign_ids, max_size=10)
        if batch_error:
            return batch_error.__dict__
    if normalized_banner_ids:
        batch_error = check_batch_limit(normalized_banner_ids, max_size=2000)
        if batch_error:
            return batch_error.__dict__

    args = ["v4tags", "get-banners"]
    if normalized_campaign_ids:
        args.extend(["--campaign-ids", normalized_campaign_ids])
    else:
        assert normalized_banner_ids is not None
        args.extend(["--banner-ids", normalized_banner_ids])
    args.extend(["--format", "json"])

    return get_runner().run_json(args)


@mcp.tool(name="v4tags_update_campaigns")
@handle_cli_errors
def v4tags_update_campaigns(
    campaign_id: int,
    tags: list[str] | None = None,
    clear_tags: bool = False,
    dry_run: bool = False,
) -> dict | list[dict]:
    """Replace campaign tags via v4 Live UpdateCampaignsTags.

    Args:
        campaign_id: Campaign ID.
        tags: Campaign tags in TAG_ID=TEXT form. Use 0 for a new tag.
        clear_tags: Remove all campaign tags.
        dry_run: Show the direct request without sending it.
    """
    normalized_tags = _normalize_tags(tags)
    if normalized_tags and clear_tags:
        return ToolError(
            error="conflicting_tag_actions",
            message="Pass tags or clear_tags, not both.",
        ).__dict__
    if not normalized_tags and not clear_tags:
        return ToolError(
            error="missing_tag_action",
            message="Pass tags or set clear_tags=True.",
        ).__dict__

    args = ["v4tags", "update-campaigns", "--campaign-id", str(campaign_id)]
    for tag in normalized_tags:
        args.extend(["--tag", tag])
    if clear_tags:
        args.append("--clear-tags")
    if dry_run:
        args.append("--dry-run")
    args.extend(["--format", "json"])

    return get_runner().run_json(args)


@mcp.tool(name="v4tags_update_banners")
@handle_cli_errors
def v4tags_update_banners(
    banner_ids: str,
    tag_ids: str | None = None,
    clear_tags: bool = False,
    dry_run: bool = False,
) -> dict | list[dict]:
    """Replace banner tag assignments via v4 Live UpdateBannersTags.

    Args:
        banner_ids: Comma-separated banner IDs.
        tag_ids: Comma-separated campaign tag IDs, up to 30.
        clear_tags: Remove all banner tags.
        dry_run: Show the direct request without sending it.
    """
    normalized_banner_ids = banner_ids.strip()
    if not normalized_banner_ids:
        return ToolError(
            error="missing_banner_ids",
            message="Provide at least one banner ID.",
        ).__dict__

    normalized_tag_ids = _normalize_optional(tag_ids)
    if normalized_tag_ids and clear_tags:
        return ToolError(
            error="conflicting_tag_actions",
            message="Pass tag_ids or clear_tags, not both.",
        ).__dict__
    if not normalized_tag_ids and not clear_tags:
        return ToolError(
            error="missing_tag_action",
            message="Pass tag_ids or set clear_tags=True.",
        ).__dict__
    if normalized_tag_ids:
        batch_error = check_batch_limit(normalized_tag_ids, max_size=30)
        if batch_error:
            return batch_error.__dict__

    args = ["v4tags", "update-banners", "--banner-ids", normalized_banner_ids]
    if normalized_tag_ids:
        args.extend(["--tag-ids", normalized_tag_ids])
    if clear_tags:
        args.append("--clear-tags")
    if dry_run:
        args.append("--dry-run")
    args.extend(["--format", "json"])

    return get_runner().run_json(args)
