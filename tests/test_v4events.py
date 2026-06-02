"""Tests for v4events MCP tools."""

from unittest.mock import patch

from server.tools.v4events import v4events_get_events_log

from tests.helpers import mock_runner


def test_v4events_get_events_log_argv():
    runner = mock_runner({"Events": []})
    with patch("server.tools.v4events.get_runner", return_value=runner):
        v4events_get_events_log(
            timestamp_from=" 2026-05-01T00:00:00 ",
            timestamp_to=" 2026-05-02T00:00:00 ",
            currency="USD",
            limit=100,
            offset=20,
        )
    runner.run_json.assert_called_once_with(
        [
            "v4events",
            "get-events-log",
            "--from",
            "2026-05-01T00:00:00",
            "--to",
            "2026-05-02T00:00:00",
            "--currency",
            "USD",
            "--limit",
            "100",
            "--offset",
            "20",
            "--format",
            "json",
        ]
    )


def test_v4events_get_events_log_requires_timestamps():
    result = v4events_get_events_log(
        timestamp_from="   ",
        timestamp_to="2026-05-02T00:00:00",
    )
    assert result["error"] == "missing_timestamp"
    result = v4events_get_events_log(
        timestamp_from="2026-05-01T00:00:00",
        timestamp_to="",
    )
    assert result["error"] == "missing_timestamp"


def test_v4events_get_events_log_dry_run():
    runner = mock_runner({"method": "GetEventsLog"})
    with patch("server.tools.v4events.get_runner", return_value=runner):
        v4events_get_events_log(
            timestamp_from="2026-05-01T00:00:00",
            timestamp_to="2026-05-02T00:00:00",
            dry_run=True,
        )
    argv = runner.run_json.call_args.args[0]
    assert "--dry-run" in argv
