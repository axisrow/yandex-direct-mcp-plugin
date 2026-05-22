"""MCP tools for Yandex Direct v4 Live shared-account commands."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors


def _base_args(*, sandbox: bool) -> list[str]:
    args: list[str] = []
    if sandbox:
        args.append("--sandbox")
    args.append("v4account")
    return args


def _require_dry_run_or_sandbox(dry_run: bool, sandbox: bool) -> ToolError | None:
    if dry_run or sandbox:
        return None
    return ToolError(
        error="sandbox_or_dry_run_required",
        message="Set dry_run=True or sandbox=True for v4account commands.",
    )


def _append_optional(args: list[str], flag: str, value: object | None) -> None:
    if value is not None:
        args.extend([flag, str(value)])


def _append_optional_text(args: list[str], flag: str, value: str | None) -> None:
    if value is not None:
        normalized = value.strip()
        if normalized:
            args.extend([flag, normalized])


@mcp.tool(name="v4account_enable_shared_account")
@handle_cli_errors
def v4account_enable_shared_account(
    client_login: str,
    dry_run: bool = False,
    sandbox: bool = False,
) -> dict | list[dict]:
    """Enable a shared account for a client via v4 Live EnableSharedAccount.

    Args:
        client_login: Client login to enable the shared account for.
        dry_run: Show the direct-cli request without sending it.
        sandbox: Execute against the Direct sandbox.
    """
    safety_error = _require_dry_run_or_sandbox(dry_run, sandbox)
    if safety_error:
        return safety_error.__dict__

    normalized_login = client_login.strip()
    if not normalized_login:
        return ToolError(
            error="missing_client_login",
            message="Provide client_login.",
        ).__dict__

    args = _base_args(sandbox=sandbox)
    args.extend(["enable-shared-account", "--client-login", normalized_login])
    if dry_run:
        args.append("--dry-run")
    args.extend(["--format", "json"])
    return get_runner().run_json(args)


@mcp.tool(name="v4account_account_management")
@handle_cli_errors
def v4account_account_management(
    account_id: int,
    day_budget: str | None = None,
    spend_mode: str | None = None,
    money_in_sms: str | None = None,
    money_out_sms: str | None = None,
    paused_by_day_budget_sms: str | None = None,
    sms_time_from: str | None = None,
    sms_time_to: str | None = None,
    email: str | None = None,
    money_warning_value: int | None = None,
    paused_by_day_budget: str | None = None,
    dry_run: bool = False,
    sandbox: bool = False,
) -> dict | list[dict]:
    """Update shared-account settings via v4 Live AccountManagement (Update action).

    direct-cli 0.3.10 supports only ``--action Update`` for this command. The
    other AccountManagement actions (Get / Deposit / Invoice / TransferMoney)
    and the related finance/master tokens are tracked in plugin issue #120 and
    will be exposed after direct-cli releases the full action set.

    Args:
        account_id: Shared account ID to update.
        day_budget: Daily budget amount (non-negative).
        spend_mode: ``Default`` or ``Stretched``.
        money_in_sms: ``Yes`` / ``No``.
        money_out_sms: ``Yes`` / ``No``.
        paused_by_day_budget_sms: ``Yes`` / ``No``.
        sms_time_from: SMS start time ``HH:MM`` (minutes 00/15/30/45).
        sms_time_to: SMS end time ``HH:MM`` (minutes 00/15/30/45).
        email: Notification email.
        money_warning_value: Balance warning percentage.
        paused_by_day_budget: ``Yes`` / ``No``.
        dry_run: Show the direct-cli request without sending it.
        sandbox: Execute against the Direct sandbox.
    """
    safety_error = _require_dry_run_or_sandbox(dry_run, sandbox)
    if safety_error:
        return safety_error.__dict__

    args = _base_args(sandbox=sandbox)
    args.extend(
        [
            "account-management",
            "--action",
            "Update",
            "--account-id",
            str(account_id),
        ]
    )

    _append_optional_text(args, "--day-budget", day_budget)
    _append_optional_text(args, "--spend-mode", spend_mode)
    _append_optional_text(args, "--money-in-sms", money_in_sms)
    _append_optional_text(args, "--money-out-sms", money_out_sms)
    _append_optional_text(args, "--paused-by-day-budget-sms", paused_by_day_budget_sms)
    _append_optional_text(args, "--sms-time-from", sms_time_from)
    _append_optional_text(args, "--sms-time-to", sms_time_to)
    _append_optional_text(args, "--email", email)
    _append_optional(args, "--money-warning-value", money_warning_value)
    _append_optional_text(args, "--paused-by-day-budget", paused_by_day_budget)

    if dry_run:
        args.append("--dry-run")
    args.extend(["--format", "json"])
    return get_runner().run_json(args)
