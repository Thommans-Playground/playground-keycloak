# 0018 Term cards tied to real code, checked

- Status: accepted
- Date: 2026-11-22
- Decided by: agent (technical); the aim comes from the owner's ethos ("learn while you build")

## Context
The aim is that the person building understands what they own: when PKCE, a nonce or OIDC comes up, it is explained
right there, tied to their own code. Explanations kept in a long study guide are not where the person is looking, and an
explanation that names code can go stale without anyone noticing.

## Decision
One short card for each term in `docs/learn/terms/` (a header, then four sections: in one line, why we need it, in our
code, look for yourself). `.claude/skills/vbench-explain/scripts/terms_tool.py` lists, shows and finds cards, records
which the learner has met in `.learning/terms-seen.txt` (git-ignored, personal), and `check` fails when a card is
malformed, a code pointer names a file or symbol that is gone, a study guide heading it cites is gone, or two cards claim
the same alias. A test runs `check` on the real cards. The skill `vbench-explain` teaches a term once, in about three
lines, at most two at a time, never in the middle of a step. A standing paragraph in CLAUDE.md makes it happen without
being asked.

## Consequences
An explanation is next to real code and stays true, or its test fails. It is not a quiz and not a course: the daily
guided session stays in `vbench-walkthrough`, which uses the same cards. Whether a person actually understood is not
measured; the skill asks one question and listens.

## Links
ADR 0017; `docs/standards/skills-and-agents.md`; the skill `vbench-explain`.
