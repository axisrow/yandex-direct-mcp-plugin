"""Tests for v4 Live MCP tools."""

from unittest.mock import MagicMock, patch


from server.contract import (
    PUBLIC_TOOL_NAMES,
    V4_LIVE_BLOCKED_METHOD_NAMES,
    V4_LIVE_TOOL_NAMES,
)
from server.tools.balance import balance_get
from server.tools.v4goals import (
    v4goals_get_retargeting_goals,
    v4goals_get_stat_goals,
)
from server.tools.v4tags import (
    v4tags_get_banners,
    v4tags_get_campaigns,
    v4tags_update_banners,
    v4tags_update_campaigns,
)


def _mock_runner(return_value):
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


def test_balance_get_without_logins():
    runner = _mock_runner({"Accounts": []})
    with patch("server.tools.balance.get_runner", return_value=runner):
        result = balance_get()

    assert result == {"Accounts": []}
    runner.run_json.assert_called_once_with(["balance", "--format", "json"])


def test_balance_get_with_logins():
    runner = _mock_runner({"Accounts": []})
    with patch("server.tools.balance.get_runner", return_value=runner):
        result = balance_get(logins=" client-a,client-b ")

    assert result == {"Accounts": []}
    runner.run_json.assert_called_once_with(
        ["balance", "--format", "json", "--logins", "client-a,client-b"]
    )


def test_v4goals_get_stat_goals():
    runner = _mock_runner({"Goals": []})
    with patch("server.tools.v4goals.get_runner", return_value=runner):
        result = v4goals_get_stat_goals(campaign_ids=" 123,456 ")

    assert result == {"Goals": []}
    runner.run_json.assert_called_once_with(
        [
            "v4goals",
            "get-stat-goals",
            "--campaign-ids",
            "123,456",
            "--format",
            "json",
        ]
    )


def test_v4goals_get_retargeting_goals():
    runner = _mock_runner({"RetargetingGoals": []})
    with patch("server.tools.v4goals.get_runner", return_value=runner):
        result = v4goals_get_retargeting_goals(campaign_ids="123,456")

    assert result == {"RetargetingGoals": []}
    runner.run_json.assert_called_once_with(
        [
            "v4goals",
            "get-retargeting-goals",
            "--campaign-ids",
            "123,456",
            "--format",
            "json",
        ]
    )


def test_v4goals_requires_campaign_ids():
    result = v4goals_get_stat_goals(campaign_ids="   ")
    assert result["error"] == "missing_campaign_ids"


def test_v4goals_retargeting_requires_campaign_ids():
    result = v4goals_get_retargeting_goals(campaign_ids="   ")
    assert result["error"] == "missing_campaign_ids"


def test_v4tags_get_campaigns():
    runner = _mock_runner({"Campaigns": []})
    with patch("server.tools.v4tags.get_runner", return_value=runner):
        result = v4tags_get_campaigns(campaign_ids=" 123,456 ")

    assert result == {"Campaigns": []}
    runner.run_json.assert_called_once_with(
        [
            "v4tags",
            "get-campaigns",
            "--campaign-ids",
            "123,456",
            "--format",
            "json",
        ]
    )


def test_v4tags_get_campaigns_requires_campaign_ids():
    result = v4tags_get_campaigns(campaign_ids="   ")
    assert result["error"] == "missing_campaign_ids"


def test_v4tags_get_banners_by_campaign_ids():
    runner = _mock_runner({"Banners": []})
    with patch("server.tools.v4tags.get_runner", return_value=runner):
        result = v4tags_get_banners(campaign_ids=" 123,456 ")

    assert result == {"Banners": []}
    runner.run_json.assert_called_once_with(
        [
            "v4tags",
            "get-banners",
            "--campaign-ids",
            "123,456",
            "--format",
            "json",
        ]
    )


def test_v4tags_get_banners_by_banner_ids():
    runner = _mock_runner({"Banners": []})
    with patch("server.tools.v4tags.get_runner", return_value=runner):
        result = v4tags_get_banners(banner_ids=" 111,222 ")

    assert result == {"Banners": []}
    runner.run_json.assert_called_once_with(
        [
            "v4tags",
            "get-banners",
            "--banner-ids",
            "111,222",
            "--format",
            "json",
        ]
    )


def test_v4tags_get_banners_requires_one_selector():
    result = v4tags_get_banners()
    assert result["error"] == "missing_selector"


def test_v4tags_get_banners_rejects_two_selectors():
    result = v4tags_get_banners(campaign_ids="123", banner_ids="456")
    assert result["error"] == "conflicting_selectors"


def test_v4tags_update_campaigns_with_tags():
    runner = _mock_runner({"success": True})
    with patch("server.tools.v4tags.get_runner", return_value=runner):
        result = v4tags_update_campaigns(
            campaign_id=123,
            tags=[" 0=New ", " 456=Existing "],
        )

    assert result == {"success": True}
    runner.run_json.assert_called_once_with(
        [
            "v4tags",
            "update-campaigns",
            "--campaign-id",
            "123",
            "--tag",
            "0=New",
            "--tag",
            "456=Existing",
            "--format",
            "json",
        ]
    )


def test_v4tags_update_campaigns_clear_tags_dry_run():
    runner = _mock_runner({"dry_run": True})
    with patch("server.tools.v4tags.get_runner", return_value=runner):
        result = v4tags_update_campaigns(
            campaign_id=123,
            clear_tags=True,
            dry_run=True,
        )

    assert result == {"dry_run": True}
    runner.run_json.assert_called_once_with(
        [
            "v4tags",
            "update-campaigns",
            "--campaign-id",
            "123",
            "--clear-tags",
            "--dry-run",
            "--format",
            "json",
        ]
    )


def test_v4tags_update_campaigns_requires_tags_or_clear():
    result = v4tags_update_campaigns(campaign_id=123)
    assert result["error"] == "missing_tag_action"


def test_v4tags_update_campaigns_rejects_tags_and_clear():
    result = v4tags_update_campaigns(
        campaign_id=123,
        tags=["0=New"],
        clear_tags=True,
    )
    assert result["error"] == "conflicting_tag_actions"


def test_v4tags_update_banners_with_tag_ids():
    runner = _mock_runner({"success": True})
    with patch("server.tools.v4tags.get_runner", return_value=runner):
        result = v4tags_update_banners(
            banner_ids=" 111,222 ",
            tag_ids=" 10,20 ",
        )

    assert result == {"success": True}
    runner.run_json.assert_called_once_with(
        [
            "v4tags",
            "update-banners",
            "--banner-ids",
            "111,222",
            "--tag-ids",
            "10,20",
            "--format",
            "json",
        ]
    )


def test_v4tags_update_banners_clear_tags_dry_run():
    runner = _mock_runner({"dry_run": True})
    with patch("server.tools.v4tags.get_runner", return_value=runner):
        result = v4tags_update_banners(
            banner_ids="111,222",
            clear_tags=True,
            dry_run=True,
        )

    assert result == {"dry_run": True}
    runner.run_json.assert_called_once_with(
        [
            "v4tags",
            "update-banners",
            "--banner-ids",
            "111,222",
            "--clear-tags",
            "--dry-run",
            "--format",
            "json",
        ]
    )


def test_v4tags_update_banners_requires_banner_ids():
    result = v4tags_update_banners(banner_ids="   ", tag_ids="10")
    assert result["error"] == "missing_banner_ids"


def test_v4tags_update_banners_requires_tag_ids_or_clear():
    result = v4tags_update_banners(banner_ids="111")
    assert result["error"] == "missing_tag_action"


def test_v4tags_update_banners_rejects_tag_ids_and_clear():
    result = v4tags_update_banners(
        banner_ids="111",
        tag_ids="10",
        clear_tags=True,
    )
    assert result["error"] == "conflicting_tag_actions"


def test_v4_contract_exposes_only_cli_backed_tools():
    assert V4_LIVE_TOOL_NAMES == {
        "balance_get",
        "v4goals_get_stat_goals",
        "v4goals_get_retargeting_goals",
        "v4tags_get_campaigns",
        "v4tags_get_banners",
        "v4tags_update_campaigns",
        "v4tags_update_banners",
    }
    assert V4_LIVE_TOOL_NAMES <= PUBLIC_TOOL_NAMES
    assert {"GetClientsUnits", "PingAPI", "CreateNewForecast"} <= (
        V4_LIVE_BLOCKED_METHOD_NAMES
    )
    assert {
        "GetBannersTags",
        "GetCampaignsTags",
        "UpdateBannersTags",
        "UpdateCampaignsTags",
    }.isdisjoint(V4_LIVE_BLOCKED_METHOD_NAMES)
    assert "v4finance_get_clients_units" not in PUBLIC_TOOL_NAMES
    assert "v4meta_ping_api" not in PUBLIC_TOOL_NAMES
