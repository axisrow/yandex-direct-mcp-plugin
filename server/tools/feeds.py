"""MCP tools for feed management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors

BUSINESS_TYPES = ("RETAIL", "HOTELS", "REALTY", "AUTOMOBILES", "FLIGHTS", "OTHER")


@mcp.tool(name="feeds_get")
@handle_cli_errors
def feeds_list(ids: str | None = None) -> dict:
    """List feeds.

    Args:
        ids: Comma-separated feed IDs (optional, omit for all feeds).
    """
    args = ["feeds", "get", "--format", "json"]
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        args.extend(["--ids", normalized_ids])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def feeds_add(
    name: str,
    url: str,
    business_type: str,
    dry_run: bool = False,
) -> dict:
    """Add a new feed.

    CLI 0.3.8 requires --business-type (WSDL FeedAddItem.BusinessType,
    minOccurs=1) and removed the free-form --json flag.

    Args:
        name: Feed name.
        url: Feed URL.
        business_type: Business type — one of RETAIL, HOTELS, REALTY,
            AUTOMOBILES, FLIGHTS, OTHER.
        dry_run: Show the direct-cli request without sending it.
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
        "--url",
        url,
        "--business-type",
        business_type,
    ]
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
    dry_run: bool = False,
) -> dict:
    """Update an existing feed.

    CLI 0.3.8 removed the free-form --json flag from `feeds update`.

    Args:
        id: Feed ID to update.
        name: Optional new feed name.
        url: Optional new feed URL.
        dry_run: Show the direct-cli request without sending it.
    """
    if not any((name, url)):
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one of: name, url",
        ).__dict__

    args = ["feeds", "update", "--id", str(id)]
    if name is not None:
        args.extend(["--name", name])
    if url is not None:
        args.extend(["--url", url])
    if dry_run:
        args.append("--dry-run")
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def feeds_delete(ids: str) -> dict:
    """Delete feeds.

    Args:
        ids: Comma-separated feed IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "feeds", "delete", ids)
