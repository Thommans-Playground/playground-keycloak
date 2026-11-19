# 0004 Database migrations with Alembic

- Status: proposed
- Date: 2026-11-19
- Decided by: together

## Context
The API creates its tables at start-up with create_all. That never alters an existing table, and Projects and Audit add tables and columns. AWS needs migrations as a deploy step.

## Decision
Use Alembic, with a baseline of today's schema, then one migration for Audit and Projects. The declarative base moves to a shared module that belongs to no context.

## Consequences
One more dependency and a deploy step. Existing databases must be stamped at the baseline. NOT BUILT YET: decision 14 asks for it, and the code still calls create_all.

## Links
decision 14; decision 4 (open item); apps/api/app/main.py.
