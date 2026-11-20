# AI-assisted learning and AI tutors, especially for programming

Verification note: sources marked (fetched) were read from the primary page or arXiv HTML in this session. Sources marked (search-only) were confirmed only through search-result summaries, so their numbers need a check against the paper. Items I could not verify are in each Gaps list. Wording like "preprint" and "vendor" is flagged inline.

## 1. What studies show about generative AI and learning outcomes (benefits and harms)

### Takeaway
The evidence converges on one conclusion: unrestricted AI raises performance during the task and lowers learning when the AI is gone, while AI that is restricted (hints, explanations, conceptual questions) largely removes the harm. How the learner uses the AI matters more than whether they use it. Almost all the programming evidence is from novices or crowd workers in short sessions, not from professional engineers over months.

### Cited Findings
- Bastani et al., PNAS 2025 (peer-reviewed; field experiment, about 1,000 high-school maths students in Turkey, four 90-minute sessions). GPT Base (a plain ChatGPT-like interface) improved practice performance by 48% but students scored 17% worse on the exam after access was removed. GPT Tutor (teacher input, hints instead of direct answers) improved practice performance by 127% and left exam scores about equal to control. Students overestimated their learning, including high achievers. — [Wharton summary](https://knowledge.wharton.upenn.edu/article/without-guardrails-generative-ai-can-harm-education/) (fetched); paper metadata at [EconPapers](https://econpapers.repec.org/RePEc:nas:journl:v:122:y:2025:p:e2422633122), DOI 10.1073/pnas.2422633122. The PNAS page returned HTTP 403, so the exact numbers come from the Wharton summary (the authors' school) and one commentary, not the paper text.
- Shen and Tamkin (Anthropic), "How AI Impacts Skill Formation", arXiv 2601.20245 v2, January 2026 (preprint; vendor research). Randomized, between-subjects, learning an unfamiliar async Python library (Trio). 52 analysed participants (26 AI, 26 control); the paper also reports 50 recruited, 53 completing all parts and 51 screen recordings, so counts vary by section. Paid crowd workers, 35 minutes for two tasks, then a 27-point quiz taken without AI. The AI group (chat-based GPT-4o) scored 4.15 points lower, about 17% of the quiz, Cohen's d = 0.738, p = 0.010. No significant speed gain on average; some participants spent up to 11 minutes composing queries. Quiz covered conceptual understanding, code reading and debugging, with the largest gap in debugging per the abstract. — [arXiv abstract](https://arxiv.org/abs/2601.20245), [HTML](https://arxiv.org/html/2601.20245v2) (fetched)
- Same study, six interaction patterns (clusters of 2 to 7 people, descriptive only, not statistically tested). Low scorers (about 24-39% on the quiz): AI Delegation (n=4), Progressive AI Reliance (n=4), Iterative AI Debugging (n=4). High scorers (about 65-86%): Generation-Then-Comprehension (n=2), Hybrid Code-Explanation (n=3), Conceptual Inquiry (n=7; fastest of the high scorers). — [arXiv HTML](https://arxiv.org/html/2601.20245v2) (fetched)
- Same study's stated limits: one library, one hour, chat interface only (agentic or autocomplete tools may differ), crowd workers without job incentives, no human-assistance comparison, no code-writing items in the quiz. — [arXiv HTML](https://arxiv.org/html/2601.20245v2) (fetched)
- Lehmann, Cornelius and Sting, "AI Meets the Classroom: When Do Large Language Models Harm Learning?", arXiv 2409.09047 (preprint; v1 was titled around ChatGPT and coding). Substituting the LLM for own work (generating exercise solutions) increases topic volume but decreases understanding per topic. Complementing (asking for explanations) does not increase volume but increases understanding. Two lab experiments showed no significant overall effect; a field study that saw only substitutive use found a significant long-term decline; LLM access widened the gap between low and high prior-knowledge students. — [arXiv](https://arxiv.org/abs/2409.09047) (search-only; I did not read the methods or effect sizes, so check before quoting numbers)
- Fan et al., "Beware of Metacognitive Laziness", arXiv 2412.09315, later in BJET (DOI 10.1111/bjet.13544 listed; journal publication not confirmed by me). Randomized experiment, 117 university students, four conditions (ChatGPT, human expert, writing-analytics tools, no tool). The ChatGPT group improved essay scores more, but knowledge gain and transfer did not differ significantly. The ChatGPT group showed fewer metacognitive processes (for example evaluation, orientation). Authors define "metacognitive laziness" as offloading metacognitive load to the AI. — [arXiv](https://arxiv.org/pdf/2412.09315) (search-only)
- Prather et al., "The Widening Gap: The Benefits and Harms of Generative AI for Novice Programmers", arXiv 2405.17739 (2024). 21 CS1 students (C++, small US university), 35 minutes, Copilot and ChatGPT available, eye tracking and think-aloud. 20 of 21 completed a working program (search summary says over 95% success), but 11 of 21 showed no metacognitive difficulties; struggling students kept an "illusion of competence" while stronger students used AI to move faster. The paper adds three GenAI-related difficulties to five earlier ones (Forming, Dislodging, Assumption, Location, Achievement): Progression (falling behind without noticing, from false confidence), Interruption (losing focus to constant suggestions) and Mislead (the tool steers down a wrong path). Recommends teaching metacognition explicitly and using scaffolded tools that guide without giving full answers. — [arXiv HTML](https://arxiv.org/html/2405.17739v1) (fetched; the last ~23k characters of the page were not read)
- Lee et al. (Microsoft Research and Carnegie Mellon), CHI 2025, "The Impact of Generative AI on Critical Thinking: Self-Reported Reductions in Cognitive Effort and Confidence Effects From a Survey of Knowledge Workers". Survey of 319 knowledge workers (professionals, not students). Higher confidence in GenAI was associated with less critical thinking; higher self-confidence with more. 58 participants reported difficulty verifying AI output because of limited domain knowledge. Critical thinking shifts toward verification, integration and "task stewardship". Self-report and correlational, not a learning outcome. — [author PDF](https://advait.org/files/lee_2025_ai_critical_thinking_survey.pdf), [summary](https://www.rdworldonline.com/microsoft-and-cmu-genai-may-undercut-critical-thinking-but-theres-an-antidote/) (search-only)
- Kosmyna et al. (MIT Media Lab), "Your Brain on ChatGPT", arXiv 2506.08872 (preprint, not peer reviewed). 54 participants in sessions 1-3 (LLM, search engine, brain-only essay writing), only 18 in the crossover session 4. EEG connectivity lowest in the LLM group; LLM group reported least ownership and struggled to quote their own essays. The authors warn the results are preliminary. Essay writing, not programming; weak evidence for programming claims. — [MIT Media Lab](https://www.media.mit.edu/publications/your-brain-on-chatgpt/) (search-only)
- A mastery-versus-performance framing study (Applied Cognitive Psychology, via PsyPost): 104 university students using ChatGPT; those prompted with a mastery goal gained more conceptual knowledge than a performance-goal group; only declarative knowledge was tested. — [PsyPost](https://www.psypost.org/how-the-desire-to-outshine-peers-ruins-learning-with-chatgpt/) (search-only, secondary; original not located)
- Novice Copilot work by Prather and colleagues found students struggled with both cognitive and metacognitive difficulties when using Copilot; related paper "It's Weird That it Knows What I Want" (Prather et al., arXiv 2304.02491). — [arXiv 2304.02491](https://ar5iv.labs.arxiv.org/html/2304.02491) (search-only)

### Inferences
- The dividing line across Bastani, Lehmann and Shen/Tamkin is the same: asking the AI to produce the answer is harmful; asking it to explain, quiz or give hints is neutral to beneficial. A code-along tutor should therefore let the learner produce, with the AI as explainer and checker.
- The fastest-finishing behaviour (delegation) is the worst for learning in the Shen and Tamkin data, so speed or "task done" is the wrong success metric for a tutor.
- The professional-engineer evidence is thin: Lee et al. is survey data on knowledge workers, and Shen and Tamkin used paid crowd workers. Treat claims about senior engineers as extrapolation.
- The Bastani result implies that "guardrails" removed the harm but did not produce a net exam gain; a tutor needs more than refusing to give answers to improve learning.

### Gaps
- I could not open the PNAS paper (403), so the exact exam effect sizes, standard errors and the wording of the GPT Tutor prompt are unverified; I have only the 48%, 127% and 17% figures from secondary summaries and the authors' school.
- Effect sizes for Lehmann et al. and Fan et al. were not read.
- I did not find "The Robots are Here" (Prather et al., 2023) in search results; I could not verify its title, venue or findings. Do not cite it without checking.
- Anthropic's own blog post on the skill-formation study was not found in search; only the arXiv paper was read.
- No long-term (months) study of AI use and programming skill by professional engineers was found.

## 2. Why learners over-rely on AI and feel more competent than they are; what reduces it

### Takeaway
Fluent, correct-looking explanations feel like understanding, and learners also feel their immediate performance is their learning. Evidence of overestimation with AI is consistent across several studies; the testing-effect literature gives the best-supported general countermeasure (retrieval and attempt before reveal). Direct evidence that specific tutor interventions reduce AI-induced overconfidence is sparse.

### Cited Findings
- Bastani et al.: students using AI (including the hint-based tutor) believed they had learned more than they had. — [Wharton summary](https://knowledge.wharton.upenn.edu/article/without-guardrails-generative-ai-can-harm-education/) (fetched); a Hechinger/Penn-based summary says students with the hint tutor still thought they did much better on the test than they did — [Devdiscourse summary](https://www.devdiscourse.com/article/technology/3843571-chatgpt-boosts-student-performance-but-may-create-dangerous-illusion-of-understanding) (search-only, secondary).
- Prather et al. 2024: struggling novices finished with an "illusion of competence" and cognitive dissonance about their ability; new difficulties include Progression (false confidence about being on track). — [arXiv HTML](https://arxiv.org/html/2405.17739v1) (fetched)
- Chile/Cenia study (illusion of explanatory depth): a group chatting with ChatGPT overestimated their ability to explain the phenomena more than a group that read the same text and a control, and their later explanations were rated lower by two evaluators. Authors caution it does not show ChatGPT is bad for learning in general. Sample size not seen. — [PsyPost summary via search](https://www.psypost.org/?p=232489) (search-only, secondary; original paper not located)
- Fan et al.: the AI group showed fewer evaluation and orientation metacognitive processes ("metacognitive laziness") while gaining on the assisted task but not on knowledge or transfer. — [arXiv](https://arxiv.org/pdf/2412.09315) (search-only)
- Lee et al.: more confidence in the AI went with less critical thinking, and verification was hard for people lacking domain knowledge. — [author PDF](https://advait.org/files/lee_2025_ai_critical_thinking_survey.pdf) (search-only)
- Classic retrieval-practice evidence: in Roediger and Karpicke 2006 (Psychological Science 17(3), 249-255), repeated studying beat repeated testing on a 5-minute test (about 81% vs 75% recall), but after one week testing won (about 61% vs 40%), even though repeated studying raised learners' confidence. Small, passage-based; percentages are from a university press summary. — [WashU summary](https://source.washu.edu/2006/03/repeated-testtaking-better-for-retention-than-repeated-studying-research-shows/), [paper PDF](https://psychology.ecu.edu/wp-content/pv-uploads/sites/216/2019/03/Roediger-Karpicke-2006.pdf) (search-only)
- Shen and Tamkin's high-scoring patterns (conceptual questions only; generate then ask comprehension questions) show learners who stay cognitively engaged retain more, though groups are tiny. — [arXiv HTML](https://arxiv.org/html/2601.20245v2) (fetched)
- Prather et al. recommend teaching metacognitive skills explicitly and using code replays to prompt reflection; these are suggestions, untested in that paper. — [arXiv HTML](https://arxiv.org/html/2405.17739v1) (fetched)

### Inferences
- Because the confidence signal is unreliable in the AI condition, a tutor should not trust learner self-report ("got it") and should instead require a small observable act (predict, answer, explain back).
- Predict-before-reveal, retrieval checks and spaced review follow from the testing effect plus the overconfidence evidence, but I found no study that tests these inside an LLM programming tutor. Treat them as well-motivated design hypotheses, not proven for this setting.
- A confidence rating before feedback (learner states how sure they are, then sees the answer) is a cheap way to expose miscalibration; this is my suggestion, not a finding from a source here.

### Gaps
- No source found that directly measures whether prediction prompts or hint ladders reduce AI-induced overconfidence in programming.
- The Chile illusion-of-explanatory-depth paper itself, with sample size and effect sizes, was not located.
- Did not search the broader cognitive-psychology literature (desirable difficulties, generation effect, worked-example and expertise-reversal effects) beyond Roediger and Karpicke; the report writer may want separate coverage.

## 3. Effective AI tutor design: Socratic questioning, hint ladders, guardrails, tutoring research

### Takeaway
Human tutoring and step-based tutoring are both strong (roughly 0.8 SD against no tutoring in VanLehn's review), far below Bloom's 2 SD. Recent trials show a carefully pedagogically designed AI tutor can match or beat active learning in a short, well-scoped unit (Kestin), but at scale usage and engagement are the weak point (Khanmigo), and AI that supports human tutors helps weaker tutors most (Tutor CoPilot).

### Cited Findings
- Bloom 1984: tutoring plus mastery learning produced about 2 SD over conventional classes, from small studies. Von Hippel (Education Next, 2024) argues the figure does not hold up: tests matched the taught content, tutored students got far more testing and feedback (he estimates about half the effect), and tutors got training others did not; most studies land at about 0.4-0.9 SD. — [Von Hippel, Education Next (PDF)](https://www.educationnext.org/wp-content/uploads/2024/03/ednext_XIV_2_von_hippel.pdf) (search-only; the ~0.4-0.9 range comes from a secondary commentary)
- VanLehn 2011, Educational Psychologist 46(4), 197-221, DOI 10.1080/00461520.2011.611369: human tutoring d = 0.79 and step-based intelligent tutoring systems d = 0.76 against no tutoring; answer-based and substep-based systems were compared by interface granularity. One summary gives substep-based as 0.40 (the 0.41 I was asked about was not confirmed). — [ERIC record](https://eric.ed.gov/?id=EJ946764) (search-only)
- Kestin et al., Scientific Reports 2025 (15:17458, DOI 10.1038/s41598-025-97652-6): randomized crossover in a Harvard undergraduate physics course, 194 students, custom AI tutor at home versus in-class active learning, two topics (surface tension, fluid flow). Median learning gains from pre-test were more than double the active-learning group's; post-test medians reported as 4.5 vs 3.5 against a pre-test median of 2.75; students used about 49 minutes versus 60. The tutor was built around the instructor's learning objectives, problems and feedback. Short term, one university, one course. I did not find a standardized effect size. The Nature page redirected and was not fetched. — [PMC full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC12179260/), [Miller summary](https://michellemillerphd.substack.com/p/r3-37-july-15-2025-how-do-tutoring) (search-only)
- Wang, Ribeiro, Robinson, Loeb and Demszky, "Tutor CoPilot", arXiv 2410.03017 (preprint; version differences). RCT, human tutors helped by AI suggestions: v2 reports 900 tutors and 1,800 K-12 students (earlier versions said 700+ tutors and about 1,000 students). Exit-ticket mastery rose from 62% to 66% (p<0.01), up to 9 percentage points for lower-rated or less-experienced tutors; cost about $20 per tutor per year; some suggestions were not grade-level appropriate. — [arXiv](https://arxiv.org/abs/2410.03017) (search-only)
- Oreopoulos and Low, "One Click Away: AI Tutoring with Khanmigo in a Two-Year School Experiment", NBER w35620 / EdWorkingPapers 26-1551 (working paper, not peer reviewed). Cluster randomized, 18 Tennessee middle schools. Effect about 0.06-0.08 SD over a school year (1.3 national percentile ranks per term), implied about 0.14 SD for full active participation, similar to Khan Academy practice without the AI. The median student messaged the tutor on about a third of practice days and rarely when making mistakes; most messages were bare answers or suggested-prompt clicks. Hechinger coverage says that when the tutor withheld answers and asked questions, students largely stopped using it. — [NBER](https://www.nber.org/papers/w35620), [EdWorkingPapers PDF](https://edworkingpapers.com/sites/default/files/ai26-1551.pdf) (search-only)
- Liffiton, Sheese, Savelka and Denny, CodeHelp, arXiv 2308.06921 (2023): an LLM assistant for programming classes with guardrails; a 52-student first-year course over 12 weeks. A follow-up (arXiv 2310.16984) analysed more than 2,500 queries: explanations were conceptually accurate in about 90% of compile-time and 75% of run-time cases, but the model often ignored the instruction not to provide solution code. Pipeline described by a third party as sufficiency check, response generation and code removal. I could not verify a SIGCSE venue. — [arXiv 2308.06921](https://arxiv.org/abs/2308.06921), [arXiv 2310.16984](https://ar5iv.labs.arxiv.org/html/2310.16984) (search-only)
- Anthropic product posture (vendor, secondary press): Claude.ai "Learning" style asks probing questions; Claude Code "Explanatory" and "Learning" output styles, the latter adding `#TODO` markers and asking the user to write short code segments; these are modified system prompts, not separate models. — [Engadget](https://www.engadget.com/ai/anthropic-brings-claudes-learning-mode-to-regular-users-and-devs-170018471/), [Tom's Guide](https://www.tomsguide.com/ai/claudes-new-learning-modes-take-on-chatgpts-study-mode-heres-what-they-do) (search-only). No outcome evidence for these modes was found.
- Bastani GPT Tutor: teacher-informed prompts that give hints rather than answers removed the exam harm (see section 1). — [Wharton summary](https://knowledge.wharton.upenn.edu/article/without-guardrails-generative-ai-can-harm-education/) (fetched)

### Inferences
- VanLehn's finding that granularity of feedback matters (step-level beats answer-level) supports a tutor that checks each step of a walkthrough rather than only the end result.
- Kestin's gain came from a tutor tightly scoped to specific objectives and problems; a generic Socratic prompt should not be expected to match it. The code-along tutor is tightly scoped (a known codebase and walkthrough), which resembles Kestin more than a general chatbot.
- Khanmigo shows the engagement risk of strict Socratic refusal: learners disengage. Design should give a way forward (hint ladder with an explicit "show me" escape after effort) rather than pure refusal. Whether an escape hatch harms learning is untested here.
- Because CodeHelp-style models ignore "do not give code", a prompt-only skill cannot guarantee no-answer behaviour; keep reveal steps explicit in the script and accept the risk.

### Gaps
- I did not find the exact prompt or hint-ladder structure used by Kestin et al. or Bastani's GPT Tutor; fetching the PMC full text and PNAS SI would settle this.
- No head-to-head trial comparing hint ladders with Socratic questioning in LLM tutors was found.
- Tutor CoPilot version discrepancy (700/1,000 vs 900/1,800) should be resolved against the final published version.
- Bloom's primary paper and the von Hippel PDF were not read directly.

## 4. Accuracy and trust: hallucination in code explanations, grounding, calibration

### Takeaway
LLM explanations of code are usually but not always right, and novices cannot reliably tell the difference. Measured accuracy is high (75-90% in CodeHelp queries), so a meaningful minority of errors reach learners. Grounding design (quoting real code, citing lines, verifying by running) is a sensible mitigation but I found little direct empirical evidence on it.

### Cited Findings
- CodeHelp follow-up on more than 2,500 student queries: explanations were conceptually accurate in about 90% of compile-time and 75% of run-time cases. — [arXiv 2310.16984](https://ar5iv.labs.arxiv.org/html/2310.16984) (search-only)
- Leinonen et al., "Comparing Code Explanations Created by Students and Large Language Models" (ITiCSE 2023, arXiv 2304.03938): LLM explanations were judged more accurate and easier to understand than student-written ones (about 1,000 students as baseline), but not always correct. Model used not confirmed by me. — [arXiv](https://arxiv.org/abs/2304.03938) (search-only)
- Lee et al.: 58 knowledge workers reported difficulty verifying AI output due to limited domain knowledge, and trust in the AI went with less critical thinking. — [author PDF](https://advait.org/files/lee_2025_ai_critical_thinking_survey.pdf) (search-only)
- Prather et al.: the Mislead difficulty (tool steering the learner down a wrong path) and recommendation that students learn to recognise and ignore unhelpful suggestions. — [arXiv HTML](https://arxiv.org/html/2405.17739v1) (fetched)
- Lee et al. design suggestions for tools: reasoning explanations, guided critiques and cross-references. — [R&D World summary](https://www.rdworldonline.com/microsoft-and-cmu-genai-may-undercut-critical-thinking-but-theres-an-antidote/) (search-only)

### Inferences
- A walkthrough tutor has an advantage a generic chatbot lacks: the real source file is available. Quoting exact lines with file path and line numbers, and reading the file at response time rather than from memory, removes one common hallucination class (invented code). This is a design inference, not a tested result.
- Tell the tutor to say when it has not read a file or is unsure, and to prefer "run this and look" over assertion; learners can then check claims against reality (tests, running code).
- Since novices cannot verify, accuracy matters more for them than for experts; prefer checks the learner can run themselves.

### Gaps
- No study found that measures whether line-cited or quoted-source explanations reduce hallucination or improve learner trust calibration.
- No recent (2025-2026) accuracy benchmark for explanation of code in a specific codebase was found.
- Model used in Leinonen et al. and its numeric accuracy figures were not confirmed.

## 5. Building the techniques into a prompt/skill, and how to measure learning

### Takeaway
The techniques below are supported mainly by general learning-science evidence and the interaction-pattern data above, not by direct tests inside prompt-driven code tutors. Build them in as defaults, and measure with delayed, AI-free tests and transfer tasks, because in-session performance and self-rated confidence are both unreliable under AI.

### Cited Findings
- Interaction patterns that preserved learning: ask conceptual questions, generate code then ask comprehension follow-ups, request code with explanations; patterns that harmed: delegation, progressive reliance, iterative AI debugging. — [Shen and Tamkin](https://arxiv.org/html/2601.20245v2) (fetched; small clusters)
- Substitute versus complement use predicts outcome (explanations help, solution generation hurts). — [Lehmann et al.](https://arxiv.org/abs/2409.09047) (search-only)
- Bastani GPT Tutor: hints instead of direct answers, informed by teacher input, removed the post-access exam penalty. — [Wharton summary](https://knowledge.wharton.upenn.edu/article/without-guardrails-generative-ai-can-harm-education/) (fetched)
- Anthropic's Claude Code Learning style: leaves `#TODO` markers for the learner to complete; Explanatory style narrates trade-offs. Prompt-based, no published outcome data found. — [Engadget](https://www.engadget.com/ai/anthropic-brings-claudes-learning-mode-to-regular-users-and-devs-170018471/) (search-only; vendor)
- Testing effect: retrieval beat restudy at one week although restudy raised confidence. — [Roediger and Karpicke 2006](https://psychology.ecu.edu/wp-content/pv-uploads/sites/216/2019/03/Roediger-Karpicke-2006.pdf) (search-only)
- Measurement caution: Bastani and Shen/Tamkin both measured learning on a post-test without AI, and in both the in-task metrics (practice score, completion) did not predict it; Fan et al. found essay-task gains without matching knowledge or transfer gains. — [Wharton summary](https://knowledge.wharton.upenn.edu/article/without-guardrails-generative-ai-can-harm-education/), [arXiv 2601.20245](https://arxiv.org/html/2601.20245v2), [arXiv 2412.09315](https://arxiv.org/pdf/2412.09315)
- Khanmigo's low engagement when it withheld answers is a design warning for strict Socratic modes. — [EdWorkingPapers](https://edworkingpapers.com/sites/default/files/ai26-1551.pdf) (search-only)

### Inferences
Practical patterns, each tied to the evidence above (patterns are my proposals; the cited evidence supports the direction, not the specific form):
- Predict then reveal: before showing what a code block does, ask the learner to say what they expect (output, state change, failure case), then show the real code and compare. Links to testing effect and the overconfidence evidence.
- One question per turn: keep cognitive load low and force a specific response; wait for the answer before continuing. Do not narrate the next step in the same message.
- Hint ladder with an exit: nudge question, then pointed hint (name the concept or the file and line), then partial worked step, then reveal after a real attempt. Avoids both answer-dumping (Bastani GPT Base) and disengagement from pure refusal (Khanmigo).
- Learner writes first: use TODO-style gaps (as in the Claude Code Learning style) so the learner produces the key lines, and the AI reviews rather than writes. Matches the high-scoring "conceptual inquiry" pattern.
- Generation-then-comprehension: if the learner has code generated or shown, require one explain-back or tracing question before moving on.
- Error-driven follow-ups: when the learner's answer is wrong, ask a question targeting the misconception (or have them run a test that exposes it) before correcting; log the missed concept.
- Retrieval at session start: open the next session with two or three questions on the previous session's concepts, answered without looking at notes, then reveal answers; space the harder items further out.
- Learner-generated summary at the end: ask for a three-sentence summary or a teach-back to an imagined new hire, then correct it against the source.
- Confidence then check: ask "how sure are you (1-5)" before revealing, to surface miscalibration, and show the learner their hit rate over time.
- Grounding rules in the prompt: quote real code with path and line numbers; read files rather than recall them; say "I have not checked" when so; invite the learner to run the code or test to confirm claims.
- Make "show me the answer" an explicit, visible learner choice that is logged, so over-reliance is observable rather than hidden.
Measurement ideas:
- Delayed, AI-free test: a short quiz or code-reading and debugging tasks one to two weeks later, closed-AI, mirroring Shen and Tamkin (conceptual, reading, debugging items) and Bastani (post-access exam).
- Transfer task: change a surface feature (a different endpoint, role or flow) and ask the learner to predict or modify behaviour in the same architecture.
- Teach-back: the learner explains the flow to a colleague or to the tutor with no code visible; rate against a rubric.
- Calibration: compare stated confidence with accuracy across sessions.
- Process logs: count unassisted attempts before help requests, "show me" uses, and hint level reached; Fan et al. and Shen and Tamkin both used process traces to separate engaged from delegating use.
- For a team, compare cohorts or sessions with and without the tutor on the delayed test, since in-session completion and satisfaction proved misleading.

### Gaps
- No published evidence tests predict-then-reveal, spaced openers or learner summaries specifically inside LLM programming tutors; they rest on general learning science (only retrieval practice was sourced here).
- I did not research spaced-repetition meta-analyses, the generation effect, worked-example fading or productive failure; the report writer should not attribute them to this note.
- No validated instrument for "is the learner learning" in a code-along setting was found; the measurement list is a proposal.
- No evidence found specific to professional engineers learning an unfamiliar codebase with AI over weeks.
