"""MCP tool for listing ads."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors

MAX_BATCH_SIZE = 10
FOREIGN_CAMPAIGN_MIN = 73_000_000
FOREIGN_CAMPAIGN_MAX = 77_999_999


def _parse_ids(ids_str: str) -> list[str]:
    """Parse and clean comma-separated IDs."""
    return [id.strip() for id in ids_str.split(",") if id.strip()]


def _check_batch_limit(ids_str: str) -> ToolError | None:
    """Validate batch size of comma-separated IDs."""
    ids = _parse_ids(ids_str)
    if len(ids) > MAX_BATCH_SIZE:
        return ToolError(error="batch_limit", message=f"Maximum {MAX_BATCH_SIZE} IDs per request. Got: {len(ids)}")
    return None


def _get_foreign_campaign_id(ids_str: str) -> str | None:
    """Return the first campaign ID in the foreign account range (73M-77M), or None."""
    for id_str in _parse_ids(ids_str):
        try:
            cid = int(id_str)
            if FOREIGN_CAMPAIGN_MIN <= cid <= FOREIGN_CAMPAIGN_MAX:
                return id_str
        except ValueError:
            continue
    return None


@mcp.tool()
@handle_cli_errors
def ads_list(campaign_ids: str) -> list[dict] | dict:
    """List ads in specified campaigns.

    Args:
        campaign_ids: Comma-separated campaign IDs (max 10).
    """
    batch_error = _check_batch_limit(campaign_ids)
    if batch_error:
        return batch_error.__dict__

    foreign_id = _get_foreign_campaign_id(campaign_ids)
    if foreign_id:
        return ToolError(
            error="foreign_campaign",
            message=f"Campaign {foreign_id} is unavailable — belongs to another account",
        ).__dict__

    runner = get_runner()
    return runner.run_json(["ads", "get", "--campaign-ids", campaign_ids, "--format", "json"])
