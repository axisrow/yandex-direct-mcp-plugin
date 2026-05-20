"""Tests for changes MCP tools (CLI 0.3.8 semantics)."""

from unittest.mock import MagicMock, patch


from server.tools.changes import (
    changes_check,
    changes_checkcamp,
    changes_checkdict,
)


def _mock_runner(return_value):
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


class TestChangesCheck:
    """Tests for changes_check (requires --campaign-ids + --timestamp)."""

    def test_check_changes(self):
        mock_result = {"Campaigns": [{"Id": 12345}]}
        runner = _mock_runner(mock_result)
        with patch("server.tools.changes.get_runner", return_value=runner):
            result = changes_check(
                campaign_ids="12345",
                timestamp="2026-01-01T00:00:00",
            )
            assert result == mock_result
            runner.run_json.assert_called_once_with(
                [
                    "changes",
                    "check",
                    "--campaign-ids",
                    "12345",
                    "--timestamp",
                    "2026-01-01T00:00:00",
                    "--format",
                    "json",
                ]
            )

    def test_check_changes_requires_campaign_ids(self):
        result = changes_check(campaign_ids="  ", timestamp="2026-01-01T00:00:00")
        assert result["error"] == "missing_campaign_ids"

    def test_check_changes_batch_limit(self):
        ids = ",".join(str(i) for i in range(1, 12))
        result = changes_check(campaign_ids=ids, timestamp="2026-01-01T00:00:00")
        assert result["error"] == "batch_limit"


class TestChangesCheckCamp:
    """Tests for changes_checkcamp (only --timestamp)."""

    def test_check_campaign_changes(self):
        runner = _mock_runner({"Campaigns": []})
        with patch("server.tools.changes.get_runner", return_value=runner):
            changes_checkcamp(timestamp="2026-01-01T00:00:00")
        runner.run_json.assert_called_once_with(
            [
                "changes",
                "check-campaigns",
                "--timestamp",
                "2026-01-01T00:00:00",
                "--format",
                "json",
            ]
        )


class TestChangesCheckDict:
    """Tests for changes_checkdict (no arguments)."""

    def test_check_dictionary_changes(self):
        runner = _mock_runner({"Dictionaries": []})
        with patch("server.tools.changes.get_runner", return_value=runner):
            changes_checkdict()
        runner.run_json.assert_called_once_with(
            ["changes", "check-dictionaries", "--format", "json"]
        )
