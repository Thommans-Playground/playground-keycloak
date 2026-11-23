---
term: Security log
say: The security log is one JSON line for each sign in, refusal and session event, with no secret in it, so you can see who did what.
aliases: [security log, SecurityLog, security event]
prereq: [ports-and-adapters]
code:
  - apps/api/app/infrastructure/security_log.py :: JsonStdoutSecurityLog
  - apps/web/src/adapters/json-security-log.ts :: JsonSecurityLog
check: A refused request has a token in its header. Why can that token never end up in the log line?
---

## In one line

Every refused sign in, refused request and session start or end writes one JSON line to standard output. On AWS the container log driver ships it to CloudWatch (ADR 0013).

## Why we need it

Without a trail you cannot tell an attack from a bug, or answer who tried what. A log that held tokens or codes would itself become something to steal. So only a fixed set of keys can be written, a reason must look like a short code, and a session id is stored as a hash. A value that does not fit is dropped.

## In our code

`SecurityLog` is a port, so the use cases call `event(...)` and never know about stdout. `JsonStdoutSecurityLog` on the API and `JsonSecurityLog` on the web are the adapters. The API guards write `request_refused` lines; the web sign in writes `sign_in` and `session_start`.

## Look for yourself

Open `security_log.py` and read the two patterns at the top. Then call the API `/me` with no token and find the `request_refused` line in `docker compose logs api`.
