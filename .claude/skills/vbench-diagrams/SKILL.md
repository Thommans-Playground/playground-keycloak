---
name: vbench-diagrams
description: Decide how to draw a diagram in this repo, and hand off to the right skill. Mermaid inline in markdown is the default; PlantUML (.puml) files are for diagrams too big or too precise for Mermaid, or opened on their own. Use this whenever the user asks for a diagram, "draw this", "add a diagram to this doc", "which format for this diagram", "should this be a puml", or an explainer describes a flow, lifecycle, structure or who-talks-to-whom in words, even if they never say "vbench", "Mermaid" or "PlantUML". Then use vbench-mermaid or vbench-puml for the style and the checks.
---

# vbench-diagrams

Choose the format, then use the skill for it. This file holds only the choice and the rules
both formats share. The standard is in `_vbench/standards/diagrams.md`. If a rule changes, change that,
not this file.

The user is learning the design to explain it and guide a team. A diagram earns its place
when it makes a relationship, a flow or a lifecycle easier to see than a paragraph would.

## Pick the format

Start with Mermaid. Move to PlantUML only when Mermaid cannot do the job. Ask two questions
in order:

1. **Can Mermaid draw it properly?** If it comes out cramped or tangled, or you cannot
   control the layout, it is not a Mermaid diagram.
2. **Would anyone open it on its own?** A reference we keep, print or quote is a `.puml`.
   A picture that only helps one paragraph stays inline.

| The diagram is | Format | Skill |
| -------------- | ------ | ----- |
| Small, explains the words around it (a flow, a sequence, a state machine, a short ER sketch) | Mermaid, inline in the markdown | `vbench-mermaid` |
| Too big or too precise for Mermaid, or a reference opened on its own (context map, domain model, object map, hexagon, **use case diagram**) | PlantUML, in a `diagrams/` folder | `vbench-puml` |
| The flow of one use case (who does what, in order) | Mermaid sequence diagram, inline in the use case file | `vbench-mermaid` |

If both answers say "Mermaid is fine, nobody opens it alone", do not make a `.puml` file.

**Do not draw the same thing twice, with one exception.** By default a diagram lives in one
form. A **reference diagram** (a context map, an object map) may have both: the `.puml` is the
printable A4 source, and an inline Mermaid copy is the reading version. Link each to the
other, and change both in the same commit. A small diagram that only helps a paragraph never
gets a `.puml` copy, and a `.puml` that adds nothing over its Mermaid version should go.

## Rules for both

- **One idea.** Write "This shows ___". If it needs "and", make two diagrams.
- **Small.** About 12 boxes or fewer. Leave out arrows that repeat on every box and say so
  in a note.
- **Say what a line means.** Write the relationship on it (for example `Customer / Supplier`,
  `ACL`), or explain it in a legend.
- **Never colour alone.** Every colour also has a word, a border style or a shape.
- **Project words.** Use the names in the ontology (`docs/domain/ontology/`). Do not invent terms.
- **No em or en dashes** in labels, titles or notes.
- **Say what is built.** Mark a target as "draft", "target" or "planned".
- **A reading guide** of one or two lines goes under every inline diagram.

## After drawing

Check it with the skill for its format, and look at the result. A diagram that parses can
still look wrong. Do not commit unasked. Offer a `docs` commit through `vbench-commit`.
