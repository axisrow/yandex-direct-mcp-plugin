"""MCP tools for vCard management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors


@mcp.tool()
@handle_cli_errors
def vcards_list(ids: str) -> list[dict] | dict:
    """List vCards.

    Args:
        ids: Comma-separated vCard IDs (max 10).
    """
    from server.tools.helpers import check_batch_limit

    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(["vcards", "get", "--ids", ids, "--format", "json"])
    return result


@mcp.tool()
@handle_cli_errors
def vcards_add(vcard_data: str) -> dict:
    """Add a vCard.

    Args:
        vcard_data: JSON string describing the vCard.
    """
    runner = get_runner()
    result = runner.run_json(
        ["vcards", "add", "--data", vcard_data, "--format", "json"]
    )
    return result


@mcp.tool()
@handle_cli_errors
def vcards_delete(ids: str) -> dict:
    """Delete vCards.

    Args:
        ids: Comma-separated vCard IDs (max 10).
    """
    from server.tools.helpers import check_batch_limit

    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(["vcards", "delete", "--ids", ids, "--format", "json"])
    return result
