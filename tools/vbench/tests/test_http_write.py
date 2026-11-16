"""The write path of the dashboard server: every guard, and the three commands behind them."""

from __future__ import annotations

import json
import shutil
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from vbench.adapters import http_server
from vbench.adapters.fs import FsWorkspace
from vbench.adapters.toml_config import load_config
from vbench.app.assist import check_overlap
from vbench.app.changes import apply_change, commit_changes, preview_change
from vbench.app.export import export_state

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "notes-app"
TOKEN = "t0ken"
PROBLEM = {
    "op": "add",
    "kind": "problem",
    "fields": {"text": "A note cannot be shared", "who": "The author", "cost": "It stays."},
}


class Repo:
    branch_name = "feat/notes"

    def branch(self) -> str:
        return self.branch_name

    def commits(self, base: str) -> list[str]:
        return []


class Committer:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], str]] = []

    def commit(self, paths, message):
        self.calls.append((list(paths), message))
        return "abc1234"


@pytest.fixture
def served(tmp_path: Path):
    root = tmp_path / "notes"
    shutil.copytree(EXAMPLE, root, ignore=shutil.ignore_patterns(".vbench/ui", "node_modules", ".git"))
    repo, committer = Repo(), Committer()

    def fresh():
        return load_config(root), FsWorkspace(root)

    def load():
        c, w = fresh()
        return c, w, lambda: export_state(c, w, repo)

    writer = http_server.Writer(
        token=TOKEN,
        blocked=lambda: "On the default branch." if repo.branch() == "main" else "",
        preview=lambda raw: preview_change(*fresh(), raw),
        apply=lambda raw, digest: apply_change(*fresh(), raw, digest),
        commit=lambda paths, summary: commit_changes(*fresh(), committer, paths, summary),
        overlap=lambda raw: check_overlap(*fresh(), None, raw),
    )
    srv = http_server.serve(load, "127.0.0.1", 0, None, writer)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}", root, repo, committer
    srv.shutdown()
    srv.server_close()


def call(url: str, body: object = None, headers: dict | None = None, method: str = "POST", raw: bytes | None = None):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    h = {"Content-Type": "application/json", "X-Vbench-Token": TOKEN, **(headers or {})}
    req = urllib.request.Request(url, data=data, headers={k: v for k, v in h.items() if v is not None}, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"null")


def doc(root: Path) -> str:
    return (root / "docs/00-requirements-engineering.md").read_text()


def test_a_read_only_server_refuses_every_write_and_says_so(tmp_path: Path):
    srv = http_server.serve(lambda: (_ for _ in ()).throw(RuntimeError), "127.0.0.1", 0, None)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    try:
        assert call(base + "/api/changes/apply", PROBLEM)[0] == 405
        assert call(base + "/api/session", method="GET")[1] == {
            "write": False,
            "token": None,
            "blocked": "",
            "agent": "",
            "chat": False,
        }
    finally:
        srv.shutdown()
        srv.server_close()


def test_the_session_tells_the_page_whether_it_may_write(served):
    base, _, repo, _ = served
    assert call(base + "/api/session", method="GET")[1] == {
        "write": True,
        "token": TOKEN,
        "blocked": "",
        "agent": "",
        "chat": False,
    }
    repo.branch_name = "main"
    assert call(base + "/api/session", method="GET")[1]["blocked"] == "On the default branch."


@pytest.mark.parametrize(
    "headers, code",
    [
        ({"X-Vbench-Token": None}, 403),  # no token
        ({"X-Vbench-Token": "wrong"}, 403),
        ({"Origin": "http://evil.example"}, 403),  # another site's page
        ({"Host": "evil.example:3000"}, 403),  # DNS rebinding
        ({"Content-Type": "text/plain"}, 415),
    ],
)
def test_a_write_without_the_token_from_the_right_origin_is_refused(served, headers, code):
    base, root, _, _ = served
    before = doc(root)
    assert call(base + "/api/changes/apply", {"change": PROBLEM, "digest": "x"}, headers)[0] == code
    assert doc(root) == before


def test_the_same_origin_the_page_really_has_is_accepted(served):
    base, _, _, _ = served
    assert call(base + "/api/changes/preview", {"change": PROBLEM}, {"Origin": base})[0] == 200


def test_bodies_must_be_small_json_objects_and_routes_must_exist(served):
    base, _, _, _ = served
    assert call(base + "/api/changes/preview", raw=b"")[0] == 413
    assert call(base + "/api/changes/preview", raw=b"x" * (http_server.MAX_BODY + 1))[0] == 413
    assert call(base + "/api/changes/preview", raw=b"{not json")[0] == 400
    assert call(base + "/api/changes/preview", raw=b"[1]")[0] == 400
    assert call(base + "/api/changes/shell", {"cmd": "ls"})[0] == 404
    assert (
        call(base + "/api/changes/preview", {"change": {"op": "add", "kind": "problem", "fields": {"colour": "red"}}})[
            0
        ]
        == 400
    )


def test_preview_returns_the_plan_and_writes_nothing(served):
    base, root, _, _ = served
    before = doc(root)
    code, plan = call(base + "/api/changes/preview", {"change": PROBLEM})
    assert (
        code == 200
        and plan["change"]["id"] == "STK-PRB-004"
        and plan["digest"]
        and "+| **STK-PRB-004**" in plan["diff"]
    )
    assert doc(root) == before


def test_apply_writes_only_what_was_previewed(served):
    base, root, _, _ = served
    _, plan = call(base + "/api/changes/preview", {"change": PROBLEM})
    code, done = call(base + "/api/changes/apply", {"change": PROBLEM, "digest": plan["digest"]})
    assert code == 200 and done["id"] == "STK-PRB-004" and "A note cannot be shared" in doc(root)
    assert any(g["name"] == "docs" and g["ok"] for g in done["gates"])
    # the same preview is now stale: the files are not what it described
    assert call(base + "/api/changes/apply", {"change": PROBLEM, "digest": plan["digest"]})[0] == 409


def test_a_wrong_digest_is_refused_and_nothing_is_written(served):
    base, root, _, _ = served
    before = doc(root)
    assert call(base + "/api/changes/apply", {"change": PROBLEM, "digest": "not-the-digest"})[0] == 409
    assert doc(root) == before


def test_applying_and_committing_are_blocked_on_the_default_branch_but_previewing_is_not(served):
    base, root, repo, committer = served
    repo.branch_name = "main"
    before = doc(root)
    assert call(base + "/api/changes/preview", {"change": PROBLEM})[0] == 200
    assert call(base + "/api/changes/apply", {"change": PROBLEM, "digest": "x"})[0] == 403
    assert (
        call(base + "/api/changes/commit", {"paths": ["docs/00-requirements-engineering.md"], "summary": "x"})[0] == 403
    )
    assert doc(root) == before and committer.calls == []


def test_commit_takes_documentation_files_only(served):
    base, _, _, committer = served
    ok = call(
        base + "/api/changes/commit",
        {"paths": ["docs/00-requirements-engineering.md"], "summary": "Add problem STK-PRB-004"},
    )
    assert ok[0] == 200 and ok[1]["commit"] == "abc1234" and committer.calls[0][1] == "chore: add problem STK-PRB-004"
    for bad in (["src/notes/note.py"], ["../../etc/passwd"], ["docs/nope.md"], []):
        assert call(base + "/api/changes/commit", {"paths": bad, "summary": "x"})[0] == 400
    assert len(committer.calls) == 1


def test_asking_whether_an_entry_exists_needs_the_token_and_works_on_the_default_branch(served):
    base, root, repo, _ = served
    ask = {
        "change": {
            "op": "add",
            "kind": "request",
            "fields": {
                "text": "I want to keep notes: write one, read it later, and fix it when I got something wrong."
            },
        }
    }
    assert call(base + "/api/assist/overlap", ask, {"X-Vbench-Token": None})[0] == 403
    assert call(base + "/api/assist/overlap", ask, {"Origin": "http://evil.example"})[0] == 403
    before = doc(root)
    repo.branch_name = "main"  # a question changes nothing, so the branch guard does not apply
    code, out = call(base + "/api/assist/overlap", ask)
    assert (
        code == 200
        and out["verdict"] == "duplicate"
        and out["matches"][0]["id"] == "STK-REQ-001"
        and out["source"] == "rules"
    )
    assert doc(root) == before
    assert (
        call(base + "/api/assist/overlap", {"change": {"op": "add", "kind": "problem", "fields": {"who": "x"}}})[0]
        == 400
    )


def test_a_server_without_the_overlap_check_does_not_have_the_route(tmp_path: Path):
    writer = http_server.Writer(
        token=TOKEN, blocked=lambda: "", preview=lambda r: {}, apply=lambda r, d: {}, commit=lambda p, s: {}
    )
    srv = http_server.serve(lambda: (_ for _ in ()).throw(RuntimeError), "127.0.0.1", 0, None, writer)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        assert call(f"http://127.0.0.1:{srv.server_address[1]}/api/assist/overlap", {"change": {}})[0] == 404
    finally:
        srv.shutdown()
        srv.server_close()
