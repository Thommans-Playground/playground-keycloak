---
name: vbench-contexts
description: Challenge, brainstorm or check the choice of bounded contexts, aggregates, ports and the hexagon for this repo, using the ontology and the context map. Use this whenever the user asks "is this the right context", "should these be together or apart", "grill the contexts", "where does this belong", "is this a context or a port", or is adding or moving something in docs/domain, even if they never say "vbench". Also use it before adding a new context, port or aggregate.
---

# vbench-contexts

Test a boundary decision by asking hard questions, one at a time, and record the result.
The user is learning the design to explain it and guide a team, so ask them to answer
before you give your view. Do not hand over the answer first.

Read these first, in this order. They are the usual places under `docs/domain/`. If one is missing, say so, work from
what exists, and offer to create it when a decision needs recording (do not invent its content):

1. `docs/domain/README.md`: the order of work and the ground rules.
2. `docs/domain/ontology.md`: the things, links, actions and rules.
3. `docs/domain/context-map.md`: the current contexts and ports.
4. `docs/domain/decisions.md`: what is already decided. Do not reopen a decision without
   a reason. If the user wants to, add a new entry that replaces the old one.

The domain and the real behaviour of the product are the source of the shape. Do not copy another system's code or boundaries to decide yours.

## The six tests

Run the ones that fit. Say which test you are using.

1. **Same word, different meaning.** If one word means two things in two places, those
   places are separate contexts. If it means the same everywhere, they probably belong
   together.
2. **Change reasons.** Parts that change for different reasons, at different speeds, are
   apart.
3. **Transaction.** Things that must change together or not at all belong in one aggregate
   or context. (A stage move and its audit entry do, which is why the audit entry is
   written in the same unit of work.)
4. **Different owners.** If different experts own the rules, the contexts are likely apart.
5. **Deletion.** If you remove A, does B still make sense? A thing that means nothing
   without another (a lifecycle without an endpoint) belongs inside it.
6. **Chatty.** Two contexts that need each other for every action are probably one.

Two more checks for ports and the hexagon:

7. **Who owns the port?** The context that needs it. The domain says what it needs, not who
   provides it.
8. **Does the domain import anything else?** It must not. If a rule needs a database or a
   framework to be tested, the rule is in the wrong layer.
9. **Does a new context get the standard shape?** In the API every context is `domain/`, `application/`,
   `adapters/inbound/` and `adapters/outbound/` (ADR 0010), wired only in `app/composition/`. Settings and the
   declarative base live in `app/infrastructure/`, not in a context. If a proposed context needs a different shape,
   that is a finding to bring to the owner, and the ADR and `tests/test_architecture.py` change first.

## How to run it

1. Pick one choice in the map. Start with the one the user is least sure about.
2. Ask one question, naming the test, in plain words. Use a small example from the product.
3. Wait for the user to answer. If they are unsure, give a hint, not the answer.
4. Say whether the answer holds, and what changes in the map if it does not.
5. Agree a result: keep, merge, split, or turn into a port.
6. When a choice changes, update `ontology.md` and `context-map.md`, and add an entry to
   `decisions.md` with the reason. If a diagram shows the choice, change its `.puml` in
   `docs/domain/diagrams/` and any inline Mermaid copy in the same change (see
   `_vbench/standards/diagrams.md`). Offer a `docs(domain)` commit via `vbench-commit`. Do not
   commit unasked.

## Rules

- Short sentences, everyday words. No em or en dashes.
- Use the project's own words, from its ontology and vocabulary. Do not invent terms.
- Do not invent id prefixes or terms.
- Say what is built and what is only a target.
- A read model (the status board, Home, search) is not a context. Do not draw it as one.
- Give a recommendation with the main reason. Do not list every option.
- If the user's instinct beats yours, say so and change the map.

## Example

Question (deletion test): "If we removed the Lifecycle context, would anything it holds
still make sense on its own?" The user answers that a stage means nothing without its
endpoint. So the lifecycle goes inside Endpoints. Update the map and add the decision.
