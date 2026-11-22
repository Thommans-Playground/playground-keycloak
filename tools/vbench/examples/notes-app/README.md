# Notes app: a worked vbench example

A tiny project that shows the V-cycle on three use cases. To see it as pictures, run `PROJECT=$PWD docker compose -f <vbench checkout>/docker-compose.yml up --build` and open http://localhost:3100 (needs Docker; the dashboard is an optional extra).

| Use case | Where it is | Why |
|---|---|---|
| **UC-N-001** Create note | built | Specified, designed (sequence and state diagrams, the Notes domain model), coded test first and tagged. |
| **UC-N-002** Read note | in code | Its criteria and task plan are written; no code or tests yet. It waits for UC-N-001, which is built, so it is next. |
| **UC-N-003** Edit note | requirements | Still a scaffold (`TBD`). It waits for UC-N-001 and UC-N-002. |

The `acs` gate **fails on purpose**: UC-N-002's criteria have no tests yet, exactly as they would mid-build. Finishing
UC-N-002 turns it green.

```bash
vbench status      # progress, waves and blockers
vbench next        # the one next step
vbench check       # refs, rungs, acs, links, diagrams, docs
python -m pytest   # the example's own tests (from this folder, with pytest installed)
```
