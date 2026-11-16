# NFR checklist

Propose only the concerns the request actually triggers. Each accepted one becomes a global `REQ-NFR-nnn` with a
**quality attribute scenario** with six parts, and the ACs it constrains cite it. The last part, the *response measure*,
is the measurable one: a number, a threshold, or a checkable yes/no.

| Part | Asks | Example |
|---|---|---|
| Source | Who or what raises the event? | End user |
| Stimulus | What is the event? | Runs a full-text search |
| Artifact | Which part of the system does it hit? | The search index |
| Environment | What state is the system in? | Normal operation, 10,000 notes |
| Response | What does the system do? | Lists the matching notes |
| Response measure | How is it measured? | Completes in under 150 ms |

| Concern | Triggered when the request... | Questions | Fit criterion, for example |
|---|---|---|---|
| **Security** | adds an endpoint, a credential, a role or a trust boundary | Who may call it? What can an attacker control? | "Unauthenticated calls return 401; a user cannot read another tenant's record" |
| **Privacy** | stores or shows personal data | Which fields are personal? Who sees them? Is consent needed? | "Email is never returned to non-admin roles" |
| **Performance** | sits on a user-facing or high-volume path | What is the expected load and the acceptable latency? | "p95 < 300 ms at 50 req/s on the reference instance" |
| **Availability** | other flows depend on it | What happens when it is down? Is a retry safe? | "Degrades to read-only; recovers without manual action" |
| **Auditability** | changes state someone may later dispute | Who did what, when, from where? How long is it kept? | "Every approval writes an audit row with actor, time and prior state" |
| **Observability** | can fail silently or asynchronously | How will we know it broke? | "Failures log a correlation id and increment an error counter" |
| **Accessibility** | adds or changes UI | Keyboard only? Screen reader? Contrast? | "All controls reachable by keyboard; WCAG 2.2 AA contrast" |
| **Data retention** | creates data that outlives the request | How long? How is it deleted? | "Soft-deleted records purged after 90 days" |

Reject a criterion that cannot fail ("fast", "secure", "user-friendly"): ask for the number or the check.
