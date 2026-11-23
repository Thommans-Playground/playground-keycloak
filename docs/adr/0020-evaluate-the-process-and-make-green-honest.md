# 0020 Evaluate the process, then make green honest and the surface light

- Status: accepted
- Date: 2026-11-22
- Decided by: agent (technical); the aims come from the owner's ethos

## Context
Six read-only reviewers evaluated the harness against the owner's ethos: friction (a dry run of one small change), honesty of
the trace (a red team), cost, the term cards, credibility (an assessor, an agile coach and a sceptical engineer) and
portability (three other projects). They confirmed bypasses: a retired criterion, a skipped or empty test, a broken use case
header under `--all`, and a stale test hash all gave a green trace; and a small change cost about 30 approvals.

## Decision
1. **Green is earned.** A listed criterion that is retired or missing fails. A tag counts only on a test that really runs
   (Python read with `ast`; JS skip forms widened). A test with no assertion, a combined tag, a deferral with no decision and
   a stale test hash are failures or warnings, never ok. `--all` fails on a broken header and on checking nothing. With
   JUnit results configured, a criterion counts only when its test passed, and the trace says when it checks existence only.
2. **Light surface.** One front door, `/vbench-next`. A change has a tier, chosen by a person: small (one combined sequence,
   no freeze, one review pass) or full. The reviewers are started once, in `vbench-uc`. TDD asks two decisions for each
   behaviour, not three. No duplicate skeleton test. One review summary before stamps.
3. **Honest claims.** `HARNESS.md` states what it does not prove first, says "forward and backward links" and calls AUTOSAR
   an analogy.
4. **Portable.** `vbench.json` gains `adoption`, `packs`, `results`, `id_patterns`, `gate` and `test_framework`. Each role has a
   pack (core, ddd, security, or the keycloak overlay), and a trace row of a pack that is off is left out. A baseline records
   known failures so only new ones fail. `vbench-adopt` proposes only keys the loader accepts, and a test loads every proposal.
5. **Cards are checked and fair.** The term cards were fact-checked and corrected, five were added, and `find` ranks, caps at
   two, respects prerequisites and brings terms back for spaced recall.

## Consequences
The trace now fails on things it used to accept, so a use case can go from green to red when a weak test is revealed; that
is the point. Not done: results from the fresh-stack run, a log of review findings and defects, release and baseline,
integration as a level, packaging as an installable plugin, `id_patterns` beyond the tag scanner, and an independent quality
owner. They are listed in the map as known gaps.

## Links
ADR 0008, 0017, 0018, 0019; `docs/HARNESS.md`; `docs/standards/skills-and-agents.md`.
