# Capability ledger

What the skills and agents can do today, so a tidy-up cannot lose any of it quietly. `.claude/skills/_vbench/test_scope.py`
checks the two tables below against the files: a script command that disappears from its `--help`, or a guard phrase
that disappears from its file, fails the test. To remove a capability on purpose, remove its row here in the same
commit and say why in the message. See [the map](skills-and-agents.md).

Inventory taken on 22 Nov 2026 by four read-only reviewers and checked against the files. The prose-only behaviours
(the questions each skill must ask, the order of steps) are not machine-checked; they are listed at the end.

## Script commands

A command or flag that must stay in the script's `--help`.

| Skill | Script | Command or flag |
|---|---|---|
| vbench-req | req_tool.py | search |
| vbench-req | req_tool.py | init |
| vbench-req | req_tool.py | convert |
| vbench-req | req_tool.py | next-ids |
| vbench-req | req_tool.py | validate |
| vbench-req | req_tool.py | append |
| vbench-req | req_tool.py | update |
| vbench-req | req_tool.py | duplicates |
| vbench-req | req_tool.py | --dry-run |
| vbench-uc | uc_tool.py | search |
| vbench-uc | uc_tool.py | impact |
| vbench-uc | uc_tool.py | coverage |
| vbench-uc | uc_tool.py | next-id |
| vbench-uc | uc_tool.py | validate |
| vbench-uc | uc_tool.py | create |
| vbench-uc | uc_tool.py | check-upstream |
| vbench-uc | uc_tool.py | freeze |
| vbench-uc | uc_tool.py | trace |
| vbench-uc | uc_tool.py | sync |
| vbench-uc | uc_tool.py | stamp |
| vbench-uc | uc_tool.py | diagram |
| vbench-at | at_tool.py | report |
| vbench-at | at_tool.py | show |
| vbench-at | at_tool.py | skeleton |
| vbench-at | at_tool.py | stamp |
| vbench-vcycle | vcycle.py | --all |
| vbench-vcycle | vcycle.py | --strict |
| vbench-vcycle | vcycle.py | --json |

## Guards that must stay

A phrase that must stay in its file, case ignored. Each is a refusal, a limit or a rule another part depends on.

| File | Phrase | Why it matters |
|---|---|---|
| .claude/skills/vbench-test-stack/SKILL.md | down -v | never wipes the development stack's data |
| .claude/skills/vbench-security-test/scripts/session.sh | refused | the sign-in helper refuses any non-local address |
| .claude/skills/vbench-security-test/scripts/session.sh | localhost | local only |
| .claude/agents/vbench-security-tester.md | Local only | the tester never leaves this machine |
| .claude/agents/vbench-security-tester.md | No flooding | no denial of service, no brute force |
| .claude/agents/vbench-security-tester.md | Advisory only | the tester never gates or edits |
| .claude/agents/vbench-spec-challenger.md | Advisory only | reviewers never edit |
| .claude/agents/vbench-design-reviewer.md | Advisory only | reviewers never edit |
| .claude/agents/vbench-security-reviewer.md | Advisory only | reviewers never edit |
| .claude/skills/vbench-uc/SKILL.md | retired | a retired use case id is never reused |
| .claude/skills/vbench-uc/SKILL.md | freeze | a frozen analysis revision cannot be edited |
| .claude/skills/vbench-uc/SKILL.md | stamp | review stamps are an owner's act |
| .claude/skills/vbench-at/SKILL.md | stamp | a test stamp is an owner's act, never to clear a warning |
| .claude/skills/vbench-vcycle/SKILL.md | never in bulk | stamps and freezes are not used to clear warnings |
| .claude/skills/vbench-vcycle/SKILL.md | exists | "exists" is not "passes" |
| .claude/skills/vbench-vcycle/SKILL.md | Security | the Security row and its not-probed hint |
| .claude/skills/vbench-walkthrough/SKILL.md | Obsidian | the learner's notes are never read |
| .claude/skills/vbench-walkthrough/SKILL.md | .learning/progress.md | the only file it writes |
| .claude/skills/vbench-pr/SKILL.md | never merge | a pull request skill does not merge |
| .claude/skills/vbench-commit/SKILL.md | git add -A | files are staged by name |
| .claude/skills/vbench-branch/SKILL.md | switch -C | a branch is never moved by force |
| .claude/agents/vbench-tdd-red.md | _test | the test database guard |
| .claude/agents/vbench-tdd-red.md | NotImplementedError | the stub rule |
| .claude/agents/vbench-tdd-green.md | never edit the test | green never edits the test |
| .claude/agents/vbench-tdd-green.md | Realises | the production tag |
| .claude/skills/vbench-decide/SKILL.md | GO | the readiness check |
| .claude/skills/vbench-req/SKILL.md | never edit | requirement files are written only by the tool |
| .claude/skills/vbench-security-test/references/wstg-checks.md | SEC-CONF-1 | the check ids the Security row and the Notes convention use |

## Prose-only behaviours (read, not checked)

- **Asking:** the four answers (Accept, Change it, Reject, I'll do it myself) in `vbench-branch`, `vbench-commit`,
  `vbench-pr`, `vbench-tdd`, `vbench-req` and `vbench-uc`; the question banks in `vbench-req`, `vbench-uc` and
  `vbench-at` under `references/questions.md`; one question at a time in `vbench-contexts` and `vbench-decide`.
- **Reviews before building:** run the three reviewers together, brief each with a path and its sources only, skip only
  for a change that touches no flow, criterion, diagram or decision, and say so.
- **`vbench-decide`:** the four phases, no code before the last, the comprehension check, the predicted file list
  compared with `git diff --stat`, and the three-question finish.
- **`vbench-tdd`:** a green baseline and a feature branch first, the pause after each step, and the fallback when the
  agents are not loaded.
- **`vbench-walkthrough`:** predict before reveal, the hint ladder, spaced questions, and the weekly and monthly modes.
- **Test-stack failure reading:** the guide to ports, service logs, `Secure` cookies and shared state.
