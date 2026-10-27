"""MCP tools for Yandex.Direct dictionaries."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors

# Names accepted by Dictionaries.get in Direct API v5. The CLI's own
# `dictionaries list-names` only knows the first ten, but `dictionaries get`
# (and the API) accept the audience / schema dictionaries too — so list them
# here to keep this tool in sync with what dictionaries_get can actually fetch.
# Source: https://yandex.ru/dev/direct/doc/ru/dictionaries/get
ALLOWED_DICTIONARY_NAMES = (
    "Currencies",
    "MetroStations",
    "GeoRegions",
    "GeoRegionNames",
    "TimeZones",
    "Constants",
    "AdCategories",
    "OperationSystemVersions",
    "ProductivityAssertions",
    "SupplySidePlatforms",
    "Interests",
    "AudienceInterests",
    "AudienceCriteriaTypes",
    "AudienceDemographicProfiles",
    "FilterSchemas",
)


@mcp.tool(
    description="Get reference dictionary data by names (Currencies, GeoRegions, TimeZones, etc.); use dictionaries_list_names to see options. Call tool_help('dictionaries_get') for parameters.",
)
@handle_cli_errors
def dictionaries_get(names: str) -> dict:
    """Get dictionary data.

    Args:
        names: Comma-separated dictionary names to retrieve.
            Available: Currencies, MetroStations, GeoRegions, GeoRegionNames,
            TimeZones, Constants, AdCategories, OperationSystemVersions,
            ProductivityAssertions, SupplySidePlatforms, Interests,
            AudienceInterests, AudienceCriteriaTypes,
            AudienceDemographicProfiles, FilterSchemas.
    """
    runner = get_runner()
    result = runner.run_json(
        ["dictionaries", "get", "--names", names, "--format", "json"]
    )
    return result


@mcp.tool(
    description="List the dictionary names accepted by dictionaries_get. Call tool_help('dictionaries_list_names') for parameters.",
)
@handle_cli_errors
def dictionaries_list_names() -> list[str]:
    """List available dictionary names."""
    return list(ALLOWED_DICTIONARY_NAMES)


@mcp.tool(
    name="dictionaries_get_retargeting_goals",
    description="Get retargeting goals via the v5 dictionary (domain/app name → ExternalId); prefer it over v4goals_get_retargeting_goals when mapping a domain to an ExternalId, the v4 tool lists goals scoped to campaigns. Call tool_help('dictionaries_get_retargeting_goals') for parameters.",
)
@handle_cli_errors
def dictionaries_get_retargeting_goals(
    name: str | None = None,
    ids: str | None = None,
) -> dict | list[dict]:
    """Get retargeting goals dictionary entries (v5, direct-cli #853).

    Maps a website address or application name to the ExternalId used in
    RetargetingList(Type=AUDIENCE) → Rules[].Arguments[].ExternalId — e.g.
    for audience rules or reports_custom Conversions_<goal>_<attr> columns.

    Yandex does not document this method and does not guarantee its
    stability. Name search may return several goal types with similar names
    (Type=HOST and Type=APPLICATION) — pick the entry with the needed Type.

    Use v4goals_get_retargeting_goals for the campaign-scoped v4 Live
    channel; this tool is the canonical domain → ExternalId dictionary.

    Args:
        name: Goal name to search for (e.g. a domain like "example.com").
        ids: Comma-separated retargeting goal IDs to search.
    """
    args = ["dictionaries", "get-retargeting-goals", "--format", "json"]
    if name is not None:
        args.extend(["--name", name])
    if ids is not None:
        args.extend(["--ids", ids])

    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(
    name="dictionaries_get_geo_regions",
    description="Get GeoRegions dictionary entries, optionally filtered by name or region IDs. Call tool_help('dictionaries_get_geo_regions') for parameters.",
)
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
