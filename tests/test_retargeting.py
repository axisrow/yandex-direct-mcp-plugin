"""Tests for retargeting MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

import server.tools
from server.tools.retargeting import (
    retargeting_add,
    retargeting_delete,
    retargeting_list,
    retargeting_update,
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

    def test_list_retargeting_no_ids(self, mock_retargeting_lists):
        """Test listing all retargeting lists."""
        with patch(
            "server.tools.retargeting.get_runner",
            return_value=_mock_runner(mock_retargeting_lists),
        ):
            result = retargeting_list()
            assert len(result) == 2

    def test_list_retargeting_with_types(self):
        """Test listing retargeting lists filtered by types."""
        runner = MagicMock()
        runner.run_json.return_value = []
        with patch(
            "server.tools.retargeting.get_runner",
            return_value=runner,
        ):
            retargeting_list(types="REMARKETING")
            call_args = runner.run_json.call_args[0][0]
            assert "--types" in call_args

    def test_list_retargeting_trims_filters(self):
        """Test retargeting filters are normalized before argv construction."""
        runner = MagicMock()
        runner.run_json.return_value = []
        with patch("server.tools.retargeting.get_runner", return_value=runner):
            retargeting_list(ids=" 201,202 ", types=" REMARKETING ")

        runner.run_json.assert_called_once_with(
            [
                "retargeting",
                "get",
                "--format",
                "json",
                "--ids",
                "201,202",
                "--types",
                "REMARKETING",
            ]
        )

    def test_list_retargeting_auth_error(self):
        """Test auth error during retargeting list."""
        runner = MagicMock()
        runner.run_json.side_effect = CliAuthError("Token expired")
        with (
            patch(
                "server.tools.retargeting.get_runner",
                return_value=runner,
            ),
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
            "Type": "AUDIENCE_SEGMENT",
            "State": "ON",
        }
        runner = MagicMock()
        runner.run_json.return_value = mock_result
        with patch(
            "server.tools.retargeting.get_runner",
            return_value=runner,
        ):
            result = retargeting_add(
                name="Site visitors",
                list_type="AUDIENCE_SEGMENT",
            )
            assert result["Id"] == 203
            call_args = runner.run_json.call_args[0][0]
            assert "--name" in call_args
            assert "--type" in call_args

    def test_add_retargeting_with_extra_json(self):
        """Test adding with extra JSON parameters."""
        runner = MagicMock()
        runner.run_json.return_value = {"Id": 204}
        with patch(
            "server.tools.retargeting.get_runner",
            return_value=runner,
        ):
            retargeting_add(
                name="Test",
                list_type="AUDIENCE_SEGMENT",
                extra_json='{"Description":"test"}',
            )
            call_args = runner.run_json.call_args[0][0]
            assert "--json" in call_args

    def test_add_retargeting_auth_error(self):
        """Test auth error during retargeting add."""
        runner = MagicMock()
        runner.run_json.side_effect = CliAuthError("Token expired")
        with (
            patch(
                "server.tools.retargeting.get_runner",
                return_value=runner,
            ),
            patch("server.tools._try_refresh_token", return_value=None),
        ):
            result = retargeting_add(name="Test", list_type="AUDIENCE_SEGMENT")
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
            result = retargeting_delete(ids="201")
            assert result["success"] is True

    def test_delete_retargeting_batch_limit(self):
        """Test batch limit validation for delete."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = retargeting_delete(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"


class TestRetargetingUpdate:
    """Tests for retargeting_update."""

    def test_update_retargeting_success(self):
        runner = MagicMock()
        runner.run_json.return_value = {"success": True}
        with patch("server.tools.retargeting.get_runner", return_value=runner):
            result = retargeting_update(
                id="201",
                name="Updated",
                list_type="AUDIENCE",
            )

        assert result["success"] is True
        runner.run_json.assert_called_once_with(
            [
                "retargeting",
                "update",
                "--id",
                "201",
                "--name",
                "Updated",
                "--type",
                "AUDIENCE",
            ]
        )

    def test_update_retargeting_requires_changes(self):
        result = retargeting_update(id="201")
        assert result["error"] == "missing_update_fields"
