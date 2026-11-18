# Security checklist: this project's overlay

The generic checklists live with the skills, in `.claude/skills/_vbench/standards/security/`:
[web.md](../../.claude/skills/_vbench/standards/security/web.md) (WEB-1 to WEB-15),
[api.md](../../.claude/skills/_vbench/standards/security/api.md) (API-1 to API-10) and
[genai.md](../../.claude/skills/_vbench/standards/security/genai.md) (GEN-1 to GEN-10).
`vbench-security-reviewer` reads them, then this file. This file holds only what is **ours**: which lenses apply, the
items we adopt or set aside, and the risks we accept for now. Cite items by id, and a decision for each deviation.

## Which lenses apply

| Lens | Applies to | Notes |
|---|---|---|
| Web (`web.md`) | every use case | sign in, sessions, accounts, audit |
| API (`api.md`) | every use case that adds or changes an API route | the API in `apps/api` |
| GenAI (`genai.md`) | a use case that sends data to a model, uses its output or lets it call tools | none yet. Evaluations (BC-EVALUATIONS) will probably need it |

## Items we adopt or set aside

None set aside yet. Add a line here, with the decision, when an item does not apply.

## Accepted for now

- **Email verification is off** (decision 10): the product is deployed inside the corporate network. This accepts a
  risk under WEB-13 and WEB-10. Revisit it with UC-A7 or before the product is reachable from outside the network.
