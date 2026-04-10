"""MCP tools for ad extensions management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors
from server.tools.helpers import run_single_id_batch


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
    if ids is not None:
        cmd.extend(["--ids", ids])
    if types is not None:
        cmd.extend(["--types", types])
    runner = get_runner()
    result = runner.run_json(cmd)
    return result


@mcp.tool()
@handle_cli_errors
def adextensions_add(extension_type: str, extra_json: str) -> dict:
    """Add an ad extension.

    Args:
        extension_type: Type of extension (e.g., "CALLOUT", "SITELINK").
        extra_json: JSON string describing the extension content.
    """
    runner = get_runner()
    result = runner.run_json(
        [
            "adextensions",
            "add",
            "--type",
            extension_type,
            "--json",
            extra_json,
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
