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
learnings) and one file for each task. A **task** is a `TSK-` line from the use case's Slices; its stages are inside
its file.

## A task file has these parts, in this order

A task file is a code-along: someone who has the design can follow it and build the same thing. It gives the logic, the
reasoning and the plan, and does not explain red, green or refactor.

1. **Header**: the task, criteria, plan status, the commit its code matches, and a link to the summary.
2. **What we are building, and why**: a table of each AC (given, then, why it exists).
3. **The logic**: the decisions, each tied to a criterion, and where the code lives and why there.
4. **The plan**: stages in the order to work, each with the test to write, the command to run, what to **expect**, then
   the code. The last stage ends on the final code, copied from its file.
5. **Check it yourself**: the commands that prove it, with the counts.
6. **Where this leaves things**: files, tests, ADR.
7. **Review**: who read the plan against the code, at which commit.

## Rules

- **The plan reflects the final code.** A block marked `# file` is a copy of that file at the commit in the header.
  Nothing in a plan is invented: an "expect" is marked "checked" only if it was run.
- **Reviewed before it is trusted.** A step is a draft until a person has read it against the code and written the commit.
- **No rewriting history.** A later change (a defect, a hardening) is a new chapter that points back and shows its own
  failing test.
- **`current.md` moves, chapters do not.** After a chapter is accepted, update `current.md` in the same commit.
- **Approval names a commit.** "Reviewed at `abc1234`", never just "reviewed". If the cited code changes in behaviour,
  the approval is stale.
