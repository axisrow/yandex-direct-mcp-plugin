"""Tests for changes MCP tools (CLI 0.3.10 semantics)."""

from unittest.mock import MagicMock, patch


from server.tools.changes import (
    changes_check,
    changes_checkcamp,
    changes_checkdict,
)
from server.contract import EXPLICIT_TIMEZONE_TIMESTAMP_TOOLS


def _mock_runner(return_value):
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


def _argv_for(runner: MagicMock) -> list[str]:
    return runner.run_json.call_args[0][0]


class TestChangesCheck:
    """Tests for changes_check (Yandex API Changes.check)."""

    def test_check_with_campaign_ids(self):
        mock_result = {"Campaigns": [{"Id": 12345}]}
        runner = _mock_runner(mock_result)
        with patch("server.tools.changes.get_runner", return_value=runner):
            result = changes_check(
                field_names="CampaignIds,AdGroupIds",
                timestamp="2026-01-01T00:00:00Z",
                campaign_ids="12345,67890",
            )
        assert result == mock_result
        runner.run_json.assert_called_once_with(
            [
                "changes",
                "check",
                "--campaign-ids",
                "12345,67890",
                "--timestamp",
                "2026-01-01T00:00:00Z",
                "--fields",
                "CampaignIds,AdGroupIds",
                "--format",
                "json",
            ]
        )

    def test_check_with_ad_group_ids(self):
        runner = _mock_runner({"AdGroupIds": [11]})
        with patch("server.tools.changes.get_runner", return_value=runner):
            changes_check(
                field_names="AdGroupIds",
                timestamp="2026-01-01T00:00:00Z",
                ad_group_ids="111,222",
            )
        argv = _argv_for(runner)
        assert argv[2:4] == ["--ad-group-ids", "111,222"]

    def test_check_with_ad_ids(self):
        runner = _mock_runner({"AdIds": [55]})
        with patch("server.tools.changes.get_runner", return_value=runner):
            changes_check(
                field_names="AdIds",
                timestamp="2026-01-01T00:00:00Z",
                ad_ids="55,66,77",
            )
        argv = _argv_for(runner)
        assert argv[2:4] == ["--ad-ids", "55,66,77"]

    def test_missing_id_filter(self):
        result = changes_check(
            field_names="CampaignIds",
            timestamp="2026-01-01T00:00:00Z",
        )
        assert result["error"] == "missing_id_filter"

    def test_empty_id_filter_treated_as_missing(self):
        result = changes_check(
            field_names="CampaignIds",
            timestamp="2026-01-01T00:00:00Z",
            campaign_ids="   ",
        )
        assert result["error"] == "missing_id_filter"

    def test_conflicting_id_filters(self):
        result = changes_check(
            field_names="CampaignIds",
            timestamp="2026-01-01T00:00:00Z",
            campaign_ids="1",
            ad_ids="2",
        )
        assert result["error"] == "conflicting_id_filters"

    def test_missing_field_names(self):
        result = changes_check(
            field_names="",
            timestamp="2026-01-01T00:00:00Z",
            campaign_ids="1",
        )
        assert result["error"] == "missing_field_names"

    def test_invalid_field_names(self):
        result = changes_check(
            field_names="Bogus",
            timestamp="2026-01-01T00:00:00Z",
            campaign_ids="1",
        )
        assert result["error"] == "invalid_field_names"

    def test_campaign_ids_limit_3000(self):
        runner = _mock_runner({"Campaigns": []})
        ids_3000 = ",".join(str(i) for i in range(3000))
        with patch("server.tools.changes.get_runner", return_value=runner):
            result = changes_check(
                field_names="CampaignIds",
                timestamp="2026-01-01T00:00:00Z",
                campaign_ids=ids_3000,
            )
        assert "error" not in result
        runner.run_json.assert_called_once()

    def test_campaign_ids_over_limit_rejected(self):
        ids_3001 = ",".join(str(i) for i in range(3001))
        result = changes_check(
            field_names="CampaignIds",
            timestamp="2026-01-01T00:00:00Z",
            campaign_ids=ids_3001,
        )
        assert result["error"] == "batch_limit"

    def test_ad_group_ids_over_limit_rejected(self):
        ids_10001 = ",".join(str(i) for i in range(10001))
        result = changes_check(
            field_names="AdGroupIds",
            timestamp="2026-01-01T00:00:00Z",
            ad_group_ids=ids_10001,
        )
        assert result["error"] == "batch_limit"

    def test_ad_ids_over_limit_rejected(self):
        ids_50001 = ",".join(str(i) for i in range(50001))
        result = changes_check(
            field_names="AdIds",
            timestamp="2026-01-01T00:00:00Z",
            ad_ids=ids_50001,
        )
        assert result["error"] == "batch_limit"

    def test_comma_only_id_filter_treated_as_missing(self):
        """A value like "," strips to non-empty but yields zero parsed IDs.

        Without parse_ids() reject this would forward `--campaign-ids ,` to
        the CLI, masking a missing_id_filter as a confusing CLI error.
        """
        result = changes_check(
            field_names="CampaignIds",
            timestamp="2026-01-01T00:00:00Z",
            campaign_ids=",",
        )
        assert result["error"] == "missing_id_filter"

    def test_comma_only_id_filter_does_not_mask_real_filter(self):
        """Comma-only campaign_ids must not block a real ad_ids filter."""
        runner = _mock_runner({})
        with patch("server.tools.changes.get_runner", return_value=runner):
            result = changes_check(
                field_names="AdIds",
                timestamp="2026-01-01T00:00:00Z",
                campaign_ids=" , , ",
                ad_ids="42",
            )
        assert "error" not in result
        argv = _argv_for(runner)
        assert argv[2:4] == ["--ad-ids", "42"]

    def test_rejects_timestamp_without_timezone(self):
        runner = _mock_runner({})
        with patch("server.tools.changes.get_runner", return_value=runner):
            result = changes_check(
                field_names="CampaignIds",
                timestamp="2026-01-01T00:00:00",
                campaign_ids="1",
            )
        assert result["error"] == "invalid_timestamp"
        assert "Timestamp must include timezone" in result["message"]
        runner.run_json.assert_not_called()

    def test_keeps_existing_z(self):
        runner = _mock_runner({})
        with patch("server.tools.changes.get_runner", return_value=runner):
            changes_check(
                field_names="CampaignIds",
                timestamp="2026-01-01T00:00:00Z",
                campaign_ids="1",
            )
        argv = _argv_for(runner)
        ts_idx = argv.index("--timestamp")
        assert argv[ts_idx + 1] == "2026-01-01T00:00:00Z"

    def test_keeps_explicit_offset(self):
        runner = _mock_runner({})
        with patch("server.tools.changes.get_runner", return_value=runner):
            changes_check(
                field_names="CampaignIds",
                timestamp="2026-01-01T00:00:00+03:00",
                campaign_ids="1",
            )
        argv = _argv_for(runner)
        ts_idx = argv.index("--timestamp")
        assert argv[ts_idx + 1] == "2026-01-01T00:00:00+03:00"

    def test_rejects_trailing_space_without_timezone(self):
        runner = _mock_runner({})
        with patch("server.tools.changes.get_runner", return_value=runner):
            result = changes_check(
                field_names="CampaignIds",
                timestamp="2026-01-01T00:00:00 ",
                campaign_ids="1",
            )
        assert result["error"] == "invalid_timestamp"
        runner.run_json.assert_not_called()

    def test_strips_trailing_newline_after_z(self):
        """Trailing '\\n' must be stripped — Python's ``$`` would otherwise
        match before the newline, mask the missing zone and forward a value
        with a literal newline to the CLI."""
        runner = _mock_runner({})
        with patch("server.tools.changes.get_runner", return_value=runner):
            changes_check(
                field_names="CampaignIds",
                timestamp="2026-01-01T00:00:00Z\n",
                campaign_ids="1",
            )
        argv = _argv_for(runner)
        ts_idx = argv.index("--timestamp")
        assert argv[ts_idx + 1] == "2026-01-01T00:00:00Z"


class TestChangesCheckCamp:
    """Tests for changes_checkcamp (only --timestamp)."""

    def test_check_campaign_changes(self):
        runner = _mock_runner({"Campaigns": []})
        with patch("server.tools.changes.get_runner", return_value=runner):
            changes_checkcamp(timestamp="2026-01-01T00:00:00Z")
        runner.run_json.assert_called_once_with(
            [
                "changes",
                "check-campaigns",
                "--timestamp",
                "2026-01-01T00:00:00Z",
                "--format",
                "json",
            ]
        )

    def test_check_campaign_changes_rejects_timestamp_without_timezone(self):
        runner = _mock_runner({"Campaigns": []})
        with patch("server.tools.changes.get_runner", return_value=runner):
            result = changes_checkcamp(timestamp="2026-01-01T00:00:00")
        assert result["error"] == "invalid_timestamp"
        assert "Timestamp must include timezone" in result["message"]
        runner.run_json.assert_not_called()

    def test_check_campaign_changes_keeps_explicit_offset(self):
        runner = _mock_runner({"Campaigns": []})
        with patch("server.tools.changes.get_runner", return_value=runner):
            changes_checkcamp(timestamp="2026-01-01T00:00:00+03:00")
        argv = _argv_for(runner)
        ts_idx = argv.index("--timestamp")
        assert argv[ts_idx + 1] == "2026-01-01T00:00:00+03:00"


class TestChangesCheckDict:
    """Tests for changes_checkdict (no arguments)."""

    def test_check_dictionary_changes(self):
        runner = _mock_runner({"Dictionaries": []})
        with patch("server.tools.changes.get_runner", return_value=runner):
            changes_checkdict()
        runner.run_json.assert_called_once_with(
            ["changes", "check-dictionaries", "--format", "json"]
        )


def test_changes_timestamp_contract_requires_explicit_timezone():
    assert EXPLICIT_TIMEZONE_TIMESTAMP_TOOLS == {
        "changes_check",
        "changes_check_campaigns",
    }
