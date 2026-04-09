"""MCP tool for campaign statistics reports."""

from datetime import date, timedelta

from server.main import mcp
from server.tools import get_runner, handle_cli_errors

DEFAULT_REPORT_TYPE = "CAMPAIGN_PERFORMANCE_REPORT"
DEFAULT_REPORT_NAME = "mcp_campaign_performance"
DEFAULT_REPORT_FIELDS = (
    "CampaignName,Impressions,Clicks,Cost,Conversions,CostPerConversion,ConversionRate"
)
DEFAULT_WINDOW_DAYS = 8


def _resolve_report_dates(
    date_from: str | None, date_to: str | None
) -> tuple[str, str]:
    """Resolve the reporting window to match Direct's default day range."""
    if date_from and date_to:
        return date_from, date_to

    if date_to:
        resolved_to = date.fromisoformat(date_to)
        resolved_from = resolved_to - timedelta(days=DEFAULT_WINDOW_DAYS)
        return resolved_from.isoformat(), date_to

    if date_from:
        resolved_from = date.fromisoformat(date_from)
        resolved_to = resolved_from + timedelta(days=DEFAULT_WINDOW_DAYS)
        return date_from, resolved_to.isoformat()

    today = date.today()
    return (today - timedelta(days=DEFAULT_WINDOW_DAYS)).isoformat(), today.isoformat()


@mcp.tool()
@handle_cli_errors
def reports_get(
    date_from: str | None = None, date_to: str | None = None
) -> list[dict] | dict:
    """Get campaign statistics with aggregated goal completions.

    Args:
        date_from: Start date (YYYY-MM-DD). Defaults to today - 8 days.
        date_to: End date (YYYY-MM-DD). Defaults to today.
    """
    runner = get_runner()
    resolved_from, resolved_to = _resolve_report_dates(date_from, date_to)
    args = [
        "reports",
        "get",
        "--type",
        DEFAULT_REPORT_TYPE,
        "--from",
        resolved_from,
        "--to",
        resolved_to,
        "--name",
        DEFAULT_REPORT_NAME,
        "--fields",
        DEFAULT_REPORT_FIELDS,
        "--format",
        "json",
    ]
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def reports_list_types() -> list[str]:
    """List available report types."""
    runner = get_runner()
    return runner.run_json(["reports", "list-types", "--format", "json"])
