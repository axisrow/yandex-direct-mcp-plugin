"""MCP tool for Yandex.Direct tracking-parameter reference data."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors


@mcp.tool(
    name="trackingparams",
    description="List Yandex.Direct dynamic tracking parameters for UTM templates. Call tool_help('trackingparams') for parameters.",
)
@handle_cli_errors
def trackingparams() -> list[dict] | dict:
    """List dynamic tracking parameters and their allowed values.

    The CLI defaults reference commands to human-readable text, so request JSON
    explicitly before passing the result through ``run_json``.
    """
    return get_runner().run_json(["trackingparams", "--format", "json"])
