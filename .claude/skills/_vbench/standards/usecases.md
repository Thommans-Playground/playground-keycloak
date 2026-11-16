# Use cases

A use case is **one thing one person does to reach one goal**, written as steps. It is the unit we
plan, build and test. It comes after the requirements and their acceptance criteria, and it is where
the criteria are run.

## Where things live

Default places. `paths` in `vbench.json` can change them.

| What | Where |
| ---- | ----- |
| Requirements and acceptance criteria | `docs/requirements/` (the two markdown files, see [requirements.md](requirements.md)) |
| Use cases | `docs/usecases/`, one file each: `UC-<area><n>-<slug>.md`, for example `UC-O1-place-an-order.md` |
| Slices (the thin pieces of a use case, one card each) | a line inside the use case file, with an id like `TSK-O1.1` |
| Use case diagrams | `docs/usecases/diagrams/`, one `.puml` for each context and an overview |
| Objects, rules, value sets | `docs/domain/ontology/` |
| Retired use case ids | `docs/usecases/retired-ids.csv` |

The area letter is the context that owns the change. It is defined in `vbench.json` under `areas`.
The ids are in [naming-conventions.md](naming-conventions.md).

## How a use case file is built

The data is a fenced `yaml` block at the top. Under it comes a block copied from the requirements files, then
the part a person writes.

1. **Header** (`yaml`): `id`, `name`, `status`, `actor`, `context`, the requirements it serves
   (`satisfies`), the acceptance criteria it runs (`criteria`), `parameters`, `objects`, `rules`,
   `effects`, and the review hashes. The fields are in [naming-conventions.md](naming-conventions.md),
   section 5.
2. **A generated block**: the full text of every requirement it serves and every criterion it runs
   (Given, When, Then), and how it is verified. A reader does not have to remember an id. It is
   copied from the requirements files by `uc_tool.py sync` and is never edited by hand.
3. **The flow**, written by a person: Description, Preconditions, Main flow, Other flows,
   Postconditions, Slices, and Not in this use case.
4. **Analysis, design and the change log**, added as the use case is worked (see "Analysis, design,
   and what changed between them" below): the sections `Analysis`, `Design` and `Changes from
   analysis to design`. They come after the slices and are kept out of the flow's hash.

Every line of the main flow ends with the requirement it serves, such as `(FR-88)`. Every other flow
(a refusal or an edge case) ends with the criterion that proves it, such as `(AC-12)`.

## Links go both ways, each fact has one owner

| Direction | Signal |
| --------- | ------ |
| A requirement or criterion changes | The use case is **suspect**, until a person reviews it and stamps it. Each pointer carries a hash of the row as it was reviewed. A change to `notes` does not count. |
| The flow changes | The use case says **flow changed**. `check-upstream` lists what the requirements and criteria may be missing: a step with no requirement, an other flow with no criterion. |

The requirements files own the wording of requirements and criteria. The use case owns the flow. Nothing is
copied upward: the tool proposes, and a person accepts the edit through the requirements skill.

## How a use case is verified

By acceptance tests that run its flow, usually through the API or the outermost interface. Each
acceptance criterion it lists becomes a test tagged `Verifies AC-<n>`. A use case with no criteria
listed has nothing that verifies it. The criterion belongs to the requirement, and the use case is
where it is run. `at_tool.py` reports a criterion with no test, a test that names a criterion that
does not exist, a test that is stale because its criterion changed, and a use case that lists a
criterion with no test.

## Slices

A slice is a thin piece of the use case that works end to end and can be tested on its own. It
becomes one card of 1 to 2 days. A slice names the criteria it proves and the rules it carries. A
rule goes in the **first slice that needs it**, not in a later hardening slice.

## Edge cases

An edge case appears once as a one-line other flow in the use case, with its criterion tag. The full
expected result is the acceptance criterion. A fact that always holds is a rule in the ontology.

## Analysis, design, and what changed between them

A use case is worked in this order. The first two records are kept apart so that nothing in the
analysis is lost on the way to the design.

| Step | Record | Test that proves it |
| ---- | ------ | ------------------- |
| 1. Flow | the use case file (above) | the acceptance criteria |
| 2. Analysis | the **Analysis** section: a sequence diagram of the flow and a list of its elements | the acceptance test |
| 3. Ontology | the objects, rules and actions the analysis revealed, updated through `vbench-ontology` | unit tests, one for each rule |
| 4. Design | the **Design** section: a class diagram with aggregates, value objects, ports and adapters, and a list of its elements | integration tests on the adapters |
| 5. Change log | the **Changes from analysis to design** section | none: the tool checks it |
| 6. Tasks | the slices, each one card | unit inside, acceptance outside |

**Elements.** Each element of the analysis (an object, a step, a rule, a port) is a line
`A1 (object): Order`, and each element of the design is `D1 (aggregate): Order`. The ids are local to
the file and append only, and from outside they read `UC-O1/A3`. No new id prefix.

**Analysis is frozen.** `uc_tool.py freeze UC-ID` records a hash of each analysis revision. An edit
to a frozen revision is reported. To correct the analysis, add a `### Revision 2` that says what
changed. Revision 1 stays as it was.

**The change log.** Every analysis element must be accounted for. A line says what became of it:

- `A1 kept -> D1`
- `A2 became -> D2: matches the target snapshot`
- `A3 renamed -> D3`, `A4 moved -> D4`, `A5 split -> D5, D6`, `A6 merged -> D7`
- `A7 dropped: the aggregate does not look orders up` (a reason is required, and no design element)
- `+ D8 added: the audit trail needs it` (a design element with no analysis source)

`uc_tool.py validate` refuses an analysis element that appears in no line (it is **lost**), a design
element with no source, a dropped element with no reason, and a line that points at an element that
does not exist. `uc_tool.py trace UC-ID` shows each analysis element and what became of it. An
ontology change that causes a design change is a reason like any other: write "ontology: ..." in the
line.

The three sections are kept out of the flow's hash, so editing the design is not a change to the
flow.

## The chain of skills

Three skills hand work on in a line: **vbench-req** writes the requirements and their acceptance
criteria, **vbench-uc** writes the use case that runs them, and **vbench-at** turns each acceptance
criterion into an acceptance test and checks that the two stay linked. Each ends by offering the
next, and each sends a problem back: a vague or wrong criterion goes back to vbench-req, which is
the only skill that edits the requirements files.

## What the tool checks

`uc_tool.py validate` refuses a use case file when:
- the id is not `UC-<area><n>`, does not match the file name, is a duplicate, or is retired,
- the area letter is not in `areas`, or its `context` does not match the name of that letter,
- `type` is not `use-case`, or `status` is not `draft`, `accepted` or `retired`,
- `actor` is missing or not in `actors`, or a `provided_by` value is not in `providers`,
- `satisfies` is empty, or names a requirement that does not exist,
- `criteria` names a criterion that does not exist,
- an entry in `satisfies` or `criteria` has no `reviewed` hash,
- `objects` or `rules` are not `OBJ-` and `RULE-` ids, or `effects` is empty,
- the slices or the change log are wrong (see above).

It also reports notes: a use case is suspect, its flow changed, its copied text is out of date, an
object or rule has no ontology file yet, or it does not list a criterion that proves a requirement
it serves.

## Tooling

The `vbench-uc` skill and its script `uc_tool.py` search, report the impact, check, write, stamp,
freeze and trace use case files, and draw the use case diagram of a context from the files
(`diagram`). Its commands are in the skill.

## The diagrams

Use case diagrams are PlantUML, a **composite** (see [diagrams.md](diagrams.md)): one standalone file
for each context and an overview that embeds them all. `uc_tool.py diagram <context> --write` writes
a context file, and `diagram overview --write` assembles the composite. Green is built, grey is not
built or has no requirement yet, and blue is provided by an outside system. A file kept by hand is
not overwritten unless told to (`--force`).
