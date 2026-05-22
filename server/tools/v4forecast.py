"""MCP tools for Yandex Direct v4 Live budget forecast commands."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors

MAX_PHRASES = 100


@mcp.tool(name="v4forecast_create")
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
    normalized_phrases = phrases.strip()
    if not normalized_phrases:
        return ToolError(
            error="missing_phrases",
            message="Provide at least one phrase.",
        ).__dict__
    phrase_count = sum(1 for p in normalized_phrases.split(",") if p.strip())
    if phrase_count > MAX_PHRASES:
        return ToolError(
            error="phrases_limit",
            message=f"Maximum {MAX_PHRASES} phrases per forecast. Got: {phrase_count}",
        ).__dict__

    args = ["v4forecast", "create", "--phrases", normalized_phrases]
    if geo_ids is not None:
        normalized_geo = geo_ids.strip()
        if normalized_geo:
            args.extend(["--geo-ids", normalized_geo])
    if currency:
        args.extend(["--currency", currency])
    if dry_run:
        args.append("--dry-run")
    args.extend(["--format", "json"])

    return get_runner().run_json(args)


@mcp.tool(name="v4forecast_list")
@handle_cli_errors
def v4forecast_list() -> dict | list[dict]:
    """List v4 Live budget forecasts via GetForecastList."""
    return get_runner().run_json(["v4forecast", "list", "--format", "json"])


@mcp.tool(name="v4forecast_get")
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


@mcp.tool(name="v4forecast_delete")
@handle_cli_errors
def v4forecast_delete(forecast_id: int, dry_run: bool = False) -> dict | list[dict]:
    """Delete a v4 Live budget forecast via DeleteForecastReport.

    Args:
        forecast_id: Forecast ID to delete.
        dry_run: Show the direct request without sending it.
    """
    args = ["v4forecast", "delete", "--forecast-id", str(forecast_id)]
    if dry_run:
        args.append("--dry-run")
    args.extend(["--format", "json"])

    return get_runner().run_json(args)
