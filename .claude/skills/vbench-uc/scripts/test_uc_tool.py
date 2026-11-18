"""Tests for uc_tool.py. Run from this folder: python3 -m unittest test_uc_tool"""

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import uc_tool as u  # noqa: E402

rq = u.rq


def req(i, statement, **kw):
    row = {c: "" for c in rq.REQ_COLS}
    row.update(id=i, kind="functional", group="product", name="n", statement=statement,
              verification="acceptance test", today="not built", status="draft", release="R1")
    row.update(kw)
    return row


def ac(i, rid):
    row = {c: "" for c in rq.AC_COLS}
    row.update(id=i, requirements=rid, given="g", when="w", then="t", test_level="acceptance", status="draft")
    return row


def make_root():
    root = Path(tempfile.mkdtemp())
    (root / "vbench.json").write_text(json.dumps({'id_prefix': 'UC', 'system_name': 'Verify AI', 'providers': ['keycloak'], 'actors': ['administrator', 'auditor', 'project_manager', 'engineer', 'person', 'guest', 'system'], 'areas': {'A': 'BC-ACCESS', 'C': 'BC-CHECKLISTS', 'E': 'BC-ENDPOINTS', 'F': 'BC-FILES', 'G': 'BC-FRAMEWORKS', 'L': 'BC-AUDIT', 'P': 'BC-PROJECTS', 'V': 'BC-EVALUATIONS'}, 'diagram': {'actor_style': {'administrator': 'Admin', 'auditor': 'Auditor', 'project_manager': 'PM', 'engineer': 'Engineer', 'person': 'Person', 'guest': 'Guest', 'system': 'Sys'}, 'actor_colour': {'administrator': '#E65100', 'auditor': '#AD1457', 'project_manager': '#00838F', 'engineer': '#5D4037', 'person': '#1565C0', 'guest': '#6A1B9A', 'system': '#455A64'}, 'context_colour': {'BC-ACCESS': '#E8F0FE', 'BC-PROJECTS': '#FFFDE7', 'BC-FILES': '#ECEFF1', 'BC-ENDPOINTS': '#FFF3E0', 'BC-CHECKLISTS': '#E8F5E9', 'BC-EVALUATIONS': '#EDE7F6', 'BC-AUDIT': '#FBE9E7', 'BC-FRAMEWORKS': '#F3E5F5'}, 'actor_is_a': [['project_manager', 'engineer']]}}))
    (root / "docs/requirements").mkdir(parents=True)
    (root / "docs/domain/ontology").mkdir(parents=True)
    rq.write_rows(root / rq.PATHS["req"], rq.REQ_COLS,
                  [req("FR-1", "The system shall move an endpoint to the next stage.", objects="OBJ-E1; OBJ-E2"),
                   req("FR-2", "The system shall export a checklist.")])
    rq.write_rows(root / rq.PATHS["ac"], rq.AC_COLS, [ac("AC-1", "FR-1")])
    (root / "docs/domain/ontology/OBJ-E1-endpoint.md").write_text("```yaml\nid: OBJ-E1\ncontext: BC-ENDPOINTS\n```\n")
    return root


def run(root, *args, stdin=""):
    out, old = io.StringIO(), sys.stdin
    sys.stdin = io.StringIO(stdin)
    try:
        with redirect_stdout(out):
            code = u.main(["--root", str(root), *args])
    finally:
        sys.stdin = old
    return code, out.getvalue()


NEW = {"area": "E", "name": "Move an endpoint between stages", "actor": "project_manager",
       "satisfies": ["FR-1"], "criteria": ["AC-1"], "parameters": ["endpoint", "target stage", "reason"],
       "objects": ["OBJ-E1", "OBJ-E2"], "rules": [], "effects": ["adds a stage move: who, what and why"],
       "description": "A project manager moves an endpoint.", "main_flow": ["Ask", "Check", "Move"]}


class Tests(unittest.TestCase):
    def test_header_reads_back(self):
        root = make_root()
        code, _ = run(root, "create", stdin=json.dumps(NEW))
        self.assertEqual(code, 0)
        files = list((root / "docs/usecases").glob("UC-E1-*.md"))
        self.assertEqual(len(files), 1)
        h = u.parse_header(files[0].read_text())
        self.assertEqual(h["id"], "UC-E1")
        self.assertEqual(h["satisfies"][0], {"id": "FR-1", "reviewed": u.req_hash(rq.read_rows(root / rq.PATHS["req"])[0])})
        self.assertEqual(h["effects"], ["adds a stage move: who, what and why"])
        self.assertEqual(h["objects"], ["OBJ-E1", "OBJ-E2"])

    def test_next_id_counts_up(self):
        root = make_root()
        run(root, "create", stdin=json.dumps(NEW))
        _, out = run(root, "next-id", "E")
        self.assertIn("UC-E2", out)

    def test_create_refuses_unknown_requirement_and_actor(self):
        root = make_root()
        bad = dict(NEW, satisfies=["FR-99"], actor="wizard")
        code, out = run(root, "create", stdin=json.dumps(bad))
        self.assertEqual(code, 1)
        self.assertIn("FR-99", out)
        self.assertIn("actor", out)
        self.assertFalse((root / "docs/usecases").exists())

    def test_dry_run_writes_nothing(self):
        root = make_root()
        run(root, "create", "--dry-run", stdin=json.dumps(NEW))
        self.assertFalse((root / "docs/usecases").exists())

    def test_impact_before_and_after(self):
        root = make_root()
        _, out = run(root, "impact", "FR-1")
        self.assertIn("use cases: NONE", out)
        self.assertIn("AC-1", out)
        self.assertIn("OBJ-E1: file exists, BC-ENDPOINTS", out)
        self.assertIn("OBJ-E2: no file yet", out)
        run(root, "create", stdin=json.dumps(NEW))
        _, out = run(root, "impact", "FR-1")
        self.assertIn("UC-E1", out)
        self.assertIn("up to date", out)

    def test_changed_requirement_makes_use_case_suspect_until_stamped(self):
        root = make_root()
        run(root, "create", stdin=json.dumps(NEW))
        rows = rq.read_rows(root / rq.PATHS["req"])
        rows[0]["statement"] = "The system shall move an endpoint to any stage."
        rq.write_rows(root / rq.PATHS["req"], rq.REQ_COLS, rows)
        _, out = run(root, "impact", "FR-1")
        self.assertIn("SUSPECT", out)
        code, out = run(root, "validate")
        self.assertIn("SUSPECT", out)
        self.assertEqual(code, 0)
        run(root, "stamp", "UC-E1")
        _, out = run(root, "impact", "FR-1")
        self.assertIn("up to date", out)

    def test_file_repeats_the_requirement_and_criterion_text(self):
        root = make_root()
        run(root, "create", stdin=json.dumps(NEW))
        text = next((root / "docs/usecases").glob("*.md")).read_text()
        self.assertIn("**FR-1**: The system shall move an endpoint to the next stage.", text)
        self.assertIn("**AC-1** (acceptance, proves FR-1)", text)
        self.assertIn("- Given g", text)

    def test_file_says_how_it_is_verified(self):
        root = make_root()
        run(root, "create", stdin=json.dumps(NEW))
        text = next((root / "docs/usecases").glob("*.md")).read_text()
        self.assertIn("## How it is verified", text)
        self.assertIn("- acceptance: AC-1", text)
        run(root, "create", stdin=json.dumps(dict(NEW, area="P", criteria=[])))
        text = next((root / "docs/usecases").glob("UC-P1*.md")).read_text()
        self.assertIn("Nothing verifies it yet", text)

    def test_copied_text_drift_is_reported_and_sync_fixes_it(self):
        root = make_root()
        run(root, "create", stdin=json.dumps(NEW))
        rows = rq.read_rows(root / rq.PATHS["req"])
        rows[0]["statement"] = "The system shall move an endpoint to any stage."
        rq.write_rows(root / rq.PATHS["req"], rq.REQ_COLS, rows)
        _, out = run(root, "validate")
        self.assertIn("out of date with the requirements files", out)
        _, out = run(root, "sync", "UC-E1")
        self.assertIn("still suspect", out.replace("stays suspect", "still suspect"))
        text = next((root / "docs/usecases").glob("*.md")).read_text()
        self.assertIn("to any stage", text)
        _, out = run(root, "validate")
        self.assertNotIn("out of date", out)
        self.assertIn("SUSPECT", out)  # sync copies the text but only a person's stamp clears suspect

    def test_edited_flow_is_reported_until_stamped(self):
        root = make_root()
        run(root, "create", stdin=json.dumps(NEW))
        p = next((root / "docs/usecases").glob("*.md"))
        self.assertNotIn("FLOW CHANGED", run(root, "validate")[1])
        p.write_text(p.read_text().replace("1. Ask", "1. Ask politely"))
        self.assertIn("FLOW CHANGED", run(root, "validate")[1])
        self.assertIn("FLOW CHANGED", run(root, "impact", "UC-E1")[1])
        run(root, "stamp", "UC-E1")
        self.assertNotIn("FLOW CHANGED", run(root, "validate")[1])

    def test_check_upstream_reports_untagged_flows_and_steps(self):
        root = make_root()
        data = dict(NEW, main_flow=["Ask (FR-1)", "Check"],
                    other_flows=["Retired endpoint: refused (AC-1)", "Empty reason: refused", "Open: later"])
        run(root, "create", stdin=json.dumps(data))
        code, out = run(root, "check-upstream", "UC-E1")
        self.assertEqual(code, 0)
        self.assertIn('step has no requirement recorded: "Check"', out)
        self.assertIn('other flow has no criterion recorded: "Empty reason: refused"', out)
        self.assertNotIn("Open: later", out)
        self.assertNotIn("FR-1: no step", out)
        self.assertNotIn("AC-1: listed, but", out)

    def test_check_upstream_reports_unserved_requirement_and_unlisted_criterion(self):
        root = make_root()
        run(root, "create", stdin=json.dumps(dict(NEW, criteria=[], main_flow=["Ask"], other_flows=[])))
        _, out = run(root, "check-upstream", "UC-E1")
        self.assertIn("FR-1: no step or other flow is tagged with it", out)
        self.assertIn("AC-1: proves a requirement this use case serves, but is not listed here", out)

    def test_slices_get_task_ids_and_are_checked(self):
        root = make_root()
        data = dict(NEW, rules=["RULE-E1"], slices=[
            {"name": "Refuse a retired endpoint", "proves": ["AC-1"], "rules": ["RULE-E1"]},
            {"name": "Move to the next stage"}])
        code, out = run(root, "create", stdin=json.dumps(data))
        self.assertEqual(code, 0, out)
        text = next((root / "docs/usecases").glob("*.md")).read_text()
        self.assertIn("- TSK-E1.1: Refuse a retired endpoint, rules RULE-E1 (AC-1)", text)
        self.assertIn("- TSK-E1.2: Move to the next stage", text)
        _, out = run(root, "validate")
        self.assertNotIn("no slice", out)
        self.assertNotIn("PROBLEM", out)

    def test_unproven_criterion_and_missing_rule_are_noted(self):
        root = make_root()
        data = dict(NEW, rules=["RULE-E1"], slices=[{"name": "Only one slice"}])
        run(root, "create", stdin=json.dumps(data))
        _, out = run(root, "validate")
        self.assertIn("AC-1 is listed but no slice proves it", out)
        self.assertIn("RULE-E1 is checked by this use case but no slice carries it", out)
        _, out = run(root, "check-upstream", "UC-E1")
        self.assertIn("AC-1 is listed but no slice proves it", out)

    def test_slice_may_not_prove_an_unlisted_criterion(self):
        root = make_root()
        data = dict(NEW, criteria=[], slices=[{"name": "x", "proves": ["AC-1"]}])
        code, out = run(root, "create", stdin=json.dumps(data))
        self.assertEqual(code, 1)
        self.assertIn("proves AC-1, which the use case does not list", out)

    def test_no_slices_is_only_a_note(self):
        root = make_root()
        run(root, "create", stdin=json.dumps(NEW))
        code, out = run(root, "validate")
        self.assertEqual(code, 0)
        self.assertIn("no slices yet", out)

    def test_diagram_is_drawn_from_the_files_in_the_mk3_look(self):
        root = make_root()
        _, out = run(root, "diagram", "E")
        self.assertIn("nothing to draw", out)
        run(root, "create", stdin=json.dumps(NEW))
        _, out = run(root, "diagram", "E")
        self.assertIn("@startuml usecases-endpoints", out)
        self.assertIn("' page: landscape", out)
        self.assertIn("!includesub _usecase-actors.puml!PM", out)
        self.assertIn("!startsub BOX", out)
        self.assertIn("!startsub LINKS", out)
        self.assertIn('as UC_E1 COLOR_TODO', out)       # FR-1 is not built in the fixture
        self.assertIn("PM -[#00838F]-> UC_E1", out)
        self.assertIn("#FFF3E0", out)                    # the context colour
        self.assertNotIn("\u2013", out)
        code, _ = run(root, "diagram", "E", "--write")
        self.assertEqual(code, 0)
        self.assertTrue((root / "docs/usecases/diagrams/usecases-endpoints.puml").exists())

    def test_built_requirements_make_the_oval_green(self):
        root = make_root()
        rows = rq.read_rows(root / rq.PATHS["req"])
        rows[0]["today"] = "built"
        rq.write_rows(root / rq.PATHS["req"], rq.REQ_COLS, rows)
        run(root, "create", stdin=json.dumps(NEW))
        _, out = run(root, "diagram", "E")
        self.assertIn("as UC_E1 COLOR_BUILT", out)

    def test_diagram_will_not_overwrite_a_file_kept_by_hand(self):
        root = make_root()
        run(root, "create", stdin=json.dumps(NEW))
        d = root / "docs/usecases/diagrams"
        d.mkdir(parents=True)
        (d / "usecases-endpoints.puml").write_text("@startuml hand\n@enduml\n")
        code, out = run(root, "diagram", "E", "--write")
        self.assertEqual(code, 1)
        self.assertIn("kept by hand", out)
        self.assertIn("hand", (d / "usecases-endpoints.puml").read_text())
        code, _ = run(root, "diagram", "E", "--write", "--force")
        self.assertEqual(code, 0)

    def test_overview_embeds_the_context_files(self):
        root = make_root()
        run(root, "create", stdin=json.dumps(NEW))
        d = root / "docs/usecases/diagrams"
        run(root, "diagram", "E", "--write")
        (d / "_usecase-actors.puml").write_text("!startsub PM\n!endsub\n!startsub SYS\n!endsub\n")
        code, _ = run(root, "diagram", "overview", "--write")
        self.assertEqual(code, 0)
        text = (d / "usecases-overview.puml").read_text()
        self.assertIn("!includesub usecases-endpoints.puml!BOX", text)
        self.assertIn("!includesub usecases-endpoints.puml!LINKS", text)
        self.assertIn("!includesub _usecase-actors.puml!SYS", text)
        self.assertIn("' page: overview", text)

    # ---- analysis, design and the change log

    def _with_sections(self, analysis="", design="", changes=""):
        root = make_root()
        run(root, "create", stdin=json.dumps(NEW))
        p = next((root / "docs/usecases").glob("*.md"))
        text = p.read_text()
        if analysis:
            text += "\n## Analysis\n\n### Revision 1\n\n" + analysis + "\n"
        if design:
            text += "\n## Design\n\n" + design + "\n"
        if changes:
            text += "\n## Changes from analysis to design\n\n" + changes + "\n"
        p.write_text(text)
        return root, p

    A = "- A1 (object): Evaluation\n- A2 (step): record the endpoint at this moment\n- A3 (port): endpoint lookup"
    D = "- D1 (aggregate): Evaluation\n- D2 (value object): TargetSnapshot\n- D3 (port): EndpointReader"
    LOG = "- A1 kept -> D1\n- A2 became -> D2: matches the target snapshot\n- A3 renamed -> D3"

    def test_analysis_needs_a_sequence_diagram_and_links_must_exist(self):
        root, p = self._with_sections(analysis=self.A)
        _, out = run(root, "validate")
        self.assertIn("Analysis section but no UC-E1-<slug>-analysis-sequence.puml", out)
        p.write_text(p.read_text() + "\nSee diagrams/UC-E1-move-design-sequence.puml\n")
        _, out = run(root, "validate")
        self.assertIn("UC-E1-move-design-sequence.puml, which does not exist", out)
        d = root / "docs/usecases/diagrams"
        d.mkdir()
        (d / "UC-E1-move-analysis-sequence.puml").write_text("@startuml\n@enduml\n")
        (d / "UC-E1-move-design-sequence.puml").write_text("@startuml\n@enduml\n")
        _, out = run(root, "validate")
        self.assertNotIn("sequence.puml", out)

    def test_no_analysis_is_only_a_note(self):
        root, _ = self._with_sections()
        code, out = run(root, "validate")
        self.assertEqual(code, 0)
        self.assertIn("no analysis yet", out)

    def test_a_complete_log_passes(self):
        root, _ = self._with_sections(self.A, self.D, self.LOG)
        code, out = run(root, "validate")
        self.assertEqual(code, 0, out)
        self.assertNotIn("LOST", out)

    def test_an_analysis_element_with_no_log_entry_is_lost(self):
        root, _ = self._with_sections(self.A, self.D, "- A1 kept -> D1\n- A2 became -> D2: x")
        code, out = run(root, "validate")
        self.assertEqual(code, 1)
        self.assertIn("UC-E1/A3: LOST", out)

    def test_dropping_needs_a_reason_and_no_target(self):
        log = "- A1 kept -> D1\n- A2 became -> D2: x\n- A3 dropped"
        root, _ = self._with_sections(self.A, "- D1 (aggregate): Evaluation\n- D2 (value object): T", log)
        code, out = run(root, "validate")
        self.assertEqual(code, 1)
        self.assertIn("A3: dropped with no reason", out)
        log = "- A1 kept -> D1\n- A2 became -> D2: x\n- A3 dropped: the aggregate does not look endpoints up"
        root, _ = self._with_sections(self.A, "- D1 (aggregate): Evaluation\n- D2 (value object): T", log)
        code, out = run(root, "validate")
        self.assertEqual(code, 0, out)

    def test_a_design_element_needs_a_source_or_an_added_reason(self):
        design = self.D + "\n- D4 (domain event): EvaluationStarted"
        root, _ = self._with_sections(self.A, design, self.LOG)
        code, out = run(root, "validate")
        self.assertEqual(code, 1)
        self.assertIn("D4: a design element with no source", out)
        root, _ = self._with_sections(self.A, design, self.LOG + "\n- + D4 added: the audit trail needs it")
        code, out = run(root, "validate")
        self.assertEqual(code, 0, out)

    def test_a_change_may_not_point_at_a_missing_element(self):
        root, _ = self._with_sections(self.A, self.D, self.LOG + "\n- A9 kept -> D1\n- A1 split -> D1, D8")
        code, out = run(root, "validate")
        self.assertEqual(code, 1)
        self.assertIn("A9, which is not in the analysis", out)
        self.assertIn("D8, which is not in the design", out)

    def test_a_frozen_analysis_cannot_be_edited_but_can_be_revised(self):
        root, p = self._with_sections(self.A, self.D, self.LOG)
        code, out = run(root, "freeze", "UC-E1")
        self.assertEqual(code, 0)
        self.assertIn("analysis_frozen: [", p.read_text())
        self.assertEqual(run(root, "validate")[0], 0)
        p.write_text(p.read_text().replace("- A1 (object): Evaluation", "- A1 (object): An evaluation run"))
        code, out = run(root, "validate")
        self.assertEqual(code, 1)
        self.assertIn("revision 1 was edited after the freeze", out)
        p.write_text(p.read_text().replace("- A1 (object): An evaluation run", "- A1 (object): Evaluation"))
        p.write_text(p.read_text().replace("## Design", "### Revision 2\n\n- A4 (rule): a retired endpoint cannot start one\n\n## Design"))
        code, out = run(root, "validate")
        self.assertIn("revision 2 is not frozen yet", out)
        self.assertIn("A4: LOST", out)

    def test_editing_the_design_is_not_a_change_to_the_flow(self):
        root, p = self._with_sections(self.A, self.D, self.LOG)
        run(root, "stamp", "UC-E1")
        self.assertNotIn("FLOW CHANGED", run(root, "validate")[1])
        p.write_text(p.read_text().replace("TargetSnapshot", "Snapshot of the target"))
        self.assertNotIn("FLOW CHANGED", run(root, "validate")[1])

    def test_trace_shows_what_became_of_each_analysis_element(self):
        root, _ = self._with_sections(self.A, self.D, "- A1 kept -> D1\n- A2 became -> D2: matches the snapshot")
        _, out = run(root, "trace", "UC-E1")
        self.assertIn("A1 (object) Evaluation", out)
        self.assertIn("kept -> D1 (aggregate) Evaluation", out)
        self.assertIn("became -> D2 (value object) TargetSnapshot  [matches the snapshot]", out)
        self.assertIn("A3 (port) endpoint lookup", out)
        self.assertIn("LOST: nothing says what happened to it", out)

    # ---- retired ids and explicit ids

    def _retire(self, root, *ids):
        p = root / "docs/usecases/retired-ids.csv"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("id,name,reason\r\n" + "".join(f"{i},x,provided elsewhere\r\n" for i in ids))

    def test_next_id_skips_retired_ids(self):
        root = make_root()
        self._retire(root, "UC-E1", "UC-E4")
        self.assertIn("UC-E5", run(root, "next-id", "E")[1])

    def test_create_with_an_explicit_free_id(self):
        root = make_root()
        code, out = run(root, "create", stdin=json.dumps(dict(NEW, id="UC-E7")))
        self.assertEqual(code, 0, out)
        self.assertTrue(list((root / "docs/usecases").glob("UC-E7-*.md")))

    def test_an_explicit_id_may_not_be_used_retired_or_in_another_area(self):
        root = make_root()
        run(root, "create", stdin=json.dumps(NEW))               # UC-E1
        self._retire(root, "UC-E3")
        for bad, why in (("UC-E1", "already used"), ("UC-E3", "retired"), ("UC-P1", "does not belong")):
            code, out = run(root, "create", stdin=json.dumps(dict(NEW, id=bad)))
            self.assertEqual(code, 1, bad)
            self.assertIn("REFUSED", out)

    def test_validate_refuses_a_file_that_uses_a_retired_id(self):
        root = make_root()
        run(root, "create", stdin=json.dumps(NEW))
        self._retire(root, "UC-E1")
        code, out = run(root, "validate")
        self.assertEqual(code, 1)
        self.assertIn("UC-E1 is retired and may not be used again", out)

    # ---- provided by Keycloak, and the person and guest actors

    def test_a_use_case_can_say_keycloak_provides_it(self):
        root = make_root()
        data = dict(NEW, actor="person", provided_by=["keycloak"])
        code, out = run(root, "create", stdin=json.dumps(data))
        self.assertEqual(code, 0, out)
        text = next((root / "docs/usecases").glob("*.md")).read_text()
        self.assertIn("provided_by: [keycloak]", text)
        self.assertEqual(run(root, "validate")[0], 0)
        _, out = run(root, "diagram", "E")
        self.assertIn("COLOR_PROVIDED", out)
        self.assertIn("Person -[#1565C0]->", out)

    def test_an_unknown_provider_is_refused(self):
        root = make_root()
        code, out = run(root, "create", stdin=json.dumps(dict(NEW, provided_by=["somebody"])))
        self.assertEqual(code, 1)
        self.assertIn("provided_by", out)

    def test_a_person_with_no_account_can_be_an_actor(self):
        root = make_root()
        self.assertEqual(run(root, "create", stdin=json.dumps(dict(NEW, actor="guest")))[0], 0)

    def test_a_note_edit_does_not_make_it_suspect(self):
        root = make_root()
        run(root, "create", stdin=json.dumps(NEW))
        rows = rq.read_rows(root / rq.PATHS["req"])
        rows[0]["notes"] = "something new"
        rq.write_rows(root / rq.PATHS["req"], rq.REQ_COLS, rows)
        _, out = run(root, "impact", "FR-1")
        self.assertIn("up to date", out)

    def test_coverage_lists_requirements_without_a_use_case(self):
        root = make_root()
        run(root, "create", stdin=json.dumps(NEW))
        _, out = run(root, "coverage")
        self.assertIn("FR-2", out)
        self.assertNotIn("FR-1,", out)

    def test_validate_catches_a_wrong_area(self):
        root = make_root()
        run(root, "create", stdin=json.dumps(NEW))
        p = next((root / "docs/usecases").glob("*.md"))
        p.write_text(p.read_text().replace("context: BC-ENDPOINTS", "context: BC-PROJECTS"))
        code, out = run(root, "validate")
        self.assertEqual(code, 1)
        self.assertIn("belongs to BC-ENDPOINTS", out)


class CollapsedCopyTests(unittest.TestCase):
    """The copied requirement text is collapsed, so a reader sees the flow first and opens the copy on purpose."""

    def block(self):
        reqs = {"FR-1": req("FR-1", "The system shall x.")}
        acs = {"AC-1": ac("AC-1", "FR-1")}
        return u.mirror({"satisfies": [{"id": "FR-1"}], "criteria": [{"id": "AC-1"}]}, reqs, acs)

    def test_the_copy_sits_inside_a_collapsed_details_block(self):
        b = self.block()
        self.assertIn("<details>", b)
        self.assertIn("<summary>", b)
        self.assertLess(b.index("<details>"), b.index("## What this serves"))
        self.assertLess(b.index("Each criterion is run"), b.index("</details>"))

    def test_the_summary_says_what_is_inside_and_not_to_edit_it(self):
        summary = self.block().split("<summary>")[1].split("</summary>")[0]
        self.assertIn("copied", summary)
        self.assertIn("1 requirement", summary)
        self.assertIn("1 criterion", summary)

    def test_the_markers_still_find_the_block_and_the_written_text_starts_after_it(self):
        b = self.block()
        text = "# Title\n\n" + b + "\n\n## Description\n\nThe flow."
        self.assertEqual(u.mirror_block(text), b)
        self.assertTrue(u.written_text(text).startswith("## Description"))

    def test_changing_only_the_copy_does_not_change_the_flow_hash(self):
        a = "# T\n\n" + self.block() + "\n\n## Main flow\n\n1. Do it.\n"
        reqs = {"FR-1": req("FR-1", "A different statement.")}
        other = u.mirror({"satisfies": [{"id": "FR-1"}], "criteria": []}, reqs, {})
        b = "# T\n\n" + other + "\n\n## Main flow\n\n1. Do it.\n"
        self.assertEqual(u.flow_hash(a), u.flow_hash(b))


if __name__ == "__main__":
    unittest.main()
