---
name: vbench-adopt
description: Bring the harness into an existing project one area at a time, like a strangler, without rewriting anything. Reads the project (stacks, tests, docs, ids, git habits, CI), shows what it found and a proposed vbench.json, then walks the adoption ladder: mark the seams, hold the line, make new work follow the V, tighten an area at a time. Use whenever the user says "adopt vbench in this project", "use this on an existing repo", "strangler", "bring this into another project", "where do we start with this codebase", "legacy", or wants the V cycle on code that already exists, even if they never say "vbench".
---

# Adopt the harness in an existing project

**Why this step:** an existing project has code, tests and habits that nobody will rewrite for a process. The way in is
to leave the old way alone and make each new piece of work follow the V, one area at a time, until the old way has
nothing left to do. That is a strangler: it grows around what exists and never stops it working.

The tool is `python3 .claude/skills/vbench-adopt/scripts/adopt_tool.py`. `discover` only reads: it writes no file.

## The ladder

| Step | What | Available today |
|---|---|---|
| 0 Observe | `discover` reports what is there and proposes a `vbench.json` | yes |
| 1 Mark the seams | name the areas, set each to `legacy`, `adopting` or `adopted` in `vbench.json` | the config is written; the trace does not read it yet |
| 2 Hold the line | record today's gaps so only new gaps fail | **not built yet** |
| 3 New work follows the V | `vbench-req`, `vbench-uc`, the reviewers, `vbench-tdd` for each new or changed thing | yes, one change at a time |
| 4 Tighten | move an area to `adopted` so its gaps fail instead of warn | **not built yet** |
| 5 Retire the old way | when every area is adopted | later |

Say which steps are available. Do not describe step 2 or 4 as working: until the trace reads the adoption states, a
gap in a legacy area is a gap, and the person should know that.

## Steps

1. **Observe.** Run `adopt_tool.py discover <root of the project>` (use `--json` if you need the data). Show the report
   as it is. If a `vbench.json` already exists, read it first and stop short of proposing a new one. It reports each id
   family with a likely role and how tests name them, branch habits, installed skills that may collide, layers with no
   test, and stacks the harness cannot scaffold (those are not gaps). The proposal holds only keys the loader accepts.
2. **Agree the seams.** Ask the person to name the areas of the code (a folder, a bounded context, a service), one at a
   time, and which one is changing now. That one becomes `adopting`; everything else stays `legacy`. Do not choose for
   them.
3. **Propose the config.** Show the proposed `vbench.json` with the areas filled in. Write it only after they say
   yes, and show it first. Never overwrite an existing one without a diff and a yes.
4. **First change.** Hand the first piece of new work to `vbench-req` then `vbench-uc`, and the three reviewers when the
   use case is written. If the change touches code with no test, write a characterisation test first: a test that
   records what the code does today and passes. It is not a RED test; do not start `vbench-tdd-red` for it.
5. **Say what is next.** Name the next step on the ladder and what it needs. Stop there.

## Boundaries
- It never moves, renames or rewrites existing code, tests or documents to fit the harness. The harness adapts through
  `vbench.json`; the project does not.
- The only file it writes is `vbench.json`, after a yes. It reads manifests and file names, not secrets, and sends nothing
  anywhere.
- It does not claim an area is adopted because it has been scanned. An area is adopted when its new work has gone
  through the V and its gaps are real checks.
- `security` is never proposed, `ddd` only with an architecture check, `test_stack` only when one framework is in use.
- Project-specific skills (the security tester, the Keycloak sign-in helper, this repo's design rules) belong to the
  project that has them; do not assume another project does.

## Hand-offs
`vbench-req`, `vbench-uc`, `vbench-at`, `vbench-tdd` for the work; `vbench-vcycle` to read the result; `vbench-explain`
for any term the person has not met.
