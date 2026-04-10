"""MCP tools for bid modifier management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit


@mcp.tool()
@handle_cli_errors
def bidmodifiers_list(
    campaign_ids: str | None = None,
    ad_group_ids: str | None = None,
) -> list[dict] | dict:
    """List bid modifiers.

    Args:
        campaign_ids: Comma-separated campaign IDs (optional, max 10).
        ad_group_ids: Comma-separated ad group IDs (optional, max 10).
    """
    args = ["bidmodifiers", "get", "--format", "json"]
    if campaign_ids is not None:
        batch_error = check_batch_limit(campaign_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--campaign-ids", campaign_ids])
    if ad_group_ids is not None:
        batch_error = check_batch_limit(ad_group_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--adgroup-ids", ad_group_ids])

    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def bidmodifiers_set(
    campaign_id: str,
    modifier_type: str,
    value: str,
    extra_json: str | None = None,
) -> dict:
    """Set bid modifier for a campaign.

    Args:
        campaign_id: Campaign ID.
        modifier_type: Type of modifier (e.g., "DEMOGRAPHICS", "MOBILE").
        value: Modifier value (float, e.g. "1.5" for 50% increase).
        extra_json: Optional JSON string with additional parameters.
    """
    args = [
        "bidmodifiers",
        "set",
        "--campaign-id",
        campaign_id,
        "--type",
        modifier_type,
        "--value",
        value,
    ]
    if extra_json is not None:
        args.extend(["--json", extra_json])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def bidmodifiers_toggle(id: str, enabled: bool = True) -> dict:
    """Toggle bid modifier on/off.

    Args:
        id: Modifier ID.
        enabled: True to enable, False to disable.
    """
    flag = "--enabled" if enabled else "--disabled"
    runner = get_runner()
    return runner.run_json(["bidmodifiers", "toggle", "--id", id, flag])


@mcp.tool()
@handle_cli_errors
def bidmodifiers_delete(ids: str) -> dict:
    """Delete bid modifiers.

    Args:
        ids: Comma-separated modifier IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "bidmodifiers", "delete", ids)
