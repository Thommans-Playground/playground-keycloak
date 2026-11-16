# Question bank for vbench-at

Ask only what the criterion in front of you needs. At most four questions a call, with a recommended first
option when there is one. Skip a question the repo already answers.

## 1. Which tool runs the acceptance tests?

The project's default stack is Next.js, React, TypeScript and Tailwind for the frontend, and Python, FastAPI and
Postgres for the backend (decision 22). Look at what is installed, say what you found, and confirm the default
instead of asking from nothing.

- **pytest against the FastAPI API** (Recommended, the default): the backend is Python, so one language for the
  rules, the integration tests and the acceptance tests. The test calls the API over HTTP (for example with
  `httpx`), never a function inside the code.
- **Playwright Test**: for the few browser journeys on top of the API tests, not for every criterion. Already
  installed from the Storybook work. Its `request` fixture can also call an API without a browser.
- **Vitest**: the frontend unit tests (components, hooks). Not an acceptance tool here.
- **Something else**: say what, and record why.

Whichever runs it, an acceptance test goes through the API and not through a screen.

## 2. How does a test reach the API?

- Does the test start the app **in process** (fast, for example `httpx` with FastAPI's ASGI transport) or call
  one that is **already running** at an address (closer to production)?
- Where does the **Postgres** test database come from: a container started for the run, one shared test
  database, or a fresh schema for each test? How is it emptied between tests?
- How does a test sign in as each role (administrator, auditor, project manager, engineer)? Keycloak is the
  identity provider (decision 23). Either a **Keycloak test container** with an imported realm that has one person
  for each role (closest to production, slower), or **tokens signed with a test key** that the API accepts only in
  tests (fast, but the real token check is not exercised).
- How is the Given state made: through the API itself (preferred, because it proves the front door), or by
  seeding the database directly? Say which parts of the Given have no API yet.
- Where does the test folder live: `tests/acceptance` at the repo root, or inside the backend folder?

If the API does not exist yet, record that the test waits for the first slice of the use case. Do not invent
the API.

## 3. One criterion, one test

- Does the Given need more than one thing set up? List them in the order the test does them.
- Is there exactly one When? A second action is a second criterion.
- Is the Then something a person can see through the API? If it is a change in the database that the API never
  shows, the criterion belongs at integration level.

## 4. What to check

Only what the criterion says, and only what can be observed.

- A status or a result the API returns.
- A state the API shows afterwards (for example, the account is active).
- A refusal: which refusal, and does it leave the state as it was ("stays pending")?
- An audit entry or a notification, only if the criterion names it.

Do not add a check for something nobody asked for. If a check feels needed that the criterion does not state,
that is a missing criterion: hand it to vbench-req.

## 5. Is the criterion testable as written?

Send it back to vbench-req, with the reason, if any answer is yes:

- It is vague ("works", "is fast", "looks right") with no result to observe.
- The Then holds two outcomes joined by "and" that could pass or fail apart.
- It names a screen, a button or a colour instead of a result. That is a use case step or a manual check.
- It is really a rule that holds with no database (unit level) or an adapter against a real system
  (integration level), but it is marked acceptance.
- Its Given cannot be set up by anything in the product.
- A number or a limit is missing ("quickly", "many").

## 6. Review and stamp

- Does the test run exactly the Given, When and Then of the criterion, in the project's words?
- Is the tag right, and does the test fail for the right reason before the code exists?
- Run `stamp AC-ID` only after a person says yes.

## 7. Close

Show what changed: the files written, what `report` says now, and which criteria still have no test. Ask:
commit as a `test(...)` commit (vbench-commit), keep going, or stop.
