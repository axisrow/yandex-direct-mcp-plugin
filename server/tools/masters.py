"""Read-only MCP tools for browser-backed Campaign Wizard campaigns."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import require_non_empty_csv, tool_error_dict

# Masters reads launch Playwright and may legitimately wait for direct-cli's
# 60-second SPA hydration bounds. Leave headroom for browser startup and, for
# ``--moderation-statuses``, the additional edit-page navigation.
MASTERS_READ_TIMEOUT_SECONDS = 120


@mcp.tool(
    name="masters_get",
    description="Get one or more Campaign Wizard (Master) campaigns by ID through the browser-only Direct UI. Read-only; optionally includes rejected moderation elements. Call tool_help('masters_get') for parameters.",
)
@handle_cli_errors
def masters_get(
    campaign_ids: str,
    moderation_statuses: bool = False,
) -> list[dict] | dict:
    """Get Campaign Wizard (Master) campaigns by ID.

    This wraps ``direct masters get``. Campaign Wizard campaigns have no
    Management API representation, so direct-cli reads the logged-in user's
    Direct UI with Playwright. This tool does not expose any Masters mutation.

    Args:
        campaign_ids: Comma-separated Campaign Wizard campaign IDs.
        moderation_statuses: Also read individually rejected ad elements from
            each campaign's edit page (``--moderation-statuses``). This adds
            ``RejectedElements``, ``RejectedCount``, and ``UnsupportedTypes``
            to each result.
    """
    normalized_ids = require_non_empty_csv(
        campaign_ids, error="missing_campaign_ids", noun="campaign ID"
    )
    if isinstance(normalized_ids, ToolError):
        return tool_error_dict(normalized_ids)

    args = ["masters", "get", normalized_ids]
    if moderation_statuses:
        args.append("--moderation-statuses")
    args.extend(["--format", "json"])
    return get_runner().run_json(args, timeout=MASTERS_READ_TIMEOUT_SECONDS)


@mcp.tool(
    name="masters_targetactions_get",
    description="Get the current target-action (CPA) goals for one Campaign Wizard campaign through the browser-only Direct UI. Read-only. Call tool_help('masters_targetactions_get') for parameters.",
)
@handle_cli_errors
def masters_targetactions_get(campaign_id: int) -> list[dict] | dict:
    """Get a Campaign Wizard campaign's current target-action goals.

    This wraps ``direct masters targetactions get``. An empty ``TargetActions``
    list is a valid result when the campaign does not use max-conversions or
    has no configured goal.

    Args:
        campaign_id: Campaign Wizard campaign ID.
    """
    return get_runner().run_json(
        [
            "masters",
            "targetactions",
            "get",
            str(campaign_id),
            "--format",
            "json",
        ],
        timeout=MASTERS_READ_TIMEOUT_SECONDS,
    )
