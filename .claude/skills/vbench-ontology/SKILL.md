---
name: vbench-ontology
description: Add to or change the project's ontology the standard way, after Palantir's Ontology: object types, links, actions, rules and value sets as Markdown files whose data is a YAML code block at the top, checked and traced. Use this whenever the user wants to add or change an object, a link, a use case or action, a rule, a value set, a context or a port, says "add this to the ontology", "model this", "is this already in the ontology", "which objects does this touch", or edits anything under docs/domain/ontology/ or docs/domain/contexts/, even if they never say "vbench" or "Palantir". Also use it to review an ontology change in a pull request.
---

# vbench-ontology

Make every ontology change the same way, so the model stays small, consistent and traceable.

The standard is `docs/domain/ontology-process.md`, and the ids and the file header are in
`_vbench/standards/naming-conventions.md`. If a rule changes, change those, not this file. Read both before
the first change in a session.

The user is learning the design to explain it and guide a team. Ask them to say each choice
back, and explain why, in plain words.

## The loop

Follow the ten steps of the process, in order, and stop at each "done when":

1. **Decision.** Write one sentence: who decides what, with which facts. Find or create the
   requirement or use case it hangs on. If there is none, say so and ask. Do not model a thing
   nobody decides anything with.
2. **Search first.** Look through `docs/domain/ontology/` and `docs/domain/contexts/` for an
   object, rule or value set that already covers it. Say what exists and why it is not enough.
   Prefer reuse to a near-duplicate.
3. **Objects.** One `OBJ-<area><n>-<slug>.md` per thing. The file starts with a YAML code block
   (context, record id prefix or `none`, one-sentence `comment`, typed `properties`, `links`,
   `rules`, `questions`), followed by plain explanation. Give each property a `type` and say if it
   is `required` or `many`. Do not put a property on an object that belongs to another.
4. **Links.** Binary only, read as a sentence: `domain`, `property`, `range`, with `cardinality` and
   `kind` (`part` or `reference`). Define it once, in the file of its domain object. In the other
   file, show it with `defined_in`. A relation with its own attributes becomes an object.
5. **Actions.** A use case is the only way state changes. Give it an actor, parameters, the
   objects it touches, the rules it checks and its effects (an audit entry, a notification).
6. **Rules and sets.** A `RULE-` file for each thing that always holds, naming its object. A
   `SET-` file for each fixed list. Quote `"Yes"`, `"No"` and `"N/A"`.
7. **Context and ports.** Put each object in exactly one context. Use `vbench-contexts` if the
   boundary is unclear. A need from outside is a `PORT-`, numbered in the area that needs it.
8. **Trace.** Fill `satisfies` upward. Add `proved_by` for rules once there is a test tagged
   `Verifies`. A link up to a requirement that does not exist is a gap: say so.
9. **Check.** Run the lint when it exists. Until then, check by hand: ids match file names, every
   link points at an item that exists, every object has one context, and no unquoted `yes`.
   Update any diagram or table that is not yet generated.
10. **Review.** Add a decision to `docs/domain/decisions.md` if a choice was made. Offer a commit
    through `vbench-commit` and a pull request through `vbench-pr`.

## What every file contains

Write each file so it can be read cold. After the YAML block:

- **Object:** what it is, why it exists, in context (a Mermaid ER diagram of its neighbours), how
  it behaves (a state diagram, flow or sequence where it helps), an example, and what is not yet a
  file.
- **Rule:** the rule in plain words, why it exists, what is allowed and refused, how it works (a
  diagram), how a test would prove it, and what it relates to.
- **Set:** the values and what each means, why it is fixed, and how it is used.
- **Context:** what it is, its boundary, in context, the rules it holds, and what is not yet built.

Use lists, not tables. Use plain Mermaid (see `vbench-mermaid`). Put the `questions` (competency
questions) in the YAML: what the item must help answer.

## Rules to hold to

- **Palantir's habits:** start from the decision, reuse before you create, links are binary,
  change state only through actions, review every change, prune what nothing uses.
- **Project words:** use the names already in the vocabulary and ontology. Do not invent terms.
- **Ids are append only.** Never renumber or invent a prefix. The prefixes are in
  `_vbench/standards/naming-conventions.md`.
- **Say what is built.** A file marked `draft` is a proposal. Do not write as if the script or the
  generated diagrams exist before they do.
- **No em or en dashes** in any file.
- **Diagrams:** plain Mermaid inline where it helps (a state machine, a flow). Use `vbench-diagrams`
  to pick the format.
- **Do not commit unasked.**

## Example

User: "we need to record who approved each order".

1. Decision: a manager must know whether an order was approved by a person or by an automatic rule.
   Today the audit trail records the change, but the order does not show who approved it.
2. Search: `OBJ-O1-order` already exists, and the audit trail records the change.
   The approver is not a new object.
3. It is a property of the order, not a new object. Add `approved by` to the order's
   properties, with a value set `SET-` of two values (person, rule) if it is fixed.
4. No new link. The action that sets it is the approve-order use case, so add it to that use case's
   effects. Add a rule if "an order approved by a rule is never final until a person has looked" must hold.
5. Trace it to the requirement, run the check, add a decision, and offer a commit.
