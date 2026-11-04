"""MCP tools for Yandex Audience segments (transport: `yac`).

Second-transport tools: every call shells out to `yac` (yandex-audience-cli),
never to the Audience API over HTTP. Mutating tools below warn in their
docstrings per the project convention — the CLI owns validation, the plugin
only informs the LLM.
"""

from server.main import mcp
from server.tools import ToolError, get_audience_runner, handle_cli_errors
from server.tools.helpers import normalize_json_arg, tool_error_dict


def _append_check_size(args: list[str], check_size: bool | None) -> None:
    """Tri-state flag: True → --check-size, False → --no-check-size, None → untouched."""
    if check_size is True:
        args.append("--check-size")
    elif check_size is False:
        args.append("--no-check-size")


def _normalized_data(data: str | dict | list | None) -> str | None:
    """Normalize a JSON body param; MCP hosts may pre-parse it into dict/list."""
    return normalize_json_arg(data)


@mcp.tool(
    name="audience_segments_list",
    description="List Yandex Audience segments (optional pixel filter). Call tool_help('audience_segments_list') for parameters.",
)
@handle_cli_errors
def audience_segments_list(
    pixel: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> list[dict] | dict:
    """List Yandex Audience segments.

    Transport: `yac segments list`. Read-only. The response carries every
    segment with its processing status, matched quantities and, for
    look-alikes, the parent segment link.

    Args:
        pixel: Only segments built from this pixel ID.
        limit: Page size (API default 10000).
        offset: Pagination offset.
    """
    args = ["segments", "list"]
    if pixel is not None:
        args.extend(["--pixel", str(pixel)])
    if limit is not None:
        args.extend(["--limit", str(limit)])
    if offset is not None:
        args.extend(["--offset", str(offset)])
    return get_audience_runner().run_json(args)


@mcp.tool(
    name="audience_segments_create_pixel",
    description="Create a Yandex Audience segment from a pixel (MUTATING: creates a segment). Call tool_help('audience_segments_create_pixel') for parameters.",
)
@handle_cli_errors
def audience_segments_create_pixel(data: str | dict | list) -> list[dict] | dict:
    """Create a segment from a pixel.

    Transport: `yac segments create-pixel --data <json>`. MUTATING: creates a
    new segment. `data` is the Audience API "create from pixel" body (name,
    pixel, etc.) as a JSON string or an already-parsed dict/list — yac passes
    it through verbatim, validation happens server-side.

    Args:
        data: Segment body JSON (string, dict or list).
    """
    normalized = _normalized_data(data)
    if normalized is None:
        return tool_error_dict(
            ToolError(
                error="missing_data",
                message="Provide data as a JSON string or object (segment body).",
            )
        )
    return get_audience_runner().run_json(
        ["segments", "create-pixel", "--data", normalized]
    )


@mcp.tool(
    name="audience_segments_create_lookalike",
    description="Create a Yandex Audience look-alike segment from an existing segment (MUTATING: creates a segment). Call tool_help('audience_segments_create_lookalike') for parameters.",
)
@handle_cli_errors
def audience_segments_create_lookalike(data: str | dict | list) -> list[dict] | dict:
    """Create a look-alike segment.

    Transport: `yac segments create-lookalike --data <json>`. MUTATING:
    creates a new segment derived from a source segment (body carries the
    source segment id and look-alike parameters).

    Args:
        data: Segment body JSON (string, dict or list).
    """
    normalized = _normalized_data(data)
    if normalized is None:
        return tool_error_dict(
            ToolError(
                error="missing_data",
                message="Provide data as a JSON string or object (segment body).",
            )
        )
    return get_audience_runner().run_json(
        ["segments", "create-lookalike", "--data", normalized]
    )


@mcp.tool(
    name="audience_segments_create_metrika",
    description="Create a Yandex Audience segment from Yandex Metrica data (MUTATING: creates a segment). Call tool_help('audience_segments_create_metrika') for parameters.",
)
@handle_cli_errors
def audience_segments_create_metrika(data: str | dict | list) -> list[dict] | dict:
    """Create a segment from Yandex Metrica.

    Transport: `yac segments create-metrika --data <json>`. MUTATING: creates
    a new segment (body describes the Metrica source: counter, segment type,
    period).

    Args:
        data: Segment body JSON (string, dict or list).
    """
    normalized = _normalized_data(data)
    if normalized is None:
        return tool_error_dict(
            ToolError(
                error="missing_data",
                message="Provide data as a JSON string or object (segment body).",
            )
        )
    return get_audience_runner().run_json(
        ["segments", "create-metrika", "--data", normalized]
    )


@mcp.tool(
    name="audience_segments_create_appmetrica",
    description="Create a Yandex Audience segment from AppMetrica data (MUTATING: creates a segment). Call tool_help('audience_segments_create_appmetrica') for parameters.",
)
@handle_cli_errors
def audience_segments_create_appmetrica(data: str | dict | list) -> list[dict] | dict:
    """Create a segment from AppMetrica.

    Transport: `yac segments create-appmetrica --data <json>`. MUTATING:
    creates a new segment (body describes the AppMetrica application source).

    Args:
        data: Segment body JSON (string, dict or list).
    """
    normalized = _normalized_data(data)
    if normalized is None:
        return tool_error_dict(
            ToolError(
                error="missing_data",
                message="Provide data as a JSON string or object (segment body).",
            )
        )
    return get_audience_runner().run_json(
        ["segments", "create-appmetrica", "--data", normalized]
    )


@mcp.tool(
    name="audience_segments_create_geo",
    description="Create a Yandex Audience geo segment — circle (MUTATING: creates a segment). Call tool_help('audience_segments_create_geo') for parameters.",
)
@handle_cli_errors
def audience_segments_create_geo(data: str | dict | list) -> list[dict] | dict:
    """Create a geo segment (circle).

    Transport: `yac segments create-geo --data <json>`. MUTATING: creates a
    new segment (body: geo points with longitude/latitude/radius).

    Args:
        data: Segment body JSON (string, dict or list).
    """
    normalized = _normalized_data(data)
    if normalized is None:
        return tool_error_dict(
            ToolError(
                error="missing_data",
                message="Provide data as a JSON string or object (segment body).",
            )
        )
    return get_audience_runner().run_json(
        ["segments", "create-geo", "--data", normalized]
    )


@mcp.tool(
    name="audience_segments_create_geo_polygon",
    description="Create a Yandex Audience geo segment — polygon (MUTATING: creates a segment). Call tool_help('audience_segments_create_geo_polygon') for parameters.",
)
@handle_cli_errors
def audience_segments_create_geo_polygon(data: str | dict | list) -> list[dict] | dict:
    """Create a geo segment (polygon).

    Transport: `yac segments create-geo-polygon --data <json>`. MUTATING:
    creates a new segment (body: polygon points).

    Args:
        data: Segment body JSON (string, dict or list).
    """
    normalized = _normalized_data(data)
    if normalized is None:
        return tool_error_dict(
            ToolError(
                error="missing_data",
                message="Provide data as a JSON string or object (segment body).",
            )
        )
    return get_audience_runner().run_json(
        ["segments", "create-geo-polygon", "--data", normalized]
    )


@mcp.tool(
    name="audience_segments_upload_file",
    description="Upload a CRM/idfa_gaid/mac/client_id data file as a new Yandex Audience segment (MUTATING: creates an uploading segment). Call tool_help('audience_segments_upload_file') for parameters.",
)
@handle_cli_errors
def audience_segments_upload_file(file: str) -> list[dict] | dict:
    """Upload a data file as a new segment.

    Transport: `yac segments upload-file <path>`. MUTATING: creates a new
    segment in "uploading" state and starts processing the file contents.

    Args:
        file: Path to the data file on the machine running the MCP server
            (CRM / idfa_gaid / mac / client_id format; one record per line).

    The segment stays unconfirmed until audience_segments_confirm is called
    for the returned segment id.
    """
    return get_audience_runner().run_json(["segments", "upload-file", file])


@mcp.tool(
    name="audience_segments_upload_csv_file",
    description="Upload a CSV data file as a new Yandex Audience segment (MUTATING: creates an uploading segment). Call tool_help('audience_segments_upload_csv_file') for parameters.",
)
@handle_cli_errors
def audience_segments_upload_csv_file(file: str) -> list[dict] | dict:
    """Upload a CSV data file as a new segment.

    Transport: `yac segments upload-csv-file <path>`. MUTATING: creates a new
    segment in "uploading" state and starts processing the CSV contents.

    Args:
        file: Path to the CSV file on the machine running the MCP server.

    The segment stays unconfirmed until audience_segments_confirm is called
    for the returned segment id.
    """
    return get_audience_runner().run_json(["segments", "upload-csv-file", file])


@mcp.tool(
    name="audience_segments_update_geo_points",
    description="Update coordinates of a geo (circle) segment (MUTATING). Call tool_help('audience_segments_update_geo_points') for parameters.",
)
@handle_cli_errors
def audience_segments_update_geo_points(
    segment_id: str, data: str | dict | list
) -> list[dict] | dict:
    """Update geo segment coordinates.

    Transport: `yac segments update-geo-points <id> --data <json>`. MUTATING:
    replaces the segment's geo points (JSON array of points).

    Args:
        segment_id: Segment ID.
        data: JSON array of geo points (string, dict/list from a pre-parsing
            host, @file path or - for stdin — yac accepts all forms).
    """
    normalized = _normalized_data(data)
    if normalized is None:
        return tool_error_dict(
            ToolError(
                error="missing_data",
                message="Provide data as a JSON array of geo points.",
            )
        )
    return get_audience_runner().run_json(
        ["segments", "update-geo-points", segment_id.strip(), "--data", normalized]
    )


@mcp.tool(
    name="audience_segments_modify_data",
    description="Modify the data of a file-based segment (add/subtract/replace) (MUTATING). Call tool_help('audience_segments_modify_data') for parameters.",
)
@handle_cli_errors
def audience_segments_modify_data(
    segment_id: str,
    file: str,
    modification_type: str,
    check_size: bool | None = None,
) -> list[dict] | dict:
    """Modify the data of a file-uploaded segment.

    Transport: `yac segments modify-data <id> <file> --modification-type <t>`.
    MUTATING: changes the segment's data contents.

    Args:
        segment_id: Segment ID to modify.
        file: Path to the file with the updated data (on the MCP server host).
        modification_type: addition | subtraction | replace.
        check_size: Tri-state. True → --check-size (require >=100 records),
            False → --no-check-size, omit → CLI default.
    """
    args = [
        "segments",
        "modify-data",
        segment_id.strip(),
        file,
        "--modification-type",
        modification_type,
    ]
    _append_check_size(args, check_size)
    return get_audience_runner().run_json(args)


@mcp.tool(
    name="audience_segments_confirm",
    description="Confirm/finalize an uploaded (unconfirmed) Yandex Audience segment (MUTATING: finalizes the segment data). Call tool_help('audience_segments_confirm') for parameters.",
)
@handle_cli_errors
def audience_segments_confirm(
    segment_id: str, data: str | dict | list, check_size: bool | None = None
) -> list[dict] | dict:
    """Confirm an uploaded segment.

    Transport: `yac segments confirm <id> --data <json>`. MUTATING: saves /
    finalizes a previously uploaded segment — after confirm the segment
    enters processing.

    Args:
        segment_id: Unconfirmed segment ID.
        data: Segment body JSON (string, dict/list from a pre-parsing host).
        check_size: Tri-state. True → --check-size (require >=100 records),
            False → --no-check-size, omit → CLI default.
    """
    normalized = _normalized_data(data)
    if normalized is None:
        return tool_error_dict(
            ToolError(
                error="missing_data",
                message="Provide data as a JSON string or object (segment body).",
            )
        )
    args = ["segments", "confirm", segment_id.strip(), "--data", normalized]
    _append_check_size(args, check_size)
    return get_audience_runner().run_json(args)


@mcp.tool(
    name="audience_segments_confirm_client_id",
    description="Confirm a Yandex Audience segment uploaded from Metrica ClientId data (MUTATING). Call tool_help('audience_segments_confirm_client_id') for parameters.",
)
@handle_cli_errors
def audience_segments_confirm_client_id(
    segment_id: str, data: str | dict | list
) -> list[dict] | dict:
    """Confirm a ClientId (Metrica) segment.

    Transport: `yac segments confirm-client-id <id> --data <json>`. MUTATING:
    saves / finalizes a segment built from Metrica ClientId data.

    Args:
        segment_id: Unconfirmed segment ID.
        data: Segment body JSON (string, dict/list from a pre-parsing host).
    """
    normalized = _normalized_data(data)
    if normalized is None:
        return tool_error_dict(
            ToolError(
                error="missing_data",
                message="Provide data as a JSON string or object (segment body).",
            )
        )
    return get_audience_runner().run_json(
        ["segments", "confirm-client-id", segment_id.strip(), "--data", normalized]
    )


@mcp.tool(
    name="audience_segments_update",
    description="Update a Yandex Audience segment, e.g. rename it (MUTATING). Call tool_help('audience_segments_update') for parameters.",
)
@handle_cli_errors
def audience_segments_update(
    segment_id: str, data: str | dict | list
) -> list[dict] | dict:
    """Update a segment.

    Transport: `yac segments update <id> --data <json>`. MUTATING: applies the
    JSON patch/body to the segment (typically renaming).

    Args:
        segment_id: Segment ID.
        data: Segment body JSON (string, dict/list from a pre-parsing host).
    """
    normalized = _normalized_data(data)
    if normalized is None:
        return tool_error_dict(
            ToolError(
                error="missing_data",
                message="Provide data as a JSON string or object (segment body).",
            )
        )
    return get_audience_runner().run_json(
        ["segments", "update", segment_id.strip(), "--data", normalized]
    )


@mcp.tool(
    name="audience_segments_delete",
    description="Permanently delete a Yandex Audience segment — IRREVERSIBLE, no undo. Call tool_help('audience_segments_delete') for parameters.",
)
@handle_cli_errors
def audience_segments_delete(segment_id: str) -> list[dict] | dict:
    """Delete a segment.

    Transport: `yac segments delete <id>`. PERMANENT: unlike pixels (which can
    be restored with audience_pixels_undelete), a deleted segment has no undo
    and no CLI rollback. Yandex shows no confirmation dialog — this tool
    deletes immediately.

    Args:
        segment_id: Segment ID to delete.
    """
    return get_audience_runner().run_json(["segments", "delete", segment_id.strip()])


@mcp.tool(
    name="audience_segments_reprocess",
    description="Reprocess (recount) a Yandex Audience segment (MUTATING: restarts segment processing). Call tool_help('audience_segments_reprocess') for parameters.",
)
@handle_cli_errors
def audience_segments_reprocess(segment_id: str) -> list[dict] | dict:
    """Reprocess a segment.

    Transport: `yac segments reprocess <id>`. MUTATING: restarts processing
    of the segment's data (matching counts refresh asynchronously).

    Args:
        segment_id: Segment ID.
    """
    return get_audience_runner().run_json(["segments", "reprocess", segment_id.strip()])
