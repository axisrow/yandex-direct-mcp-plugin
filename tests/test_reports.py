"""Tests for reports MCP tool."""

from unittest.mock import patch, MagicMock

import pytest

import server.tools
from server.tools.reports import reports_get


@pytest.fixture(autouse=True)
def setup():
    server.tools.set_token_getter(lambda: "test-token")


SAMPLE_REPORTS = [
    {"CampaignId": 12345, "Impressions": 15420, "Clicks": 312, "Cost": 1000.00},
]


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


def test_reports_get():
    """Test 16: Statistics for date range."""
    with patch("server.tools.reports.get_runner", return_value=_mock_runner(SAMPLE_REPORTS)):
        result = reports_get(date_from="2026-03-30", date_to="2026-04-06")
        assert len(result) == 1
        assert result[0]["Impressions"] == 15420


def test_reports_no_dates():
    """Reports without date range."""
    with patch("server.tools.reports.get_runner", return_value=_mock_runner(SAMPLE_REPORTS)):
        result = reports_get()
        assert len(result) == 1
