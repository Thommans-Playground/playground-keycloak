# CSV files

Some records are one flat file in CSV format, so a person can scan, filter and sort them in a
spreadsheet, and git can show a changed row. The tools (`req_tool.py`, `uc_tool.py`, `at_tool.py`)
read and check them. The default places are below, and `paths` in `vbench.json` can change them.

## When a thing is a CSV, and when it is a file

Use a **CSV** when the thing is:
- flat and uniform, with the same columns in every row,
- many rows that you scan, filter and sort,
- short on prose, with no diagram,
- something a person may want to open in a spreadsheet.

Keep **files** (a YAML block with explanation and diagrams) when the thing is nested, such as the
ontology objects with their links and properties, or explained, such as a decision or a diagram, or
read in order, such as a README.

A CSV costs three things. It enforces nothing by itself, so a check must. Its columns must be
written down. And the ids must match across the CSVs and the YAML files, so one tool reads both. So
keep the number of CSV files small, and write each one's columns here.

## The files

### requirements.md and acceptance-criteria.md are not CSV

The requirements and the acceptance criteria are markdown tables, because a person has to read them.
Their layout and fields are in [requirements.md](requirements.md). `req_tool.py init` creates them empty,
and `req_tool.py convert` turns an old `requirements.csv` and `acceptance-criteria.csv` into them.

The acceptance criteria fields, for reference:
- `id`: `AC-<n>`.
- `requirements`: the requirement ids it proves, separated by semicolons.
- `given`, `when`, `then`: the scenario.
- `test_level`: `unit`, `integration`, `acceptance`, `manual`, `inspection` or `future`.
- `status`: `draft`, `accepted`, `open` or `retired`.
- `notes`.

### requirements/permissions.csv (optional)
Who may do what: one row for each permission, one column for each role. Only for a product with
roles.
- `permission`: a thing a role may do, in plain words.
- One column for each role (the roles are the project's own, for example `admin` and `member`):
  `yes`, `no`, or a condition (`only where a member`).
- `requirements`: the `FR-` ids that state it, separated by semicolons. Empty means no requirement
  row says it yet.
- `source`, `notes`.

### domain/ontology/rule-inventory.csv (optional)
The numbered rules, one row each: a list of what is to be reviewed and promoted to a `RULE-` file.
- `ref`: the rule's working number (`R9`). It is a working reference, not a final id.
- `statement`: the rule, in the project's words.
- `enforced_in`: where the code enforces it today.
- `status`: `live` or `retired`.
- `rule_file`: the `RULE-` file it became, empty if not written yet.
- `notes`.

### domain/vocabulary.csv (optional)
The words: the terms in use, and the words not to use.
- `term`: the word or phrase.
- `kind`: `term`, or `retired word`.
- `context`: the part of the product it belongs to (for a term).
- `meaning`: what it means, or why not to use it.
- `use_instead`: the word to use, for a retired word.
- `source`, `notes`.

`req_tool.py` reads the retired words and flags one in a new requirement. A word that is also an
everyday word is flagged as "watch in context", not as an error.

### usecases/retired-ids.csv (optional)
The use case ids that were reserved or issued and then retired, so they are never handed out again.
- `id`: the retired use case id.
- `name`: what it was called.
- `reason`: why it went.

`uc_tool.py next-id` skips them, and `uc_tool.py validate` refuses a use case file that uses one.

## Conventions

- One header row, UTF-8, a comma as the separator, and quotes around any cell with a comma.
- A list in one cell is separated by semicolons.
- An id is written the same way everywhere (`FR-12`, `RULE-O1`, `OBJ-P1`).
- A CSV lives beside what it describes, and its columns are written in this file.
- The tools keep the file's own line ending when they edit a row, so a change shows as one changed
  row in git.
- No em or en dashes: use a full stop, a comma or brackets.
