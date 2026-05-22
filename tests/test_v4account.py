"""Tests for v4account MCP tools."""

from unittest.mock import MagicMock, patch

from server.tools.v4account import (
    v4account_deposit,
    v4account_enable_shared_account,
    v4account_get_accounts,
    v4account_invoice,
    v4account_transfer_money,
    v4account_update_account,
)

_FINANCE_TOKEN_FLAGS = ("--finance-token", "--master-token", "--finance-login")


def _mock_runner(return_value):
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


def _assert_no_finance_token_flags(argv: list[str]) -> None:
    """Issue #120 security policy: finance/master tokens stay env-only."""
    for flag in _FINANCE_TOKEN_FLAGS:
        assert flag not in argv, f"{flag} must never appear in argv"


# ---------------------------------------------------------------------------
# v4account_enable_shared_account
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# v4account_get_accounts
# ---------------------------------------------------------------------------


def test_v4account_get_accounts_by_logins_argv():
    runner = _mock_runner({"method": "AccountManagement"})
    with patch("server.tools.v4account.get_runner", return_value=runner):
        v4account_get_accounts(logins=" client-a,client-b ", dry_run=True)
    runner.run_json.assert_called_once_with(
        [
            "v4account",
            "account-management",
            "--action",
            "Get",
            "--logins",
            "client-a,client-b",
            "--dry-run",
            "--format",
            "json",
        ]
    )


def test_v4account_get_accounts_by_account_ids_argv():
    runner = _mock_runner({"method": "AccountManagement"})
    with patch("server.tools.v4account.get_runner", return_value=runner):
        v4account_get_accounts(account_ids="111,222", sandbox=True)
    runner.run_json.assert_called_once_with(
        [
            "--sandbox",
            "v4account",
            "account-management",
            "--action",
            "Get",
            "--account-ids",
            "111,222",
            "--format",
            "json",
        ]
    )


def test_v4account_get_accounts_without_selectors_lists_all():
    """``--action Get`` without a selector is a valid CLI 0.3.11 mode.

    Codex review (PR #123 P2): the v4 Live API allows AccountManagement
    Get without ``SelectionCriteria`` and direct-cli builds the request
    as ``{"Action": "Get"}``. The MCP wrapper must not impose a stricter
    barrier than the CLI itself.
    """
    runner = _mock_runner({"method": "AccountManagement"})
    with patch("server.tools.v4account.get_runner", return_value=runner):
        v4account_get_accounts(dry_run=True)
    runner.run_json.assert_called_once_with(
        [
            "v4account",
            "account-management",
            "--action",
            "Get",
            "--dry-run",
            "--format",
            "json",
        ]
    )


def test_v4account_get_accounts_accepts_both_selectors():
    """Codex review (PR #123 iter 5, P2): direct-cli 0.3.11 forwards both
    ``--logins`` and ``--account-ids`` into one ``SelectionCriteria``,
    so the MCP wrapper must not reject the combination.
    """
    runner = _mock_runner({"method": "AccountManagement"})
    with patch("server.tools.v4account.get_runner", return_value=runner):
        v4account_get_accounts(logins="a,b", account_ids="1,2", dry_run=True)
    runner.run_json.assert_called_once_with(
        [
            "v4account",
            "account-management",
            "--action",
            "Get",
            "--logins",
            "a,b",
            "--account-ids",
            "1,2",
            "--dry-run",
            "--format",
            "json",
        ]
    )


def test_v4account_get_accounts_rejects_explicitly_empty_logins():
    """Codex review (PR #123 iter 3 P2): ``logins=""`` must NOT silently
    broaden a filtered request into a list-all. The unfiltered mode
    requires omitting the argument entirely.
    """
    for blank in ("", "   ", "\t"):
        result = v4account_get_accounts(logins=blank)
        assert result["error"] == "empty_selector", blank
        assert "logins" in result["message"]


def test_v4account_get_accounts_rejects_explicitly_empty_account_ids():
    for blank in ("", "   ", "\t"):
        result = v4account_get_accounts(account_ids=blank)
        assert result["error"] == "empty_selector", blank
        assert "account_ids" in result["message"]


def test_v4account_get_accounts_does_not_require_dry_run_or_sandbox():
    runner = _mock_runner({"method": "AccountManagement"})
    with patch("server.tools.v4account.get_runner", return_value=runner):
        v4account_get_accounts(logins="client-a")
    runner.run_json.assert_called_once()
    argv = runner.run_json.call_args.args[0]
    assert "--dry-run" not in argv
    assert "--sandbox" not in argv


# ---------------------------------------------------------------------------
# v4account_update_account
# ---------------------------------------------------------------------------


def test_v4account_update_account_argv():
    runner = _mock_runner({"method": "AccountManagement"})
    with patch("server.tools.v4account.get_runner", return_value=runner):
        v4account_update_account(
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


def test_v4account_update_account_sandbox_argv():
    runner = _mock_runner({"result": "ok"})
    with patch("server.tools.v4account.get_runner", return_value=runner):
        v4account_update_account(
            account_id=1327944,
            money_in_sms="No",
            sandbox=True,
        )
    argv = runner.run_json.call_args.args[0]
    assert argv[:3] == ["--sandbox", "v4account", "account-management"]
    assert "--dry-run" not in argv


def test_v4account_update_account_requires_dry_run_or_sandbox():
    result = v4account_update_account(account_id=1327944)
    assert result["error"] == "sandbox_or_dry_run_required"


# ---------------------------------------------------------------------------
# v4account_deposit
# ---------------------------------------------------------------------------


def test_v4account_deposit_argv():
    runner = _mock_runner({"method": "AccountManagement"})
    with patch("server.tools.v4account.get_runner", return_value=runner):
        v4account_deposit(
            payment=["111=50000", "222=30000"],
            currency="rub",
            origin="Overdraft",
            contract="C-2026-01",
            operation_num=42,
            dry_run=True,
        )
    argv = runner.run_json.call_args.args[0]
    assert argv == [
        "v4account",
        "account-management",
        "--action",
        "Deposit",
        "--payment",
        "111=50000",
        "--payment",
        "222=30000",
        "--currency",
        "rub",
        "--origin",
        "Overdraft",
        "--contract",
        "C-2026-01",
        "--operation-num",
        "42",
        "--dry-run",
        "--format",
        "json",
    ]
    _assert_no_finance_token_flags(argv)


def test_v4account_deposit_sandbox_argv():
    runner = _mock_runner({"result": "ok"})
    with patch("server.tools.v4account.get_runner", return_value=runner):
        v4account_deposit(
            payment=["1=100"],
            currency="usd",
            sandbox=True,
        )
    argv = runner.run_json.call_args.args[0]
    assert argv[0] == "--sandbox"
    assert "--dry-run" not in argv
    _assert_no_finance_token_flags(argv)


def test_v4account_deposit_requires_dry_run_or_sandbox():
    result = v4account_deposit(payment=["1=100"], currency="rub")
    assert result["error"] == "sandbox_or_dry_run_required"


def test_v4account_deposit_requires_payment():
    result = v4account_deposit(payment=[], currency="rub", dry_run=True)
    assert result["error"] == "missing_payment"


def test_v4account_deposit_validates_payment_format():
    result = v4account_deposit(
        payment=["valid=10", "no-equals-here"], currency="rub", dry_run=True
    )
    assert result["error"] == "invalid_payment_format"


def test_v4account_normalize_payment_rejects_empty_sides():
    """claude[bot] PR #123 cycle-review finding 2 (Low): tighten
    ACCOUNT_ID=AMOUNT shape — both sides must be non-empty so a CLI
    error like ``invalid integer for ACCOUNT_ID`` becomes an explicit
    ``invalid_payment_format`` ToolError up-front.
    """
    for bad in ("=50000", "123=", "=", "  =  "):
        result = v4account_deposit(payment=[bad], currency="rub", dry_run=True)
        assert result["error"] == "invalid_payment_format", bad


def test_v4account_deposit_rejects_empty_currency():
    """claude[bot] PR #123 cycle-review finding 1 (Medium): financial
    tools previously forwarded ``currency=" "`` to argv producing a
    cryptic CLI error; surface ``missing_currency`` ToolError instead."""
    for blank in ("", "   ", "\t"):
        result = v4account_deposit(payment=["1=100"], currency=blank, dry_run=True)
        assert result["error"] == "missing_currency", blank


def test_v4account_invoice_rejects_empty_currency():
    for blank in ("", "   "):
        result = v4account_invoice(payment=["1=100"], currency=blank, dry_run=True)
        assert result["error"] == "missing_currency", blank


def test_v4account_transfer_money_rejects_empty_currency():
    for blank in ("", "   "):
        result = v4account_transfer_money(
            from_account_id=1,
            to_account_id=2,
            amount="10",
            currency=blank,
            dry_run=True,
        )
        assert result["error"] == "missing_currency", blank


def test_v4account_transfer_money_rejects_empty_amount():
    for blank in ("", "   "):
        result = v4account_transfer_money(
            from_account_id=1,
            to_account_id=2,
            amount=blank,
            currency="rub",
            dry_run=True,
        )
        assert result["error"] == "missing_amount", blank


def test_v4account_deposit_does_not_pass_finance_token():
    """Even with full optional surface, no finance/master/login flag leaks."""
    runner = _mock_runner({"result": "ok"})
    with patch("server.tools.v4account.get_runner", return_value=runner):
        v4account_deposit(
            payment=["1=100"],
            currency="rub",
            origin="Overdraft",
            contract="x",
            operation_num=7,
            dry_run=True,
        )
    _assert_no_finance_token_flags(runner.run_json.call_args.args[0])


# ---------------------------------------------------------------------------
# v4account_invoice
# ---------------------------------------------------------------------------


def test_v4account_invoice_argv():
    runner = _mock_runner({"method": "AccountManagement"})
    with patch("server.tools.v4account.get_runner", return_value=runner):
        v4account_invoice(
            payment=["555=10000"],
            currency="eur",
            operation_num=99,
            dry_run=True,
        )
    argv = runner.run_json.call_args.args[0]
    assert argv == [
        "v4account",
        "account-management",
        "--action",
        "Invoice",
        "--payment",
        "555=10000",
        "--currency",
        "eur",
        "--operation-num",
        "99",
        "--dry-run",
        "--format",
        "json",
    ]
    _assert_no_finance_token_flags(argv)


def test_v4account_invoice_sandbox_argv():
    runner = _mock_runner({"result": "ok"})
    with patch("server.tools.v4account.get_runner", return_value=runner):
        v4account_invoice(payment=["1=100"], currency="usd", sandbox=True)
    argv = runner.run_json.call_args.args[0]
    assert argv[0] == "--sandbox"
    assert "--dry-run" not in argv


def test_v4account_invoice_requires_dry_run_or_sandbox():
    result = v4account_invoice(payment=["1=100"], currency="rub")
    assert result["error"] == "sandbox_or_dry_run_required"


def test_v4account_invoice_requires_payment():
    result = v4account_invoice(payment=[], currency="rub", dry_run=True)
    assert result["error"] == "missing_payment"


def test_v4account_invoice_does_not_pass_finance_token():
    runner = _mock_runner({"result": "ok"})
    with patch("server.tools.v4account.get_runner", return_value=runner):
        v4account_invoice(payment=["1=100"], currency="rub", dry_run=True)
    _assert_no_finance_token_flags(runner.run_json.call_args.args[0])


# ---------------------------------------------------------------------------
# v4account_transfer_money
# ---------------------------------------------------------------------------


def test_v4account_transfer_money_argv():
    runner = _mock_runner({"method": "AccountManagement"})
    with patch("server.tools.v4account.get_runner", return_value=runner):
        v4account_transfer_money(
            from_account_id=10,
            to_account_id=20,
            amount="500.75",
            currency="rub",
            operation_num=7,
            dry_run=True,
        )
    argv = runner.run_json.call_args.args[0]
    assert argv == [
        "v4account",
        "account-management",
        "--action",
        "TransferMoney",
        "--from-account-id",
        "10",
        "--to-account-id",
        "20",
        "--amount",
        "500.75",
        "--currency",
        "rub",
        "--operation-num",
        "7",
        "--dry-run",
        "--format",
        "json",
    ]
    _assert_no_finance_token_flags(argv)


def test_v4account_transfer_money_sandbox_argv():
    runner = _mock_runner({"result": "ok"})
    with patch("server.tools.v4account.get_runner", return_value=runner):
        v4account_transfer_money(
            from_account_id=1,
            to_account_id=2,
            amount="100",
            currency="usd",
            sandbox=True,
        )
    argv = runner.run_json.call_args.args[0]
    assert argv[0] == "--sandbox"
    assert "--dry-run" not in argv


def test_v4account_transfer_money_requires_dry_run_or_sandbox():
    result = v4account_transfer_money(
        from_account_id=1,
        to_account_id=2,
        amount="100",
        currency="rub",
    )
    assert result["error"] == "sandbox_or_dry_run_required"


def test_v4account_transfer_money_does_not_pass_finance_token():
    runner = _mock_runner({"result": "ok"})
    with patch("server.tools.v4account.get_runner", return_value=runner):
        v4account_transfer_money(
            from_account_id=1,
            to_account_id=2,
            amount="100",
            currency="rub",
            dry_run=True,
        )
    _assert_no_finance_token_flags(runner.run_json.call_args.args[0])
