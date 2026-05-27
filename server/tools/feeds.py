"""MCP tools for feed management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import CliOption, append_cli_options, provided_update_value

BUSINESS_TYPES = ("RETAIL", "HOTELS", "REALTY", "AUTOMOBILES", "FLIGHTS", "OTHER")

FEED_SOURCE_OPTIONS = (
    CliOption("file_feed_path", "--file-feed-path"),
    CliOption("file_feed_filename", "--file-feed-filename"),
    CliOption("remove_utm_tags", "--remove-utm-tags"),
    CliOption("feed_login", "--feed-login"),
    CliOption("feed_password", "--feed-password"),
)


@mcp.tool(name="feeds_get")
@handle_cli_errors
def feeds_list(
    ids: str | None = None,
    limit: int | None = None,
    fetch_all: bool = False,
    fields: str | None = None,
) -> dict:
    """List feeds.

    Args:
        ids: Comma-separated feed IDs (omit for all feeds).
        limit: Limit number of results.
        fetch_all: Fetch all pages.
        fields: Comma-separated field names.
    """
    args = ["feeds", "get", "--format", "json"]
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        args.extend(["--ids", normalized_ids])
    if limit is not None:
        args.extend(["--limit", str(limit)])
    if fetch_all:
        args.append("--fetch-all")
    if fields is not None:
        args.extend(["--fields", fields])
    return get_runner().run_json(args)


@mcp.tool()
@handle_cli_errors
def feeds_add(
    name: str,
    business_type: str,
    url: str | None = None,
    file_feed_path: str | None = None,
    file_feed_filename: str | None = None,
    remove_utm_tags: str | None = None,
    feed_login: str | None = None,
    feed_password: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Add a new feed.

    CLI 0.3.12 supports URL feeds and file-feed uploads through typed flags.
    Provide `url` for a UrlFeed source, or `file_feed_path` plus optional
    `file_feed_filename` for a FileFeed upload.

    Args:
        name: Feed name.
        business_type: Business type — one of RETAIL, HOTELS, REALTY,
            AUTOMOBILES, FLIGHTS, OTHER.
        url: Feed URL for UrlFeed.
        file_feed_path: Local file path to upload for FileFeed.
        file_feed_filename: Optional uploaded file name override.
        remove_utm_tags: Optional remove-UTM setting.
        feed_login: Optional feed basic-auth login.
        feed_password: Optional feed basic-auth password.
        dry_run: Show the direct request without sending it.
    """
    if business_type not in BUSINESS_TYPES:
        return ToolError(
            error="invalid_business_type",
            message=(
                f"business_type must be one of {', '.join(BUSINESS_TYPES)}; "
                f"got '{business_type}'"
            ),
        ).__dict__

    args = [
        "feeds",
        "add",
        "--name",
        name,
    ]
    if url is not None:
        args.extend(["--url", url])
    append_cli_options(args, locals(), FEED_SOURCE_OPTIONS)
    args.extend(["--business-type", business_type])
    if dry_run:
        args.append("--dry-run")
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def feeds_update(
    id: int,
    name: str | None = None,
    url: str | None = None,
    file_feed_path: str | None = None,
    file_feed_filename: str | None = None,
    remove_utm_tags: str | None = None,
    feed_login: str | None = None,
    feed_password: str | None = None,
    clear_feed_login: bool = False,
    clear_feed_password: bool = False,
    dry_run: bool = False,
) -> dict:
    """Update an existing feed.

    CLI 0.3.8 removed the free-form --json flag from `feeds update`.

    Args:
        id: Feed ID to update.
        name: Optional new feed name.
        url: Optional new feed URL.
        dry_run: Show the direct request without sending it.
    """
    values = locals()
    if not any(
        provided_update_value(value)
        for key, value in values.items()
        if key not in {"id", "dry_run"}
    ):
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one typed feed field to update.",
        ).__dict__

    args = ["feeds", "update", "--id", str(id)]
    if name is not None:
        args.extend(["--name", name])
    if url is not None:
        args.extend(["--url", url])
    append_cli_options(args, values, FEED_SOURCE_OPTIONS)
    if clear_feed_login:
        args.append("--clear-feed-login")
    if clear_feed_password:
        args.append("--clear-feed-password")
    if dry_run:
        args.append("--dry-run")
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def feeds_delete(ids: str, dry_run: bool = False) -> dict:
    """Delete feeds.

    Args:
        ids: Comma-separated feed IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "feeds", "delete", ids, dry_run=dry_run)
