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

# Tool registration happens via imports
import server.tools.adextensions  # noqa: E402, F401
import server.tools.adgroups  # noqa: E402, F401
import server.tools.ads  # noqa: E402, F401
import server.tools.advideos  # noqa: E402, F401
import server.tools.agency  # noqa: E402, F401
import server.tools.audience  # noqa: E402, F401
import server.tools.auth_tools  # noqa: E402, F401
import server.tools.balance  # noqa: E402, F401
import server.tools.businesses  # noqa: E402, F401
import server.tools.bidmodifiers  # noqa: E402, F401
import server.tools.bids  # noqa: E402, F401
import server.tools.campaigns  # noqa: E402, F401
import server.tools.changes  # noqa: E402, F401
import server.tools.clients  # noqa: E402, F401
import server.tools.creatives  # noqa: E402, F401
import server.tools.dictionaries  # noqa: E402, F401
import server.tools.dynamic_ads  # noqa: E402, F401
import server.tools.dynamic_feed_ad_targets  # noqa: E402, F401
import server.tools.feeds  # noqa: E402, F401
import server.tools.images  # noqa: E402, F401
import server.tools.keyword_bids  # noqa: E402, F401
import server.tools.keywords  # noqa: E402, F401
import server.tools.leads  # noqa: E402, F401
import server.tools.negative_keyword_shared_sets  # noqa: E402, F401
import server.tools.reports  # noqa: E402, F401
import server.tools.research  # noqa: E402, F401
import server.tools.retargeting  # noqa: E402, F401
import server.tools.sitelinks  # noqa: E402, F401
import server.tools.smart_ad_targets  # noqa: E402, F401
import server.tools.strategies  # noqa: E402, F401
import server.tools.tool_help  # noqa: E402, F401
import server.tools.turbo_pages  # noqa: E402, F401
import server.tools.v4account  # noqa: E402, F401
import server.tools.v4adimage  # noqa: E402, F401
import server.tools.v4events  # noqa: E402, F401
import server.tools.v4forecast  # noqa: E402, F401
import server.tools.v4goals  # noqa: E402, F401
import server.tools.v4keywords  # noqa: E402, F401
import server.tools.v4tags  # noqa: E402, F401
import server.tools.v4wordstat  # noqa: E402, F401
import server.tools.vcards  # noqa: E402, F401

# Apply the configured tool surface (#149): with no YANDEX_DIRECT_TOOL_* env the
# default is the full 146-tool surface, so this is a no-op unless a profile or
# enable/disable rules are set.
import os  # noqa: E402

from server.config import (  # noqa: E402
    apply_tool_surface,
    config_from_env,
    env_config_warnings,
)

_TOOL_SURFACE = config_from_env(os.environ)
for _warning in env_config_warnings(os.environ, _TOOL_SURFACE):
    print(f"[yandex-direct-mcp] tool-surface config: {_warning}", file=sys.stderr)
_REMOVED_TOOLS = apply_tool_surface(mcp, _TOOL_SURFACE)
if _REMOVED_TOOLS:
    print(
        f"[yandex-direct-mcp] tool surface: {len(_REMOVED_TOOLS)} tool(s) disabled "
        f"by config; {len(_TOOL_SURFACE.enabled_tool_names())} enabled.",
        file=sys.stderr,
    )

if __name__ == "__main__":
    mcp.run(transport="stdio")
