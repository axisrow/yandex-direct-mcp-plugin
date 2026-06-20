"""MCP tools for Yandex Direct v4 Live shared-account commands."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import finalize_json_args, tool_error_dict


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

    Each entry must be ``ACCOUNT_ID=AMOUNT`` with both sides non-empty.
    CLI validates the numeric types; the plugin only catches structurally
    malformed entries early so the operator sees a clear ``ToolError``
    instead of a CLI traceback.
    """
    if not payment:
        return ToolError(
            error="missing_payment",
            message="Provide at least one payment entry (ACCOUNT_ID=AMOUNT).",
        )
    normalized: list[str] = []
    for entry in payment:
        stripped = entry.strip() if isinstance(entry, str) else ""
        # Tighten the ACCOUNT_ID=AMOUNT shape: both sides must be present.
        # ``"=50000"`` / ``"123="`` / ``"="`` previously slipped through and
        # got forwarded to the CLI verbatim, yielding cryptic errors for the
        # caller.
        account_id, sep, amount = stripped.partition("=")
        if not sep or not account_id.strip() or not amount.strip():
            return ToolError(
                error="invalid_payment_format",
                message=(
                    "Each payment entry must be in ACCOUNT_ID=AMOUNT format "
                    f"with both sides non-empty; got {entry!r}."
                ),
            )
        normalized.append(stripped)
    return normalized


def _require_non_empty(value: str, *, field: str, error: str) -> ToolError | str:
    """Trim and reject an empty required string parameter.

    Used by the financial v4account tools to surface ``ToolError`` before
    the empty value reaches the subprocess argv (where the CLI would emit
    a less specific error). Mirrors the existing
    ``missing_client_login`` guard in ``v4account_enable_shared_account``.
    """
    normalized = value.strip()
    if not normalized:
        return ToolError(
            error=error,
            message=f"Provide a non-empty {field}.",
        )
    return normalized


@mcp.tool(
    name="v4account_enable_shared_account",
    description="Enable a shared account for a client (v4 Live EnableSharedAccount); requires dry_run or sandbox. Call tool_help('v4account_enable_shared_account') for parameters.",
)
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
        return tool_error_dict(safety_error)

    normalized_login = client_login.strip()
    if not normalized_login:
        return tool_error_dict(
            ToolError(
                error="missing_client_login",
                message="Provide client_login.",
            )
        )

    args = _base_args(sandbox=sandbox)
    args.extend(["enable-shared-account", "--client-login", normalized_login])
    return get_runner().run_json(finalize_json_args(args, dry_run))


@mcp.tool(
    name="v4account_get_accounts",
    description="Read shared-account info via v4 Live AccountManagement (Get); pass logins and/or account_ids, or omit both to list all. Read-only. Call tool_help('v4account_get_accounts') for parameters.",
)
@handle_cli_errors
def v4account_get_accounts(
    logins: str | None = None,
    account_ids: str | None = None,
    dry_run: bool = False,
    sandbox: bool = False,
) -> dict | list[dict]:
    """Read shared-account info via v4 Live AccountManagement (Get action).

    Pass any combination of ``logins`` (comma-separated client logins,
    max 50) and ``account_ids`` (comma-separated shared account IDs,
    max 100). Both selectors together are forwarded as one
    ``SelectionCriteria`` to the v4 Live API; omit both to list every
    shared account the caller owns. This is a read-only operation and
    does not require dry_run or sandbox.

    Args:
        logins: Optional comma-separated client logins selector.
        account_ids: Optional comma-separated shared account IDs selector.
        dry_run: Show the direct request without sending it.
        sandbox: Execute against the Direct sandbox.
    """
    # An explicitly-passed selector that strips to empty (``logins=""`` or
    # ``account_ids="   "``) is treated as a user mistake, not as a request
    # to list every account. The unfiltered listing requires omitting the
    # selector argument entirely so the caller's intent is unambiguous.
    logins_provided = logins is not None
    account_ids_provided = account_ids is not None
    normalized_logins = logins.strip() if logins is not None else ""
    normalized_account_ids = account_ids.strip() if account_ids is not None else ""

    if logins_provided and not normalized_logins:
        return tool_error_dict(
            ToolError(
                error="empty_selector",
                message=(
                    "logins was provided but is empty after stripping whitespace; "
                    "omit the argument entirely to list every shared account."
                ),
            )
        )
    if account_ids_provided and not normalized_account_ids:
        return tool_error_dict(
            ToolError(
                error="empty_selector",
                message=(
                    "account_ids was provided but is empty after stripping "
                    "whitespace; omit the argument entirely to list every "
                    "shared account."
                ),
            )
        )

    args = _base_args(sandbox=sandbox)
    args.extend(["account-management", "--action", "Get"])
    # direct-cli 0.3.11 forwards both selectors into one ``SelectionCriteria``
    # block, so the wrapper passes through any combination instead of forcing
    # a single-selector dialect that the underlying CLI/API never imposed.
    if normalized_logins:
        args.extend(["--logins", normalized_logins])
    if normalized_account_ids:
        args.extend(["--account-ids", normalized_account_ids])
    return get_runner().run_json(finalize_json_args(args, dry_run))


@mcp.tool(
    name="v4account_update_account",
    description="Update shared-account settings (budget, SMS/email notifications) via v4 Live AccountManagement (Update); requires dry_run or sandbox. Call tool_help('v4account_update_account') for parameters.",
)
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
        return tool_error_dict(safety_error)

    # direct-cli requires day_budget and spend_mode to be set together (the
    # DayBudget block needs both Amount and Mode); one without the other is a
    # hard CLI error. Match the emission's blank-string handling. (#170-28)
    budget_set = bool(day_budget and day_budget.strip())
    mode_set = bool(spend_mode and spend_mode.strip())
    if budget_set != mode_set:
        return tool_error_dict(
            ToolError(
                error="day_budget_spend_mode_pair",
                message=(
                    "day_budget and spend_mode must be set together — direct-cli "
                    "rejects one without the other."
                ),
            )
        )

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

    return get_runner().run_json(finalize_json_args(args, dry_run))


@mcp.tool(
    name="v4account_deposit",
    description="Money operation: deposit funds into shared accounts via v4 Live AccountManagement (Deposit); finance tokens are env-only, requires dry_run or sandbox. Call tool_help('v4account_deposit') for parameters.",
)
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
        return tool_error_dict(safety_error)

    normalized = _normalize_payment(payment)
    if isinstance(normalized, ToolError):
        return tool_error_dict(normalized)

    normalized_currency = _require_non_empty(
        currency, field="currency", error="missing_currency"
    )
    if isinstance(normalized_currency, ToolError):
        return tool_error_dict(normalized_currency)

    args = _base_args(sandbox=sandbox)
    args.extend(["account-management", "--action", "Deposit"])
    for entry in normalized:
        args.extend(["--payment", entry])
    args.extend(["--currency", normalized_currency])
    _append_optional_text(args, "--origin", origin)
    _append_optional_text(args, "--contract", contract)
    _append_optional(args, "--operation-num", operation_num)

    return get_runner().run_json(finalize_json_args(args, dry_run))


@mcp.tool(
    name="v4account_invoice",
    description="Money operation: issue invoice payments via v4 Live AccountManagement (Invoice); finance tokens are env-only, requires dry_run or sandbox. Call tool_help('v4account_invoice') for parameters.",
)
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
        return tool_error_dict(safety_error)

    normalized = _normalize_payment(payment)
    if isinstance(normalized, ToolError):
        return tool_error_dict(normalized)

    normalized_currency = _require_non_empty(
        currency, field="currency", error="missing_currency"
    )
    if isinstance(normalized_currency, ToolError):
        return tool_error_dict(normalized_currency)

    args = _base_args(sandbox=sandbox)
    args.extend(["account-management", "--action", "Invoice"])
    for entry in normalized:
        args.extend(["--payment", entry])
    args.extend(["--currency", normalized_currency])
    _append_optional(args, "--operation-num", operation_num)

    return get_runner().run_json(finalize_json_args(args, dry_run))


@mcp.tool(
    name="v4account_transfer_money",
    description="Money operation: transfer funds between shared accounts via v4 Live AccountManagement (TransferMoney); finance tokens are env-only, requires dry_run or sandbox. Call tool_help('v4account_transfer_money') for parameters.",
)
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
        return tool_error_dict(safety_error)

    normalized_amount = _require_non_empty(
        amount, field="amount", error="missing_amount"
    )
    if isinstance(normalized_amount, ToolError):
        return tool_error_dict(normalized_amount)

    normalized_currency = _require_non_empty(
        currency, field="currency", error="missing_currency"
    )
    if isinstance(normalized_currency, ToolError):
        return tool_error_dict(normalized_currency)

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
            normalized_amount,
            "--currency",
            normalized_currency,
        ]
    )
    _append_optional(args, "--operation-num", operation_num)

    return get_runner().run_json(finalize_json_args(args, dry_run))
