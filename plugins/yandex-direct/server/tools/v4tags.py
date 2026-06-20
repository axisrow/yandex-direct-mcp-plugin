"""MCP tools for Yandex Direct v4 Live tag commands."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import (
    check_batch_limit,
    finalize_json_args,
    normalize_optional_str,
    normalize_str_list,
    require_non_empty_csv,
    tool_error_dict,
)


@mcp.tool(
    name="v4tags_get_campaigns",
    description="Get campaign tags via v4 Live GetCampaignsTags; use v4tags_get_banners for banner tags. Call tool_help('v4tags_get_campaigns') for parameters.",
)
@handle_cli_errors
def v4tags_get_campaigns(campaign_ids: str) -> dict | list[dict]:
    """Get campaign tags via v4 Live GetCampaignsTags.

    Args:
        campaign_ids: Comma-separated campaign IDs.
    """
    normalized_ids = require_non_empty_csv(
        campaign_ids, error="missing_campaign_ids", noun="campaign ID"
    )
    if isinstance(normalized_ids, ToolError):
        return tool_error_dict(normalized_ids)

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


@mcp.tool(
    name="v4tags_get_banners",
    description="Get banner tag IDs via v4 Live GetBannersTags (filter by campaign_ids or banner_ids); use v4tags_get_campaigns for campaign tags. Call tool_help('v4tags_get_banners') for parameters.",
)
@handle_cli_errors
def v4tags_get_banners(
    campaign_ids: str | None = None, banner_ids: str | None = None
) -> dict | list[dict]:
    """Get banner tag IDs via v4 Live GetBannersTags.

    Args:
        campaign_ids: Comma-separated campaign IDs, up to 10.
        banner_ids: Comma-separated banner IDs, up to 2000.
    """
    normalized_campaign_ids = normalize_optional_str(campaign_ids)
    normalized_banner_ids = normalize_optional_str(banner_ids)
    if normalized_campaign_ids and normalized_banner_ids:
        return tool_error_dict(
            ToolError(
                error="conflicting_selectors",
                message="Pass either campaign_ids or banner_ids, not both.",
            )
        )
    if not normalized_campaign_ids and not normalized_banner_ids:
        return tool_error_dict(
            ToolError(
                error="missing_selector",
                message="Pass campaign_ids or banner_ids.",
            )
        )
    if normalized_campaign_ids:
        batch_error = check_batch_limit(normalized_campaign_ids, max_size=10)
        if batch_error:
            return tool_error_dict(batch_error)
    if normalized_banner_ids:
        batch_error = check_batch_limit(normalized_banner_ids, max_size=2000)
        if batch_error:
            return tool_error_dict(batch_error)

    args = ["v4tags", "get-banners"]
    if normalized_campaign_ids:
        args.extend(["--campaign-ids", normalized_campaign_ids])
    else:
        assert normalized_banner_ids is not None
        args.extend(["--banner-ids", normalized_banner_ids])
    args.extend(["--format", "json"])

    return get_runner().run_json(args)


@mcp.tool(
    name="v4tags_update_campaigns",
    description="Replace campaign tags via v4 Live UpdateCampaignsTags; use v4tags_update_banners for banner tags. Call tool_help('v4tags_update_campaigns') for parameters.",
)
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
    normalized_tags = normalize_str_list(tags)
    if normalized_tags and clear_tags:
        return tool_error_dict(
            ToolError(
                error="conflicting_tag_actions",
                message="Pass tags or clear_tags, not both.",
            )
        )
    if not normalized_tags and not clear_tags:
        return tool_error_dict(
            ToolError(
                error="missing_tag_action",
                message="Pass tags or set clear_tags=True.",
            )
        )

    args = ["v4tags", "update-campaigns", "--campaign-id", str(campaign_id)]
    for tag in normalized_tags:
        args.extend(["--tag", tag])
    if clear_tags:
        args.append("--clear-tags")

    return get_runner().run_json(finalize_json_args(args, dry_run))


@mcp.tool(
    name="v4tags_update_banners",
    description="Replace banner tag assignments via v4 Live UpdateBannersTags; use v4tags_update_campaigns for campaign tags. Call tool_help('v4tags_update_banners') for parameters.",
)
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
    normalized_banner_ids = require_non_empty_csv(
        banner_ids, error="missing_banner_ids", noun="banner ID"
    )
    if isinstance(normalized_banner_ids, ToolError):
        return tool_error_dict(normalized_banner_ids)

    normalized_tag_ids = normalize_optional_str(tag_ids)
    if normalized_tag_ids and clear_tags:
        return tool_error_dict(
            ToolError(
                error="conflicting_tag_actions",
                message="Pass tag_ids or clear_tags, not both.",
            )
        )
    if not normalized_tag_ids and not clear_tags:
        return tool_error_dict(
            ToolError(
                error="missing_tag_action",
                message="Pass tag_ids or set clear_tags=True.",
            )
        )
    if normalized_tag_ids:
        batch_error = check_batch_limit(normalized_tag_ids, max_size=30)
        if batch_error:
            return tool_error_dict(batch_error)

    args = ["v4tags", "update-banners", "--banner-ids", normalized_banner_ids]
    if normalized_tag_ids:
        args.extend(["--tag-ids", normalized_tag_ids])
    if clear_tags:
        args.append("--clear-tags")

    return get_runner().run_json(finalize_json_args(args, dry_run))
