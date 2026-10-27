"""MCP tool for the direct-cli API-units balance readout (direct-cli 0.5.5)."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors


@mcp.tool(
    name="api_units",
    description="Show remaining Yandex.Direct API units (spent, left, daily limit; per-login for agency accounts). No parameters. Call tool_help('api_units') for details.",
)
@handle_cli_errors
def api_units() -> list[dict] | dict:
    """Report the remaining API-unit balance parsed from the Units HTTP header.

    Cheap pre-flight check before expensive operations (reports, batch
    mutations); also explains unit-exhaustion errors. Read-only: the balance is
    read from the ``Units`` response header of a live API call — a minimal
    ``Clients.get`` that itself costs ~10 units — and the resolved login
    matches the active ``direct`` auth profile.
    """
    return get_runner().run_json(["api", "units", "--format", "json"])
