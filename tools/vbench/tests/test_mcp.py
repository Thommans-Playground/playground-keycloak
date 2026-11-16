"""The MCP server: the protocol it speaks, the tools it offers, and the guards on changing anything."""

from __future__ import annotations

import io
import json
import shutil
from pathlib import Path

import pytest

from vbench.adapters.fs import FsWorkspace
from vbench.adapters.mcp_server import SUPPORTED, McpServer, serve_stdio
from vbench.adapters.package_templates import PackageTemplates
from vbench.adapters.toml_config import load_config
from vbench.app.mcp_tools import INSTRUCTIONS, mcp_tools

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "notes-app"
READ_TOOLS = {
    "project_overview",
    "get_use_case",
    "get_item",
    "impact",
    "read_file",
    "search_docs",
    "next_step",
    "status",
    "commit_message",
    "check",
    "next_id",
    "preview_change",
    "check_overlap",
}
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

    staged_paths: tuple[str, ...] = ()

    def staged(self) -> list[str]:
        return list(self.staged_paths)

    def unstaged(self) -> list[str]:
        return []

    def behind(self, base: str) -> int | None:
        return 0

    def branch_age_days(self, base: str) -> int | None:
        return None

    def stale_worktrees(self) -> list[str]:
        return []


class Committer:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], str]] = []

    def commit(self, paths, message):
        self.calls.append((list(paths), message))
        return "abc1234"


@pytest.fixture
def rig(tmp_path: Path):
    root = tmp_path / "notes"
    shutil.copytree(EXAMPLE, root, ignore=shutil.ignore_patterns(".vbench/ui", "node_modules", ".git"))
    repo, committer = Repo(), Committer()

    def server(write: bool = False, allow: bool = False) -> McpServer:
        tools = mcp_tools(
            lambda: (load_config(root), FsWorkspace(root)),
            repo,
            PackageTemplates(),
            committer,
            write=write,
            allow_default_branch=allow,
        )
        return McpServer("vbench", "9.9", tools, INSTRUCTIONS)

    return server, root, repo, committer


def rpc(server: McpServer, method: str, params: dict | None = None, ident: int = 1):
    return server.handle(
        {"jsonrpc": "2.0", "id": ident, "method": method, **({"params": params} if params is not None else {})}
    )


def call(server: McpServer, name: str, args: dict | None = None):
    reply = rpc(server, "tools/call", {"name": name, "arguments": args or {}})
    result = reply["result"]
    return result["isError"], result["content"][0]["text"]


# ------------------------------------------------------------------------------------------------- the protocol
def test_initialize_agrees_a_version_and_says_what_the_server_is(rig):
    server = rig[0]()
    ok = rpc(
        server,
        "initialize",
        {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}},
    )
    assert ok["result"]["protocolVersion"] == "2024-11-05" and ok["result"]["serverInfo"] == {
        "name": "vbench",
        "version": "9.9",
    }
    assert (
        ok["result"]["capabilities"]["tools"] == {"listChanged": False}
        and "preview_change" in ok["result"]["instructions"]
    )
    assert rpc(server, "initialize", {"protocolVersion": "1999-01-01"})["result"]["protocolVersion"] == SUPPORTED[0]


def test_a_notification_gets_no_reply_and_ping_answers(rig):
    server = rig[0]()
    assert server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
    assert rpc(server, "ping")["result"] == {}


def test_unknown_methods_and_malformed_requests_are_protocol_errors(rig):
    server = rig[0]()
    assert rpc(server, "resources/list")["error"]["code"] == -32601
    assert server.handle({"id": 3, "method": "ping"})["error"]["code"] == -32600  # no jsonrpc marker
    assert server.handle("nonsense")["error"]["code"] == -32600
    assert rpc(server, "tools/call", {"name": "no_such_tool"})["error"]["code"] == -32602
    assert rpc(server, "tools/call", {"name": "check", "arguments": "x"})["error"]["code"] == -32602


def test_stdio_carries_only_json_lines_and_survives_a_bad_line(rig):
    server = rig[0]()
    lines = [
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": SUPPORTED[0]}}),
        "{this is not json",
        "",
        json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
        json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}),
    ]
    out = io.StringIO()
    serve_stdio(server, io.StringIO("\n".join(lines) + "\n"), out)
    replies = [json.loads(line) for line in out.getvalue().splitlines()]  # every line of output parses: nothing stray
    assert [r.get("id") for r in replies] == [1, None, 2] and replies[1]["error"]["code"] == -32700
    assert {t["name"] for t in replies[2]["result"]["tools"]} == READ_TOOLS


def test_a_batch_is_answered_as_a_batch(rig):
    out = rig[0]().handle(
        [{"jsonrpc": "2.0", "id": 1, "method": "ping"}, {"jsonrpc": "2.0", "method": "notifications/x"}]
    )
    assert out == [{"jsonrpc": "2.0", "id": 1, "result": {}}]


# ------------------------------------------------------------------------------------------------- the tools
def test_reading_is_always_offered_and_changing_only_when_enabled(rig):
    server = rig[0]
    names = lambda s: {t["name"]: t["annotations"] for t in rpc(s, "tools/list")["result"]["tools"]}  # noqa: E731
    read_only = names(server())
    assert set(read_only) == READ_TOOLS and all(
        a["readOnlyHint"] and not a["destructiveHint"] for a in read_only.values()
    )
    enabled = names(server(write=True))
    assert set(enabled) == READ_TOOLS | {"apply_change", "commit_changes"}
    assert all(
        enabled[n]["destructiveHint"] and not enabled[n]["readOnlyHint"] for n in ("apply_change", "commit_changes")
    )
    tool = rpc(server(), "tools/list")["result"]["tools"][0]
    assert tool["inputSchema"]["type"] == "object" and tool["description"] and tool["title"]


def test_the_read_tools_answer_from_the_project(rig):
    server = rig[0]()
    err, text = call(server, "project_overview")
    assert not err and {u["id"] for u in json.loads(text)["useCases"]} == {"UC-N-001", "UC-N-002", "UC-N-003"}
    assert "UC-N-002" in call(server, "get_use_case", {"id": "UC-N-002"})[1]
    assert json.loads(call(server, "next_step")[1])["command"].startswith("/vbench:")
    gates = json.loads(call(server, "check", {"gate": "links"})[1])
    assert gates[0]["name"] == "links" and gates[0]["passing"] is True
    assert json.loads(call(server, "next_id", {"kind": "fr"})[1]) == ["REQ-FR-004"]
    assert json.loads(call(server, "next_id", {"kind": "ac", "area": "N", "count": 2})[1]) == ["AC-N-007", "AC-N-008"]


def test_a_tool_that_fails_reports_it_as_a_result_the_model_can_read(rig):
    server = rig[0]()
    err, text = call(server, "check", {"gate": "everything"})
    assert err and "gate" in text
    err, text = call(server, "next_id", {"kind": "fr", "count": 500})
    assert err and "1 to 50" in text
    err, text = call(server, "preview_change", {"change": {"op": "add", "kind": "tweet"}})
    assert err and "kind" in text
    assert call(server, "get_item", {"id": "NOPE"})[0] is False  # a missing item is an answer, not a failure


def test_previewing_writes_nothing_and_the_overlap_check_finds_the_closest_entry(rig):
    server, root, _, _ = rig
    s = server()
    before = (root / "docs/00-requirements-engineering.md").read_text()
    err, text = call(s, "preview_change", {"change": PROBLEM})
    plan = json.loads(text)
    assert not err and plan["change"]["id"] == "STK-PRB-004" and plan["digest"] and "STK-PRB-004" in plan["diff"]
    ask = {
        "change": {
            "op": "add",
            "kind": "request",
            "fields": {
                "text": "I want to keep notes: write one, read it later, and fix it when I got something wrong."
            },
        }
    }
    found = json.loads(call(s, "check_overlap", ask)[1])
    assert found["verdict"] == "duplicate" and found["matches"][0]["id"] == "STK-REQ-001" and found["source"] == "rules"
    assert (root / "docs/00-requirements-engineering.md").read_text() == before


def test_applying_needs_the_digest_of_what_was_previewed_and_commit_takes_docs_only(rig):
    server, root, _, committer = rig
    s = server(write=True)
    plan = json.loads(call(s, "preview_change", {"change": PROBLEM})[1])
    assert (
        call(s, "apply_change", {"change": PROBLEM, "digest": "not-it"})[0] is True
    )  # stale: refused, nothing written
    assert "A note cannot be shared" not in (root / "docs/00-requirements-engineering.md").read_text()
    err, text = call(s, "apply_change", {"change": PROBLEM, "digest": plan["digest"]})
    done = json.loads(text)
    assert (
        not err
        and done["id"] == "STK-PRB-004"
        and "A note cannot be shared" in (root / "docs/00-requirements-engineering.md").read_text()
    )
    err, text = call(s, "commit_changes", {"paths": done["written"], "summary": done["summary"]})
    assert (
        not err and json.loads(text)["commit"] == "abc1234" and committer.calls[0][1].startswith("chore: add problem")
    )
    assert call(s, "commit_changes", {"paths": ["src/notes/note.py"], "summary": "x"})[0] is True


def test_writing_is_refused_on_the_default_branch_unless_allowed(rig):
    server, root, repo, committer = rig
    repo.branch_name = "main"
    s = server(write=True)
    plan = json.loads(call(s, "preview_change", {"change": PROBLEM})[1])  # looking is fine
    err, text = call(s, "apply_change", {"change": PROBLEM, "digest": plan["digest"]})
    assert (
        err
        and "default branch" in text
        and "A note cannot be shared" not in (root / "docs/00-requirements-engineering.md").read_text()
    )
    assert (
        call(s, "commit_changes", {"paths": ["docs/00-requirements-engineering.md"], "summary": "x"})[0] is True
        and committer.calls == []
    )
    assert (
        call(server(write=True, allow=True), "apply_change", {"change": PROBLEM, "digest": plan["digest"]})[0] is False
    )


def test_a_very_long_result_is_cut(rig):
    server = rig[0]()
    server.tools["project_overview"] = server.tools["project_overview"].__class__(
        **{**server.tools["project_overview"].__dict__, "handler": lambda a: "x" * 100_000}
    )
    err, text = call(server, "project_overview")
    assert not err and len(text) < 61_000 and text.endswith("...truncated")


def test_commit_message_plans_the_commit_for_the_staged_files_and_commits_nothing(rig):
    server, _root, repo, committer = rig
    s = server()
    err, text = call(s, "commit_message", {"summary": "Cover the limits", "type": "chore"})
    assert err and "Nothing is staged" in text  # nothing staged is a clear error
    repo.staged_paths = ("docs/00-glossary.md",)
    err, text = call(s, "commit_message", {"summary": "Cover the limits", "type": "chore"})
    plan = json.loads(text)
    assert not err and plan["message"] == "chore: cover the limits" and plan["blockers"] == []
    assert committer.calls == []  # planning never commits, and the read-only server offers no way to
