# Diagrams: Mermaid inline, PlantUML for files

Two formats. **Start with Mermaid.** Move to PlantUML only when Mermaid cannot do the job.

| Format | Use it when |
| ------ | ----------- |
| **Mermaid**, inline in markdown (a `mermaid` code block) | Mermaid can draw it properly, and the diagram has no value on its own. It explains the words around it: a small flow, a sequence, a state machine, a short ER sketch. GitHub and VS Code draw it with no tools, and it stays next to the text. |
| **PlantUML**, its own `.puml` file | The diagram is too big or too precise for Mermaid (a context map, an object map, a hexagon, a use case diagram), or it is a **reference** someone opens on its own, prints or puts in a report. |

## When to use which

Ask two questions, in this order:

1. **Can Mermaid draw it properly?** If it comes out cramped, tangled, or you cannot control the
   layout, it is not a Mermaid diagram.
2. **Would anyone open it on its own?** A reference we keep, print or quote is a `.puml` file. A
   picture that only helps one paragraph stays inline.

If the answer to both is "Mermaid is fine, nobody opens it alone", keep it inline. Do not make a
`.puml` file for it.

**Do not draw the same thing twice, with one exception.** By default a diagram lives in one form.
The exception is a **reference diagram** (a context map, an object map): it may have a `.puml` as
the printable A4 source for reports, and an inline Mermaid copy as the reading version in the
document. When both exist:

- The `.puml` is the source. The Mermaid copy may be simpler.
- Each one links to the other.
- Change both in the same commit, so they do not drift.

A small diagram that only helps a paragraph never gets a `.puml` copy.

## Use case diagrams

A **use case diagram** shows the actors and the use cases each can start, inside a system boundary,
one box for each context. Mermaid has no real use case diagram, so these are **PlantUML**, in
`diagrams/` under the use case folder (default `docs/usecases/diagrams/`).

They are a **composite**: one standalone file for each context (a context with more than about nine
use cases is split in two), landscape and about 3:2 so it reads on a laptop, and one overview that
embeds them all with `!includesub`. The overview is for the screen and is not fitted to a page. The
pattern is in the `vbench-puml` skill.

`uc_tool.py diagram <context> --write` draws a context file from the use case files (their `actor`,
`context` and the requirements they serve). `uc_tool.py diagram overview --write` assembles the
composite. A use case is green when every requirement it serves is built, grey when not, and blue
when it is provided by an outside system (`provided_by`). The tool refuses to overwrite a file kept
by hand unless told to (`--force`). Names and colours of actors and contexts can be set under
`diagram` in `vbench.json`.

The **flow of one use case** is a different diagram. It stays Mermaid, inline in the use case file,
as a sequence diagram under "Main flow", and only when it helps.

## Where the files go

- Standalone diagrams sit in a `diagrams/` folder beside the documents that use them, for example
  `docs/domain/diagrams/`.
- Name files in lowercase with hyphens, and make the name say what the diagram shows:
  `context-map.puml`, `object-map-orders.puml`.
- Share the look through `_style.puml`. Start every diagram with `!include _style.puml`.
- Start each diagram with `@startuml <same name as the file>` and a `title`.
- Rendered images (`.png`, `.svg`) are **not committed**. The `.puml` is the source.

## Page size: portrait A4

Every standalone diagram must fit one **portrait A4 page** (a use case diagram is the exception,
below), so it can be printed, put in a report or read on a phone without zooming.

- **Taller than wide.** Flow top to bottom (`top to bottom direction`).
- **At most 180 x 267 mm** at the size it is drawn. That is A4 (210 x 297 mm) with a 15 mm margin.
  The font stays about 10 pt on paper, because the size is not scaled down.
- **If it does not fit, split it.** Do not shrink it. A diagram too big for a page is too big to
  understand. Repeat a shared box in each part (as a plain box) so each part stands alone.
- **Shorten the text in boxes** (about 20 characters a line) and put long explanations in a note or
  the legend. Group repeating arrows into one note.
- Mermaid diagrams inline in markdown follow the page they sit on. Keep them narrow too. Inline
  diagrams are exempt from the A4 check, but a wide one is a sign it needs to be split or moved to
  a `.puml`.

**Exception: use case diagrams are landscape, about 3:2.** Actors in a row on top and the use cases
in a grid below, at most 267 x 180 mm (A4 landscape with a margin) and no wider than 1.65 to 1. Put
the line `' page: landscape` in the file so the check expects it. A composite overview for the screen
says `' page: overview` and is only parsed. They are read on a laptop screen, where a thin portrait
diagram shrinks to nothing.

Check it with the script, which renders each file and measures it:

```bash
python3 .claude/skills/vbench-puml/scripts/check_diagrams.py docs/domain/diagrams
```

It prints each diagram's size in millimetres and fails if one is landscape (when it should not be),
too wide or too tall, or if PlantUML cannot parse it.

## The look

The two formats have their own style, held in their own skills. Read the skill, not a copy.

| Format | Style | Where it is written down |
| ------ | ----- | ------------------------ |
| **Mermaid**, inline | Plain Mermaid: no config, theme, colours or card. The viewer draws it in its own theme, so it stays readable in light and dark. Domain-driven design relationship words on the lines | the `vbench-mermaid` skill |
| **PlantUML**, standalone | Calm grey surfaces, hierarchy from weight and border, one colour per job. Domain-driven design notation: building-block colours, integration patterns on the lines, a status in each title | the `vbench-puml` skill and the shared `_style.puml` |

Rules that hold for both:

- **Mermaid is left plain** (no config, theme, colours or white card). GitHub can paint a black
  frame behind a diagram even on a white page, and a forced light theme then draws dark lines on
  black. The viewer's own theme avoids that. A diagram that must look the same everywhere, or
  print, is a `.puml`.
- **PlantUML is light mode only**: a white background and dark text, set in `_style.puml`.
- Hierarchy comes from weight and position first. Colour carries meaning and has one job.
- Never rely on colour alone. A zone has a title, a role has a border style or shape, and a line
  carries its relationship in words.
- Write the relationship on a line (`Customer / Supplier`, `ACL`, `shared`), not a bare arrow.
- Use the project's words (see the ontology) and the product's name.

The inline and standalone styles look different on purpose: Mermaid takes the viewer's theme, and
PlantUML follows its own design with a white background.

The `vbench-diagrams` skill picks the format and hands off to the right one.

## Writing them

- One idea per diagram. If it needs more than about 12 boxes, split it. It must also fit a portrait
  A4 page (see above), except a use case diagram, which is landscape.
- Say what a line means: label it, or add a legend.
- Leave out repeating lines (every context writing to an audit log) and say so in a note.
- Use the project's words. No em or en dashes in labels.
- Mark what is not built. A diagram of a target says "draft" or "target" in its title.

## Checking and viewing

- In VS Code, the PlantUML extension (`jebbs.plantuml`) previews a file with Alt+D.
- To check syntax and page size from a terminal, use the script in "Page size" above. It needs Java
  and the PlantUML jar, which ships with the VS Code extension (set `PLANTUML_JAR` to use another).
  Some diagram types also need Graphviz (`dot`).
