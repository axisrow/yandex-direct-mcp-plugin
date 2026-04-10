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


def test_dynamic_ads_list_trims_ids():
    runner = _mock_runner(SAMPLE_TARGETS)
    with patch("server.tools.dynamic_ads.get_runner", return_value=runner):
        dynamic_ads_list(ad_group_ids=" 200 ")

    runner.run_json.assert_called_once_with(
        [
            "dynamicads",
            "get",
            "--adgroup-ids",
            "200",
            "--format",
            "json",
        ]
    )


def test_dynamic_ads_list_requires_ids():
    result = dynamic_ads_list(ad_group_ids="   ")
    assert result["error"] == "missing_ad_group_ids"


def test_dynamic_ads_list_empty():
    with patch("server.tools.dynamic_ads.get_runner", return_value=_mock_runner([])):
        result = dynamic_ads_list(ad_group_ids="200")
        assert result == []


def test_dynamic_ads_add():
    mock_result = {"Id": 300}
    with patch(
        "server.tools.dynamic_ads.get_runner", return_value=_mock_runner(mock_result)
    ) as mock:
        result = dynamic_ads_add(
            ad_group_id="200", target_data='{"Name": "Test", "Conditions": []}'
        )
        assert result["Id"] == 300
        mock.return_value.run_json.assert_called_once_with(
            [
                "dynamicads",
                "add",
                "--adgroup-id",
                "200",
                "--json",
                '{"Name": "Test", "Conditions": []}',
            ]
        )


def test_dynamic_ads_update():
    mock_result = {"success": True}
    with patch(
        "server.tools.dynamic_ads.get_runner", return_value=_mock_runner(mock_result)
    ) as mock:
        result = dynamic_ads_update(id="100", extra_json='{"Conditions": []}')
        assert result["success"] is True
        mock.return_value.run_json.assert_called_once_with(
            ["dynamicads", "update", "--id", "100", "--json", '{"Conditions": []}']
        )


def test_dynamic_ads_delete():
    mock_result = {"success": True}
    with patch(
        "server.tools.dynamic_ads.get_runner", return_value=_mock_runner(mock_result)
    ) as mock:
        result = dynamic_ads_delete(id="100")
        assert result["success"] is True
        mock.return_value.run_json.assert_called_once_with(
            ["dynamicads", "delete", "--id", "100"]
        )


class TestDynamicAdsAuthErrors:
    """Auth error scenarios for dynamic ads."""

    def test_dynamic_ads_list_auth_error(self):
        """Test auth error during list."""
        from server.cli.runner import CliAuthError

        runner = MagicMock()
        runner.run_json.side_effect = CliAuthError("Token expired")
        with (
            patch("server.tools.dynamic_ads.get_runner", return_value=runner),
            patch("server.tools._try_refresh_token", return_value=None),
        ):
            result = dynamic_ads_list(ad_group_ids="200")
            assert result["error"] == "auth_expired"

    def test_dynamic_ads_add_auth_error(self):
        """Test auth error during add."""
        from server.cli.runner import CliAuthError

        runner = MagicMock()
        runner.run_json.side_effect = CliAuthError("Token expired")
        with (
            patch("server.tools.dynamic_ads.get_runner", return_value=runner),
            patch("server.tools._try_refresh_token", return_value=None),
        ):
            result = dynamic_ads_add(
                ad_group_id="200", target_data='{"Name": "Test"}'
            )
            assert result["error"] == "auth_expired"

    def test_dynamic_ads_update_auth_error(self):
        """Test auth error during update."""
        from server.cli.runner import CliAuthError

        runner = MagicMock()
        runner.run_json.side_effect = CliAuthError("Token expired")
        with (
            patch("server.tools.dynamic_ads.get_runner", return_value=runner),
            patch("server.tools._try_refresh_token", return_value=None),
        ):
            result = dynamic_ads_update(id="100", extra_json='{"Name": "Test"}')
            assert result["error"] == "auth_expired"

    def test_dynamic_ads_delete_auth_error(self):
        """Test auth error during delete."""
        from server.cli.runner import CliAuthError

        runner = MagicMock()
        runner.run_json.side_effect = CliAuthError("Token expired")
        with (
            patch("server.tools.dynamic_ads.get_runner", return_value=runner),
            patch("server.tools._try_refresh_token", return_value=None),
        ):
            result = dynamic_ads_delete(id="100")
            assert result["error"] == "auth_expired"
