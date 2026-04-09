"""MCP tools for sitelinks management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors


@mcp.tool()
@handle_cli_errors
def sitelinks_list(ids: str) -> list[dict] | dict:
    """List sitelinks sets.

    Args:
        ids: Comma-separated sitelinks set IDs (max 10).
    """
    from server.tools.helpers import check_batch_limit

    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(["sitelinks", "get", "--ids", ids, "--format", "json"])
    return result


@mcp.tool()
@handle_cli_errors
def sitelinks_add(sitelinks_data: str) -> dict:
    """Add a sitelinks set.

    Args:
        sitelinks_data: JSON string describing the sitelinks set.
    """
    runner = get_runner()
    result = runner.run_json(
        ["sitelinks", "add", "--data", sitelinks_data, "--format", "json"]
    )
    return result


@mcp.tool()
@handle_cli_errors
def sitelinks_delete(ids: str) -> dict:
    """Delete sitelinks sets.

    Args:
        ids: Comma-separated sitelinks set IDs (max 10).
    """
    from server.tools.helpers import check_batch_limit

    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(["sitelinks", "delete", "--ids", ids, "--format", "json"])
    return result
