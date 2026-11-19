```yaml
id: RULE-A6
type: rule
name: A return address stays on our site
status: draft
object: OBJ-A1
statement: "A sign in sends the person back only to a path of ours. Anything else is replaced by the person's own page."
proved_by: [AC-40]
satisfies: [FR-1]
```

# A return address stays on our site

## In plain words

After sign in the person goes to the page they first asked for, but only if that address is a path of ours, starting with one `/`. A full address, `//host`, `/\host`, a bare word, an empty value or one with a line break is replaced by `/dashboard`.

## Why it exists

A sign in link that could send a person to another site would be a way to phish them right after they proved who they are (an open redirect).

## Allowed and refused

| Case | Answer |
|---|---|
| `/admin/accounts?tab=2` | kept |
| `https://evil.example`, `//evil.example`, `/\evil.example` | `/dashboard` |
| `dashboard`, empty, none, `/a` plus a line break | `/dashboard` |

## How a test would prove it

A unit test of the pure function `safeReturnTo` in `apps/web/src/domain/return-to.ts` (`return-to.test.ts`), and the sign in use case test SI-3. Both are tagged `Verifies AC-40, RULE-A6`.

## Related

- [UC-A1 Sign in](../../usecases/UC-A1-sign-in.md)
