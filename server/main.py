import sys
from pathlib import Path

# Prevent dual-import: when run as `python3 server/main.py`, register
# the __main__ module under its canonical name so that tool modules
# doing `from server.main import mcp` get the same instance.
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    sys.modules.setdefault("server.main", sys.modules["__main__"])

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("yandex-direct-mcp", json_response=True)

# Tool registration happens via imports. Required modules form the default
# surface; optional bundles are imported only when explicitly enabled (#293).
import os

import server.tools.adextensions
import server.tools.adgroups
import server.tools.ads
import server.tools.advideos
import server.tools.agency
import server.tools.audience
import server.tools.auth_tools
import server.tools.balance
import server.tools.bidmodifiers
import server.tools.bids
import server.tools.businesses
import server.tools.campaigns
import server.tools.changes
import server.tools.clients
import server.tools.creatives
import server.tools.dictionaries
import server.tools.dynamic_ads
import server.tools.dynamic_feed_ad_targets
import server.tools.feeds
import server.tools.images
import server.tools.keyword_bids
import server.tools.keywords
import server.tools.leads
import server.tools.negative_keyword_shared_sets
import server.tools.reports
import server.tools.research
import server.tools.retargeting
import server.tools.sitelinks
import server.tools.smart_ad_targets
import server.tools.strategies
import server.tools.tool_help
import server.tools.trackingparams_legacy
import server.tools.turbo_pages
import server.tools.v4account
import server.tools.v4adimage
import server.tools.v4events
import server.tools.v4forecast
import server.tools.v4goals
import server.tools.v4keywords
import server.tools.v4tags
import server.tools.v4wordstat
import server.tools.vcards  # noqa: F401
from server.config import (
    apply_tool_surface,
    config_from_env,
    env_config_warnings,
)
from server.optional_tools import import_optional_modules, optional_tools_warnings

for _warning in optional_tools_warnings(os.environ):
    print(f"[yandex-direct-mcp] tool-surface config: {_warning}", file=sys.stderr)
_OPTIONAL_LOADED = import_optional_modules(os.environ)

_TOOL_SURFACE = config_from_env(os.environ)
for _warning in env_config_warnings(os.environ, _TOOL_SURFACE):
    print(f"[yandex-direct-mcp] tool-surface config: {_warning}", file=sys.stderr)
_REMOVED_TOOLS = apply_tool_surface(mcp, _TOOL_SURFACE)
if _REMOVED_TOOLS:
    _REGISTERED_TOOL_COUNT = len(
        getattr(getattr(mcp, "_tool_manager", None), "_tools", {})
    )
    print(
        f"[yandex-direct-mcp] tool surface: {len(_REMOVED_TOOLS)} tool(s) disabled "
        f"by config; {_REGISTERED_TOOL_COUNT} enabled.",
        file=sys.stderr,
    )

if __name__ == "__main__":
    mcp.run(transport="stdio")
