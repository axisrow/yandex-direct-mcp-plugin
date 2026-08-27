"""Opt-in MCP tools for the direct-cli Playwright session pipeline."""

from server.main import mcp
from server.tools import get_browser_runner, handle_cli_errors
from server.tools.helpers import finalize_json_args


@mcp.tool(
    name="playwright_doctor",
    description="Diagnose the browser-session pipeline without logging in, launching a browser, or writing files. No parameters. Call tool_help('playwright_doctor') for details.",
)
@handle_cli_errors
def playwright_doctor() -> list[dict] | dict:
    """Return read-only diagnostics for browser dependencies and session state."""
    args = finalize_json_args(["playwright", "doctor"], False)
    return get_browser_runner().run_json_lenient(args)
