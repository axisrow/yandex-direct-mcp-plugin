"""MCP tools for ad images management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import normalize_optional_str, validate_yes_no


@mcp.tool(
    name="adimages_get",
    description="List ad images (image assets used in ads), optionally filtered by IDs/hashes/association. Use adimages_add to upload, adimages_delete to remove. Call tool_help('adimages_get') for parameters.",
)
@handle_cli_errors
def adimages_list(
    ids: str | None = None,
    image_hashes: str | None = None,
    associated: str | None = None,
    limit: int | None = None,
    fetch_all: bool = False,
    fields: str | None = None,
) -> list[dict] | dict:
    """List ad images.

    Args:
        ids: Comma-separated image IDs (empty for all images).
        image_hashes: Comma-separated ad image hashes.
        associated: Filter by association — "YES" or "NO".
        limit: Limit number of results.
        fetch_all: Fetch all pages.
        fields: Comma-separated field names.
    """
    if associated is not None:
        err = validate_yes_no(
            associated, field="associated", error="invalid_associated"
        )
        if err is not None:
            return err.__dict__

    cmd = ["adimages", "get", "--format", "json"]
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        cmd.extend(["--ids", normalized_ids])
    if image_hashes is not None:
        cmd.extend(["--image-hashes", image_hashes])
    if associated is not None:
        cmd.extend(["--associated", associated])
    if limit is not None:
        cmd.extend(["--limit", str(limit)])
    if fetch_all:
        cmd.append("--fetch-all")
    if fields is not None:
        cmd.extend(["--fields", fields])
    return get_runner().run_json(cmd)


@mcp.tool(
    description="Add an ad image from base64 data or a local file path. Use adimages_get to list existing images. Call tool_help('adimages_add') for parameters.",
)
@handle_cli_errors
def adimages_add(
    name: str,
    image_data: str | None = None,
    image_file: str | None = None,
    type: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Add an ad image.

    CLI 0.3.8 dropped --json. Provide either base64-encoded image_data or a
    path via image_file (CLI will read and base64-encode it).

    Args:
        name: Image name.
        image_data: Base64-encoded image data.
        image_file: Path to an image file (CLI base64-encodes it).
        type: Ad image type.
        dry_run: Show the direct request without sending it.
    """
    # Match the CLI's truthy XOR (`bool(image_data) == bool(image_file)`):
    # normalize blanks to None so an empty-string source counts as absent and
    # is never emitted as `--image-data ""`. (#170-24)
    image_data = normalize_optional_str(image_data)
    image_file = normalize_optional_str(image_file)
    if image_data is None and image_file is None:
        return ToolError(
            error="missing_image_source",
            message="Provide either image_data (base64) or image_file (path).",
        ).__dict__
    if image_data is not None and image_file is not None:
        return ToolError(
            error="conflicting_image_source",
            message="Provide image_data OR image_file, not both.",
        ).__dict__

    args = ["adimages", "add", "--name", name]
    if image_data is not None:
        args.extend(["--image-data", image_data])
    if image_file is not None:
        args.extend(["--image-file", image_file])
    if type is not None:
        args.extend(["--type", type])
    if dry_run:
        args.append("--dry-run")
    return get_runner().run_json(args)


@mcp.tool(
    description="Delete an ad image by its hash. Use adimages_get to find the hash. Call tool_help('adimages_delete') for parameters.",
)
@handle_cli_errors
def adimages_delete(hash_value: str, dry_run: bool = False) -> dict:
    """Delete an ad image by its hash.

    Args:
        hash_value: Ad image hash to delete.
        dry_run: Show the direct request without sending it.
    """
    args = ["adimages", "delete", "--hash", hash_value]
    if dry_run:
        args.append("--dry-run")
    return get_runner().run_json(args)
