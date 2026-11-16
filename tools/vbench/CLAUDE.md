# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

VBenchAI: a harness that keeps AI-assisted teams on the V-cycle. One repo ships three things that must stay
in lockstep (one version tag covers all three):

- `src/vbench/`: the stdlib-only Python CLI (`init`, `check`, `new uc`, `status`).
- `plugin/`: the Claude Code plugin (skills in `plugin/skills/*/SKILL.md`, subagents in `plugin/agents/`).
  The marketplace manifest is `.claude-plugin/marketplace.json` at the repo root; the plugin manifest is
  `plugin/.claude-plugin/plugin.json`.
- `src/vbench/templates/`: what `vbench init` copies into a user's project (config, the docs tree modelled on
  `../aiaas-mk3/docs`, use-case template, `CONTRIBUTING.md`, CI for GitHub and GitLab). Everything under
  `templates/docs/` is copied as-is, so a new template file needs a row in `templates/docs/README.md`
  (`test_docs_map_links_every_top_level_document`).

`docs/00-pitch.md` is the original pitch (partly superseded; the README states the current scope). The
method was extracted from a sibling project, `../aiaas-mk3`, whose `docs/tools/check_*.py` scripts are the
origin of `src/vbench/domain/checks.py` and whose `.claude/skills/v-*` are the origin of the plugin skills.

## Commands

```bash
uv venv && uv pip install -e ".[dev]"      # first time
.venv/bin/python -m pytest                  # all tests
.venv/bin/ruff check . && .venv/bin/ruff format --check .   # lint and format (one tool; config in pyproject.toml)
VBENCH_STACK_E2E=1 .venv/bin/python -m pytest tests/test_stack.py   # also generate a project and run its real gates (network)
.venv/bin/python -m pytest tests/test_vbench.py -k rung   # one test
.venv/bin/vbench check                      # run the gates on a project that has .vbench/config.toml
claude plugin validate .                    # marketplace manifest
claude plugin validate ./plugin             # plugin (skills, agents, manifest)
uv build --wheel                            # verify templates are packaged (see src/vbench/templates in the wheel)
```

## The dashboard (`src/vbench/ui/`): optional, not in the CLI package

The CLI and the skills are version 1. Everything in this section (dashboard, write path, agents, `vbench mcp`, `serve`, `export`) is
an optional layer: those three commands work but are hidden from `--help`, and no verdict depends on them. User docs: `docs/dashboard.md`.

```bash
cd src/vbench/ui && npm install      # first time (only needed to work on the UI itself)
npm run typecheck && npm run build   # tsc strict, then vite build -> dist/
npm run dev                          # Vite on 127.0.0.1:5173, proxying /api and /plantuml to `vbench serve` (port 3000)
PROJECT=$PWD/examples/notes-app docker compose up --build   # the full stack in Docker (app + PlantUML renderer), project mounted read-only
```

The dashboard is not part of the CLI package: the wheel carries only the templates (package-data in `pyproject.toml`), and
the UI source stays in the repo. `docker-compose.yml` and the root `Dockerfile` (a Node stage builds the UI, then `vbench serve`
serves it on a Python image) are how it is run; the `write` compose profile mounts the project read-write. There is no
`vbench ui` command. Packaging gotchas: delete `src/vbench.egg-info` and `build/` before `uv build` (setuptools reuses a stale
`SOURCES.txt`), and keep `namespaces = false` in `pyproject.toml` (otherwise stray `.py` files in `node_modules` are swept in).

`domain/vview.py` is the logical view of the V: it places every requirement, context, domain model, diagram, task, code
file and test on one of nine phases, each item naming its use cases (tests are indexed per function with `ast` for
Python, per file otherwise; tests that name no use case or level are `unplaced`). `export_state` carries it as `v`; the UI
only draws it. `tests/test_vview.py` keeps the UI's phase list in step with `PHASES`.

The UI is a second driving adapter's front end: `vbench serve` (`adapters/http_server.py`) exposes `app/export.py`'s
state as JSON, plus read-only file and diagram endpoints, and serves the built UI. The UI computes nothing; any rule it
seems to need belongs in `domain/` and comes out through `export_state`. The look follows `src/vbench/ui/DESIGN.md` (the AGIL
Secure Shield console tokens, mapped onto shadcn variables in `src/vbench/ui/src/index.css`, without the AGIL brand assets).
`examples/notes-app` is the worked example and is pinned by `tests/test_example.py`.

**The write path** (`vbench serve --write`). Two kinds are written in the specs rather than the doc and can only be added: a *criterion* (`_plan_criterion`: a row in its use case's AC table, filling a scaffold `TBD` row when there is one) and a *use case* (`_plan_use_case`: `domain/scaffold.py:spec_text`, the same file `vbench new uc` writes, with the Realises row filled; `app/changes.py` passes the spec template in). `domain/mdtable.py` edits one row of a markdown table and leaves the rest
untouched (cells are one line, `|` is escaped, columns are found by header text). `domain/changes.py` plans a change to
the requirements doc (problem, request, functional or quality requirement; add, update or delete): it validates fields
and links, builds the new text, a diff and the *blast radius* from `domain/trace.py` (the graph problem <- request <-
requirement <- use case <- criterion <- test, derived and never stored), and cascades link clean-ups inside the doc
automatically while only flagging specs, criteria and tests for review. `app/changes.py` is the use cases: `preview` writes
nothing, `apply` re-plans and writes only if the digest still matches (else `StaleError`, 409), then syncs and re-runs the
gates, and `commit` takes documentation files only (`Committer` port, `GitRepo.commit`). `adapters/http_server.py` adds
`GET /api/session` and three POSTs behind a token, an `Origin` check, a 64 KB limit and a default-branch guard; a server
started without a `Writer` still answers 405 to every POST. Actions are one three-dots menu (`components/ActionsMenu.tsx` on the shadcn Base UI dropdown, `components/ui/dropdown-menu.tsx`), whose items are data in `lib/actions.ts`. The UI side is `components/change/` (the sheet that walks
form, review, done), `lib/changes.ts` (forms and words, pure) and `lib/write.ts`; `ChangeButton` renders nothing unless
the server was started with `--write`. `vbench mcp` (`adapters/mcp_server.py`: the protocol only, JSON-RPC lines on stdio, nothing but protocol on stdout; `app/mcp_tools.py`: the catalogue of `ToolSpec`s, which reuses the chat read tools and the change operations) lets an agent use the same operations; apply and commit exist only with `--write` and are marked destructive. The root `Dockerfile` packages the CLI and MCP server (git inside, project mounted at `/project`; the project's own toolchain is not in it). The agent is a port (`ports.Agent`, `structured(system, user, schema)`), with `adapters/claude.py` behind it (the official
SDK, the optional `vbench[agent]` extra, imported only when asked; `claude-opus-5-5`, effort `medium`, structured output;
every failure becomes `AgentError`). Its first use is `app/assist.py:check_overlap` (`POST /api/assist/overlap`): the pure
parts are `domain/overlap.py` (what to compare: the entries the new one links to, then the most alike; a word-overlap
baseline that always runs; the prompt, which treats entries as JSON data; and `parse_answer`, which lets the agent name only
entries it was shown). The agent advises and never applies; any failure leaves the word check with the reason. A later
agent calls the same `app/changes.py` operations as tools and never applies.

The look is the AGIL palette laid out by Apple's HIG (system font, named text styles, light and dark, segmented controls,
translucent bars; see `DESIGN.md`). Three rules for new screens: a name is never shown alone (every `VItem` carries a
`description`, criteria their text), pages are tables or sheets first with diagrams behind `Visualise`, and every
drill-down has a pinned breadcrumb whose last crumb carries a `switch` menu (`lib/crumbs.ts`). Requirements open as a
sheet: `app/export.py:_sheet` joins `domain/requirements_doc.py` (the doc's tables, read by header name, and each
criterion's text) with the V items, so the UI computes nothing. Clicking anything opens a record (`components/Record.tsx`, `components/records/`): a header card with facts, then sections of grouped tables, with a `Scrollspy` rail on a wide window (the same record is the pane in List and detail). The breadcrumb is the lineage of the page (`lib/lineage.ts`: problem, request, requirement, use case, criterion, test, the last four layers, with the other parents in each crumb's menu). The lookups that join a requirement to its origin, derived requirements and tests are in `lib/records.ts`. Use colour tokens, never hex, so dark mode holds (light is the default; the choice is in Settings, under the profile menu). Keep
TanStack table inputs memoised.

## The stack standard

`vbench init --stack python-fastapi` (the default) scaffolds `templates/stacks/python-fastapi/`: the app skeleton, a
pyproject for uv, Ruff and mypy, compose with PostgreSQL, CI jobs, `04-technology-stack.md` and pre-filled accepted ADRs
(which replace the generic ADR file). `--stack none` is the harness alone. The skeleton is written only when there is no
`pyproject.toml`; `{{PACKAGE}}`, `{{NAME}}`, `{{DIST}}` are rendered, and a name is made safe for TOML and Python
(`domain/stack.py`). The architecture rule is generated, not hand-kept: `domain/stack.py:importlinter_text` derives
`.importlinter` from the contexts under `src/<package>`, and `vbench new context` creates the package and rewrites it.
Stack-specific changes belong in the stack's templates, `domain/stack.py` and `app/init.py`, with a test in
`tests/test_stack.py`; the gates stay stack-independent. Ruff replaced Black on purpose (it lints and formats). The
skills' guidance for the stack is `plugin/skills/v-2-design/references/stack-python-fastapi.md`.

Not applied to vbench itself: it is stdlib-only (its dashboard server is `http.server`, its UI is Vite, not Next.js, because
it is a static page served by Python), it keeps no database, and it targets Python 3.11+. A FastAPI dashboard server is
planned as the optional `vbench[ui]` extra, behind the same adapter interface; until then the stdlib server stays.

## Architecture notes that need more than one file to see

- **Hexagonal layout.** `domain/` (config values, id rules, the three verdicts, status derivation) is pure; it
  reaches the project only through the `Workspace` port in `ports.py`. `app/` holds one use case per command
  (`init`, `check`, `new`, `status`, `update`) and depends on the domain and the ports. `adapters/` implements
  the ports (filesystem, TOML, package templates, git, uv, the PEP 610 install record); `cli.py` is the
  driving adapter and the only place adapters are wired in. `tests/test_architecture.py` fails if `domain/` or
  `app/` imports an adapter, `cli`, or an I/O module. A new capability = a port + an adapter + a use case; tests
  pass fakes through `cli.main(argv, Adapters(...))`.
- **Config-driven checks.** `adapters/toml_config.py` reads `.vbench/config.toml` into `domain/config.py`'s `Config`; `domain/checks.py` takes a `Config` and never
  hard-codes a path, id shape or marker. Anything project-specific belongs in config, not in the checks.
- **Machine-readable output is one shape.** `status --json`, `check --json` and `next --json` (and the MCP tools `status`,
  `check`, `next_step`) come from `app/status.py:status_json` / `results_json`, so skills read fields and never parse the
  CLI's tables. Do not add a skill script that re-parses text output; add a field.
- **Writes are narrow.** `FsWorkspace` refuses any path that resolves outside the project and writes through a temp file
  and a rename; `apply_change` puts files back if a write fails; `commit_changes` takes only files the same session's
  `apply_change` wrote (the `written` set the composition root passes in) and only `domain/paths.py:docs_path` files;
  `branch_block` refuses the default branch and a detached HEAD. One rule each, shared by the HTTP server and MCP.
- **Tags must stand on a real test (Python).** `domain/pytests.py` reads test files with `ast`: a `Verifies` clause counts only
  in a docstring with a test behind it, and the AC marker only on a `test*` function that is not skipped/xfail and asserts
  something that can fail (not `assert True`, not literals only). Other languages and unparseable Python keep the text
  match. It is a floor, not a judgement of quality; `tests/test_redteam.py` pins the cheap bypasses.
- **Styling lives in the driving adapter.** `adapters/term.py` maps roles (`ok`, `fail`, `command`, `planned`, ...) to ANSI
  and decides when it is on (a terminal, `NO_COLOR`, `FORCE_COLOR`, `--color`); `cli.py` creates one `Style` as `args.style`.
  Printers ask for a role and never write an escape code, `domain/` and `app/` return plain text, and `--json` is never
  styled. Meaning must not depend on style alone (`tests/test_term.py` pins that stripping the codes gives the plain output).
- **Verdicts are deterministic.** The gates parse files with regexes; no LLM sits in any pass/fail path. Keep
  it that way. The checks prove a link *exists*, never that a test is good.
- **Tag conventions are the contract** between code, tests, specs and the checks: `Realises UC-…` in
  production code, `Verifies UC-… · <rung> rung.` plus an AC marker in tests, `**AC-…**` rows in spec tables.
  Changing one means changing `domain/checks.py`, the templates, the skills and the tests together.
- **Short names are pointers.** `plugin/skills/{req,design,code,verify,ship,fix,status}` hold no workflow: each tells Claude to
  follow its long skill (`v-1-requirements`, ...) and shares its `argument-hint`. Edit the long one only; `tests/test_skills.py`
  keeps the pair in step and `/vbench:help` listing every user-invocable skill. CLI short forms (`c`, `st`, `n`) are
  `cli.ALIASES`, normalised before dispatch and left out of `--help`.
- **Skill layout.** `plugin/skills/<name>/SKILL.md` is the workflow (kept short, ≤150 lines); heavy material lives
  in `references/` and deterministic steps in `scripts/` (stdlib Python that shells out to `vbench`; paths in
  SKILL.md are relative to the skill's directory). `tests/test_skills.py` fails on a bad frontmatter, a dead or
  unlinked reference/script, and runs each script against a real temp repo.
- **Use-case order is derived.** The only authored fact is a spec's `**Depends on**` header row
  (`domain/graph.py`). Waves, what a use case enables, blockers and the single next step (`vbench next`,
  `domain/next.py`) are all computed from it plus the tags and tests; `vbench check links` rejects dangling ids,
  self-links and cycles. A use case's *stage* (requirements, design, code, rung, verify) comes from its files
  (`domain/status.py`); an AC row still marked `TBD` counts as unwritten.
- **Diagrams.** `vbench check diagrams` (`domain/checks.py:check_diagrams`) enforces `<spec-stem>-(sequence|class|state)[.n].puml`,
  a link in the spec's `Diagrams` row, `@startuml`/`@enduml`, and the set the `Rigor` tier requires once a task plan
  exists (standard: sequence; full: + class; plus state whenever the spec's `Lifecycle` row is `yes`, and the full tier needs that
  row decided, `yes` or `none`, since "needed" cannot be judged by a regex; see `required_kinds` and `lifecycle_undecided`). A missing required diagram keeps a use case at the `design` stage.
  `_`-prefixed `.puml` files are shared includes. System level (`domain/contexts.py`, `usecase_map.py`): `08-usecase-diagrams.puml`
  is generated by `app/sync.py` from spec headers (structure only, never progress) and compared byte for byte by the
  check; `09-context-ddd.puml` and `NN-<context>-ddd.puml` are authored (`vbench new context[-map]`), required at the
  full tier / once two contexts have designed use cases, and never overwritten. PlantUML is the format of record; Mermaid is for explanations
  inside docs and READMEs.
- **Steps.** A sequence diagram opts in by giving each message a step id (`STP-<area>-<nnn>`, `vbench id step --area A`;
  `domain/steps.py` parses, `domain/checks.py:check_steps` judges). A task row names the steps it builds; code says
  `Realises UC-… · STP-…` on the line that does the work; a test says `Verifies UC-… · STP-… · <rung> rung.` and counts only
  with a real test behind it (the same `pytests.py` rule). From then on every step needs a task, and once the use case has
  code, a tag and a test; `(planned)` in the message exempts one. Ids are unique across use cases and append-only. A diagram
  with no step ids is not checked (light tier stays as it was). `vbench trace UC-…` reads the chain back (`app/trace.py`),
  derived from the tags and never stored; `vbench next --ready` (`domain/next.py:ready_steps`) lists every unblocked use case.
- **Vocabulary and ontology.** The requirements doc's vocabulary table is read as data (`domain/vocabulary.py`: a term is named by
  its words, no id). `check vocabulary` fails when a diagram declares a name that uses a word a term lists under *Not to be
  confused with* (unless that word is itself a term); it never demands a term for every name. `domain/ontology.py` derives the
  ontology from the specs, tags and vocabulary: a fixed method layer (classes and relations) plus this project's individuals,
  rendered as Turtle and RDF/XML (both OWL 2), JSON-LD and YAML with no library (`vbench ontology [--format] [--write]`,
  `app/ontology.py`). Files under `[ontology]` are generated, never edited; `check ontology` compares the ones that exist with a
  fresh render and `vbench sync` refreshes them. Local names are percent-encoded so a test id is a valid Turtle name. The three
  RDF formats were checked triple-for-triple with rdflib and an OWL RL closure (a one-off, not a test dependency).
- **Generated blocks.** `domain/docsgen.py` owns the `<!-- vbench:begin NAME -->` blocks in the requirements and backlog
  docs (`dependencies`, `waves`, `coverage`, `fr-map`); `app/sync.py` rewrites only inside them and `check docs` compares
  each with a fresh render. The templates ship each block holding exactly the empty render, so a fresh project passes
  (`test_fresh_project_passes_all_gates`). Add a block = a name in `BLOCKS`, a branch in `render_block`, a marker in a
  template, and a test.
- **Learning on demand.** A newcomer needs three things (`/vbench:next`, `vbench status`, the dashboard); everything
  else is introduced when first needed (Levels 0 to 2 in `templates/docs/00-getting-started.md`). Keep it that way:
  every skill opens with a one-line `**Why this step:**` (`test_every_skill_says_why_the_step_exists`),
  `vbench next` prints a plain-language `for:` line (`domain/next.py:PURPOSE`), a failing check points to
  `00-glossary.md`, and the glossary must mention every gate (`test_the_glossary_defines_every_gate...`). Add a gate or
  a stage and you add its glossary line and its purpose line in the same change.
- **Discovery before requirements.** `/vbench:discovery` saves a draft brief (`vbench new discovery`); the human sets
  `Status: approved`; `vbench next` routes an empty project through it (`domain/briefs.py`). The brief's Becomes ids
  are not checked yet.
- **Skills hold no state.** Progress is derived from specs, tags and `vbench check`. Do not add state files.
- **`vbench commit` builds the subject the gate checks.** `domain/commits.py` (pure: branch parsing, summary tidy, `build_subject`,
  `infer_type`) and `app/commit.py` (`plan_commit`, `make_commit`) share `Config.commit_re` with `check_commits`, so a generated
  subject cannot fail the gate (a test pins it). A commit is **one finished TDD task**, not a phase: code types (feat, fix,
  refactor, perf) are refused while the task's enforced criteria lack a test or a gate fails *for this work* (a failure naming the use
  case or a staged file; other use cases' open criteria are only warned about), and then run `[commands] test` through the `Runner` port (`adapters/shell.py`; a red run refuses, the commit gets a
  `Tested:` trailer); `--green` (self-attested, trailer says so) is only the fallback when no test command is set. Ambiguity (two tasks or use cases staged) is `AmbiguousError`, exit 2; a refusal is `RefusedError`, exit 1.
  It commits only the index (`Repo.staged`, `Committer.commit_staged`), never on the default branch or a detached HEAD.
- **Git conventions are checked, not just written.** `vbench check commits` (`domain/checks.py:check_commits`)
  lints `base..HEAD` subjects (Conventional Commits, `<type>(<UC>[/<TSK>])[!]: …`) and the branch name, and requires the cited spec and
  task row to exist. It is explicit, not part of `all`, because it needs git. The branching model is trunk-based (short-lived
  `<type>/<slug>` branches, one PR per use case, rebase-and-merge, `vX.Y.Z` tags), written into the `CONTRIBUTING.md` template;
  vbench cannot set repository settings, so `vbench doctor` (`app/doctor.py`) checks what it can see: behind the base, older
  than `branch_max_days`, badly named, dead worktrees. Task rows are `**TSK-<area>-<nnn>**` rows
  in the spec; their closure is derived from their ACs, never stored.
- **Ids are three parts and append-only.** Every id is `<KIND>-<SCOPE>-<NNN>` (`domain/ids.py`): `STK-REQ-001`,
  `REQ-FR-001`, `REQ-NFR-001`, `UC-A-001`, `AC-A-001`, `TSK-A-001`, `EPC-A-001`, `ADR-DEC-001`. Criteria and tasks are
  numbered per area and belong to the spec that declares them (never inferred from the id). `vbench new uc` and
  `vbench id <kind>` skip any number already used. Artifacts that are found rather than written (contexts, models,
  diagrams, code files, tests) get `SYS-CTX-001`, `ARC-DOM-001`, `MOD-SEQ-001`, `COD-SRC-001`, `TST-UNT-001` from the
  registry in `docs/00-id-registry.md` (`domain/registry.py`): a generated block that `app/sync.py` only appends to and
  `check docs` verifies; a rename is a new alias and a new id. Template placeholders use `nnn` so they never match an
  id pattern. `export_state` carries each item's id as `ref`.
- **Templates must pass their own gates.** `vbench init` into an empty dir followed by `vbench check` must
  exit 0 (`test_fresh_project_passes_all_gates`). Example paths in template docs must either exist or avoid
  the literal `docs/….md` form.
