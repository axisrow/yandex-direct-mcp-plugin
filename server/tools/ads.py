"""MCP tool for listing ads."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import CliOption, append_cli_options

MAX_BATCH_SIZE = 10
MOBILE_VALUES = ("YES", "NO")

ADS_ADD_EXTRA_OPTIONS = (
    CliOption("titles", "--titles"),
    CliOption("texts", "--texts"),
    CliOption("image_hashes", "--image-hashes"),
    CliOption("mobile_app_features", "--mobile-app-feature", repeat=True),
    CliOption("final_url", "--final-url"),
    CliOption("video_extension_creative_id", "--video-extension-creative-id"),
    CliOption("price_extension_price", "--price-extension-price"),
    CliOption("price_extension_old_price", "--price-extension-old-price"),
    CliOption("price_extension_price_qualifier", "--price-extension-price-qualifier"),
    CliOption("price_extension_price_currency", "--price-extension-price-currency"),
    CliOption("video_extension_ids", "--video-extension-ids"),
    CliOption("business_id", "--business-id"),
    CliOption("prefer_vcard_over_business", "--prefer-vcard-over-business"),
    CliOption("erir_ad_description", "--erir-ad-description"),
    CliOption("creative_id", "--creative-id"),
    CliOption("tracking_pixels", "--tracking-pixels"),
    CliOption("logo_extension_hash", "--logo-extension-hash"),
    CliOption("feed_id", "--feed-id"),
    CliOption("feed_filter_conditions", "--feed-filter-condition", repeat=True),
    CliOption("title_sources", "--title-sources"),
    CliOption("text_sources", "--text-sources"),
    CliOption("default_texts", "--default-texts"),
)

ADS_UPDATE_EXTRA_OPTIONS = (
    CliOption("status", "--status"),
    CliOption("titles", "--titles"),
    CliOption("texts", "--texts"),
    CliOption("image_hashes", "--image-hashes"),
    CliOption("mobile_app_features", "--mobile-app-feature", repeat=True),
    CliOption("callouts_add", "--callouts-add"),
    CliOption("callouts_remove", "--callouts-remove"),
    CliOption("callouts_set", "--callouts-set"),
    CliOption("video_extension_creative_id", "--video-extension-creative-id"),
    CliOption("video_extension_ids", "--video-extension-ids"),
    CliOption("price_extension_price", "--price-extension-price"),
    CliOption("price_extension_old_price", "--price-extension-old-price"),
    CliOption("price_extension_price_qualifier", "--price-extension-price-qualifier"),
    CliOption("price_extension_price_currency", "--price-extension-price-currency"),
    CliOption("business_id", "--business-id"),
    CliOption("prefer_vcard_over_business", "--prefer-vcard-over-business"),
    CliOption("erir_ad_description", "--erir-ad-description"),
    CliOption("logo_extension_hash", "--logo-extension-hash"),
    CliOption("creative_id", "--creative-id"),
    CliOption("creative_erir_ad_description", "--creative-erir-ad-description"),
    CliOption("final_url", "--final-url"),
    CliOption("tracking_pixels", "--tracking-pixels"),
    CliOption("feed_filter_conditions", "--feed-filter-condition", repeat=True),
    CliOption("title_sources", "--title-sources"),
    CliOption("text_sources", "--text-sources"),
    CliOption("default_texts", "--default-texts"),
)


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


@mcp.tool(name="ads_get")
@handle_cli_errors
def ads_list(
    campaign_ids: str | None = None,
    ids: str | None = None,
    ad_group_ids: str | None = None,
    status: str | None = None,
    statuses: str | None = None,
    states: str | None = None,
    types: str | None = None,
    mobile: str | None = None,
    vcard_ids: str | None = None,
    sitelink_set_ids: str | None = None,
    image_hashes: str | None = None,
    vcard_moderation_statuses: str | None = None,
    sitelinks_moderation_statuses: str | None = None,
    image_moderation_statuses: str | None = None,
    adextension_ids: str | None = None,
    limit: int | None = None,
    fetch_all: bool = False,
    fields: str | None = None,
    text_ad_fields: str | None = None,
) -> list[dict] | dict:
    """List ads.

    Args:
        campaign_ids: Comma-separated campaign IDs (max 10).
        ids: Comma-separated ad IDs (max 10).
        ad_group_ids: Comma-separated ad group IDs (max 10).
        status: Filter by a single status.
        statuses: Comma-separated statuses.
        states: Comma-separated states.
        types: Comma-separated ad types.
        mobile: "YES" or "NO".
        vcard_ids: Comma-separated vCard IDs.
        sitelink_set_ids: Comma-separated sitelink set IDs.
        image_hashes: Comma-separated ad image hashes.
        vcard_moderation_statuses: Comma-separated vCard moderation statuses.
        sitelinks_moderation_statuses: Comma-separated sitelinks moderation statuses.
        image_moderation_statuses: Comma-separated image moderation statuses.
        adextension_ids: Comma-separated ad extension IDs.
        limit: Limit number of results.
        fetch_all: Fetch all pages.
        fields: Comma-separated top-level FieldNames.
        text_ad_fields: Comma-separated TextAd FieldNames.
    """
    normalized_campaign_ids = campaign_ids.strip() if campaign_ids is not None else None
    if normalized_campaign_ids:
        batch_error = _check_batch_limit(normalized_campaign_ids)
        if batch_error:
            return batch_error.__dict__

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
    if statuses is not None:
        args.extend(["--statuses", statuses])
    if states is not None:
        args.extend(["--states", states])
    if types is not None:
        args.extend(["--types", types])
    if mobile is not None:
        if mobile not in ("YES", "NO"):
            return ToolError(
                error="invalid_mobile",
                message=f"mobile must be YES or NO; got '{mobile}'",
            ).__dict__
        args.extend(["--mobile", mobile])
    if vcard_ids is not None:
        args.extend(["--vcard-ids", vcard_ids])
    if sitelink_set_ids is not None:
        args.extend(["--sitelink-set-ids", sitelink_set_ids])
    if image_hashes is not None:
        args.extend(["--image-hashes", image_hashes])
    if vcard_moderation_statuses is not None:
        args.extend(["--vcard-moderation-statuses", vcard_moderation_statuses])
    if sitelinks_moderation_statuses is not None:
        args.extend(["--sitelinks-moderation-statuses", sitelinks_moderation_statuses])
    if image_moderation_statuses is not None:
        args.extend(["--image-moderation-statuses", image_moderation_statuses])
    if adextension_ids is not None:
        args.extend(["--adextension-ids", adextension_ids])
    if limit is not None:
        args.extend(["--limit", str(limit)])
    if fetch_all:
        args.append("--fetch-all")
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
    titles: str | None = None,
    texts: str | None = None,
    href: str | None = None,
    image_hash: str | None = None,
    image_hashes: str | None = None,
    tracking_url: str | None = None,
    action: str | None = None,
    age_label: str | None = None,
    mobile_app_features: list[str] | None = None,
    title2: str | None = None,
    display_url_path: str | None = None,
    mobile: str | None = None,
    vcard_id: int | None = None,
    sitelink_set_id: int | None = None,
    turbo_page_id: int | None = None,
    ad_extensions: str | None = None,
    final_url: str | None = None,
    video_extension_creative_id: int | None = None,
    price_extension_price: str | None = None,
    price_extension_old_price: str | None = None,
    price_extension_price_qualifier: str | None = None,
    price_extension_price_currency: str | None = None,
    video_extension_ids: str | None = None,
    business_id: int | None = None,
    prefer_vcard_over_business: str | None = None,
    erir_ad_description: str | None = None,
    creative_id: int | None = None,
    tracking_pixels: str | None = None,
    logo_extension_hash: str | None = None,
    feed_id: int | None = None,
    feed_filter_conditions: list[str] | None = None,
    title_sources: str | None = None,
    text_sources: str | None = None,
    default_texts: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Create a new ad.

    CLI 0.3.9 enforces strict WSDL parity — invalid field/type combinations
    (e.g. TEXT_IMAGE_AD + title, MOBILE_APP_AD + href) are rejected by the CLI,
    not by this tool. Field/type compatibility:

    - TEXT_AD: title, text, href, title2, display_url_path, mobile, vcard_id,
      sitelink_set_id, turbo_page_id, ad_extensions, image_hash.
    - TEXT_IMAGE_AD: href, image_hash, turbo_page_id.
    - MOBILE_APP_AD: title, text, image_hash, tracking_url, action, age_label.

    Args:
        ad_group_id: Ad group ID to add the ad to.
        ad_type: Ad type (TEXT_AD | TEXT_IMAGE_AD | MOBILE_APP_AD).
        title: Ad title (TEXT_AD / MOBILE_APP_AD).
        text: Ad text content (TEXT_AD / MOBILE_APP_AD).
        href: Ad URL (TEXT_AD / TEXT_IMAGE_AD).
        image_hash: Ad image hash (TEXT_AD / TEXT_IMAGE_AD / MOBILE_APP_AD).
        tracking_url: MOBILE_APP_AD tracking URL.
        action: MOBILE_APP_AD call-to-action (MobileAppAdActionEnum, e.g. INSTALL).
        age_label: MOBILE_APP_AD age label (MobAppAgeLabelEnum).
        title2: Second headline (TEXT_AD).
        display_url_path: Display URL path (TEXT_AD).
        mobile: "YES" or "NO" — mobile-only ad flag (TEXT_AD).
        vcard_id: VCard ID (TEXT_AD).
        sitelink_set_id: Sitelink set ID (TEXT_AD).
        turbo_page_id: Turbo page ID (TEXT_AD / TEXT_IMAGE_AD).
        ad_extensions: Comma-separated ad extension IDs (TEXT_AD).
        dry_run: Show the direct request without sending it.
    """
    if mobile is not None and mobile not in MOBILE_VALUES:
        return ToolError(
            error="invalid_mobile",
            message=f"mobile must be one of {MOBILE_VALUES}; got '{mobile}'",
        ).__dict__

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
    if title2:
        args.extend(["--title2", title2])
    if display_url_path:
        args.extend(["--display-url-path", display_url_path])
    if mobile is not None:
        args.extend(["--mobile", mobile])
    if vcard_id is not None:
        args.extend(["--vcard-id", str(vcard_id)])
    if sitelink_set_id is not None:
        args.extend(["--sitelink-set-id", str(sitelink_set_id)])
    if turbo_page_id is not None:
        args.extend(["--turbo-page-id", str(turbo_page_id)])
    if ad_extensions:
        args.extend(["--ad-extensions", ad_extensions])
    append_cli_options(args, locals(), ADS_ADD_EXTRA_OPTIONS)
    if dry_run:
        args.append("--dry-run")
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def ads_update(
    id: int,
    type: str | None = None,
    status: str | None = None,
    title: str | None = None,
    text: str | None = None,
    titles: str | None = None,
    texts: str | None = None,
    href: str | None = None,
    image_hash: str | None = None,
    image_hashes: str | None = None,
    tracking_url: str | None = None,
    action: str | None = None,
    age_label: str | None = None,
    mobile_app_features: list[str] | None = None,
    title2: str | None = None,
    display_url_path: str | None = None,
    mobile: str | None = None,
    vcard_id: int | None = None,
    sitelink_set_id: int | None = None,
    turbo_page_id: int | None = None,
    ad_extensions: str | None = None,
    callouts_add: str | None = None,
    callouts_remove: str | None = None,
    callouts_set: str | None = None,
    video_extension_creative_id: int | None = None,
    video_extension_ids: str | None = None,
    price_extension_price: str | None = None,
    price_extension_old_price: str | None = None,
    price_extension_price_qualifier: str | None = None,
    price_extension_price_currency: str | None = None,
    business_id: int | None = None,
    prefer_vcard_over_business: str | None = None,
    erir_ad_description: str | None = None,
    logo_extension_hash: str | None = None,
    creative_id: int | None = None,
    creative_erir_ad_description: str | None = None,
    final_url: str | None = None,
    tracking_pixels: str | None = None,
    feed_filter_conditions: list[str] | None = None,
    title_sources: str | None = None,
    text_sources: str | None = None,
    default_texts: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Update an ad.

    CLI 0.3.12 exposes typed flags for supported ad update subtypes. `type`
    is optional when the CLI can apply the supplied fields without an explicit
    subtype, and `status` is accepted for typed status updates.
    Field/type compatibility examples:

    - TEXT_AD: title, text, href, title2, display_url_path, mobile, vcard_id,
      sitelink_set_id, turbo_page_id, ad_extensions, image_hash.
    - TEXT_IMAGE_AD: href, image_hash, turbo_page_id.
    - MOBILE_APP_AD: title, text, image_hash, tracking_url, action, age_label.

    Args:
        id: Ad ID to update.
        type: Optional ad subtype (TEXT_AD, TEXT_IMAGE_AD, MOBILE_APP_AD, and
            newer 0.3.12 subtype families).
        status: Optional ad status value.
        title: Optional new title (TEXT_AD / MOBILE_APP_AD).
        text: Optional new text (TEXT_AD / MOBILE_APP_AD).
        titles: Structured title list for responsive/shopping/listing subtypes.
        texts: Structured text list for responsive/shopping/listing subtypes.
        href: Optional new URL (TEXT_AD / TEXT_IMAGE_AD).
        image_hash: Optional new image hash (TEXT_AD / TEXT_IMAGE_AD / MOBILE_APP_AD).
        image_hashes: Structured image hash list for multi-image subtypes.
        tracking_url: Optional MOBILE_APP_AD tracking URL.
        action: Optional MOBILE_APP_AD call-to-action.
        age_label: Optional MOBILE_APP_AD age label.
        mobile_app_features: Repeated MOBILE_APP_AD feature specs.
        title2: Optional second headline (TEXT_AD).
        display_url_path: Optional display URL path (TEXT_AD).
        mobile: Optional "YES"/"NO" mobile-only ad flag (TEXT_AD).
        vcard_id: Optional VCard ID (TEXT_AD).
        sitelink_set_id: Optional sitelink set ID (TEXT_AD).
        turbo_page_id: Optional Turbo page ID (TEXT_AD / TEXT_IMAGE_AD).
        ad_extensions: Optional comma-separated ad extension IDs (TEXT_AD).
        callouts_add/callouts_remove/callouts_set: Callout update operations.
        video_extension_*: Video extension typed fields.
        price_extension_*: Price extension typed fields.
        business_id/prefer_vcard_over_business: Business/VCard binding fields.
        erir_ad_description: ERIR ad description.
        logo_extension_hash: Logo extension hash.
        creative_id/creative_erir_ad_description: Ad builder creative fields.
        final_url/tracking_pixels: Final URL and tracking pixel fields.
        feed_filter_conditions: Repeated feed filter condition specs.
        title_sources/text_sources/default_texts: Smart/ad builder text sources.
        dry_run: Show the direct request without sending it.
    """
    if not any(
        (
            title,
            text,
            titles,
            texts,
            href,
            image_hash,
            image_hashes,
            tracking_url,
            action,
            age_label,
            mobile_app_features,
            title2,
            display_url_path,
            mobile,
            vcard_id,
            sitelink_set_id,
            turbo_page_id,
            ad_extensions,
            status,
            callouts_add,
            callouts_remove,
            callouts_set,
            video_extension_creative_id,
            video_extension_ids,
            price_extension_price,
            price_extension_old_price,
            price_extension_price_qualifier,
            price_extension_price_currency,
            business_id,
            prefer_vcard_over_business,
            erir_ad_description,
            logo_extension_hash,
            creative_id,
            creative_erir_ad_description,
            final_url,
            tracking_pixels,
            feed_filter_conditions,
            title_sources,
            text_sources,
            default_texts,
        )
    ):
        return ToolError(
            error="missing_update_fields",
            message=(
                "Provide at least one typed update field, for example: title, "
                "text, href, image_hash, tracking_url, action, age_label, "
                "title2, display_url_path, mobile, vcard_id, sitelink_set_id, "
                "turbo_page_id, ad_extensions, status, callouts_*, "
                "video_extension_*, price_extension_*, business_id, "
                "creative_id, final_url, tracking_pixels, "
                "feed_filter_conditions, title_sources, text_sources, or "
                "default_texts."
            ),
        ).__dict__
    if mobile is not None and mobile not in MOBILE_VALUES:
        return ToolError(
            error="invalid_mobile",
            message=f"mobile must be one of {MOBILE_VALUES}; got '{mobile}'",
        ).__dict__

    args = ["ads", "update", "--id", str(id)]
    if type is not None:
        args.extend(["--type", type])
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
    if title2:
        args.extend(["--title2", title2])
    if display_url_path:
        args.extend(["--display-url-path", display_url_path])
    if mobile is not None:
        args.extend(["--mobile", mobile])
    if vcard_id is not None:
        args.extend(["--vcard-id", str(vcard_id)])
    if sitelink_set_id is not None:
        args.extend(["--sitelink-set-id", str(sitelink_set_id)])
    if turbo_page_id is not None:
        args.extend(["--turbo-page-id", str(turbo_page_id)])
    if ad_extensions:
        args.extend(["--ad-extensions", ad_extensions])
    append_cli_options(args, locals(), ADS_UPDATE_EXTRA_OPTIONS)
    if dry_run:
        args.append("--dry-run")
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def ads_delete(ids: str, dry_run: bool = False) -> dict:
    """Delete ads.

    Args:
        ids: Comma-separated ad IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "ads", "delete", ids, dry_run=dry_run)


@mcp.tool()
@handle_cli_errors
def ads_moderate(ids: str, dry_run: bool = False) -> dict:
    """Submit ads for moderation.

    Args:
        ids: Comma-separated ad IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "ads", "moderate", ids, dry_run=dry_run)


@mcp.tool()
@handle_cli_errors
def ads_suspend(ids: str, dry_run: bool = False) -> dict:
    """Suspend ads.

    Args:
        ids: Comma-separated ad IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "ads", "suspend", ids, dry_run=dry_run)


@mcp.tool()
@handle_cli_errors
def ads_resume(ids: str, dry_run: bool = False) -> dict:
    """Resume suspended ads.

    Args:
        ids: Comma-separated ad IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "ads", "resume", ids, dry_run=dry_run)


@mcp.tool()
@handle_cli_errors
def ads_archive(ids: str, dry_run: bool = False) -> dict:
    """Archive ads.

    Args:
        ids: Comma-separated ad IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "ads", "archive", ids, dry_run=dry_run)


@mcp.tool()
@handle_cli_errors
def ads_unarchive(ids: str, dry_run: bool = False) -> dict:
    """Unarchive ads.

    Args:
        ids: Comma-separated ad IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "ads", "unarchive", ids, dry_run=dry_run)
