# The dashboard

A read-only guide to a vbench project, for people who did not build it. They start at the V, click a requirement, a
criterion or a use case, and follow the links down to the design, the code and the test that proves it. It has no rules
of its own: it shows what `vbench export` computes, so it cannot disagree with `vbench status`. The CLI's verdicts never
depend on it.

## Run it

```bash
PROJECT=$PWD/examples/notes-app docker compose up --build   # then open http://localhost:3100 (PROJECT defaults to .)
docker compose down
```

The project is mounted read-only, the app runs as a non-root user on a read-only filesystem, and the port is published on
`127.0.0.1` only. A PlantUML renderer runs beside it (no published port) and draws the `.puml` diagrams; without one the
server answers 503 for a diagram and the page shows the source. Docker builds the UI in a Node stage, so no Node is needed
on the host. Refresh the page after you change a file.

Without Docker: `vbench serve` in a project serves the API on `http://127.0.0.1:3100`, and
`cd src/vbench/ui && npm install && npm run dev` runs the UI with hot reload against it (set `VBENCH_PLANTUML_URL` to a
renderer for diagrams).

## What it shows

The sidebar is the V-cycle itself: **Requirements, System design, Architecture, Module design** (the left arm),
**Code** (the vertex) and **Unit, Integration, System and Acceptance tests** (the right arm). Each phase lists what the
project holds there (for unit tests, the individual test functions with their file, use case and criteria), and clicking
an item shows the V it belongs to: its use case's whole V, the item outlined, and a dashed line to the test level that
proves it or the specification it proves. The Overview adds statistics and a V with a count on every phase. The data
comes from `vbench export` (`domain/vview.py`); tests are indexed per function for Python and per file for other
languages.

Clicking anything opens a record: a header card with facts, then the items it links to. The breadcrumb is the lineage of
the page (problem, request, requirement, use case, criterion, test), so a newcomer can always see where they are.

## Safety

`vbench serve` only answers GET and HEAD (anything else is 405), keeps requests inside the docs and specs folders, and
rejects non-loopback `Host` headers unless `VBENCH_ALLOWED_HOSTS` lists them.

The look follows [`src/vbench/ui/DESIGN.md`](../src/vbench/ui/DESIGN.md): what was adopted and what was deliberately left
out.
