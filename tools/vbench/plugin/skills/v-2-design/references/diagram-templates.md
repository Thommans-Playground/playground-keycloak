# PlantUML diagrams per use case

Three kinds, one file each, named after the spec so the pairing is mechanical:

```
docs/usecase-diagrams/UC-N-001-create-note.md             the spec
docs/usecase-diagrams/UC-N-001-create-note-sequence.puml  who calls whom, in order
docs/usecase-diagrams/UC-N-001-create-note-class.puml     the structure: aggregates, ports, adapters
docs/usecase-diagrams/UC-N-001-create-note-state.puml     an aggregate's lifecycle
```

A second flow is `-sequence.2.puml`. Shared styling is `_style.puml` (and the colour key `_legend.puml`) in the
docs root, included as `!include ../_style.puml`. Those two files have no `@startuml`.

## Which, and when

| Kind | Required | Draw it to answer |
|---|---|---|
| **sequence** | standard and full tiers | In what order do the participants collaborate, and where do the alternates and errors go? |
| **class** | full tier | What are the aggregates, ports and adapters, and which way do the dependencies point? |
| **state** | any tier, **when the spec's `Lifecycle` row is `yes`**: something has two or more states with guarded transitions. The full tier requires the row to be decided (`yes` or `none`) | Which states can the thing be in, and which events move it between them? |

Whether something has a lifecycle is a design decision, so record it in the spec's **Lifecycle** row and give the reason
under Design decisions ("Note has Draft and Saved; saving is guarded by a non-empty body" gives `yes`; "a read has no
states" gives `none`). If an aggregate has one state, it is `none`. `yes` requires the state diagram at any tier, and the
full tier will not pass with the row left undecided.

After drawing, add the links to the spec's **Diagrams** row, e.g.
`[sequence](UC-N-001-create-note-sequence.puml), [state](UC-N-001-create-note-state.puml)`. `vbench check diagrams`
fails on a bad name, a file missing from the row, a missing required kind, or a file without `@startuml`/`@enduml`.

## System-level diagrams (MK3's numbering)

| File | Made by | Answers |
|---|---|---|
| `08-usecase-diagrams.puml` | **generated** by `vbench sync` from the spec headers (actor, bounded context, title, Depends on) | Who does what, grouped by context? Never edit it; fix the spec header and re-sync. |
| `09-context-ddd.puml` | scaffolded by `vbench new context-map` once two contexts exist; **authored** | How do the contexts relate (strategic DDD)? |
| `NN-<context>-ddd.puml` | scaffolded by `vbench new context --name "<Context>"` (NN = 10, 20, ...); **authored**, grown per use case | What are this context's aggregates, entities, value objects and events (tactical DDD)? |

**Context map.** One package per context, coloured by subdomain kind (Core `#FFD966`, Supporting `#F0F0F0`, Shared
kernel `#E6E6E6`, External `#E8E8E8`). One arrow per edge that crosses a boundary, labelled with the integration
pattern: `«C/S»` customer/supplier, `«OHS»` open host service, `«ACL»` anti-corruption layer, `«shared kernel»`,
`«conformist»`. A new context or a new edge is a full-tier change with an ADR. Name each context exactly as the
specs' **Bounded context** row does: `vbench check diagrams` looks for the name.

**Domain model.** Stereotype colours: root entity `#FFE6CC`, entity `#FFF2CC`, value object `#D5E8D4`, domain event
`#F8CECC`. Draw only the tactical blocks; facades, repositories, ports and adapters stay white. Write an AS-BUILT
note at the top (what the context owns, which value objects make a bad state unrepresentable, what is not drawn,
what is planned). Omit method parameters: the model shows parts, boundaries and language, and signatures live in
the code. Wrap the package in `!startsub` / `!endsub` so other diagrams can include just this context.

## Conventions
- `@startuml UC<id>_<Kind>` (e.g. `UCN1_Sequence`), then `!include ../_style.puml`, then `title UC-N-001 - <Title> (<Kind>)`.
- Colour by stereotype, matching `_legend.puml`: boundary `#E6F0FB`, service `#E7F4EA`, aggregate `#FFE6CC`,
  entity `#FFF2CC`, value object `#FBF2D9`, port `#EEE7F7`, infra `#ECECEC`.
- Use the project's vocabulary for every name (the requirements glossary). Cite the file for a participant once
  the code exists, and reconcile the diagram to the code in `/vbench:v-3-code` (code is the source of truth).
- One flow per diagram. Give every message a step id (`STP-N-001`, next free from `vbench id step --area N`) and group them
  in `== Phase ==` bands. Ids are unique and append-only: never renumber a step, retire it. Mark one not built yet with
  `(planned)`. Tasks, code and tests cite the id; `vbench check steps` and `vbench trace` read it back.

## Skeletons (example: a "create note" use case; replace the names)

### Sequence
```plantuml
@startuml UCN1_Sequence
!include ../_style.puml
title UC-N-001 - Create note (Sequence)

actor "Author" as U
participant "«boundary»\nNotesApi" as API #E6F0FB
participant "«service»\nCreateNote" as SVC #E7F4EA
participant "«aggregate»\nNote" as N #FFE6CC
participant "«port»\nNoteRepository" as REPO #EEE7F7
database "Store" as DB #ECECEC

== Phase 1 - Validate and build ==
U   -> API : STP-N-001 POST /notes {title, body}
API -> SVC : STP-N-002 create(title, body)
SVC -> N   : STP-N-003 Note.create(title, body)
alt body empty or too long
  N  --> SVC : raise InvalidNote
  SVC --> API : error
  API --> U  : STP-N-004 422 {field: body}
else valid
  N  --> SVC : Note {id, created_at}
  == Phase 2 - Persist ==
  SVC -> REPO : STP-N-005 add(note)
  REPO -> DB  : INSERT
  SVC --> API : note
  API --> U   : STP-N-006 201 {id, created_at}
end
@enduml
```

### Class
```plantuml
@startuml UCN1_Class
!include ../_style.puml
title UC-N-001 - Create note (Class)

rectangle "Notes context" as CTX {
  class "«boundary»\nNotesApi" as API #E6F0FB {
    +create(request) : Response
  }
  class "«service»\nCreateNote" as SVC #E7F4EA {
    +execute(title, body) : Note
  }
  class "«aggregate»\nNote" as N #FFE6CC {
    -id : NoteId
    -body : Body
    +{static} create(title, body) : Note
  }
  class "«value object»\nBody" as B #FBF2D9 {
    +value : str
  }
  class "«port»\nNoteRepository" as REPO #EEE7F7 {
    +add(note)
    +get(id) : Note
  }
  class "«adapter»\nSqliteNoteRepository" as IMPL #EEE7F7
}

API --> SVC : execute
SVC --> N : create
SVC --> REPO : add
N *-- B
IMPL ..|> REPO
@enduml
```

### State
```plantuml
@startuml UCN1_State
!include ../_style.puml
title UC-N-001 - Note lifecycle (State)

[*] --> Draft : create
Draft --> Saved : save [body not empty]
Saved --> Saved : edit [body not empty]
Saved --> [*] : delete
@enduml
```
