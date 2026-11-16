"""The read-only API behind the dashboard: the exported state, and the HTTP adapter's guards."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from tests.test_vbench import PUML, build, cli, fakes, uc_spec, write  # noqa: F401 (fixtures and helpers)
from vbench.adapters import http_server
from vbench.adapters.fs import FsWorkspace
from vbench.adapters.toml_config import load_config
from vbench.app.export import export_state
from vbench.domain.contexts import USECASE_MAP


class Repo:
    def branch(self) -> str:
        return "feat/uc-n1-create"

    def commits(self, base: str) -> list[str]:
        return []


def state(proj: Path) -> dict:
    return export_state(load_config(proj), FsWorkspace(proj), Repo())


def notes(proj: Path) -> None:
    uc_spec(
        proj,
        "UC-N-001",
        acs=[("AC-N-011", ""), ("AC-N-012", "")],
        tasks=[(1, ["AC-N-011"])],
        actor="Author",
        context="Notes",
        realises=["REQ-FR-001"],
    )
    uc_spec(proj, "UC-N-002", depends=["UC-N-001"], acs=[("AC-N-013", "TBD:")], actor="Author", context="Notes")
    build(proj, "UC-N-001", "AC-N-011")
    cli.main(["sync"])


def test_export_matches_what_the_cli_derives(proj: Path):
    notes(proj)
    s = state(proj)
    json.dumps(s)  # plain data
    assert s["branch"] == "feat/uc-n1-create"
    by = {u["id"]: u for u in s["useCases"]}
    assert by["UC-N-001"]["stage"] == "verify" and by["UC-N-001"]["enables"] == ["UC-N-002"]
    assert (
        by["UC-N-002"]["stage"] == "requirements"
        and by["UC-N-002"]["dependsOn"] == ["UC-N-001"]
        and by["UC-N-002"]["wave"] == 1
    )
    assert s["next"]["command"] == "/vbench:v-1-requirements UC-N-002"
    states = {c["id"]: c["state"] for c in s["criteria"]}
    assert states == {"AC-N-011": "covered", "AC-N-012": "uncovered", "AC-N-013": "tbd"}
    assert s["rungs"][0]["uc"] == "UC-N-001" and s["rungs"][0]["verifiedBy"][0]["rung"] == "unit"
    assert {g["name"] for g in s["gates"]} >= {"refs", "rungs", "acs", "links", "diagrams", "docs"}
    assert "UC_N_001 --> UC_N_002" in s["graph"]
    kinds = {d["path"].rsplit("/", 1)[-1]: d["kind"] for d in s["diagrams"]}
    assert kinds[USECASE_MAP] == "use-case map"
    assert any(d["path"].endswith("00-requirements-engineering.md") for d in s["docs"])
    assert not any(d["path"].endswith("_TEMPLATE.md") and "usecase-diagrams" in d["path"] for d in s["docs"])


def test_export_command_prints_the_same_json(proj: Path, capsys):
    notes(proj)
    capsys.readouterr()
    assert cli.main(["export"], cli.Adapters(repo_for=lambda root: Repo())) == 0
    assert json.loads(capsys.readouterr().out)["useCases"][0]["id"] == "UC-N-001"


@pytest.fixture
def server(proj: Path):
    notes(proj)
    write(
        proj / "docs/usecase-diagrams/UC-N-001-thing-sequence.puml",
        "@startuml X\n!include ../_style.puml\nA -> B\n@enduml\n",
    )
    dist = proj / "dist"
    write(dist / "index.html", "<html>app</html>")
    write(dist / "assets/app.js", "console.log(1)")

    def load():
        c, w = load_config(proj), FsWorkspace(proj)
        return c, w, lambda: export_state(c, w, Repo())

    srv = http_server.serve(load, "127.0.0.1", 0, dist)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()


def get(url: str, headers: dict | None = None, method: str = "GET"):
    req = urllib.request.Request(url, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, r.read().decode(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(), dict(e.headers)


def test_server_serves_state_files_diagrams_and_the_ui(server: str):
    code, body, hdr = get(server + "/api/state")
    assert code == 200 and hdr["Content-Type"] == "application/json" and hdr["Cache-Control"] == "no-store"
    assert json.loads(body)["useCases"][0]["id"] == "UC-N-001"
    assert get(server + "/api/file?path=docs/01-backlog-epics-stories.md")[0] == 200
    code, body, _ = get(server + "/api/diagram?path=docs/usecase-diagrams/UC-N-001-thing-sequence.puml")
    assert code == 200 and "skinparam shadowing false" in body and "A -> B" in body
    assert not any(ln.lstrip().startswith("!include") for ln in body.splitlines())  # the directive is replaced
    assert get(server + "/")[1] == "<html>app</html>"
    assert get(server + "/assets/app.js")[1] == "console.log(1)"
    assert get(server + "/some/client/route")[1] == "<html>app</html>"  # single-page-app fallback


@pytest.mark.parametrize(
    "path",
    [
        "../pyproject.toml",
        "/etc/passwd",
        "docs/../.vbench/config.toml",
        "docs/../../x.md",
        "src/x.puml",
        "docs/missing.md",
        "docs/00-naming-conventions.txt",
        "..%2f..%2fetc%2fpasswd",
        "",
    ],
)
def test_files_outside_docs_and_specs_are_not_served(server: str, path: str):
    assert get(f"{server}/api/file?path={path}")[0] == 404
    assert get(f"{server}/api/diagram?path={path}")[0] == 404


def test_the_server_is_read_only_and_checks_the_host_header(server: str):
    for method in ("POST", "PUT", "DELETE", "PATCH"):
        req = urllib.request.Request(server + "/api/state", data=b"{}", method=method)
        with pytest.raises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(req)
        assert e.value.code == 405
    assert get(server + "/api/state", {"Host": "evil.example:3000"})[0] == 403  # DNS-rebinding
    assert get(server + "/api/state", {"Host": "localhost:3000"})[0] == 200
    assert get(server + "/api/nope")[0] == 404


def test_a_broken_project_returns_an_error_instead_of_crashing(proj: Path):
    def load():
        raise RuntimeError("boom")

    srv = http_server.serve(load, "127.0.0.1", 0, None)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        code, body, _ = get(f"http://127.0.0.1:{srv.server_address[1]}/api/state")
        assert code == 500 and "boom" in body
        assert get(f"http://127.0.0.1:{srv.server_address[1]}/")[0] == 404  # no UI build configured
    finally:
        srv.shutdown()
        srv.server_close()


def test_plantuml_requests_are_forwarded_only_in_hex_form_and_only_to_the_configured_renderer(server: str, monkeypatch):
    import http.server

    seen: list[str] = []

    class Renderer(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append(self.path)
            body = b"<svg>drawn</svg>"
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    up = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Renderer)
    threading.Thread(target=up.serve_forever, daemon=True).start()
    try:
        hexed = "~h" + b"@startuml\nA -> B\n@enduml".hex()
        assert get(f"{server}/plantuml/svg/{hexed}")[0] == 503  # nothing configured yet
        monkeypatch.setenv("VBENCH_PLANTUML_URL", f"http://127.0.0.1:{up.server_address[1]}")
        code, body, hdr = get(f"{server}/plantuml/svg/{hexed}")
        assert code == 200 and body == "<svg>drawn</svg>" and hdr["Content-Type"] == "image/svg+xml"
        assert seen == [f"/svg/{hexed}"]
        for bad in (
            "/plantuml/svg/http://evil.example/x",
            "/plantuml/gif/~h41",
            "/plantuml/svg/~hZZ",
            "/plantuml/../x",
            "/plantuml/svg/%7Eh41",
        ):
            assert get(server + bad)[0] == 400, bad
        assert len(seen) == 1  # nothing else reached the renderer
    finally:
        up.shutdown()
        up.server_close()
        monkeypatch.setenv("VBENCH_PLANTUML_URL", "http://127.0.0.1:1")
    assert get(f"{server}/plantuml/svg/{hexed}")[0] == 502  # a renderer that is down is a clean 502
