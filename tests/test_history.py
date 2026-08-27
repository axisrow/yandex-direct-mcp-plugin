"""Tests for the optional browser-backed ``history_get`` MCP tool."""

import inspect
from unittest.mock import MagicMock, patch

from server.cli.runner import CliBrowserAuthError
from tests.helpers import mock_runner

SAMPLE_HISTORY = [
    {
        "Datetime": "2026-08-13T16:22:39",
        "Login": "example-login",
        "Uid": 1000000001,
        "ChangeSource": "WEB",
        "Category": "CAMPAIGN_STRATEGY",
        "EventType": "CampaignStrategyEvent",
        "CampaignId": 77593206,
        "CampaignName": "Example campaign",
        "Gtid": "00000000-0000-0000-0000-000000000000:1",
        "Event": {
            "__typename": "CampaignStrategyEvent",
            "category": "CAMPAIGN_STRATEGY",
            "unknownFutureField": {"preserved": True},
        },
    }
]


def _load_history_module():
    """Import the optional module without leaking its tool into default tests."""
    from server.main import mcp
    from server.tools import history

    # W-02 owns env-gated imports. Until that integration lands, importing this
    # module in a unit test must not mutate the process-wide default tool surface.
    mcp._tool_manager._tools.pop("history_get", None)
    return history


def _history_runner(result=SAMPLE_HISTORY) -> MagicMock:
    runner = mock_runner()
    runner.run_json_lenient.return_value = result
    return runner


def test_history_get_forwards_all_domain_filters_in_click_order() -> None:
    history = _load_history_module()
    runner = _history_runner()

    with patch("server.tools.history.get_browser_runner", return_value=runner):
        result = history.history_get(
            campaign_ids=" 1,2 ",
            date_from=" 2026-08-01 ",
            date_to=" 2026-08-02T10:30:00 ",
            logins=" user-a,user-b ",
            change_sources=" WEB,API ",
            categories=" CAMPAIGN_STRATEGY,CAMPAIGN_ARCHIVED ",
            limit=7,
        )

    assert result == SAMPLE_HISTORY
    runner.run_json_lenient.assert_called_once_with(
        [
            "history",
            "get",
            "--campaign-ids",
            "1,2",
            "--date-from",
            "2026-08-01",
            "--date-to",
            "2026-08-02T10:30:00",
            "--logins",
            "user-a,user-b",
            "--change-sources",
            "WEB,API",
            "--categories",
            "CAMPAIGN_STRATEGY,CAMPAIGN_ARCHIVED",
            "--limit",
            "7",
            "--format",
            "json",
        ]
    )
    runner.run_json.assert_not_called()


def test_history_get_omits_unset_and_blank_non_category_filters() -> None:
    history = _load_history_module()
    runner = _history_runner([])

    with patch("server.tools.history.get_browser_runner", return_value=runner):
        result = history.history_get(
            campaign_ids="   ",
            date_from="",
            date_to="   ",
            logins=" ",
            change_sources="",
        )

    assert result == []
    runner.run_json_lenient.assert_called_once_with(
        ["history", "get", "--format", "json"]
    )


def test_history_get_distinguishes_unset_from_empty_categories() -> None:
    history = _load_history_module()

    unset_runner = _history_runner([])
    with patch("server.tools.history.get_browser_runner", return_value=unset_runner):
        history.history_get(categories=None)

    empty_runner = _history_runner([])
    with patch("server.tools.history.get_browser_runner", return_value=empty_runner):
        history.history_get(categories="")

    assert "--categories" not in unset_runner.run_json_lenient.call_args.args[0]
    empty_runner.run_json_lenient.assert_called_once_with(
        ["history", "get", "--categories", "", "--format", "json"]
    )


def test_history_get_whitespace_categories_remains_explicit_empty_filter() -> None:
    history = _load_history_module()
    runner = _history_runner([])

    with patch("server.tools.history.get_browser_runner", return_value=runner):
        history.history_get(categories="   ")

    runner.run_json_lenient.assert_called_once_with(
        ["history", "get", "--categories", "", "--format", "json"]
    )


def test_history_get_forwards_non_positive_limit_for_direct_usage_error() -> None:
    """The CLI owns the positive-limit UsageError; the MCP must not drop zero."""
    history = _load_history_module()
    runner = _history_runner([])

    with patch("server.tools.history.get_browser_runner", return_value=runner):
        history.history_get(limit=0)

    runner.run_json_lenient.assert_called_once_with(
        ["history", "get", "--limit", "0", "--format", "json"]
    )


def test_history_get_maps_browser_auth_failures() -> None:
    history = _load_history_module()
    runner = _history_runner()
    runner.run_json_lenient.side_effect = CliBrowserAuthError("browser login required")

    with patch("server.tools.history.get_browser_runner", return_value=runner):
        result = history.history_get(limit=1)

    assert result["error"] == "browser_auth_required"
    assert "direct playwright login" in result["hint"]


def test_history_get_signature_covers_all_seven_domain_click_parameters() -> None:
    history = _load_history_module()
    expected_domain_params = {
        "campaign_ids",
        "date_from",
        "date_to",
        "logins",
        "change_sources",
        "categories",
        "limit",
    }

    assert expected_domain_params == set(
        inspect.signature(history.history_get).parameters
    )
