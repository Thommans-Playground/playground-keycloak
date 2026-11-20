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

## The order: think, draft, review, then build

This is the V cycle in small. **Nothing is built until the design has been reviewed and settled.** Jumping ahead (building while the decision is still open) carries the designer's blind spots straight into the code, and is the most common way to end up redoing work.

| Phase | What happens | The rule |
|---|---|---|
| **1. Think** | Load the context, interview the person one question at a time, challenge assumptions, weigh options. | **No code.** No source or test file changes in this phase. Notes and docs only. |
| **2. Draft** | Write the decision to a file: the ADR (or the decisions.md entry), with its alternatives and the files that will change. | The draft is a file, not a chat message, so a reviewer can read it cold. |
| **3. Review** | Three fresh-eyes checks (below), fix what they find, loop until it holds. A person decides. | Reviewers get only the file path and its sources, never your conclusions. |
| **4. Build** | Test first, then the minimum code (`vbench-tdd`), then the checks and the example. | Only now. If the design has to change, go back to phase 2. |

## Steps

**Phase 1: think (no code)**

1. **State the decision in one sentence.** If you cannot, it is not ready.
2. **Load the context.** Read `docs/adr/`, `docs/domain/decisions.md`, the context page in `docs/domain/contexts/` and `CLAUDE.md`. A new decision never edits an old ADR's meaning. It extends or supersedes it by number.
3. **Look before you invent.** Is there a well known pattern that fits (ports and adapters, unit of work, composition root, shared kernel, anti-corruption layer, deny by default)? Follow it and name it in the ADR. Say why only where the project differs. A student reading the ADR should be able to look the pattern up.
4. **Interview, do not announce.** Ask the person one question at a time about what they need and what worries them, and let them make the call. List at least two real options with what each costs. Write down the ones you drop, because the ADR must say why.
5. **Split the owner's part from the technical part** (table above).

**Phase 2: draft**

6. **Write the ADR as a file.** `docs/adr/NNNN-short-title.md` from `docs/adr/0000-template.md`, status `proposed`: context in two or three sentences, the decision in the present tense, **the alternatives considered**, **the files that change**, the consequences with their cost. Number it, never reuse a number.

**Phase 3: review with fresh eyes**

7. **Comprehension check.** Give a fresh agent only the ADR path and ask it to explain, in its own words, what will be built and why. If its explanation differs from your intent, the draft is ambiguous: fix the draft, not the agent.
8. **Run the reviewers** when the decision touches a flow, a boundary, a requirement or a decision: `vbench-design-reviewer`, `vbench-spec-challenger` and `vbench-security-reviewer` together, read-only (CLAUDE.md, "Reviews"). Brief each with the file path and its sources only, with no conclusion of yours. Treat their output as advice, not as approval. Resolve each finding, or record it as accepted, and loop until nothing serious is left.
9. **Readiness check.** Ask a fresh agent: "could you build this from the file alone, or would you have to guess?" List what it would have to guess (paths, names, signatures, error codes) and add it to the draft. Have it also write down **which files it expects the build to change**, and keep that prediction with the draft. End with an explicit verdict: **GO** (it could build the behaviour without guessing) or **NO-GO** with the blockers listed. The bar is that behaviour, names and error codes are unambiguous, not that every function signature is written out: test first leaves the signatures to the code. On NO-GO, go back to step 6. Only on GO does a person set the status to `accepted`.

**Phase 4: build (only now)**

10. **Make it checked.** Add or extend a test that fails when the rule is broken, and make the failure message say why (see `apps/api/tests/test_architecture.py`). Write the failing test first and watch it fail. If the rule cannot be tested, say so in the ADR and name who checks it.
11. **Compare the prediction with the build.** Run `git diff --stat` and set it beside the predicted file list. A file nobody predicted, or a predicted file that did not change, is a sign the design was unclear or the build wandered outside it. Say which, and fix the draft or the build. Do not keep the file list in the use case or the ADR after the build: it goes stale, and the `Realises UC-...` tags and `uc_tool.py trace` are what trace the code.
12. **Leave an example.** The first thing built the new way is the template. Point to it from the ADR and from `docs/GETTING-STARTED.md`.
13. **Tell the people and the agents.** Update `CLAUDE.md` where it describes the area, and the agents or skills that mention the old way (`grep -rn` the old path or name under `.claude/`). An agent has no hallway conversation: if it is not written there, it will not know.
14. **Check the three questions before you stop.**
    - Is it written down?
    - Does a test fail if someone breaks it?
    - Is there an example to copy?

    If any answer is no, the decision is not finished. Say which one, and why.

## What this skill does not do

- It does not decide scope, permissions or risk for the owner.
- It does not commit, and it does not edit an old ADR's meaning.
- It does not replace the reviewers. It makes sure they are run, and run on a file, not on your summary.
- It does not build anything in phases 1 to 3.

The comprehension check and the readiness check, and the habit of designing in one context and reviewing in a fresh one, come from the Elephant-Goldfish Model (Google, Apache 2.0, announced on the Google Open Source blog, October 2026). The post gives no evidence that it works, so treat these steps as a sensible practice and measure whether they catch problems here.
