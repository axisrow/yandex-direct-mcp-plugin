"""MCP tools for agency client management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors


@mcp.tool(name="agencyclients_get")
@handle_cli_errors
def agency_clients_list(ids: str | None = None) -> list[dict] | dict:
    """List agency clients.

    Args:
        ids: Comma-separated client IDs to filter by (optional).
    """
    runner = get_runner()
    cmd = ["agencyclients", "get", "--format", "json"]
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        cmd.extend(["--ids", normalized_ids])

    result = runner.run_json(cmd)
    return result


@mcp.tool(name="agencyclients_add")
@handle_cli_errors
def agency_clients_add(client_json: str) -> dict:
    """Add a client to an agency.

    Args:
        client_json: JSON string containing client information.
    """
    runner = get_runner()
    result = runner.run_json(["agencyclients", "add", "--json", client_json])
    return result


@mcp.tool(name="agencyclients_delete")
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


@mcp.tool(name="agencyclients_update")
@handle_cli_errors
def agency_clients_update(
    client_id: int,
    phone: str | None = None,
    email: str | None = None,
    grant: str | None = None,
    clear_grants: bool = False,
) -> dict:
    """Update an agency client.

    Args:
        client_id: Client ID.
        phone: Client phone.
        email: Client email.
        grant: Grant value to add.
        clear_grants: Whether to clear all grants.
    """
    if not any((phone, email, grant, clear_grants)):
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one of: phone, email, grant, clear_grants",
        ).__dict__

    args = ["agencyclients", "update", "--client-id", str(client_id)]
    if phone is not None:
        args.extend(["--phone", phone])
    if email is not None:
        args.extend(["--email", email])
    if grant is not None:
        args.extend(["--grant", grant])
    if clear_grants:
        args.append("--clear-grants")

    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(name="agencyclients_add_passport_organization")
@handle_cli_errors
def agency_clients_add_passport_organization(
    name: str,
    currency: str,
    notification_email: str | None = None,
    notification_lang: str | None = None,
    send_account_news: bool | None = None,
    send_warnings: bool | None = None,
) -> dict:
    """Add a new agency client backed by a Passport organization.

    Args:
        name: Display name for the new client account.
        currency: Account currency code, e.g. "RUB".
        notification_email: Email address for system notifications (optional).
        notification_lang: Notification language code, e.g. "RU" (optional).
        send_account_news: Whether to send account news emails (optional).
        send_warnings: Whether to send warning emails (optional).
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

    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(name="agencyclients_add_passport_organization_member")
@handle_cli_errors
def agency_clients_add_passport_organization_member(
    passport_organization_login: str,
    role: str,
    invite_email: str | None = None,
    invite_phone: str | None = None,
) -> dict:
    """Invite a user to a Passport organization client account.

    Args:
        passport_organization_login: Login of the Passport organization to invite to.
        role: Role to assign to the invited user, e.g. "CHIEF".
        invite_email: Email address to send the invitation to (optional).
        invite_phone: Phone number to send the invitation to (optional).
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

    runner = get_runner()
    return runner.run_json(args)
