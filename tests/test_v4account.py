"""Tests for v4account MCP tools."""

from unittest.mock import MagicMock, patch

from server.tools.v4account import (
    v4account_account_management,
    v4account_enable_shared_account,
)


def _mock_runner(return_value):
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


def test_v4account_enable_shared_account_dry_run_argv():
    runner = _mock_runner({"method": "EnableSharedAccount"})
    with patch("server.tools.v4account.get_runner", return_value=runner):
        v4account_enable_shared_account(
            client_login=" client-login ",
            dry_run=True,
        )
    runner.run_json.assert_called_once_with(
        [
            "v4account",
            "enable-shared-account",
            "--client-login",
            "client-login",
            "--dry-run",
            "--format",
            "json",
        ]
    )


def test_v4account_enable_shared_account_sandbox_argv():
    runner = _mock_runner({"result": "ok"})
    with patch("server.tools.v4account.get_runner", return_value=runner):
        v4account_enable_shared_account(
            client_login="client-login",
            sandbox=True,
        )
    runner.run_json.assert_called_once_with(
        [
            "--sandbox",
            "v4account",
            "enable-shared-account",
            "--client-login",
            "client-login",
            "--format",
            "json",
        ]
    )


def test_v4account_enable_shared_account_requires_dry_run_or_sandbox():
    result = v4account_enable_shared_account(client_login="client-login")
    assert result["error"] == "sandbox_or_dry_run_required"


def test_v4account_enable_shared_account_requires_login():
    result = v4account_enable_shared_account(client_login=" ", dry_run=True)
    assert result["error"] == "missing_client_login"


def test_v4account_account_management_update_argv():
    runner = _mock_runner({"method": "AccountManagement"})
    with patch("server.tools.v4account.get_runner", return_value=runner):
        v4account_account_management(
            account_id=1327944,
            day_budget="100.50",
            spend_mode="Default",
            money_in_sms="Yes",
            money_out_sms="No",
            paused_by_day_budget_sms="Yes",
            sms_time_from="09:15",
            sms_time_to="19:45",
            email="ops@example.com",
            money_warning_value=25,
            paused_by_day_budget="No",
            dry_run=True,
        )
    runner.run_json.assert_called_once_with(
        [
            "v4account",
            "account-management",
            "--action",
            "Update",
            "--account-id",
            "1327944",
            "--day-budget",
            "100.50",
            "--spend-mode",
            "Default",
            "--money-in-sms",
            "Yes",
            "--money-out-sms",
            "No",
            "--paused-by-day-budget-sms",
            "Yes",
            "--sms-time-from",
            "09:15",
            "--sms-time-to",
            "19:45",
            "--email",
            "ops@example.com",
            "--money-warning-value",
            "25",
            "--paused-by-day-budget",
            "No",
            "--dry-run",
            "--format",
            "json",
        ]
    )


def test_v4account_account_management_sandbox_argv():
    runner = _mock_runner({"result": "ok"})
    with patch("server.tools.v4account.get_runner", return_value=runner):
        v4account_account_management(
            account_id=1327944,
            money_in_sms="No",
            sandbox=True,
        )
    argv = runner.run_json.call_args.args[0]
    assert argv[:3] == ["--sandbox", "v4account", "account-management"]
    assert "--dry-run" not in argv


def test_v4account_account_management_requires_dry_run_or_sandbox():
    result = v4account_account_management(account_id=1327944)
    assert result["error"] == "sandbox_or_dry_run_required"
