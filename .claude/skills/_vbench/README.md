# vbench skills: drop-in kit

A set of Claude Code skills for a use case driven workflow: requirements, acceptance criteria, use cases,
acceptance tests, branches, commits and pull requests, plus the diagram and domain model skills.

## Install in any repo

Copy the skills into the repo's `.claude/skills/` folder. Keep the `_vbench` folder, because every skill
shares it.

```bash
cp -R /path/to/source/.claude/skills/vbench-* /path/to/source/.claude/skills/_vbench  <repo>/.claude/skills/
```

Or put them in `~/.claude/skills/` to have them in every repo. The scripts then live at
`~/.claude/skills/...` and the skills' `python3 .claude/skills/...` commands need that path, so a
per-repo copy is the simple choice.

Nothing else is needed. There is no config to write and no folder to create: the first use creates what it needs.
The scripts use only the Python 3.10+ standard library (PlantUML checks also want Java and a PlantUML jar).

```bash
python3 .claude/skills/vbench-req/scripts/req_tool.py init      # optional: creates the two requirements files (markdown)
```

## Settings: `vbench.json` (optional)

Put it at the repo root or in `.claude/`. Leave out any key to keep its default.

| Key | Default | Meaning |
| --- | ------- | ------- |
| `id_prefix` | `"UC"` | Use case id prefix: `UC-P1` |
| `use_case_ids` | `"required"` | `"optional"` also allows `feat/<slug>` branches |
| `base_branch` | detected | Where PRs go. Detected from `origin/HEAD`, else `main`, `master`, `develop`, `trunk` |
| `areas` | `{}` | `{"P": "projects"}`: area letters and their context names. Empty allows any letter |
| `actors` | `[]` | Allowed use case actors. Empty allows any |
| `providers` | `[]` | Allowed `provided_by` values. Empty allows any |
| `system_name` | repo folder | Name shown in generated use case diagrams |
| `tests_dirs` | `["tests/acceptance"]` | Where acceptance tests live |
| `test_stack` | detected | `pytest`, `vitest` or `playwright` for drafted tests |
| `commit_types`, `branch_types` | Conventional Commits | Allowed types |
| `max_branch`, `max_summary`, `max_title` | 60, 72, 72 | Length limits |
| `paths` | `docs/...` | Where the requirements files, use cases and ontology live |
| `diagram` | `{}` | Optional colours and names for generated use case diagrams |

Example:

```json
{
  "id_prefix": "UC",
  "base_branch": "develop",
  "areas": { "P": "projects", "O": "orders" },
  "actors": ["customer", "admin", "system"],
  "tests_dirs": ["tests/acceptance", "e2e"]
}
```

## The skills

| Skill | What it does |
| ----- | ------------ |
| `vbench-req` | Search, write and check requirements and acceptance criteria (CSV) |
| `vbench-uc` | Write and check use cases, with impact analysis from the recorded links |
| `vbench-at` | Link acceptance criteria to acceptance tests, report gaps, draft failing tests |
| `vbench-branch`, `vbench-commit`, `vbench-pr` | Name branches, write commits, open PRs in the vbench format |
| `vbench-ontology`, `vbench-contexts` | Domain model: objects, rules, bounded contexts |
| `vbench-diagrams`, `vbench-mermaid`, `vbench-puml` | Diagrams |

The standards the skills apply are in `_vbench/standards/`. Edit them to change a rule for your repo.
Starter PlantUML style files for the diagram skills are in `_vbench/templates/`. Copy them next to your diagrams
(`vbench-puml` says when).

## Tests

```bash
for d in vbench-req vbench-uc vbench-at; do (cd .claude/skills/$d/scripts && python3 -m unittest discover -p 'test_*.py'); done
```
