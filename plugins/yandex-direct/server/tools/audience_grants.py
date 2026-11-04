"""MCP tools for Yandex Audience segment grants (transport: `yac`)."""

from server.main import mcp
from server.tools import get_audience_runner, handle_cli_errors


@mcp.tool(
    name="audience_grants_list",
    description="List access grants (permissions) on a Yandex Audience segment. Call tool_help('audience_grants_list') for parameters.",
)
@handle_cli_errors
def audience_grants_list(segment_id: str) -> list[dict] | dict:
    """List grants on a segment.

    Transport: `yac grants list <id>`. Read-only. Each grant carries the
    granted login and the permission level (view / edit).

    Args:
        segment_id: Segment ID whose grants to list.
    """
    return get_audience_runner().run_json(["grants", "list", segment_id.strip()])


@mcp.tool(
    name="audience_grants_add",
    description="Grant another Yandex login access (view/edit) to a segment (MUTATING: shares the segment). Call tool_help('audience_grants_add') for parameters.",
)
@handle_cli_errors
def audience_grants_add(
    segment_id: str,
    user_login: str,
    permission: str | None = None,
    comment: str | None = None,
) -> list[dict] | dict:
    """Grant access to a segment.

    Transport: `yac grants add <id> --user-login <login>`. MUTATING: shares
    the segment with another account — the recipient sees the segment's data.

    Args:
        segment_id: Segment ID to share.
        user_login: Yandex login of the grant recipient.
        permission: edit | view (optional; API default applies when omitted).
        comment: Optional comment for the recipient.
    """
    args = ["grants", "add", segment_id.strip(), "--user-login", user_login]
    if permission is not None:
        args.extend(["--permission", permission])
    if comment is not None:
        args.extend(["--comment", comment])
    return get_audience_runner().run_json(args)


@mcp.tool(
    name="audience_grants_remove",
    description="Revoke a login's access to a Yandex Audience segment (MUTATING: removes the grant). Call tool_help('audience_grants_remove') for parameters.",
)
@handle_cli_errors
def audience_grants_remove(segment_id: str, user_login: str) -> list[dict] | dict:
    """Remove a grant from a segment.

    Transport: `yac grants remove <id> --user-login <login>`. MUTATING:
    revokes the recipient's access (the segment data itself is untouched).

    Args:
        segment_id: Segment ID.
        user_login: Yandex login whose grant to remove.
    """
    return get_audience_runner().run_json(
        ["grants", "remove", segment_id.strip(), "--user-login", user_login]
    )
