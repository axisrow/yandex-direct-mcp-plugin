"""MCP tools for Yandex.Direct dictionaries."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors

ALLOWED_DICTIONARY_NAMES = (
    "Currencies",
    "MetroStations",
    "GeoRegions",
    "TimeZones",
    "Constants",
    "AdCategories",
    "OperationSystemVersions",
    "ProductivityAssertions",
    "SupplySidePlatforms",
    "Interests",
)


@mcp.tool()
@handle_cli_errors
def dictionaries_get(names: str) -> dict:
    """Get dictionary data.

    Args:
        names: Comma-separated dictionary names to retrieve.
            Available: Currencies, MetroStations, GeoRegions, TimeZones,
            Constants, AdCategories, OperationSystemVersions,
            ProductivityAssertions, SupplySidePlatforms, Interests.
    """
    runner = get_runner()
    result = runner.run_json(
        ["dictionaries", "get", "--names", names, "--format", "json"]
    )
    return result


@mcp.tool()
@handle_cli_errors
def dictionaries_list_names() -> list[str]:
    """List available dictionary names."""
    return list(ALLOWED_DICTIONARY_NAMES)


@mcp.tool(name="dictionaries_get_geo_regions")
@handle_cli_errors
def dictionaries_get_geo_regions(
    fields: str,
    name: str | None = None,
    region_ids: str | None = None,
    exact_names: str | None = None,
) -> dict:
    """Get GeoRegions dictionary entries."""
    args = ["dictionaries", "get-geo-regions", "--fields", fields, "--format", "json"]
    if name is not None:
        args.extend(["--name", name])
    if region_ids is not None:
        args.extend(["--region-ids", region_ids])
    if exact_names is not None:
        args.extend(["--exact-names", exact_names])

    runner = get_runner()
    return runner.run_json(args)
