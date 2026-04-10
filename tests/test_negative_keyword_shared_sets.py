"""Tests for negative_keyword_shared_sets MCP tools."""

from unittest.mock import patch, MagicMock

import pytest

import server.tools
from server.tools.negative_keyword_shared_sets import (
    negative_keyword_shared_sets_list,
    negative_keyword_shared_sets_add,
    negative_keyword_shared_sets_update,
    negative_keyword_shared_sets_delete,
)


@pytest.fixture(autouse=True)
def setup():
    server.tools.set_token_getter(lambda: "test-token")


SAMPLE_SETS = [
    {"Id": 100, "Name": "Block list", "NegativeKeywords": ["free", "cheap"]},
]


def _mock_runner(return_value):
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


def test_nkss_list():
    with patch(
        "server.tools.negative_keyword_shared_sets.get_runner",
        return_value=_mock_runner(SAMPLE_SETS),
    ):
        result = negative_keyword_shared_sets_list()
        assert len(result) == 1


def test_nkss_list_with_ids():
    with patch(
        "server.tools.negative_keyword_shared_sets.get_runner",
        return_value=_mock_runner(SAMPLE_SETS),
    ):
        result = negative_keyword_shared_sets_list(ids="100")
        assert len(result) == 1


def test_nkss_list_trims_ids():
    runner = _mock_runner(SAMPLE_SETS)
    with patch(
        "server.tools.negative_keyword_shared_sets.get_runner",
        return_value=runner,
    ):
        negative_keyword_shared_sets_list(ids=" 100 ")

    runner.run_json.assert_called_once_with(
        [
            "negativekeywordsharedsets",
            "get",
            "--format",
            "json",
            "--ids",
            "100",
        ]
    )


def test_nkss_list_empty():
    with patch(
        "server.tools.negative_keyword_shared_sets.get_runner",
        return_value=_mock_runner([]),
    ):
        result = negative_keyword_shared_sets_list()
        assert result == []


def test_nkss_add():
    mock_result = {"Id": 200}
    with patch(
        "server.tools.negative_keyword_shared_sets.get_runner",
        return_value=_mock_runner(mock_result),
    ) as mock:
        result = negative_keyword_shared_sets_add(name="New list", keywords="bad,word")
        assert result["Id"] == 200
        mock.return_value.run_json.assert_called_once_with(
            [
                "negativekeywordsharedsets",
                "add",
                "--name",
                "New list",
                "--keywords",
                "bad,word",
            ]
        )


def test_nkss_update():
    mock_result = {"success": True}
    with patch(
        "server.tools.negative_keyword_shared_sets.get_runner",
        return_value=_mock_runner(mock_result),
    ) as mock:
        result = negative_keyword_shared_sets_update(
            id="100", name="Updated", extra_json='{"Keywords":["bad"]}'
        )
        assert result["success"] is True
        mock.return_value.run_json.assert_called_once_with(
            [
                "negativekeywordsharedsets",
                "update",
                "--id",
                "100",
                "--name",
                "Updated",
                "--json",
                '{"Keywords":["bad"]}',
            ]
        )


def test_nkss_update_requires_changes():
    runner = _mock_runner({"success": True})
    with patch(
        "server.tools.negative_keyword_shared_sets.get_runner", return_value=runner
    ):
        result = negative_keyword_shared_sets_update(id="100")
        assert result["error"] == "missing_update_fields"
        runner.run_json.assert_not_called()


def test_nkss_delete():
    mock_result = {"success": True}
    with patch(
        "server.tools.negative_keyword_shared_sets.get_runner",
        return_value=_mock_runner(mock_result),
    ) as mock:
        result = negative_keyword_shared_sets_delete(id="100")
        assert result["success"] is True
        mock.return_value.run_json.assert_called_once_with(
            ["negativekeywordsharedsets", "delete", "--id", "100"]
        )
