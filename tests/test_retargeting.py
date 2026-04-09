"""Tests for retargeting MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

import server.tools
from server.tools.retargeting import (
    retargeting_add,
    retargeting_delete,
    retargeting_list,
)
from server.cli.runner import CliAuthError


@pytest.fixture(autouse=True)
def setup_token_getter():
    """Configure a mock token getter for all tests."""
    server.tools.set_token_getter(lambda: "test-token")


@pytest.fixture
def mock_retargeting_lists():
    """Sample retargeting list data."""
    return [
        {
            "Id": 201,
            "Name": "Visitors who viewed product page",
            "Type": "REMARKETING",
            "State": "ON",
        },
        {
            "Id": 202,
            "Name": "Cart abandoners",
            "Type": "REMARKETING",
            "State": "ON",
        },
    ]


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


class TestRetargetingList:
    """Tests for retargeting_list."""

    def test_list_retargeting_success(self, mock_retargeting_lists):
        """Test listing retargeting lists successfully."""
        with patch(
            "server.tools.retargeting.get_runner",
            return_value=_mock_runner(mock_retargeting_lists),
        ):
            result = retargeting_list(ids="201,202")
            assert len(result) == 2

    def test_list_retargeting_empty(self):
        """Test listing retargeting lists with empty result."""
        with patch(
            "server.tools.retargeting.get_runner", return_value=_mock_runner([])
        ):
            result = retargeting_list(ids="201")
            assert result == []

    def test_list_retargeting_auth_error(self):
        """Test auth error during retargeting list."""
        runner = MagicMock()
        runner.run_json.side_effect = CliAuthError("Token expired")
        with (
            patch("server.tools.retargeting.get_runner", return_value=runner),
            patch("server.tools._try_refresh_token", return_value=None),
        ):
            result = retargeting_list(ids="201")
            assert result["error"] == "auth_expired"


class TestRetargetingAdd:
    """Tests for retargeting_add."""

    def test_add_retargeting_success(self):
        """Test adding a retargeting list successfully."""
        mock_result = {
            "Id": 203,
            "Name": "Site visitors",
            "Type": "REMARKETING",
            "State": "ON",
        }
        rule = '{"conditions": [{"operator": "AND", "operands": [{"type": "time_on_site", "time_on_site": 30}]}]}'
        with patch(
            "server.tools.retargeting.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = retargeting_add(name="Site visitors", rule=rule)
            assert result["Id"] == 203
            assert result["Name"] == "Site visitors"

    def test_add_retargeting_auth_error(self):
        """Test auth error during retargeting add."""
        runner = MagicMock()
        runner.run_json.side_effect = CliAuthError("Token expired")
        with (
            patch("server.tools.retargeting.get_runner", return_value=runner),
            patch("server.tools._try_refresh_token", return_value=None),
        ):
            result = retargeting_add(name="Test", rule="{}")
            assert result["error"] == "auth_expired"


class TestRetargetingDelete:
    """Tests for retargeting_delete."""

    def test_delete_retargeting_success(self):
        """Test deleting retargeting lists successfully."""
        mock_result = {"success": True}
        with patch(
            "server.tools.retargeting.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = retargeting_delete(ids="201,202")
            assert result["success"] is True

    def test_delete_retargeting_batch_limit(self):
        """Test batch limit validation for delete."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = retargeting_delete(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_delete_retargeting_auth_error(self):
        """Test auth error during retargeting delete."""
        runner = MagicMock()
        runner.run_json.side_effect = CliAuthError("Token expired")
        with (
            patch("server.tools.retargeting.get_runner", return_value=runner),
            patch("server.tools._try_refresh_token", return_value=None),
        ):
            result = retargeting_delete(ids="201")
            assert result["error"] == "auth_expired"
