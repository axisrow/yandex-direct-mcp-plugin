"""MCP tools for ad images management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors


@mcp.tool()
@handle_cli_errors
def adimages_list(ids: str) -> list[dict]:
    """List ad images.

    Args:
        ids: Comma-separated image IDs (empty string for all images).
    """
    runner = get_runner()
    result = runner.run_json(["adimages", "get", "--ids", ids, "--format", "json"])
    return result


@mcp.tool()
@handle_cli_errors
def adimages_add(image_data: str) -> dict:
    """Add an ad image.

    Args:
        image_data: JSON string with image data (base64 encoded).
    """
    runner = get_runner()
    result = runner.run_json(
        ["adimages", "add", "--data", image_data, "--format", "json"]
    )
    return result


@mcp.tool()
@handle_cli_errors
def adimages_delete(ids: str) -> dict:
    """Delete ad images.

    Args:
        ids: Comma-separated image IDs.
    """
    runner = get_runner()
    result = runner.run_json(["adimages", "delete", "--ids", ids, "--format", "json"])
    return result
