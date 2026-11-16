# Design Patterns: Catalogue

> **What this is.** An inventory of the patterns this codebase actually uses: architectural (hexagonal ports and
> adapters, bounded contexts, anti-corruption layers) and Gang of Four. **Code is the source of truth**: every
> entry cites the file that realises it, and a pattern the code does not use is listed under *Not used* rather
> than claimed.

A pattern appears here only when `/vbench:v-2-design` named the force that demanded it. If you cannot name the
force, the code should be plain.

## Entry template

One file per pattern, `NN-<pattern>.md`, answering the same questions in the same order:

1. **Intent**: the canonical definition, stated once.
2. **Where it is used**: a table of participants with file references.
3. **Why here**: the design pressure that made it the right answer.
4. **Consequences and how to extend**: what it costs, and the one-line change it enables.

Mark the fit: **Canonical** (textbook instance), **Idiomatic** (genuine, in the language's idiom) or **Partial**
(the intent is present but a participant is missing; say so, do not overclaim).

## Numbering

| Range | Family |
|---|---|
| `10`–`19` | Architectural (hexagonal, bounded contexts, anti-corruption layer, read models) |
| `20`–`29` | Creational |
| `30`–`39` | Structural |
| `40`–`49` | Behavioural |
| `50`–`59` | Domain and persistence (repository, unit of work, value object and entity) |
| `90` | Patterns not used, and why |

## Catalogue

| Pattern | Fit | Realised in |
|---|---|---|
| (none recorded yet) | | |

## Not used

| Pattern | Why not |
|---|---|
| (none recorded yet) | |
