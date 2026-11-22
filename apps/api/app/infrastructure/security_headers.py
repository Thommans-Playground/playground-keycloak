"""Browser protection headers on every answer of the API (NFR-6, AC-96).

A pure ASGI middleware, so it adds the headers to refused answers as well as to successful ones. The content security
policy is a starting one: it forbids being framed, other base addresses and plugins. Locking scripts down (a
script-src) is a separate step, because it needs care with the pages that serve them."""

from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

HEADERS = (
    (b"content-security-policy", b"frame-ancestors 'none'; base-uri 'self'; object-src 'none'"),
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"no-referrer"),
)

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]


class SecurityHeaders:
    def __init__(self, app: Callable[[Scope, Receive, Send], Awaitable[None]]) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                present = {name.lower() for name, _ in message.get("headers", [])}
                message["headers"] = [*message.get("headers", []), *(h for h in HEADERS if h[0] not in present)]
            await send(message)

        await self.app(scope, receive, send_with_headers)
