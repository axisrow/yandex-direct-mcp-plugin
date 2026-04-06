"""Yandex.Direct MCP Server — main entry point."""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("yandex-direct", json_response=True)

# Import and register tools here as they are implemented
# from server.tools.campaigns import register as register_campaigns
# from server.tools.ads import register as register_ads
# etc.

if __name__ == "__main__":
    mcp.run(transport="stdio")
