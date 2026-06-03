"""MCP tools for Yandex Direct v4 Live budget forecast commands."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import (
    finalize_json_args,
    normalize_optional_str,
    validate_phrase_csv,
)

MAX_PHRASES = 100


@mcp.tool(
    name="v4forecast_create",
    description="Create a v4 Live budget forecast via CreateNewForecast (up to 100 phrases). Call tool_help('v4forecast_create') for parameters.",
)
@handle_cli_errors
def v4forecast_create(
    phrases: str,
    geo_ids: str | None = None,
    currency: str = "RUB",
    dry_run: bool = False,
) -> dict | list[dict]:
    """Create a v4 Live budget forecast via CreateNewForecast.

    Args:
        phrases: Comma-separated phrases, up to 100.
        geo_ids: Comma-separated geo region IDs (optional).
        currency: Forecast currency (default RUB).
        dry_run: Show the direct request without sending it.
    """
    normalized_phrases = validate_phrase_csv(phrases, MAX_PHRASES, subject="forecast")
    if isinstance(normalized_phrases, ToolError):
        return normalized_phrases.__dict__

    args = ["v4forecast", "create", "--phrases", normalized_phrases]
    normalized_geo = normalize_optional_str(geo_ids)
    if normalized_geo:
        args.extend(["--geo-ids", normalized_geo])
    if currency:
        args.extend(["--currency", currency])

    return get_runner().run_json(finalize_json_args(args, dry_run))


@mcp.tool(
    name="v4forecast_list",
    description="List v4 Live budget forecasts via GetForecastList. Call tool_help('v4forecast_list') for parameters.",
)
@handle_cli_errors
def v4forecast_list() -> dict | list[dict]:
    """List v4 Live budget forecasts via GetForecastList."""
    return get_runner().run_json(["v4forecast", "list", "--format", "json"])


@mcp.tool(
    name="v4forecast_get",
    description="Get a ready v4 Live budget forecast by ID via GetForecast. Call tool_help('v4forecast_get') for parameters.",
)
@handle_cli_errors
def v4forecast_get(forecast_id: int) -> dict | list[dict]:
    """Get a ready v4 Live budget forecast via GetForecast.

    Args:
        forecast_id: Forecast ID returned by v4forecast_create / v4forecast_list.
    """
    return get_runner().run_json(
        [
            "v4forecast",
            "get",
            "--forecast-id",
            str(forecast_id),
            "--format",
            "json",
        ]
    )


@mcp.tool(
    name="v4forecast_delete",
    description="Delete a v4 Live budget forecast by ID via DeleteForecastReport. Call tool_help('v4forecast_delete') for parameters.",
)
@handle_cli_errors
def v4forecast_delete(forecast_id: int, dry_run: bool = False) -> dict | list[dict]:
    """Delete a v4 Live budget forecast via DeleteForecastReport.

    Args:
        forecast_id: Forecast ID to delete.
        dry_run: Show the direct request without sending it.
    """
    args = ["v4forecast", "delete", "--forecast-id", str(forecast_id)]

    return get_runner().run_json(finalize_json_args(args, dry_run))
