"""Simple FastMCP server."""

from fastmcp import FastMCP

mcp = FastMCP("Demo Server")
if __name__ == "__main__":
    mcp.run()
