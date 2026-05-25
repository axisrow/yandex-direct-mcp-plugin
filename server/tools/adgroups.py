"""MCP tools for ad group management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import CliOption, append_cli_options, check_batch_limit

MAX_BATCH_SIZE = 10

ADGROUP_EXTRA_OPTIONS = (
    CliOption("autotargeting_categories", "--autotargeting-category", repeat=True),
    CliOption("autotargeting_settings_exact", "--autotargeting-settings-exact"),
    CliOption("autotargeting_settings_narrow", "--autotargeting-settings-narrow"),
    CliOption(
        "autotargeting_settings_alternative",
        "--autotargeting-settings-alternative",
    ),
    CliOption("autotargeting_settings_accessory", "--autotargeting-settings-accessory"),
    CliOption("autotargeting_settings_broader", "--autotargeting-settings-broader"),
    CliOption(
        "autotargeting_settings_without_brands",
        "--autotargeting-settings-without-brands",
    ),
    CliOption(
        "autotargeting_settings_with_advertiser_brand",
        "--autotargeting-settings-with-advertiser-brand",
    ),
    CliOption(
        "autotargeting_settings_with_competitors_brand",
        "--autotargeting-settings-with-competitors-brand",
    ),
    CliOption("feed_category_ids", "--feed-category-ids"),
    CliOption("offer_retargeting", "--offer-retargeting"),
    CliOption("store_url", "--store-url"),
    CliOption("target_device_types", "--target-device-types"),
    CliOption("target_carrier", "--target-carrier"),
    CliOption("target_operating_system_version", "--target-operating-system-version"),
    CliOption("negative_keywords", "--negative-keywords"),
    CliOption("negative_keyword_shared_set_ids", "--negative-keyword-shared-set-ids"),
    CliOption("tracking_params", "--tracking-params"),
)


def _check_batch_limit(ids_str: str) -> ToolError | None:
    """Validate batch size of comma-separated IDs."""
    return check_batch_limit(ids_str, MAX_BATCH_SIZE)


@mcp.tool(name="adgroups_get")
@handle_cli_errors
def adgroups_list(
    campaign_ids: str | None = None,
    ids: str | None = None,
    status: str | None = None,
    statuses: str | None = None,
    types: str | None = None,
    tag_ids: str | None = None,
    tags: str | None = None,
    app_icon_statuses: str | None = None,
    serving_statuses: str | None = None,
    negative_keyword_shared_set_ids: str | None = None,
    limit: int | None = None,
    fetch_all: bool = False,
    fields: str | None = None,
) -> list[dict] | dict:
    """List ad groups.

    Args:
        campaign_ids: Comma-separated campaign IDs (max 10).
        ids: Comma-separated ad group IDs (max 10).
        status: Filter by a single status.
        statuses: Comma-separated statuses.
        types: Comma-separated ad group types.
        tag_ids: Comma-separated tag IDs.
        tags: Comma-separated tag names.
        app_icon_statuses: Comma-separated app icon statuses.
        serving_statuses: Comma-separated serving statuses.
        negative_keyword_shared_set_ids: Comma-separated negative keyword shared set IDs.
        limit: Limit number of results.
        fetch_all: Fetch all pages.
        fields: Comma-separated field names.
    """
    args = ["adgroups", "get", "--format", "json"]
    normalized_campaign_ids = campaign_ids.strip() if campaign_ids is not None else None
    if normalized_campaign_ids:
        batch_error = _check_batch_limit(normalized_campaign_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--campaign-ids", normalized_campaign_ids])
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        batch_error = _check_batch_limit(normalized_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--ids", normalized_ids])
    if status is not None:
        args.extend(["--status", status])
    if statuses is not None:
        args.extend(["--statuses", statuses])
    if types is not None:
        args.extend(["--types", types])
    if tag_ids is not None:
        args.extend(["--tag-ids", tag_ids])
    if tags is not None:
        args.extend(["--tags", tags])
    if app_icon_statuses is not None:
        args.extend(["--app-icon-statuses", app_icon_statuses])
    if serving_statuses is not None:
        args.extend(["--serving-statuses", serving_statuses])
    if negative_keyword_shared_set_ids is not None:
        args.extend(
            ["--negative-keyword-shared-set-ids", negative_keyword_shared_set_ids]
        )
    if limit is not None:
        args.extend(["--limit", str(limit)])
    if fetch_all:
        args.append("--fetch-all")
    if fields is not None:
        args.extend(["--fields", fields])

    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def adgroups_add(
    campaign_id: int,
    name: str,
    type: str | None = None,
    region_ids: str | None = None,
    domain_url: str | None = None,
    feed_id: int | None = None,
    feed_category_ids: str | None = None,
    ad_title_source: str | None = None,
    ad_body_source: str | None = None,
    autotargeting_categories: list[str] | None = None,
    autotargeting_settings_exact: str | None = None,
    autotargeting_settings_narrow: str | None = None,
    autotargeting_settings_alternative: str | None = None,
    autotargeting_settings_accessory: str | None = None,
    autotargeting_settings_broader: str | None = None,
    autotargeting_settings_without_brands: str | None = None,
    autotargeting_settings_with_advertiser_brand: str | None = None,
    autotargeting_settings_with_competitors_brand: str | None = None,
    offer_retargeting: str | None = None,
    store_url: str | None = None,
    target_device_types: str | None = None,
    target_carrier: str | None = None,
    target_operating_system_version: str | None = None,
    negative_keywords: str | None = None,
    negative_keyword_shared_set_ids: str | None = None,
    tracking_params: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Create a new ad group.

    CLI 0.3.8 dropped the free-form --json flag; only the typed flags listed
    below are accepted.

    Args:
        campaign_id: Campaign ID to add the ad group to.
        name: Ad group name.
        type: Ad group type (TEXT_AD_GROUP, DYNAMIC_TEXT_AD_GROUP, etc.).
        region_ids: Comma-separated region IDs for targeting.
        domain_url: Domain URL for DYNAMIC_TEXT_AD_GROUP.
        feed_id: Feed ID for SMART_AD_GROUP.
        feed_category_ids: Comma-separated feed category IDs.
        ad_title_source: Title source for SMART_AD_GROUP.
        ad_body_source: Body source for SMART_AD_GROUP.
        autotargeting_categories: Repeated autotargeting category specs.
        autotargeting_settings_*: Autotargeting setting values.
        offer_retargeting: Offer retargeting setting.
        store_url: Mobile app store URL.
        target_device_types: Mobile app target device types.
        target_carrier: Mobile app target carrier.
        target_operating_system_version: Mobile app target OS version.
        negative_keywords: Ad group negative keyword specs.
        negative_keyword_shared_set_ids: Negative keyword shared set IDs.
        tracking_params: Tracking parameter specs.
        dry_run: Show the direct request without sending it.
    """
    args = [
        "adgroups",
        "add",
        "--campaign-id",
        str(campaign_id),
        "--name",
        name,
    ]
    if type is not None:
        args.extend(["--type", type])
    if region_ids is not None:
        args.extend(["--region-ids", region_ids])
    if domain_url is not None:
        args.extend(["--domain-url", domain_url])
    if feed_id is not None:
        args.extend(["--feed-id", str(feed_id)])
    if ad_title_source is not None:
        args.extend(["--ad-title-source", ad_title_source])
    if ad_body_source is not None:
        args.extend(["--ad-body-source", ad_body_source])
    append_cli_options(args, locals(), ADGROUP_EXTRA_OPTIONS)
    if dry_run:
        args.append("--dry-run")
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def adgroups_update(
    id: int,
    name: str | None = None,
    status: str | None = None,
    region_ids: str | None = None,
    domain_url: str | None = None,
    dynamic_feed: str | None = None,
    negative_keywords: str | None = None,
    negative_keyword_shared_set_ids: str | None = None,
    tracking_params: str | None = None,
    feed_id: int | None = None,
    feed_category_ids: str | None = None,
    ad_title_source: str | None = None,
    ad_body_source: str | None = None,
    offer_retargeting: str | None = None,
    target_device_types: str | None = None,
    target_carrier: str | None = None,
    target_operating_system_version: str | None = None,
    autotargeting_categories: list[str] | None = None,
    autotargeting_settings_exact: str | None = None,
    autotargeting_settings_narrow: str | None = None,
    autotargeting_settings_alternative: str | None = None,
    autotargeting_settings_accessory: str | None = None,
    autotargeting_settings_broader: str | None = None,
    autotargeting_settings_without_brands: str | None = None,
    autotargeting_settings_with_advertiser_brand: str | None = None,
    autotargeting_settings_with_competitors_brand: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Update an ad group.

    CLI 0.3.8 dropped the free-form --json flag; only the typed flags listed
    below are accepted.

    Args:
        id: Ad group ID to update.
        name: New name for the ad group.
        status: New status.
        region_ids: Comma-separated region IDs for targeting.
        dry_run: Show the direct request without sending it.
    """
    values = locals()
    if not any(value for key, value in values.items() if key not in {"id", "dry_run"}):
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one typed ad group field to update.",
        ).__dict__

    args = ["adgroups", "update", "--id", str(id)]
    if name is not None:
        args.extend(["--name", name])
    if status is not None:
        args.extend(["--status", status])
    if region_ids is not None:
        args.extend(["--region-ids", region_ids])
    if domain_url is not None:
        args.extend(["--domain-url", domain_url])
    if dynamic_feed is not None:
        args.extend(["--dynamic-feed", dynamic_feed])
    if feed_id is not None:
        args.extend(["--feed-id", str(feed_id)])
    if ad_title_source is not None:
        args.extend(["--ad-title-source", ad_title_source])
    if ad_body_source is not None:
        args.extend(["--ad-body-source", ad_body_source])
    append_cli_options(args, values, ADGROUP_EXTRA_OPTIONS)
    if dry_run:
        args.append("--dry-run")
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def adgroups_delete(ids: str, dry_run: bool = False) -> dict:
    """Delete ad groups.

    Args:
        ids: Comma-separated ad group IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "adgroups", "delete", ids, dry_run=dry_run)
