"""MCP tools for Yandex Audience account info (transport: `yac`)."""

from server.main import mcp
from server.tools import get_audience_runner, handle_cli_errors


@mcp.tool(
    name="audience_accounts_list",
    description="List Yandex Audience accounts where the current login is a representative. Call tool_help('audience_accounts_list') for parameters.",
)
@handle_cli_errors
def audience_accounts_list() -> list[dict] | dict:
    """List representative accounts.

    Transport: `yac accounts list`. Read-only. Returns the Audience accounts
    the authenticated login can act on behalf of; an empty list means the
    login is not a representative anywhere.
    """
    return get_audience_runner().run_json(["accounts", "list"])
