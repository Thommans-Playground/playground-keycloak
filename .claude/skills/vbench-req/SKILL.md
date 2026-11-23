---
name: vbench-req
description: Check, write and tidy requirements and their acceptance criteria. The user types one or more requirements, and the skill searches docs/requirements/requirements.md and acceptance-criteria.md to say whether each one already exists, is a change to an existing row, or is new, then helps write the row and its Given/When/Then criteria with multiple-choice questions. Use this whenever the user says "vbench-req", "add a requirement", "is this requirement already there", "do we already have", "write acceptance criteria for", "check this requirement", "new FR", "update FR-12", or pastes a sentence that sounds like "the system shall ...", even if they never say "vbench".
---

# vbench-req

Examine a requirement in small, scoped steps: is it already here, what is it, what proves it. The
files are the source of truth, so every claim starts from a search, not from memory.

The rules for the files are in `_vbench/standards/requirements.md` (the layout of the two markdown files) and `_vbench/standards/csv-files.md` (the CSV files beside them). The ids are in
`_vbench/standards/naming-conventions.md`. This skill applies them and does not restate them.

## The helper

`python3 .claude/skills/vbench-req/scripts/req_tool.py <command>` (run from the repo root):

- `search "text"`: close requirements (with their criteria), similar criteria, rules, permissions,
  decisions, and wording problems (shape and retired words).
- `next-ids`, `validate`
- `convert`: once, when a repo still has `requirements.csv` and `acceptance-criteria.csv`: writes the two markdown files. The CSV files stay until the person deletes them.
- `append requirements|acceptance` and `update ID`: JSON on stdin. Add `--dry-run` to preview. They
  assign ids, keep the CRLF line endings, and refuse a row that fails the checks.

Do not edit the requirements or criteria files with Edit. Use the helper, so the ids, columns, notes and
line endings stay right. A person may fix a cell by hand: the tool reads it back.

## Steps

Work on one requirement at a time. If the user gives several, list them, then take them in order and
say which one you are on.

1. **Keep the scope.** State in one line what you are examining. Do not wander into use cases, screens
   or code. Use cases are a later step.

2. **Search.** Run `search` with the user's own sentence. Read the output yourself. The score only
   guides you. Open the row if you are unsure.

3. **Say what you found, in plain words.** One of:
   - *Same as FR-n* (score about 0.6 or more, same verb and same thing).
   - *A change to FR-n* (same thing, different wording, release, scope or role).
   - *Overlaps FR-n* (a neighbour, probably a different requirement).
   - *New* (nothing close).

   Show the matching statement and its criteria. Note if `today` says it is built, if its release is
   parked or backlog, and if a decision or rule in the output bears on it. If a rule or a decision
   conflicts with the request, say so before going on.

4. **Ask the choice.** Use `references/questions.md`, section 1, with AskUserQuestion. Give a
   recommendation and the main reason. Do not go on until the user picks.

5. **Examine, then shape.** Take the questions from `references/questions.md` that this requirement
   needs (one, kind, place, who, ontology, proof). At most four per call. Skip a question when the
   answer is already clear from the search or the user's words. Check the wording rules: "The system
   shall ...", one thing, project words, no retired words, no how.

6. **Acceptance criteria.** Look at the criteria the search listed.
   - If the requirement has none, help write them (questions.md section 7): the happy path, what is
     refused, the edge, the test level. One outcome in each.
   - If it has some, check them against the change. Say which ones still hold, which need a new line,
     which are now wrong.
   - A quality requirement needs the four scenario answers first (section 8).

7. **Show the plan.** Show each row to add or change as a short before and after. Say what ids they
   will get (`next-ids`). Say anything left unsettled: it goes in `notes` or the status `open`. Do not
   fill a gap with a guess.

8. **Ask, then write.** Offer the four answers of `_vbench/standards/conventions.md` ("How the skills ask"): **Accept**, **Change it**, **Reject**, **I'll do it myself**. On Accept, run `append` or
   `update` (use `--dry-run` first if the change is large), then `validate`. Then run
   `python3 .claude/skills/vbench-uc/scripts/uc_tool.py sync --all`, so the copied text in every use case
   file matches the rows you just wrote. This refreshes the generated copy only: it never edits a flow and never
   changes a review hash, so each use case stays suspect until a person stamps it. Report the ids written, the
   use cases refreshed and any problem. If a criterion about sign in, tokens, sessions, accounts, roles or audit
   changed, say that it touches security, so the security reviewer must be in the review pass (`vbench-uc` starts the
   reviewers once, when the use case is written or changed; do not start them here). Do not commit. If the user wants a commit, use vbench-commit.

## Next step: the chain

The three skills hand work on in a line: **vbench-req** (requirements and criteria), then **vbench-uc** (use
cases), then **vbench-at** (acceptance tests). After you write or change rows, say what comes next and offer it.
Do not start it unasked.

- A functional requirement with no use case (`uc_tool.py impact ID`, or `coverage`): offer **vbench-uc**.
- An acceptance-level criterion with no test (`at_tool.py report`): offer **vbench-at**.
- A criterion that vbench-uc or vbench-at sent back as vague, wrong, or at the wrong level: this is where it
  is fixed. Ask the owner, then change the row.

## Duplicates

`python3 .claude/skills/vbench-req/scripts/req_tool.py duplicates` is read only. It lists likely duplicates
in three places, with the same word matching as `search` (no model, so the same input gives the same output):
requirements (name and statement, default 0.55), acceptance criteria (given, when, then, default 0.65, plus
pairs with near-identical then-clauses of three words or more under different requirements), and use cases (name and description,
default 0.5, pairs sharing half of the smaller one's criteria, and any criterion listed by more than one use
case). Retired rows are skipped. `--threshold N` overrides the score, `--kind requirements|acceptance|usecases`
picks one section. It always exits 0: it reports, it does not gate.

Run it before adding a row (to see if the area is already crowded) and before a release. It is a prompt for a
person: it never edits, retires or merges anything. Show the pairs and offer the safe options: retire one
(status `retired`), merge keeping one id, move it to another level, or defer with an R2 note. The owner decides.

## Rules that matter

- Ids are append only. Never renumber or reuse. A dropped row gets `status: retired`.
- A new requirement starts as `draft`. Only the owner moves it to `accepted`.
- Use the project's own words. If `vocabulary.csv` retires a word, do not use it.
- No em dashes or en dashes in anything you write.
- If the request needs an ontology object or rule that does not exist, record it in `notes` and hand
  it to the vbench-ontology skill. Do not invent it here.
- If it changes the shape of the contexts, hand it to vbench-contexts.
- Teaching: when the user is learning, ask them to write the Given, When, Then of one criterion
  themselves, then compare.

## Example

User: `/vbench-req the system shall let an administrator approve an account`

You: run `search`. FR-1 scores 0.71 and says "...approve a pending account so that the person can
sign in", with AC-1 and AC-2. Say: "This is already FR-1, with two criteria." Ask whether to change
nothing, change FR-1, or add a new row. Likely answer: nothing to change, then check whether the
criteria cover a refused case (they do: AC-2).
