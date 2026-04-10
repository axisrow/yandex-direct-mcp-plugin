"""MCP tools for feed management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors


@mcp.tool()
@handle_cli_errors
def feeds_list(ids: str) -> dict:
    """List feeds by IDs.

    Args:
        ids: Comma-separated feed IDs.
    """
    runner = get_runner()
    normalized_ids = ids.strip()
    return runner.run_json(
        ["feeds", "get", "--ids", normalized_ids, "--format", "json"]
    )


@mcp.tool()
@handle_cli_errors
def feeds_add(name: str, url: str, extra_json: str | None = None) -> dict:
    """Add a new feed.

    Args:
        name: Feed name.
        url: Feed URL.
        extra_json: JSON string with additional parameters (optional).
    """
    args = ["feeds", "add", "--name", name, "--url", url]
    if extra_json is not None:
        args.extend(["--json", extra_json])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def feeds_update(
    id: str,
    name: str | None = None,
    url: str | None = None,
    extra_json: str | None = None,
) -> dict:
    """Update an existing feed.

    Args:
        id: Feed ID to update.
        name: Optional new feed name.
        url: Optional new feed URL.
        extra_json: Optional JSON string with additional parameters.
    """
    if not any((name, url, extra_json)):
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one of: name, url, extra_json",
        ).__dict__

    args = ["feeds", "update", "--id", id]
    if name is not None:
        args.extend(["--name", name])
    if url is not None:
        args.extend(["--url", url])
    if extra_json is not None:
        args.extend(["--json", extra_json])
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
