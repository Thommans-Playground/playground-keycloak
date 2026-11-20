# Instructional design evidence for teaching complex technical material to novices

Method note: about 16 searches. Search returned abstracts, bibliographic records and secondary summaries; I did not open full texts of the primary papers, so effect sizes are quoted only where a search snippet stated them. Items from my background knowledge that I could not verify this session are in Gaps, labelled "unverified".

## 1. Cognitive load theory: load types, split-attention/redundancy/modality, chunking and sequencing

### Takeaway
Cognitive load theory (CLT) treats working memory as the bottleneck for novices; instruction should cut extraneous load and fit intrinsic load to the learner. The main foundational reviews are Sweller, van Merriënboer & Paas (1998) and the 2019 update. The detailed effect sizes for split-attention, redundancy and modality were not verified here.

### Cited Findings
- The foundational review is Sweller, van Merriënboer & Paas (1998), "Cognitive Architecture and Instructional Design", Educational Psychology Review 10(3), 251-296. It frames CLT around working-memory constraints as determinants of instructional effectiveness — [Twente record](https://research.utwente.nl/en/publications/cognitive-architecture-and-instructional-design/)
- The update is Sweller, van Merriënboer & Paas (2019), "Cognitive Architecture and Instructional Design: 20 Years Later", Educational Psychology Review 31(2), 261-292. It revisits the architecture and the original load effects and has a section on measuring load — [Maastricht record](https://cris.maastrichtuniversity.nl/en/publications/cognitive-architecture-and-instructional-design-20years-later/)
- Kirschner, Sweller & Clark (2006), Educational Psychologist 41, 75-86, argue from CLT that minimally guided instruction (discovery, problem-based, inquiry) harms learning for novices through high load. This was contested by Hmelo-Silver, Duncan & Chinn (2007) and Schmidt et al. (2007), with a reply by Sweller, Kirschner & Clark (2007) — [secondary summary](https://louisville.edu/psychology/decaro/lab/publications-2/NewmanDeCaro2019.pdf)
- Segmenting: Rey et al. (2019), "A Meta-analysis of the Segmenting Effect", Educational Psychology Review 31, 389-419 (56 investigations, 88 comparisons). Small-to-medium effects on retention and transfer. Segmentation lowered overall cognitive load and increased learning time. Effects held for both system-paced and learner-paced segmentation. Learners with high prior knowledge gained more on retention than low-prior-knowledge learners — [MPI record](https://is.mpg.de/publications/rey2018segmenting)

### Inferences
- Split-attention, redundancy and modality are not verified here. For a text-only chat code-along the implied rules are: put the explanation next to the code line it concerns (not in a distant paragraph), do not restate the code in prose verbatim, and keep one concept per message. These are applications of the effects as I know them, not findings I verified.
- Intrinsic load rises with element interactivity. A walkthrough of an auth flow (browser, BFF, Keycloak, API, DB) has high interactivity. Sequence the steps so each introduces one new element, and name the term (OIDC, JWT) at first use.
- Concrete move: one message = one step of the flow = one code block (under about 15 lines) with a 2-3 sentence gloss, followed by one question. Show a one-line "you are here" strip of the flow in each message to avoid forcing the learner to hold the whole map in mind.
- The Rey et al. result that segmentation helps but costs time argues for pausing at step boundaries rather than mid-step. Its finding that higher prior knowledge gained more suggests it is not a novice-only device.

### Gaps
- Unverified: the exact split-attention, redundancy and modality citations (Chandler & Sweller 1991; Mayer's multimedia principles; Mayer & Moreno 2003). I did not retrieve them. Mayer's modality principle assumes spoken narration with graphics; it does not map cleanly to a text chat, so the writer should not claim it applies.
- Unverified: the germane-load construct. I recall that the 2019 update recasts it as part of intrinsic load rather than a separate load type, but I did not confirm this from the paper text.
- Not found: a reliable figure for a "right" segment length in minutes or items for text-based code explanations. No source answered this directly.

## 2. Worked examples, completion problems, fading, and expertise reversal

### Takeaway
For novices, studying worked examples beats solving equivalent problems; backward fading of solution steps eases the move to independent work. Guidance that helps novices tends to become neutral or harmful as expertise grows (expertise reversal), so scaffolding should be removed as the learner shows skill.

### Cited Findings
- Sweller & Cooper (1985), "The use of worked examples as a substitute for problem solving in learning algebra", Cognition and Instruction 2, 59-89, is the original worked-example effect. Learners who studied worked examples did better than those who solved problems. This is a lab/classroom algebra study, per a secondary summary — [Worked-example effect overview](https://en.wikipedia.org/wiki/Worked-example_effect) (weak source; bibliographic details cross-checked in several reference lists)
- Atkinson, Derry, Renkl & Wortham (2000), "Learning from examples: Instructional principles from the worked examples research", Review of Educational Research 70, 181-214, is the review that sets out instructional principles for examples — [reference confirmed via search](https://www.cambridge.org/core/books/cambridge-handbook-of-cognition-and-education/learning-how-to-solve-problems-by-studying-examples/632DFF3E1B3166EB325A59BD6028B6EA) (this page is a related Cambridge chapter, not the 2000 paper itself)
- Renkl, Atkinson, Maier & Staley (2002), "From example study to problem solving: Smooth transitions help learning", Journal of Experimental Education 70(4), 293-315. Fading removes solution steps from worked examples. In backward fading the final step is removed first, then the second-to-last, until the learner solves the whole problem. Later work reports backward fading benefits learning. I could not retrieve sample sizes or effect sizes — [secondary summary](https://link.springer.com/doi/10.1007/s11251-009-9107-8)
- Expertise reversal: Kalyuga, Ayres, Chandler & Sweller (2003), Educational Psychologist 38(1), 23-31. Guidance useful for novices can be negative for more experienced learners. Author order differs between repositories; Kalyuga-first is the common citation form — [Wollongong repository](https://ro.uow.edu.au/edupapers/136)
- Meta-analysis: Tetzlaff, Simonsmeier, Peters & Brod (2025), "A cornerstone of adaptivity - A meta-analysis of the expertise reversal effect", Learning and Instruction 98, 102142 (176 effect sizes, 60 experiments, 5,924 participants). The effect is robust across contexts, moderated by educational status and domain, grows with age, is smaller in language/humanities, and giving novices help had a larger effect than withholding help from experts — [summary](https://www.learningandthebrain.com/blog/one-size-doesnt-fit-all-teaching-experts-and-novices/) (secondary; one search result misattributed the journal, the Learning and Instruction citation is the consistent one)

### Inferences
- Concrete code-along pattern ("worked, completion, independent"): (1) fully narrate one request path (for example, login). (2) For a parallel path (for example, token refresh or deactivate), narrate all but the last step and ask the learner to say what comes next or write the next assertion. (3) Remove more steps each time until the learner predicts the whole flow and writes the failing test first.
- Completion problems (Paas 1992; van Merriënboer) are the same idea; I did not verify those citations (see Gaps).
- Expertise reversal in practice: watch for signals (learner answers before you finish, says "I know this", skips explanations) and cut the glosses, jump to the tricky step, and shift from "explain" to "predict and critique". Because the learner's level is estimated from a chat, probe with a short prediction question first rather than assuming.
- Most worked-example evidence is from well-structured domains (algebra, physics, programming exercises) with school or undergraduate samples. Whether it carries to explaining an existing architecture is an extrapolation.

### Gaps
- Unverified: Paas (1992) and van Merriënboer & de Croock completion-problem studies; Kalyuga & Sweller (2004) rapid-assessment method of adapting to expertise. Not retrieved.
- Not found: a meta-analysis of the worked-example effect itself with an effect size I could verify.
- Not verified: Renkl's "principle-based explanation" and self-explanation prompt findings within examples.

## 3. Self-explanation (Chi; Renkl): prompts, failure modes, eliciting

### Takeaway
Prompted self-explanation helps learning on average, but most evidence is from undergraduates. Chi's work shows good learners generate many explanations and monitor understanding accurately, while poor learners produce few and re-read. Learners often will not do it unprompted, so it must be elicited.

### Cited Findings
- Chi, Bassok, Lewis, Reimann & Glaser (1989), "Self-explanations: How students study and use examples in learning to solve problems", Cognitive Science 13(2), 145-182. Talk-aloud study of mechanics examples. "Good" students (about 82% on problems) generated many explanations that refined the conditions of actions and tied them to principles, with accurate monitoring. "Poor" students (about 46%) explained little and, when solving, re-read examples from the first line looking for solutions to copy — [summary](https://serc.carleton.edu/resources/19512.html)
- Bisra et al. (2018), "Inducing Self-Explanation: a Meta-Analysis", Educational Psychology Review 30, 703-725. It pooled 64 studies (about 6,000 participants) and found prompted self-explanation beneficial, including compared with instructor explanation. The large majority of studies used undergraduates. The authors suggest researching computer-generated prompts — [BPS digest](https://www.bps.org.uk/research-digest/self-explanation-powerful-learning-technique-according-meta-analysis-64-studies)
- Dunlosky et al. (2013), Psychological Science in the Public Interest 14, 4-58, rated both self-explanation and elaborative interrogation "moderate utility": benefits generalize across some conditions, but evidence in educational contexts was too limited for a high rating. It defines self-explanation as explaining how new information relates to known information, or the steps taken in problem solving — [summary](https://stafforini.com/works/dunlosky-2013-improving-students-learning/)

### Inferences
- Failure modes (from Chi 1989): too few explanations, poor monitoring of one's own gaps, and surface re-reading. In a chat, they show up as "makes sense" replies with no content. Elicit with specific prompts, not "does that make sense?": "Why does this line need the issuer check?" "Which earlier step made this one possible?" "What would break if we deleted it?"
- Kind of prompt: concrete, tied to a given code line and its rule, beat generic "explain this". The Bisra moderator results on prompt type were not retrieved, so this is an inference.
- Give the learner a model first (a worked self-explanation by you), then ask for theirs.

### Gaps
- Unverified: Chi et al. (1994) "Eliciting self-explanations improves understanding" (Cognitive Science 18) and Renkl's work on self-explanation prompts and instructional explanations. Not retrieved.
- Not verified: Bisra's moderator findings (prompt type, domain, age).
- Not found: evidence on self-explanation in code reading or auth domains specifically.

## 4. Elaborative interrogation, concept maps, analogies

### Takeaway
"Why" questions about stated facts earn a moderate utility rating, with limited classroom evidence. For analogies and concept maps I found no verified sources this session.

### Cited Findings
- Dunlosky et al. (2013) define elaborative interrogation as generating an explanation for why an explicitly stated fact or concept is true, and rate it moderate utility with limited evidence in educational contexts — [summary](https://stafforini.com/works/dunlosky-2013-improving-students-learning/)

### Inferences
- Elaborative interrogation fits atomic rules ("the token says who, the database says what they may do"): ask "why is the role read from the database on every request rather than from the token?" It needs enough prior knowledge to answer, so for a true novice supply a worked reason first, then ask a variation.
- Analogies: a likely failure is that learners carry over features of the source that do not hold (a JWT "like a passport" invites the belief that it is only checked at the border). The usual remedy is to state explicitly where the analogy breaks. I did not verify literature for this.

### Gaps
- Unverified: Gentner structure-mapping work; Glynn's teaching-with-analogies model; reviews of misconceptions from analogies; Nesbit & Adesope (2006) concept-map meta-analysis (Review of Educational Research). None retrieved.

## 5. Learning by teaching, teach-back, protégé effect, Feynman technique

### Takeaway
Meta-analyses find small-to-moderate benefits of preparing to teach and teaching; interactivity seems to matter, and benefits depend on the learner actually generating and organising content. Protégé effect evidence is mostly effort and motivation in children using software agents.

### Cited Findings
- Kobayashi (2019), "Learning by preparing-to-teach and teaching: A meta-analysis", Japanese Psychological Research. Across 28 studies, Hedges g was 0.35 for preparing-to-teach and 0.56 for teaching with preparing. Benefits were larger when teaching was interactive — [search result summary](https://www.frontiersin.org/articles/10.3389/fpsyg.2018.02755) (this is Kobayashi's related Frontiers perspective piece; the meta-analysis numbers come from the search digest)
- Kobayashi (2024), Educational Psychology Review (DOI 10.1007/s10648-024-09871-4): 39 studies, small overall effect g = 0.27 for teaching after studying with teaching expectancy. In 14 studies teaching added g = 0.38 beyond preparing alone — [x-mol record](https://x-mol.com/paper/1763030854519197696)
- A commentary critiques the separate Ribosa & Duran meta-analysis (23 studies) on eligibility and effect estimation — [Frontiers 2023](https://www.frontiersin.org/articles/10.3389/fpsyg.2023.1095285/pdf)
- Chase, Chin, Oppezzo & Schwartz (2009), Journal of Science Education and Technology 18(4), 334-352: students made more effort to learn for a teachable agent than for themselves (protégé effect); the second study used verbal protocols with 5th graders — [record](https://purl.stanford.edu/zm369yx3532)
- Fiorella & Mayer (2013), "The relative benefits of learning by teaching and teaching expectancy", Contemporary Educational Psychology 38(4), 281-288, and Fiorella & Mayer (2014), 39(2), 75-85, exist as references, and Fiorella & Mayer (2015) "Eight Ways to Promote Generative Learning" (Educational Psychology Review) covers teaching among eight strategies. I did not retrieve their findings — [Springer record](https://link.springer.com/doi/10.1007/s10648-015-9348-9)

### Inferences
- Teach-back in chat: ask the learner to explain a step to an imagined newcomer, then respond as that newcomer with a naive question. The interactive form matches the moderator Kobayashi found.
- Limits: a learner who does not yet know the material can only repeat it; do teach-back after worked examples and a self-explanation round, not before. Fluent-sounding explanation can mask gaps, so probe with a "what if" variant.
- Feynman technique: no research evidence retrieved; treat it as a popular label for explain-in-plain-words plus gap-finding.

### Gaps
- Not found: evidence that the protégé effect holds for adult learners or technical content.
- Not verified: Fiorella & Mayer findings (explain-to-others vs. teaching expectancy).

## 6. Mastery learning, ZPD, productive failure

### Takeaway
Mastery learning shows positive effects in a 108-study meta-analysis. Problem-solving-before-instruction has a moderate effect overall (g 0.36) but depends on design and learner age. For true novices in an unfamiliar system, start with a worked example, and reserve struggle for something the learner has a partial basis for.

### Cited Findings
- Kulik, Kulik & Bangert-Drowns (1990), "Effectiveness of mastery learning programs: A meta-analysis", Review of Educational Research 60(2), 265-299, pooled 108 controlled evaluations and found positive effects on exam performance at college, high school and upper elementary level. Secondary sources say gains were larger for weaker students. I did not verify the average effect size (one page listing 0.52 SD looked AI-generated) — [record](https://typeset.io/pdf/effectiveness-of-mastery-learning-programs-a-meta-analysis-45bgwh1byb.pdf)
- Kapur (2008), "Productive failure", Cognition and Instruction 26(3), 379-424: learners struggle with problems first, then get the canonical solution — [secondary description](https://link.springer.com/10.1007/978-3-030-22341-0_23)
- Sinha & Kapur (2021), "When problem solving followed by instruction works: Evidence for productive failure", Review of Educational Research (DOI 10.3102/00346543211019105). 53 studies, 166 comparisons: overall g = 0.36 [0.20, 0.51] favouring problem solving first. Stronger (g 0.37-0.58) when the problem-solving phase followed productive failure design principles. Younger learners (grades 2-5) and domain-general skills favoured instruction first. Press coverage conflates this with a separate ETH Zurich course test — [X-MOL record](https://www.x-mol.com/paper/1406031499744456704); [press summary](https://phys.org/news/2021-09-productively-wiser.html)
- Loibl, Roll & Rummel (2017), Educational Psychology Review 29(4), 693-715: effect depends on design features, with proposed mechanisms being activation of prior knowledge, awareness of knowledge gaps, and recognition of deep features. A 2020 Loibl study in Instructional Science found problem solving first helped conceptual understanding while instruction first helped procedural fluency — [record](https://cris.iucc.ac.il/en/publications/towards-a-theory-of-when-and-how-problem-solving-followed-by-inst/)

### Inferences
- Use productive failure sparingly and for concepts: ask "before I show it, how would you stop a deactivated user from using an old token?" and let them propose, then show the real design and compare. Do not use it for procedure or syntax, or on a learner who has no relevant prior knowledge.
- Mastery gating: do not move to the next step until the learner can predict or explain the current one; if not, re-teach with a different example, not the same words.
- ZPD: no source retrieved this session (see Gaps); use it only as the idea of keeping tasks just beyond what the learner can do alone.

### Gaps
- Unverified: Vygotsky (1978) ZPD; Bloom (1984) 2-sigma paper; Hattie meta-analyses (the user asked for caution; not retrieved).
- Not found: productive-failure studies in programming or security domains.

## 7. Segmenting, signalling, pacing: how long before a check

### Takeaway
Segmenting reduces load and improves retention and transfer modestly; I found no verified rule for the exact unit length. A check after each coherent step is the best-supported inference.

### Cited Findings
- Rey et al. (2019) found segmenting improved retention and transfer in small-to-medium measure, reduced cognitive load, and increased learning time; learner pacing and system pacing both worked — [MPI record](https://is.mpg.de/publications/rey2018segmenting)
- A secondary French source reports d = 0.42 (retention) and d = 0.37 (transfer); unconfirmed against the original — [Substack summary](https://partempsclair.substack.com/p/le-principe-de-segmentation-en-enseignement)
- Dunlosky et al. (2013) rate practice testing as the recommended alternative to low-utility rereading/highlighting — [summary](https://stafforini.com/works/dunlosky-2013-improving-students-learning/)

### Inferences
- Unit = one step of the sequence diagram (one hop, one concept), checked by one prediction or "why" question before moving on. Signalling: bold the new term once and mark the one line that matters in a block.
- Pacing: let the learner choose when to continue; offer "next" or "go deeper", as learner-paced segmentation was effective.
- Because testing a learner who has just read is easy, add a delayed check: re-ask a step from three steps earlier.

### Gaps
- Unverified: signalling principle meta-analysis (Schneider et al. 2018, Educational Research Review) and redundancy meta-analyses.
- Not found: any source that states a specific length (minutes, words or lines) for a segment.
- Not verified: Miller (1956) and Cowan (2001) working-memory capacity figures, which are often misquoted as "7 items".

## Cross-cutting caveats for the report writer
- Most of this evidence comes from lab or classroom studies with undergraduates or school pupils in well-structured domains (algebra, physics, science). The extrapolation to adults learning an architecture through a chat is an inference.
- Two meta-analysis citations were corrected from the query: Tetzlaff et al. is in Learning and Instruction (not J. Educ. Psychol.), and Rey et al. is in Educational Psychology Review (not Educational Research Review).
- Effect sizes quoted from search snippets or secondary summaries should be checked against the originals before publication.
