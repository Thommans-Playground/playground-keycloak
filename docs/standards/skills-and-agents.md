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
| Beside: knowledge transfer | training | `vbench-walkthrough` |

## Roles

"Owns" is what only this role may decide or write. "Hands off to" is where it sends what is not its job.

| Role | Owns | Does not | Hands off to |
|---|---|---|---|
| `vbench-req` | requirement and criterion rows, their ids, wording and duplicates | use case flows, objects, tests | `vbench-uc`, `vbench-at`, `vbench-ontology`, `vbench-contexts` |
| `vbench-uc` | the use case file, impact, slices, the analysis-to-design log, review stamps, freeze | requirement rows, ontology files | `vbench-req`, `vbench-at`, `vbench-ontology`, `vbench-contexts` |
| `vbench-ontology` | objects, links, rules, value sets, ports as files | use case flow, where a boundary goes, decisions | `vbench-contexts`, `vbench-decide` |
| `vbench-contexts` | the challenge of a context, aggregate, port or hexagon choice | writing objects, technical decisions | `vbench-ontology`, `vbench-decide` |
| `vbench-decide` | `docs/domain/decisions.md` and `docs/adr/`, and making a decision checked and exampled | the owner's choices (scope, people, permissions, risk) | the three reviewers, `vbench-tdd` |
| `vbench-diagrams` | which format a diagram takes | drawing | `vbench-mermaid`, `vbench-puml` |
| `vbench-mermaid` | small inline diagrams in a document | reference and per-use-case diagrams | `vbench-diagrams`, `vbench-puml` |
| `vbench-puml` | `.puml` reference and per-use-case diagrams, the A4 fit check | inline diagrams | `vbench-diagrams`, `vbench-mermaid` |
| `vbench-tdd` | one slice, test first: order, preconditions, a pause after each step, closing the slice | writing the test or the code itself | the three TDD agents, `vbench-commit` |
| `vbench-tdd-red` | the one failing test, proved to fail for the right reason | production code beyond a stub | `vbench-tdd-green` |
| `vbench-tdd-green` | the minimum code that passes, placed by ADR 0010 | editing the test | `vbench-tdd-refactor` |
| `vbench-tdd-refactor` | behaviour-preserving tidying on green | new behaviour | `vbench-tdd` |
| `vbench-at` | the criterion-to-test link report, the skeleton and the test stamp | writing the real test | `vbench-tdd-red`, `vbench-req` |
| `vbench-test-stack` | running the whole gate on a fresh stack and reporting counts | judging test quality, fixing | `vbench-vcycle`, `vbench-at` |
| `vbench-vcycle` | the per-use-case trace, as facts, from files | running tests, editing, stamping | `vbench-at`, `vbench-security-test`, `vbench-test-stack` |
| `vbench-status` | a table view of the trace | any check of its own | `vbench-vcycle` |
| `vbench-security-test` | the workflow and the check catalogue for live security tests | gating, fixing | `vbench-security-tester`, `vbench-req`, `vbench-tdd` |
| `vbench-security-tester` | probing one use case on the local stack | editing, deciding, flooding, any non-local target | `vbench-security-test` |
| `vbench-spec-challenger` | the flow, the criteria, the ids, the words and the open questions of a spec | architecture fit, security content | `vbench-design-reviewer`, `vbench-security-reviewer` |
| `vbench-design-reviewer` | the design against the architecture rules, the design diagram against the class diagram, the change log | spec wording, security content | `vbench-spec-challenger`, `vbench-security-reviewer` |
| `vbench-security-reviewer` | all security content on paper, from the checklists and the overlay | live testing | `vbench-security-tester` |
| `vbench-branch` | branch names and starting a branch | pushing, deleting | `vbench-commit` |
| `vbench-commit` | splitting changes and commit messages | pushing, amending | `vbench-pr` |
| `vbench-pr` | the pull request title, description and honest checklist | merging, approving | `vbench-branch`, `vbench-commit` |
| `vbench-walkthrough` | teaching existing code, one learner at a time | editing code, reading the learner's notes | `vbench-tdd` |

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

## Known gaps against the yardstick (not built)

| Gap | Today |
|---|---|
| Test results | the trace says a test exists, not that it passed; nothing stores pass or fail per criterion |
| Problem resolution | a failing gate or a broken security check has no log and no closure |
| Review findings | nothing records that the three reviewers ran or that their findings were settled |
| Change requests | a change is traced only through the use case id |
| Release and baseline | nothing tags a release, writes notes or merges |
| Interfaces | external interfaces (Keycloak, API contracts) and quality requirements have no owner |
| Ontology checks | no lint that ids match files and links resolve; a changed object or context does not make a use case suspect |
| Regression and integration | no regression strategy, and integration is "not tracked" on the status card |
| Code review | nothing reviews a code diff |

## Known defects

- `vbench-ontology` cites `docs/domain/ontology-process.md`, and `vbench-contexts` cites `docs/domain/README.md`,
  `ontology.md` and `context-map.md`. None of these exist in `docs/domain/`.

## Changes the owners above still need in the skill files (not made yet)

These are text edits only, so no capability moves. Each is one or two lines in the named file.

| File | Edit |
|---|---|
| `vbench-spec-challenger.md` | drop the class-diagram and port check (it moves to the design reviewer); hand abuse cases to the security reviewer |
| `vbench-security-reviewer.md` | name the tester as the live half |
| `vbench-security-tester.md` | already points back; keep |
| `vbench-contexts`, `vbench-ontology` | call `vbench-decide` for `decisions.md`; fix the broken references |
| `vbench-at` | stop at the skeleton and the stamp, and hand the failing test to `vbench-tdd-red` |
| `vbench-test-stack` | call `vbench-vcycle` and `at_tool report` for counts |
| `vbench-tdd` | call `scripts/check.sh` to close a slice |
| `vbench-mermaid` | point to `vbench-diagrams` for the format choice |
| `vbench-branch`, `vbench-commit`, `vbench-pr` | done already: each follows "How the skills ask" in `conventions.md` |
| `CLAUDE.md` ("Reviews") | add the tester as the step after building |
