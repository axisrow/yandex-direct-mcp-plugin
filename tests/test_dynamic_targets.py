"""Tests for dynamic targets MCP tools."""

from unittest.mock import MagicMock, call, patch

import pytest

import server.tools
from server.tools.dynamic_targets import (
    dynamic_targets_add,
    dynamic_targets_delete,
    dynamic_targets_list,
    dynamic_targets_update,
)


@pytest.fixture(autouse=True)
def setup_token_getter():
    server.tools.set_token_getter(lambda: "test-token")


SAMPLE_TARGETS = [
    {"Id": 301, "AdGroupId": 67890, "Name": "Product pages"},
]


def _mock_runner(return_value):
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


class TestDynamicTargetsList:
    def test_list_dynamic_targets_success(self):
        with patch(
            "server.tools.dynamic_targets.get_runner",
            return_value=_mock_runner(SAMPLE_TARGETS),
        ):
            result = dynamic_targets_list(ad_group_ids="67890")
            assert len(result) == 1

    def test_list_dynamic_targets_ignores_blank_ids(self):
        runner = MagicMock()
        runner.run_json.return_value = SAMPLE_TARGETS
        with patch("server.tools.dynamic_targets.get_runner", return_value=runner):
            result = dynamic_targets_list(ad_group_ids="   ")
            assert len(result) == 1
            call_args = runner.run_json.call_args[0][0]
            assert "--adgroup-ids" not in call_args

    def test_list_dynamic_targets_no_ids(self):
        with patch(
            "server.tools.dynamic_targets.get_runner",
            return_value=_mock_runner(SAMPLE_TARGETS),
        ):
            result = dynamic_targets_list()
            assert len(result) == 1

    def test_list_dynamic_targets_batch_limit(self):
        ids = ",".join(str(i) for i in range(1, 12))
        result = dynamic_targets_list(ad_group_ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"


class TestDynamicTargetsAdd:
    def test_add_dynamic_target_success(self):
        mock_result = {"Id": 303}
        target_data = '{"Name": "Test", "Conditions": []}'
        with patch(
            "server.tools.dynamic_targets.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = dynamic_targets_add(ad_group_id="67892", target_data=target_data)
            assert result["Id"] == 303


class TestDynamicTargetsUpdate:
    def test_update_dynamic_target(self):
        mock_result = {"Id": 301}
        with patch(
            "server.tools.dynamic_targets.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = dynamic_targets_update(id="301", extra_json='{"Conditions": []}')
            assert result["Id"] == 301

    def test_update_dynamic_target_argv_composition(self):
        runner = _mock_runner({"Id": 301})
        with patch("server.tools.dynamic_targets.get_runner", return_value=runner):
            dynamic_targets_update(id="301", extra_json='{"Conditions": []}')
            runner.run_json.assert_called_once_with(
                [
                    "dynamictargets",
                    "update",
                    "--id",
                    "301",
                    "--json",
                    '{"Conditions": []}',
                    "--format",
                    "json",
                ]
            )


class TestDynamicTargetsDelete:
    def test_delete_dynamic_targets_success(self):
        mock_result = {"success": True}
        with patch(
            "server.tools.dynamic_targets.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = dynamic_targets_delete(ids="301")
            assert result["success"] is True

    def test_delete_dynamic_targets_batches_multiple_ids(self):
        runner = MagicMock()
        runner.run_json.return_value = {"success": True}
        with patch("server.tools.dynamic_targets.get_runner", return_value=runner):
            result = dynamic_targets_delete(ids="301,302")

        assert result["success"] is True
        assert result["ids"] == ["301", "302"]
        assert runner.run_json.call_args_list == [
            call(["dynamictargets", "delete", "--id", "301"]),
            call(["dynamictargets", "delete", "--id", "302"]),
        ]

    def test_delete_dynamic_targets_batch_limit(self):
        ids = ",".join(str(i) for i in range(1, 12))
        result = dynamic_targets_delete(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"
