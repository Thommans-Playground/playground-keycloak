---
name: v-4-verify
description: V-model step 4 (right arm). Independently re-verify a UC rung by rung in ascending order (unit, integration, system, acceptance) and audit the quality of its tests. Read-only.
disable-model-invocation: true
argument-hint: <UC-id | all> [unit|integration|system|acceptance|all]
---

# /vbench:v-4-verify: the right arm

**Why this step:** a second, independent look catches what the author has stopped seeing.

Read-only: report, never edit. Input: `$ARGUMENTS` (a UC id, or `all` = the UCs the branch touches, from `python3 scripts/branch_ucs.py`;
rung defaults to `all`). Paths to `scripts/` and `references/` are relative to this skill's directory.

`/vbench:v-3-code` wrote the tests test-first. This step is the independent second look: a fresh run of every
rung plus an audit of whether the tests deserve trust. Do not rely on the earlier run's claims.

## Ascent order
Run **unit → integration → system → acceptance**. A rung is not trusted until the one below it passes: on the
first failing rung, stop, report it as Blocking and mark higher rungs `not run`. A rung with nothing planned
is `not designed` (fine for light-tier UCs), not a failure.

| Rung | Proves | Run |
|---|---|---|
| **unit** | Aggregates, value objects and services behave; code is well formed | tests tagged `· unit rung.`; the `lint` and `types` commands |
| **integration** | Boundaries and adapters hold | the `boundaries` command; adapter and public-interface tests |
| **system** | Cross-context and pipeline behaviour | tests tagged `· system rung.` |
| **acceptance** | The ACs are true | the AC → test matrix; the gates; drift review; a real run |

`all` also runs the full `test` command. `python3 ../v-3-code/scripts/run_gates.py` runs `test`, `lint`, `types`,
`boundaries` and `vbench check` in one call.

## Acceptance rung detail
1. **Traceability.** Run the `vbench-trace-checker` subagent (or `vbench check`). Failures are must-fix.
2. **AC → test matrix.** `vbench check acs --matrix`; for each AC report the marked test and its result:
   `pass` / `fail` / `skipped (scaffold)` / `no test`.
3. **Tasks.** `vbench status <UC>` shows tasks closed / declared. Report any task row that names no AC, an AC
   no task closes, or a commit citing a task the spec lacks (`vbench check commits`).
4. **Drift review** (include the PlantUML diagrams against the code: participants, states and transitions that the
   code lacks or omits; the context's domain model against its aggregates; the context map against actual imports
   between contexts), with file:line: spec flows with no code path or test; code behaviour (endpoints, statuses,
   error cases) absent from the spec; Maturity ahead of or behind reality; schema changes without a migration
   note; ports or patterns in the spec that the code lacks, or vice versa; domain terms in code, tests or ACs
   that differ from the glossary.
5. **Real behaviour.** For UI or API changes, offer to run the app and exercise the main flow. Passing tests
   alone do not show it works.

## Test-quality audit (every rung)
Apply `references/test-quality-audit.md` to the UC's tests: it lists the findings to flag (with `file:line`),
why each matters and its severity, and the mutation thought experiment for AC tests.

## Output
Per UC: a rung table (rung · planned · ran · result), the AC matrix, then the test-quality findings. Then
**Blocking** (failures, dangling refs, layering) and **Should fix** (gaps, drift, weak tests). If clean, say so
in one line. A Should-fix becomes a task row, a new use case or a `99-problems` entry, never a silent fix.

## Connections
- Reads: specs, code, tests, `vbench check` output.
- Writes: nothing.
- Back-edges: `/vbench:v-3-code` (gaps, weak tests), `/vbench:v-2-design` (design was wrong),
  `/vbench:v-1-requirements` (an AC is wrong or untestable).
- Next: `/vbench:v-5-ship` when clean.
