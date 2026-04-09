"""MCP tools for Yandex.Direct dictionaries."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors

ALLOWED_DICTIONARY_TYPES = (
    "GeographyRegions",
    "TimeZones",
    "Currencies",
    "Constants",
    "AdCategories",
    "OperationSystemVersions",
    "MobileOperatingSystemVersions",
    "DeviceTypes",
    "AgeRanges",
    "Genders",
    "Interests",
)


@mcp.tool()
@handle_cli_errors
def dictionaries_get(dictionary_type: str, locale: str | None = None) -> dict:
    """Get dictionary data.

    Args:
        dictionary_type: Type of dictionary to retrieve. Must be one of:
            GeographyRegions, TimeZones, Currencies, Constants, AdCategories,
            OperationSystemVersions, MobileOperatingSystemVersions, DeviceTypes,
            AgeRanges, Genders, Interests
        locale: Optional locale code (e.g., "ru", "en").
    """
    if dictionary_type not in ALLOWED_DICTIONARY_TYPES:
        return ToolError(
            error="invalid_type",
            message=f"Dictionary type must be one of {ALLOWED_DICTIONARY_TYPES}. Got: '{dictionary_type}'",
        ).__dict__

    runner = get_runner()
    cmd = ["dictionaries", "get", "--type", dictionary_type, "--format", "json"]
    if locale is not None:
        cmd.extend(["--locale", locale])

    result = runner.run_json(cmd)
    return result
