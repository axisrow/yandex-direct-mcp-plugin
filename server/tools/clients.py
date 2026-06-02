"""MCP tools for client management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import CliOption, append_cli_options, provided_update_value

ERIR_OPTIONS = (
    CliOption("erir_organization_name", "--erir-organization-name"),
    CliOption("erir_organization_kpp", "--erir-organization-kpp"),
    CliOption("erir_organization_epay_number", "--erir-organization-epay-number"),
    CliOption("erir_organization_reg_number", "--erir-organization-reg-number"),
    CliOption("erir_organization_oksm_number", "--erir-organization-oksm-number"),
    CliOption("erir_organization_okved_code", "--erir-organization-okved-code"),
    CliOption("erir_contract_number", "--erir-contract-number"),
    CliOption("erir_contract_date", "--erir-contract-date"),
    CliOption("erir_contract_type", "--erir-contract-type"),
    CliOption("erir_contract_action_type", "--erir-contract-action-type"),
    CliOption("erir_contract_subject_type", "--erir-contract-subject-type"),
    CliOption("erir_contract_is_agency_payment", "--erir-contract-is-agency-payment"),
    CliOption("erir_contract_price_amount", "--erir-contract-price-amount"),
    CliOption(
        "erir_contract_price_including_vat",
        "--erir-contract-price-including-vat",
    ),
    CliOption("erir_contragent_name", "--erir-contragent-name"),
    CliOption("erir_contragent_kpp", "--erir-contragent-kpp"),
    CliOption("erir_contragent_phone", "--erir-contragent-phone"),
    CliOption("erir_contragent_epay_number", "--erir-contragent-epay-number"),
    CliOption("erir_contragent_reg_number", "--erir-contragent-reg-number"),
    CliOption("erir_contragent_oksm_number", "--erir-contragent-oksm-number"),
    CliOption("erir_contragent_tin_type", "--erir-contragent-tin-type"),
    CliOption("erir_contragent_tin", "--erir-contragent-tin"),
)


@mcp.tool(
    description="Get information about clients by IDs (the authenticated account or its sub-clients). Call tool_help('clients_get') for parameters.",
)
@handle_cli_errors
def clients_get(
    ids: str | None = None,
    limit: int | None = None,
    fetch_all: bool = False,
    fields: str | None = None,
) -> dict:
    """Get client information.

    Args:
        ids: Comma-separated client IDs.
        limit: Limit number of results.
        fetch_all: Fetch all pages.
        fields: Comma-separated field names.
    """
    cmd = ["clients", "get", "--format", "json"]
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        cmd.extend(["--ids", normalized_ids])
    if limit is not None:
        cmd.extend(["--limit", str(limit)])
    if fetch_all:
        cmd.append("--fetch-all")
    if fields is not None:
        cmd.extend(["--fields", fields])
    return get_runner().run_json(cmd)


@mcp.tool(
    description="Update the authenticated client's settings and ERIR organization/contract/contragent fields. Call tool_help('clients_update') for parameters.",
)
@handle_cli_errors
def clients_update(
    client_info: str | None = None,
    phone: str | None = None,
    notification_email: str | None = None,
    notification_lang: str | None = None,
    email_subscriptions: list[str] | None = None,
    settings: list[str] | None = None,
    tin_type: str | None = None,
    tin: str | None = None,
    erir_organization_name: str | None = None,
    erir_organization_kpp: str | None = None,
    erir_organization_epay_number: str | None = None,
    erir_organization_reg_number: str | None = None,
    erir_organization_oksm_number: str | None = None,
    erir_organization_okved_code: str | None = None,
    erir_contract_number: str | None = None,
    erir_contract_date: str | None = None,
    erir_contract_type: str | None = None,
    erir_contract_action_type: str | None = None,
    erir_contract_subject_type: str | None = None,
    erir_contract_is_agency_payment: str | None = None,
    erir_contract_price_amount: str | None = None,
    erir_contract_price_including_vat: str | None = None,
    erir_contragent_name: str | None = None,
    erir_contragent_kpp: str | None = None,
    erir_contragent_phone: str | None = None,
    erir_contragent_epay_number: str | None = None,
    erir_contragent_reg_number: str | None = None,
    erir_contragent_oksm_number: str | None = None,
    erir_contragent_tin_type: str | None = None,
    erir_contragent_tin: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Update the authenticated client's settings.

    CLI 0.3.8 dropped --json and acts on the currently authenticated client
    (there is no --client-id flag — use the agency layer to switch context
    via --login at the global `direct` level).

    Args:
        client_info: Free-form client information / display name.
        phone: Client phone.
        notification_email: Notification email.
        notification_lang: Notification language.
        email_subscriptions: List of OPTION=YES|NO entries (repeats CLI's
            --email-subscription flag).
        settings: List of OPTION=YES|NO entries (repeats CLI's --setting flag).
        tin_type: TIN type.
        tin: Taxpayer identification number.
        erir_organization_*: ERIR organization fields, including name, KPP,
            ePay number, registration number, OKSM number, and OKVED code.
        erir_contract_*: ERIR contract fields, including number, date, type,
            action type, subject type, agency payment, price amount, and VAT flag.
        erir_contragent_*: ERIR contragent fields, including name, KPP, phone,
            ePay number, registration number, OKSM number, TIN type, and TIN.
        dry_run: Show the direct request without sending it.
    """
    values = locals()
    if not any(
        provided_update_value(value)
        for key, value in values.items()
        if key not in {"dry_run"}
    ):
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one typed client field to update.",
        ).__dict__

    args = ["clients", "update"]
    if client_info is not None:
        args.extend(["--client-info", client_info])
    if phone is not None:
        args.extend(["--phone", phone])
    if notification_email is not None:
        args.extend(["--notification-email", notification_email])
    if notification_lang is not None:
        args.extend(["--notification-lang", notification_lang])
    if email_subscriptions:
        for item in email_subscriptions:
            args.extend(["--email-subscription", item])
    if settings:
        for item in settings:
            args.extend(["--setting", item])
    if tin_type is not None:
        args.extend(["--tin-type", tin_type])
    if tin is not None:
        args.extend(["--tin", tin])
    append_cli_options(args, values, ERIR_OPTIONS)
    if dry_run:
        args.append("--dry-run")
    return get_runner().run_json(args)
