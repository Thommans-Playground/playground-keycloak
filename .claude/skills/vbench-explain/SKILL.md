---
name: vbench-explain
description: Explain a term the learner meets while building (PKCE, nonce, OIDC, a session cookie, CSP, a port) right where it comes up, tied to this project's own code, once, and in a few lines. Uses the term cards in docs/learn/terms/ and remembers what the learner has already seen. Use whenever the user asks "what is X", "explain PKCE", "what does this mean", "why do we need a nonce", "teach me this term", or when you are about to use a term that has a card and the learner has not met it, even if they never say "vbench". For a whole guided session over a use case, use vbench-walkthrough.
---

# Explain a term, where it comes up

**Why this step:** you should leave every session knowing more than you went in. A term explained in a textbook is
forgotten; a term explained next to the line of your own code that uses it sticks.

The cards are in `docs/learn/terms/`, one for each idea. Each has a plain one-liner, why we need it, where it is in
our code (real files, checked so they cannot rot), something to look at yourself, and a question to check understanding.
The tool is `python3 .claude/skills/vbench-explain/scripts/terms_tool.py` (`list`, `show TERM`, `find UC-A1 --unseen [--limit N | --all]`,
`seen TERM`, `due`, `reviewed TERM`, `check`). `find` ranks, prints two by default and offers a prerequisite (card field `prereq`) before the term that needs it.

## Steps

1. **Find the term.** If the learner names one, `show` it. If you are about to use terms in an explanation or a step,
   run `terms_tool.py find <use case id, file or the text> --unseen`. Skip the ones they have met.
2. **Show at most two terms at a time**, and only the ones that matter for what is on screen now. Do not interrupt a
   step that has to finish (a failing run, a red test). Offer, or wait for the break.
3. **Teach it in about three lines** from the card: what it is in one line, why we need it, and the real file and symbol
   where it lives, quoted from the code, not from memory. Add the study guide section if the card names one.
4. **Ask the card's question, once, and let the learner answer first.** Then say whether it holds and fix what is
   off. Do not hand over the answer before they try.
5. **Record it:** `terms_tool.py seen TERM`. The learner can say "known" and you record it without teaching.
6. **No card?** Explain it briefly from the code. Then offer to write a card in the same shape. Every code pointer
   must be a real file and a symbol that is in it; run `terms_tool.py check` and keep it at zero problems. Do not
   invent a pointer.

## Spaced recall
At the start of a session run `terms_tool.py due`. Ask each question it lists once, before new material, then run
`terms_tool.py reviewed TERM`. A term is due 3 days after it is seen, then 14 days after each review.

## Boundaries
- The only file this writes is `.learning/terms-seen.txt` (git-ignored, personal). It never reads or writes the
  learner's notes, including any Obsidian vault.
- A card is an explanation, not a rule. If a card and the code disagree, the code wins: say so and fix the card.
- No nagging: a term is explained once. Do not repeat it unless the learner asks.
- For a daily guided session that follows a whole use case, hand off to `vbench-walkthrough`, which reads the same cards.
