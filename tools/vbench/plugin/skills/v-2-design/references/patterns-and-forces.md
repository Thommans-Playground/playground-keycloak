# GoF patterns: only when a force demands them

State the force in one sentence. If you cannot name it, write plain code.

| Force | Pattern | Skip it when |
|---|---|---|
| Behaviour varies by a runtime choice and the variants will grow | **Strategy** | there are two variants and no third in sight |
| An object's behaviour depends on its state, with legal transitions to enforce | **State** | a flag and one `if` do the job |
| Several steps must be undoable or queued or logged as units | **Command** | you only call a function |
| Construction is complex, or must hide which concrete type is made | **Factory / Builder** | a constructor with defaults suffices |
| A third-party API's shape must not leak into the domain | **Adapter** (or anti-corruption layer) | the API already matches your terms |
| Many collaborators react to one event, and the sender must not know them | **Observer / domain event** | one known listener |
| An operation needs a stable, simpler face over a subsystem | **Facade** | the subsystem is already one call |
| Cross-cutting behaviour wraps a call (auth, retry, metrics) | **Decorator** | one call site needs it |

Prefer deep modules: a small interface over substantial behaviour. For a non-trivial interface, sketch two
designs and choose one, recording the force behind the choice under Design decisions.
