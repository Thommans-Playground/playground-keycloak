---
name: vbench-security-test
description: Security-test one or more use cases against the running local stack, as a step on the right arm of the V. Runs the vbench-security-tester agent (OWASP WSTG checks, live probes and code reads), shows the findings, and for each broken check proposes an acceptance criterion and a failing test for a person to approve. Use whenever the user says "security test", "pentest", "OWASP test", "attack UC-A1", "is this use case secure", "abuse cases", or has just built or changed a use case and wants it tried before shipping, even if they never say "vbench".
---

# Security test: try to break a use case

**Why this step:** a use case can meet every criterion it lists and still be open to what nobody listed. Security tests
are verification on the right arm of the V: they prove the system resists what the security requirements promise.

The agent reports; it does not gate. A verdict comes from the tests that this step creates, which give the same
answer every run. The agent's judgement never sits in a pass or fail.

## Steps

1. **Check the stack is up:** `docker compose ps` shows web, api and keycloak running. If not, tell the person to run
   `docker compose up -d` and stop. This tests the local stack only.
2. **Run the agent** `vbench-security-tester` with the use case id (one agent per use case when there are several).
   Give it only the id; do not tell it what you expect to find.
3. **Show the findings** as the agent wrote them. Then stop for the person's reading. Do not start fixing. When a
   finding names a term that has a card (CSP, clickjacking, a nonce, a session cookie), offer it through `vbench-explain`.
4. **For each broken check**, offer the proposed criterion. Ask which to keep, change or drop. This is the
   requirement, so the person decides.
5. **Record the approved ones:** add each as an acceptance criterion with `vbench-req` (Level `acceptance` or
   `system`, and the Notes column starting `security SEC-xxx-n`), and list it in the use case. Then write its failing
   test first with `vbench-tdd` (RED), tagged `@pytest.mark.ac("AC-n")`. Do not write the fix in this step.
6. **Unclear checks** that need a deployed setting (HTTPS, the `Secure` cookie flag) go to the person as notes, or
   into `docs/standards/security-checklist.md` under "Accepted for now" if they decide to accept the risk.
7. **Finish** with where the use case stands: broken, now covered by a red test, unclear, held.

## Files
- `references/wstg-checks.md`: the checks, as data. Add a row to add a check.
- `scripts/session.sh`: signs in to the local stack as a development account and prints a cookie jar path. It refuses
  any address that is not local.
