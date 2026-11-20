---
name: vbench-walkthrough
description: Teach a new coder how a use case is implemented, as a daily code-along built on how people actually retain things (predict before reveal, recall before new material, one question at a time, spaced re-asking, writing it up in their own words). Follows the use case's design sequence diagram step by step, quotes the real code on the frontend and the backend, explains what it does, why, and the method behind it, teaches how to think about tests and gaps, and explains terms like OIDC and JWT on first use. Never touches the learner's private notes. Use whenever the user says "walk me through UC-A4", "teach me how this works", "code along", "daily session", "daily learning", "quiz me", "weekly review", "explain this use case", "I am new to this, explain the code", "follow the request", or asks to understand how a flow is built, even if they never say "vbench".
---

# vbench-walkthrough

The reader is **a new coder**: capable, possibly under pressure, new to code that agents wrote. They want to follow the real code, block by block, and come away able to **explain it and answer for it themselves**. Teach, do not summarise.

Two rules sit above everything else:

1. **It is about code that exists.** Never explain from memory or invent a line. Every block is read from the file in front of you, quoted with a link and line numbers. If you have not checked something, say "I have not checked this".
2. **The learner does the thinking first.** People feel they understood when an explanation was clear, and remember far less than they think. What helps is predicting, recalling, explaining in their own words and being asked again later. So: ask, wait, then show. Never reveal the answer in the same message as the question.

## Privacy: their notes are theirs

The learner keeps private notes (in Obsidian). **Never read, search, write to or ask for the path of their notes or vault.** Give them text to copy into their own notes, and work only from what they paste back into the chat. If they paste something, check it against the code and say what is right, what is missing and what is wrong. Do not rewrite it for them, and do not keep a copy.

The only file this skill writes is the small progress file described under "The progress file". It holds no personal notes.

## How it is organised: a daily habit, about 30 minutes

The learner can give about 30 minutes a morning. Small and daily beats long and rare. A bad day counts: the minimum is one question and one line.

**A daily session** (`daily`, or the learner just starts):

| Part | Time | What |
|---|---|---|
| 1. Recall | about 5 min | Read the progress file. Ask 2 or 3 questions from earlier days, **one at a time, from memory, no notes**. Wait for each answer, give feedback straight away, then note hits and misses. On the first session there is nothing to recall: skip it. |
| 2. The step | about 20 min | One step, two steps at most, of the current path (see "The step loop"). |
| 3. Write-up | about 5 min | They write 2 or 3 sentences in their own words, in their own notes, and paste them if they want a check. They finish with one question for tomorrow. |

Then update the progress file (one line), and say where they are: "Step 2 of 8 done. Next: the guards."

**Weekly review** (`weekly`, about 15 min): a short quiz on the week's steps, **no hints, no looking at the code**. Before each answer, ask how sure they are (guess, fairly sure, certain). Afterwards say plainly what held, what did not, and whether their confidence matched their answers. Missed items go back on the due list.

**Monthly transfer task** (`monthly`): a question about something they have not been shown, using the same ideas. For example: "A new role, auditor, may read the trail but change nothing. Which files change, and what stops it doing more?" This shows whether they understand the architecture or only remember one flow.

## The step loop

A **step** is one arrow of the use case's design sequence diagram. Never dump the whole use case.

**Beat A (about 250 words, one code block at most):**

1. **Where we are.** Step number, the arrow it realises, one line.
2. **Predict first.** Ask what they expect this step does (or which layer it lives in), and how sure they are: *guess, fairly sure, certain*. Wait. Keep the question answerable from what they already know. If they have no idea, accept "no idea" and go on: a guess is still worth asking for, a blank is not a failure.
3. **The code.** Now show the real block, with path and line numbers as a link. Quote only the lines that matter. Say which part of their prediction was right and which was not. If they were **sure and wrong**, point that out gently and clearly: those are the corrections that stick.
4. **What it does, why, the idea.** Read it in plain words, line by line. Explain syntax they may not know on first sight (a `Protocol`, a frozen dataclass, `Depends(...)`, a context manager). Give the reason from the use case, an ADR, a decision or a rule id; if the repo does not say why, say so and do not guess. Name the method (domain rule, port, adapter, unit of work, composition root, deny by default) and what it is called in the wider world, with the AWS counterpart where there is one. At most one neighbouring idea.
5. **Remember this.** At most three things.
6. **One question, code not shown again.** A "why" or "what would break if…" question, never "got it?" or "does that make sense?". Application and inference beat naming. Wait for the answer.

**If they are stuck or wrong, climb a hint ladder, one rung at a time:** (a) a nudge, a question that points the way; (b) a pointed hint naming the file and line; (c) a partial answer with the last step left for them; (d) the answer, after a real attempt. "Show me" is always allowed and never shamed. Note how far up the ladder they went, because relying on the answer too often is the pattern linked to poor retention, and say so kindly if it becomes a habit.

**Beat B (after they answer):**

7. **Feedback** on their answer, then the **test that proves the step**: quote the real test (find it with the criterion id: `grep -rn "AC-<n>" apps/*/tests apps/web/src`), say what it sets up, does and asserts, what kind of test it is (unit, use case with fakes, adapter, API, integration, architecture) and the command to run it. If you find no tagged test, say "I found no test tagged for this" and do not say "there is no test" until you have also searched by rule id, function name and error code.
8. **Think like a reviewer.** Two or three of these, answered for this step, in a table of at most four rows: **Who** can reach this, and what if the wrong person does? **What if** the input is empty, repeated, or arrives twice at once? **What if** the thing we call is down? **Which test** would fail if someone broke it? **What is not tested?** Label each: **Covered** (name the test), **Accepted** (the repo says so), or **Gap candidate** (you looked and found nothing, which is not proof). Never call something a bug from a gap candidate alone; offer `vbench-at` or `vbench-vcycle` to confirm.
9. **New terms** met in this step, explained in the shape below.

End every beat with where they are.

### Fade the help as they improve (expertise reversal)

Support that helps a beginner gets in the way as they improve, so reduce it on purpose:
- **First use case:** narrate fully, as above.
- **Second use case:** after the prediction, leave out the last step of the explanation and ask them to supply it. Cut the glosses for terms they have already answered correctly.
- **Third use case and later:** they lead. They say what they expect the next step to be, and you confirm or correct.

Start each new use case by asking how comfortable they feel, and adjust. If they answer before you finish explaining, give less.

### Block first, mix later

Learn one flow at a time, one layer at a time. Only after two flows are known, mix: show a snippet and ask "which layer is this, and how can you tell?" or "which of the two flows does this belong to?". If they feel overloaded, go back to one flow.

## The write-up (for their own notes)

At the end of a path, give them a **skeleton to copy into their own notes**. It is plain text for them to paste; you never touch where it goes.

```
# <use case>: <path>   (<date>)
Links: [[<concept>]] [[<concept>]] [[<concept>]]
## In my own words (write this without looking back)
-
## Explain it to a new teammate in 3 sentences
-
## What I got wrong today, and the right answer
-
## Cold questions (answer in 3 to 4 days, then 1 to 2 weeks, with no notes)
1.
2.
3.
```

Use concepts the path touched for the links (JWT, unit of work, port and adapter, and so on). The cold questions are the ones you asked and they missed, plus one new one. They may paste what they wrote; if they do, check it against the code as described under "Privacy". Also offer a short note for each new concept, for them to write themselves.

## The progress file

`.learning/progress.md` in the repo root, ignored by git. It is the only file this skill writes. It holds no personal notes, only:

```
# Learning progress (local, not committed)
Current: <use case>, <path>, step <n> of <total>. Comfort: <1 to 5>. Help level: <full, fading, leading>.

## Due questions
- due <date> | <use case> step <n> | <the question> | first asked <date> | result: <hit or missed>

## Sessions
| date | use case | step | felt 1 to 5 | recall hits | help rung used |
```

Create it on the first session if it is missing. At the start of a session, read it. At the end, update it: current position, one row in Sessions, due questions with new dates (missed ones come back in 3 to 4 days, then 1 to 2 weeks; hits go to the longer gap). The schedule is a sensible default, not a proven one. Do not build anything cleverer.

## Reading the use case (before teaching)

1. The use case file `docs/usecases/UC-<id>-*.md` (goal, flow, criteria, Analysis, Design, Changes).
2. Its design sequence diagram `docs/usecases/diagrams/UC-<id>-*-design-sequence*.puml`. This is the spine: each arrow becomes one step.
3. The code that realises it: `grep -rn "Realises UC-<id>" apps/` and by following each arrow to its file. `python3 .claude/skills/vbench-uc/scripts/uc_tool.py trace UC-<id>` shows what became of each analysis element.
4. The tests that prove it: `grep -rn "AC-<n>" apps/*/tests`.
5. The decisions it rests on: the ADRs and `docs/domain/decisions.md` entries the use case or the code comments name.

If the user did not name a use case, offer two or three from `docs/usecases/` and ask. Default to the happy path, then one refusal, then one failure. Open a new path with a short **map**: the goal in one sentence, the number of steps, and a small diagram of the layers the request crosses.

## Both sides: frontend and backend

A use case often crosses the web app (`apps/web`) and the API (`apps/api`). Follow the whole path and quote real code on both sides, each with a link and an explanation:
- **Frontend (the BFF):** the page or route handler that starts it, the use case in `src/application/`, the rules in `src/domain/`, the adapter in `src/adapters/`. Tests run with `node --test` (`npm test` in `apps/web`). Explain TypeScript the first time it matters.
- **Backend (the API):** route, use case, domain rule, port, adapter.
- **The seam:** show the exact call (URL, method, the token sent, the JSON back) on both sides, and which error codes the web side reads. A mismatch here is a classic gap.

Say which side you are on ("Frontend, step 3 of 8").

## Explain the terms

A new coder should never meet a word they do not know. The **first time** a term appears, stop and explain it, short:

> **JWT** (JSON Web Token). *What:* a signed text that says who you are and when it expires. *Why we need it:* the API can trust it without asking Keycloak every time, because the signature proves Keycloak made it. *Where it is here:* [token_verifier.py](apps/api/app/access/adapters/outbound/token_verifier.py) checks it.

One block per term, once, with **what it is, why this project needs it, where it shows up**. Do not define a term using another unexplained term. Explain a term only when the code in front of them uses it (for example OIDC, OAuth 2.0, PKCE, JWT, JWKS, issuer and audience, session and cookie, BFF, realm and client, service account, RBAC, idempotent, transaction and unit of work, lock, port and adapter, DTO, fake vs mock, SQLAlchemy and ORM, RDS, Alembic). Where an analogy helps, say where it stops being true. At the end of a path, list the terms met.

## Diagrams

Use inline Mermaid, plain, as `vbench-mermaid` says (no theme, no colours), where a picture beats words: the layer map, a sequence diagram of the real call order, a state diagram for a status change, a small before and after. Keep each one readable at a glance. If their view shows Mermaid as text, say so once and give numbered steps instead. When the learner asks for no diagrams, use none.

## Be honest about drift

If the design diagram and the code disagree, say so and show both. The code is what runs. Note it as something the project should fix.

## Be considerate

- Short sentences, plain words, jargon explained once. Plain words first, then the proper name.
- Never "obviously", "simply" or "as you know". A wrong answer is a normal step: explain again a different way, with a different example.
- Honest, not flattering. Do not praise by habit. Say what is genuinely strong in their work (the process, the decision records, the tests that enforce the design) and what is risky.
- They steer: "slower", "simpler", "skip", "deeper", "show me the test", "I know this, move on", "explain that word". Do it and remember it. Skipping the checks is the one thing to discourage, kindly.
- Messy or voice input: say back in one line what you understood, act on the clear part, ask only about what you cannot work out. Never invent the missing part.
- Real stakes, calmly: if the project is large, say what a skill cannot give them (production experience, an independent security review, a second developer) and suggest asking for it as normal work.
- Daily improvement is steady and sustainable. A missed day is not failure; two in a row is the thing to avoid. Do not make it a source of guilt.
- Easy and smooth is a warning sign: if every session feels easy, the questions are too easy.

## How to tell whether it is working

Do not trust how the session felt. Trust the weekly quiz (no hints), the monthly transfer task, the calibration of their confidence against their answers, and how far up the hint ladder they climb. If these do not improve over a few weeks, say so, and change the method.

## An honest note on the evidence

The research behind this is strongest for retrieval practice, spacing and giving feedback; moderate for self-explanation, teach-back, prediction before reveal and fading support; weak or mixed for interleaving and for most code-specific exercises. Almost all of it comes from students and short lab tasks, not working engineers learning a codebase. This design is a set of well-motivated bets. If asked, say so, and point to `docs/research/retention-techniques-for-code-walkthroughs.md`.

## What this skill does not do

- It does not read or write the learner's notes or vault.
- It does not explain code it has not read.
- It does not run the app or the tests unless asked. It names the command.
- It does not edit the code. If they want a change, point them to `vbench-tdd`.
- It does not replace the use case or the ADRs. It sends the reader to them.
- It does not teach the whole codebase at once. One use case, one path, a step or two a day.
