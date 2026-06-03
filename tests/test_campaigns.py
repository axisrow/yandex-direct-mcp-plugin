"""Tests for campaign MCP tools."""

from unittest.mock import MagicMock, call, patch

import pytest

from server.tools.campaigns import (
    campaigns_list,
    campaigns_update,
    campaigns_add,
    campaigns_delete,
    campaigns_archive,
    campaigns_unarchive,
    campaigns_suspend,
    campaigns_resume,
)
from server.cli.runner import CliAuthError, CliError

from tests.helpers import mock_runner


@pytest.fixture
def mock_campaigns():
    """Sample campaign data."""
    return [
        {"Id": 12345, "Name": "Campaign_1", "State": "ON", "DailyBudget": 5000},
        {"Id": 67890, "Name": "Campaign_2", "State": "OFF", "DailyBudget": 3000},
        {"Id": 11111, "Name": "Campaign_3", "State": "ON", "DailyBudget": 7000},
    ]


class TestCampaignsList:
    """Test scenarios 7-8."""

    def test_list_all_campaigns(self, mock_campaigns):
        """Test 7: List all campaigns."""
        with patch(
            "server.tools.campaigns.get_runner",
            return_value=mock_runner(mock_campaigns),
        ):
            result = campaigns_list()
            assert len(result) == 3

    def test_list_active_campaigns(self, mock_campaigns):
        """Test 8: Filter by state=ON."""
        with patch(
            "server.tools.campaigns.get_runner",
            return_value=mock_runner(mock_campaigns),
        ):
            result = campaigns_list(state="ON")
            assert len(result) == 2
            assert all(c["State"] == "ON" for c in result)

    def test_list_empty_result(self):
        """Empty response returns empty list."""
        with patch("server.tools.campaigns.get_runner", return_value=mock_runner([])):
            result = campaigns_list()
            assert result == []

    def test_list_campaigns_batch_limit(self):
        """Test batch limit validation for campaign IDs."""
        ids = ",".join(str(i) for i in range(1, 12))
        result = campaigns_list(ids=ids)
        assert result["error"] == "batch_limit"

    def test_list_campaigns_trims_ids_before_cli(self, mock_campaigns):
        """Test campaign IDs are normalized before argv construction."""
        runner = mock_runner(mock_campaigns)
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            campaigns_list(ids=" 12345,67890 ")

        runner.run_json.assert_called_once_with(
            ["campaigns", "get", "--format", "json", "--ids", "12345,67890"]
        )

    def test_list_campaigns_text_campaign_fields_argv(self, mock_campaigns):
        """Test campaign type-specific fields are forwarded to the CLI."""
        runner = mock_runner(mock_campaigns)
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            campaigns_list(
                ids="103258204",
                fields="Id,Name,State",
                text_campaign_fields="BiddingStrategy",
            )

        runner.run_json.assert_called_once_with(
            [
                "campaigns",
                "get",
                "--format",
                "json",
                "--ids",
                "103258204",
                "--fields",
                "Id,Name,State",
                "--text-campaign-field-names",
                "BiddingStrategy",
            ]
        )

    def test_list_campaigns_filters_and_campaign_specific_fields_argv(
        self, mock_campaigns
    ):
        """Test filters and campaign-specific selectors compose in CLI argv."""
        runner = mock_runner(mock_campaigns)
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            campaigns_list(
                ids="12345,67890",
                fields="Id,Name,State",
                status="ACCEPTED",
                types="TEXT_CAMPAIGN",
                state="ON",
                text_campaign_fields="BiddingStrategy,PriorityGoals",
                mobile_app_campaign_fields="Settings",
                dynamic_text_campaign_fields="BiddingStrategy",
                dynamic_text_campaign_search_strategy_placement_types_fields=(
                    "SearchResults,DynamicPlaces"
                ),
                cpm_banner_campaign_fields="BiddingStrategy",
                smart_campaign_fields="Settings",
                unified_campaign_fields="BiddingStrategy",
                unified_campaign_search_strategy_placement_types_fields=(
                    "SearchResults,Maps"
                ),
                unified_campaign_package_bidding_strategy_platforms_fields=(
                    "SearchResult,Network"
                ),
            )

        runner.run_json.assert_called_once_with(
            [
                "campaigns",
                "get",
                "--format",
                "json",
                "--ids",
                "12345,67890",
                "--status",
                "ACCEPTED",
                "--types",
                "TEXT_CAMPAIGN",
                "--fields",
                "Id,Name,State",
                "--text-campaign-field-names",
                "BiddingStrategy,PriorityGoals",
                "--mobile-app-campaign-field-names",
                "Settings",
                "--dynamic-text-campaign-field-names",
                "BiddingStrategy",
                "--dynamic-text-campaign-search-strategy-placement-types-field-names",
                "SearchResults,DynamicPlaces",
                "--cpm-banner-campaign-field-names",
                "BiddingStrategy",
                "--smart-campaign-field-names",
                "Settings",
                "--unified-campaign-field-names",
                "BiddingStrategy",
                "--unified-campaign-search-strategy-placement-types-field-names",
                "SearchResults,Maps",
                "--unified-campaign-package-bidding-strategy-platforms-field-names",
                "SearchResult,Network",
            ]
        )

    def test_list_campaigns_legacy_argv_unchanged(self, mock_campaigns):
        """Test old campaigns_get() calls do not add selector flags."""
        runner = mock_runner(mock_campaigns)
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            campaigns_list()

        runner.run_json.assert_called_once_with(
            ["campaigns", "get", "--format", "json"]
        )


class TestCampaignsUpdate:
    """Test scenarios 9-10."""

    def test_enable_campaign(self):
        """Test 9: Enable a campaign."""
        with patch(
            "server.tools.campaigns.get_runner",
            return_value=mock_runner({"Id": 67890, "State": "ON"}),
        ):
            result = campaigns_update(id=67890, status="ON")
            assert result["success"] is True
            assert result["status"] == "ON"

    def test_disable_campaign(self):
        """Test 9: Disable a campaign."""
        with patch(
            "server.tools.campaigns.get_runner",
            return_value=mock_runner({"Id": 12345, "State": "OFF"}),
        ):
            result = campaigns_update(id=12345, status="OFF")
            assert result["success"] is True

    def test_not_found_campaign(self):
        """Test 10: Nonexistent campaign."""
        runner = MagicMock()
        runner.run_json.side_effect = CliError(
            "Campaign 999 not found", error_code=8800
        )
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            result = campaigns_update(id=999, status="ON")
            assert "error" in result
            assert result["error"] == "not_found"

    def test_auth_error(self):
        """Test: Auth expired during update."""
        runner = MagicMock()
        runner.run_json.side_effect = CliAuthError("Token expired")
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            result = campaigns_update(id=12345, status="ON")
            assert result["error"] == "auth_expired"

    def test_campaigns_update_argv_composition(self):
        """Test that update passes the typed CLI surface (no --json in 0.3.8)."""
        runner = mock_runner({"Id": 12345})
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            result = campaigns_update(
                id=12345,
                name="Renamed",
                status="SUSPENDED",
                budget=5000,
                start_date="2026-06-01",
                end_date="2026-12-31",
            )

        runner.run_json.assert_called_once_with(
            [
                "campaigns",
                "update",
                "--id",
                "12345",
                "--name",
                "Renamed",
                "--status",
                "SUSPENDED",
                "--budget",
                "5000",
                "--start-date",
                "2026-06-01",
                "--end-date",
                "2026-12-31",
            ]
        )
        assert result["budget"] == 5000
        assert result["start_date"] == "2026-06-01"
        assert result["end_date"] == "2026-12-31"

    def test_campaigns_update_dry_run(self):
        """dry_run=True appends --dry-run to argv."""
        runner = mock_runner({"Id": 12345})
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            campaigns_update(id=12345, name="x", dry_run=True)
            argv = runner.run_json.call_args[0][0]
            assert "--dry-run" in argv

    def test_campaigns_update_requires_changes(self):
        """Test that empty updates are rejected before CLI call."""
        runner = mock_runner({"Id": 12345})
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            result = campaigns_update(id=12345)

        assert result["error"] == "missing_update_fields"
        runner.run_json.assert_not_called()

    def test_campaigns_update_accepts_zero_values(self):
        """Zero-valued typed fields are valid updates and must reach the CLI."""
        runner = mock_runner({"Id": 12345})
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            result = campaigns_update(id=12345, holidays_start_hour=0)

        runner.run_json.assert_called_once_with(
            [
                "campaigns",
                "update",
                "--id",
                "12345",
                "--holidays-start-hour",
                "0",
            ]
        )
        assert result == {"success": True, "id": 12345}

    def test_campaigns_update_passes_notification_and_time_targeting_json(self):
        """Update supports JSON aliases just like add."""
        runner = mock_runner({"Id": 12345})
        notification = '{"EmailSettings":{"Email":"ops@example.com"}}'
        time_targeting = '{"ConsiderWorkingWeekends":"YES"}'
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            campaigns_update(
                id=12345,
                notification_json=notification,
                time_targeting_json=time_targeting,
            )

        argv = runner.run_json.call_args[0][0]
        assert argv[argv.index("--notification") + 1] == notification
        assert argv[argv.index("--time-targeting") + 1] == time_targeting


class TestCampaignsCrudOperations:
    """Tests for campaign CRUD operations (add, delete, archive, unarchive)."""

    def test_campaigns_add(self):
        """Test adding a new campaign with typed strategy/settings flags."""
        mock_result = {"Id": 99999, "Name": "New Campaign"}
        runner = mock_runner(mock_result)
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            result = campaigns_add(
                name="New Campaign",
                start_date="2026-01-01",
                campaign_type="TEXT_CAMPAIGN",
                budget=5000,
                end_date="2026-12-31",
                search_strategy="HIGHEST_POSITION",
                network_strategy="MAXIMUM_COVERAGE",
                settings=[
                    "EnableEmailNotification=YES",
                    "RequireServicing=NO",
                ],
            )
            assert result["Id"] == 99999
            runner.run_json.assert_called_once_with(
                [
                    "campaigns",
                    "add",
                    "--name",
                    "New Campaign",
                    "--start-date",
                    "2026-01-01",
                    "--type",
                    "TEXT_CAMPAIGN",
                    "--budget",
                    "5000",
                    "--end-date",
                    "2026-12-31",
                    "--search-strategy",
                    "HIGHEST_POSITION",
                    "--network-strategy",
                    "MAXIMUM_COVERAGE",
                    "--setting",
                    "EnableEmailNotification=YES",
                    "--setting",
                    "RequireServicing=NO",
                ]
            )

    def test_campaigns_add_dry_run(self):
        """dry_run=True appends --dry-run to argv."""
        runner = mock_runner({"Id": 99999})
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            campaigns_add(name="x", start_date="2026-01-01", dry_run=True)
            argv = runner.run_json.call_args[0][0]
            assert "--dry-run" in argv

    def test_campaigns_add_passes_counter_ids(self):
        """CLI 0.3.9: --counter-ids for TextCampaign/DynamicText."""
        runner = mock_runner({"Id": 1})
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            campaigns_add(
                name="c",
                start_date="2026-01-01",
                campaign_type="TEXT_CAMPAIGN",
                counter_ids="111,222",
            )
        argv = runner.run_json.call_args[0][0]
        assert "--counter-ids" in argv
        assert "111,222" in argv

    def test_campaigns_add_passes_goal_id(self):
        runner = mock_runner({"Id": 1})
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            campaigns_add(
                name="c",
                start_date="2026-01-01",
                campaign_type="TEXT_CAMPAIGN",
                goal_id=12345,
            )
        argv = runner.run_json.call_args[0][0]
        assert "--goal-id" in argv
        assert "12345" in argv

    def test_campaigns_add_passes_priority_goals(self):
        runner = mock_runner({"Id": 1})
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            campaigns_add(
                name="c",
                start_date="2026-01-01",
                campaign_type="TEXT_CAMPAIGN",
                priority_goals="123:50,456:30",
            )
        argv = runner.run_json.call_args[0][0]
        assert "--priority-goals" in argv
        assert "123:50,456:30" in argv

    def test_campaigns_add_passes_average_cpa(self):
        runner = mock_runner({"Id": 1})
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            campaigns_add(
                name="c",
                start_date="2026-01-01",
                campaign_type="TEXT_CAMPAIGN",
                average_cpa=500_000_000,
            )
        argv = runner.run_json.call_args[0][0]
        assert "--average-cpa" in argv
        assert "500000000" in argv

    def test_campaigns_add_passes_crr(self):
        runner = mock_runner({"Id": 1})
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            campaigns_add(
                name="c",
                start_date="2026-01-01",
                campaign_type="TEXT_CAMPAIGN",
                crr=15,
            )
        argv = runner.run_json.call_args[0][0]
        assert "--crr" in argv
        assert "15" in argv

    def test_campaigns_add_passes_bid_ceiling(self):
        runner = mock_runner({"Id": 1})
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            campaigns_add(
                name="c",
                start_date="2026-01-01",
                campaign_type="TEXT_CAMPAIGN",
                bid_ceiling=200_000_000,
            )
        argv = runner.run_json.call_args[0][0]
        assert "--bid-ceiling" in argv
        assert "200000000" in argv

    def test_campaigns_add_passes_notification_json(self):
        runner = mock_runner({"Id": 1})
        payload = '{"SmsSettings":{"Events":["FINISHED"]}}'
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            campaigns_add(
                name="c",
                start_date="2026-01-01",
                campaign_type="TEXT_CAMPAIGN",
                notification_json=payload,
            )
        argv = runner.run_json.call_args[0][0]
        assert "--notification" in argv
        assert payload in argv

    def test_campaigns_add_passes_time_targeting_json(self):
        runner = mock_runner({"Id": 1})
        payload = '{"ConsiderWorkingWeekends":"YES"}'
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            campaigns_add(
                name="c",
                start_date="2026-01-01",
                campaign_type="TEXT_CAMPAIGN",
                time_targeting_json=payload,
            )
        argv = runner.run_json.call_args[0][0]
        assert "--time-targeting" in argv
        assert payload in argv

    def test_campaigns_delete_success(self):
        """Test deleting campaigns successfully."""
        runner = mock_runner({"success": True})
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            result = campaigns_delete(ids="12345,67890")
            assert result["success"] is True
            runner.run_json.assert_has_calls(
                [
                    call(["campaigns", "delete", "--id", "12345"]),
                    call(["campaigns", "delete", "--id", "67890"]),
                ]
            )

    def test_campaigns_delete_batch_limit(self):
        """Test batch limit validation for delete."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        runner = mock_runner({"success": True})
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            result = campaigns_delete(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"
        runner.run_json.assert_not_called()

    def test_campaigns_archive_success(self):
        """Test archiving campaigns successfully."""
        runner = mock_runner({"success": True})
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            result = campaigns_archive(ids="12345,67890")
            assert result["success"] is True
            runner.run_json.assert_has_calls(
                [
                    call(["campaigns", "archive", "--id", "12345"]),
                    call(["campaigns", "archive", "--id", "67890"]),
                ]
            )

    def test_campaigns_archive_batch_limit(self):
        """Test batch limit validation for archive."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = campaigns_archive(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_campaigns_unarchive_success(self):
        """Test unarchiving campaigns successfully."""
        runner = mock_runner({"success": True})
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            result = campaigns_unarchive(ids="12345,67890")
            assert result["success"] is True
            runner.run_json.assert_has_calls(
                [
                    call(["campaigns", "unarchive", "--id", "12345"]),
                    call(["campaigns", "unarchive", "--id", "67890"]),
                ]
            )

    def test_campaigns_unarchive_batch_limit(self):
        """Test batch limit validation for unarchive."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = campaigns_unarchive(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_campaigns_suspend_success(self):
        """Test suspending campaigns successfully."""
        runner = mock_runner({"success": True})
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            result = campaigns_suspend(ids="12345")
            assert result["success"] is True
            runner.run_json.assert_called_once_with(
                ["campaigns", "suspend", "--id", "12345"]
            )

    def test_campaigns_suspend_batch_limit(self):
        """Test batch limit validation for suspend."""
        ids = ",".join(str(i) for i in range(1, 12))
        result = campaigns_suspend(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_campaigns_resume_success(self):
        """Test resuming campaigns successfully."""
        runner = mock_runner({"success": True})
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            result = campaigns_resume(ids="12345")
            assert result["success"] is True
            runner.run_json.assert_called_once_with(
                ["campaigns", "resume", "--id", "12345"]
            )

    def test_campaigns_resume_batch_limit(self):
        """Test batch limit validation for resume."""
        ids = ",".join(str(i) for i in range(1, 12))
        result = campaigns_resume(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"


class TestCampaignsStrategyDictExpansion:
    """Strategy params are grouped into dicts; expansion must keep argv identical."""

    def test_update_text_search_dict_argv_identical_to_old_flat(self):
        """Dict keys expand to the same flags the old flat params produced."""
        runner = mock_runner({"Id": 12345})
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            campaigns_update(
                id=12345,
                text_search_options={
                    "text_search_average_cpc": 15_000_000,
                    "text_search_weekly_spend_limit": 500_000_000,
                },
            )
        argv = runner.run_json.call_args[0][0]
        assert argv.count("--text-search-average-cpc") == 1
        assert argv[argv.index("--text-search-average-cpc") + 1] == "15000000"
        assert argv[argv.index("--text-search-weekly-spend-limit") + 1] == "500000000"
        assert "text_search_options" not in argv

    def test_update_search_and_network_dicts_both_expand(self):
        """Search and network dicts for the same campaign type both expand."""
        runner = mock_runner({"Id": 12345})
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            campaigns_update(
                id=12345,
                text_search_options={"text_search_average_cpc": 10_000_000},
                text_network_options={"text_network_average_cpc": 8_000_000},
            )
        argv = runner.run_json.call_args[0][0]
        assert argv[argv.index("--text-search-average-cpc") + 1] == "10000000"
        assert argv[argv.index("--text-network-average-cpc") + 1] == "8000000"

    def test_update_budget_type_via_dict_reaches_cli(self):
        """The update-only *_budget_type key inside a dict reaches the CLI."""
        runner = mock_runner({"Id": 12345})
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            campaigns_update(
                id=12345,
                text_search_options={"text_search_budget_type": "WEEKLY_BUDGET"},
            )
        argv = runner.run_json.call_args[0][0]
        assert argv[argv.index("--text-search-budget-type") + 1] == "WEEKLY_BUDGET"

    def test_update_empty_strategy_dict_triggers_guard(self):
        """An empty dict does not satisfy the update guard (bool({}) is False)."""
        runner = mock_runner({"Id": 12345})
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            result = campaigns_update(id=12345, text_search_options={})
        assert result["error"] == "missing_update_fields"
        runner.run_json.assert_not_called()

    def test_update_non_dict_strategy_param_rejected(self):
        """A non-dict strategy value returns invalid_param before any CLI call."""
        runner = mock_runner({"Id": 12345})
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            result = campaigns_update(id=12345, text_search_options="bad")
        assert result["error"] == "invalid_param"
        runner.run_json.assert_not_called()

    def test_update_unknown_dict_key_silently_ignored(self):
        """Unknown keys inside a strategy dict never reach argv."""
        runner = mock_runner({"Id": 12345})
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            campaigns_update(
                id=12345,
                text_search_options={
                    "text_search_average_cpc": 5_000_000,
                    "not_a_real_option": "ignored",
                },
            )
        argv = runner.run_json.call_args[0][0]
        assert "not_a_real_option" not in argv
        assert "--not-a-real-option" not in argv
        assert "--text-search-average-cpc" in argv

    def test_add_strategy_dict_argv_parity(self):
        """campaigns_add expands a strategy dict to the correct flags."""
        runner = mock_runner({"Id": 1})
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            campaigns_add(
                name="c",
                start_date="2026-01-01",
                campaign_type="TEXT_CAMPAIGN",
                search_strategy="WB_MAXIMUM_CLICKS",
                text_search_options={"text_search_weekly_spend_limit": 100_000_000},
            )
        argv = runner.run_json.call_args[0][0]
        assert argv[argv.index("--search-strategy") + 1] == "WB_MAXIMUM_CLICKS"
        assert argv[argv.index("--text-search-weekly-spend-limit") + 1] == "100000000"

    def test_add_ignores_update_only_budget_type_in_dict(self):
        """budget_type is update-only; campaigns_add must not emit it."""
        runner = mock_runner({"Id": 1})
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            campaigns_add(
                name="c",
                start_date="2026-01-01",
                text_search_options={
                    "text_search_budget_type": "WEEKLY_BUDGET",
                    "text_search_pay_cpa": 3_000_000,
                },
            )
        argv = runner.run_json.call_args[0][0]
        assert "--text-search-budget-type" not in argv
        assert "--text-search-pay-cpa" in argv
