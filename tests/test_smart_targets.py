"""Tests for smart target MCP tools."""

from unittest.mock import MagicMock, call, patch

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


SAMPLE_TARGETS = [
    {"Id": 1, "AdGroupId": 100, "Type": "RETARGETING"},
]


def _mock_runner(return_value):
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


def test_smart_targets_list():
    """Test listing smart targets."""
    with patch(
        "server.tools.smart_targets.get_runner",
        return_value=_mock_runner(SAMPLE_TARGETS),
    ):
        result = smart_targets_list(ad_group_ids="100")
        assert len(result) == 1


def test_smart_targets_use_canonical_cli_surface():
    """Legacy wrapper should call canonical smartadtargets command."""
    runner = MagicMock()
    runner.run_json.return_value = {"success": True}
    with patch("server.tools.smart_targets.get_runner", return_value=runner):
        smart_targets_list(ad_group_ids="100")
        smart_targets_add(ad_group_id="100", target_type="RETARGETING")
        smart_targets_update(id="1", extra_json='{"Condition":"URL_CONTAINS"}')
        smart_targets_delete(ids="1")

    assert runner.run_json.call_args_list[0][0][0][0] == "smartadtargets"
    assert runner.run_json.call_args_list[1][0][0][0] == "smartadtargets"
    assert runner.run_json.call_args_list[2][0][0][0] == "smartadtargets"
    assert runner.run_json.call_args_list[3][0][0][0] == "smartadtargets"


def test_smart_targets_list_ignores_blank_ids():
    """Test blank ad group IDs behave like no filter."""
    runner = MagicMock()
    runner.run_json.return_value = SAMPLE_TARGETS
    with patch("server.tools.smart_targets.get_runner", return_value=runner):
        result = smart_targets_list(ad_group_ids="   ")
        assert len(result) == 1
        call_args = runner.run_json.call_args[0][0]
        assert "--adgroup-ids" not in call_args


def test_smart_targets_list_no_ids():
    """Test listing all smart targets."""
    with patch(
        "server.tools.smart_targets.get_runner",
        return_value=_mock_runner(SAMPLE_TARGETS),
    ):
        result = smart_targets_list()
        assert len(result) == 1


def test_smart_targets_add():
    """Test adding smart target."""
    mock_result = {"Id": 1}
    with patch(
        "server.tools.smart_targets.get_runner",
        return_value=_mock_runner(mock_result),
    ):
        result = smart_targets_add(ad_group_id="100", target_type="RETARGETING")
        assert result["Id"] == 1


def test_smart_targets_update():
    """Test updating smart target."""
    mock_result = {"success": True}
    with patch(
        "server.tools.smart_targets.get_runner",
        return_value=_mock_runner(mock_result),
    ):
        result = smart_targets_update(id="1", extra_json='{"Condition":"URL_CONTAINS"}')
        assert result["success"] is True


def test_smart_targets_update_requires_fields():
    """Test missing smart target update fields returns a local error."""
    result = smart_targets_update(id="1")
    assert result["error"] == "missing_update_fields"


class TestSmartTargetsDelete:
    """Tests for smart target delete operations."""

    def test_smart_targets_delete_success(self):
        mock_result = {"success": True}
        with patch(
            "server.tools.smart_targets.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = smart_targets_delete(ids="1")
            assert result["success"] is True

    def test_smart_targets_delete_batches_multiple_ids(self):
        runner = MagicMock()
        runner.run_json.return_value = {"success": True}
        with patch("server.tools.smart_targets.get_runner", return_value=runner):
            result = smart_targets_delete(ids="1,2")

        assert result["success"] is True
        assert result["ids"] == ["1", "2"]
        assert runner.run_json.call_args_list == [
            call(["smartadtargets", "delete", "--id", "1"]),
            call(["smartadtargets", "delete", "--id", "2"]),
        ]

    def test_smart_targets_delete_batch_limit(self):
        ids = ",".join(str(i) for i in range(1, 12))
        result = smart_targets_delete(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"
