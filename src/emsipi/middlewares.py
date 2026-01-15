"""Middlewares (mostly for logging) for the FastMCP server."""

import json
import logging
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, cast

from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from starlette.types import ASGIApp, Message, Receive, Scope, Send

if TYPE_CHECKING:
    from starlette.requests import Request

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)


class BytesEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle bytes."""

    def default(self, o: object) -> object:
        """Encode bytes to a UTF-8 string.

        Args:
            o: The object to encode.

        Returns:
            The encoded object, or the original object if not bytes.
        """
        if isinstance(o, bytes):
            return o.decode("utf-8", errors="replace")
        return super().default(o)


class ASGIMiddleware:
    """ASGI middleware to wrap the application."""

    def __init__(self, app: ASGIApp) -> None:
        """Initialize the ASGI middleware.

        Args:
            app: The ASGI application to wrap.
        """
        self.app = app

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        """Call the ASGI application with the given scope, receive, and send.

        Args:
            scope: The ASGI scope containing the request context.
            receive: The ASGI receive function to get messages.
            send: The ASGI send function to send messages.
        """

        def clean_starlette_dict(d: Mapping) -> dict:  # type: ignore[type-arg]
            """Clean the Starlette dictionary by removing empty values."""
            return {k: v for k, v in d.items() if k not in {"app"}}

        req_log = {
            "scope": clean_starlette_dict(scope),
            "receive": None,
            "send": None,
        }

        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        if "path" in scope and scope["path"] == "/mcp":
            scope["path"] = "/mcp/"
        if "raw_path" in scope and scope["raw_path"] == b"/mcp":
            scope["raw_path"] = b"/mcp/"

        async def receive_wrapper() -> Message:
            message = await receive()
            req_log["receive"] = clean_starlette_dict(message)
            return message

        async def send_wrapper(message: Message) -> None:
            # ... Do something
            req_log["send"] = clean_starlette_dict(message)
            logger.info(json.dumps(req_log, cls=BytesEncoder))
            logger.info(req_log)
            await send(message)

        return await self.app(scope, receive_wrapper, send_wrapper)


class SimpleLoggingMiddleware(Middleware):
    """Simple logging middleware for MCP server."""

    async def __call__(
        self,
        context: MiddlewareContext,  # type: ignore[type-arg]
        call_next: CallNext,  # type: ignore[type-arg]
    ) -> Any:  # noqa: ANN401
        """Log the incoming message and call the next middleware or handler.

        Args:
            context: The incoming request containing the context.
            call_next: The next middleware or handler to call.

        Returns:
            The result of the next middleware or handler.
        """
        logger.info(f"{context}")
        if context.fastmcp_context is not None:
            request = cast(
                "Request", context.fastmcp_context.request_context.request
            )
            body = await request.json()
            headers = request.headers
            query_params = request.query_params
            path_params = request.path_params
            logger.info(
                {
                    "body": body,
                    "headers": headers,
                    "query_params": query_params,
                    "path_params": path_params,
                }
            )

        try:
            result = await call_next(context)
        except Exception as e:
            logger.info(f"Failed {context}: {e}")
            raise
        return result
