---
name: vbench-decide
description: Make a structural or technical decision the way a team passes it down, so that people and agents can follow it without asking. Writes the decision down (an ADR or a decisions.md entry), adds a check that fails when it is broken, and leaves an example to copy. Use whenever the user or an agent is about to choose a folder layout, a pattern, a naming rule, a boundary, a library or any rule others must follow, says "let's standardise", "what should the convention be", "how do we make sure everyone does this", "add this as a rule", "record this decision", or finishes a refactor that changed how things are built, even if they never say "vbench".
---

# vbench-decide

A rule that lives only in someone's head is forgotten. A rule that is written down, checked by a test and shown by an example is followed, by new people and by agents alike. This skill makes sure every decision gets all three.

## Who decides what

| Kind of decision | Who | Where it goes |
|---|---|---|
| Scope, people, who may do what, accepted risk | **The owner.** Ask, never decide for them. | `docs/domain/decisions.md`, and the checklist's "Accepted for now" list for an accepted risk |
| How it is built: layout, pattern, naming, library, boundary | **The agent or the architect.** Decide, then record. | `docs/adr/` (see `docs/adr/README.md`) |

If a decision has both parts, split it. Decide the technical part, put the owner's part to the owner, and say in the ADR which questions are still open. Do not let an open owner question block the technical part when the two can be separated.

## Steps

1. **State the decision in one sentence.** If you cannot, it is not ready.
2. **Look before you invent.** Is there a well known pattern that fits (ports and adapters, unit of work, composition root, shared kernel, anti-corruption layer, deny by default)? Follow it and name it in the ADR. Say why only where the project differs. A student reading the ADR should be able to look the pattern up.
3. **Check what exists.** Read `docs/adr/`, `docs/domain/decisions.md` and `CLAUDE.md`. A new decision never edits an old ADR's meaning. It extends or supersedes it by number.
4. **Split the owner's part from the technical part** (table above).
5. **Review it when it touches a flow, a boundary, a requirement or a decision.** Run `vbench-design-reviewer`, `vbench-spec-challenger` and `vbench-security-reviewer` together, read-only, before building (CLAUDE.md, "Reviews"). Treat their output as advice, not as approval.
6. **Write the ADR.** `docs/adr/NNNN-short-title.md` from `docs/adr/0000-template.md`: context in two or three sentences, the decision in the present tense, the consequences with their cost, and what was left out and why. Number it, never reuse a number.
7. **Make it checked.** Add or extend a test that fails when the rule is broken, and make the failure message say why (see `apps/api/tests/test_architecture.py`). Write the failing test first and watch it fail. If the rule cannot be tested, say so in the ADR and name who checks it.
8. **Leave an example.** The first thing built the new way is the template. Point to it from the ADR and from `docs/GETTING-STARTED.md`.
9. **Tell the people and the agents.** Update `CLAUDE.md` where it describes the area, and the agents or skills that mention the old way (`grep -rn` the old path or name under `.claude/`). An agent has no hallway conversation: if it is not written there, it will not know.
10. **Check the three questions before you stop.**
    - Is it written down?
    - Does a test fail if someone breaks it?
    - Is there an example to copy?

    If any answer is no, the decision is not finished. Say which one, and why.

## What this skill does not do

- It does not decide scope, permissions or risk for the owner.
- It does not commit, and it does not edit an old ADR's meaning.
- It does not replace the reviewers. It makes sure they are run.
