"""MCP tools for ad extensions management."""

import json

from server.main import mcp
from server.tools import get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit, run_single_id_batch


@mcp.tool()
@handle_cli_errors
def adextensions_list(
    ids: str | None = None, types: str | None = None
) -> list[dict] | dict:
    """List ad extensions.

    Args:
        ids: Comma-separated extension IDs (optional).
        types: Comma-separated extension types to filter (optional).
    """
    cmd = ["adextensions", "get", "--format", "json"]
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        batch_error = check_batch_limit(normalized_ids)
        if batch_error:
            return batch_error.__dict__
        cmd.extend(["--ids", normalized_ids])
    normalized_types = types.strip() if types is not None else None
    if normalized_types:
        cmd.extend(["--types", normalized_types])
    runner = get_runner()
    result = runner.run_json(cmd)
    return result


@mcp.tool()
@handle_cli_errors
def adextensions_add(extension_type: str, extra_json: str | dict) -> dict:
    """Add an ad extension.

    Args:
        extension_type: Type of extension (e.g., "CALLOUT", "SITELINK").
        extra_json: JSON string describing the extension content.
    """
    runner = get_runner()
    json_str = json.dumps(extra_json) if isinstance(extra_json, dict) else extra_json
    result = runner.run_json(
        [
            "adextensions",
            "add",
            "--type",
            extension_type,
            "--json",
            json_str,
        ]
    )
    return result


@mcp.tool()
@handle_cli_errors
def adextensions_delete(ids: str) -> dict:
    """Delete ad extensions.

    Args:
        ids: Comma-separated extension IDs (max 10).
    """
    return run_single_id_batch(get_runner(), "adextensions", "delete", ids)
