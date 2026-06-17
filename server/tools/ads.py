"""MCP tool for listing ads."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import (
    CliOption,
    append_cli_options,
    check_batch_limit,
    run_batch_mutation,
    tool_error_dict,
    validate_yes_no,
)

MAX_BATCH_SIZE = 10

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


@mcp.tool(
    name="ads_get",
    description="List ads filtered by campaign, ad group, or ad IDs, plus optional status/type filters. Read-only; use ads_add to create or ads_update to modify. Call tool_help('ads_get') for parameters.",
)
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
        batch_error = check_batch_limit(normalized_campaign_ids, MAX_BATCH_SIZE)
        if batch_error:
            return tool_error_dict(batch_error)

    args = ["ads", "get", "--format", "json"]
    if normalized_campaign_ids:
        args.extend(["--campaign-ids", normalized_campaign_ids])
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        batch_error = check_batch_limit(normalized_ids, MAX_BATCH_SIZE)
        if batch_error:
            return tool_error_dict(batch_error)
        args.extend(["--ids", normalized_ids])
    normalized_ad_group_ids = ad_group_ids.strip() if ad_group_ids is not None else None
    if normalized_ad_group_ids:
        batch_error = check_batch_limit(normalized_ad_group_ids, MAX_BATCH_SIZE)
        if batch_error:
            return tool_error_dict(batch_error)
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
        err = validate_yes_no(mobile, field="mobile", error="invalid_mobile")
        if err is not None:
            return tool_error_dict(err)
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
        args.extend(["--text-ad-field-names", text_ad_fields])

    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(
    description="Create one or many ads — a single ad in an ad group, or a batch via from_file/ads_json. Use ads_update to change an existing ad. Call tool_help('ads_add') for parameters.",
)
@handle_cli_errors
def ads_add(
    ad_group_id: int | None = None,
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
    from_file: str | None = None,
    ads_json: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Create one or many ads.

    Three mutually exclusive modes (CLI #562):

    1. Single: ad_group_id + typed ad fields.
    2. JSONL batch: from_file = path to a .jsonl file, one ad object per line.
       Per-row keys use the kebab CLI-flag form ("adgroup-id", "type", "title",
       "image-hash", ...); "type" defaults to TEXT_AD, and ad_group_id acts as
       the batch default for rows that omit "adgroup-id".
    3. Inline JSON: ads_json = a JSON array of the same objects.

    In batch mode the rows are the source of truth; any single-item content
    field passed alongside from_file/ads_json is ignored.

    CLI 0.3.9 enforces strict WSDL parity — invalid field/type combinations
    (e.g. TEXT_IMAGE_AD + title, MOBILE_APP_AD + href) are rejected by the CLI,
    not by this tool. Field/type compatibility:

    - TEXT_AD: title, text, href, title2, display_url_path, mobile, vcard_id,
      sitelink_set_id, turbo_page_id, ad_extensions, image_hash.
    - TEXT_IMAGE_AD: href, image_hash, turbo_page_id.
    - MOBILE_APP_AD: title, text, image_hash, tracking_url, action, age_label.

    CLI #562 forwards the array as Yandex Direct API requests (chunked at 100,
    API ceiling 1000 per call) with partial-success reporting.

    Args:
        ad_group_id: Ad group ID. Required in single mode; optional default in
            batch modes (each row's adgroup-id wins).
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
        from_file: Path to a JSONL file with ad objects (batch mode).
        ads_json: Inline JSON array of ad objects (batch mode).
        dry_run: Show the direct request without sending it.
    """
    result = run_batch_mutation(
        get_runner(),
        "ads",
        "add",
        from_file=from_file,
        json_arg=ads_json,
        json_flag="--ads-json",
        default_id_flag="--adgroup-id",
        default_id=ad_group_id,
        dry_run=dry_run,
    )
    if result is not None:
        return result

    if ad_group_id is None:
        return tool_error_dict(
            ToolError(
                error="missing_mode",
                message=(
                    "Provide exactly one of: ad_group_id (single ad), from_file "
                    "(JSONL), or ads_json (inline JSON array)."
                ),
            )
        )

    if mobile is not None:
        err = validate_yes_no(mobile, field="mobile", error="invalid_mobile")
        if err is not None:
            return tool_error_dict(err)

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


@mcp.tool(
    description="Update one or many ads — a single ad by id, or a batch via from_file/ads_json. Supports clear_image_hash to reset AdImageHash. For status changes use ads_suspend/resume/archive/unarchive. Use ads_add to create. Call tool_help('ads_update') for parameters.",
)
@handle_cli_errors
def ads_update(
    id: int | None = None,
    type: str | None = None,
    status: str | None = None,
    title: str | None = None,
    text: str | None = None,
    titles: str | None = None,
    texts: str | None = None,
    href: str | None = None,
    image_hash: str | None = None,
    clear_image_hash: bool = False,
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
    from_file: str | None = None,
    ads_json: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Update one or many ads.

    Three mutually exclusive modes (CLI #563):

    1. Single: id (+ at least one typed update field).
    2. JSONL batch: from_file = path to a .jsonl file, one ad-update object per
       line. Per-row keys use the kebab CLI-flag form ("id", "type",
       "image-hash", "clear-image-hash", ...); "id" is required per row.
    3. Inline JSON: ads_json = a JSON array of the same objects.

    In batch mode the rows are the source of truth; any single-item content
    field passed alongside from_file/ads_json is ignored.

    CLI 0.3.12 exposes typed flags for supported ad update subtypes. `type`
    is optional when the CLI can apply the supplied fields without an explicit
    subtype. Ad *status* is NOT mutable here (WSDL AdUpdateItem has no status
    field; CLI 0.4.2 rejects `--status`) — use ads_suspend / ads_resume /
    ads_archive / ads_unarchive to change an ad's status instead.
    Field/type compatibility examples:

    - TEXT_AD: title, text, href, title2, display_url_path, mobile, vcard_id,
      sitelink_set_id, turbo_page_id, ad_extensions, image_hash.
    - TEXT_IMAGE_AD: href, image_hash, turbo_page_id.
    - MOBILE_APP_AD: title, text, image_hash, tracking_url, action, age_label.

    Args:
        id: Ad ID to update (single mode).
        type: Ad subtype (TEXT_AD, TEXT_IMAGE_AD, MOBILE_APP_AD, and newer
            0.3.12 subtype families). Required by the CLI in single mode — it
            picks the typed payload branch; omit it and the CLI rejects the call.
        status: Deprecated — ad status is not mutable via this tool. Passing it
            returns an error pointing to ads_suspend/resume/archive/unarchive.
        title: Optional new title (TEXT_AD / MOBILE_APP_AD).
        text: Optional new text (TEXT_AD / MOBILE_APP_AD).
        titles: Structured title list for responsive/shopping/listing subtypes.
        texts: Structured text list for responsive/shopping/listing subtypes.
        href: Optional new URL (TEXT_AD / TEXT_IMAGE_AD).
        image_hash: Optional new image hash (TEXT_AD / TEXT_IMAGE_AD / MOBILE_APP_AD).
        clear_image_hash: Set AdImageHash to null to remove the image. Mutually
            exclusive with image_hash. Available for TEXT_AD / DYNAMIC_TEXT_AD /
            MOBILE_APP_AD; the CLI rejects it for image-ad subtypes (error 8000).
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
        from_file: Path to a JSONL file with ad-update objects (batch mode).
        ads_json: Inline JSON array of ad-update objects (batch mode).
        dry_run: Show the direct request without sending it.
    """
    if status is not None:
        return tool_error_dict(
            ToolError(
                error="status_not_updatable",
                message=(
                    "Ad status is not mutable via ads_update (WSDL AdUpdateItem has "
                    "no status field; direct-cli 0.4.2 rejects --status). Use "
                    "ads_suspend / ads_resume / ads_archive / ads_unarchive to "
                    "change an ad's status."
                ),
            )
        )

    if (from_file or ads_json) and id is not None:
        return tool_error_dict(
            ToolError(
                error="conflicting_modes",
                message=(
                    "id is for single-ad mode; in batch mode every row carries its "
                    "own id. Pass id OR from_file/ads_json, not both."
                ),
            )
        )

    result = run_batch_mutation(
        get_runner(),
        "ads",
        "update",
        from_file=from_file,
        json_arg=ads_json,
        json_flag="--ads-json",
        dry_run=dry_run,
    )
    if result is not None:
        return result

    if id is None:
        return tool_error_dict(
            ToolError(
                error="missing_mode",
                message=(
                    "Provide exactly one of: id (single ad), from_file (JSONL), "
                    "or ads_json (inline JSON array)."
                ),
            )
        )

    if image_hash and clear_image_hash:
        return tool_error_dict(
            ToolError(
                error="conflicting_image_hash",
                message="Use either image_hash or clear_image_hash, not both.",
            )
        )

    if not any(
        (
            title,
            text,
            titles,
            texts,
            href,
            image_hash,
            clear_image_hash,
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
        return tool_error_dict(
            ToolError(
                error="missing_update_fields",
                message=(
                    "Provide at least one typed update field, for example: title, "
                    "text, href, image_hash, clear_image_hash, tracking_url, "
                    "action, age_label, title2, display_url_path, mobile, vcard_id, "
                    "sitelink_set_id, turbo_page_id, ad_extensions, "
                    "callouts_*, video_extension_*, price_extension_*, business_id, "
                    "creative_id, final_url, tracking_pixels, "
                    "feed_filter_conditions, title_sources, text_sources, or "
                    "default_texts."
                ),
            )
        )
    if mobile is not None:
        err = validate_yes_no(mobile, field="mobile", error="invalid_mobile")
        if err is not None:
            return tool_error_dict(err)

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
    if clear_image_hash:
        args.append("--clear-image-hash")
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


@mcp.tool(
    description="Permanently delete ads by ID (max 10). Call tool_help('ads_delete') for parameters.",
)
@handle_cli_errors
def ads_delete(ids: str, dry_run: bool = False) -> dict:
    """Delete ads.

    Args:
        ids: Comma-separated ad IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "ads", "delete", ids, dry_run=dry_run)


@mcp.tool(
    description="Submit ads for moderation by ID (max 10). Call tool_help('ads_moderate') for parameters.",
)
@handle_cli_errors
def ads_moderate(ids: str, dry_run: bool = False) -> dict:
    """Submit ads for moderation.

    Args:
        ids: Comma-separated ad IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "ads", "moderate", ids, dry_run=dry_run)


@mcp.tool(
    description="Suspend (pause) serving ads by ID (max 10); reverse with ads_resume. Call tool_help('ads_suspend') for parameters.",
)
@handle_cli_errors
def ads_suspend(ids: str, dry_run: bool = False) -> dict:
    """Suspend ads.

    Args:
        ids: Comma-separated ad IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "ads", "suspend", ids, dry_run=dry_run)


@mcp.tool(
    description="Resume previously suspended ads by ID (max 10). Call tool_help('ads_resume') for parameters.",
)
@handle_cli_errors
def ads_resume(ids: str, dry_run: bool = False) -> dict:
    """Resume suspended ads.

    Args:
        ids: Comma-separated ad IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "ads", "resume", ids, dry_run=dry_run)


@mcp.tool(
    description="Archive ads by ID (max 10); reverse with ads_unarchive. Call tool_help('ads_archive') for parameters.",
)
@handle_cli_errors
def ads_archive(ids: str, dry_run: bool = False) -> dict:
    """Archive ads.

    Args:
        ids: Comma-separated ad IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "ads", "archive", ids, dry_run=dry_run)


@mcp.tool(
    description="Unarchive previously archived ads by ID (max 10). Call tool_help('ads_unarchive') for parameters.",
)
@handle_cli_errors
def ads_unarchive(ids: str, dry_run: bool = False) -> dict:
    """Unarchive ads.

    Args:
        ids: Comma-separated ad IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "ads", "unarchive", ids, dry_run=dry_run)
