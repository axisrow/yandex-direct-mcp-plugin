"""MCP tools for client management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors


@mcp.tool()
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


@mcp.tool()
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
        )
    ):
        return ToolError(
            error="missing_update_fields",
            message=(
                "Provide at least one of: client_info, phone, notification_email, "
                "notification_lang, email_subscriptions, settings, tin_type, tin"
            ),
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
    if dry_run:
        args.append("--dry-run")
    return get_runner().run_json(args)
