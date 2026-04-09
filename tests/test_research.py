"""Tests for keyword research MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

import server.tools
from server.tools.research import keywords_has_volume, keywords_deduplicate


@pytest.fixture(autouse=True)
def setup():
    server.tools.set_token_getter(lambda: "test-token")


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


class TestKeywordsHasVolume:
    """Tests for keywords_has_volume tool."""

    def test_keywords_has_volume_basic(self):
        """Test checking keyword search volume without region."""
        mock_result = {"keyword1": True, "keyword2": False}
        with patch(
            "server.tools.research.get_runner", return_value=_mock_runner(mock_result)
        ):
            result = keywords_has_volume(keywords="keyword1,keyword2")
            assert result["keyword1"] is True
            assert result["keyword2"] is False

    def test_keywords_has_volume_with_region(self):
        """Test checking keyword search volume with region ID."""
        mock_result = {"keyword1": True}
        with patch(
            "server.tools.research.get_runner", return_value=_mock_runner(mock_result)
        ):
            result = keywords_has_volume(keywords="keyword1", region_id="1")
            assert result["keyword1"] is True


class TestKeywordsDeduplicate:
    """Tests for keywords_deduplicate tool."""

    def test_keywords_deduplicate_basic(self):
        """Test deduplicating keywords."""
        mock_result = {
            "original": ["keyword1", "keyword2", "keyword1"],
            "deduplicated": ["keyword1", "keyword2"],
        }
        with patch(
            "server.tools.research.get_runner", return_value=_mock_runner(mock_result)
        ):
            result = keywords_deduplicate(keywords="keyword1,keyword2,keyword1")
            assert result["deduplicated"] == ["keyword1", "keyword2"]
