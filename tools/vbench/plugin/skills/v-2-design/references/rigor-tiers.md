# Rigor tiers

Pick the smallest tier that fits and say why. Default is the spec's `Rigor` field (`rigor_default` in config).

| Tier | When | Produces |
|---|---|---|
| **light** | Low-stakes, reversible, inside one context | ACs, a few design lines, tests. No diagrams. |
| **standard** | A user-facing feature inside one context | + Design decisions, Verification plan, sequence diagram |
| **full** | External API, auth/security, schema change, or a new cross-context edge | + class diagram, domain-model update, ADR, integration and system tests |

The **full** tier also owes the context's domain model (`NN-<context>-ddd.puml`), and any project with two or more
contexts that have designed use cases owes the context map (`09-context-ddd.puml`), at every tier.

A **state diagram** is required at any tier when the spec's `Lifecycle` row is `yes` (something has two or more states
with guarded transitions). The full tier also requires the row to be decided, `yes` or `none`. `vbench check diagrams` requires the sequence (standard) and class (full) files once the task plan exists.

Escalate when any of these appear mid-design: a new table or column, a new inbound or outbound integration,
a change to who may do what, a new edge between bounded contexts. De-escalate only with the user's say-so.
Never produce a diagram the tier does not call for.
