"""Tests for dynamic targets MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

import server.tools
from server.tools.dynamic_targets import (
    dynamic_targets_add,
    dynamic_targets_delete,
    dynamic_targets_list,
    dynamic_targets_update,
)
from server.cli.runner import CliAuthError


@pytest.fixture(autouse=True)
def setup_token_getter():
    """Configure a mock token getter for all tests."""
    server.tools.set_token_getter(lambda: "test-token")


@pytest.fixture
def mock_dynamic_targets():
    """Sample dynamic target data."""
    return [
        {
            "Id": 301,
            "AdGroupId": 67890,
            "Conditions": '{"type": "page", "url": "https://example.com/product"}',
            "State": "ON",
        },
        {
            "Id": 302,
            "AdGroupId": 67891,
            "Conditions": '{"type": "query", "text": "buy shoes"}',
            "State": "ON",
        },
    ]


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


class TestDynamicTargetsList:
    """Tests for dynamic_targets_list."""

    def test_list_dynamic_targets_success(self, mock_dynamic_targets):
        """Test listing dynamic targets successfully."""
        with patch(
            "server.tools.dynamic_targets.get_runner",
            return_value=_mock_runner(mock_dynamic_targets),
        ):
            result = dynamic_targets_list(ad_group_ids="67890,67891")
            assert len(result) == 2

    def test_list_dynamic_targets_empty(self):
        """Test listing dynamic targets with empty result."""
        with patch(
            "server.tools.dynamic_targets.get_runner", return_value=_mock_runner([])
        ):
            result = dynamic_targets_list(ad_group_ids="67890")
            assert result == []

    def test_list_dynamic_targets_batch_limit(self):
        """Test batch limit validation for list."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = dynamic_targets_list(ad_group_ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"


class TestDynamicTargetsAdd:
    """Tests for dynamic_targets_add."""

    def test_add_dynamic_target_success(self):
        """Test adding a dynamic target successfully."""
        mock_result = {
            "Id": 303,
            "AdGroupId": 67892,
            "Conditions": '{"type": "page", "url": "https://example.com/special"}',
            "State": "ON",
        }
        conditions = '{"type": "page", "url": "https://example.com/special"}'
        with patch(
            "server.tools.dynamic_targets.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = dynamic_targets_add(ad_group_id="67892", conditions=conditions)
            assert result["Id"] == 303
            assert result["AdGroupId"] == 67892

    def test_add_dynamic_target_auth_error(self):
        """Test auth error during dynamic target add."""
        runner = MagicMock()
        runner.run_json.side_effect = CliAuthError("Token expired")
        with (
            patch("server.tools.dynamic_targets.get_runner", return_value=runner),
            patch("server.tools._try_refresh_token", return_value=None),
        ):
            result = dynamic_targets_add(ad_group_id="67892", conditions="{}")
            assert result["error"] == "auth_expired"


class TestDynamicTargetsUpdate:
    """Tests for dynamic_targets_update."""

    def test_update_dynamic_target_with_conditions(self):
        """Test updating a dynamic target with new conditions."""
        mock_result = {
            "Id": 301,
            "AdGroupId": 67890,
            "Conditions": '{"type": "page", "url": "https://example.com/new"}',
            "State": "ON",
        }
        conditions = '{"type": "page", "url": "https://example.com/new"}'
        with patch(
            "server.tools.dynamic_targets.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = dynamic_targets_update(id="301", conditions=conditions)
            assert result["Id"] == 301

    def test_update_dynamic_target_argv_composition(self):
        """Test that update passes correct argv to CLI."""
        runner = _mock_runner({"Id": 301})
        conditions = '{"type": "page", "url": "https://example.com/new"}'
        with patch("server.tools.dynamic_targets.get_runner", return_value=runner):
            dynamic_targets_update(id="301", conditions=conditions)
            runner.run_json.assert_called_once_with(
                ["dynamictargets", "update", "--id", "301", "--conditions", conditions, "--format", "json"]
            )

    def test_update_dynamic_target_auth_error(self):
        """Test auth error during dynamic target update."""
        runner = MagicMock()
        runner.run_json.side_effect = CliAuthError("Token expired")
        with (
            patch("server.tools.dynamic_targets.get_runner", return_value=runner),
            patch("server.tools._try_refresh_token", return_value=None),
        ):
            result = dynamic_targets_update(id="301", conditions="{}")
            assert result["error"] == "auth_expired"


class TestDynamicTargetsDelete:
    """Tests for dynamic_targets_delete."""

    def test_delete_dynamic_targets_success(self):
        """Test deleting dynamic targets successfully."""
        mock_result = {"success": True}
        with patch(
            "server.tools.dynamic_targets.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = dynamic_targets_delete(ids="301,302")
            assert result["success"] is True

    def test_delete_dynamic_targets_batch_limit(self):
        """Test batch limit validation for delete."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = dynamic_targets_delete(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_delete_dynamic_targets_auth_error(self):
        """Test auth error during dynamic target delete."""
        runner = MagicMock()
        runner.run_json.side_effect = CliAuthError("Token expired")
        with (
            patch("server.tools.dynamic_targets.get_runner", return_value=runner),
            patch("server.tools._try_refresh_token", return_value=None),
        ):
            result = dynamic_targets_delete(ids="301")
            assert result["error"] == "auth_expired"
