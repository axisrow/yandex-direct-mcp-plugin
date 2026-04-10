"""MCP tools for sitelinks management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit, run_single_id_batch


@mcp.tool()
@handle_cli_errors
def sitelinks_list(ids: str | None = None) -> list[dict] | dict:
    """List sitelinks sets.

    Args:
        ids: Comma-separated sitelinks set IDs (optional, max 10).
    """
    cmd = ["sitelinks", "get", "--format", "json"]
    if ids is not None:
        batch_error = check_batch_limit(ids)
        if batch_error:
            return batch_error.__dict__
        cmd.extend(["--ids", ids])
    runner = get_runner()
    result = runner.run_json(cmd)
    return result


@mcp.tool()
@handle_cli_errors
def sitelinks_add(links: str) -> dict:
    """Add a sitelinks set.

    Args:
        links: JSON array of sitelink objects.
            Example: '[{"Title":"About","Href":"https://example.com/about"}]'
    """
    runner = get_runner()
    result = runner.run_json(["sitelinks", "add", "--links", links])
    return result


@mcp.tool()
@handle_cli_errors
def sitelinks_delete(ids: str) -> dict:
    """Delete sitelinks sets.

    Args:
        ids: Comma-separated sitelinks set IDs (max 10).
    """
    return run_single_id_batch(get_runner(), "sitelinks", "delete", ids)
