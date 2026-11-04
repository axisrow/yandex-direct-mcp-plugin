"""MCP tools for Yandex Audience pixels (transport: `yac`)."""

from server.main import mcp
from server.tools import get_audience_runner, handle_cli_errors


@mcp.tool(
    name="audience_pixels_list",
    description="List Yandex Audience pixels with their audience counters. Call tool_help('audience_pixels_list') for parameters.",
)
@handle_cli_errors
def audience_pixels_list() -> list[dict] | dict:
    """List pixels.

    Transport: `yac pixels list`. Read-only. Each pixel carries its tracking
    URL and user_quantity_* counters.
    """
    return get_audience_runner().run_json(["pixels", "list"])


@mcp.tool(
    name="audience_pixels_create",
    description="Create a Yandex Audience pixel (MUTATING: creates a pixel). Call tool_help('audience_pixels_create') for parameters.",
)
@handle_cli_errors
def audience_pixels_create(name: str) -> list[dict] | dict:
    """Create a pixel.

    Transport: `yac pixels create --name <name>`. MUTATING: creates a new
    tracking pixel — install its URL on the site to start collecting
    audiences.

    Args:
        name: Pixel name.
    """
    return get_audience_runner().run_json(["pixels", "create", "--name", name])


@mcp.tool(
    name="audience_pixels_update",
    description="Rename a Yandex Audience pixel (MUTATING). Call tool_help('audience_pixels_update') for parameters.",
)
@handle_cli_errors
def audience_pixels_update(pixel_id: str, name: str) -> list[dict] | dict:
    """Update (rename) a pixel.

    Transport: `yac pixels update <id> --name <name>`. MUTATING: renames the
    pixel; tracking URL and collected data are untouched.

    Args:
        pixel_id: Pixel ID.
        name: New pixel name.
    """
    return get_audience_runner().run_json(
        ["pixels", "update", pixel_id.strip(), "--name", name]
    )


@mcp.tool(
    name="audience_pixels_delete",
    description="Delete a Yandex Audience pixel (MUTATING: soft-deletes; restorable via audience_pixels_undelete). Call tool_help('audience_pixels_delete') for parameters.",
)
@handle_cli_errors
def audience_pixels_delete(pixel_id: str) -> list[dict] | dict:
    """Delete a pixel.

    Transport: `yac pixels delete <id>`. MUTATING: the Audience API soft-
    deletes pixels — restoration is possible via audience_pixels_undelete,
    but do not rely on it for cleanup hygiene. Segments built on the pixel
    are a separate matter: deleting a segment is permanent
    (audience_segments_delete).

    Args:
        pixel_id: Pixel ID.
    """
    return get_audience_runner().run_json(["pixels", "delete", pixel_id.strip()])


@mcp.tool(
    name="audience_pixels_undelete",
    description="Restore a previously deleted Yandex Audience pixel. Call tool_help('audience_pixels_undelete') for parameters.",
)
@handle_cli_errors
def audience_pixels_undelete(pixel_id: str) -> list[dict] | dict:
    """Restore a deleted pixel.

    Transport: `yac pixels undelete <id>`. Reverses audience_pixels_delete.

    Args:
        pixel_id: Pixel ID.
    """
    return get_audience_runner().run_json(["pixels", "undelete", pixel_id.strip()])
