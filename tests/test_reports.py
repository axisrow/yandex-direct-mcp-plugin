"""Tests for reports MCP tool."""

from datetime import date, timedelta
from unittest.mock import patch, MagicMock

import pytest

import server.tools
from server.tools.reports import (
    DEFAULT_REPORT_FIELDS,
    DEFAULT_REPORT_NAME,
    DEFAULT_REPORT_TYPE,
    reports_get,
)


@pytest.fixture(autouse=True)
def setup():
    server.tools.set_token_getter(lambda: "test-token")


SAMPLE_REPORTS = [
    {
        "CampaignName": "Sample campaign",
        "Impressions": 15420,
        "Clicks": 312,
        "Cost": 1000.00,
        "Conversions": 14,
    },
]


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


def test_reports_get():
    """Test 16: Statistics for date range."""
    runner = _mock_runner(SAMPLE_REPORTS)
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_get(date_from="2026-03-30", date_to="2026-04-06")
        assert len(result) == 1
        assert result[0]["Impressions"] == 15420
        runner.run_json.assert_called_once_with(
            [
                "reports",
                "get",
                "--type",
                DEFAULT_REPORT_TYPE,
                "--from",
                "2026-03-30",
                "--to",
                "2026-04-06",
                "--name",
                DEFAULT_REPORT_NAME,
                "--fields",
                DEFAULT_REPORT_FIELDS,
                "--format",
                "json",
            ]
        )


def test_reports_no_dates():
    """Reports without date range."""
    runner = _mock_runner(SAMPLE_REPORTS)
    today = date.today()
    expected_from = (today - timedelta(days=8)).isoformat()
    expected_to = today.isoformat()
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_get()
        assert len(result) == 1
        runner.run_json.assert_called_once_with(
            [
                "reports",
                "get",
                "--type",
                DEFAULT_REPORT_TYPE,
                "--from",
                expected_from,
                "--to",
                expected_to,
                "--name",
                DEFAULT_REPORT_NAME,
                "--fields",
                DEFAULT_REPORT_FIELDS,
                "--format",
                "json",
            ]
        )


def test_reports_only_date_to():
    """Missing start date uses the same default 8-day window."""
    runner = _mock_runner(SAMPLE_REPORTS)
    with patch("server.tools.reports.get_runner", return_value=runner):
        reports_get(date_to="2026-04-08")
        runner.run_json.assert_called_once_with(
            [
                "reports",
                "get",
                "--type",
                DEFAULT_REPORT_TYPE,
                "--from",
                "2026-03-31",
                "--to",
                "2026-04-08",
                "--name",
                DEFAULT_REPORT_NAME,
                "--fields",
                DEFAULT_REPORT_FIELDS,
                "--format",
                "json",
            ]
        )


def test_reports_only_date_from():
    """Missing end date uses the same default 8-day window."""
    runner = _mock_runner(SAMPLE_REPORTS)
    with patch("server.tools.reports.get_runner", return_value=runner):
        reports_get(date_from="2026-03-30")
        runner.run_json.assert_called_once_with(
            [
                "reports",
                "get",
                "--type",
                DEFAULT_REPORT_TYPE,
                "--from",
                "2026-03-30",
                "--to",
                "2026-04-07",
                "--name",
                DEFAULT_REPORT_NAME,
                "--fields",
                DEFAULT_REPORT_FIELDS,
                "--format",
                "json",
            ]
        )
