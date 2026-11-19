```yaml
id: RULE-A5
type: rule
name: The first administrator comes from setup, once
status: draft
object: OBJ-A1
statement: "A new account whose email is in the setup list and is verified becomes an active administrator only while no active administrator exists. Otherwise it is a pending user."
proved_by: [AC-61]
satisfies: []
```

# The first administrator comes from setup, once

## In plain words

When Playground is new there is nobody to approve anyone. So the one email in the setup list (`BOOTSTRAP_ADMIN_EMAILS`),
if Keycloak says it is verified, becomes the first administrator without an approval. This is allowed only while the
product has no active administrator. After that, a person with the same email is treated like anyone else: a pending
account that an administrator approves.

## Why it exists

Decision 14. Without the limit, anyone who can create a Keycloak user with the setup email and tick "email verified"
would become a full administrator on their first sign in, even long after setup. It is a different rule from
[RULE-A1](RULE-A1-always-an-administrator.md), which protects the last administrator once there is one.

## Allowed and refused

| Case | Answer |
|---|---|
| No active administrator, setup email, verified | active administrator, with an audit entry from setup |
| An active administrator exists, setup email, verified | pending user |
| Setup email, not verified | pending user |

## Not built

The code in `AccessService.account_for` checks the email list and the verified flag, but not whether an
administrator exists. A failing test first (AC-61).
