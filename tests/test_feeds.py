"""Tests for feeds MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

import server.tools
from server.tools.feeds import feeds_list, feeds_add, feeds_update, feeds_delete


@pytest.fixture(autouse=True)
def setup():
    server.tools.set_token_getter(lambda: "test-token")


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


class TestFeedsList:
    """Tests for feeds_list tool."""

    def test_feeds_list_basic(self):
        """Test listing feeds by IDs."""
        mock_result = {"feeds": [{"id": 1, "name": "Feed 1"}]}
        with patch(
            "server.tools.feeds.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = feeds_list(ids="1")
            assert "feeds" in result


class TestFeedsAdd:
    """Tests for feeds_add tool."""

    def test_feeds_add_basic(self):
        """Test adding a new feed."""
        mock_result = {
            "id": 1,
            "name": "New Feed",
            "url": "https://example.com/feed.xml",
        }
        with patch(
            "server.tools.feeds.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = feeds_add(name="New Feed", url="https://example.com/feed.xml")
            assert result["name"] == "New Feed"

    def test_feeds_add_with_extra_json(self):
        """Test adding a feed with extra JSON parameters."""
        runner = MagicMock()
        runner.run_json.return_value = {"id": 2}
        with patch(
            "server.tools.feeds.get_runner",
            return_value=runner,
        ):
            feeds_add(
                name="Test",
                url="https://example.com/feed.xml",
                extra_json='{"BusinessType":"RETAIL"}',
            )
            call_args = runner.run_json.call_args[0][0]
            assert "--json" in call_args


class TestFeedsUpdate:
    """Tests for feeds_update tool."""

    def test_feeds_update_name_only(self):
        """Test updating feed name."""
        mock_result = {"id": 1, "name": "Updated Feed"}
        with patch(
            "server.tools.feeds.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = feeds_update(id="1", name="Updated Feed")
            assert result["name"] == "Updated Feed"

    def test_feeds_update_url_only(self):
        """Test updating feed URL."""
        mock_result = {"id": 1, "url": "https://example.com/new.xml"}
        with patch(
            "server.tools.feeds.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = feeds_update(id="1", url="https://example.com/new.xml")
            assert result["url"] == "https://example.com/new.xml"

    def test_feeds_update_extra_json_only(self):
        """Test updating with extra JSON only."""
        runner = MagicMock()
        runner.run_json.return_value = {"id": 1}
        with patch(
            "server.tools.feeds.get_runner",
            return_value=runner,
        ):
            feeds_update(id="1", extra_json='{"Status":"ACTIVE"}')
            call_args = runner.run_json.call_args[0][0]
            assert "--json" in call_args

    def test_feeds_update_nothing(self):
        """Test that updating nothing returns error."""
        result = feeds_update(id="1")
        assert "error" in result
        assert result["error"] == "missing_update_fields"


class TestFeedsDelete:
    """Tests for feeds_delete tool."""

    def test_feeds_delete_success(self):
        """Test deleting feeds successfully."""
        mock_result = {"success": True}
        with patch(
            "server.tools.feeds.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = feeds_delete(ids="1")
            assert result["success"] is True

    def test_feeds_delete_batch_limit(self):
        """Test batch limit validation for feeds_delete."""
        ids = ",".join(str(i) for i in range(1, 12))
        result = feeds_delete(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"
