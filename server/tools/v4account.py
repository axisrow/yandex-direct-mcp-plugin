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


def _normalize_payment(payment: list[str]) -> ToolError | list[str]:
    """Validate ``--payment`` entries.

    Each entry must be ``ACCOUNT_ID=AMOUNT``. CLI validates the numeric
    types; the plugin only catches structurally malformed entries early
    so the operator sees a clear error instead of a CLI traceback.
    """
    if not payment:
        return ToolError(
            error="missing_payment",
            message="Provide at least one payment entry (ACCOUNT_ID=AMOUNT).",
        )
    normalized: list[str] = []
    for entry in payment:
        stripped = entry.strip() if isinstance(entry, str) else ""
        if "=" not in stripped:
            return ToolError(
                error="invalid_payment_format",
                message=(
                    "Each payment entry must be in ACCOUNT_ID=AMOUNT format; "
                    f"got {entry!r}."
                ),
            )
        normalized.append(stripped)
    return normalized


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
        dry_run: Show the direct request without sending it.
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


@mcp.tool(name="v4account_get_accounts")
@handle_cli_errors
def v4account_get_accounts(
    logins: str | None = None,
    account_ids: str | None = None,
    dry_run: bool = False,
    sandbox: bool = False,
) -> dict | list[dict]:
    """Read shared-account info via v4 Live AccountManagement (Get action).

    Pass exactly one of ``logins`` (comma-separated client logins, max 50)
    or ``account_ids`` (comma-separated shared account IDs, max 100).
    This is a read-only operation and does not require dry_run or sandbox.

    Args:
        logins: Comma-separated client logins selector.
        account_ids: Comma-separated shared account IDs selector.
        dry_run: Show the direct request without sending it.
        sandbox: Execute against the Direct sandbox.
    """
    normalized_logins = logins.strip() if logins else ""
    normalized_account_ids = account_ids.strip() if account_ids else ""

    if normalized_logins and normalized_account_ids:
        return ToolError(
            error="conflicting_selectors",
            message="Pass exactly one of logins / account_ids, not both.",
        ).__dict__
    if not normalized_logins and not normalized_account_ids:
        return ToolError(
            error="missing_selector",
            message="Provide either logins or account_ids.",
        ).__dict__

    args = _base_args(sandbox=sandbox)
    args.extend(["account-management", "--action", "Get"])
    if normalized_logins:
        args.extend(["--logins", normalized_logins])
    else:
        args.extend(["--account-ids", normalized_account_ids])
    if dry_run:
        args.append("--dry-run")
    args.extend(["--format", "json"])
    return get_runner().run_json(args)


@mcp.tool(name="v4account_update_account")
@handle_cli_errors
def v4account_update_account(
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
    """Update shared-account settings via v4 Live AccountManagement (Update).

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
        dry_run: Show the direct request without sending it.
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


@mcp.tool(name="v4account_deposit")
@handle_cli_errors
def v4account_deposit(
    payment: list[str],
    currency: str,
    origin: str | None = None,
    contract: str | None = None,
    operation_num: int | None = None,
    dry_run: bool = False,
    sandbox: bool = False,
) -> dict | list[dict]:
    """Deposit funds via v4 Live AccountManagement (Deposit action).

    Financial tokens (``finance_token``, ``master_token``, ``finance_login``)
    are intentionally **not** accepted as parameters — set them in the
    environment instead (``YANDEX_DIRECT_FINANCE_TOKEN``,
    ``YANDEX_DIRECT_MASTER_TOKEN``, ``YANDEX_DIRECT_FINANCE_LOGIN``). This
    keeps secrets out of MCP argv, logs, and Claude context.

    Args:
        payment: List of ``ACCOUNT_ID=AMOUNT`` entries. At least one required.
        currency: Currency code (``rub|chf|eur|kzt|try|uah|usd|byn``).
        origin: Funding origin; only ``Overdraft`` is valid.
        contract: Contract number.
        operation_num: Unique operation number for idempotency.
        dry_run: Show the direct request without sending it.
        sandbox: Execute against the Direct sandbox.
    """
    safety_error = _require_dry_run_or_sandbox(dry_run, sandbox)
    if safety_error:
        return safety_error.__dict__

    normalized = _normalize_payment(payment)
    if isinstance(normalized, ToolError):
        return normalized.__dict__

    args = _base_args(sandbox=sandbox)
    args.extend(["account-management", "--action", "Deposit"])
    for entry in normalized:
        args.extend(["--payment", entry])
    args.extend(["--currency", currency.strip()])
    _append_optional_text(args, "--origin", origin)
    _append_optional_text(args, "--contract", contract)
    _append_optional(args, "--operation-num", operation_num)

    if dry_run:
        args.append("--dry-run")
    args.extend(["--format", "json"])
    return get_runner().run_json(args)


@mcp.tool(name="v4account_invoice")
@handle_cli_errors
def v4account_invoice(
    payment: list[str],
    currency: str,
    operation_num: int | None = None,
    dry_run: bool = False,
    sandbox: bool = False,
) -> dict | list[dict]:
    """Issue invoice payments via v4 Live AccountManagement (Invoice action).

    See ``v4account_deposit`` for the financial-token env-var policy.

    Args:
        payment: List of ``ACCOUNT_ID=AMOUNT`` entries.
        currency: Currency code.
        operation_num: Unique operation number.
        dry_run: Show the direct request without sending it.
        sandbox: Execute against the Direct sandbox.
    """
    safety_error = _require_dry_run_or_sandbox(dry_run, sandbox)
    if safety_error:
        return safety_error.__dict__

    normalized = _normalize_payment(payment)
    if isinstance(normalized, ToolError):
        return normalized.__dict__

    args = _base_args(sandbox=sandbox)
    args.extend(["account-management", "--action", "Invoice"])
    for entry in normalized:
        args.extend(["--payment", entry])
    args.extend(["--currency", currency.strip()])
    _append_optional(args, "--operation-num", operation_num)

    if dry_run:
        args.append("--dry-run")
    args.extend(["--format", "json"])
    return get_runner().run_json(args)


@mcp.tool(name="v4account_transfer_money")
@handle_cli_errors
def v4account_transfer_money(
    from_account_id: int,
    to_account_id: int,
    amount: str,
    currency: str,
    operation_num: int | None = None,
    dry_run: bool = False,
    sandbox: bool = False,
) -> dict | list[dict]:
    """Transfer funds between shared accounts via AccountManagement TransferMoney.

    See ``v4account_deposit`` for the financial-token env-var policy.

    Args:
        from_account_id: Source shared account ID.
        to_account_id: Destination shared account ID.
        amount: Positive amount, e.g. ``"100.50"``.
        currency: Currency code.
        operation_num: Unique operation number.
        dry_run: Show the direct request without sending it.
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
            "TransferMoney",
            "--from-account-id",
            str(from_account_id),
            "--to-account-id",
            str(to_account_id),
            "--amount",
            amount.strip(),
            "--currency",
            currency.strip(),
        ]
    )
    _append_optional(args, "--operation-num", operation_num)

    if dry_run:
        args.append("--dry-run")
    args.extend(["--format", "json"])
    return get_runner().run_json(args)
