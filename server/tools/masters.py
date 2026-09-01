"""MCP tools for browser-backed Campaign Wizard campaigns."""

import os
from typing import cast

from server.contract import PUBLIC_CONTRACT
from server.main import mcp
from server.tools import ToolError, get_browser_runner, handle_cli_errors
from server.tools.browser_helpers import browser_session_args
from server.tools.helpers import (
    CliOption,
    append_cli_options,
    check_batch_limit,
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


def _run_browser_json(
    args: list[str], *, allow_nonzero: bool = False
) -> list[dict] | dict:
    args.extend(browser_session_args(os.environ))
    finalize_json_args(args, False)
    runner = get_browser_runner()
    if allow_nonzero:
        return runner.run_json_lenient(args, allow_nonzero=True)
    return runner.run_json_lenient(args)


@mcp.tool(
    name="masters_list",
    description="Read Campaign Wizard campaigns by status. See tool_help('masters_list').",
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
    description="Read Campaign Wizard campaigns by ID. See tool_help('masters_get').",
)
@handle_cli_errors
def masters_get(
    campaign_ids: str,
    moderation_statuses: bool = False,
    tracking_params: bool = False,
) -> list[dict] | dict:
    """Get one or more Campaign Wizard campaigns by comma-separated ID.

    ``tracking_params=True`` requires a direct-cli release containing commit
    https://github.com/axisrow/direct-cli/commit/4ce5b27. The published 0.5.2
    wheel predates that read flag; the default call remains compatible with it.

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


def _run_campaign_batch(tool_name: str, campaign_ids: str) -> list[dict] | dict:
    """Run one native browser session for a comma-separated campaign batch."""
    normalized_ids = require_non_empty_csv(
        campaign_ids,
        error="missing_campaign_ids",
        noun="campaign ID",
    )
    if isinstance(normalized_ids, ToolError):
        return tool_error_dict(normalized_ids)

    batch_error = check_batch_limit(normalized_ids)
    if batch_error:
        return tool_error_dict(batch_error)

    return _run_browser_json(
        [*_command_path(tool_name), normalized_ids], allow_nonzero=True
    )


@mcp.tool(
    name="masters_launch",
    description="Launch Wizard campaigns. See tool_help('masters_launch').",
)
@handle_cli_errors
def masters_launch(campaign_ids: str) -> list[dict] | dict:
    """Launch one or more draft campaigns by comma-separated ID.

    Args:
        campaign_ids: Comma-separated campaign IDs (maximum 10).
    """
    return _run_campaign_batch("masters_launch", campaign_ids)


@mcp.tool(
    name="masters_suspend",
    description="Suspend Wizard campaigns. See tool_help('masters_suspend').",
)
@handle_cli_errors
def masters_suspend(campaign_ids: str) -> list[dict] | dict:
    """Suspend one or more campaigns by comma-separated ID.

    Args:
        campaign_ids: Comma-separated campaign IDs (maximum 10).
    """
    return _run_campaign_batch("masters_suspend", campaign_ids)


@mcp.tool(
    name="masters_resume",
    description="Resume Wizard campaigns. See tool_help('masters_resume').",
)
@handle_cli_errors
def masters_resume(campaign_ids: str) -> list[dict] | dict:
    """Resume one or more campaigns by comma-separated ID.

    Args:
        campaign_ids: Comma-separated campaign IDs (maximum 10).
    """
    return _run_campaign_batch("masters_resume", campaign_ids)


@mcp.tool(
    name="masters_archive",
    description="Archive Wizard campaigns. See tool_help('masters_archive').",
)
@handle_cli_errors
def masters_archive(campaign_ids: str) -> list[dict] | dict:
    """Archive one or more campaigns by comma-separated ID.

    Args:
        campaign_ids: Comma-separated campaign IDs (maximum 10).
    """
    return _run_campaign_batch("masters_archive", campaign_ids)


@mcp.tool(
    name="masters_copy",
    description="Copy a Wizard campaign. See tool_help('masters_copy').",
)
@handle_cli_errors
def masters_copy(campaign_id: str) -> dict:
    """Clone a campaign and save the copy as a draft.

    Args:
        campaign_id: Source campaign ID.
    """
    args = [*_command_path("masters_copy"), str(campaign_id)]
    return cast(dict, _run_browser_json(args))


def _get_campaign_resource(tool_name: str, campaign_id: str) -> dict:
    # Keep object IDs as strings at the MCP boundary: JavaScript hosts can round
    # int64 values before Python sees them. Click still validates this token as INT.
    return cast(
        dict,
        _run_browser_json([*_command_path(tool_name), str(campaign_id)]),
    )


@mcp.tool(
    name="masters_adimages_get",
    description="Read Campaign Wizard images. See tool_help('masters_adimages_get').",
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
    description="Read Campaign Wizard goals. See tool_help('masters_targetactions_get').",
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
    description="Read Campaign Wizard counters. See tool_help('masters_counters_get').",
)
@handle_cli_errors
def masters_counters_get(campaign_id: str) -> dict:
    """Get the campaign's linked Yandex Metrika counters.

    Requires a direct-cli release containing commit
    https://github.com/axisrow/direct-cli/commit/a52fe95. The command is absent
    from the published 0.5.2 wheel.

    Args:
        campaign_id: Campaign ID.
    """
    return _get_campaign_resource("masters_counters_get", campaign_id)


@mcp.tool(
    name="masters_audience_get",
    description="Read Campaign Wizard audience. See tool_help('masters_audience_get').",
)
@handle_cli_errors
def masters_audience_get(campaign_id: str) -> dict:
    """Get the campaign's manual audience settings.

    Args:
        campaign_id: Campaign ID.
    """
    return _get_campaign_resource("masters_audience_get", campaign_id)
