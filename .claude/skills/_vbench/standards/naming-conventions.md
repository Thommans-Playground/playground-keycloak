# Naming and id conventions

The single source of truth for the ids used in the requirements, use case and ontology files. **The
prefix says the type. The letter says the area. The number is a stable sequence.** So `UC-O1` is a
use case in Orders, and `OBJ-P2` is an object type in Projects.

The examples below use a small shop and tracker app with two areas, Projects (P) and Orders (O).
Your project defines its own.

## 1. Area letters

An area is one part of the product, usually one bounded context. It gets one capital letter. A
letter is append only: once used it is never changed or reused. A new area gets a new letter.

The letters are defined in `vbench.json` at the repo root, under `areas`. The key is the letter and
the value is the context name that use cases in that area put in their `context` field:

```json
{
  "areas": { "P": "Projects", "O": "Orders" },
  "actors": ["admin", "member"],
  "providers": ["identity-provider"]
}
```

- With `areas` set, the tools reject a use case whose letter is not listed, or whose `context` does
  not match the name of its letter.
- With `areas` empty, any capital letter is accepted and `context` is free text.
- `actors` limits the allowed `actor` of a use case. Empty means any.
- `providers` limits the allowed `provided_by` values (an outside system that supplies a use case, so
  you do not build it). Empty means any.
- `id_prefix` (default `UC`) changes the use case prefix for the whole repo.

If the context map changes, the letters follow it, and a retired letter stays retired.

## 2. The ids

| Item | Prefix | Pattern | Area letter? | Example |
| ---- | ------ | ------- | ------------ | ------- |
| Functional requirement | `FR-` | `FR-<n>` | no, global | `FR-12` |
| Non-functional requirement | `NFR-` | `NFR-<n>` | no, global | `NFR-5` |
| Acceptance criterion | `AC-` | `AC-<n>` | no, global | `AC-12` |
| **Use case** | `UC-` | `UC-<area><n>` | yes | `UC-O1` |
| Task (a slice of a use case) | `TSK-` | `TSK-<UC>.<k>` | yes | `TSK-O1.3` |
| **Ontology object type** | `OBJ-` | `OBJ-<area><n>` | yes | `OBJ-P1` |
| **Rule that always holds** | `RULE-` | `RULE-<area><n>` | yes | `RULE-O2` |
| **Value set** (a fixed list) | `SET-` | `SET-<n>` | no, global | `SET-4` |

**Why some ids carry a letter and some do not.** A use case, an object or a rule belongs to one
area, so the letter makes it easy to find. Requirements and criteria cut across areas (one
requirement can serve several use cases), so they stay one global sequence. A global id never
pretends to one owner.

`FR-` is only for the functional kind. Quality, constraint and process requirements are all `NFR-`,
and the `kind` column says which one it is.

### Not the same as record ids

A running system also has ids for **data records**, such as `PROJ-<uuid>` or `ORD-<uuid>`. Those
belong to the product. The ids in this document name **documents and design items**. `OBJ-O1` is
the object type Order. `ORD-<uuid>` is one particular order.

## 3. Rules for numbering

1. **Prefix is the type, letter is the area, the number is a stable sequence.**
2. **Append only.** Never renumber on insertion. A retired id is retired, not reused. Retired use
   case ids are listed in `retired-ids.csv` (see [csv-files.md](csv-files.md)). The tool skips
   them when it hands out the next id and refuses a file that uses one.
3. The number runs **within the area** for area-coded ids, and runs globally for the rest.
4. **A new area gets a new letter.** Add it to `areas` in `vbench.json`.
5. **Ask the tool for the next number.** `req_tool.py next-ids` gives the next `FR-`, `NFR-` and
   `AC-`. `uc_tool.py next-id O` gives the next use case in area O.
6. An item may split, merge or be dropped without a numbering puzzle. A file may say where an item
   came from in `evolved_from` (for example `evolved_from: [old tracker UC-06]`).

## 4. Where the files go and how they are named

A file is named `<ID>-<slug>.md`, with a short lowercase slug that says what it is:
`UC-O1-place-an-order.md`. The default folders below can be changed under `paths` in `vbench.json`.

| Item | Default place |
| ---- | ------------- |
| `FR-`, `NFR-` | rows in `docs/requirements/requirements.csv` |
| `AC-` | rows in `docs/requirements/acceptance-criteria.csv` |
| `UC-` | `docs/usecases/` |
| `TSK-` (a slice of a use case) | a line inside its use case file, not a file of its own |
| Use case diagrams (`.puml`) | `docs/usecases/diagrams/` |
| `OBJ-`, `RULE-`, `SET-` | `docs/domain/ontology/` |

Requirements and criteria are CSV rows, not files. A folder is created when the first file in it is
written.

## 5. The file header

Every use case and ontology item is a Markdown file. The data is a **fenced `yaml` code block at
the very top of the file**, and the explanation is the prose below it. The tools read the first
`yaml` block in a file.

Why a code block and not front matter (the `---` lines): GitHub draws front matter as a **table**
in the preview, which is hard to read for nested data like links. A code block keeps the shape and
the indentation, and is coloured.

```yaml
id: UC-O1
type: use-case
name: Place an order
status: draft            # draft | accepted | retired
actor: member
context: Orders
satisfies:
  - id: FR-12
    reviewed: a1b2c3d    # written by the tool, see below
criteria:
  - id: AC-20
    reviewed: 4e5f6a7
objects: [OBJ-O1]
rules: [RULE-O1]
effects: [an order record is created]
```

**Common fields**

| Field | Meaning |
| ----- | ------- |
| `id` | The id from section 2. Must match the file name. |
| `type` | `use-case`, `object`, `rule` or `set`. |
| `name` | A short name in the domain's words. |
| `status` | `draft`, `accepted` or `retired`. A retired item keeps its file and its id. |
| `satisfies` | The upstream items this one serves. Each entry has an `id` and a `reviewed` hash. |
| `evolved_from` | Optional. Where the item came from before. |

**The `reviewed` hash.** It is a short hash of the upstream row's text at the time a person last
checked this item against it. The tool writes it (`uc_tool.py stamp UC-ID`). If the upstream text
changes, the hash no longer matches, and this item is **suspect** until it is reviewed. A change to
the `notes` column does not count.

**Use case fields.** These are checked by `uc_tool.py validate`.

- `id`, `type: use-case`, `name`, `status`.
- `actor`: who does it. Must be one of `actors` in `vbench.json` when that list is set.
- `context`: the context that owns it. Must match the name of the area letter in `areas`.
- `provided_by` (optional): outside systems that supply it, from `providers`. The use case is drawn
  differently, and you do not build it.
- `satisfies`: the requirements it serves, each with `id` and `reviewed`. It may not be empty.
- `criteria`: the acceptance criteria it runs, each with `id` and `reviewed`. A use case should list
  every criterion that proves a requirement it serves.
- `parameters`: what it is given.
- `objects`: the `OBJ-` ids it touches.
- `rules`: the `RULE-` ids it checks before it changes anything.
- `effects`: what it records or sends, such as an audit entry or a notification. It may not be empty.
- `flow_reviewed`: a hash of the flow a person wrote. The tool sets it. If the flow changes, the tool
  says **flow changed**.
- `evolved_from`: optional.

The body repeats the requirement and criterion text in a generated block, then the flow and its
slices, and later the analysis, the design and the change log between them. See
[usecases.md](usecases.md).

**Object fields**: `context`, `id_prefix` (the record prefix such as `ORD-`, or `none` for a part
with no id of its own), `comment` (one sentence), `properties`, `links`, `rules`, `questions`.

**Rule fields**: `object`, `statement`, `proved_by` (tests tagged `Verifies`, empty until there is
one).

**Set fields**: `values`, `meanings` (what each value means), `ordered` (true or false), `used_by`.

**Element ids inside a use case file** are local to the file: `A1`, `A2` for the elements of its
analysis and `D1`, `D2` for its design, append only. From outside they read `UC-O1/A3`. They are not
a new id prefix.

A **property** of an object has a `name`, a `type`, and optionally `required`, `many` and a
`comment`. The `type` is a scalar (`text`, `number`, `date`, `boolean`, `map of text`), the id of a
value set (such as `SET-1`), or the name of another object.

A **link** reads as a sentence: `domain`, `property`, `range` (for example "Project has Order"),
with `cardinality` (`one-to-one`, `zero-or-one`, `one-to-many`, `many-to-one` or `many-to-many`) and
`kind`: `part` (it lives inside the domain object) or `reference` (it points at another object by
id). A link is **defined once, in the file of its domain object**. A file may also show a link it is
only part of, by adding `defined_in` with the owning file's id, and a check confirms the two agree.
A link marked `planned: true` points at an object that is not a file yet.

`questions` is a list of **competency questions**: plain-language questions the item helps answer.
If a question cannot be answered by walking the files, the model is missing something.

**One YAML trap.** `yes`, `no` and `n/a` can be read as true, false or nothing by some parsers. If
your answer choices are literally Yes, No and N/A, always write them in quotes (`"Yes"`, `"No"`,
`"N/A"`).

## 6. Linking code and tests

Code and tests are not files with a header. They link by a **tag** in a comment or a test name:

- Code is tagged `Realises UC-O1`.
- A test is tagged `Verifies UC-O1`, or `Verifies AC-12` when it executes one acceptance criterion.
  An acceptance test also records the criterion as it was last checked:
  `Verifies AC-12 [reviewed 7a2439b]`. The hash is the same short fingerprint of the criterion's
  given, when, then and test level that a use case keeps. If the criterion changes, the test is
  **stale** until a person checks it again. `at_tool.py` reports this and stamps it
  (`at_tool.py stamp AC-12`).

`at_tool.py` scans the test folders (`tests_dirs` in `vbench.json`, default `tests/acceptance`) for
the `Verifies AC-<n>` tags. So a criterion shows which tests point at it, and one with no tag shows
up as untested. A use case that lists a criterion with no test shows up too.
