"""MCP tools for Yandex Direct v4 Live account balance."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors


@mcp.tool(name="balance_get")
@handle_cli_errors
def balance_get(logins: str | None = None) -> dict | list[dict]:
    """Get account money balance via the v4 Live AccountManagement method.

    Args:
        logins: Optional comma-separated client logins.
    """
    args = ["balance", "--format", "json"]
    normalized_logins = logins.strip() if logins is not None else None
    if normalized_logins:
        args.extend(["--logins", normalized_logins])
    return get_runner().run_json(args)
