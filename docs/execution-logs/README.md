# Execution logs

A living engineering notebook for each use case: a reviewed, step by step plan to build it, whose code is the code that
exists, and how it works today. The decision is [ADR 0021](../adr/0021-execution-log-a-notebook-for-each-use-case.md). It is plain Markdown, so
you can read it in an editor or on GitHub without any tool.

| Page | Answers |
|---|---|
| `<UC>/README.md` | What this use case is, and the table of chapters |
| `<UC>/current.md` | How it works **today**: the files, the tests, the limits. The only page that describes now |
| `<UC>/chapters/NNN-name/` | One change (initial build, a defect, a hardening). Kept as it happened |
| `<UC>/evidence/index.json` | The code each step matches, its files and tests, and the review commit |

## Notebooks

| Use case | Chapters |
|---|---|
| [UC-P1 create a project](UC-P1-create-a-project/README.md) | 001 (8 tasks written, drafts) |

## The shape

```
docs/execution-logs/UC-P1-create-a-project/
├── README.md
├── current.md
├── chapters/
│   └── 001-initial-implementation/
│       ├── summary.md          the chapter overview: objective, context, ground rules, plan, risks, verification, approvals
│       ├── plan.yaml
│       └── TSK-P1.5-name-members-and-fields.md   one file for each task
└── evidence/index.json
```

A **chapter** is one change. It has a `summary.md` (the overview, in nine sections: objective, engineering context, implementation strategy with the ground
rules every task assumes, execution plan, risks, decisions and deviations, verification summary, approvals, outcome and
learnings) and one file for each task. A **task** is a `TSK-` line from the use case's Slices; its steps are inside
its file, each one behaviour with one failing test.

## A task file: a code-along

A **task** is one slice that can be built and tested on its own. A **step** is one behaviour inside it, with one failing test
and the code that makes it pass ([ADR 0022](../adr/0022-execution-log-tasks-are-code-alongs.md)). The what and why of every
task is in the chapter's `summary.md`, under "What and why, task by task". The task file is what you follow at the keyboard:

1. **Header**: task id, use case, criteria, the commit its code matches.
2. **A link** to the task's entry in `summary.md`, and **the command** that runs its tests.
3. **Steps**, each with **Test** (and its level: Unit, API, Integration or Architecture), **Code** and **Logic.**

Write one with the `vbench-execlog` skill and check it with
`python3 .claude/skills/vbench-execlog/scripts/execlog_tool.py check`. `execlog_tool.py shape` prints the shape to copy.

## Rules

- **The plan reflects the final code.** A block marked `# file` is a copy of that file at the commit in the header.
  Nothing in a plan is invented: an "expect" is marked "checked" only if it was run.
- **Reviewed before it is trusted.** A step is a draft until a person has read it against the code and written the commit.
- **No rewriting history.** A later change (a defect, a hardening) is a new chapter that points back and shows its own
  failing test.
- **`current.md` moves, chapters do not.** After a chapter is accepted, update `current.md` in the same commit.
- **Approval names a commit.** "Reviewed at `abc1234`", never just "reviewed". If the cited code changes in behaviour,
  the approval is stale.
