---
name: requirements-engineering
description: Decide where a new stakeholder ask goes before it becomes a use case, and keep the STK-REQ/REQ-FR/REQ-NFR/EPC ids and the maturity tags honest. Use for genuinely new scope or when reconciling the requirements doc against a code change.
---

# requirements-engineering: where does this ask go?

**Why this step:** every use case traces back to a requirement, so nothing is built for no reason.

Read the project's naming conventions (ids) and its requirements document and backlog. Their paths are the
`requirements` and `backlog` keys in `.vbench/config.toml`; `vbench init` creates both from templates. A new
use case also goes into the backlog under its epic. The dependency, build-order and coverage tables there, and the
FR map in the requirements doc, are generated blocks (`<!-- vbench:begin NAME -->`): record a dependency or a
realised requirement in the spec header and run `vbench sync`; never edit inside the markers.

## The shape
Breadth first, then depth on what survives prioritisation: requests, language, context, FRs, NFRs, priority,
detail, architecture, review. The ten steps and the id scheme are in `references/document-shape.md`.

## Routing a new ask
- No `STK-REQ-` or `REQ-FR-` behind it: add a `STK-REQ-nnn` first, in the stakeholder's words, then derive FRs/NFRs. Name the problem it addresses (`STK-PRB-nnn`, section 0); if there is none, add the problem first.
- A refinement of something modelled: usually a new flow inside an existing use case, not a new use case.
- Genuinely new scope: confirm its epic, then allocate the use case with `vbench new uc` (never by hand).

## Rules
- Prefix = type, area letter = bounded context, number = append-only. Never renumber; retire, don't reuse.
- `STK-REQ`, `REQ-FR`, `REQ-NFR` and `ADR-DEC` are global; `EPC`, `UC`, `AC` and `TSK` carry the area letter. Allocate with `vbench id`.
- Maturity (✅ built and verified, 🟡 partial, ⚪ specified only) is derived from the code, not from intent.
- Code is the source of truth. When a doc and the code disagree, fix the doc and note the discrepancy.
- A requirement that forces an architectural choice gets an ADR.

## Connections
- Called by: `/vbench:v-1-requirements` when nothing traces to a `STK-REQ` or `REQ-FR` id.
- Hands off to: `uc-scaffolder` (or `vbench new uc`) once the requirement exists.
