from mcp.server.fastmcp import FastMCP

mcp = FastMCP("yandex-direct", json_response=True)

if __name__ == "__main__":
    mcp.run(transport="stdio")
