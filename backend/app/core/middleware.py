import logging
from http import HTTPStatus
from uuid import uuid4

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.logging import request_id_context

logger = logging.getLogger(__name__)
REQUEST_ID_HEADER = "X-Request-ID"


class RequestIdMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request_id = str(uuid4())
        scope.setdefault("state", {})["request_id"] = request_id
        token = request_id_context.set(request_id)
        # Unhandled errors are rendered by the outer ServerErrorMiddleware.
        status = HTTPStatus.INTERNAL_SERVER_ERROR

        async def send_with_request_id(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
                status = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            try:
                logger.info(
                    "HTTP %s %s status=%s", scope["method"], scope["path"], status
                )
            finally:
                request_id_context.reset(token)
