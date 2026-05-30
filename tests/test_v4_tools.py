"""Tests for v4 Live MCP tools."""

from unittest.mock import MagicMock, patch

from server.cli.runner import DirectCliRunner
from server.contract import (
    PUBLIC_TOOL_NAMES,
    V4_LIVE_BLOCKED_METHOD_NAMES,
    V4_LIVE_DEFERRED_ACTIONS,
    V4_LIVE_SUPPORTED_ACTIONS,
    V4_LIVE_TOOL_NAMES,
)
from server.tools.balance import balance_get
from server.tools.v4adimage import v4adimage_get, v4adimage_set
from server.tools.v4goals import (
    v4goals_get_retargeting_goals,
    v4goals_get_stat_goals,
)
from server.tools.v4keywords import v4keywords_get_suggestion
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


def _completed(stdout: str) -> MagicMock:
    result = MagicMock()
    result.stdout = stdout
    result.stderr = ""
    result.returncode = 0
    return result


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


def test_v4tags_get_banners_rejects_too_many_campaign_ids():
    campaign_ids = ",".join(str(i) for i in range(1, 12))
    result = v4tags_get_banners(campaign_ids=campaign_ids)
    assert result["error"] == "batch_limit"
    assert "Maximum 10 IDs" in result["message"]


def test_v4tags_get_banners_rejects_too_many_banner_ids():
    banner_ids = ",".join(str(i) for i in range(1, 2002))
    result = v4tags_get_banners(banner_ids=banner_ids)
    assert result["error"] == "batch_limit"
    assert "Maximum 2000 IDs" in result["message"]


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


def test_v4tags_update_banners_returns_wrapped_scalar():
    runner = DirectCliRunner()
    with (
        patch("server.tools.v4tags.get_runner", return_value=runner),
        patch(
            "server.cli.runner._resolve_direct_cached",
            return_value="/usr/bin/direct",
        ),
        patch("server.cli.runner.subprocess.run", return_value=_completed("1")),
    ):
        result = v4tags_update_banners(
            banner_ids="111,222",
            tag_ids="10,20",
        )

    assert result == {"result": 1}


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


def test_v4tags_update_banners_rejects_too_many_tag_ids():
    tag_ids = ",".join(str(i) for i in range(1, 32))
    result = v4tags_update_banners(banner_ids="111", tag_ids=tag_ids)
    assert result["error"] == "batch_limit"
    assert "Maximum 30 IDs" in result["message"]


def test_v4_contract_exposes_only_cli_backed_tools():
    assert V4_LIVE_TOOL_NAMES == {
        "balance_get",
        "v4goals_get_stat_goals",
        "v4goals_get_retargeting_goals",
        "v4tags_get_campaigns",
        "v4tags_get_banners",
        "v4tags_update_campaigns",
        "v4tags_update_banners",
        "v4forecast_create",
        "v4forecast_list",
        "v4forecast_get",
        "v4forecast_delete",
        "v4account_get_accounts",
        "v4account_update_account",
        "v4account_deposit",
        "v4account_invoice",
        "v4account_transfer_money",
        "v4account_enable_shared_account",
        "v4events_get_events_log",
        "v4wordstat_create_report",
        "v4wordstat_list_reports",
        "v4wordstat_get_report",
        "v4wordstat_delete_report",
        "v4keywords_get_suggestion",
        "v4adimage_get",
        "v4adimage_set",
    }
    assert V4_LIVE_TOOL_NAMES <= PUBLIC_TOOL_NAMES
    assert {"GetClientsUnits", "PingAPI"} <= V4_LIVE_BLOCKED_METHOD_NAMES
    # AccountManagement action coverage on direct-cli 0.3.11: five discrete
    # MCP tools own one action each — Get / Update / Deposit / Invoice /
    # TransferMoney — so the full surface is supported. ``balance_get`` is
    # treated as a Logins-only convenience alias and intentionally does not
    # claim ``supported_actions`` (the canonical Get is owned by
    # ``v4account_get_accounts`` which also supports the AccountIDs selector).
    assert V4_LIVE_SUPPORTED_ACTIONS["AccountManagement"] == frozenset(
        {"Get", "Update", "Deposit", "Invoice", "TransferMoney"}
    )
    assert "AccountManagement" not in V4_LIVE_DEFERRED_ACTIONS
    # No action may be simultaneously supported and deferred for the same
    # tapi method.
    for method_name, supported in V4_LIVE_SUPPORTED_ACTIONS.items():
        deferred = V4_LIVE_DEFERRED_ACTIONS.get(method_name, frozenset())
        assert supported.isdisjoint(deferred), (
            f"{method_name}: supported and deferred actions overlap: "
            f"{supported & deferred}"
        )
    assert {
        "GetBannersTags",
        "GetCampaignsTags",
        "UpdateBannersTags",
        "UpdateCampaignsTags",
        "CreateNewForecast",
        "GetForecastList",
        "GetForecast",
        "DeleteForecastReport",
        "AccountManagement",
        "EnableSharedAccount",
        "GetEventsLog",
        "CreateNewWordstatReport",
        "GetWordstatReportList",
        "GetWordstatReport",
        "DeleteWordstatReport",
        # CLI 0.4.1 typed these two v4 Live methods and the plugin now exposes
        # them as MCP tools, so they must no longer be in the blocked set.
        "AdImageAssociation",
        "GetKeywordsSuggestion",
    }.isdisjoint(V4_LIVE_BLOCKED_METHOD_NAMES)
    # PayCampaignsByCard stays blocked despite being typed in CLI 0.4.1 —
    # it is a real money movement gated behind the financial policy.
    assert "PayCampaignsByCard" in V4_LIVE_BLOCKED_METHOD_NAMES
    assert "v4finance_get_clients_units" not in PUBLIC_TOOL_NAMES
    assert "v4finance_transfer_money" not in PUBLIC_TOOL_NAMES
    assert "v4finance_pay_campaigns_by_card" not in PUBLIC_TOOL_NAMES
    assert "v4meta_ping_api" not in PUBLIC_TOOL_NAMES


def test_v4keywords_get_suggestion() -> None:
    runner = _mock_runner(["мебельные ручки", "ручка мебельная"])
    with patch("server.tools.v4keywords.get_runner", return_value=runner):
        result = v4keywords_get_suggestion(keywords=[" ручки для шкафа ", "стол"])

    assert result == ["мебельные ручки", "ручка мебельная"]
    runner.run_json.assert_called_once_with(
        [
            "v4keywords",
            "get-suggestion",
            "--keyword",
            "ручки для шкафа",
            "--keyword",
            "стол",
            "--format",
            "json",
        ]
    )


def test_v4keywords_get_suggestion_requires_keywords() -> None:
    result = v4keywords_get_suggestion(keywords=["   "])
    assert result["error"] == "missing_keywords"


def test_v4adimage_get_without_filters() -> None:
    runner = _mock_runner({"AdImageAssociations": [], "TotalObjectsCount": "0"})
    with patch("server.tools.v4adimage.get_runner", return_value=runner):
        result = v4adimage_get()

    assert result == {"AdImageAssociations": [], "TotalObjectsCount": "0"}
    runner.run_json.assert_called_once_with(["v4adimage", "get", "--format", "json"])


def test_v4adimage_get_with_filters() -> None:
    runner = _mock_runner({"AdImageAssociations": []})
    with patch("server.tools.v4adimage.get_runner", return_value=runner):
        result = v4adimage_get(
            campaign_ids=" 123,456 ",
            status_moderate=[" yes ", "ready"],
            limit=3,
            offset=10,
            dry_run=True,
        )

    assert result == {"AdImageAssociations": []}
    runner.run_json.assert_called_once_with(
        [
            "v4adimage",
            "get",
            "--status-moderate",
            "yes",
            "--status-moderate",
            "ready",
            "--campaign-ids",
            "123,456",
            "--limit",
            "3",
            "--offset",
            "10",
            "--dry-run",
            "--format",
            "json",
        ]
    )


def test_v4adimage_set() -> None:
    runner = _mock_runner({"AdImageAssociations": []})
    with patch("server.tools.v4adimage.get_runner", return_value=runner):
        result = v4adimage_set(
            associations=[" 15552664629=aX63TKm1t_G4hJ93AKlAxg ", "16344915985"],
            dry_run=True,
        )

    assert result == {"AdImageAssociations": []}
    runner.run_json.assert_called_once_with(
        [
            "v4adimage",
            "set",
            "--association",
            "15552664629=aX63TKm1t_G4hJ93AKlAxg",
            "--association",
            "16344915985",
            "--dry-run",
            "--format",
            "json",
        ]
    )


def test_v4adimage_set_requires_associations() -> None:
    result = v4adimage_set(associations=["   "])
    assert result["error"] == "missing_associations"
