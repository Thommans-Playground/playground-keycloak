# Interview technique

Used by `/vbench:discovery` to agree scope, and by `/vbench:v-2-design` to settle a contested design choice.
The aim is a shared understanding the user can sign off, not a list of questions answered.

## Rules
- **One question at a time.** Wait for the answer before asking the next. A list of questions is bewildering.
- **Bring a recommendation.** Every question comes with your suggested answer and the reason, so the user can say
  "yes" quickly or push back. Never ask an open question when you can propose an answer.
- **Look before you ask.** If the code, the specs or the docs can answer it, read them instead of asking.
- **Walk the decision tree in order.** Resolve a decision before the ones that depend on it. When an answer changes an
  earlier one, say so and revisit.
- **Use the project's words.** Take vocabulary from the requirements doc; flag a term that is ambiguous or means two
  things, and record the agreed meaning.
- **Say what you do not know.** An open question goes in the brief as open. Do not close it with a guess.
- **Stop when it is enough.** End when the open questions are closed or the user says so.

## Discovery: the order that usually works
1. **Problem.** What is wrong or missing today, and for whom? No solution yet.
2. **Actors.** Who does this, and what are they trying to achieve? Who else is affected?
3. **Scope.** What is in? What is deliberately out, so nobody assumes it?
4. **Vocabulary.** The few nouns the product is made of. Are two words used for one thing?
5. **Constraints and assumptions.** Time, platform, data, people, anything taken as true.
6. **Risks and the unknowns.** What could make this wrong? What can only be learnt by trying?

## A contested design choice
1. State the decision and the forces pulling on it (what must be true, what is expensive to change).
2. Offer two or three options, each with what it makes easy and what it makes hard.
3. Recommend one, with the reason in a sentence.
4. Record the outcome under **Design decisions** in the spec, as `D<n>: choice, because force`. A choice that is
   expensive to reverse also gets a decision record.

## Closing summary (a few lines)
What was decided. What is out of scope. What stays open. What happens next.
