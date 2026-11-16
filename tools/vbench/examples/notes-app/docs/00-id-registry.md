# Id registry

Every artifact has a three-part id, `<KIND>-<SCOPE>-<NNN>` (see [naming conventions](00-naming-conventions.md)).
Requirements, use cases, criteria and tasks carry theirs in the document that declares them. A context, a domain
model, a diagram, a code file and a test do not, so each is given one here.

`vbench sync` appends a row for anything new and never rewrites or renumbers a row, so an id keeps meaning the same
artifact. A renamed file or test is a new alias with a new id; the old row stays as a record. Do not edit inside the
markers.

<!-- vbench:begin registry -->
| Id | Alias | Kind |
|---|---|---|
| ARC-DOM-001 | `notes-model` | ARC-DOM |
| COD-SRC-001 | `src/notes/create.py` | COD-SRC |
| COD-SRC-002 | `src/notes/note.py` | COD-SRC |
| MOD-SEQ-001 | `UC-N-001:sequence` | MOD-SEQ |
| MOD-STA-001 | `UC-N-001:state` | MOD-STA |
| SYS-CTX-001 | `notes` | SYS-CTX |
| TST-ACC-001 | `tests/test_create_note.py::test_a_saved_note_has_an_id_and_both_timestamps` | TST-ACC |
| TST-UNT-001 | `tests/test_create_note.py::test_a_body_one_byte_over_the_limit_is_refused_and_the_limit_is_accepted` | TST-UNT |
| TST-UNT-002 | `tests/test_create_note.py::test_an_empty_or_blank_body_is_refused_and_nothing_is_stored` | TST-UNT |
<!-- vbench:end registry -->
