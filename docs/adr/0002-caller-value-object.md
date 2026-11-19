# 0002 Projects receive a Caller, and never look a role up

- Status: accepted
- Date: 2026-11-19
- Decided by: together

## Context
Project commands depend on one fact, whether the caller is an active administrator. Three documents gave three answers, and a role check inside a route could only be tested over HTTP.

## Decision
The API resolves the token, the account and the role once, in the shared route guard, and passes a Caller (account id, is administrator) into every Projects use case. Projects never reads a role and never imports Access. Every project route goes through the same full check as the account routes (token, account found, not deactivated, not pending) before the role matters.

## Consequences
The superuser rule is a pure function of the Caller and can be unit tested. The guard is shared, so a forgotten route is the main risk: an architecture test should fail on a route without it. NOT BUILT YET.

## Links
decision 14; BC-PROJECTS; docs/domain/diagrams/projects-design.puml; UC-P1, UC-P2, UC-P3.
