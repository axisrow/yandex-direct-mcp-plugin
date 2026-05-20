"""Tests for v4forecast MCP tools."""

from unittest.mock import MagicMock, patch

from server.tools.v4forecast import (
    v4forecast_create,
    v4forecast_delete,
    v4forecast_get,
    v4forecast_list,
)


def _mock_runner(return_value):
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


def test_v4forecast_create_argv():
    runner = _mock_runner({"forecast_id": 1})
    with patch("server.tools.v4forecast.get_runner", return_value=runner):
        v4forecast_create(
            phrases="phrase1, phrase2",
            geo_ids="225,1",
            currency="RUB",
        )
    runner.run_json.assert_called_once_with(
        [
            "v4forecast",
            "create",
            "--phrases",
            "phrase1, phrase2",
            "--geo-ids",
            "225,1",
            "--currency",
            "RUB",
            "--format",
            "json",
        ]
    )


def test_v4forecast_create_requires_phrases():
    result = v4forecast_create(phrases="   ")
    assert result["error"] == "missing_phrases"


def test_v4forecast_create_phrase_limit():
    phrases = ",".join(f"p{i}" for i in range(101))
    result = v4forecast_create(phrases=phrases)
    assert result["error"] == "phrases_limit"


def test_v4forecast_create_dry_run():
    runner = _mock_runner({"_dry_run": True})
    with patch("server.tools.v4forecast.get_runner", return_value=runner):
        v4forecast_create(phrases="x", dry_run=True)
        argv = runner.run_json.call_args[0][0]
        assert "--dry-run" in argv


def test_v4forecast_list_argv():
    runner = _mock_runner([])
    with patch("server.tools.v4forecast.get_runner", return_value=runner):
        v4forecast_list()
    runner.run_json.assert_called_once_with(["v4forecast", "list", "--format", "json"])


def test_v4forecast_get_argv():
    runner = _mock_runner({"forecast_id": 42})
    with patch("server.tools.v4forecast.get_runner", return_value=runner):
        v4forecast_get(forecast_id=42)
    runner.run_json.assert_called_once_with(
        [
            "v4forecast",
            "get",
            "--forecast-id",
            "42",
            "--format",
            "json",
        ]
    )


def test_v4forecast_delete_argv():
    runner = _mock_runner({"ok": True})
    with patch("server.tools.v4forecast.get_runner", return_value=runner):
        v4forecast_delete(forecast_id=42)
    runner.run_json.assert_called_once_with(
        [
            "v4forecast",
            "delete",
            "--forecast-id",
            "42",
            "--format",
            "json",
        ]
    )


def test_v4forecast_delete_dry_run():
    runner = _mock_runner({"_dry_run": True})
    with patch("server.tools.v4forecast.get_runner", return_value=runner):
        v4forecast_delete(forecast_id=42, dry_run=True)
        argv = runner.run_json.call_args[0][0]
        assert "--dry-run" in argv
