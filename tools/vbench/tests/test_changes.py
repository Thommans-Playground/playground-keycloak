"""Planning, applying and committing a change to the requirements, and the blast radius it reports."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from vbench.adapters.fs import FsWorkspace
from vbench.adapters.package_templates import PackageTemplates
from vbench.adapters.toml_config import load_config
from vbench.app.changes import apply_change, commit_changes, preview_change
from vbench.domain.changes import ChangeError, parse_change, plan_change
from vbench.domain.checks import check_docs
from vbench.domain.errors import StaleError, UsageError
from vbench.domain.requirements_doc import read_requirements
from vbench.domain.specs import read_specs

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "notes-app"


@pytest.fixture
def proj(tmp_path: Path) -> Path:
    root = tmp_path / "notes"
    shutil.copytree(EXAMPLE, root, ignore=shutil.ignore_patterns(".vbench/ui", "node_modules", ".git"))
    return root


def plan(proj: Path, **raw):
    return plan_change(load_config(proj), FsWorkspace(proj), parse_change(raw))


def effects(p, **match):
    return [(i.id, i.direction, i.effect) for i in p.impact if all(getattr(i, k) == v for k, v in match.items())]


def test_a_change_must_be_well_formed():
    for raw in (
        "x",
        {"op": "drop", "kind": "problem"},
        {"op": "add", "kind": "tweet"},
        {"op": "add", "kind": "problem", "fields": {"colour": "red"}},
        {"op": "add", "kind": "request", "fields": {"problems": "STK-PRB-001"}},
        {"op": "update", "kind": "problem"},
        {"op": "update", "kind": "problem", "id": "STK-REQ-001"},
        {"op": "add", "kind": "problem", "fields": {"text": "x" * 2001}},
    ):
        with pytest.raises(ChangeError):
            parse_change(raw)


def test_adding_a_problem_allocates_the_next_id_and_touches_only_that_table(proj: Path):
    p = plan(
        proj,
        op="add",
        kind="problem",
        fields={"text": "A note cannot be shared", "who": "The author", "cost": "It stays here."},
    )
    assert p.errors == [] and p.change.id == "STK-PRB-004" and p.summary == "Add problem STK-PRB-004"
    assert [ln for ln in p.diff.split("\n") if ln.startswith(("+|", "-|"))] == [
        "+| **STK-PRB-004** | A note cannot be shared | The author | It stays here. |"
    ]
    assert "request" in p.next_step and p.digest


def test_a_value_with_a_pipe_or_a_newline_cannot_break_the_table(proj: Path):
    p = plan(proj, op="add", kind="problem", fields={"text": "one | two\nthree", "who": "x"})
    assert "| **STK-PRB-004** | one \\| two three | x |" in p.diff


def test_required_fields_and_links_are_checked(proj: Path):
    assert plan(proj, op="add", kind="problem", fields={"who": "x"}).errors == ["`text` is required"]
    p = plan(proj, op="add", kind="request", fields={"text": "Ask", "problems": ["STK-PRB-099"]})
    assert p.errors == ["STK-PRB-099 is not a problem in the requirements doc"] and p.edits == {}
    p = plan(proj, op="add", kind="functional", fields={"text": "Do it", "satisfies": ["STK-REQ-099"]})
    assert p.errors == ["STK-REQ-099 is not a request in the requirements doc"]
    assert plan(proj, op="update", kind="problem", id="STK-PRB-099", fields={"text": "x"}).errors


def test_a_near_duplicate_is_warned_about_not_refused(proj: Path):
    p = plan(proj, op="add", kind="problem", fields={"text": "A note saved over by mistake loses what it said before"})
    assert p.errors == [] and "STK-PRB-003" in p.warnings[0]


def test_adding_a_request_says_what_it_does_to_the_problem_it_names(proj: Path):
    p = plan(
        proj,
        op="add",
        kind="request",
        fields={"text": "Stop me overwriting notes", "raised_by": "STK-PER-001", "problems": ["STK-PRB-003"]},
    )
    assert effects(p, id="STK-PRB-003") == [("STK-PRB-003", "up", "status-changes")]
    assert '| **STK-REQ-003** | STK-PER-001 | STK-PRB-003 | "Stop me overwriting notes" |' in p.diff
    q = plan(proj, op="add", kind="request", fields={"text": "Another way in", "problems": ["STK-PRB-001"]})
    assert effects(q, id="STK-PRB-001") == [("STK-PRB-001", "up", "link-added")]  # it already had a request


def test_a_quality_requirement_is_written_to_both_its_tables_and_asks_for_a_measure(proj: Path):
    p = plan(
        proj,
        op="add",
        kind="quality",
        fields={"quality": "Speed", "outline": "Notes open fast", "satisfies": ["STK-REQ-001"]},
    )
    assert p.errors == [] and any("response measure" in w for w in p.warnings)
    added = [ln for ln in p.diff.split("\n") if ln.startswith("+| **REQ-NFR-003**")]
    assert len(added) == 2 and "STK-REQ-001" in added[0] and "Speed" in added[1]


def test_changing_what_a_requirement_says_flags_what_hangs_below_it_for_review(proj: Path):
    p = plan(
        proj,
        op="update",
        kind="functional",
        id="REQ-FR-001",
        fields={"text": "The system shall let the author save a note.", "story": "x"},
    )
    assert ("UC-N-001", "down", "needs-review") in effects(p)
    assert ("AC-N-001", "down", "needs-review") in effects(p)
    deep = [i for i in p.impact if i.kind == "test"]
    assert deep and all(i.effect == "affected" for i in deep)
    assert not [i for i in p.impact if i.direction == "up"]  # wording is not a link: nothing above changes


def test_changing_only_a_link_moves_status_up_the_trace_and_not_review_down(proj: Path):
    p = plan(proj, op="update", kind="functional", id="REQ-FR-002", fields={"satisfies": ["STK-REQ-002"]})
    assert ("STK-REQ-002", "up", "link-added") in effects(p)
    assert ("STK-REQ-001", "up", "link-removed") in effects(p)
    assert not [i for i in p.impact if i.effect == "needs-review"]
    gone = plan(proj, op="update", kind="functional", id="REQ-FR-002", fields={"satisfies": []})
    assert ("REQ-FR-002", "here", "orphaned") in effects(gone)


def test_deleting_a_problem_cleans_the_links_to_it_and_flags_what_was_left_without_one(proj: Path):
    p = plan(proj, op="delete", kind="problem", id="STK-PRB-001")
    assert ("STK-REQ-001", "down", "link-removed") in effects(p) and p.impact[0].auto
    assert ("STK-REQ-001", "down", "orphaned") in effects(p)
    assert '| **STK-REQ-001** | STK-PER-001 |  | "I want to keep notes' in p.diff
    assert "STK-PRB-001** |" not in p.edits["docs/00-requirements-engineering.md"]


def test_deleting_a_request_unlinks_its_requirements_and_changes_the_problem_it_addressed(proj: Path):
    p = plan(proj, op="delete", kind="request", id="STK-REQ-002")
    assert ("STK-PRB-002", "up", "status-changes") in effects(p)  # it was the only request for that problem
    q = plan(proj, op="delete", kind="request", id="STK-REQ-001")
    assert {("REQ-FR-001", "down", "link-removed"), ("REQ-NFR-002", "down", "link-removed")} <= set(effects(q))
    assert ("REQ-FR-001", "down", "orphaned") in effects(q)
    after = read_requirements_from(proj, q)
    assert all("STK-REQ-001" not in x.satisfies for x in (*after.functional, *after.quality))


def test_deleting_a_requirement_flags_the_use_cases_and_criteria_that_still_name_it(proj: Path):
    p = plan(proj, op="delete", kind="functional", id="REQ-FR-001")
    assert ("UC-N-001", "down", "needs-review") in effects(p)
    assert ("AC-N-001", "down", "needs-review") in effects(p)
    assert ("STK-REQ-001", "up", "link-removed") in effects(p)  # the request still has other requirements
    only = plan(proj, op="delete", kind="functional", id="REQ-FR-003")
    assert "| **REQ-FR-003** |" not in only.edits["docs/00-requirements-engineering.md"]  # the row is gone ...
    assert ("UC-N-003", "down", "needs-review") in effects(only)  # ... and the spec that realises it is flagged


def test_nothing_is_written_by_planning(proj: Path):
    before = (proj / "docs/00-requirements-engineering.md").read_text()
    plan(proj, op="delete", kind="problem", id="STK-PRB-001")
    preview_change(load_config(proj), FsWorkspace(proj), {"op": "add", "kind": "problem", "fields": {"text": "x"}})
    assert (proj / "docs/00-requirements-engineering.md").read_text() == before


def test_apply_writes_the_previewed_change_regenerates_and_runs_the_gates(proj: Path):
    cfg, ws = load_config(proj), FsWorkspace(proj)
    raw = {
        "op": "add",
        "kind": "problem",
        "fields": {"text": "A note cannot be shared", "who": "The author", "cost": "It stays."},
    }
    shown = preview_change(cfg, ws, raw)
    done = apply_change(cfg, ws, raw, shown["digest"])
    assert done["id"] == "STK-PRB-004" and done["written"] == ["docs/00-requirements-engineering.md"]
    assert {g["name"] for g in done["gates"]} >= {"refs", "docs", "links"}
    assert [p.id for p in read_requirements(cfg, ws).problems][-1] == "STK-PRB-004"
    assert check_docs(cfg, ws).ok


def test_a_preview_that_is_no_longer_true_is_refused_not_applied(proj: Path):
    cfg, ws = load_config(proj), FsWorkspace(proj)
    raw = {"op": "add", "kind": "problem", "fields": {"text": "First"}}
    shown = preview_change(cfg, ws, raw)
    apply_change(
        cfg,
        ws,
        {"op": "add", "kind": "problem", "fields": {"text": "Sneaked in meanwhile"}},
        preview_change(cfg, ws, {"op": "add", "kind": "problem", "fields": {"text": "Sneaked in meanwhile"}})["digest"],
    )
    with pytest.raises(StaleError):
        apply_change(cfg, ws, raw, shown["digest"])
    with pytest.raises(UsageError):
        apply_change(cfg, ws, {"op": "add", "kind": "problem", "fields": {}}, "x")  # errors are refused too


def test_only_documentation_files_are_committed_with_a_conventional_message(proj: Path):
    cfg, ws = load_config(proj), FsWorkspace(proj)
    seen = []

    class Committer:
        def commit(self, paths, message):
            seen.append((list(paths), message))
            return "abc1234"

    out = commit_changes(cfg, ws, Committer(), ["docs/00-requirements-engineering.md"], "Add problem STK-PRB-004")
    assert out["commit"] == "abc1234" and seen == [
        (["docs/00-requirements-engineering.md"], "chore: add problem STK-PRB-004")
    ]
    assert cfg.commit_re.match(out["message"])
    for bad in (["src/notes/note.py"], ["../x.md"], ["/etc/passwd"], ["docs/missing.md"], [], "docs/a.md", [3]):
        with pytest.raises(UsageError):
            commit_changes(cfg, ws, Committer(), bad, "x")


def read_requirements_from(proj: Path, p):
    from vbench.domain.requirements_doc import parse_requirements

    return parse_requirements(p.edits["docs/00-requirements-engineering.md"])


# ------------------------------------------------------------------------------------------ criteria and use cases
def plan_with_template(proj: Path, **raw):
    from vbench.app.new import spec_template

    cfg, ws = load_config(proj), FsWorkspace(proj)
    return plan_change(cfg, ws, parse_change(raw), spec_template=spec_template(cfg, ws, PackageTemplates()))


def test_a_criterion_or_a_use_case_can_only_be_added_from_here():
    for raw in (
        {"op": "update", "kind": "criterion", "id": "AC-N-001", "fields": {"text": "x"}},
        {"op": "delete", "kind": "usecase", "id": "UC-N-001"},
    ):
        with pytest.raises(ChangeError, match="can only be added"):
            parse_change(raw)


def test_a_criterion_fills_the_scaffold_row_when_the_spec_still_has_one(proj: Path):
    text = "Given an author with a saved note, when they change its title, then the title is updated."
    p = plan(proj, op="add", kind="criterion", fields={"uc": "UC-N-003", "text": text, "satisfies": ["REQ-FR-003"]})
    assert (
        p.errors == [] and p.change.id == "AC-N-006" and "fills the scaffold row" in p.summary
    )  # UC-N-003 had a TBD row
    spec = "docs/usecase-diagrams/UC-N-003-edit-note.md"
    assert list(p.edits) == [spec] and f"+| **AC-N-006** | {text} | REQ-FR-003 |" in p.diff
    assert any("No test carries AC-N-006" in w for w in p.warnings)
    assert ("REQ-FR-003", "up", "link-added") in effects(p) and ("UC-N-003", "up", "link-added") in effects(p)
    assert "AC-N-006" in p.next_step


def test_a_criterion_is_added_with_a_new_id_when_every_row_is_written(proj: Path):
    p = plan(
        proj,
        op="add",
        kind="criterion",
        fields={"uc": "UC-N-001", "text": "Given a, when b, then c.", "satisfies": ["REQ-FR-001"]},
    )
    assert p.change.id == "AC-N-007" and "fills" not in p.summary  # AC-N-001..006 exist already
    assert any(ln.startswith("+| **AC-N-007**") for ln in p.diff.split("\n"))


def test_a_criterion_is_checked(proj: Path):
    ok = {"uc": "UC-N-001", "text": "Given a, when b, then c.", "satisfies": ["REQ-FR-001"]}
    assert plan(proj, op="add", kind="criterion", fields={**ok, "uc": "UC-N-099"}).errors == [
        "UC-N-099 has no spec under docs/usecase-diagrams"
    ]
    assert (
        "not a requirement"
        in plan(proj, op="add", kind="criterion", fields={**ok, "satisfies": ["REQ-FR-099"]}).errors[0]
    )
    assert plan(proj, op="add", kind="criterion", fields={"uc": "UC-N-001"}).errors == ["`text` is required"]
    loose = plan(proj, op="add", kind="criterion", fields={**ok, "text": "It should work."})
    assert loose.errors == [] and any("Given" in w for w in loose.warnings)


def test_a_use_case_is_the_same_file_vbench_new_uc_writes_naming_what_it_realises(proj: Path):
    p = plan_with_template(
        proj, op="add", kind="usecase", fields={"title": "Share a note", "area": "n", "realises": ["REQ-FR-001"]}
    )
    assert p.errors == [] and p.change.id == "UC-N-004" and p.summary == "Add use case UC-N-004"
    ((path, body),) = p.edits.items()
    assert path == "docs/usecase-diagrams/UC-N-004-share-a-note.md" and body.startswith("# UC-N-004 - Share a note")
    assert "| **Realises** | REQ-FR-001 |" in body and "AC-X-nnn" not in body and "TSK-X-nnn" not in body
    assert (
        "| **AC-N-007** | TBD:" in body and "REQ-FR-001 |" in body.split("AC-N-007")[1].split("\n")[0]
    )  # the scaffold criterion cites it
    assert ("REQ-FR-001", "up", "link-added") in effects(p) and "UC-N-004" in p.next_step
    assert p.diff.startswith("--- docs/usecase-diagrams/UC-N-004-share-a-note.md")


def test_a_use_case_is_checked(proj: Path):
    assert plan_with_template(proj, op="add", kind="usecase", fields={"title": "x", "area": "NN"}).errors == [
        "`area` is a single letter, the area code"
    ]
    assert (
        "no letters"
        in plan_with_template(proj, op="add", kind="usecase", fields={"title": "!!!", "area": "N"}).errors[0]
    )
    assert plan(proj, op="add", kind="usecase", fields={"title": "Share", "area": "N"}).errors == [
        "there is no use-case template to scaffold from"
    ]
    assert (
        "not a requirement"
        in plan_with_template(
            proj, op="add", kind="usecase", fields={"title": "x", "area": "N", "realises": ["REQ-FR-099"]}
        ).errors[0]
    )


def test_applying_a_use_case_writes_the_spec_and_regenerates_the_map_and_the_backlog(proj: Path):
    cfg, ws, t = load_config(proj), FsWorkspace(proj), PackageTemplates()
    raw = {"op": "add", "kind": "usecase", "fields": {"title": "Share a note", "area": "N", "realises": ["REQ-FR-001"]}}
    shown = preview_change(cfg, ws, raw, t)
    done = apply_change(cfg, ws, raw, shown["digest"], t)
    assert done["id"] == "UC-N-004" and "docs/usecase-diagrams/UC-N-004-share-a-note.md" in done["written"]
    assert any(p.endswith("08-usecase-diagrams.puml") for p in done["regenerated"])
    assert "UC-N-004" in (proj / "docs/08-usecase-diagrams.puml").read_text() and check_docs(cfg, ws).ok
    assert "UC-N-004" in {u.uc for u in read_specs(cfg, ws)}


def test_applying_a_criterion_edits_only_that_spec_and_the_trace_sees_it(proj: Path):
    from vbench.domain.requirements_doc import read_criteria

    cfg, ws = load_config(proj), FsWorkspace(proj)
    raw = {
        "op": "add",
        "kind": "criterion",
        "fields": {
            "uc": "UC-N-003",
            "text": "Given a note, when I edit it, then it changes.",
            "satisfies": ["REQ-FR-003"],
        },
    }
    done = apply_change(cfg, ws, raw, preview_change(cfg, ws, raw)["digest"])
    assert (
        done["written"] == ["docs/usecase-diagrams/UC-N-003-edit-note.md"]
        and next(g for g in done["gates"] if g["name"] == "acs")["ok"] is False
    )
    c = read_criteria(cfg, ws)["AC-N-006"]
    assert c.text == "Given a note, when I edit it, then it changes." and c.satisfies == ("REQ-FR-003",)


# ------------------------------------------------------------------------------------------------- safety
def test_a_commit_can_be_limited_to_what_an_applied_change_wrote(proj: Path):
    cfg, ws = load_config(proj), FsWorkspace(proj)
    seen = []

    class Committer:
        def commit(self, paths, message):
            seen.append(list(paths))
            return "abc1234"

    raw = {"op": "add", "kind": "problem", "fields": {"text": "A note cannot be shared with anyone."}}
    written: set[str] = set()
    with pytest.raises(UsageError):  # nothing applied yet, so nothing may be committed through this path
        commit_changes(cfg, ws, Committer(), ["docs/00-requirements-engineering.md"], "x", written)
    shown = preview_change(cfg, ws, raw)
    apply_change(cfg, ws, raw, shown["digest"], written=written)
    assert written == {"docs/00-requirements-engineering.md"}
    with pytest.raises(UsageError):  # another documentation file the caller did not change
        commit_changes(cfg, ws, Committer(), ["docs/00-glossary.md"], "x", written)
    out = commit_changes(cfg, ws, Committer(), ["./docs/../docs/00-requirements-engineering.md"], "x", written)
    assert seen == [["docs/00-requirements-engineering.md"]] and out["paths"] == seen[0]  # git got the clean path
    assert written == set()


def test_a_failed_write_puts_back_the_files_already_written(proj: Path, monkeypatch):
    from vbench.app import changes as app_changes
    from vbench.domain.changes import edits_digest

    cfg, real = load_config(proj), FsWorkspace(proj)
    raw = {"op": "add", "kind": "problem", "fields": {"text": "A note cannot be shared with anyone."}}
    base = plan_change(cfg, real, parse_change(raw))
    first, second = "docs/00-requirements-engineering.md", "docs/00-glossary.md"
    base.edits = {first: base.edits[first], second: real.read(second) + "\nchanged\n"}  # a plan that writes two files
    base.digest = edits_digest(base.edits)
    monkeypatch.setattr(app_changes, "_plan", lambda *a, **k: base)
    before = {f: real.read(f) for f in base.edits}

    class Failing:
        def __getattr__(self, name):
            return getattr(real, name)

        def write(self, rel, text, overwrite=True):
            if rel == second:
                raise OSError("disk full")
            return real.write(rel, text, overwrite)

    with pytest.raises(UsageError, match="nothing was changed"):
        apply_change(cfg, Failing(), raw, base.digest)
    assert {f: real.read(f) for f in before} == before  # the first file was put back


def test_the_workspace_never_reads_or_writes_outside_the_project(tmp_path: Path):
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "proj"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "link").symlink_to(outside)
    ws = FsWorkspace(root)
    with pytest.raises(ValueError):
        ws.write("docs/link/evil.md", "x")
    with pytest.raises(ValueError):
        ws.write("../evil.md", "x")
    assert not (outside / "evil.md").exists() and not ws.exists("docs/link")
    assert ws.write("docs/ok.md", "fine") and ws.read("docs/ok.md") == "fine"
    assert [p.name for p in (root / "docs").iterdir() if p.name != "link"] == ["ok.md"]  # no temp file left behind


def test_writing_is_refused_off_a_branch_or_on_the_default_branch():
    from vbench.domain.paths import branch_block

    assert branch_block("feature", "main", False) == ""
    assert "default branch" in branch_block("main", "main", False)
    assert "not on a branch" in branch_block("", "main", False)  # detached HEAD, or no git
    assert branch_block("main", "main", True) == branch_block("", "main", True) == ""
