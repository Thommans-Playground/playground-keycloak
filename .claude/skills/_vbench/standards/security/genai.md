# GenAI and LLM checklist

Generic questions for a feature that uses a large language model, drawn from the **OWASP Top 10 for LLM
Applications** (the OWASP GenAI Security Project). Use this lens only for a use case that sends data to a model,
uses a model's output, or lets a model call tools or other systems (for example an evaluation judged by a model).
**Written from memory:** the list changes between editions, so fetch the current one from genai.owasp.org before you
rely on it, and write the edition and exact references here. If you also need OWASP's broader AI guidance (the AI
Exchange, or machine learning security), add a file for it.

| ID | Question | Where | Category |
|---|---|---|---|
| GEN-1 | Can text from a person, a file or a web page change what the model is told to do (prompt injection)? What does it stop? | flow, design | Prompt injection |
| GEN-2 | Can the model reveal data it was given: other people's data, secrets, or its instructions? | flow, design | Sensitive information disclosure |
| GEN-3 | Where do the model, its data, plugins and libraries come from, and are they pinned and checked? | design | Supply chain |
| GEN-4 | Can the data a model learns from or retrieves be changed by someone who should not change it? | design | Data and model poisoning |
| GEN-5 | Is the model's output checked before it is shown, stored, run or passed to another system? | design | Improper output handling |
| GEN-6 | What can the model do on its own (tools, writes, sends), with whose authority, and is a person asked first for anything that matters? | flow, design | Excessive agency |
| GEN-7 | Are system prompts free of secrets, and is nothing enforced only by the prompt? | design | System prompt leakage |
| GEN-8 | If retrieval is used, does it respect who may see each document? | design | Vector and embedding weaknesses |
| GEN-9 | Is a wrong or invented answer handled: is it labelled, checked or reviewed before someone relies on it? | flow, criteria | Misinformation |
| GEN-10 | Is there a limit on the size, number and cost of model calls per person? | criteria | Unbounded consumption |
