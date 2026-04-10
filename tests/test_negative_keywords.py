"""Tests for negative keyword MCP tools."""

from unittest.mock import MagicMock, call, patch

import pytest

import server.tools
from server.tools.negative_keywords import (
    negative_keywords_list,
    negative_keywords_add,
    negative_keywords_update,
    negative_keywords_delete,
)


@pytest.fixture(autouse=True)
def setup():
    server.tools.set_token_getter(lambda: "test-token")


SAMPLE_SETS = [
    {"Id": 1, "Name": "Bad words", "Keywords": "bad, awful"},
]


def _mock_runner(return_value):
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


def test_negative_keywords_list():
    """Test listing negative keyword sets."""
    with patch(
        "server.tools.negative_keywords.get_runner",
        return_value=_mock_runner(SAMPLE_SETS),
    ):
        result = negative_keywords_list(ids="1")
        assert len(result) == 1
        assert result[0]["Id"] == 1


def test_negative_keywords_list_no_ids():
    """Test listing all negative keyword sets."""
    with patch(
        "server.tools.negative_keywords.get_runner",
        return_value=_mock_runner(SAMPLE_SETS),
    ):
        result = negative_keywords_list()
        assert len(result) == 1


def test_negative_keywords_list_ignores_blank_ids():
    """Test blank ids behave like no filter."""
    runner = MagicMock()
    runner.run_json.return_value = SAMPLE_SETS
    with patch("server.tools.negative_keywords.get_runner", return_value=runner):
        result = negative_keywords_list(ids="   ")
        assert len(result) == 1
        call_args = runner.run_json.call_args[0][0]
        assert "--ids" not in call_args


def test_negative_keywords_add():
    """Test adding a negative keyword set."""
    mock_result = {"Id": 1}
    with patch(
        "server.tools.negative_keywords.get_runner",
        return_value=_mock_runner(mock_result),
    ):
        result = negative_keywords_add(name="Bad words", keywords="bad, awful")
        assert result["Id"] == 1


def test_negative_keywords_use_canonical_cli_surface():
    """Legacy wrapper should call canonical shared-set command."""
    runner = MagicMock()
    runner.run_json.return_value = SAMPLE_SETS
    with patch("server.tools.negative_keywords.get_runner", return_value=runner):
        negative_keywords_list(ids="1")
        negative_keywords_add(name="Bad words", keywords="bad, awful")
        negative_keywords_update(id="1", name="Updated")

    assert runner.run_json.call_args_list[0][0][0][0] == "negativekeywordsharedsets"
    assert runner.run_json.call_args_list[1][0][0][0] == "negativekeywordsharedsets"
    assert runner.run_json.call_args_list[2][0][0][0] == "negativekeywordsharedsets"


def test_negative_keywords_update():
    """Test updating a negative keyword set."""
    mock_result = {"success": True}
    with patch(
        "server.tools.negative_keywords.get_runner",
        return_value=_mock_runner(mock_result),
    ):
        result = negative_keywords_update(id="1", name="Updated")
        assert result["success"] is True


class TestNegativeKeywordsDelete:
    """Tests for negative keyword delete operations."""

    def test_negative_keywords_delete_success(self):
        mock_result = {"success": True}
        with patch(
            "server.tools.negative_keywords.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = negative_keywords_delete(ids="1")
            assert result["success"] is True

    def test_negative_keywords_delete_batches_multiple_ids(self):
        runner = MagicMock()
        runner.run_json.return_value = {"success": True}
        with patch("server.tools.negative_keywords.get_runner", return_value=runner):
            result = negative_keywords_delete(ids="1,2")

        assert result["success"] is True
        assert result["ids"] == ["1", "2"]
        assert runner.run_json.call_args_list == [
            call(["negativekeywordsharedsets", "delete", "--id", "1"]),
            call(["negativekeywordsharedsets", "delete", "--id", "2"]),
        ]

    def test_negative_keywords_delete_batch_limit(self):
        ids = ",".join(str(i) for i in range(1, 12))
        result = negative_keywords_delete(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"
