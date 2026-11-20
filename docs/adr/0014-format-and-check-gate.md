# 0014 One check script, and formatting that happens by itself

- Status: accepted
- Date: 2026-11-20
- Decided by: the agent (technical), at the owner's request

## Context
Code style depended on each person (and agent) remembering to format. CI ran its checks as separate steps in `ci.yml`, so a laptop and CI could disagree about what "green" means.

## Decision
- **Tools:** ruff for the API (format, and lint with E, F, I, UP, B; line length 120, set in `apps/api/pyproject.toml`), prettier for the web (`apps/web/.prettierrc.json`, CSS and Markdown left alone), and the existing ESLint.
- **`scripts/check.sh` is the one definition of green.** `fix` formats everything, no argument runs the fast gate (format and lint checks, types, unit tests, requirement and test-tag checks), `full` adds the fresh stack through `scripts/test-stack.sh`. The CI jobs call its modes (`api`, `web`, `trace`), so CI and a laptop cannot drift apart.
- **Three layers, each catching what the one before it misses:** a Claude Code `PostToolUse` hook (`.claude/settings.json`, `scripts/hooks/format-file.sh`) formats the one file the agent just wrote; a git `pre-commit` hook (`lefthook.yml`, installed once with `lefthook install`) fixes the staged files for everyone; CI fails an unformatted push. Only CI cannot be skipped.
- The hooks never fail a tool call or block a commit on a tool error. The check script and CI are the gate.

## Consequences
One commit reformats the existing code. Add it to `.git-blame-ignore-revs` once it has a hash. A new tool or check is added to `scripts/check.sh`, not as a loose CI step. The lefthook install is a manual step for each person.

## Links
ADR 0007 (CI on GitHub Actions); `scripts/check.sh`; `.github/workflows/ci.yml`.
