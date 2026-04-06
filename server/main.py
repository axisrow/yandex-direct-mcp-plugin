from mcp.server.fastmcp import FastMCP

mcp = FastMCP("yandex-direct", json_response=True)

# Tool registration happens via imports
import server.tools.campaigns  # noqa: E402, F401

if __name__ == "__main__":
    mcp.run(transport="stdio")
