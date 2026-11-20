# Program comprehension and the pedagogy of code reading (for a guided walkthrough of a layered codebase)

Method note: built from about 15 web searches (snippets only; I did not open full papers). Claims below carry the URL that supported them. Items I know from background reading but could not confirm this session are in Gaps, marked UNVERIFIED. Many teaching studies are on novices in introductory university courses; this is flagged where it applies.

## 1. Comprehension theory: top-down vs bottom-up, beacons, plans, mental models, notional machines, experts vs novices

### Takeaway
Classic theory says experts read top-down (hypothesis then check, using plans and beacons) when the domain is familiar and bottom-up (chunking) when it is not; professionals on large systems switch opportunistically (integrated model). Notional machines are an explicit learning goal in Sorva's survey. fMRI evidence is small-sample and should not drive design.

### Cited Findings
- Soloway and Ehrlich: expert programmers rely on reusable plan fragments and rules of programming discourse; two empirical studies tested this. Brooks (1983) is the origin of the top-down model (hypotheses generated, tested, refined). Both are described in a review — [arXiv 2310.11301](https://arxiv.org/pdf/2310.11301); [Soloway and Ehrlich listing](https://www.oreilly.com/library/view/readings-in-artificial/9780934613125/xhtml/B9780934613125500422.xhtml). Secondary sources, not the originals.
- Brooks' theory starts from a vague hypothesis, often from the program name, refined as code is examined; Letovsky described programmers as "opportunistic processors" who switch strategies on cues — [Saarland course reading](https://www.st.cs.uni-saarland.de/edu/empirical-se/2006/PDFs/brien03.pdf).
- Letovsky's hypothesis types: "why" (purpose), "how" (method), "what" (content). Von Mayrhauser and Vans' integrated model combines top-down and bottom-up with four components: program model, situation model, domain model, knowledge base — [Colorado State paper](https://www.cs.colostate.edu/~somlo/pubs/ijhcs99.pdf). Their studies were on professionals doing corrective maintenance on large systems — [Vans dissertation](https://mountainscholar.org/bitstream/10217/183411/1/ETDF_1996_Vans_AMarie_DIP.pdf).
- Beacons are semantic cues (method signatures, idioms, identifier names) that hint at purpose; an fMRI study (11 participants) manipulating beacons and layout found semantic chunking in bottom-up comprehension and lower activation when beacons were present, which supports beacons easing comprehension — [Siegmund et al. 2017, Saarland](https://www.se.cs.uni-saarland.de/publications/docs/SPP+17.pdf); [project summary](https://www.se.cs.uni-saarland.de/projects/BrainsOnCode/).
- Sorva (2013), "Notional Machines and Introductory Programming Education", ACM TOCE 13, 8:1-8:31: extends du Boulay's notional machine; students may hold several, possibly contradictory, mental models; the survey concludes notional machines should be an explicit learning goal — via [secondary summary and Dagstuhl 19281](https://drops.dagstuhl.de/opus/volltexte/2019/11627). I did not read the paper itself.
- Lister et al. (2004) and Whalley et al. (2006) SOLO work: students mostly give multistructural answers (line-by-line, "trees") where educators give relational ones (purpose, "forest"); rewording the question did not remove this; reading performance correlates with writing performance — [Whalley et al. 2006 (UTS)](https://opus.lib.uts.edu.au/bitstream/10453/12626/1/2008001537.pdf); [SOLO summary](https://research.aston.ac.uk/en/publications/not-seeing-the-forest-for-the-trees-novice-programmers-and-the-so/). Novice, intro-course population.

### Inferences
- A walkthrough of an unfamiliar layered codebase is the "unfamiliar domain" case, so learners need both a top-down anchor (what is this use case for, one-sentence hypothesis) and bottom-up reading; stating a "why/how/what" per step maps onto Letovsky.
- Naming and signatures (port names, test names) work as beacons; the walkthrough should point at them explicitly.
- The hexagon itself is a notional machine: teach "a request enters via an adapter, calls a use case, which calls ports, implemented by adapters" as the model, then test it with prediction questions.
- Expect learners to narrate multistructurally; prompt for the relational summary ("what is this step for?").

### Gaps
- UNVERIFIED (background knowledge): the expert-vs-novice contrast that experts chunk by plans and recall meaningful code better than scrambled code (Shneiderman; Soloway and Ehrlich), and Crosby/Scholtz/Wiedenbeck on beacons. My search for Crosby et al. returned nothing.
- Siegmund's 2014 fMRI study details (participant count) not confirmed; the 11-participant figure is from the 2017 work as summarised. Treat fMRI as weak, small-sample, student participants.
- Hermans' "The Programmer's Brain" (secondary, popular): search returned nothing; not cited.
- No evidence found specific to professional engineers reading layered/hexagonal architectures.

## 2. Teaching approaches with evidence: PRIMM, tracing, EiPE, Parsons, reading before writing

### Takeaway
PRIMM is a reading-first scaffold (worked example fading) with encouraging but mostly teacher-reported evidence, school age. Lister's tracing work and the EiPE/SOLO line show reading and tracing precede writing in novices. Parsons problems cut time; learning gains are mixed.

### Cited Findings
- PRIMM = Predict, Run, Investigate, Modify, Make (Sentance and colleagues); starts from reading working code; Investigate = trace, annotate, explain; one framing ties it to worked-example fading — [Raspberry Pi Foundation](https://www.raspberrypi.org/blog/primm-talk-in-programming-lessons-research-seminar/); the fading framing comes from a general FAQ site, so weak — [FAQ](https://faq.computersciencewiki.org/index.php/intro/article/primm).
- PRIMM evaluation: 13 schools, 493 students aged 11-14 with a control group, mixed methods (Sentance, Waite, Kallia); teachers reported it helped mixed-ability classes. I did not find reported attainment effects; randomisation not confirmed — [Computer Science Education, doi 10.1080/08993408.2019.1608781](https://informahealthcare.com/doi/epub/10.1080/08993408.2019.1608781). Pilot (WiPSCE 2017): 47% of teachers found it very helpful, 80% planned to use it — same search result set. School children, not professionals.
- Lister et al. (2004), "A multi-national study of reading and tracing skills in novice programmers", SIGCSE Bulletin 36(4), 119-150 (ITiCSE working group, over 500 students, seven countries): many students performed much worse than expected on predicting code output; authors treat reading/tracing as precursors to problem solving — [Hamer's copy](https://www.cs.auckland.ac.nz/~j-hamer/ITiCSE04-wg.pdf); [dblp](https://dblp.dagstuhl.de/rec/journals/sigcse/ListerAFFHLMMSSST04.html). DOI differs between listings; verify before citing. Intro-course novices.
- EiPE: Whalley et al. 2006 "An Australasian study of reading and comprehension skills in novice programmers, using the Bloom and SOLO taxonomies" (ACE 2006) — [CRPIT abstract](https://crpit.scem.westernsydney.edu.au/abstracts/CRPITV52Whalley.html); SOLO findings above.
- Parsons problems: scaffolding studies show efficiency gains (less time on write-code tasks) with no significant learning gain in one study (Hou, Ericson, Wang, Koli Calling 2023); students can solve standard Parsons by syntactic heuristics without full understanding — [NSF PAR listing](https://par.nsf.gov/servlets/purl/10510497); [Faded Parsons](https://escholarship.org/content/qt8794g5s0/qt8794g5s0.pdf?t=qbddoc). Ericson, Margulieux, Rick (2017) "Solving Parsons problems versus fixing and writing code" exists but I could not read its findings.
- Fitzgerald et al. (2008), Computer Science Education 18(2), 93-116: good novice debuggers were mostly good programmers, but not all good programmers debugged well — [Aberystwyth record](https://research.aber.ac.uk/en/publications/debugging-finding-fixing-and-flailing-a-multi-institutional-study/).
- Worked examples reduce extraneous cognitive load and beat unaided problem solving early on (cognitive load theory review in computing education) — [review](https://typeset.io/pdf/cognitive-load-theory-in-computing-education-research-a-114j3eiz.pdf); Morrison and Margulieux subgoal-labelled worked examples — same search; results not seen.

### Inferences
- Walkthrough step pattern (PRIMM-lite): before showing a layer, ask "predict what this adapter returns / which port it calls", then reveal and compare; then ask for a relational one-line summary (EiPE) and compare with a model answer.
- A Parsons-style task fits: give the six steps of the request (browser, proxy, route, use case, port, adapter) shuffled and ask the learner to order them, then check against the sequence diagram. Expect it to save time, not necessarily deepen learning, so pair with a "why" question.
- Fade scaffolding: first use case fully narrated, second use case with learner predictions, third learner leads.

### Gaps
- No peer-reviewed study of PRIMM with adult or professional learners found; attainment effect sizes not found.
- UNVERIFIED: McCauley et al. 2008 "Debugging: A review of the literature from an educational perspective" (not searched directly); Lopez et al. 2008 relationship between tracing and code-explaining skills; Venables, Tan, Lister 2009 (hierarchy of skills). I know of them but did not confirm them.
- The brief's phrase "Lister tracing ability" thresholds (e.g., tracing predicts writing) is supported only at the level of the Lister 2004 abstract-level claims above.

## 3. Software engineering onboarding research

### Takeaway
Evidence says newcomers' barriers are documentation, finding a starting point, social contact and code complexity; mentor support in critical stages speeds onboarding; evidence for code tours is thin, with one 2026 preprint-style study.

### Cited Findings
- Steinmacher, Silva, Gerosa (2014), "Barriers Faced by Newcomers to Open Source Projects: A Systematic Review" (IFIP chapter): 21 studies; five categories: social interactions, finding a way to start, documentation problems, code issues, newcomers' knowledge — [Springer chapter](https://link.springer.com/content/pdf/10.1007/978-3-642-55128-4_21.pdf); [NAU record](https://experts.nau.edu/en/publications/barriers-faced-by-newcomers-to-open-source-projects-a-systematic-/).
- Steinmacher's later work: interviews with 35 developers from 13 projects, a questionnaire, student feedback, producing a model of 58 barriers in six categories — [UCI ISR listing](https://isr.uci.edu/node/2204.html); [CSCW 2015 social barriers](https://www.ime.usp.br/~gerosa/papers/CSCW_2015.pdf). OSS context, not employed hires.
- Ju, Sajnani, Kelly, Herzig (ICSE 2021), "A Case Study of Onboarding in Software Teams: Tasks and Strategies": interviews with 32 developers and 15 managers, survey of 189 developers and 37 managers (Microsoft); onboarding correlates with productivity and satisfaction; confidence, motivation and stress matter as indicators — [arXiv 2103.05055](https://arxiv.org/abs/2103.05055v1). Not a time-to-productivity measurement.
- Fagerholm et al.: multiple-case OSS study; mentor support in critical stages can accelerate onboarding, project maturity matters — summarised in the search results via [DX newsletter](https://newsletter.getdx.com/p/onboarding) (secondary; exact paper not confirmed).
- Code tours: Lacy (arXiv 2603.25391, FSE 2026 industry track), 30K-line legacy finance codebase at Beko: learners with expert-guided tours scored 83% on quizzes vs 57% for AI-only tours, preferred tours over self-study; authors' own study — [arXiv](https://arxiv.org/abs/2603.25391). CodeTour (VS Code) had a PPIG 2022 paper (Taylor), findings not retrieved — [PPIG](https://www.ppig.org/papers/2022-ppig-33rd-taylor/). Also Balfroid 2024 on tours (unread) — [UNamur](https://researchportal.unamur.be/files/93244689/balfroid-2024.pdf).

### Inferences
- A walkthrough substitutes for expert mentoring on the barrier "finding a way to start": begin with the single entry point and the map of layers.
- Include a quick quiz per step (as in Lacy) as retrieval practice and as a check of understanding.
- Make explicit what the learner can ask and where to find docs, to address the social/documentation barriers.

### Gaps
- No solid time-to-productivity figures found (commonly cited "N months" numbers are practitioner claims, not cited).
- UNVERIFIED: Storey et al. work on newcomer/awareness; Dagenais et al. 2010 "Moving into a new software project landscape" (ICSE); Begel and Simon on novice developers at Microsoft. Not searched, not confirmed.
- No controlled study of pair programming for onboarding found in this session.

## 4. Tests as documentation, mutation / "break it and see", predicting test outcomes

### Takeaway
Tests are widely described as living documentation and developers use them to build mental models, but controlled evidence that reading tests improves comprehension is thin; the best support is for readable assertions and well-named tests.

### Cited Findings
- Leotta et al.: controlled experiment with 51 students; fluent assertions significantly reduced time to understand assertions vs basic JUnit — [QUATIC 2018](https://sepl.dibris.unige.it/publications/2018-leotta-QUATIC.pdf). Student participants.
- Aniche, Treude, Zaidman, "How Developers Engineer Test Cases: An Observational Study": developers used documentation to build an initial mental model of the program under test — [arXiv 2103.01783](https://arxiv.org/pdf/2103.01783).
- Moonen, van Deursen, Zaidman, Bruntink: in XP tests explicitly serve as documentation and communication between developers — via the search results, secondary summary; see [TU Delft work on test comprehension](https://repository.tudelft.nl/record/uuid:3d251634-5499-4423-ab66-d9803a6ae877).
- Only about 3.56% of unit tests had preceding comments and 14.02% inner comments (Daka and colleagues' UnitTestScribe) — [Academia copy](https://www.academia.edu/96056192/Automatically_Documenting_Unit_Test_Cases); so test names carry the documentation burden.
- Madeja and Porubán: 49% of Android unit test names contain the full unit-under-test method name, 76% partial — same search results; paper not opened.

### Inferences
- In the walkthrough, read the test before the implementation for each step; ask the learner to predict what the test asserts from its title (a beacon), then compare.
- "Break it and see": remove an authorisation check or change a status code and have the learner predict which test fails and why; ties tests to architecture tests (a boundary violation should fail the architecture test).
- Mutation as a learning exercise is my proposal, not evidence-backed.

### Gaps
- No empirical study found on mutation testing or "break it" exercises as a comprehension teaching method.
- No study found on predicting test outcomes as a learning activity (it is a variant of Predict in PRIMM and tracing, so indirectly supported).
- Yu (TU Delft) test comprehension findings not read.

## 5. Diagrams and visualisation: when do they help, and limits

### Takeaway
Aggregated controlled experiments suggest UML class and sequence diagrams give a modest comprehension benefit for source code, but benefit depends on experience and familiarity with the notation; diagrams drift from code, which I could not support with a source.

### Cited Findings
- Scanniello, Gravino et al., aggregating 12 controlled experiments (Empirical Software Engineering 2018), "Do Software Models Based on the UML Aid in Source-Code Comprehensibility?": earlier work reported an average improvement of about 12% with UML class and sequence diagrams — [EMSE 2018 PDF](https://www.iris.unisa.it/retrieve/e2915b35-290e-8981-e053-6605fe0a83a3/EMSE_2018_gravino_risi.pdf). Mostly students.
- Torchiano, Scanniello et al., family of four experiments (124 participants), J. Visual Languages and Computing 41 (2017) 10-21: object diagrams did not reliably improve design comprehension; benefit depended on experience and UML familiarity; no substantial change in time — [Polito record](https://iris.polito.it/handle/11583/2645071).
- Layout: multi-cluster layouts improved comprehension accuracy in UML class diagrams (Sharif et al., cited secondhand) — [Polito VLC paper](https://iris.polito.it/retrieve/handle/11583/2645071/159446/VLC_final.pdf).

### Inferences
- A sequence diagram per use case is a reasonable top-down map, but learners unfamiliar with the notation gain less, so spend one minute on how to read it, and walk the diagram step by step with the code.
- Keep the diagram next to the code and have the learner find each arrow in the code; mismatches become a teachable check on drift.

### Gaps
- No empirical source on diagram drift (outdated diagrams) found; I only know it from practice. Marked UNVERIFIED.
- No study on Mermaid vs other renderings or on architecture (hexagon) diagrams specifically.

## 6. Applying each to a guided walkthrough (one request through the layers)

### Takeaway
A step per sequence-diagram arrow, with predict, reveal, summarise, and a short quiz, covers the strongest evidence (worked examples with fading, tracing, EiPE, retrieval).

### Cited Findings
- (Drawn from sections above; no new sources.)

### Inferences
1. Theory: open with the use case's one-sentence purpose, then ask for a hypothesis of the layers touched (Brooks/Letovsky). Highlight beacons (names).
2. PRIMM: Predict the response/status of a request, Run it (curl or test), Investigate the code, Modify (tighten a rule, watch the test fail), Make (add a small variant).
3. Tracing and EiPE: ask for one-line purposes of each function; compare to a model answer; coach from line-by-line to purpose.
4. Parsons: shuffle the request path or the TDD steps.
5. Onboarding: give a map, an entry point, and a place to ask; short quiz at the end of each layer.
6. Tests: read the test first; predict failures when a boundary is broken.
7. Diagrams: one sequence diagram, walked arrow by arrow, flag any arrow without code.

### Gaps
- None of these combinations has been tested with professional engineers in the literature I found; the design is an inference, so evaluate with a quiz and learner feedback.
