"""A Model Context Protocol server over stdio: the project's operations as tools an agent can call.

MCP is JSON-RPC 2.0, one message per line on stdin and stdout. This implements the part vbench needs and nothing more:
`initialize`, `ping`, `tools/list` and `tools/call` (and ignores notifications). It does not know what the tools do;
the composition root hands it a list of `ToolSpec`. Only protocol goes to stdout, anything for a person goes to stderr,
because a stray line on stdout would corrupt the stream. A tool that fails is reported as a result with `isError`, the
way MCP asks, so the model can read why; only a malformed call is a protocol error.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import IO, Any

from ..domain.changes import ChangeError
from ..domain.errors import AgentError, StaleError, VBenchError
from ..ports import ToolSpec

SUPPORTED = ("2025-06-18", "2025-03-26", "2024-11-05")
PARSE_ERROR, INVALID_REQUEST, METHOD_NOT_FOUND, INVALID_PARAMS, INTERNAL = -32700, -32600, -32601, -32602, -32603
MAX_RESULT = 60_000  # characters of one result handed back to the model


class McpServer:
    def __init__(self, name: str, version: str, tools: Iterable[ToolSpec], instructions: str = "") -> None:
        self.name, self.version, self.instructions = name, version, instructions
        self.tools = {t.name: t for t in tools}

    # ------------------------------------------------------------------------------------------ one message
    def handle(self, message: Any) -> dict | list | None:
        """The reply to one JSON-RPC message, or None when it needs none (a notification)."""
        if isinstance(message, list):
            replies = [r for m in message if (r := self.handle(m)) is not None]
            return replies or None
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0" or "method" not in message:
            return self._error(
                message.get("id") if isinstance(message, dict) else None, INVALID_REQUEST, "Not a JSON-RPC request"
            )
        method, ident, params = message["method"], message.get("id"), message.get("params") or {}
        if "id" not in message:
            return None  # a notification, such as notifications/initialized: no reply is allowed
        try:
            if method == "initialize":
                return self._ok(ident, self._initialize(params))
            if method == "ping":
                return self._ok(ident, {})
            if method == "tools/list":
                return self._ok(ident, {"tools": [self._describe(t) for t in self.tools.values()]})
            if method == "tools/call":
                return self._call(ident, params)
        except _Invalid as e:
            return self._error(ident, INVALID_PARAMS, str(e))
        return self._error(ident, METHOD_NOT_FOUND, f"Unknown method {method}")

    def _initialize(self, params: dict) -> dict:
        asked = params.get("protocolVersion")
        result: dict[str, Any] = {
            "protocolVersion": asked if asked in SUPPORTED else SUPPORTED[0],
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": self.name, "version": self.version},
        }
        if self.instructions:
            result["instructions"] = self.instructions
        return result

    @staticmethod
    def _describe(t: ToolSpec) -> dict:
        return {
            "name": t.name,
            "title": t.title or t.name,
            "description": t.description,
            "inputSchema": t.schema,
            "annotations": {
                "title": t.title or t.name,
                "readOnlyHint": t.read_only,
                "destructiveHint": t.destructive,
                "openWorldHint": False,
            },
        }

    def _call(self, ident: Any, params: dict) -> dict:
        tool = self.tools.get(params.get("name")) if isinstance(params.get("name"), str) else None
        if tool is None:
            raise _Invalid(f"Unknown tool {params.get('name')!r}")
        args = params.get("arguments") or {}
        if not isinstance(args, dict):
            raise _Invalid("`arguments` must be an object")
        try:
            text, failed = tool.handler(args), False
        except (ChangeError, StaleError, AgentError, VBenchError) as e:
            text, failed = str(e), True
        except Exception as e:
            text, failed = f"{type(e).__name__}: {e}", True
        if len(text) > MAX_RESULT:
            text = text[:MAX_RESULT] + "\n...truncated"
        return self._ok(ident, {"content": [{"type": "text", "text": text}], "isError": failed})

    @staticmethod
    def _ok(ident: Any, result: dict) -> dict:
        return {"jsonrpc": "2.0", "id": ident, "result": result}

    @staticmethod
    def _error(ident: Any, code: int, message: str) -> dict:
        return {"jsonrpc": "2.0", "id": ident, "error": {"code": code, "message": message}}


class _Invalid(Exception):
    """A call that is not well formed: reported as a protocol error."""


def serve_stdio(server: McpServer, stdin: IO[str], stdout: IO[str]) -> None:
    """Read one JSON message per line until the client closes the stream."""
    for line in stdin:
        if not line.strip():
            continue
        try:
            reply = server.handle(json.loads(line))
        except ValueError:
            reply = McpServer._error(None, PARSE_ERROR, "Not valid JSON")
        if reply is not None:
            stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            stdout.flush()
