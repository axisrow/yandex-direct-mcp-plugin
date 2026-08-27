"""Read-only MCP tools for browser-backed Campaign Wizard campaigns."""

import os
from typing import cast

from server.contract import PUBLIC_CONTRACT
from server.main import mcp
from server.tools import ToolError, get_browser_runner, handle_cli_errors
from server.tools.browser_helpers import browser_session_args
from server.tools.helpers import (
    CliOption,
    append_cli_options,
    finalize_json_args,
    require_non_empty_csv,
    tool_error_dict,
    validate_enum,
)

MASTERS_STATUS_CHOICES = (
    "not-archived",
    "active",
    "stopped",
    "archived",
    "all",
)

MASTERS_LIST_OPTIONS = (CliOption("status", "--status"),)
MASTERS_GET_OPTIONS = (
    CliOption("moderation_statuses", "--moderation-statuses", is_flag=True),
    CliOption("tracking_params", "--tracking-params", is_flag=True),
)

_CONTRACT_BY_NAME = {tool.public_name: tool for tool in PUBLIC_CONTRACT}


def _command_path(tool_name: str) -> list[str]:
    """Return the full direct CLI path declared by the public contract."""
    tool = _CONTRACT_BY_NAME[tool_name]
    if tool.cli_subcommand_path is not None:
        return list(tool.cli_subcommand_path)
    if tool.cli_service is None or tool.cli_subcommand is None:
        raise RuntimeError(f"{tool_name} has no direct CLI command path")
    return [tool.cli_service, tool.cli_subcommand]


def _run_browser_json(args: list[str]) -> list[dict] | dict:
    args.extend(browser_session_args(os.environ))
    finalize_json_args(args, False)
    return get_browser_runner().run_json_lenient(args)


@mcp.tool(
    name="masters_list",
    description="List Campaign Wizard campaigns by status (browser-backed, read-only). Call tool_help('masters_list') for parameters.",
)
@handle_cli_errors
def masters_list(status: str = "not-archived") -> list[dict] | dict:
    """List Campaign Wizard campaigns from the logged-in browser account.

    Args:
        status: Status filter: not-archived, active, stopped, archived, or all.
    """
    enum_error = validate_enum(
        status,
        MASTERS_STATUS_CHOICES,
        field="status",
        error="invalid_status",
    )
    if enum_error:
        return tool_error_dict(enum_error)

    args = _command_path("masters_list")
    append_cli_options(args, locals(), MASTERS_LIST_OPTIONS)
    return _run_browser_json(args)


@mcp.tool(
    name="masters_get",
    description="Get Campaign Wizard campaigns by ID (browser-backed, read-only). Call tool_help('masters_get') for parameters.",
)
@handle_cli_errors
def masters_get(
    campaign_ids: str,
    moderation_statuses: bool = False,
    tracking_params: bool = False,
) -> list[dict] | dict:
    """Get one or more Campaign Wizard campaigns by comma-separated ID.

    Args:
        campaign_ids: Comma-separated campaign IDs.
        moderation_statuses: Include per-image moderation rejection details.
        tracking_params: Include UTM and URL tracking parameters.
    """
    normalized_ids = require_non_empty_csv(
        campaign_ids,
        error="missing_campaign_ids",
        noun="campaign ID",
    )
    if isinstance(normalized_ids, ToolError):
        return tool_error_dict(normalized_ids)

    args = [*_command_path("masters_get"), normalized_ids]
    append_cli_options(args, locals(), MASTERS_GET_OPTIONS)
    return _run_browser_json(args)


def _get_campaign_resource(tool_name: str, campaign_id: str) -> dict:
    # Keep object IDs as strings at the MCP boundary: JavaScript hosts can round
    # int64 values before Python sees them. Click still validates this token as INT.
    return cast(
        dict,
        _run_browser_json([*_command_path(tool_name), str(campaign_id)]),
    )


@mcp.tool(
    name="masters_adimages_get",
    description="Get Campaign Wizard images (browser-backed, read-only). Call tool_help('masters_adimages_get') for parameters.",
)
@handle_cli_errors
def masters_adimages_get(campaign_id: str) -> dict:
    """Get the campaign's current image set.

    Args:
        campaign_id: Campaign ID.
    """
    return _get_campaign_resource("masters_adimages_get", campaign_id)


@mcp.tool(
    name="masters_targetactions_get",
    description="Get Campaign Wizard target actions (browser-backed, read-only). Call tool_help('masters_targetactions_get') for parameters.",
)
@handle_cli_errors
def masters_targetactions_get(campaign_id: str) -> dict:
    """Get the campaign's target-action goals and prices.

    Args:
        campaign_id: Campaign ID.
    """
    return _get_campaign_resource("masters_targetactions_get", campaign_id)


@mcp.tool(
    name="masters_counters_get",
    description="Get Campaign Wizard Metrika counters (browser-backed, read-only). Call tool_help('masters_counters_get') for parameters.",
)
@handle_cli_errors
def masters_counters_get(campaign_id: str) -> dict:
    """Get the campaign's linked Yandex Metrika counters.

    Args:
        campaign_id: Campaign ID.
    """
    return _get_campaign_resource("masters_counters_get", campaign_id)


@mcp.tool(
    name="masters_audience_get",
    description="Get Campaign Wizard audience settings (browser-backed, read-only). Call tool_help('masters_audience_get') for parameters.",
)
@handle_cli_errors
def masters_audience_get(campaign_id: str) -> dict:
    """Get the campaign's manual audience settings.

    Args:
        campaign_id: Campaign ID.
    """
    return _get_campaign_resource("masters_audience_get", campaign_id)
