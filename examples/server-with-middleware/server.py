"""Simple MCP server."""

import asyncio
import logging
import os

from fastmcp import FastMCP
from starlette.middleware import Middleware as StarletteMiddleware

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)


mcp = FastMCP("MCP Server on Cloud Run")  # type: ignore[var-annotated] # pyright: ignore[reportUnknownVariableType]


@mcp.tool()
def add(a: int, b: int) -> int:
    """Use this to add two numbers together.

    Args:
        a: The first number.
        b: The second number.

    Returns:
        The sum of the two numbers.
    """
    logger.info(f">>> 🛠️ Tool: 'add' called with numbers '{a}' and '{b}'")
    return a + b


@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Use this to subtract two numbers.

    Args:
        a: The first number.
        b: The second number.

    Returns:
        The difference of the two numbers.
    """
    logger.info(f">>> 🛠️ Tool: 'subtract' called with numbers '{a}' and '{b}'")

    return a - b


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    logger.info(f"🚀 MCP server started on port {port}")
    # Could also use 'sse' transport, host="0.0.0.0" required for Cloud Run.
    from emsipi.middlewares import (
        AddTrailingSlashASGIMiddleware,
        LoggingASGIMiddleware,
        SimpleLoggingMiddleware,
    )

    mcp.add_middleware(SimpleLoggingMiddleware())
    asyncio.run(
        mcp.run_http_async(
            port=port,
            host="0.0.0.0",  # noqa: S104
            middleware=[
                StarletteMiddleware(AddTrailingSlashASGIMiddleware),
                StarletteMiddleware(LoggingASGIMiddleware),
            ],
        ),
    )
