# Question bank for vbench-req

Pick only the questions the requirement in front of you needs. Ask at most four at a time with
AskUserQuestion. Give a recommended first option when there is one. Each question is about one
requirement, so the examination stays small.

## 1. Is it new, a change, or the same?

Ask after the search shows a close match.

- It is the same as FR-n: change nothing, or add acceptance criteria if it has none. (Recommended when
  the score is 0.6 or more.)
- It changes FR-n: update that row. Ask what changes: the wording, the release, the scope.
- It is new, and FR-n is a different thing: add a new row.
- It splits FR-n into two: keep the id on one half, add a new row for the other.

An id never changes and is never reused. A dropped requirement is set to `retired`.

## 2. Is it one thing?

- Does the sentence need "and" to join two actions? Offer to split it.
- Is it a goal ("should") or a duty ("shall")? Only "shall" goes in the file.
- Does it say what, or how? A how (a screen, a button, a table) belongs in a use case later. Offer to
  rewrite it as what the person gets.

## 3. Which kind is it?

- **Functional**: the system does something a person can see.
- **Quality**: a measurable level of how well (speed, safety, no lost updates). It needs the five
  scenario fields. Ask for the measure. If nobody knows, record `not decided`.
- **Constraint**: a limit imposed from outside (where data lives, a law, a framework). A choice the team
  made itself is a decision (ADR), not a constraint.
- **Process**: the team shall do something to build or release (test a restore, review a change).

## 4. Where does it sit?

- Area letter (the part of the product).
- Release: R1, R2, R3, backlog, parked, or none. If R1, remind the owner that the release plan has no
  slack and ask what drops or waits. (Release 1 already widened for both frameworks, decision 14.)
- Today: built or not built in the prototype.

## 5. Who may do it?

For a functional requirement that changes something, check `permissions.csv`.

- Which roles may do it: administrator, auditor, project manager, engineer?
- Is there a permission row for it already? If not, offer to add the row (an owner decision).

## 6. Does it touch the ontology or the rules?

- Which objects does it use (OBJ ids)? If one is missing, say so in `notes`. Do not invent an object here.
  Hand the object to the vbench-ontology skill.
- Is there a rule that always holds (RULE id, or an R number in the rule inventory)? Reuse it. A new rule
  is written with vbench-ontology.
- Does it clash with a decision? Read the decisions the search listed.

## 7. How will it be proved? (acceptance criteria)

A requirement is confirmed when something can prove it. For each requirement ask:

- What is the happy path? Write Given, When, Then.
- What is refused? (no reason given, wrong role, a duplicate, an empty value)
- What is the edge? (zero items, the limit, the last one, the first one)
- Is there an audit entry or a notification the person should see?
- Which level proves it?
  - **unit**: one rule, no database.
  - **integration**: a port and its adapter.
  - **acceptance**: the whole thing through the front door. (Recommended for anything a person does.)
  - **manual**, **inspection**: a person looks. Say who.
  - **future**: cannot be tested yet. Say why in notes.

Keep one scenario to one outcome. Use the project's words (checklist, evaluation, project manager).

## 8. Quality scenario (only for a quality requirement)

Ask these four in order. Skip none, even if the answer is "not decided".

- Stimulus: what happens that triggers it?
- Environment: under what conditions (normal load, offline, a full database)?
- Response: what must the system do?
- Measure: how do we tell it passed (a number and a unit)?

## 9. Close

Show the final rows. Ask: add them, change them, or stop. Run `validate` after writing.
