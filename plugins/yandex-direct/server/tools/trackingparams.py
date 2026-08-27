"""Opt-in MCP tool for Yandex.Direct tracking-parameter reference data."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors
from server.tools.helpers import finalize_json_args


@mcp.tool(
    name="trackingparams_get",
    description="List Yandex.Direct dynamic tracking parameters for UTM templates. No parameters. Call tool_help('trackingparams_get') for details.",
)
@handle_cli_errors
def trackingparams_get() -> list[dict] | dict:
    """List dynamic tracking parameters and their allowed values.

    The CLI defaults reference commands to human-readable text, so request JSON
    explicitly before passing the result through ``run_json``.
    """
    args = finalize_json_args(["trackingparams"], False)
    return get_runner().run_json(args)
