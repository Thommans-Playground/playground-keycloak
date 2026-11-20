# Memory science: techniques for durable retention and transfer, applied to a guided code walkthrough

Method note: figures marked (PRIMARY) were read in the paper's own text this session (Rowland 2014, Pan & Rickard 2018 abstracts/full text via PDF). Others come from search-result abstracts or secondary summaries and are marked (secondary). Items from my background knowledge that I could not verify are placed under Gaps, not Cited Findings. Hedges g / Cohen d are in SD units; roughly 0.2 small, 0.5 medium, 0.8 large.

## 1. Retrieval practice / testing effect

### Takeaway
Testing beats restudy reliably (about g 0.5 across meta-analyses, in labs and classrooms), with larger effects for recall than recognition, with feedback, and at delays of a day or more. Transfer to new questions is real but smaller (d about 0.4) and can vanish when the practice is shallow. There is almost no direct evidence for programming/code comprehension specifically.

### Cited Findings
- Rowland 2014 (Psychological Bulletin 140(6)), testing vs restudy: random-effects overall g = 0.50 (CI 0.42-0.58); published studies gave larger effects than unpublished (possible publication bias, effects still reliable). (PRIMARY) — [Rowland 2014 PDF](https://courseware.epfl.ch/assets/courseware/v1/fdde2f0aa590bf3b1324077a6bf1540c/asset-v1%3AEPFL%2BDEMO%2B2020%2Btype%40asset%2Bblock/Rowland2014-meta-analysis.pdf)
- Same paper, format: cued recall g = 0.72, free recall g = 0.81, recognition g = 0.36; recall tests give larger benefits than recognition (supports the "effortful retrieval" account). (PRIMARY) — [Rowland 2014](https://courseware.epfl.ch/assets/courseware/v1/fdde2f0aa590bf3b1324077a6bf1540c/asset-v1%3AEPFL%2BDEMO%2B2020%2Btype%40asset%2Bblock/Rowland2014-meta-analysis.pdf)
- Same paper, delay: retention interval >= 1 day g = 0.69 vs < 1 day g = 0.41. (PRIMARY) — [Rowland 2014](https://courseware.epfl.ch/assets/courseware/v1/fdde2f0aa590bf3b1324077a6bf1540c/asset-v1%3AEPFL%2BDEMO%2B2020%2Btype%40asset%2Bblock/Rowland2014-meta-analysis.pdf)
- Same paper, feedback: with feedback g = 0.73 (CI 0.61-0.86), without g = 0.39 (CI 0.29-0.49), so testing still helps without feedback. Among feedback studies, delayed feedback g = 1.38 (k = 6) vs immediate g = 0.66 (k = 46); author warns this is few studies and confounded with retention interval. Low initial accuracy (<50%) with feedback gave g = 0.99, vs 0.68 (51-75%) and 0.40 (>75%), i.e. harder retrieval plus feedback helps more; author calls this a constrained dataset. (PRIMARY) — [Rowland 2014](https://courseware.epfl.ch/assets/courseware/v1/fdde2f0aa590bf3b1324077a6bf1540c/asset-v1%3AEPFL%2BDEMO%2B2020%2Btype%40asset%2Bblock/Rowland2014-meta-analysis.pdf)
- Classroom: Yang, Luo, Vadillo, Yu & Shanks 2021 (Psychological Bulletin 147(4):399-435), 222 independent studies, about 48,000 students, overall g = 0.499; moderators include feedback, test-format consistency, number of repetitions. Effects extend beyond facts to conceptual/problem-solving (secondary summary). (secondary) — [X-MOL abstract](https://www.x-mol.com/paper/1390918175115857920); [commentary](https://tipsforteachers.substack.com/p/research-bite-4-testing-quizzing)
- Adesope, Trevisan & Sundararajan 2017 (Review of Educational Research 87(3):659-701), meta-analysis of practice testing; practice tests beat restudy and other controls, with moderators including feedback. One secondary source says its multiple-choice vs short-answer finding is the opposite of Rowland's (MC larger) — I could not read its numbers (study counts also conflict across sources: 118 vs 217). So format conclusions are contested. — [Adesope 2017 listing](https://rex.libraries.wsu.edu/esploro/outputs/journalArticle/Rethinking-the-Use-of-Tests-A/99900601154801842); [Klingenstein summary](https://www.klingensteincenter.org/klingbrief/standardizing-retrieval)
- Transfer: Pan & Rickard 2018 (Psychological Bulletin 144(7):710-756): 192 effect sizes, 122 experiments, N = 10,382; testing vs non-testing re-exposure transfer d = 0.40 (CI 0.31-0.50). Transfer is greatest across test formats, to application and inference questions, and medical-diagnosis problems; weakest to rearranged stimulus-response items, to untested material seen in initial study, and to worked-example problems. Response congruency, elaborated retrieval practice and initial test performance strongly drive transfer. After publication-bias correction (PET-PEESE), intercept predictions were often near zero transfer when none of those moderators was present. (PRIMARY) — [Pan & Rickard 2018](https://sc-pan.github.io/pdf/PR_2018.pdf)
- Karpicke & Blunt 2011 (Science 331:772-775), 200 students, science texts: retrieval practice vs concept mapping, similar on immediate test, retrieval group about 50% better a week later, including on inference questions and a concept-map criterion test; students predicted concept mapping would work better. (secondary: press/abstract; original not read) — [Purdue summary](https://www.purdue.edu/newsroom/research/2011/110120KarpickeScience.html); [PMC commentary](https://pmc.ncbi.nlm.nih.gov/articles/PMC3577217)
- Dunlosky, Rawson, Marsh, Nathan & Willingham 2013 (Psychological Science in the Public Interest 14(1):4-58): ten techniques rated; practice testing and distributed practice = high utility; summarization, highlighting, rereading, keyword mnemonic, imagery for text = low. (secondary) — [Psychological Science summary](https://www.psychologicalscience.org/?p=82014); [ScienceDaily](https://www.sciencedaily.com/releases/2013/01/130110111734.htm)
- Programming evidence: the only items found were an arXiv preprint (LLM-generated retrieval-practice questions in two data-science courses, about 60 students; instructors had to vet generated questions) and an unverified intro-programming study (Jiang 2022, J. Information Systems Education) seen only via a blog. Neither verified. — [arXiv 2507.05629](https://arxiv.org/html/2507.05629v2)

### Inferences
- For a walkthrough, "predict/recall then reveal" questions (cued or free recall, "what does the guard do when the token is expired?") should outperform "does that make sense?" or multiple-choice recognition. Expected benefit is largest when checked a day or more later.
- Because transfer is conditional (Pan & Rickard), questions should be application/inference style ("what would break if this port were removed?") and recall should be elaborated and answered correctly most of the time (initial accuracy high enough to support transfer, but not trivial). There is a tension: Rowland's feedback-plus-low-accuracy result favors hard retrieval, Pan & Rickard favors good initial performance; treat as "moderately hard with feedback", not as a settled optimum.
- Feedback timing: immediate feedback is the safe default in a conversation; the delayed-feedback advantage is from few studies and confounded.

### Gaps
- No peer-reviewed study found of retrieval practice on code comprehension or onboarding; effect size for software walkthroughs is unknown.
- MC vs short-answer: meta-analyses disagree; I could not read Adesope's numbers.
- Roediger & Karpicke 2006 (rereading beats testing at 5 minutes, testing wins at 2 days/1 week) and McDaniel et al. 2007 (short-answer practice > MC practice) are well known to me but I did not verify them this session.

## 2. Spacing and schedules

### Takeaway
Spacing beats massing, and the best gap grows with how long you need to remember, but the optimal gap as a proportion of the retention interval shrinks as the interval grows (no fixed 10-20% rule). Expanding schedules mainly help short-term retention; what matters for long-term retention is not testing too soon and spacing repeats.

### Cited Findings
- Cepeda, Pashler, Vul, Wixted & Rohrer 2006 (Psychological Bulletin 132:354-380), verbal recall meta-analysis: the inter-study interval that maximises retention increases as the retention interval increases; counts of studies/assessments differ across secondary sources, so verify numbers in the paper. (secondary) — [PubMed](https://pubmed.ncbi.nlm.nih.gov/16719566/); [full text copy](https://www.evullab.org/pdf/CepedaPashlerVulWixtedRohrer-PB-2006.pdf)
- Cepeda, Vul, Rohrer, Wixted & Pashler 2008 (Psychological Science 19(11):1095-1102), 1,354 participants, gaps up to 3.5 months, tests up to 1 year: optimal gap rises with test delay; as a proportion of test delay the optimal gap falls (about 20-40% for a 1-week test per the PDF text). Flat "10-20%" summaries are not supported by the paper. (secondary, PDF text via search tool) — [PubMed](https://pubmed.ncbi.nlm.nih.gov/19076480/); [PDF](https://www.evullab.org/pdf/CepedaVulRohrerWixtedPashler-PS-2008.pdf)
- Karpicke & Roediger 2007 (JEP:LMC): expanding retrieval gave better results on an immediate test, but equal spacing was better on a test 2 days later; delaying the first retrieval is what helped long-term retention. Karpicke & Roediger 2010 found no expanding-vs-equal difference at 1 week with text. Kang, Lindsey, Mozer & Pashler 2014 found equivalent recall at 8 weeks. (secondary) — [Wash U record](https://profiles.wustl.edu/en/publications/expanding-retrieval-practice-promotes-short-term-retention-but-eq/); [Kang et al. 2014](https://home.cs.colorado.edu/~mozer/Research/Selected%20Publications/reprints/KangLindseyMozerPashler2014.pdf)
- Spacing also helped inductive learning (paintings by 12 artists): Kornell & Bjork 2008 (Psychological Science), with learners rating massing as more effective; a replication reported a medium-sized spacing advantage, though a 2014 Frontiers replication of Experiment 2 asked whether spacing is "really" the friend of induction. (secondary) — [PubMed](https://pubmed.ncbi.nlm.nih.gov/18578849/); [PMC replication](https://pmc.ncbi.nlm.nih.gov/articles/PMC3978334)

### Inferences
- Practical schedule for a learner over days to weeks (my synthesis from the above, not a validated protocol): re-ask key items at the end of the session, next day, about 3-4 days later, then about 1-2 weeks later. The first re-test should not be immediate. If the aim is to still know it in a month, gaps of roughly a week fit the 2008 ridgeline better than daily repeats; for a one-week horizon, 1-2 days.
- Expanding vs fixed is not worth engineering; simple fixed or loosely expanding gaps suffice.

### Gaps
- Cepeda 2006 exact counts unverified (sources conflict).
- No evidence found on spacing for code walkthroughs specifically; evidence is verbal material, facts, categories.
- Anki/SM-2-style algorithms are not backed by a primary source I verified.

## 3. Interleaving vs blocking, varied practice

### Takeaway
Interleaving helps on average (g about 0.42) but is highly heterogeneous; it helps most when categories are similar to each other and complex, and can hurt for word/text material. For a novice learning a single new codebase, interleaving is a later-stage tool, not a first-pass default.

### Cited Findings
- Brunmair & Richter 2019 (Psychological Bulletin 145(11):1029-1052): 59 studies, 238 effect sizes; overall Hedges g = 0.42, I-squared = 77%. Larger when categories are similar and items within category are dissimilar, and for complex materials; blocking won for word-based studies (g = -0.39); authors advise caution with expository texts. Math effect was small but significant in the final version. (secondary) — [PubMed](https://pubmed.ncbi.nlm.nih.gov/31556629/); [X-MOL](https://www.x-mol.com/paper/1213055298318831616); [corrigendum note](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6813467/); [PMC summary](https://pmc.ncbi.nlm.nih.gov/articles/PMC10950551)
- Kornell & Bjork 2008: interleaved (spaced) exemplars improved category induction even though learners judged blocking better (see section 2). (secondary) — [PubMed](https://pubmed.ncbi.nlm.nih.gov/18578849/)
- Boundary: Chen, Castro-Alonso, Paas & Sweller 2018 (Frontiers in Psychology) argue desirable difficulties turn undesirable under high element interactivity and low expertise (working-memory overload); worked-example and expertise-reversal literature (Kalyuga et al. 2003) shows guidance helps novices and can hurt experts. This is a theoretical argument from one research camp; secondary reading only. — [Frontiers 2018](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2018.01483/pdf); [summary notes](https://notes.andymatuschak.org/z2kL5dsbU6myECcr4Cn7ZGc)

### Inferences
- Walkthrough: teach the first use case blocked and guided (worked example). Once two flows are known, interleave: "here is a snippet; which layer does it belong in, and is it domain, port or adapter?" mixing examples from different use cases (discrimination practice on similar categories, which the meta-analysis favors).
- Varied practice (different use cases through the same layers) is a plausible transfer aid, but I found no verified meta-analytic number here.

### Gaps
- No evidence for interleaving in code reading or software architecture learning.
- Rohrer & Taylor 2007 and Rohrer's classroom math studies (large effects) known from memory only; not verified.

## 4. Desirable difficulties, illusions of competence

### Takeaway
Performance during learning is a poor guide to durable learning: conditions that feel fluent (rereading, massing, watching an explanation) inflate confidence and often depress later retention, while harder conditions (testing, spacing, interleaving) feel worse and work better. Difficulty is only desirable when the learner can still succeed with effort.

### Cited Findings
- Soderstrom & Bjork 2015 (Perspectives on Psychological Science) review: manipulations can raise in-training performance while lowering long-term learning, and vice versa; performance during instruction is an unreliable index of learning. Bjork & Bjork 2011 chapter ("Making things hard on yourself, but in a good way"): desirable difficulties, storage vs retrieval strength; value depends on learner knowledge and support. (secondary summaries only) — [Research bite summary](https://tipsforteachers.substack.com/p/research-bite-23-learning-versus); [Bjork & Bjork chapter copy](https://www.unh.edu/teaching-learning-resource-hub/sites/default/files/media/2023-06/itow-introducing-desirable-difficulties-into-practice-and-instruction-bjork-and-bjork.pdf)
- Learners misjudge: students expected concept mapping to beat retrieval (Karpicke & Blunt 2011) and rated massed study better than spaced even after worse test scores (Kornell & Bjork 2008); see sections 1-2 for sources. Learners also avoid retrieval practice because of mistaken beliefs about its value, but did engage more after experiencing the effect themselves (secondary). — [Karpicke & Blunt summary](https://www.purdue.edu/newsroom/research/2011/110120KarpickeScience.html); [PubMed](https://pubmed.ncbi.nlm.nih.gov/18578849/)
- Dunlosky 2013 rated rereading and highlighting low utility. (secondary) — [Psychological Science summary](https://www.psychologicalscience.org/?p=82014)
- Cognitive load boundary: see Chen et al. 2018 in section 3; some desirable-difficulty effects fail to replicate or reverse with high-load material or low expertise. — [Frontiers 2018](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2018.01483/pdf)

### Inferences
- A new engineer will say "that all makes sense" after a clear explanation; that feeling is not evidence of retention. Use a tiny recall prompt as the evidence.
- Keep difficulty at "effortful but answerable": give a cue or hint ladder rather than leaving the learner stuck, since novices facing high-interactivity code may be overloaded.

### Gaps
- Fluency-illusion primary papers (e.g. Koriat & Bjork on foresight bias; Kornell & Bjork 2007 on study choices) not retrieved this session.
- Desirable-difficulty replication status is mixed, and I have no systematic replication audit.

## 5. Generation, pretesting, prediction, hypercorrection

### Takeaway
Generating an answer beats reading it (d about 0.4), and a failed guess before the answer is shown can help later learning, especially when feedback follows promptly and the guess was confidently wrong (hypercorrection). Boundary conditions are real.

### Cited Findings
- Bertsch, Pesta, Wiscott & McDaniel 2007 (Memory & Cognition 35(2):201-210): generation effect, 86 studies, 445 effect sizes, overall about d = 0.40; cued recall about 0.55, recognition about 0.46 (those subtype figures via a 2023 review citation). (secondary) — [PubMed](https://pubmed.ncbi.nlm.nih.gov/17645161/); [Schindler & Richter 2023](https://link.springer.com/content/pdf/10.1007/s10648-023-09758-w.pdf)
- Kornell, Hays & Bjork 2009 (JEP:LMC 35(4):989-998): unsuccessful retrieval attempts before study enhanced later learning (six experiments, weak-associate word pairs). Richland, Kornell & Kao 2009 extended to a text essay. Replicated by others, but Grimaldi & Karpicke 2012 found no benefit with a brief delay between the attempt and study; Knight et al. 2012 found benefit for weakly related pairs but impairment for unrelated pairs. No pretesting meta-analysis was found. (secondary) — [PubMed](https://pubmed.ncbi.nlm.nih.gov/19586265/); [search roundup incl. Grimaldi & Karpicke](https://learninglab.psych.purdue.edu/downloads/2012/2012_Grimaldi_Karpicke_MC.pdf); [Knight 2012](https://amalab.uta.edu/files/2021/12/knight-2012-2.pdf)
- Hypercorrection: Butterfield & Metcalfe 2001: high-confidence errors are more likely to be corrected on retest than low-confidence errors; the effect survives equal feedback time, delay, and multiple-choice formats (Butler & Roediger 2008, Fazio & Marsh 2010), and with children; partly survives controlling for item difficulty; the leading account is attentional surprise. (secondary; original not read) — [PMC3970786](https://pmc.ncbi.nlm.nih.gov/articles/PMC3970786); [Duke thesis](https://dukespace.lib.duke.edu/items/d6ab09ca-f55c-4efb-9d32-2788bc5838b2)

### Inferences
- Ask for a prediction before each reveal ("before I show the handler, what do you expect the order of checks to be?"), and ask for a confidence rating ("sure, or guessing?"). Confident wrong predictions are the most valuable teaching moments.
- Pretesting works best with plausible, semantically related guesses, followed immediately by the answer; avoid guessing on arbitrary or unrelated items (Knight 2012 impairment).

### Gaps
- Evidence is for words, pairs, facts and short texts, not code.
- Magnitude of pretesting benefit not established here (no meta-analysis found).

## 6. Sleep, delay, chunking (brief)

### Takeaway
Little verified material was retrieved here; treat as background only.

### Cited Findings
- Delay itself: testing benefits are larger at >= 1 day (g = 0.69) than < 1 day (g = 0.41), see section 1; delaying the first retrieval improves long-term retention (Karpicke & Roediger 2007, section 2).

### Inferences
- Splitting a long walkthrough across days and putting a recall check at the start of the next session combines delay, spacing and a night's sleep with no extra work.
- Chunk by use-case step (one flow, one layer at a time), consistent with working-memory limits under the cognitive-load view in section 3.

### Gaps
- I did not retrieve or verify sleep-consolidation sources (e.g. Diekelmann & Born 2010, Nature Reviews Neuroscience) or chunking sources (Miller 1956; Chase & Simon 1973); I know them from memory only and do not cite them as findings.

## 7. One low-effort application per technique in a conversational code walkthrough

### Takeaway
Each technique maps to a single conversational move that needs no tooling.

### Cited Findings
- (Applications are design suggestions, not findings; evidence for each is in sections 1-6.)

### Inferences
- Retrieval practice: after each step, ask one cued-recall question with the code hidden ("Where is the role checked, and why there?"); reveal and give feedback immediately; end the session with 3 questions, no peeking.
- Spacing: open the next session with 2-3 questions from the previous one, then re-ask the missed ones about 3-4 days and about 1-2 weeks later; keep a short "to re-ask" list in the walkthrough notes.
- Interleaving: after two use cases are covered, mix snippets from both and ask "which layer is this and why?"; block the first pass.
- Desirable difficulty / illusion of competence: replace "got it?" with a retrieval prompt; if the learner struggles give a hint ladder (hint, partial, answer) rather than the answer.
- Generation / pretesting / hypercorrection: before each reveal, "predict what the next function does and how sure are you (guess, fairly sure, certain)?", then show the code and call out confident misses.
- Transfer: finish with an application question that changes the scenario ("add a new role; which files change?"), since Pan & Rickard show transfer is strongest to application and inference questions.
- Delay/chunking: one flow per sitting; recall opener next day.

### Gaps
- None of these combined protocols has been tested in a software onboarding setting; effects stack in theory but combined magnitudes are unknown.
