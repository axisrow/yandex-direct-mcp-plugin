"""Tests for smart target MCP tools."""

from unittest.mock import patch, MagicMock

import pytest

import server.tools
from server.tools.smart_targets import (
    smart_targets_list,
    smart_targets_add,
    smart_targets_update,
    smart_targets_delete,
)


@pytest.fixture(autouse=True)
def setup():
    server.tools.set_token_getter(lambda: "test-token")


SAMPLE_SMART_TARGETS = [
    {
        "Id": 1,
        "AdGroupId": 100,
        "Conditions": '{"RetargetingListId": "123"}',
    },
]


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


def test_smart_targets_list():
    """Test listing smart targets."""
    with patch(
        "server.tools.smart_targets.get_runner",
        return_value=_mock_runner(SAMPLE_SMART_TARGETS),
    ):
        result = smart_targets_list(ad_group_ids="100,101")
        assert len(result) == 1
        assert result[0]["Id"] == 1
        assert result[0]["AdGroupId"] == 100


def test_smart_targets_add():
    """Test adding smart target."""
    conditions = '{"RetargetingListId": "123"}'
    mock_result = {"success": True, "id": 1}
    with patch(
        "server.tools.smart_targets.get_runner",
        return_value=_mock_runner(mock_result),
    ):
        result = smart_targets_add(ad_group_id="100", conditions=conditions)
        assert result["success"] is True
        assert result["id"] == 1


def test_smart_targets_add_invalid_json():
    """Test adding smart target with invalid JSON."""
    result = smart_targets_add(ad_group_id="100", conditions="invalid json")
    assert "error" in result
    assert result["error"] == "invalid_json"


def test_smart_targets_update():
    """Test updating smart target."""
    conditions = '{"RetargetingListId": "456"}'
    mock_result = {"success": True, "id": 1}
    with patch(
        "server.tools.smart_targets.get_runner",
        return_value=_mock_runner(mock_result),
    ):
        result = smart_targets_update(id="1", conditions=conditions)
        assert result["success"] is True
        assert result["id"] == 1


def test_smart_targets_update_invalid_json():
    """Test updating smart target with invalid JSON."""
    result = smart_targets_update(id="1", conditions="not json")
    assert "error" in result
    assert result["error"] == "invalid_json"


def test_smart_targets_update_missing_conditions():
    """Test updating smart target without conditions."""
    result = smart_targets_update(id="1", conditions=None)
    assert "error" in result
    assert result["error"] == "missing_conditions"


class TestSmartTargetsDelete:
    """Tests for smart target delete operations."""

    def test_smart_targets_delete_success(self):
        """Test deleting smart targets successfully."""
        mock_result = {"success": True}
        with patch(
            "server.tools.smart_targets.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = smart_targets_delete(ids="1,2")
            assert result["success"] is True

    def test_smart_targets_delete_batch_limit(self):
        """Test batch limit validation for delete."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = smart_targets_delete(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"
