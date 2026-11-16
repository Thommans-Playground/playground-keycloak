# Shape of the requirements document

Breadth first, then depth on what survives prioritisation. One document, in `docs/`, append-only ids.

0. **Problems** (`STK-PRB-nnn`): what people struggle with, who is affected and what leaving it costs. One row each.
1. **Stakeholders and requests**: who (`STK-PER-nnn`) and the raw ask (`STK-REQ-nnn`), in their own words, each naming the problem it addresses.
2. **Ubiquitous language**: the shared vocabulary; one definition per term, no synonyms.
3. **System context**: what is inside and what is outside; the external actors and systems.
4. **Functional requirements** (`REQ-FR-nnn`), breadth only, each with a one-line user story.
5. **Non-functional requirements** (`REQ-NFR-nnn`), breadth only.
6. **Prioritise**: must / should / could / won't (this release).
7. **Detail the FRs**: flows, pre- and post-conditions. These become use cases (`vbench new uc`).
8. **Detail the NFRs**: each as a six-part quality attribute scenario whose response measure is checkable (see the v-1 NFR checklist).
9. **Fold into the architecture**: which requirement forces which decision (ADR).
10. **Review with stakeholders**: the human sign-off.

## Id scheme
| Prefix | Meaning | Scope |
|---|---|---|
| `STK-PER` `STK-REQ` `REQ-FR` `REQ-NFR` `ADR-DEC` | stakeholder, request, functional, non-functional, decision | global, one counter |
| `EP` `UC` | epic, use case | area-coded: `UC-A-001` = area A, number 1 |
| `AC` | acceptance criterion | `AC-<area>-<nnn>` |

Numbers are append-only. Retire an id, never reuse it. Maturity is derived from code: ✅ built and verified,
🟡 partial, ⚪ specified only.
