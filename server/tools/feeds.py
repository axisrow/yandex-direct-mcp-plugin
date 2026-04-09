"""MCP tools for feed management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit


@mcp.tool()
@handle_cli_errors
def feeds_list(ids: str) -> dict:
    """List feeds by IDs.

    Args:
        ids: Comma-separated feed IDs.
    """
    runner = get_runner()
    return runner.run_json(["feeds", "get", "--ids", ids, "--format", "json"])


@mcp.tool()
@handle_cli_errors
def feeds_add(name: str, url: str) -> dict:
    """Add a new feed.

    Args:
        name: Feed name.
        url: Feed URL.
    """
    runner = get_runner()
    return runner.run_json(["feeds", "add", "--name", name, "--url", url, "--format", "json"])


@mcp.tool()
@handle_cli_errors
def feeds_update(id: str, name: str | None = None, url: str | None = None) -> dict:
    """Update an existing feed.

    Args:
        id: Feed ID to update.
        name: Optional new feed name.
        url: Optional new feed URL.
    """
    if name is None and url is None:
        return ToolError(
            error="nothing_to_update",
            message="At least one field (name, url) must be provided for update",
        ).__dict__

    runner = get_runner()
    args = [
        "feeds",
        "update",
        "--id",
        id,
        "--format",
        "json",
    ]
    if name is not None:
        args.extend(["--name", name])
    if url is not None:
        args.extend(["--url", url])
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def feeds_delete(ids: str) -> dict:
    """Delete feeds.

    Args:
        ids: Comma-separated feed IDs (max 10).
    """
    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    return runner.run_json(["feeds", "delete", "--ids", ids, "--format", "json"])
