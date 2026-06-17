"""MCP tools for agency client management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import validate_yes_no


@mcp.tool(
    name="agencyclients_get",
    description="List agency clients, optionally filtered by logins or archived state. Call tool_help('agencyclients_get') for parameters.",
)
@handle_cli_errors
def agency_clients_list(
    logins: str | None = None,
    archived: str | None = None,
    limit: int | None = None,
    fetch_all: bool = False,
    fields: str | None = None,
) -> list[dict] | dict:
    """List agency clients.

    CLI 0.3.8 `agencyclients get` accepts `--logins` (not `--ids`) and an
    `--archived [YES|NO]` filter (default NO).

    Args:
        logins: Comma-separated client logins to filter by.
        archived: Filter archived clients — "YES" or "NO".
        limit: Limit number of results.
        fetch_all: Fetch all pages.
        fields: Comma-separated field names.
    """
    if archived is not None:
        err = validate_yes_no(archived, field="archived", error="invalid_archived")
        if err is not None:
            return err.__dict__

    runner = get_runner()
    cmd = ["agencyclients", "get", "--format", "json"]
    normalized_logins = logins.strip() if logins is not None else None
    if normalized_logins:
        cmd.extend(["--logins", normalized_logins])
    if archived is not None:
        cmd.extend(["--archived", archived])
    if limit is not None:
        cmd.extend(["--limit", str(limit)])
    if fetch_all:
        cmd.append("--fetch-all")
    if fields is not None:
        cmd.extend(["--fields", fields])

    return runner.run_json(cmd)


@mcp.tool(
    name="agencyclients_add",
    description="Add a new client to the agency (mirrors WSDL ClientAddItem); use agencyclients_add_passport_organization for a Passport-backed client. Call tool_help('agencyclients_add') for parameters.",
)
@handle_cli_errors
def agency_clients_add(
    login: str,
    first_name: str,
    last_name: str,
    currency: str,
    notification_email: str | None = None,
    notification_lang: str | None = None,
    send_account_news: bool | None = None,
    send_warnings: bool | None = None,
    dry_run: bool = False,
) -> dict:
    """Add a client to an agency.

    CLI 0.3.8 dropped --json. Mirrors WSDL ClientAddItem.

    Args:
        login: Client login.
        first_name: First name.
        last_name: Last name.
        currency: Account currency code, e.g. "RUB".
        notification_email: Notification email.
        notification_lang: Notification language code, e.g. "RU".
        send_account_news: Whether to send account news emails.
        send_warnings: Whether to send warning emails.
        dry_run: Show the direct request without sending it.
    """
    args = [
        "agencyclients",
        "add",
        "--login",
        login,
        "--first-name",
        first_name,
        "--last-name",
        last_name,
        "--currency",
        currency,
    ]
    if notification_email is not None:
        args.extend(["--notification-email", notification_email])
    if notification_lang is not None:
        args.extend(["--notification-lang", notification_lang])
    if send_account_news is not None:
        args.append(
            "--send-account-news" if send_account_news else "--no-send-account-news"
        )
    if send_warnings is not None:
        args.append("--send-warnings" if send_warnings else "--no-send-warnings")
    if dry_run:
        args.append("--dry-run")
    return get_runner().run_json(args)


@mcp.tool(
    name="agencyclients_delete",
    description="Remove a client from the agency (no real Direct API backing; kept for completeness). Call tool_help('agencyclients_delete') for parameters.",
)
@handle_cli_errors
def agency_clients_delete(id: int) -> dict:
    """Remove a client from an agency.

    Note: The Yandex Direct API does not actually support deleting
    agency clients. This tool is kept for completeness.

    Args:
        id: Client ID to remove.
    """
    runner = get_runner()
    result = runner.run_json(["agencyclients", "delete", "--id", str(id)])
    return result


@mcp.tool(
    name="agencyclients_update",
    description="Update an agency client's settings, contacts and grants (mirrors WSDL ClientUpdateItem). Call tool_help('agencyclients_update') for parameters.",
)
@handle_cli_errors
def agency_clients_update(
    client_id: int,
    client_info: str | None = None,
    phone: str | None = None,
    notification_email: str | None = None,
    notification_lang: str | None = None,
    email_subscriptions: list[str] | None = None,
    settings: list[str] | None = None,
    tin_type: str | None = None,
    tin: str | None = None,
    grants: list[str] | None = None,
    clear_grants: bool = False,
    dry_run: bool = False,
) -> dict:
    """Update an agency client.

    CLI 0.3.8 dropped --json and exposes the full typed surface mirroring
    WSDL ClientUpdateItem. Note: the previous tool exposed a non-existent
    --email flag — the correct one is --notification-email.

    Args:
        client_id: Client ID.
        client_info: Free-form client information / display name.
        phone: Client phone.
        notification_email: Notification email.
        notification_lang: Notification language code.
        email_subscriptions: List of OPTION=YES|NO entries.
        settings: List of OPTION=YES|NO entries.
        tin_type: TIN type.
        tin: Taxpayer identification number.
        grants: List of PRIVILEGE=YES|NO entries (repeats CLI's --grant flag).
        clear_grants: Whether to clear all grants. Mutually exclusive with grants.
        dry_run: Show the direct request without sending it.
    """
    if not any(
        (
            client_info,
            phone,
            notification_email,
            notification_lang,
            email_subscriptions,
            settings,
            tin_type,
            tin,
            grants,
            clear_grants,
        )
    ):
        return ToolError(
            error="missing_update_fields",
            message=(
                "Provide at least one of: client_info, phone, notification_email, "
                "notification_lang, email_subscriptions, settings, tin_type, tin, "
                "grants, clear_grants"
            ),
        ).__dict__
    if grants and clear_grants:
        return ToolError(
            error="conflicting_grants",
            message="Pass grants or clear_grants, not both.",
        ).__dict__

    args = ["agencyclients", "update", "--client-id", str(client_id)]
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
    if grants:
        for grant in grants:
            args.extend(["--grant", grant])
    if clear_grants:
        args.append("--clear-grants")
    if dry_run:
        args.append("--dry-run")

    return get_runner().run_json(args)


@mcp.tool(
    name="agencyclients_add_passport_organization",
    description="Add a new agency client backed by a Passport organization; use agencyclients_add for a regular client. Call tool_help('agencyclients_add_passport_organization') for parameters.",
)
@handle_cli_errors
def agency_clients_add_passport_organization(
    name: str,
    currency: str,
    notification_email: str | None = None,
    notification_lang: str | None = None,
    send_account_news: bool | None = None,
    send_warnings: bool | None = None,
    dry_run: bool = False,
) -> dict:
    """Add a new agency client backed by a Passport organization.

    Args:
        name: Display name for the new client account.
        currency: Account currency code, e.g. "RUB".
        notification_email: Email address for system notifications.
        notification_lang: Notification language code, e.g. "RU".
        send_account_news: Whether to send account news emails.
        send_warnings: Whether to send warning emails.
        dry_run: Show the direct request without sending it.
    """
    args = [
        "agencyclients",
        "add-passport-organization",
        "--name",
        name,
        "--currency",
        currency,
    ]
    if notification_email is not None:
        args.extend(["--notification-email", notification_email])
    if notification_lang is not None:
        args.extend(["--notification-lang", notification_lang])
    if send_account_news is not None:
        flag = "--send-account-news" if send_account_news else "--no-send-account-news"
        args.append(flag)
    if send_warnings is not None:
        flag = "--send-warnings" if send_warnings else "--no-send-warnings"
        args.append(flag)
    if dry_run:
        args.append("--dry-run")

    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(
    name="agencyclients_add_passport_organization_member",
    description="Invite a user to a Passport organization client account. Call tool_help('agencyclients_add_passport_organization_member') for parameters.",
)
@handle_cli_errors
def agency_clients_add_passport_organization_member(
    passport_organization_login: str,
    role: str,
    invite_email: str | None = None,
    invite_phone: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Invite a user to a Passport organization client account.

    Args:
        passport_organization_login: Login of the Passport organization to invite to.
        role: Role to assign to the invited user, e.g. "CHIEF".
        invite_email: Email address to send the invitation to.
        invite_phone: Phone number to send the invitation to.
        dry_run: Show the direct request without sending it.
    """
    args = [
        "agencyclients",
        "add-passport-organization-member",
        "--passport-organization-login",
        passport_organization_login,
        "--role",
        role,
    ]
    if invite_email is not None:
        args.extend(["--invite-email", invite_email])
    if invite_phone is not None:
        args.extend(["--invite-phone", invite_phone])
    if dry_run:
        args.append("--dry-run")

    runner = get_runner()
    return runner.run_json(args)
