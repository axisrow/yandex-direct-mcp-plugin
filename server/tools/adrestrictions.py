"""MCP tool for browser-backed ad moderation restrictions."""

import os

from server.contract import PUBLIC_CONTRACT
from server.main import mcp
from server.tools import get_browser_runner, handle_cli_errors
from server.tools.browser_helpers import browser_session_args
from server.tools.helpers import normalize_optional_str


def _command_path() -> list[str]:
    """Return the direct CLI path declared by the public contract."""
    tool = next(
        item for item in PUBLIC_CONTRACT if item.public_name == "adrestrictions_get"
    )
    if tool.cli_subcommand_path is None:
        raise RuntimeError("adrestrictions_get has no direct CLI command path")
    return list(tool.cli_subcommand_path)


@mcp.tool(
    name="adrestrictions_get",
    description="Read a campaign's ads with their UI moderation restrictions. Call tool_help('adrestrictions_get') for parameters.",
)
@handle_cli_errors
def adrestrictions_get(
    campaign_id: str, group_ids: str | None = None
) -> list[dict] | dict:
    """Read the campaign's ads element-by-element with their UI restrictions.

    Opens the web UI's banners grid for the campaign and reads its own data
    calls (``ads:list`` + ``AdDisclaimers`` + ``ads:batchGet``): every headline,
    text, image and video of every ad, each with the ad's restriction warnings —
    the machine reason (moderation flags, aggregated-status reasons) and the
    UI's verbatim explanation (the «Добавлено предупреждение» popup texts, e.g.
    the «Медицина и фармацевтика» category notice).

    The warning granularity is the ad — that is what the UI's own popup shows
    and what its data calls carry; a per-headline split does not exist in any
    data surface. Read-only, browser-backed: uses the same logged-in Direct web
    session as the masters tools (the browser's account is authoritative).

    Args:
        campaign_id: Campaign ID.
        group_ids: Optional comma-separated ad group IDs; default: all the
            groups the page loads.

    Returns:
        The ads with their restriction warnings, or a structured error dict
        when the browser session or the page read fails.
    """
    args = [*_command_path(), str(campaign_id)]

    normalized_groups = normalize_optional_str(group_ids)
    if normalized_groups is not None:
        args.extend(["--group-ids", normalized_groups])

    args.extend(browser_session_args(os.environ))
    args.extend(["--format", "json"])
    return get_browser_runner().run_json_lenient(args)
