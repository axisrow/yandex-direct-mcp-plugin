"""Tests for dynamic_ads MCP tools."""

from unittest.mock import patch, MagicMock

import pytest

import server.tools
from server.tools.dynamic_ads import (
    dynamic_ads_list,
    dynamic_ads_add,
    dynamic_ads_update,
    dynamic_ads_delete,
)


@pytest.fixture(autouse=True)
def setup():
    server.tools.set_token_getter(lambda: "test-token")


SAMPLE_TARGETS = [
    {
        "Id": 100,
        "AdGroupId": 200,
        "Conditions": [
            {"Operand": "URL", "Operator": "CONTAINS", "Arguments": ["sale"]}
        ],
    },
]


def _mock_runner(return_value):
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


def test_dynamic_ads_list():
    with patch(
        "server.tools.dynamic_ads.get_runner", return_value=_mock_runner(SAMPLE_TARGETS)
    ):
        result = dynamic_ads_list(ad_group_ids="200")
        assert len(result) == 1


def test_dynamic_ads_list_empty():
    with patch("server.tools.dynamic_ads.get_runner", return_value=_mock_runner([])):
        result = dynamic_ads_list(ad_group_ids="200")
        assert result == []


def test_dynamic_ads_add():
    mock_result = {"Id": 300}
    with patch("server.tools.dynamic_ads.get_runner", return_value=_mock_runner(mock_result)):
        result = dynamic_ads_add(
            ad_group_id="200", target_data='{"Name": "Test", "Conditions": []}'
        )
        assert result["Id"] == 300


def test_dynamic_ads_update():
    mock_result = {"success": True}
    with patch("server.tools.dynamic_ads.get_runner", return_value=_mock_runner(mock_result)):
        result = dynamic_ads_update(id="100", extra_json='{"Conditions": []}')
        assert result["success"] is True


def test_dynamic_ads_delete():
    mock_result = {"success": True}
    with patch("server.tools.dynamic_ads.get_runner", return_value=_mock_runner(mock_result)):
        result = dynamic_ads_delete(id="100")
        assert result["success"] is True
