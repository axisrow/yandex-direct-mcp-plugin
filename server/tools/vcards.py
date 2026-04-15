"""MCP tools for vCard management."""

import json

from server.main import mcp
from server.tools import get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit, run_single_id_batch


@mcp.tool(name="vcards_get")
@handle_cli_errors
def vcards_list(ids: str | None = None) -> list[dict] | dict:
    """List vCards.

    Args:
        ids: Comma-separated vCard IDs (optional, max 10).
    """
    cmd = ["vcards", "get", "--format", "json"]
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        batch_error = check_batch_limit(normalized_ids)
        if batch_error:
            return batch_error.__dict__
        cmd.extend(["--ids", normalized_ids])
    runner = get_runner()
    result = runner.run_json(cmd)
    return result


@mcp.tool()
@handle_cli_errors
def vcards_add(vcard_json: str | dict) -> dict:
    """Add a vCard.

    Args:
        vcard_json: JSON string describing the vCard.
    """
    runner = get_runner()
    json_str = json.dumps(vcard_json) if isinstance(vcard_json, dict) else vcard_json
    result = runner.run_json(["vcards", "add", "--json", json_str])
    return result


@mcp.tool()
@handle_cli_errors
def vcards_delete(ids: str) -> dict:
    """Delete vCards.

    Args:
        ids: Comma-separated vCard IDs (max 10).
    """
    return run_single_id_batch(get_runner(), "vcards", "delete", ids)
