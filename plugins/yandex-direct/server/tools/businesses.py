"""MCP tools for business management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors
from server.tools.helpers import append_pagination


@mcp.tool(
    name="businesses_get",
    description="List Yandex.Business profiles (organizations) for the account. Call tool_help('businesses_get') for parameters.",
)
@handle_cli_errors
def businesses_list(
    ids: str | None = None,
    limit: int | None = None,
    fetch_all: bool = False,
    fields: str | None = None,
) -> list[dict] | dict:
    """List businesses.

    Args:
        ids: Comma-separated business IDs.
        limit: Limit number of results.
        fetch_all: Fetch all pages.
        fields: Comma-separated field names.
    """
    args = ["businesses", "get", "--format", "json"]
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        args.extend(["--ids", normalized_ids])
    append_pagination(args, limit, fetch_all, fields)
    return get_runner().run_json(args)
