---
name: vbench-puml
description: Write, restyle or check a PlantUML (.puml) diagram in this repo: a context map, a domain model (aggregates, entities, value objects, events), an object map, a hexagon, a use case diagram or a relational ER. Follows the project's PlantUML standard: shared _style.puml, DDD context-map notation (Customer/Supplier, ACL, Open Host Service, shared kernel), portrait A4 page, with a script that renders and measures every diagram. Use this whenever the user asks for a puml or PlantUML diagram, a context map, a domain model diagram, "restyle the puml", "does this fit A4", or edits anything under a diagrams/ folder, even if they never say "vbench". Use vbench-diagrams first if it is not clear that PlantUML is the right format.
---

# vbench-puml

Standalone, reference-quality diagrams: a context map, a domain model, an object map, a
hexagon, an ER. They are too big or too precise for Mermaid, or someone will open, print or
quote them on their own. Small inline diagrams are Mermaid: use `vbench-mermaid`.

The standard is in `_vbench/standards/diagrams.md` and the look is in the repo's `_style.puml` (usually
`docs/domain/diagrams/_style.puml`). If the repo has none yet, copy `_vbench/templates/_style.puml` and
`_legend.puml` next to the first diagram. If a rule changes, change those, not this file.

The notation is the usual DDD one: a shared style file
included by every diagram, a colour key for the DDD building blocks, DDD integration
patterns written on the relationships, a status in each title, and honest comments about
what is not drawn. The look is in `_style.puml`; edit that file to change it for every diagram.

## Step 1: Say the one idea, and fit one page

Write one sentence: "This shows ___". If it needs "and", make two diagrams. Aim for about
12 boxes or fewer. Leave out arrows that repeat on every box (every context writing to
Audit) and say so in a note.

**Every diagram fits one portrait A4 page**: taller than wide, at most 180 x 267 mm at its
drawn size. Use `top to bottom direction`, keep box text to about 20 characters a line, and
put long words in a note or the legend. A diagram too big for a page is too big to
understand. If it does not fit, split it and repeat the shared boxes as plain boxes. Never
shrink it: text stays about 10 pt on paper whatever the dpi setting, so only the layout
can fix a wide diagram.

Use the project's words (the names in the ontology, `docs/domain/ontology/`). No em or en dashes. Do not invent
terms or id prefixes.

## Step 2: Start the file the same way every time

```
@startuml context-map
!include _style.puml
title <Product> context map (draft)
```

- The name after `@startuml` equals the file name, lowercase with hyphens, and says what is
  shown: `context-map.puml`, `object-map-orders.puml`.
- One folder `diagrams/` beside the documents that use it. Rendered images are not
  committed.
- `_style.puml` has no `@startuml`: it is only included. Do not copy colours into a diagram.
  Give a box a role with a stereotype and the style does the rest.
- Put the status in the title or a note: "draft", "target", "built", "planned". A reader
  must not take a target for something that exists.
- Start with a comment block saying what the diagram shows, what is **not** drawn, and why.
  It is the most useful habit to keep.

## Step 3: Colour roles (set with a stereotype)

| Stereotype | Use for | Look |
| ---------- | ------- | ---- |
| `<<core>>` | What the product exists for | White, bold charcoal border |
| `<<supporting>>` | The work around the core | Off-white, soft border |
| `<<generic>>` | Things any product needs | Light grey, muted text |
| `<<reference>>` | Read only knowledge | Dashed border |
| `<<kernel>>` | A shared kernel | Grey, solid border |
| `<<external>>` | A system we do not own | Grey, dashed, drawn as a `cloud` |
| `<<ai>>` | Anything an AI produced | Purple, AI content only |
| `<<human>>` | What a person wrote | Yellow, human content only |
| `<<aggregate>>` | An aggregate boundary (a package) | Pale blue |

Role stereotypes are hidden. They only set colour, so every role also differs by border
style or shape, and the legend names them. Never rely on colour alone.

Hierarchy comes from weight and position first, and colour has one job. Do not add hues.

**Always light mode.** Diagrams are drawn on a white background with dark text. `_style.puml`
sets `backgroundColor #FFFFFF`. Do not use `!theme` or a dark palette, so a rendered or printed
diagram looks the same everywhere.

## Step 4: Context maps (strategic)

Show the **relationship** on every line, in DDD words. A bare arrow says
"they touch" and nothing more.

| Write | Means |
| ----- | ----- |
| `Customer / Supplier` | The downstream side asks and the upstream side plans for it |
| `Conformist` | The downstream side takes what upstream gives and cannot ask for more |
| `Open Host Service` | The upstream side offers a published interface to many |
| `ACL` | An anti-corruption layer: we translate an outside system so its words stay out |
| `shared kernel` | A small model two contexts share and change together |
| `Published Language` | A documented format used between them |

Line style: a solid arrow for a direct dependency, a dashed arrow for something through a
port, a kernel or an ACL. Name the port on the arrow when it helps (`ChecklistProgress`).
Draw external systems as `cloud ... <<external>>` and join them through an ACL.

```
package "Core" {
  rectangle "Orders" as ORD <<core>>
  rectangle "Billing" as BIL <<core>>
}
cloud "Payment provider" as PP <<external>>
ORD --> BIL : Customer / Supplier
ORD ..> PP : ACL
```

References between contexts are **by identity only**. Say so in a note if it is not
obvious.

## Step 5: Domain models (tactical)

One diagram per context. Use the four DDD building blocks, and include the colour key:

```
!include _style.puml
!include _legend.puml

package "aggregate\nEvaluation" <<aggregate>> {
  class Evaluation <<root entity>> { status }
  class SmokeTest <<entity>>
  class Verdict <<value object>>
}
```

- Stereotypes `<<root entity>>`, `<<entity>>`, `<<value object>>`, `<<domain event>>` are
  shown, because they name the block in words as well as colour.
- Leave method parameters out. The model shows parts, boundaries and language. Signatures
  live in the code.
- Domain services and repositories are not building blocks here, so do not tint them.
- Show only what is built, or mark the rest "planned".

## Step 6: Check it, then look at it

```bash
python3 .claude/skills/vbench-puml/scripts/check_diagrams.py <diagrams folder or file>
```

The script renders each diagram to a temporary folder and checks that it parses and fits
portrait A4. It prints each size in millimetres and fails on a landscape, too wide or too
tall diagram. It needs Java and the PlantUML jar (the VS Code PlantUML extension ships one;
set `PLANTUML_JAR` for another). Passing means the shape is right, not that it looks right,
so also render a PNG into the session scratchpad (never the repo) and read it:

```bash
J=$(ls ~/.vscode/extensions/jebbs.plantuml-*/plantuml.jar | head -1)
java -Djava.awt.headless=true -jar "$J" -tpng -o <scratch folder> <file>.puml
```

Check: is the one idea clear in five seconds? Do lines cross labels or titles? Is any text
cut off or tiny? Is each role used for its one job? Does the legend explain every line and
fill? Fix and render again. Stop after a few rounds and say what is still not perfect. If
Java or the jar is missing, say the diagram was not rendered.

## Step 7: Finish

- Link the `.puml` from the document that uses it and add it to the table in
  `_vbench/standards/diagrams.md`.
- If the same thing exists as inline Mermaid, keep both only for a reference diagram (a
  context map, an object map). The `.puml` is the source, the Mermaid copy may be simpler,
  each links to the other, and both change in the same commit. Otherwise remove the copy.
- Do not commit unasked. Offer a `docs` commit through `vbench-commit`.

## What not to copy from older diagrams

Long orthogonal lines that cross titles and boxes, grey label boxes that hide the line,
serif fonts, saturated fills that make everything equally loud, and no legend. If a map
needs `linetype ortho` to be tidy, it probably has too many lines.

## Use case diagrams

The files live in `docs/usecases/diagrams/` (the `usecases` path in `vbench.json`). Starter copies of the two shared
files are in `_vbench/templates/` (`_usecase-style.puml`, and an example `_usecase-actors.puml` to extend with one
block per actor):

- `_usecase-style.puml`: the look (coloured actors, `actorStyle awesome`, ortho lines, a pastel box for each
  context) and the status fills, `COLOR_BUILT` (green) and `COLOR_TODO` (grey).
- `_usecase-actors.puml`: one block for each actor, so a diagram includes only the actors it draws.
- `usecases-<context>.puml`: one standalone diagram for each context. Landscape, about 3:2
  (`' page: landscape`). A context with more than about nine use cases is split in two (for example
  `usecases-orders.puml` and `usecases-orders-fulfilment.puml`). The ovals are grouped by the actor who
  starts them, and the actors stand in the same order, so the arrows stay short.
- `usecases-overview.puml`: the **composite**. It embeds every context file, so it is the sum of them.

**The composite uses `!includesub`.** In a context file, `!startsub BOX` wraps the context box with its
ovals, and `!startsub LINKS` wraps its arrows. The context file draws fine on its own. The overview
includes each box and each links block with `!includesub usecases-<context>.puml!BOX` and `!LINKS`, and
`!define OVERVIEW` switches on the links that cross contexts (they sit in `!ifdef OVERVIEW`, so a standalone
file never draws a stray oval for another context). An actor is declared once, behind a guard
(`!ifndef ACTOR_<name>`). The overview says `' page: overview`, so the checker parses it and does not fit
it to a page.

**Notation.** Each oval is `UC-<area><n>` and the name, filled green if built and grey if not (or if no
requirement exists yet). A use case that evolved from an earlier one says so in the comment above it. `[norank]`
on a link between use cases stops it adding a column. A grid is built with hidden links
(`-[hidden]right->` along a row, `-[hidden]down->` between rows). The ids in these diagrams are the reserved
numbers: the first use case files must use them.

**Generated later.** `uc_tool.py diagram CONTEXT --write` writes a context file in this same look from the use
case files, and `diagram overview --write` writes the composite. It will not replace a hand-kept file (one
without the `Generated by vbench-uc` line) unless told to with `--force`.
