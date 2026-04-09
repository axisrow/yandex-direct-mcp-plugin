"""MCP tools for ad extensions management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors


@mcp.tool()
@handle_cli_errors
def adextensions_list(ids: str) -> list[dict] | dict:
    """List ad extensions.

    Args:
        ids: Comma-separated extension IDs (empty string for all extensions).
    """
    runner = get_runner()
    result = runner.run_json(["adextensions", "get", "--ids", ids, "--format", "json"])
    return result


@mcp.tool()
@handle_cli_errors
def adextensions_add(extension_type: str, extension_data: str) -> dict:
    """Add an ad extension.

    Args:
        extension_type: Type of extension (e.g., "Call", "Message", "Rating").
        extension_data: JSON string describing the extension.
    """
    runner = get_runner()
    result = runner.run_json(
        [
            "adextensions",
            "add",
            "--type",
            extension_type,
            "--data",
            extension_data,
            "--format",
            "json",
        ]
    )
    return result


@mcp.tool()
@handle_cli_errors
def adextensions_delete(ids: str) -> dict:
    """Delete ad extensions.

    Args:
        ids: Comma-separated extension IDs.
    """
    runner = get_runner()
    result = runner.run_json(
        ["adextensions", "delete", "--ids", ids, "--format", "json"]
    )
    return result
