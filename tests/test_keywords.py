"""Tests for keyword MCP tools."""

from unittest.mock import patch, MagicMock

import pytest

import server.tools
from server.tools.keywords import (
    keywords_list,
    keywords_update,
    keywords_add,
    keywords_delete,
    keywords_suspend,
    keywords_resume,
    keywords_archive,
    keywords_unarchive,
)


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
    with patch(
        "server.tools.keywords.get_runner", return_value=_mock_runner(SAMPLE_KEYWORDS)
    ):
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


def test_keywords_update_argv_composition():
    """Test that update passes the expanded CLI surface."""
    runner = _mock_runner({})
    with patch("server.tools.keywords.get_runner", return_value=runner):
        result = keywords_update(
            id="99999",
            bid="15000000",
            context_bid="9000000",
            status="SUSPENDED",
            extra_json='{"StrategyPriority": "HIGH"}',
        )

    runner.run_json.assert_called_once_with(
        [
            "keywords",
            "update",
            "--id",
            "99999",
            "--bid",
            "15000000",
            "--context-bid",
            "9000000",
            "--status",
            "SUSPENDED",
            "--json",
            '{"StrategyPriority": "HIGH"}',
            "--format",
            "json",
        ]
    )
    assert result["context_bid"] == 9000000


def test_keywords_update_requires_changes():
    """Test that empty updates are rejected before CLI call."""
    runner = _mock_runner({})
    with patch("server.tools.keywords.get_runner", return_value=runner):
        result = keywords_update(id="99999")

    assert result["error"] == "missing_update_fields"
    runner.run_json.assert_not_called()


class TestKeywordsCrudOperations:
    """Tests for keyword CRUD operations (add, delete, suspend, resume)."""

    def test_keywords_add(self):
        """Test adding a keyword to an ad group."""
        mock_result = {"success": True}
        with patch(
            "server.tools.keywords.get_runner", return_value=_mock_runner(mock_result)
        ):
            result = keywords_add(ad_group_id="1", keyword="buy shoes")
            assert result["success"] is True

    def test_keywords_delete_success(self):
        """Test deleting keywords successfully."""
        mock_result = {"success": True}
        with patch(
            "server.tools.keywords.get_runner", return_value=_mock_runner(mock_result)
        ):
            result = keywords_delete(ids="111,222")
            assert result["success"] is True

    def test_keywords_delete_batch_limit(self):
        """Test batch limit validation for delete."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = keywords_delete(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_keywords_suspend_success(self):
        """Test suspending keywords."""
        mock_result = {"success": True}
        with patch(
            "server.tools.keywords.get_runner", return_value=_mock_runner(mock_result)
        ):
            result = keywords_suspend(ids="111,222")
            assert result["success"] is True

    def test_keywords_suspend_batch_limit(self):
        """Test batch limit validation for suspend."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = keywords_suspend(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_keywords_resume_success(self):
        """Test resuming suspended keywords."""
        mock_result = {"success": True}
        with patch(
            "server.tools.keywords.get_runner", return_value=_mock_runner(mock_result)
        ):
            result = keywords_resume(ids="111,222")
            assert result["success"] is True

    def test_keywords_resume_batch_limit(self):
        """Test batch limit validation for resume."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = keywords_resume(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"


def test_keywords_archive_success():
    mock_result = {"success": True}
    with patch("server.tools.keywords.get_runner", return_value=_mock_runner(mock_result)):
        result = keywords_archive(ids="111,222")
        assert result["success"] is True


def test_keywords_archive_batch_limit():
    ids = ",".join(str(i) for i in range(1, 12))
    result = keywords_archive(ids=ids)
    assert "error" in result
    assert result["error"] == "batch_limit"


def test_keywords_unarchive_success():
    mock_result = {"success": True}
    with patch("server.tools.keywords.get_runner", return_value=_mock_runner(mock_result)):
        result = keywords_unarchive(ids="111,222")
        assert result["success"] is True


def test_keywords_unarchive_batch_limit():
    ids = ",".join(str(i) for i in range(1, 12))
    result = keywords_unarchive(ids=ids)
    assert "error" in result
    assert result["error"] == "batch_limit"
