# The optional dashboard, the write path and the MCP server

These sit on top of the CLI and are not needed to use it. The CLI's verdicts never depend on them.

## Dashboard

A read-only, visual view of a vbench project: the next step, each use case's stage on the V-cycle, the build-order
graph, the traceability tables, the rendered diagrams and the docs. It has no rules of its own: it shows what
`vbench export` computes, so it cannot disagree with `vbench status`.

The first version of vbench is the CLI and the skills. The dashboard is a separate, optional install that runs in Docker;
the CLI package does not carry it, and nothing in the CLI needs it. From a checkout of this repo:

```bash
PROJECT=/path/to/your/project docker compose up --build   # then open http://localhost:3000 (PROJECT defaults to .)
docker compose down
docker compose --profile write up --build                  # also lets it edit the requirements, on http://localhost:3001
```

The project is mounted read-only; the `write` profile mounts it read-write and runs `serve --write` (experimental: it
previews, applies and commits documentation changes on your branch, and refuses the default branch). Ports are published
on 127.0.0.1 only, and a PlantUML renderer for the diagrams runs beside it with no published port. Docker builds the
dashboard in a Node stage, so no Node is needed on the host. To try it on the bundled example: `PROJECT=$PWD/examples/notes-app`.

The sidebar is the V-cycle itself: **Requirements, System design, Architecture, Module design** (the left arm),
**Code** (the vertex) and **Unit, Integration, System and Acceptance tests** (the right arm). Each phase lists what the
project holds there (for unit tests, the individual test functions with their file, use case and criteria), and
clicking an item shows the V it belongs to: its use case's whole V, the item outlined, and a dashed line to the test
level that proves it or the specification it proves. The Overview adds statistics and a V with a count on every phase.
The data comes from `vbench export` (`domain/vview.py`); tests are indexed per function for Python and per file for
other languages.

Two containers: the app (the React UI served by `vbench serve`) and a PlantUML renderer that only the app can reach.
The project is mounted read-only, the app runs as a non-root user on a read-only filesystem, and the port is published
on `127.0.0.1` only. Refresh the page after you change a file.

To work on the dashboard itself: `vbench serve` in a project serves the API on `http://127.0.0.1:3000`, and
`cd src/vbench/ui && npm install && npm run dev` runs the UI with hot reload against it (diagrams need
`VBENCH_PLANTUML_URL` pointing at a renderer, or show their source). The stack is Vite, React, TypeScript, Tailwind v4 and shadcn-style components, styled after the AGIL
Secure Shield console language: see [`src/vbench/ui/DESIGN.md`](src/vbench/ui/DESIGN.md) for what was adopted and what was deliberately left out.
`vbench serve` only answers GET, keeps requests inside the docs and specs folders, and rejects non-loopback `Host`
headers unless `VBENCH_ALLOWED_HOSTS` lists them.

### Changing the requirements from the dashboard

`vbench serve --write` (run it on your machine, not in Docker, so git works) adds a **+ Add** button to each table
and Edit, Delete and "Add request for this problem" on each record. A change goes through three steps and nothing is
written before the second: it is **previewed** (the exact diff, the problems found, and the *blast radius*: what else it
touches, up toward the problem and down toward the tests), then **applied** (only if the files are still exactly what
was previewed; the generated docs are regenerated and the checks re-run), then **committed** only if you press Commit
(just those files, as `chore: …`). Links inside the requirements doc are cleaned up for you: deleting a request removes
it from the requirements that satisfied it, and what it leaves with nothing above it is flagged. Anything in a spec, a
criterion or a test is flagged "read again", never edited. Writing needs the session token the page fetches, a
same-origin request, a JSON body under 64 KB and a branch that is not the default one (`--allow-default-branch` lifts
that); without `--write` the server is read-only as before.

**Actions are one three-dots button.** Each row of the requirements tables ends with a quiet `…` (and each record's header
has the same one); it opens a menu, so nothing else is drawn on the page. Its *Add* group depends on the row: a problem
adds a *request*; a request adds a *functional* or *quality* requirement; a requirement adds a *use case* that realises it
and a *criterion* (shown disabled, with the reason, until it has a use case); a use case adds a *criterion*. Its *Change*
group has *Edit* and *Delete*. The link back is already filled in. A criterion is written into its use case's spec, filling
the scaffold's `TBD` row when there is one; a use case is the file `vbench new uc` writes, naming the requirements it
realises. Both can only be added here: to change one, edit its spec. The preview warns that `vbench check acs` fails until a
test carries the new criterion's id, because it will. The menu is the shadcn dropdown (Base UI variant) and is not drawn at
all without `--write`.

**"Does this already exist?"** The add form has this check, and so do the buttons on each row (a problem's *Add request*, a
request's *Functional* and *Quality*), so an entry is written where it belongs. The word-overlap check is free and local
and always there. With `--agent claude` an agent reads the new entry beside the entries it might repeat (the ones it links
to and the nearest by wording, never code, specs or tests) and says whether it is new, already exists, partly written or a
narrower version, naming the entries and why; *Edit it instead* jumps to the one that exists. It advises and writes
nothing. It needs `pip install "vbench[agent]"` (the official Anthropic SDK, loaded only then) and credentials
(`ANTHROPIC_API_KEY` or `ant auth login`); `--agent-model` picks the model (default `claude-opus-5-5`). It sends the new
entry and those entries to Anthropic, only when you press the button, and the server says so when it starts. If the
agent is not set up, refuses, or fails, the word-overlap answer is shown with the reason.

## Use vbench from Claude Code through Docker (MCP)

vbench can run as a container that Claude Code talks to over the Model Context Protocol, so nothing is installed on the
host but Docker. `vbench mcp` speaks MCP on stdin and stdout and offers the project's operations as tools.

```bash
docker build -t vbench .                              # once, from this repo (add --build-arg EXTRAS=agent for the SDKs)

# in the project you want Claude Code to work on; $(id -u) and the git identity are filled in when you run this:
claude mcp add vbench -- docker run -i --rm --user "$(id -u):$(id -g)" \
  -e GIT_AUTHOR_NAME="$(git config user.name)" -e GIT_AUTHOR_EMAIL="$(git config user.email)" \
  -e GIT_COMMITTER_NAME="$(git config user.name)" -e GIT_COMMITTER_EMAIL="$(git config user.email)" \
  -v "$PWD:/project" vbench mcp --write
```

Leave out `--write` for a server that can only read. Without Docker the same server is `claude mcp add vbench -- vbench mcp`.

**The tools.** Reading is always on: `project_overview`, `get_use_case`, `get_item`, `impact`, `read_file`, `search_docs`,
`next_step`, `check` (vbench's own gates), `next_id`, `preview_change` and `check_overlap`. With `--write` there are two
more, `apply_change` and `commit_changes`, both marked destructive so Claude Code asks you before calling them. A change
keeps the dashboard's shape: `preview_change` writes nothing and returns the diff, what else it touches and a digest;
`apply_change` writes only if that digest still matches the files; `commit_changes` is a separate step that takes
documentation files only. Applying and committing are refused on the default branch unless you add `--allow-default-branch`.

**What stays on the host.** Inside the container only vbench's own gates run (links, criteria, rungs, diagrams, docs). The
project's own `test`, `lint` and `types` commands need the project's toolchain, so `/vbench:v-3-code`'s gate runner keeps
running them on the host. A commit is authored by the identity you pass in. `--user` makes the files the container writes
yours on Linux; Docker Desktop on macOS and Windows maps ownership itself, so there it can be left out.

**Running it from the image.** One image, three ways in. The project is always mounted at `/project`.

```bash
# 1. The CLI: a shell function (put it in ~/.zshrc or ~/.bashrc), then use `vbench` as if it were installed.
vbench() { docker run --rm -i --user "$(id -u):$(id -g)" -v "$PWD:/project" vbench "$@"; }
vbench init --stack none && vbench check && vbench status

# 2. The dashboard is a separate, optional extra: `docker compose up` (see Dashboard).

# 3. Claude Code: the `claude mcp add` command above.
```

The dashboard runs with `docker compose` (see Dashboard), which also starts the PlantUML renderer its diagrams need.
`vbench update` reads the install record, so run it from a host install, not from inside the image.

