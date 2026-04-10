"""MCP tools for vCard management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit, run_single_id_batch


@mcp.tool()
@handle_cli_errors
def vcards_list(ids: str | None = None) -> list[dict] | dict:
    """List vCards.

    Args:
        ids: Comma-separated vCard IDs (optional, max 10).
    """
    cmd = ["vcards", "get", "--format", "json"]
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
def vcards_add(vcard_json: str) -> dict:
    """Add a vCard.

    Args:
        vcard_json: JSON string describing the vCard.
    """
    runner = get_runner()
    result = runner.run_json(["vcards", "add", "--json", vcard_json])
    return result


@mcp.tool()
@handle_cli_errors
def vcards_delete(ids: str) -> dict:
    """Delete vCards.

    Args:
        ids: Comma-separated vCard IDs (max 10).
    """
    return run_single_id_batch(get_runner(), "vcards", "delete", ids)
