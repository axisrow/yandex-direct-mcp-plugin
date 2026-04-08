"""Tests for negative keyword MCP tools."""

from unittest.mock import patch, MagicMock

import pytest

import server.tools
from server.tools.negative_keywords import (
    negative_keywords_list,
    negative_keywords_add,
    negative_keywords_update,
    negative_keywords_delete,
)


@pytest.fixture(autouse=True)
def setup():
    server.tools.set_token_getter(lambda: "test-token")


SAMPLE_NEGATIVE_KEYWORDS = [
    {"Id": 1, "CampaignId": 12345, "Keywords": "bad keyword, another bad"},
]


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


def test_negative_keywords_list():
    """Test listing negative keywords."""
    with patch(
        "server.tools.negative_keywords.get_runner",
        return_value=_mock_runner(SAMPLE_NEGATIVE_KEYWORDS),
    ):
        result = negative_keywords_list(campaign_ids="12345")
        assert len(result) == 1
        assert result[0]["Id"] == 1
        assert result[0]["CampaignId"] == 12345


def test_negative_keywords_add():
    """Test adding negative keywords."""
    mock_result = {"success": True, "id": 1}
    with patch(
        "server.tools.negative_keywords.get_runner",
        return_value=_mock_runner(mock_result),
    ):
        result = negative_keywords_add(campaign_id="12345", keywords="bad, awful")
        assert result["success"] is True
        assert result["id"] == 1


def test_negative_keywords_update():
    """Test updating negative keywords."""
    mock_result = {"success": True, "id": 1}
    with patch(
        "server.tools.negative_keywords.get_runner",
        return_value=_mock_runner(mock_result),
    ):
        result = negative_keywords_update(id="1", keywords="new bad, worse")
        assert result["success"] is True
        assert result["id"] == 1


class TestNegativeKeywordsDelete:
    """Tests for negative keyword delete operations."""

    def test_negative_keywords_delete_success(self):
        """Test deleting negative keywords successfully."""
        mock_result = {"success": True}
        with patch(
            "server.tools.negative_keywords.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = negative_keywords_delete(ids="1,2")
            assert result["success"] is True

    def test_negative_keywords_delete_batch_limit(self):
        """Test batch limit validation for delete."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = negative_keywords_delete(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"
