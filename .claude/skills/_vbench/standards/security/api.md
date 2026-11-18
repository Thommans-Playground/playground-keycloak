# API checklist

Generic questions for an API, drawn from the **OWASP API Security Top 10**. The names below are the categories as
remembered. **Written from memory:** fetch the current edition from owasp.org before you rely on it, and write the
edition and the exact references here. Use this lens for every use case that adds or changes an API route.

| ID | Question | Where | Category |
|---|---|---|---|
| API-1 | For every route that takes an id, is it checked that this person may touch this object (not only that they are signed in)? | criteria, flow | Broken object level authorization |
| API-2 | Is the person proved on every request, with no route that skips it by accident, and are tokens and credentials handled safely? | flow, criteria | Broken authentication |
| API-3 | Can a person read or write a field they should not (mass assignment, over-sharing in an answer)? | criteria, design | Broken object property level authorization |
| API-4 | Is there a limit on size, rate and cost of a request, and what happens past it? | criteria | Unrestricted resource consumption |
| API-5 | Is every function checked against the person's role, especially administrative ones? | criteria, rules | Broken function level authorization |
| API-6 | Can a flow be abused at volume (registration, account requests, enumeration), and is that limited? | flow, criteria | Unrestricted access to sensitive business flows |
| API-7 | Does the server fetch a URL a person gave it, and is that restricted? | design | Server side request forgery |
| API-8 | Are errors, headers, CORS, defaults and debug settings safe and the same in every environment? | design | Security misconfiguration |
| API-9 | Are old or unlisted routes and versions known, and removed or protected? | design | Improper inventory management |
| API-10 | Does the API trust the answers of other services (Keycloak, an LLM, a partner) without checking them? | design | Unsafe consumption of APIs |
