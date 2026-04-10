"""MCP tools for ad images management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors


@mcp.tool()
@handle_cli_errors
def adimages_list(ids: str | None = None) -> list[dict] | dict:
    """List ad images.

    Args:
        ids: Comma-separated image IDs (optional, empty for all images).
    """
    runner = get_runner()
    cmd = ["adimages", "get", "--format", "json"]
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        cmd.extend(["--ids", normalized_ids])
    result = runner.run_json(cmd)
    return result


@mcp.tool()
@handle_cli_errors
def adimages_add(image_json: str) -> dict:
    """Add an ad image.

    Args:
        image_json: JSON string with image data (e.g. base64-encoded).
    """
    runner = get_runner()
    result = runner.run_json(["adimages", "add", "--json", image_json])
    return result


@mcp.tool()
@handle_cli_errors
def adimages_delete(hash_value: str) -> dict:
    """Delete an ad image by its hash.

    Note: The previous ``ids`` parameter accepted comma-separated IDs,
    but the CLI only supports deleting a single image at a time via
    ``--hash``.  The old parameter was always incorrect.

    Args:
        hash_value: Ad image hash to delete.
    """
    runner = get_runner()
    result = runner.run_json(["adimages", "delete", "--hash", hash_value])
    return result
