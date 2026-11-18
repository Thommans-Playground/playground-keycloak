---
name: vbench-uc
description: Create, update and check use cases, linked to requirements and acceptance criteria. The user names requirements (or types a goal in free text), and the skill reports a definite impact analysis from the recorded links (which use cases serve a requirement, which are suspect because the requirement changed, which requirements have no use case, which objects and rules are involved), then helps write or update the use case file in docs/usecases/ with multiple-choice questions, and records its analysis, its design and what changed between them. Use this whenever the user says "vbench-uc", "write a use case", "create the use case for FR-12", "which use cases does this affect", "do we have a use case for", "what is not covered by a use case", "update UC-E1", or has just finished requirements and wants the next step, even if they never say "vbench".
---

# vbench-uc

A use case is the step after requirements: **one thing one person does to reach one goal**, in
steps. It is the unit we plan, build and test. This skill writes and checks them, and reports what a
change reaches.

The folder, the file layout and the rules are in `_vbench/standards/usecases.md`. The ids are in
`_vbench/standards/naming-conventions.md` (section 5, the `use-case` fields). The
requirements and criteria it links to are described in `_vbench/standards/requirements.md`. Use vbench-req
to change those. This skill does not edit the two requirements files.

## Why the impact is definite

Every use case file records the requirements it serves and the criteria it runs, each with a short hash
of that row as a person last reviewed it. So the tool reports **facts that are written down**:
a use case serves FR-3, FR-3 has changed since the review, so the use case is suspect. A requirement
that no file serves has no use case. If the tool cannot show a link, say "no link recorded", never
"likely". Wording similarity is only used to suggest where to look, and is labelled as such.

## The helper

`python3 .claude/skills/vbench-uc/scripts/uc_tool.py <command>` (from the repo root):

- `impact ID [ID ...]`: for FR-/NFR- ids or UC- ids. Shows criteria, use cases (up to date or suspect),
  objects and rules (file exists or planned), and other requirements sharing them.
- `coverage`: functional requirements with no use case, by release.
- `diagram CONTEXT [--write]`: the use case diagram of one context, drawn from the files, or
  `diagram overview --write` for the composite. It never draws a use case that has no file, and it
  refuses to overwrite a hand-kept diagram unless told to (`--force`).
- `search "text"`: use cases and requirements that read like the text (by wording), and retired words.
- `next-id AREA`, `validate`
- `create` (JSON on stdin, `--dry-run` to preview): assigns the id, stamps the hashes, refuses a bad file. An
  explicit `"id"` is allowed when it is free. Retired ids (`docs/usecases/retired-ids.csv`) are never handed out.
- `check-upstream UC-ID`: read the flow against the requirements and criteria it serves. Lists, as
  facts, what vbench-req should propose. It changes nothing.
- `freeze UC-ID`: record a hash of each analysis revision, so an edit to a frozen one is caught.
- `trace UC-ID`: from each analysis element to what became of it in the design. Lost ones are marked.
- `sync UC-ID`: refresh the copied text of the requirements and criteria from the requirements files. `sync --all` does it for every use case (vbench-req runs it after it writes rows).
- `stamp UC-ID`: after a person has reviewed the use case against the current rows, record that
  (it also syncs).

**The file repeats the text.** A reader should not have to remember an id, so each use case file
carries the full statement of every requirement it serves and every criterion it runs (Given, When,
Then), between two `vbench-uc` comment markers. It is generated from the requirements files. Never edit it by
hand: change the row with vbench-req, then run `sync`. `validate` reports a copy that has drifted.
`sync` refreshes the text only. The use case stays suspect until a person reviews it and stamps it,
because new text is exactly what a person has to read.

To change an existing use case, edit the file, then `validate`. Run `stamp` only after the person has
confirmed the use case still matches the requirement. Stamping is the act of review, so never stamp
to make a warning go away.

## Two directions, one owner for each fact

- **Down (requirement or criterion changed):** the use case is SUSPECT, by the review hashes.
- **Up (the flow changed):** each use case also records a hash of the flow a person wrote. If the flow is
  edited after the last stamp, `validate` and `impact` say FLOW CHANGED, and `check-upstream` lists
  what the requirements and criteria may be missing. Hand that list to vbench-req, which proposes
  the edit for the owner to accept. Never edit the requirements files from here.

To make the up direction definite, **tag the flow lines with the ids they serve**, at the end of the
line: a main flow step ends with `(FR-88)`, and an other flow ends with the criterion that proves it,
`(AC-2)`. A step with no tag may mean a requirement is missing. An other flow with no `AC` tag has no
criterion yet. Lines starting "Open:" are exempt.

## Steps

1. **Scope.** Say in one line what you are examining. Take one use case at a time. If the user gives
   free text and no ids, run `search`, show the requirements it reads like, and ask which ones are meant.
   If the requirement does not exist yet, stop and send them to vbench-req.

2. **Impact analysis first.** Run `impact` on every requirement involved (and on the use case, if
   updating one). Report, in plain words and as facts:
   - the requirement and its criteria (or that it has none),
   - the use cases that serve it, up to date or suspect, and which criteria they do not list,
   - the objects and rules, with which have no file yet, and the contexts of those that do,
   - the other requirements that share the same objects or rules (they may need the same review).
   For a new use case, say it is new because no recorded link exists, and show what `coverage` says.

3. **Ask the choice.** Use `references/questions.md` section 1 (attach, change, new, split) with
   AskUserQuestion, with a recommendation and its main reason.

4. **Examine, then shape.** Take only the needed questions from `references/questions.md` (one thing,
   actor and area, what it serves and proves, what it touches, the flow, what it leaves behind).
   Skip a question the files already answer. Cross-check the actor against `permissions.csv` and the
   refusals against the criteria. A flow step with no matching requirement is a missing requirement, so
   raise it and offer vbench-req.

5. **Show the plan.** Show the file as it would be written (use `create --dry-run`), or the edit as a
   before and after. Show the id it will get. List anything unsettled; do not fill a gap with a guess.
   Put open points in the flow as a line starting "Open:".

6. **Ask, then write.** Offer **Accept**, **Change it**, **Reject**. On Accept, run `create` (or make the
   edit), then `validate`, then `impact` again on the requirements and report what changed. Do not
   commit. If the user wants a commit, use vbench-commit.

## Next step: the chain

The three skills hand work on in a line: vbench-req, then **vbench-uc**, then **vbench-at**. When a use case is
written or changed and `validate` is clean, **run the reviews first**, then say what comes next and offer it:

- **Reviews (run them, do not wait to be asked).** Start `vbench-spec-challenger`, `vbench-security-reviewer` and
  `vbench-design-reviewer` together on the use case id (they are read-only and independent). Show their findings
  as they come back, in plain words: what is wrong, why it matters, the options. Do not fix anything from them
  unasked. A person decides. Skip the reviews only for a change that touches no flow, criterion, diagram or
  decision (a typo, a rewording), and say that you skipped them.

- A criterion the use case lists has no acceptance test (`python3 .claude/skills/vbench-at/scripts/at_tool.py
  report`): offer **vbench-at**. The test is the outer loop, so it comes before the code of the first slice.
- A requirement it serves has no criteria, or a criterion is vague or wrong: offer **vbench-req**. This skill
  never edits the requirements files.

## Slices

A use case does not have to be built in one go. The **Slices** section lists the thin pieces, each
becoming one card with an id `TSK-<area><n>.<k>` (for example `TSK-V1.1`). A slice names the criteria
it proves, and the rules it carries. In `create`, give `slices` as a list of
`{"name": ..., "proves": ["AC-1"], "rules": ["RULE-V1"]}` and the tool numbers them.

Put each rule in the first slice that needs it. `validate` and `check-upstream` report a criterion no
slice proves, and a rule no slice carries. A slice may not prove a criterion the use case does not list.

## Analysis, design and the change log

After the flow, a use case is analysed and then designed, and the change between the two is recorded so that
nothing in the analysis is lost. The format is in `_vbench/standards/usecases.md`.

1. **Analysis**: add `## Analysis`, `### Revision 1`, the **analysis sequence diagram** and one line for each
   element: `A1 (object): ...`, `A2 (step): ...`, `A3 (rule): ...`, `A4 (port): ...`. The diagram is a system
   sequence diagram, a file `docs/usecases/diagrams/UC-<id>-<slug>-analysis-sequence.puml`: the person, Playground as
   one box and any outside system (for example Keycloak), the messages between them and the failure branches. No
   route, store, port, adapter, token, cookie or algorithm: those words belong to the design. Its steps carry the
   main flow numbers. Ask the person to accept it, then `freeze` it. A use case with one system and no security
   flow keeps a single `UC-<id>-<slug>-sequence.puml` and says in its Design section that the analysis and the
   design are the same (decision 9).
2. **Ontology** (a later step, not built): the objects and rules the analysis revealed go to vbench-ontology.
3. **Design**: add `## Design`, the **design sequence diagram** (`UC-<id>-<slug>-design-sequence.puml`: routes, use
   cases, ports and adapters, same step numbers), the context **class diagram** (`docs/domain/diagrams/<context>-design.puml`,
   and one for the web server (BFF) where the use case runs there) and one line for each element: `D1 (aggregate): ...`,
   `D2 (value object)`, `D3 (port)`, `D4 (adapter)`, `D5 (domain event)`.
4. **Changes from analysis to design**: one line for each analysis element (`A1 kept -> D1`, `A2 became -> D2:
   reason`, `A7 dropped: reason`), and `+ D8 added: reason` for a design element with no source.
5. Run `validate` and `trace`. `validate` notes an Analysis section with no analysis (or single) sequence file, and a
   linked `UC-*.puml` that does not exist. The link between the two levels is the change log, not the diagrams; in
   the design, every step of the sequence lands on a class and every port and adapter carries a step. A lost
   analysis element is a problem to fix, not to hide.

Never edit a frozen analysis revision. If the analysis was wrong, add `### Revision 2` and say what changed. Do not
drop an analysis element to make the log pass: drop it only with a reason a reader can judge.

## Writing the file

The flow is what makes a use case useful to the team, so write it for a developer who has not met the
requirement:

- Steps are numbered and each says one thing and who does it. Use "the project manager asks", "the
  system checks", not passive blur.
- Every refusal in the criteria appears in "Other flows" with what the person sees, ending with its
  criterion in brackets, for example `(AC-2)`. Every main flow step ends with the requirement it serves,
  for example `(FR-88)`.
- Slices come after the flow, and the analysis, design and change log come after the slices. The smallest
  slice that works on its own comes first.
- No screens, endpoints, tables or code. Those belong to the cards. Say what, not how.
- Use the project's own words. If `vocabulary.csv` retires a word, do not use it.
- No em dashes or en dashes anywhere.
- The `evolved_from` field may name where an idea came from. Leave it empty if unknown.
- Do not copy text from the earlier products. Read, then write it fresh.

## Rules that matter

- Ids are append only. Never renumber or reuse. A dropped use case becomes `status: retired`.
- New use cases start as `draft`. Only the owner moves one to `accepted`.
- A use case that changes an object does so through its rules. If a rule is missing, say so and hand
  it to vbench-ontology. If the boundary of a context is in doubt, hand it to vbench-contexts.
- A branch named `feat/UC-<id>-<slug>` is for building the use case later. Writing the spec is a docs
  change.
- The tool only covers functional requirements for `coverage`. Quality, constraint and process
  requirements constrain use cases rather than being served by one.

## Example

User: `/vbench-uc approve a pending account`

You: run `search`, which reads like FR-1 (approve a pending account). Run `impact FR-1`: criteria AC-1
and AC-2, no use case, no object or rule recorded in the row. Report: "FR-1 has two criteria and no use
case. No link is recorded to any object. Nothing else shares its objects." Ask: new use case in the
Access area (UC-A1)? Then ask the actor (administrator), parameters (the account), and the flow, and
show the file with `create --dry-run`.
