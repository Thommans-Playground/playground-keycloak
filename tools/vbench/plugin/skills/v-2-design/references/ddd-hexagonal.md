# DDD and hexagonal, as applied here

## Domain first
- **Bounded context**: default to an existing one. Propose a new one only when the use case needs a model whose
  terms conflict with an existing context, or it has a different lifecycle or owner. State each neighbour and
  the relationship (published language, anti-corruption layer, conformist).
- **Aggregate**: the consistency boundary. Name it, name its invariants in the context's language, and keep it
  small: reference other aggregates by id, change one aggregate per transaction.
- **Entity vs value object**: has identity that outlives its attributes, then entity; defined by its
  attributes and replaceable, then value object (immutable, validated at construction).
- **Domain service**: only for behaviour that belongs to no single aggregate.
- **Ubiquitous language**: reuse an existing term; add a new one (append-only) with a one-line definition;
  translate at the seam when a neighbour means something different.

## Hexagonal at the seams
- The domain depends on nothing outside itself. Ports are defined by the core; adapters implement them.
- A **port** exists only where there is a real external dependency, a genuine second implementation, or a
  test that needs a fake. In-process logic with one implementation gets no port.
- Cross-context calls go only through the other context's public interface, never its tables or internals.
- Driving adapters (HTTP, CLI, consumers) translate input into use-case calls; they hold no rules. Driven
  adapters (database, queues, third-party APIs) translate the core's needs into technology.
- Translate errors at the boundary: the core raises domain errors; the adapter maps them to status codes.

## Verifying the shape
A `boundaries` command in `[commands]` (for example an import-linter contract) turns the dependency rule into a
failing test. Prefer one over a convention that depends on review.
