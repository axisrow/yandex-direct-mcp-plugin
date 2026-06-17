"""MCP tools for ad group management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import (
    CliOption,
    append_cli_options,
    check_batch_limit,
    provided_update_value,
    run_batch_mutation,
    tool_error_dict,
)

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


@mcp.tool(
    name="adgroups_get",
    description="List ad groups filtered by campaign or ad group IDs, plus optional status/type filters. Read-only; use adgroups_add to create or adgroups_update to modify. Call tool_help('adgroups_get') for parameters.",
)
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
        campaign_ids: Comma-separated campaign IDs (≤10 per call, plugin cap).
        ids: Comma-separated ad group IDs (≤10 per call, plugin cap).
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
        batch_error = check_batch_limit(normalized_campaign_ids, MAX_BATCH_SIZE)
        if batch_error:
            return tool_error_dict(batch_error)
        args.extend(["--campaign-ids", normalized_campaign_ids])
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        batch_error = check_batch_limit(normalized_ids, MAX_BATCH_SIZE)
        if batch_error:
            return tool_error_dict(batch_error)
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


@mcp.tool(
    description="Create one or many ad groups — a single group in a campaign, or a batch via from_file/adgroups_json. Use adgroups_update to change an existing group. Call tool_help('adgroups_add') for parameters.",
)
@handle_cli_errors
def adgroups_add(
    campaign_id: int | None = None,
    name: str | None = None,
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
    from_file: str | None = None,
    adgroups_json: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Create one or many ad groups.

    Three mutually exclusive modes (CLI #564):

    1. Single: campaign_id + name (+ region_ids and typed fields).
    2. JSONL batch: from_file = path to a .jsonl file, one ad-group object per
       line. Per-row keys use the kebab CLI-flag form ("campaign-id", "name",
       "region-ids", "type", ...); "campaign-id", "name", "region-ids" are
       required per row, and campaign_id acts as the batch default.
    3. Inline JSON: adgroups_json = a JSON array of the same objects.

    In batch mode the rows are the source of truth; any single-item content
    field passed alongside from_file/adgroups_json is ignored.

    CLI 0.3.8 dropped the free-form --json flag; only the typed flags listed
    below are accepted. CLI #564 chunks the batch at 100 (API ceiling 1000).

    Args:
        campaign_id: Campaign ID. Required in single mode; optional default in
            batch modes (each row's campaign-id wins).
        name: Ad group name (single mode).
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
        from_file: Path to a JSONL file with ad-group objects (batch mode).
        adgroups_json: Inline JSON array of ad-group objects (batch mode).
        dry_run: Show the direct request without sending it.
    """
    result = run_batch_mutation(
        get_runner(),
        "adgroups",
        "add",
        from_file=from_file,
        json_arg=adgroups_json,
        json_flag="--adgroups-json",
        default_id_flag="--campaign-id",
        default_id=campaign_id,
        dry_run=dry_run,
    )
    if result is not None:
        return result

    if campaign_id is None or name is None:
        return tool_error_dict(
            ToolError(
                error="missing_mode",
                message=(
                    "Single mode requires campaign_id and name; otherwise use "
                    "from_file (JSONL) or adgroups_json (inline JSON array)."
                ),
            )
        )

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


@mcp.tool(
    description="Update one or many ad groups — a single group by id, or a batch via from_file/adgroups_json. Use adgroups_add to create. Call tool_help('adgroups_update') for parameters.",
)
@handle_cli_errors
def adgroups_update(
    id: int | None = None,
    name: str | None = None,
    status: str | None = None,
    region_ids: str | None = None,
    domain_url: str | None = None,
    dynamic_feed: bool = False,
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
    from_file: str | None = None,
    adgroups_json: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Update one or many ad groups.

    Three mutually exclusive modes (CLI #565):

    1. Single: id (+ at least one typed update field).
    2. JSONL batch: from_file = path to a .jsonl file, one ad-group-update
       object per line. Per-row keys use the kebab CLI-flag form ("id", "name",
       "status", ...); "id" is required per row.
    3. Inline JSON: adgroups_json = a JSON array of the same objects.

    In batch mode the rows are the source of truth; any single-item content
    field passed alongside from_file/adgroups_json is ignored.

    CLI 0.3.8 dropped the free-form --json flag; only the typed flags listed
    below are accepted. CLI #565 chunks the batch at 100 (API ceiling 1000).

    Args:
        id: Ad group ID to update (single mode).
        name: New name for the ad group.
        status: New status.
        region_ids: Comma-separated region IDs for targeting.
        from_file: Path to a JSONL file with ad-group-update objects (batch mode).
        adgroups_json: Inline JSON array of ad-group-update objects (batch mode).
        dry_run: Show the direct request without sending it.
    """
    if (from_file or adgroups_json) and id is not None:
        return tool_error_dict(
            ToolError(
                error="conflicting_modes",
                message=(
                    "id is for single-group mode; in batch mode every row carries "
                    "its own id. Pass id OR from_file/adgroups_json, not both."
                ),
            )
        )

    result = run_batch_mutation(
        get_runner(),
        "adgroups",
        "update",
        from_file=from_file,
        json_arg=adgroups_json,
        json_flag="--adgroups-json",
        dry_run=dry_run,
    )
    if result is not None:
        return result

    if id is None:
        return tool_error_dict(
            ToolError(
                error="missing_mode",
                message=(
                    "Provide exactly one of: id (single group), from_file (JSONL), "
                    "or adgroups_json (inline JSON array)."
                ),
            )
        )

    values = locals()
    if not any(
        provided_update_value(value)
        for key, value in values.items()
        if key
        not in {"id", "dry_run", "from_file", "adgroups_json", "handled", "result"}
    ):
        return tool_error_dict(
            ToolError(
                error="missing_update_fields",
                message="Provide at least one typed ad group field to update.",
            )
        )

    args = ["adgroups", "update", "--id", str(id)]
    if name is not None:
        args.extend(["--name", name])
    if status is not None:
        args.extend(["--status", status])
    if region_ids is not None:
        args.extend(["--region-ids", region_ids])
    if domain_url is not None:
        args.extend(["--domain-url", domain_url])
    if dynamic_feed:
        # CLI 0.4.2 defines --dynamic-feed as is_flag=True (no value); it builds
        # a DynamicTextFeedAdGroup update block for --autotargeting-category.
        args.append("--dynamic-feed")
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


@mcp.tool(
    description="Permanently delete ad groups by ID (max 10). Call tool_help('adgroups_delete') for parameters.",
)
@handle_cli_errors
def adgroups_delete(ids: str, dry_run: bool = False) -> dict:
    """Delete ad groups.

    Args:
        ids: Comma-separated ad group IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "adgroups", "delete", ids, dry_run=dry_run)
