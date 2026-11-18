# Use cases

- [Access use case diagram](diagrams/usecases-access.puml): who starts what, and where Keycloak takes part.
- [Order of execution](diagrams/order-of-execution.puml): how the use cases depend on each other, what is built, and the order to build the rest. Update its colours when a use case is built.
- [Design diagram](../domain/diagrams/access-design.puml): the ports and adapters the use cases share.
- Each use case file has a short **Mermaid overview**, and links to a **PlantUML sequence** (in `diagrams/`) with the
  detail: every step numbered as in the main flow, and the failure paths.

Use Mermaid for the overview that explains a paragraph, and PlantUML for the detail you keep as a reference.
Check the `.puml` files with
`python3 .claude/skills/vbench-puml/scripts/check_diagrams.py docs/usecases/diagrams docs/domain/diagrams`.
