# Getting started (15 minutes)

> For someone new to this way of working. You do not need to know the V-model, DDD or TDD first. You will meet
> each idea when the tool first needs it, and the [glossary](00-glossary.md) explains every word in plain terms.

## The idea in one minute

You will build a tiny notes app. Each thing it can do (create a note, read a note, edit a note) is a **use case**.
For each one, you do the same five things:

1. **Agree what "done" means**, as short checkable sentences (acceptance criteria).
2. **Plan it**: where it lives, what it is made of, and the small tasks to build it.
3. **Build it test first**: write a test that fails, then the code that makes it pass.
4. **Prove it**: re-check it independently.
5. **Ship it**: review everything together, then merge.

The tool keeps track of where you are and always knows the next step. You stay in charge: the agent stops and asks
for your approval at each gate, so nothing moves on without your yes.

## What you need to know today (Level 0)

Three things, and nothing else yet:

| To do this | Use |
|---|---|
| Do the next step | `/vbench:next` in Claude Code |
| See where you are, in a terminal | `vbench status`, and `vbench next` for just the next step |
| See it as pictures | The dashboard is an optional extra, not part of the CLI: from a checkout of the vbench repo run `PROJECT=/path/to/your/project docker compose up --build` (needs Docker), then open `http://localhost:3000`. Click a phase of the V in the sidebar to see its items, and any item to see the V it belongs to. `vbench status` shows the same facts as a table. |

Everything else is learned on demand:

| Level | You learn it when | Examples |
|---|---|---|
| **0** | now | `/vbench:next`, approving a step, `vbench status` |
| **1** | a check fails or you first commit | the tags in code and tests, the commit format, the gates |
| **2** | a use case really needs it | bounded contexts, the context map, the full rigor tier, decision records |

## The walkthrough

**0. Set up, once.** Install the CLI (`uv tool install` of the vbench Git URL) and the Claude Code plugin
(`/plugin marketplace add`, then `/plugin install vbench`). In your project folder run `vbench init`. It creates
this documentation folder, the configuration and the CI checks.

**1. Say your idea.** In Claude Code, run `/vbench:next`. With no use cases yet it starts **discovery**: the agent
asks one question at a time, each with a suggested answer, so you can reply "yes" or push back. At the end it
saves your answers as a brief in the discovery folder. Read it, fix anything wrong, and set its Status to
`approved`. *Why: agreeing the scope first stops you building the wrong thing.*

**2. Turn it into requirements.** Run `/vbench:next` again. The agent writes the requirements (what the app must do
and how well), creates the three use cases, and writes the acceptance criteria for each, for example "given a
body that is empty, when the author saves, then nothing is stored". You approve. *Why: these sentences are the
contract that every test and review is later checked against.* Run `vbench status` and you will see the three use
cases in order, with read waiting for create.

**3. Plan the first use case.** `/vbench:next` picks create note, because nothing it depends on is unbuilt. The
agent proposes the pieces (a `Note`, and a place to keep it), draws a small sequence diagram, and lists the tasks.
You approve. *Why: deciding the structure and the tests up front keeps the code small and the tests honest.*

**4. Build it, one task per turn.** Keep running `/vbench:next`. Each turn does one task test first: a failing test,
the least code to pass it, a tidy-up, then a commit such as `feat(UC-N-001/TSK-N-001): reject an empty body`. *Why:
a test you have seen fail is a test whose pass means something.* `vbench status` shows tasks closing and
criteria getting covered.

**5. Prove it and ship it.** When create note is built, `/vbench:next` moves to the independent re-check, then
unlocks read note, and so on. When every use case is built it runs the final review and drafts the pull request.
It asks before it pushes anything.

## When a check fails

Checks run with `vbench check` and again in CI. A failure names the file and the fix. The common ones:

| It says | It means | Fix |
|---|---|---|
| a criterion has no test | nothing marks a test as covering it | add the criterion's marker to the test |
| a use case has code but no verifying test | the code is not tied to a test | tag the test with the use case and its level |
| a generated block or diagram is out of date | a spec header changed | run `vbench sync` |
| a commit does not match the format | the message does not name its use case | reword it (see the commit format in the contributing guide) |

If you are unsure what a word means, look it up in the [glossary](00-glossary.md). If you are unsure what to do,
`vbench next` always says, and `/vbench:v-status` explains where you are.

## Where things live

If the project uses the stack standard (the default `vbench init` scaffolds), `04-technology-stack.md` says what it is
built on and why, and `uv run lint-imports` checks the architecture rules.

The [documentation map](README.md) lists every document and what it answers. The two that matter first are the
[requirements](00-requirements-engineering.md) (who wants what) and the
[backlog](01-backlog-epics-stories.md) (the use cases and the order to build them). Parts of both are generated
from the use-case files, so you edit the use case and run `vbench sync`, never the generated block.
