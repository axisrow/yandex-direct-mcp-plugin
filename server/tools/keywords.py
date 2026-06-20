"""MCP tools for keyword management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import (
    CliOption,
    append_cli_options,
    require_update_fields,
    tool_error_dict,
)

KEYWORD_AUTOTARGETING_OPTIONS = (
    CliOption("autotargeting_categories", "--autotargeting-category", repeat=True),
    CliOption(
        "autotargeting_brand_options", "--autotargeting-brand-option", repeat=True
    ),
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
)


@mcp.tool(
    name="keywords_get",
    description="List keywords filtered by campaign, ad group, or keyword IDs. Call tool_help('keywords_get') for parameters.",
)
@handle_cli_errors
def keywords_list(
    campaign_ids: str | None = None,
    ids: str | None = None,
    ad_group_ids: str | None = None,
    status: str | None = None,
    statuses: str | None = None,
    states: str | None = None,
    modified_since: str | None = None,
    serving_statuses: str | None = None,
    limit: int | None = None,
    fetch_all: bool = False,
    fields: str | None = None,
) -> list[dict] | dict:
    """List keywords.

    Limits: CampaignIds≤10, AdGroupIds≤1000;
    Ids unlimited. Enforced by direct-cli 0.4.3 (#571).

    Args:
        campaign_ids: Comma-separated campaign IDs.
        ids: Comma-separated keyword IDs.
        ad_group_ids: Comma-separated ad group IDs.
        status: Filter by a single status.
        statuses: Comma-separated statuses.
        states: Comma-separated states.
        modified_since: ModifiedSince datetime in CLI-accepted form.
        serving_statuses: Comma-separated serving statuses.
        limit: Limit number of results.
        fetch_all: Fetch all pages.
        fields: Comma-separated field names.
    """
    args = ["keywords", "get", "--format", "json"]
    has_selector = False
    for value, flag in (
        (campaign_ids, "--campaign-ids"),
        (ids, "--ids"),
        (ad_group_ids, "--adgroup-ids"),
    ):
        if value is None:
            continue
        normalized = value.strip()
        if not normalized:
            continue
        args.extend([flag, normalized])
        has_selector = True

    if not has_selector and not fetch_all:
        return tool_error_dict(
            ToolError(
                error="missing_selector",
                message=(
                    "Provide at least one of: campaign_ids, ids, ad_group_ids. "
                    "To list every keyword in the account, pass fetch_all=True explicitly."
                ),
            )
        )
    if status is not None:
        args.extend(["--status", status])
    if statuses is not None:
        args.extend(["--statuses", statuses])
    if states is not None:
        args.extend(["--states", states])
    if modified_since is not None:
        args.extend(["--modified-since", modified_since])
    if serving_statuses is not None:
        args.extend(["--serving-statuses", serving_statuses])
    if limit is not None:
        args.extend(["--limit", str(limit)])
    if fetch_all:
        args.append("--fetch-all")
    if fields is not None:
        args.extend(["--fields", fields])

    return get_runner().run_json(args)


@mcp.tool(
    description="Update keyword text or user params; use keywordbids_set for bids and keywords_suspend/resume for status. Call tool_help('keywords_update') for parameters.",
)
@handle_cli_errors
def keywords_update(
    id: int,
    keyword: str | None = None,
    user_param_1: str | None = None,
    user_param_2: str | None = None,
    autotargeting_categories: list[str] | None = None,
    autotargeting_brand_options: list[str] | None = None,
    autotargeting_settings_exact: str | None = None,
    autotargeting_settings_narrow: str | None = None,
    autotargeting_settings_alternative: str | None = None,
    autotargeting_settings_accessory: str | None = None,
    autotargeting_settings_broader: str | None = None,
    autotargeting_settings_without_brands: str | None = None,
    autotargeting_settings_with_advertiser_brand: str | None = None,
    autotargeting_settings_with_competitors_brand: str | None = None,
    bid: int | None = None,
    context_bid: int | None = None,
    status: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Update keyword text, user params, or autotargeting projection fields.

    direct-cli 0.4.2 removed --bid/--context-bid/--status from
    `keywords update`. Bids are now managed exclusively via `keywordbids_set`
    (KeywordId-scoped) or `bids_set`; keyword status is changed via
    `keywords_suspend` / `keywords_resume`. The bid/context_bid/status
    parameters below are kept only to return a clear redirect error if passed.

    Args:
        id: Keyword ID.
        keyword: Optional new keyword text.
        user_param_1: Optional user parameter 1.
        user_param_2: Optional user parameter 2.
        autotargeting_categories: Repeated autotargeting category specs.
        autotargeting_brand_options: Repeated autotargeting brand option specs.
        autotargeting_settings_*: Autotargeting setting values.
        bid: Deprecated — use keywordbids_set/bids_set (returns an error).
        context_bid: Deprecated — use keywordbids_set/bids_set (returns an error).
        status: Deprecated — use keywords_suspend/keywords_resume (returns an error).
        dry_run: Show the direct request without sending it.
    """
    if bid is not None or context_bid is not None:
        return tool_error_dict(
            ToolError(
                error="bid_not_updatable_here",
                message=(
                    "Keyword bids are not mutable via keywords_update (direct-cli "
                    "0.4.2 removed --bid/--context-bid). Use keywordbids_set "
                    "(KeywordId-scoped) or bids_set instead."
                ),
            )
        )
    if status is not None:
        return tool_error_dict(
            ToolError(
                error="status_not_updatable",
                message=(
                    "Keyword status is not mutable via the Keywords API (direct-cli "
                    "0.4.2 removed --status). Use keywords_suspend / keywords_resume "
                    "to pause or resume keywords."
                ),
            )
        )

    values = locals()
    fields_error = require_update_fields(
        values,
        message="Provide at least one typed keyword field to update.",
        exclude={"id", "dry_run"},
    )
    if fields_error:
        return tool_error_dict(fields_error)

    runner = get_runner()
    args = ["keywords", "update", "--id", str(id)]
    if keyword is not None:
        args.extend(["--keyword", keyword])
    if user_param_1 is not None:
        args.extend(["--user-param-1", user_param_1])
    if user_param_2 is not None:
        args.extend(["--user-param-2", user_param_2])
    append_cli_options(args, values, KEYWORD_AUTOTARGETING_OPTIONS)
    if dry_run:
        args.append("--dry-run")
    cli_output = runner.run_json(args)

    if dry_run:
        return {
            "dry_run": True,
            "command": ["direct", *args],
            "request_body": cli_output,
        }
    result: dict[str, object] = {"success": True, "id": id}
    if keyword is not None:
        result["keyword"] = keyword
    if user_param_1 is not None:
        result["user_param_1"] = user_param_1
    if user_param_2 is not None:
        result["user_param_2"] = user_param_2
    return result


@mcp.tool(
    description="Add one or many keywords to an ad group (single, JSONL file, or inline JSON). Call tool_help('keywords_add') for parameters.",
)
@handle_cli_errors
def keywords_add(
    ad_group_id: int | None = None,
    keyword: str | None = None,
    bid: int | None = None,
    context_bid: int | None = None,
    autotargeting_search_bid_is_auto: str | None = None,
    priority: str | None = None,
    autotargeting_categories: list[str] | None = None,
    autotargeting_brand_options: list[str] | None = None,
    autotargeting_settings_exact: str | None = None,
    autotargeting_settings_narrow: str | None = None,
    autotargeting_settings_alternative: str | None = None,
    autotargeting_settings_accessory: str | None = None,
    autotargeting_settings_broader: str | None = None,
    autotargeting_settings_without_brands: str | None = None,
    autotargeting_settings_with_advertiser_brand: str | None = None,
    autotargeting_settings_with_competitors_brand: str | None = None,
    user_param_1: str | None = None,
    user_param_2: str | None = None,
    from_file: str | None = None,
    keywords_json: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Add one or many keywords to an ad group.

    Three mutually exclusive modes (CLI 0.3.9):

    1. Single: ad_group_id + keyword (+ optional bid / context_bid / user_params).
    2. JSONL batch: from_file = path to a .jsonl file, one keyword object per line.
       Per-line schema uses WSDL CamelCase: required keys are "Keyword" and
       "AdGroupId" unless a top-level ad_group_id default is provided. Optional
       keys are "Bid" (micro-RUB), "ContextBid" (micro-RUB), "UserParam1", and
       "UserParam2". Per-line AdGroupId overrides the top-level ad_group_id
       default.
    3. Inline JSON: keywords_json = a JSON array of the same objects.

    `Bid` and `ContextBid` are documented Yandex Direct `Keywords.add`
    fields, but they are strategy-dependent: `Bid` is only for manual
    strategies, and `ContextBid` is only for manual strategies with
    independent ad-network bid management. For automatic strategies, Yandex
    ignores these values and returns warning 10160; do not set them in
    auto-strategy / RSYA (РСЯ) JSONL or inline JSON inputs.

    CLI 0.3.9 forwards the array as a single Yandex Direct API request (up to
    1000 keywords per call).

    Args:
        ad_group_id: Ad group ID. Required in single mode; optional default
            in batch modes (each row's AdGroupId wins).
        keyword: Keyword text (single mode only).
        bid: Optional search bid in micro-units (RUB × 1,000,000); CLI 0.2.10+
            rejects values 0 < x < 100_000 with a "did you mean × 1_000_000" hint.
        context_bid: Optional context bid in micro-units (same rules as `bid`).
        user_param_1: Optional user parameter 1.
        user_param_2: Optional user parameter 2.
        from_file: Path to a JSONL file with keyword objects (batch mode).
        keywords_json: Inline JSON array of keyword objects (batch mode).
        dry_run: Show the direct request without sending it.
    """
    modes = (bool(keyword), bool(from_file), bool(keywords_json))
    mode_count = sum(modes)
    if mode_count == 0:
        return tool_error_dict(
            ToolError(
                error="missing_mode",
                message=(
                    "Provide exactly one of: keyword (single), from_file (JSONL), "
                    "or keywords_json (inline JSON array)."
                ),
            )
        )
    if mode_count > 1:
        return tool_error_dict(
            ToolError(
                error="conflicting_modes",
                message=(
                    "keyword, from_file and keywords_json are mutually exclusive — "
                    "pass exactly one."
                ),
            )
        )

    args = ["keywords", "add"]
    if ad_group_id is not None:
        args.extend(["--adgroup-id", str(ad_group_id)])
    if keyword:
        args.extend(["--keyword", keyword])
    if from_file:
        args.extend(["--from-file", from_file])
    if keywords_json:
        args.extend(["--keywords-json", keywords_json])
    if bid is not None:
        args.extend(["--bid", str(bid)])
    if context_bid is not None:
        args.extend(["--context-bid", str(context_bid)])
    if autotargeting_search_bid_is_auto is not None:
        args.extend(
            [
                "--autotargeting-search-bid-is-auto",
                autotargeting_search_bid_is_auto,
            ]
        )
    if priority is not None:
        args.extend(["--priority", priority])
    append_cli_options(args, locals(), KEYWORD_AUTOTARGETING_OPTIONS)
    if user_param_1 is not None:
        args.extend(["--user-param-1", user_param_1])
    if user_param_2 is not None:
        args.extend(["--user-param-2", user_param_2])
    if dry_run:
        args.append("--dry-run")
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(
    description="Delete keywords by ID. Call tool_help('keywords_delete') for parameters.",
)
@handle_cli_errors
def keywords_delete(ids: str, dry_run: bool = False) -> dict:
    """Delete keywords.

    Args:
        ids: Comma-separated keyword IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "keywords", "delete", ids, dry_run=dry_run)


@mcp.tool(
    description="Suspend keywords by ID. Call tool_help('keywords_suspend') for parameters.",
)
@handle_cli_errors
def keywords_suspend(ids: str, dry_run: bool = False) -> dict:
    """Suspend keywords.

    Args:
        ids: Comma-separated keyword IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(
        get_runner(), "keywords", "suspend", ids, dry_run=dry_run
    )


@mcp.tool(
    description="Resume suspended keywords by ID. Call tool_help('keywords_resume') for parameters.",
)
@handle_cli_errors
def keywords_resume(ids: str, dry_run: bool = False) -> dict:
    """Resume suspended keywords.

    Args:
        ids: Comma-separated keyword IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "keywords", "resume", ids, dry_run=dry_run)
