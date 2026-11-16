---
name: v-1-requirements
description: V-model step 1 (left arm, top). Turn an idea, a `STK-REQ`/`REQ-FR` id, or an existing UC into an approved requirement-level spec with testable acceptance criteria, relevant NFRs, and a decision to create or update a use case. Writes no code.
disable-model-invocation: true
argument-hint: <idea | STK-REQ-/REQ-FR-/UC- id>
---

# /vbench:v-1-requirements: Requirement ↔ Acceptance

**Why this step:** acceptance criteria are the contract that every later test and review is checked against.

Left arm, top of the V. The output is a UC spec whose **AC rows are the contract** that
`/vbench:v-4-verify` later proves. Write no production code and do not fill design sections (that is
`/vbench:v-2-design`).

Input: `$ARGUMENTS`. If empty, ask what to specify (offer `/vbench:v-status` to find specs with gaps).
Paths, id patterns and commands come from `.vbench/config.toml`.

## Steps

1. **Locate.** A UC id: read its spec. A `STK-REQ-` or `REQ-FR-` id or free text: search the requirements doc and
   `specs` for it. Report what already exists before creating anything.
2. **Requirements gap?** Nothing traces to a `STK-REQ-` or `REQ-FR-` id: run the `requirements-engineering` skill first.
   Never create a UC with no requirement behind it.
3. **Start from the discovery brief (new scope; skip for a small change).** Look in the discovery folder for an
   approved brief on this idea and build from it: its scope, vocabulary, assumptions and decisions are settled, so do
   not re-ask them. None, and the scope is new or vague: stop and send the user to `/vbench:discovery`. When the
   requirements are written, fill the brief's **Becomes** table with the ids you created.
4. **Suggest NFRs.** Check the request against the concerns in `references/nfr-checklist.md` and propose only
   the ones it triggers, each as a six-part scenario (source, stimulus, artifact, environment, response, response
   measure). The user accepts or rejects each; accepted ones get the next `REQ-NFR-nnn` id, a row in §5 naming the request it satisfies and a row in §8 of the
   requirements doc, and are cited by the ACs they constrain. Each FR gets a one-line user story
   (`As a <role>, I want <goal> so that <benefit>`) in §4.
5. **Create or update.** Decide, with evidence from sibling specs: is this a new flow in an existing UC, or a
   new UC? New: run `vbench new uc --area <letter> --title "<title>"`, or delegate to the `uc-scaffolder`
   subagent. Existing: edit in place. Say which and why. Fill the spec header's **Primary actor** and **Bounded
   context** (the context's name, reused exactly across specs) and **Depends on**: the overall use-case diagram is
   generated from them.
6. **Number with the CLI.** Take ids from `vbench id fr|nfr|request|ac --area <A> --count <n>`; never invent one.
7. **Make every AC testable.** Each `AC-<area>-<nnn>` is Given/when/then, observable through a public
   interface, and cites the FR/NFR it satisfies. Follow `references/acceptance-criteria.md` (rules, rewrites of
   vague rows, smells). Cover the main flow, each alternative or exception flow, and each postcondition.
8. **Check the docs.** Fill the spec's **Realises** row (FR/NFR ids) and run `vbench sync`: it regenerates the overall
   use-case diagram and the generated blocks in the backlog and requirements docs (dependencies, build-order waves,
   coverage, FR map). Never edit inside a `<!-- vbench:begin ... -->` marker or the generated diagram; fix the spec
   header instead. Then `vbench check docs`, `vbench check refs` and `vbench check links`. Fix what you caused.
9. **Approval gate.** Summarise scope (in and out), the ACs, the accepted NFRs and open risks. Ask the user
   to approve; stop. On approval offer to commit as `docs(UC-<id>): <summary>`: that commit is the approval
   record. Next: `/vbench:v-2-design <UC-id>`.

## Rules
- Maturity stays ⚪ until code lands.
- Append ids only; never renumber. Allocate with `vbench new`.
- No `TBD` in AC rows.

## Connections
- Reads: requirements doc, sibling specs, `docs/00-naming-conventions.md`.
- Writes: the UC spec (ACs), `STK-REQ`, `REQ-FR` and `REQ-NFR` entries.
- Reads: the approved discovery brief. Calls: `requirements-engineering`, `uc-scaffolder`.
- Next: `/vbench:v-2-design`. Back-edge from it: a design that exposes a missing AC returns here.
