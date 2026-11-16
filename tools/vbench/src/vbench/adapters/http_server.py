"""A read-only HTTP driving adapter: the project state as JSON, its docs and diagrams as text, and a built UI.

    GET /api/state              the whole project state (app.export), computed fresh on every request
    GET /api/file?path=...      a .md or .puml file under the docs or specs folder
    GET /api/diagram?path=...   a .puml file with its `!include` lines inlined, ready for a PlantUML renderer
    GET /plantuml/svg/~h<hex>   the diagram source (hex) drawn by the renderer named in VBENCH_PLANTUML_URL
    GET /...                    static files from the UI build, falling back to index.html

By default it only ever reads: anything but GET and HEAD is refused. Started with a `Writer` (`vbench serve --write`) it
also answers three POSTs, each a fixed command and nothing more:

    GET  /api/session           whether writing is on, the token that goes with every write, and whether it is blocked
    POST /api/changes/preview   plan a change: the diff, the blast radius, the problems found; writes nothing
    POST /api/changes/apply     write a previewed change, but only if it is still exactly what was previewed
    POST /api/changes/commit    commit documentation files with a one-line message in the repository's convention
    POST /api/assist/overlap    does a new entry already exist? Word overlap, and an agent too when one is set up
    POST /api/chat/stream       ask the assistant (read-only tools); Server-Sent Events: tool, token, done, error

A write needs the token in `X-Vbench-Token`, a same-origin `Origin` (or none), a JSON body of at most 64 KB, and a
branch that is not the default one. Paths cannot leave the docs and specs folders, and the Host header must be a
loopback name (or listed in VBENCH_ALLOWED_HOSTS), which blocks DNS-rebinding from a web page.
"""

from __future__ import annotations

import hmac
import json
import mimetypes
import os
import posixpath
import re
import urllib.error
import urllib.request
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from ..domain.changes import ChangeError
from ..domain.config import Config
from ..domain.errors import AgentError, StaleError, UsageError
from ..domain.paths import docs_path
from ..ports import Workspace

INCLUDE = re.compile(r"^\s*!include\s+(\S+)\s*$")
LOOPBACK = {"localhost", "127.0.0.1", "[::1]", "::1"}
MAX_INCLUDE_DEPTH = 3
MAX_BODY = 64 * 1024
PLANTUML_ID = re.compile(r"^/plantuml/(svg|png)/(~h[0-9a-f]{2,200000})$")


def inline_includes(cfg: Config, ws: Workspace, path: str, depth: int = 0) -> str:
    """The diagram text with each `!include <file>` replaced by that file's text, so a renderer that only sees the
    source (no filesystem) still gets the shared styling. Unresolvable includes are left in place."""
    out = []
    for line in ws.read(path).splitlines():
        m = INCLUDE.match(line)
        target = docs_path(cfg, posixpath.join(posixpath.dirname(path), m.group(1))) if m else None
        if m and target and depth < MAX_INCLUDE_DEPTH and ws.exists(target):
            out.append(inline_includes(cfg, ws, target, depth + 1))
        else:
            out.append(line)
    return "\n".join(out) + "\n"


def hostname(header: str) -> str:
    """`Localhost:3000` -> `localhost`; `[::1]:3000` -> `[::1]`."""
    h = header.strip().lower()
    if h.startswith("["):
        return h.split("]")[0] + "]"
    return h.rsplit(":", 1)[0] if ":" in h else h


NO_UI = (
    "No UI build was found. The dashboard is an optional extra: run `docker compose up` from the vbench repo, "
    "or pass --static."
)


@dataclass(frozen=True)
class Writer:
    """What a write-enabled server can do, handed in by the composition root (`cli.py`)."""

    token: str
    blocked: Callable[[], str]  # why writing is not allowed right now (empty when it is)
    preview: Callable[[object], dict]
    apply: Callable[[object, str], dict]
    commit: Callable[[object, object], dict]
    overlap: Callable[[object], dict] | None = None
    chat: Callable[[object], Iterator[dict]] | None = None  # the assistant: a stream of `tool` and `token` events
    agent: str = ""  # who answers the overlap question besides the word check, or empty


def make_handler(
    load: Callable[[], tuple[Config, Workspace, Callable[[], dict]]],
    static: Path | None,
    writer: Writer | None = None,
):
    allowed = LOOPBACK | {h.strip().lower() for h in os.environ.get("VBENCH_ALLOWED_HOSTS", "").split(",") if h.strip()}

    class Handler(BaseHTTPRequestHandler):
        server_version = "vbench"

        def log_message(self, fmt, *args):  # quiet by default
            pass

        def _send(self, code: int, body: bytes, ctype: str, cache: str = "no-store") -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", cache)
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _text(self, code: int, text: str, ctype: str = "text/plain; charset=utf-8") -> None:
            self._send(code, text.encode("utf-8"), ctype)

        def _json(self, code: int, data: object) -> None:
            self._send(code, json.dumps(data).encode("utf-8"), "application/json")

        def do_GET(self) -> None:
            if hostname(self.headers.get("Host") or "") not in allowed:
                return self._text(403, "Host not allowed")
            url = urlparse(self.path)
            if url.path.startswith("/plantuml/"):
                return self._plantuml(url.path)
            if url.path.startswith("/api/"):
                return self._api(url.path, parse_qs(url.query))
            self._static(url.path)

        do_HEAD = do_GET

        def _method_not_allowed(self) -> None:
            self.send_response(405)
            self.send_header("Allow", "GET, HEAD")
            self.send_header("Content-Length", "0")
            self.end_headers()

        do_PUT = do_DELETE = do_PATCH = _method_not_allowed

        def do_POST(self) -> None:
            if writer is None:
                return self._method_not_allowed()
            if hostname(self.headers.get("Host") or "") not in allowed:
                return self._json(403, {"error": "Host not allowed"})
            route = urlparse(self.path).path
            if route not in (
                "/api/changes/preview",
                "/api/changes/apply",
                "/api/changes/commit",
                "/api/assist/overlap",
                "/api/chat/stream",
            ):
                return self._json(404, {"error": "Not found"})
            origin = self.headers.get("Origin")
            if origin and urlparse(origin).netloc.lower() != (self.headers.get("Host") or "").lower():
                return self._json(403, {"error": "Origin not allowed"})
            if not hmac.compare_digest(self.headers.get("X-Vbench-Token") or "", writer.token):
                return self._json(403, {"error": "A write needs the session token"})
            if not (self.headers.get("Content-Type") or "").startswith("application/json"):
                return self._json(415, {"error": "Send JSON"})
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = -1
            if length <= 0 or length > MAX_BODY:
                return self._json(413, {"error": f"The body must be between 1 byte and {MAX_BODY} bytes"})
            try:
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise ValueError
            except ValueError:
                return self._json(400, {"error": "The body is not a JSON object"})
            if route not in ("/api/changes/preview", "/api/assist/overlap", "/api/chat/stream") and (
                why := writer.blocked()
            ):
                return self._json(403, {"error": why})
            if route == "/api/chat/stream":
                return self._chat(body)
            try:
                if route == "/api/assist/overlap":
                    if writer.overlap is None:
                        return self._json(404, {"error": "Not found"})
                    result = writer.overlap(body.get("change"))
                elif route == "/api/changes/preview":
                    result = writer.preview(body.get("change"))
                elif route == "/api/changes/apply":
                    result = writer.apply(body.get("change"), str(body.get("digest") or ""))
                else:
                    result = writer.commit(body.get("paths"), body.get("summary"))
                return self._json(200, result)
            except StaleError as e:
                return self._json(409, {"error": str(e)})
            except (UsageError, ChangeError) as e:
                return self._json(400, {"error": str(e)})
            except Exception as e:  # a broken project must not take the server down
                return self._json(500, {"error": f"{type(e).__name__}: {e}"})

        def _chat(self, body: dict) -> None:
            if writer is None or writer.chat is None:
                return self._json(404, {"error": "Not found"})
            events = writer.chat(body)
            try:
                first = next(events, None)  # a bad question or a missing key fails here, before the stream opens
            except (UsageError, AgentError) as e:
                return self._json(400 if isinstance(e, UsageError) else 502, {"error": str(e)})
            except Exception as e:
                return self._json(500, {"error": f"{type(e).__name__}: {e}"})

            def frame(name: str, data: dict) -> bytes:
                return f"event: {name}\ndata: {json.dumps(data)}\n\n".encode()

            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("X-Accel-Buffering", "no")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Connection", "close")
            self.end_headers()
            self.close_connection = True
            try:
                pending = [first] if first is not None else []
                for event in [*pending, *events]:
                    kind = event["type"]
                    self.wfile.write(frame(kind, {k: v for k, v in event.items() if k != "type"}))
                    self.wfile.flush()
                self.wfile.write(frame("done", {}))
            except (BrokenPipeError, ConnectionResetError):
                return  # the reader stopped; nothing is left to say
            except (UsageError, AgentError) as e:
                self.wfile.write(frame("error", {"message": str(e)}))
            except Exception:
                self.wfile.write(frame("error", {"message": "The assistant could not finish its answer."}))
            self.wfile.flush()

        def _plantuml(self, route: str) -> None:
            # Only the hex-encoded form is forwarded, and only to the renderer the operator configured, so
            # this cannot be used to make the server fetch an arbitrary address.
            base = os.environ.get("VBENCH_PLANTUML_URL", "").rstrip("/")
            m = PLANTUML_ID.match(route)
            if not m:
                return self._text(400, "Not a PlantUML request")
            if not base:
                return self._text(503, "No PlantUML renderer is configured (set VBENCH_PLANTUML_URL).")
            try:
                with urllib.request.urlopen(f"{base}/{m.group(1)}/{m.group(2)}", timeout=20) as r:
                    return self._send(200, r.read(), r.headers.get("Content-Type", "image/svg+xml"))
            except urllib.error.HTTPError as e:  # a syntax error still comes back as an image the renderer drew
                body = e.read()
                return self._send(
                    200 if body else 502, body or b"The renderer failed.", e.headers.get("Content-Type", "text/plain")
                )
            except (urllib.error.URLError, OSError):
                return self._text(502, "The PlantUML renderer did not answer.")

        def _api(self, route: str, query: dict[str, list[str]]) -> None:
            try:
                if route == "/api/session":
                    return self._json(
                        200,
                        {
                            "write": writer is not None,
                            "token": writer.token if writer else None,
                            "blocked": writer.blocked() if writer else "",
                            "agent": writer.agent if writer else "",
                            "chat": bool(writer and writer.chat),
                        },
                    )
                cfg, ws, state = load()
                if route == "/api/state":
                    return self._json(200, state())
                if route in ("/api/file", "/api/diagram"):
                    path = docs_path(cfg, (query.get("path") or [""])[0])
                    if not path or not ws.exists(path):
                        return self._text(404, "Not found")
                    if route == "/api/diagram":
                        if not path.endswith(".puml"):
                            return self._text(400, "Not a diagram")
                        return self._text(200, inline_includes(cfg, ws, path))
                    return self._text(200, ws.read(path))
                return self._text(404, "Not found")
            except Exception as e:  # a broken project must not take the server down
                return self._json(500, {"error": f"{type(e).__name__}: {e}"})

        def _static(self, route: str) -> None:
            if static is None or not static.is_dir():
                return self._text(
                    404,
                    NO_UI,
                )
            rel = posixpath.normpath(route).lstrip("/") or "index.html"
            target = (static / rel).resolve()
            if not str(target).startswith(str(static.resolve()) + os.sep) or not target.is_file():
                target = static / "index.html"  # single-page app fallback
                if not target.is_file():
                    return self._text(
                        404,
                        NO_UI,
                    )
            ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            self._send(
                200,
                target.read_bytes(),
                ctype,
                "no-cache" if target.name == "index.html" else "public, max-age=3600",
            )

    return Handler


def serve(load, host: str, port: int, static: Path | None, writer: Writer | None = None) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), make_handler(load, static, writer))
