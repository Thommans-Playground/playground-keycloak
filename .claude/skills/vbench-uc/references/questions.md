# Question bank for vbench-uc

Ask only what the use case in front of you needs. At most four questions a call, with a recommended
first option when there is one. One use case at a time keeps the examination small.

## 1. New use case, change, or attach?

Ask after `impact` and `search`.

- **Attach**: the requirement fits an existing use case (same actor, same goal). Add it to that file's
  `satisfies`. (Recommended when one use case already does the same thing for the same person.)
- **Change**: an existing use case needs different steps. Edit the file, then `stamp`.
- **New**: nothing covers it. Write a new file.
- **Split**: one use case does two things. Keep the id on one, write a new file for the other.

## 2. Is it one use case?

A use case is **one thing one person does to reach one goal**, small enough to plan as a few cards.
Group requirements into one use case when the answer to all five tests is yes, and split when it is
no:

| Test | Question |
| ---- | -------- |
| Actor goal | Do they serve the same objective of the same person? |
| Business outcome | Together, do they produce one meaningful result? |
| Dependency | Must these behaviours work together to make sense? |
| Independence | Can the person trigger it on its own, without the rest? |
| Transaction boundary | Should these steps succeed or fail together? (If so, they are one use case, and usually one aggregate.) |

- Two actors or two goals: split it.
- A quality, a constraint or a process rule is usually not a use case. It constrains several. Record it
  in the `notes` of the use cases it bears on.
- A requirement may serve more than one use case, and a use case more than one requirement.

## 3. Who and where?

- **Actor**: administrator, auditor, project_manager, engineer, or system (a step with no person).
  Check `permissions.csv` so the actor may do it.
- **Area**: the letter of the context that owns the change (A, C, E, F, G, L, P, V). If a use case
  changes objects in two contexts, name the one that owns the main change and list the other as a port
  in the flow. Hand a boundary doubt to vbench-contexts.

## 4. What does it serve and prove?

- Which requirements does it serve? List every one. Each must exist in `requirements.md`.
- Which acceptance criteria does it run? Every criterion of a served requirement should be run by some
  use case. `validate` lists those not listed.
- A requirement with no criteria cannot be confirmed. Send the user to vbench-req first.

## 5. What does it touch?

- **Objects** (OBJ ids) it reads or changes. If one has no ontology file yet, say so; do not invent it
  here. Hand it to vbench-ontology.
- **Rules** (RULE ids) it checks before it changes anything. A rule that is not a file yet is noted.
- **Parameters**: what the person gives it.

## 6. What happens?

- **Preconditions**: what must already be true (an account exists, the endpoint is in a stage).
- **Main flow**: numbered steps, each one thing, in the project's words. Say who does each step.
- **Other flows**: each refusal and edge from the acceptance criteria. One line each: the situation,
  then what the person sees. Each should match a criterion.
- **Postconditions**: what is true afterwards.

## 7. What does it leave behind?

- **Effects**: what it records or sends. An audit entry? A stage move? A notification? Write each as a
  short line.
- **Not in this use case**: what a reader might expect but is left out, so nobody looks for it.

## 8. Slices

A slice is a thin, testable piece of the use case that delivers behaviour end to end (domain, use
case, adapter, screen) and becomes one card. Each gets an id `TSK-<area><n>.<k>`.

- Which is the smallest slice that works on its own? Put it first.
- Which criteria does each slice prove? Every listed criterion should belong to one slice.
- Which rules must hold? Put each rule in the **first slice that needs it**, never in a later "hardening"
  slice. A rule added late is a rule that was missing in between.
- Can a slice merge within 1 to 2 days? If not, split it.

## 9. Analysis and design

Ask these after the flow is agreed, one record at a time.

- **Analysis:** Who or what takes part in each step? Which domain objects appear? Which port does each call to
  another context go through? Which rule is checked, and where? Is there anything in a step that the use case
  file does not say?
- **Freeze:** Is the analysis complete enough to design from? If yes, freeze it. If a mistake turns up later, add a
  revision and never edit the frozen one.
- **Design:** Which object is the aggregate root, and what must hold inside it? Which is a value object? Which
  call is a port, and what answers it? What is only an adapter detail?
- **Change log:** For each analysis element, what became of it? If it was dropped, why? Which design elements have
  no analysis source, and why do we need them?

## 10. Close

Show the file (or the change). Ask: write it, change it, or stop. Run `validate` after writing, then
`impact` on the requirements it serves and report the result.
