"""MCP tools for Yandex Audience delegates (representatives) (transport: `yac`)."""

from server.main import mcp
from server.tools import get_audience_runner, handle_cli_errors


@mcp.tool(
    name="audience_delegates_list",
    description="List Yandex Audience delegates (representatives) of the current account. Call tool_help('audience_delegates_list') for parameters.",
)
@handle_cli_errors
def audience_delegates_list() -> list[dict] | dict:
    """List delegates.

    Transport: `yac delegates list`. Read-only. Each delegate carries the
    login and permission level (view / edit).
    """
    return get_audience_runner().run_json(["delegates", "list"])


@mcp.tool(
    name="audience_delegates_add",
    description="Add a delegate (representative) to the Yandex Audience account (MUTATING: grants account-level access). Call tool_help('audience_delegates_add') for parameters.",
)
@handle_cli_errors
def audience_delegates_add(
    user_login: str,
    perm: str | None = None,
    comment: str | None = None,
) -> list[dict] | dict:
    """Add a delegate.

    Transport: `yac delegates add --user-login <login>`. MUTATING: grants
    another login account-level representative access (wider than a
    per-segment grant — see audience_grants_add).

    Args:
        user_login: Yandex login of the delegate.
        perm: view | edit (optional; API default applies when omitted).
        comment: Optional comment.
    """
    args = ["delegates", "add", "--user-login", user_login]
    if perm is not None:
        args.extend(["--perm", perm])
    if comment is not None:
        args.extend(["--comment", comment])
    return get_audience_runner().run_json(args)


@mcp.tool(
    name="audience_delegates_remove",
    description="Remove a delegate (representative) from the Yandex Audience account (MUTATING: revokes account-level access). Call tool_help('audience_delegates_remove') for parameters.",
)
@handle_cli_errors
def audience_delegates_remove(user_login: str) -> list[dict] | dict:
    """Remove a delegate.

    Transport: `yac delegates remove --user-login <login>`. MUTATING: revokes
    the delegate's account-level access.

    Args:
        user_login: Yandex login of the delegate to remove.
    """
    return get_audience_runner().run_json(
        ["delegates", "remove", "--user-login", user_login]
    )
