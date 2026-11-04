"""Opt-in MCP tools for the direct-cli Playwright session pipeline."""

import os

from server.main import mcp
from server.tools import get_browser_runner, handle_cli_errors
from server.tools.browser_helpers import browser_session_args
from server.tools.helpers import finalize_json_args


@mcp.tool(
    name="playwright_doctor",
    description="Diagnose the browser-session pipeline without logging in or launching a browser; the saved-session check includes a cookie-only server-side probe. No parameters. Call tool_help('playwright_doctor') for details.",
)
@handle_cli_errors
def playwright_doctor() -> list[dict] | dict:
    """Return read-only diagnostics for browser dependencies and session state.

    Wraps ``direct auth doctor`` — the canonical diagnostics command since the
    CLI hid the deprecated ``playwright doctor`` alias; the MCP tool keeps its
    public name and its ``playwright`` config group (YANDEX_DIRECT_DISABLED_
    GROUPS=playwright still works). The ``auth doctor`` saved-session check may
    run a cookie-only server-side probe (direct-cli #954), so this command can
    touch the network — it still never logs in, launches a browser, or writes
    files.
    """
    args = ["auth", "doctor"]
    args.extend(browser_session_args(os.environ, include_headful=False))
    finalize_json_args(args, False)
    return get_browser_runner().run_json_lenient(args)
