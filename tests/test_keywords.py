"""Tests for keyword MCP tools."""

from unittest.mock import patch, MagicMock

import pytest

import server.tools
from server.tools.keywords import keywords_list, keywords_update


@pytest.fixture(autouse=True)
def setup():
    server.tools.set_token_getter(lambda: "test-token")


SAMPLE_KEYWORDS = [
    {"Id": 99999, "Keyword": "keyword_99999", "Bid": 12000000},
]


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


def test_keywords_list():
    """Test 14: List keywords."""
    with patch("server.tools.keywords.get_runner", return_value=_mock_runner(SAMPLE_KEYWORDS)):
        result = keywords_list(campaign_ids="12345")
        assert len(result) == 1
        assert result[0]["Id"] == 99999


def test_keywords_update():
    """Test 15: Update bid."""
    with patch("server.tools.keywords.get_runner", return_value=_mock_runner({})):
        result = keywords_update(id="99999", bid="15000000")
        assert result["success"] is True
        assert result["bid"] == 15000000


def test_keywords_update_invalid_bid():
    """Invalid bid value."""
    result = keywords_update(id="99999", bid="-100")
    assert "error" in result
    assert result["error"] == "invalid_bid"

    result = keywords_update(id="99999", bid="abc")
    assert "error" in result
    assert result["error"] == "invalid_bid"
