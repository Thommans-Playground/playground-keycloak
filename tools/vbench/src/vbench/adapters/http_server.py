"""A read-only HTTP driving adapter: the project state as JSON, its docs and diagrams as text, and a built UI.

    GET /api/state              the whole project state (app.export), computed fresh on every request
    GET /api/file?path=...      a .md or .puml file under the docs or specs folder
    GET /api/diagram?path=...   a .puml file with its `!include` lines inlined, ready for a PlantUML renderer
    GET /plantuml/svg/~h<hex>   the diagram source (hex) drawn by the renderer named in VBENCH_PLANTUML_URL
    GET /...                    static files from the UI build, falling back to index.html

It only ever reads: anything but GET and HEAD is refused (405). Paths cannot leave the docs and specs folders, and the
Host header must be a loopback name (or listed in VBENCH_ALLOWED_HOSTS), which blocks DNS-rebinding from a web page.
"""

from __future__ import annotations

import json
import mimetypes
import os
import posixpath
import re
import urllib.error
import urllib.request
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from ..domain.config import Config
from ..domain.paths import docs_path
from ..ports import Workspace

INCLUDE = re.compile(r"^\s*!include\s+(\S+)\s*$")
LOOPBACK = {"localhost", "127.0.0.1", "[::1]", "::1"}
MAX_INCLUDE_DEPTH = 3
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


def make_handler(
    load: Callable[[], tuple[Config, Workspace, Callable[[], dict]]],
    static: Path | None,
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

        do_PUT = do_DELETE = do_PATCH = do_POST = _method_not_allowed

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


def serve(load, host: str, port: int, static: Path | None) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), make_handler(load, static))
