# Skills and agents: one job each

Every skill and agent in `.claude/` has one job, a place on the V, and a named owner for each thing it touches. This
page is the map. The capabilities that must not be lost are in [the ledger](skills-and-agents-ledger.md), and
`.claude/skills/_vbench/test_scope.py` fails when a skill or agent has no row here, a hand-off names something that
does not exist, or a ledger item has gone. The decision is [ADR 0017](../adr/0017-one-owner-for-each-skill-and-agent-job.md).

**ASPICE is the yardstick, not a claim.** The process is inspired by Automotive SPICE: a left arm that specifies, a
vertex that builds, a right arm that proves, and support processes around them. We make no conformance claim. The
process names below are from memory (the 3.1 names, which 4.0 reorganised) and carry no base-practice numbers. This is
the one place the mapping is written; the skills do not repeat it.

## The map

| Arm | ASPICE process it is inspired by | Skills and agents |
|---|---|---|
| Left: specify | system and software requirements analysis | `vbench-req`, `vbench-uc` |
| Left: design | software architectural design, detailed design | `vbench-ontology`, `vbench-contexts`, `vbench-diagrams`, `vbench-mermaid`, `vbench-puml`, `vbench-decide` |
| Vertex: build | software construction | `vbench-tdd`, `vbench-tdd-red`, `vbench-tdd-green`, `vbench-tdd-refactor` |
| Right: prove | unit verification, integration test, qualification test, cybersecurity verification | `vbench-at`, `vbench-test-stack`, `vbench-vcycle`, `vbench-status`, `vbench-security-test`, `vbench-security-tester` |
| Beside: review before building | verification of work products by review, quality assurance | `vbench-spec-challenger`, `vbench-design-reviewer`, `vbench-security-reviewer` |
| Beside: configuration and change | configuration management, change control | `vbench-branch`, `vbench-commit`, `vbench-pr` |
| Beside: adoption | tailoring the process to a project (the ASPICE idea of tailoring), introduced one area at a time | `vbench-adopt`, `vbench-next` |
| Beside: knowledge transfer | training | `vbench-walkthrough`, `vbench-explain` |

## Roles

"Owns" is what only this role may decide or write. "Hands off to" is where it sends what is not its job.

| Role | Owns | Does not | Hands off to | Pack |
|---|---|---|---|---|
| `vbench-req` | requirement and criterion rows, their ids, wording and duplicates | use case flows, objects, tests | `vbench-uc`, `vbench-at`, `vbench-ontology`, `vbench-contexts` | core |
| `vbench-uc` | the use case file, impact, slices, the analysis-to-design log, review stamps, freeze | requirement rows, ontology files | `vbench-req`, `vbench-at`, `vbench-ontology`, `vbench-contexts` | core |
| `vbench-ontology` | objects, links, rules, value sets, ports as files | use case flow, where a boundary goes, decisions | `vbench-contexts`, `vbench-decide` | ddd |
| `vbench-contexts` | the challenge of a context, aggregate, port or hexagon choice | writing objects, technical decisions | `vbench-ontology`, `vbench-decide` | ddd |
| `vbench-decide` | `docs/domain/decisions.md` and `docs/adr/`, and making a decision checked and exampled | the owner's choices (scope, people, permissions, risk) | the three reviewers, `vbench-tdd` | core |
| `vbench-diagrams` | which format a diagram takes | drawing | `vbench-mermaid`, `vbench-puml` | ddd |
| `vbench-mermaid` | small inline diagrams in a document | reference and per-use-case diagrams | `vbench-diagrams`, `vbench-puml` | ddd |
| `vbench-puml` | `.puml` reference and per-use-case diagrams, the A4 fit check | inline diagrams | `vbench-diagrams`, `vbench-mermaid` | ddd |
| `vbench-tdd` | one slice, test first: order, preconditions, a pause after each step, closing the slice | writing the test or the code itself | the three TDD agents, `vbench-commit` | core |
| `vbench-tdd-red` | the one failing test, proved to fail for the right reason | production code beyond a stub | `vbench-tdd-green` | core |
| `vbench-tdd-green` | the minimum code that passes, placed by ADR 0010 | editing the test | `vbench-tdd-refactor` | core |
| `vbench-tdd-refactor` | behaviour-preserving tidying on green | new behaviour | `vbench-tdd` | core |
| `vbench-at` | the criterion-to-test link report, the skeleton and the test stamp | writing the real test | `vbench-tdd-red`, `vbench-req` | core |
| `vbench-test-stack` | running the whole gate on a fresh stack and reporting counts | judging test quality, fixing | `vbench-vcycle`, `vbench-at` | keycloak |
| `vbench-vcycle` | the per-use-case trace, as facts, from files | running tests, editing, stamping | `vbench-at`, `vbench-security-test`, `vbench-test-stack` | core |
| `vbench-status` | a table view of the trace | any check of its own | `vbench-vcycle` | core |
| `vbench-security-test` | the workflow and the check catalogue for live security tests | gating, fixing | `vbench-security-tester`, `vbench-req`, `vbench-tdd` | security |
| `vbench-security-tester` | probing one use case on the local stack | editing, deciding, flooding, any non-local target | `vbench-security-test` | security |
| `vbench-spec-challenger` | the flow, the criteria, the ids, the words and the open questions of a spec | architecture fit, security content | `vbench-design-reviewer`, `vbench-security-reviewer` | core |
| `vbench-design-reviewer` | the design against the architecture rules, the design diagram against the class diagram, the change log | spec wording, security content | `vbench-spec-challenger`, `vbench-security-reviewer` | ddd |
| `vbench-security-reviewer` | all security content on paper, from the checklists and the overlay | live testing | `vbench-security-tester` | security |
| `vbench-branch` | branch names and starting a branch | pushing, deleting | `vbench-commit` | core |
| `vbench-commit` | splitting changes and commit messages | pushing, amending | `vbench-pr` | core |
| `vbench-pr` | the pull request title, description and honest checklist | merging, approving | `vbench-branch`, `vbench-commit` | core |
| `vbench-next` | the front door: where each use case is and the one next step, in three moments | running a stamp or a freeze, doing the step for the person without a yes | `vbench-req`, `vbench-uc`, `vbench-at`, `vbench-tdd`, `vbench-security-test` | core |
| `vbench-adopt` | reading an existing project, the proposed config, and the ladder for adopting the harness one area at a time | moving, renaming or rewriting the project's own files, marking an area adopted because it was scanned | `vbench-req`, `vbench-uc`, `vbench-tdd`, `vbench-vcycle` | core |
| `vbench-walkthrough` | teaching existing code, one learner at a time, over a whole use case | editing code, reading the learner's notes | `vbench-tdd` | core |
| `vbench-explain` | the term cards in `docs/learn/terms/` and what the learner has seen; explaining one term where it comes up | reading the learner's notes, teaching a term twice | `vbench-walkthrough` | core |
| `vbench-execlog` | the shape of an execution log task file (steps, test levels, the summary entry) and its check | writing the code or the test, approving its own work | `vbench-tdd`, `vbench-walkthrough` | core |

## Who owns what when two could (decided in ADR 0017)

1. **The three reviewers split by subject.** The challenger owns the flow against the analysis diagram, ids, words and
   open questions. The design reviewer owns the design diagram against the class diagram, the architecture rules and
   the change log. The security reviewer owns everything that is security, including the abuse cases the challenger now
   hands over. They keep one report shape.
2. **Reviewers run from one rule.** CLAUDE.md ("Reviews") says when. A skill that starts them points there, and keeps
   the rule that a reviewer is briefed with a path and its sources, never with the author's conclusions.
3. **`decisions.md` is written by `vbench-decide` only.** `vbench-contexts` and `vbench-ontology` call it.
4. **A failing test is written by `vbench-tdd-red` only.** `vbench-at` stops at a skeleton and the stamp, and
   `vbench-security-test` hands its criteria to `vbench-tdd`.
5. **One status owner per question.** Per use case: `vbench-vcycle`. Across the product: `at_tool report`. A view:
   `vbench-status`. `vbench-test-stack` calls them and does not restate them.
6. **The fast gate is `scripts/check.sh`.** `vbench-tdd`, `vbench-tdd-refactor` and `vbench-commit` call it and do not
   name the individual commands.
7. **"Is it already there?"** `vbench-req` answers for requirements and criteria, `vbench-uc` for use cases.
8. **Diagram format is decided in `vbench-diagrams` and the diagram standard**, and the other two point there.
9. **Branch, commit and pull request rules are in `conventions.md`**, including the four-answer ask. The three skills
   point there.
10. **Security has two halves.** The reviewer reads the design before building. The tester tries the running stack after.
    A broken check becomes a criterion whose Notes start `security SEC-…`, and the `vbench-vcycle` Security row reads that.
11. **Each tool checks its own files, and only `vbench-vcycle` joins them.** `req_tool validate`, `uc_tool validate`
    and `at_tool report` stay separate.
12. **Term cards are owned by `vbench-explain`.** `vbench-walkthrough` and the other skills use the cards and record
    a term as seen; a term with no card is explained briefly and a card is offered. A card's code pointers are checked.
13. **Adopting the harness in an existing project is owned by `vbench-adopt`.** It reads and proposes; the config it writes is
    `vbench.json`, after a yes. It never changes the project's own files. The adoption states and the baseline it describes
    are not built yet, and it says so.
14. **The reviewers are started in one place:** `vbench-uc`, when a use case is written or changed. `vbench-req`, `vbench-tdd` and
    CLAUDE.md point there. `vbench-req` flags that a change touches security so the security reviewer is in the pass.
15. **The front door is `vbench-next`.** It reads the trace and names the one next step; it never runs a stamp or a freeze.
16. **A change has a tier, chosen by a person.** `tier: small` (no new object, port, role or outside system, no new flow) needs
    one combined sequence, no freeze and one review pass; anything else, and any doubt, is full.
17. **Packs.** Each role belongs to one pack: `core` (portable), `ddd`, `security`, or the `keycloak` overlay (this repo only).
    `vbench.json` `packs` says which are on; a trace row of a pack that is off is left out. `vbench-adopt` proposes `core` only.

## Known gaps against the yardstick (not built)

| Gap | Today |
|---|---|
| Test results | partly closed: with `results` in `vbench.json` (JUnit XML, `scripts/test-results.sh`) a criterion counts only when its test passed. The stack run (integration and acceptance) does not write results yet, so those criteria show "no result" |
| Problem resolution | a failing gate or a broken security check has no log and no closure |
| Review findings | nothing records that the three reviewers ran or that their findings were settled |
| Change requests | a change is traced only through the use case id |
| Release and baseline | nothing tags a release, writes notes or merges |
| Interfaces | external interfaces (Keycloak, API contracts) and quality requirements have no owner |
| Ontology checks | no lint that ids match files and links resolve; a changed object or context does not make a use case suspect |
| Regression and integration | no regression strategy, and integration is "not tracked" on the status card |
| Portability | only the tag scanner reads `id_patterns`; other id shapes (use case, requirement) and the document formats are still this repo's own. Skills are not yet packaged as an installable plugin, and `paths: null` ("this project has no such file") is not supported |
| Independence | the author and the reviewers are the same kind of model; there is no independent quality assurance owner |
| Code review | nothing reviews a code diff |

## Defects found and fixed (22 Nov 2026)

- `vbench-ontology` and `vbench-contexts` cited files that do not exist (`ontology-process.md`, `docs/domain/README.md`,
  `ontology.md`, `context-map.md`). They now point at `docs/domain/contexts/`, `ontology/` and `diagrams/`.

## Text changes made to match the rules above

Text only, so no capability moved. The ledger and its test pin what must stay.

| File | Change |
|---|---|
| `vbench-spec-challenger.md` | security points are flagged and handed to the security reviewer; the design diagram against the class diagram moved to the design reviewer |
| `vbench-security-reviewer.md` | names the tester as the live half |
| `vbench-contexts`, `vbench-ontology` | call `vbench-decide` for `decisions.md`; broken references fixed |
| `vbench-at` | stops at the skeleton and the stamp; the real failing test is written by `vbench-tdd-red` |
| `vbench-test-stack` | quotes `vbench-vcycle` for per use case counts |
| `vbench-tdd` | closes a slice with `scripts/check.sh` |
| `vbench-mermaid` | defers the format choice to `vbench-diagrams` |
| `vbench-branch`, `vbench-commit`, `vbench-pr` | already follow "How the skills ask" in `conventions.md` |
| `CLAUDE.md` ("Reviews") | adds the tester as the step after building |
