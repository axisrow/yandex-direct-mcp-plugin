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
