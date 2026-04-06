"""Tests for ads MCP tool."""

from unittest.mock import patch, MagicMock

import pytest

import server.tools
from server.tools.ads import ads_list


@pytest.fixture(autouse=True)
def setup():
    server.tools.set_token_getter(lambda: "test-token")


SAMPLE_ADS = [
    {
        "Id": 111,
        "Title": "Ad title placeholder",
        "Title2": "Ad title2 placeholder",
        "State": "ON",
    },
    {"Id": 222, "Title": "Ad title placeholder 2", "State": "OFF"},
]


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


def test_ads_list_success():
    """Test 11: List ads in a campaign."""
    with patch("server.tools.ads.get_runner", return_value=_mock_runner(SAMPLE_ADS)):
        result = ads_list(campaign_ids="12345")
        assert len(result) == 2


def test_ads_foreign_campaign():
    """Test 12: Campaign belongs to second account (73-77M range)."""
    result = ads_list(campaign_ids="75000001")
    assert "error" in result
    assert result["error"] == "foreign_campaign"


def test_ads_batch_limit():
    """Test 13: Too many IDs."""
    ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
    result = ads_list(campaign_ids=ids)
    assert "error" in result
    assert result["error"] == "batch_limit"


def test_ads_empty():
    """Empty result."""
    with patch("server.tools.ads.get_runner", return_value=_mock_runner([])):
        result = ads_list(campaign_ids="12345")
        assert result == []
