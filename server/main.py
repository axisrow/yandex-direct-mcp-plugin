import sys

# Prevent dual-import: when run as `python3 server/main.py`, register
# the __main__ module under its canonical name so that tool modules
# doing `from server.main import mcp` get the same instance.
if __name__ == "__main__":
    sys.modules.setdefault("server.main", sys.modules["__main__"])

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("yandex-direct-mcp", json_response=True)

# Tool registration happens via imports
import server.tools.adgroups  # noqa: E402, F401
import server.tools.ads  # noqa: E402, F401
import server.tools.auth_tools  # noqa: E402, F401
import server.tools.campaigns  # noqa: E402, F401
import server.tools.keywords  # noqa: E402, F401
import server.tools.reports  # noqa: E402, F401

# Initialize token getter for production use
from server.auth.oauth import OAuthManager  # noqa: E402
from server.tools import set_token_getter  # noqa: E402

_manager = OAuthManager()
set_token_getter(_manager.get_valid_token)

if __name__ == "__main__":
    mcp.run(transport="stdio")
