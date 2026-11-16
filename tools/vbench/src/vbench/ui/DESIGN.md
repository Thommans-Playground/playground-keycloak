# Design language for the dashboard

The dashboard uses the **AGIL Secure Shield palette and components** (tokens, chips, voice and accessibility), laid out
by **Apple's Human Interface Guidelines** (type, hierarchy, appearance, controls, navigation). This page records what was
adopted, how it maps onto Tailwind v4 and shadcn, and what was left out on purpose. The tokens live in `src/index.css`.

## Apple Human Interface Guidelines, as applied

**Clarity, deference, depth.** Content comes first and the chrome stays quiet: the data is the interface. Hierarchy comes
from size, weight and space, not from colour or boxes; a surface rises only when it is on top of something.

**Type.** The platform's own face (`-apple-system`, San Francisco on Apple devices, the system font elsewhere; monospace
only for ids, commands and counts). Named text styles in `src/index.css`, after Dynamic Type: `t-large-title` (34px, the
page title), `t-title` (22px, a section), `t-headline` (17px), `t-body` (15px), `t-subhead` (14px), `t-footnote` (13px),
`t-caption` (12px), `t-overline`. Use a style, not a one-off size.

**Appearance.** Light is the default, whatever the device prefers. Dark is a choice in **Settings**, reached from the
profile menu at the end of the top bar (Light, Dark or System, which follows the device). The choice is kept in this
browser (`lib/prefs.ts`, guarded, with an in-memory fallback when storage is blocked) and applied as `data-theme` on the
html element: by a script in `index.html` before the first paint, so there is no flash, and by `lib/theme.ts` after. The
dark tokens are one block in `src/index.css`; the same roles are re-lit, so nothing is hard-coded to a colour. Use the
tokens, never a hex, so both appearances stay right. Status keeps its word in both. Diagram images are drawn for a light
page, so they sit on a white backing in either appearance.

**Controls and navigation.** A choice between views of the same content is a **segmented control** (`Segmented`), one
always chosen, arrow keys to move. Top bars are translucent (`bg-surface/85 backdrop-blur`) so content scrolls under them.
Targets are at least 44px, the focus ring is always visible, motion respects `prefers-reduced-motion`.

**Breadcrumbs** (after the dim-a prototype). A page's breadcrumb is pinned under the top bar. For anything on the trace it
is the **lineage**, the last four layers from the problem down to the test: problem > request > requirement > use case >
criterion > test (a task, code file or diagram sits under its use case), so a requirement reads `STK-PRB-001 > STK-REQ-001
> REQ-FR-001` and a test reads `REQ-FR-001 > UC-N-001 > AC-N-002 > TST-UNT-002` (`lib/lineage.ts`). The trace is a graph,
so each crumb shows the first parent, and its menu lists the others the layer below could have come from; the last crumb's
menu lists the others under the same parent. Anything off the trace (a context, a domain model, a problem with nothing
above it) keeps the plain trail, V-cycle > phase > item. The sidebar already shows the phase.

The general rules for any breadcrumb follow. The last crumb is the page
and, where there are siblings, carries a **menu** to go to another of the same kind (another use case, phase or item,
each with a line saying what it is) and ends with a way to the whole list. `PageHeader` takes `crumbs` with an optional
`switch`; the menus are built in `src/lib/crumbs.ts`.

**Records** (after dim-a's run and checklist pages). Anything you click opens a **record**, either a page or, in
List and detail, a pane beside the list. A record is a header card (kind and id, the title, what it is, a status chip,
and a strip of facts) followed by sections, each a short heading and a grouped table of the related things: where it
came from, what it says, the use cases, the criteria, the tests, where it lives, the picture in context. On a wide
window a rail of the sections sits beside the content and follows the reader (`Scrollspy`: the active section is the
last whose top has crossed a line under the pinned bars, a jump holds its choice, and at the foot of the page the last
section in view counts); on a narrower one the same sections are a row of chips. Sections keep `scroll-mt-32` so a jump
lands under the pinned bars. `RecordFrame`, `RecordHeader`, `RecordSection` and `RelatedTable` (`components/Record.tsx`)
build every record; `components/records/` has the requirement record (problem, request, requirement, with the trace
from problem to test) and the record for everything else; the use case page is a record too. In a pane the sections stack
without the rail, with an "Open as a page" link. A new page starts at the top; a `#section` link scrolls to its section.

**Changes** (only when the server was started with `--write`). Anything on the requirements side can be added, edited
or deleted from a sheet (`ChangeSheet`) that slides in from the right: **write it**, **check it**, **done**. Checking is
the point: the exact diff of the files, the problems found (errors stop Apply, warnings do not), and the blast radius in
two columns, up the trace toward the problem and down it toward the tests, each affected thing with a word for what
happens to it (link removed for you, left with nothing above it, read again, may be affected). Only Apply writes and only
Commit commits, so a person decides each step. Add from where you are: a problem's page offers "Add request for this
problem" with the link filled in.

**Actions live in a three-dots menu.** A row, or a record's header, has one quiet `…` (`ActionsMenu`, the shadcn dropdown-menu in
its Base UI variant: `components/ui/dropdown-menu.tsx`) instead of buttons scattered through the cells, so the table stays
a table. The menu has an *Add* group, whose items depend on the kind and already carry the link back, and a *Change* group
with *Edit* and *Delete* (destructive, in the risk colour). What each kind offers is data in `lib/actions.ts`, so every row of
a kind offers the same and a test can say what. An action that cannot be done yet is shown disabled with its reason (a
criterion needs a use case) rather than hidden. The trigger names its row for assistive technology, Escape returns focus to it,
and nothing is drawn unless the server was started with `--write`. The one *Add …* button in each section's header stays: it
is the section's primary action and sits outside the table.

**Does this already exist?** The add form carries the question (`OverlapCheck`): a button (*Check*, or *Ask Claude* when the
server has an agent, with a line saying what is sent to Anthropic), then a verdict chip (looks new, already exists, partly
written, a narrower version), a plain sentence, the advice, and each close entry with its id, its own words, why it
matters, and *Open it* / *Edit it instead* (same kind only). Asking is always a deliberate press, never silent. The
answer goes dim when the wording changes. The same add buttons sit on the rows (a problem's *Add request*, a request's
*Functional* and *Quality*) with the link already filled in, so an entry is written where it belongs.

**A name is never alone.** Whatever a person sees by its name (a code file, a test, a diagram, a context, a criterion) is
shown with an explanation: `VItem.description` (a module's first docstring line, a test's humanised name, a diagram's
title), a criterion's Given/When/Then text, a requirement's story or scenario. A row is the id, the name and what it is.

**Tabular first, pictures second.** Pages open on a table or a sheet of linked rows; a diagram sits behind a **Show** control
in context (`Visualise`). Requirements open as a **sheet** (`RequirementsSheet`): the problem, the requests, then each
functional requirement with its story, the use cases that realise it, its criteria and the tests that prove them in one
row, then each quality requirement as its six-part scenario. Table and List-and-detail are the other views.

## What was adopted

**Surface.** Calm, dense, data-first, light by default with a dark option. A 4px accent bar tops every page. Navigation is a 240px left sidebar that collapses to 64px (and starts
collapsed under 1024px), a 64px top bar, a content column of at most 1360px, breadcrumbs on every drill-down page that
reuse the sidebar's names.

**Principles, in order.** People decide, the tool recommends (the dashboard is read-only and only offers a command to
copy). Clarity over decoration. Hierarchy through restraint. Depth means something. Details on demand. One family, one
feel. Transparency is built in. Everything is accountable.

**Tokens.**

| Secure Shield token | CSS variable | shadcn / Tailwind name | Job here |
|---|---|---|---|
| page `#F5F6F7` | `--page` | `background` | page background |
| surface `#FFFFFF` | `--surface` | `card`, `popover` | cards and panels |
| ink `#1F2328` | `--ink` | `foreground` | text and headings |
| muted `#5A6170` | `--muted` | `muted-foreground` | secondary text |
| charcoal `#23272F` | `--charcoal` | `primary` | the one primary action per area |
| hover `#F1F2F4` | `--hover` | `accent`, `muted` | hover and active backgrounds |
| border `#E3E5E8` | `--border` | `border` | card borders |
| border-input `#D4D7DC` | `--border-input` | `input` | inputs and secondary buttons |
| risk `#B4400C` (bg, text) | `--risk*` | `destructive`, `risk*` | failing gates, no verifying test |
| warning, success | `--warn-*`, `--ok-*` | `warn-*`, `ok-*` | in progress, waiting, built, passing |
| brand `#E1251B` | `--brand` | `brand` | the accent bar and the active nav marker only, never a fill |
| ai, note | `--ai*`, `--note*` | `note-*` | reserved, currently unused (see below) |

Radii: 12px cards, panels and popovers; 8px buttons, inputs and nav items; 6px small inner bits; pills for chips.
Elevation: four cool blue-grey levels (`shadow-e1` to `shadow-e4`); only interactive cards lift on hover. Type: the system font stack
(San Francisco on Apple devices, so nothing is downloaded and it works offline), a monospace stack for ids, commands and
counts; the scale is the named text styles above.

**Components.** Buttons are charcoal (primary), white with an input border (secondary) or risk orange (containment),
44px tall. Chips pair colour with a word and use only four tones: neutral, ok, warn, risk. Tables use a quiet header row
and hairline dividers. Loading is a skeleton, never a spinner over content. Every empty and error state says what
happened and what to do.

**Voice and accessibility.** British spelling, sentence case, no em dashes, plain sentences, every number with its
context ("2 of 3 covered", not "2"). Targets of 44px, a visible 2px ink focus ring, `aria-current` on navigation and the
lifecycle step, `aria-label` and `title` on icon buttons, no colour-only status, `prefers-reduced-motion` respected.

## How it maps to vbench

| Dashboard concept | Language element |
|---|---|
| A use case's stage | a chip: Requirements and Design are neutral, In code and Closing tests are warn, Built is ok |
| Gate result | a chip: Passing is ok, Failing is risk (always with the word) |
| A use case waiting on another | a warn chip naming what it waits for |
| The V-cycle position of one use case | the numbered life-cycle tracker: done steps green, the current step with a charcoal ring |
| Next step | the one primary (charcoal) action on the page, with the command to copy |
| Generated blocks and the generated use-case diagram | labelled "Generated, do not edit" in a warn chip or a caption |
| The use-case view | the case view: facts, tracker, criteria, order, diagrams, then the spec |

**AI purple and the human-note yellow are not used yet.** They mark AI-written and human-written content in the source
language. vbench's generated content is produced by a command, not a model, so it is labelled "generated" instead of
being given the AI sparkle. If the dashboard later shows agent-written drafts, use `--ai` for them.

## The V view

The sidebar is the V-cycle: Specify (requirements, system design, architecture, module design), Build (code) and
Prove (unit, integration, system, acceptance tests). A phase page is the table pattern: a stat row, a use-case filter
(chips), then one row per item with a kind chip and a status chip that always carries a word. An item page is the case
view: a V diagram of the item's use case in a card, with the item's node outlined in charcoal and the node on the other
arm that pairs with it ringed more lightly.

Each V node is a card with an accent edge (`inset 0 3px 0`) in the colour of its worst status (ok, warning, risk, or the
input border when empty), so the shape of the project's health reads at a glance without colour carrying meaning alone:
every node also shows its count and the item chips show their status word on hover and on the item page. On narrow
screens the V becomes a stacked Specify, Build, Prove list. The nine phases, their copy and their V positions are in
`src/lib/phases.tsx` and `src/components/VDiagram.tsx`; a test keeps them in step with the backend.

## What was left out on purpose

The language is branded for AGIL Secure Shield (an ST Engineering product) and its skill is marked proprietary, for
internal use. This dashboard adopts the **system** (tokens, shapes, type, components, rules) but not the **brand**:
no AGIL wordmark or mark, no "Secure Shield" lockup, no "by ST Engineering" endorsement, no tagline, no mascot, and not
the dark front-door surface. The lockup is a plain "vbench" with a V mark. The accent colour is the one place the
brand red survives (`--brand`); change that single variable to re-tint the accent bar and the active marker.
Confirm that using the tokens in this project is within the licence before publishing it beyond your own use.

## Working with shadcn

`components.json` is set up (style `new-york`, CSS variables, `@/` aliases), so `npx shadcn@latest add <component>`
works from `src/vbench/ui/`. A freshly added component uses the mapped variables above, so it already looks right; then check it
against the rules: 8px control radius, 12px for surfaces, the four chip tones, 44px targets, no new hues. The
components in `src/components/ui/` were written in the shadcn style and themed by hand.

## Checklist before adding a screen

- One primary action per area; the rest secondary.
- Only the tokens above, each doing its one job; no new hues.
- Radii and shadows from the scales; only interactive cards lift.
- Empty, loading and error states designed.
- Detail on demand (a `<details>`, a drawer, a card one step away), not on the surface.
- Status always carries a word; targets 44px; focus ring visible; labels on icon buttons.
- Colours only from tokens, so dark mode is right for free; try the page in both.
- Anything shown by name is shown with what it is. Breadcrumb on every drill-down, with a menu to its siblings.
- Keep table inputs stable (memoise columns, data and state on the URL); a fresh array each render loops TanStack Table.
- British spelling, sentence case, no em dashes, numbers with context.
