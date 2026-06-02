"""Tests for v4wordstat MCP tools."""

from unittest.mock import patch

from server.cli.runner import DirectCliRunner
from server.tools.v4wordstat import (
    v4wordstat_create_report,
    v4wordstat_delete_report,
    v4wordstat_get_report,
    v4wordstat_list_reports,
)

from tests.helpers import completed, mock_runner


def test_v4wordstat_create_report_argv():
    runner = mock_runner({"ReportID": 1})
    with patch("server.tools.v4wordstat.get_runner", return_value=runner):
        v4wordstat_create_report(
            phrases=" phrase one, phrase two ",
            geo_ids=" 225,1 ",
        )
    runner.run_json.assert_called_once_with(
        [
            "v4wordstat",
            "create-report",
            "--phrases",
            "phrase one, phrase two",
            "--geo-ids",
            "225,1",
            "--format",
            "json",
        ]
    )


def test_v4wordstat_create_report_requires_phrases():
    result = v4wordstat_create_report(phrases="   ")
    assert result["error"] == "missing_phrases"


def test_v4wordstat_create_report_rejects_only_separators():
    result = v4wordstat_create_report(phrases=" , , ")
    assert result["error"] == "missing_phrases"


def test_v4wordstat_create_report_phrase_limit():
    phrases = ",".join(f"phrase{i}" for i in range(11))
    result = v4wordstat_create_report(phrases=phrases)
    assert result["error"] == "phrases_limit"


def test_v4wordstat_create_report_dry_run():
    runner = mock_runner({"method": "CreateNewWordstatReport"})
    with patch("server.tools.v4wordstat.get_runner", return_value=runner):
        v4wordstat_create_report(phrases="phrase", dry_run=True)
    argv = runner.run_json.call_args.args[0]
    assert "--dry-run" in argv


def test_v4wordstat_create_report_returns_wrapped_scalar():
    runner = DirectCliRunner()
    with (
        patch("server.tools.v4wordstat.get_runner", return_value=runner),
        patch(
            "server.cli.runner._resolve_direct_cached",
            return_value="/usr/bin/direct",
        ),
        patch(
            "server.cli.runner.subprocess.run",
            return_value=completed("1233756017"),
        ),
    ):
        result = v4wordstat_create_report(phrases="phrase")
    assert result == {"result": 1233756017}


def test_v4wordstat_list_reports_argv():
    runner = mock_runner([])
    with patch("server.tools.v4wordstat.get_runner", return_value=runner):
        v4wordstat_list_reports()
    runner.run_json.assert_called_once_with(
        ["v4wordstat", "list-reports", "--format", "json"]
    )


def test_v4wordstat_list_reports_dry_run():
    runner = mock_runner({"method": "GetWordstatReportList"})
    with patch("server.tools.v4wordstat.get_runner", return_value=runner):
        v4wordstat_list_reports(dry_run=True)
    assert "--dry-run" in runner.run_json.call_args.args[0]


def test_v4wordstat_get_report_argv():
    runner = mock_runner({"ReportID": 42})
    with patch("server.tools.v4wordstat.get_runner", return_value=runner):
        v4wordstat_get_report(report_id=42)
    runner.run_json.assert_called_once_with(
        [
            "v4wordstat",
            "get-report",
            "--report-id",
            "42",
            "--format",
            "json",
        ]
    )


def test_v4wordstat_get_report_dry_run():
    runner = mock_runner({"method": "GetWordstatReport"})
    with patch("server.tools.v4wordstat.get_runner", return_value=runner):
        v4wordstat_get_report(report_id=42, dry_run=True)
    assert "--dry-run" in runner.run_json.call_args.args[0]


def test_v4wordstat_delete_report_argv():
    runner = mock_runner({"ok": True})
    with patch("server.tools.v4wordstat.get_runner", return_value=runner):
        v4wordstat_delete_report(report_id=42)
    runner.run_json.assert_called_once_with(
        [
            "v4wordstat",
            "delete-report",
            "--report-id",
            "42",
            "--format",
            "json",
        ]
    )


def test_v4wordstat_delete_report_dry_run():
    runner = mock_runner({"method": "DeleteWordstatReport"})
    with patch("server.tools.v4wordstat.get_runner", return_value=runner):
        v4wordstat_delete_report(report_id=42, dry_run=True)
    assert "--dry-run" in runner.run_json.call_args.args[0]


def test_v4wordstat_delete_report_returns_wrapped_scalar():
    runner = DirectCliRunner()
    with (
        patch("server.tools.v4wordstat.get_runner", return_value=runner),
        patch(
            "server.cli.runner._resolve_direct_cached",
            return_value="/usr/bin/direct",
        ),
        patch("server.cli.runner.subprocess.run", return_value=completed("1")),
    ):
        result = v4wordstat_delete_report(report_id=42)
    assert result == {"result": 1}
