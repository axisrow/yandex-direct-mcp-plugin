"""MCP tools for keyword management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import CliOption, append_cli_options

MAX_BATCH_SIZE = 10

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


def _check_batch_limit(ids_str: str) -> ToolError | None:
    """Validate batch size of comma-separated IDs."""
    ids = [id.strip() for id in ids_str.split(",") if id.strip()]
    if len(ids) > MAX_BATCH_SIZE:
        return ToolError(
            error="batch_limit",
            message=f"Maximum {MAX_BATCH_SIZE} IDs per request. Got: {len(ids)}",
        )
    return None


@mcp.tool(name="keywords_get")
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

    Args:
        campaign_ids: Comma-separated campaign IDs (max 10).
        ids: Comma-separated keyword IDs (max 10).
        ad_group_ids: Comma-separated ad group IDs (max 10).
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
    for value, flag, batch in (
        (campaign_ids, "--campaign-ids", True),
        (ids, "--ids", True),
        (ad_group_ids, "--adgroup-ids", True),
    ):
        if value is None:
            continue
        normalized = value.strip()
        if not normalized:
            continue
        if batch:
            batch_error = _check_batch_limit(normalized)
            if batch_error:
                return batch_error.__dict__
        args.extend([flag, normalized])
        has_selector = True

    if not has_selector and not fetch_all:
        return ToolError(
            error="missing_selector",
            message=(
                "Provide at least one of: campaign_ids, ids, ad_group_ids. "
                "To list every keyword in the account, pass fetch_all=True explicitly."
            ),
        ).__dict__
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


@mcp.tool()
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
    bid: str | None = None,
    context_bid: str | None = None,
    status: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Update keyword text or user params.

    CLI 0.3.12 accepts typed bid, status, and autotargeting projection fields
    here. `keywordbids_set` remains the bulk bid-management tool, but this
    wrapper mirrors the `direct keywords update` flags for single keyword
    updates.

    Args:
        id: Keyword ID.
        keyword: Optional new keyword text.
        user_param_1: Optional user parameter 1.
        user_param_2: Optional user parameter 2.
        autotargeting_categories: Repeated autotargeting category specs.
        autotargeting_brand_options: Repeated autotargeting brand option specs.
        autotargeting_settings_*: Autotargeting setting values.
        bid: Optional search bid.
        context_bid: Optional context bid.
        status: Optional keyword status.
        dry_run: Show the direct request without sending it.
    """
    values = locals()
    if not any(value for key, value in values.items() if key not in {"id", "dry_run"}):
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one typed keyword field to update.",
        ).__dict__

    runner = get_runner()
    args = ["keywords", "update", "--id", str(id)]
    if keyword is not None:
        args.extend(["--keyword", keyword])
    if user_param_1 is not None:
        args.extend(["--user-param-1", user_param_1])
    if user_param_2 is not None:
        args.extend(["--user-param-2", user_param_2])
    append_cli_options(args, values, KEYWORD_AUTOTARGETING_OPTIONS)
    if bid is not None:
        args.extend(["--bid", bid])
    if context_bid is not None:
        args.extend(["--context-bid", context_bid])
    if status is not None:
        args.extend(["--status", status])
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


@mcp.tool()
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
       Per-line schema (WSDL CamelCase): {"AdGroupId": int, "Keyword": str,
       "Bid": int (micro-RUB), "ContextBid": int, "UserParam1": str,
       "UserParam2": str}. Per-line AdGroupId overrides the top-level
       ad_group_id default.
    3. Inline JSON: keywords_json = a JSON array of the same objects.

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
        return ToolError(
            error="missing_mode",
            message=(
                "Provide exactly one of: keyword (single), from_file (JSONL), "
                "or keywords_json (inline JSON array)."
            ),
        ).__dict__
    if mode_count > 1:
        return ToolError(
            error="conflicting_modes",
            message=(
                "keyword, from_file and keywords_json are mutually exclusive — "
                "pass exactly one."
            ),
        ).__dict__

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


@mcp.tool()
@handle_cli_errors
def keywords_delete(ids: str, dry_run: bool = False) -> dict:
    """Delete keywords.

    Args:
        ids: Comma-separated keyword IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "keywords", "delete", ids, dry_run=dry_run)


@mcp.tool()
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


@mcp.tool()
@handle_cli_errors
def keywords_resume(ids: str, dry_run: bool = False) -> dict:
    """Resume suspended keywords.

    Args:
        ids: Comma-separated keyword IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "keywords", "resume", ids, dry_run=dry_run)
