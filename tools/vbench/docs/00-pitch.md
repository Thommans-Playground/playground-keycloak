> **Superseded.** This is the original pitch, kept for history. It describes a larger product (a Postgres store, a
> central MCP broker, Jira sync, transcript ingestion, brownfield recovery, IDE panels) that does not exist. What
> exists is in the [README](../README.md): files as state, deterministic gates, skills, a dashboard and an MCP server.


VBenchAI: The Agentic Systems Engineering Workbench
#idea 

VBenchAI is a self-hosted, Git-native Agentic Application Lifecycle Management (ALM) platform. It transforms the traditional Systems Engineering V-Model into a high-velocity, automated software delivery loop sitting directly above the execution layer.
Rather than trapping data in proprietary cloud silos, VBenchAI treats your Git repository text files as the single source of truth (Document-as-Code). It orchestrates a dynamic, customizable factory of AI Skill Agents that break down raw human intent (from structured definitions to messy meeting transcripts) into traceable use-case flows, visual diagrams, and project tickets. It then serves this context directly to developers via a local Model Context Protocol (MCP) Server that integrates with terminal tools like Claude Code and modern IDEs [CCDV-F].

1. Architectural Strategy: The Dual-Engine Pipeline
VBenchAI operates directly on local file structures within your internal network, supporting both greenfield forward generation and brownfield legacy recovery.

 [ GREENFIELD PATHWAY ]                              [ BROWNFIELD PATHWAY ]
 ┌──────────────────────┐                            ┌──────────────────────┐
 │ Meeting Transcript   │                            │ Existing Git Repo    │
 └──────────┬───────────┘                            └──────────┬───────────┘
            │ Forward Generation                                │ Reverse Engineering
            ▼                                                   ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            VBENCHAI AUTOMATION LOOPS                             │
│                                                                                  │
│   .vbench/reqs.md   ◄───►   .vbench/flows.md   ◄───►   .vbench/architecture.mermaid│
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
                                         ▼ Establishes Local Truth
                        ┌─────────────────────────────────┐
                        │      Central MCP Server         │ ◄── Feeds Claude Code
                        └─────────────────────────────────┘

The Greenfield Pathway (Forward Generation)
* Transcript Ingestion: Users drop raw meeting minutes or audio transcripts directly into the system via the local CLI (vbench ingest --transcript huddle.txt).
* Intent Extraction: The platform parses conversational dialogue, automatically generating .vbench/requirements.md split into Functional requirements and Non-Functional security/performance criteria.
* Symmetrical Test Drafting: The loop automatically maps use cases directly to Gherkin Behavior-Driven Development (BDD) .feature files, locking down validation criteria parallel to requirement definitions before code is written.

The Brownfield Pathway (Reverse Engineering)
* Repository Analysis: For legacy codebases lacking documentation, VBenchAI scans repository files, routing mechanisms, and data schemas.
* System Reconstruction: The engine works backward up the V-cycle, generating technical specifications, use-case logs, and architectural maps from the existing raw code.
* The Baseline Blueprint: Legacy applications are automatically modernized with full documentation, laying the groundwork for safe, contextual refactoring.



2. Core Feature Pillars

The Open Agent & Tool Factory
* Dynamic Agent Configuration: Organizations are not locked into standard agents. Teams can build infinitely customizable workforces by creating configuration profiles directly in code (.vbench/agents/auditor.json).
* Decoupled Tool Binding: Your central VBenchAI MCP server acts as a Universal Tool Broker [CCDV-F]. Custom agents are dynamically equipped with atomic enterprise toolkits (e.g., scan_for_secrets(), run_gherkin_validation(), query_jira_tickets()).

High-Velocity Git & Kanban Orchestration
* Flow-to-Branch Isolation: Requirements are broken down into discrete user flows. Every unique flow is assigned its own tracking structures to isolate development work.
* Automated Branch Provisioning: For every flow, the platform provisions a dedicated Feature Branch (e.g., feature/flow-UC01-auth), pre-populating it with the associated Gherkin test assertions and architecture markdown files.
* Bi-Directional Kanban Synchronization: VBenchAI integrates with Jira and GitHub Projects. It breaks down use cases into precise developer tasks (Database schema updates, Backend endpoints, UI implementation), dynamically shifting cards on the board based on live engineering progress.

The Continuous Acceleration Recycle Loop
* Bi-Directional Drift Prevention: If a project manager updates a requirement in the VBenchAI viewport dashboard, the change cascades downstream automatically. Affected Mermaid diagrams are updated, Gherkin test criteria adapt, and the associated Kanban tasks shift back to the "Refining" state.
* Autofix Feedback Loop: When testing agents detect a validation failure on the right side of the V, the error logs are bundled with the design spec and recycled back down to the implementation layer, allowing tools like Claude Code to fix code bugs within seconds.

3. The IDE Connector Network & MCP Engine
Developers do not need to switch tools or leave their high-velocity development environments to stay aligned with corporate standards.
* The Live Context Oracle: Running as a centralized Model Context Protocol (MCP) server inside the internal network, VBenchAI exposes live project states straight to the developer's workstation [CCDV-F].
* In-Editor Panel Integration: Lightweight extensions for VS Code and Cursor map the active Git branch to the database, rendering the exact Mermaid sequence diagrams and checking off local Kanban tasks directly inside the IDE sidebar.
* Supercharging Claude Code: When an engineer executes claude-code in the terminal, Claude automatically calls the local MCP server [CCDV-F]. It receives precise system prompts, functional constraints, corporate stylesheets, and database constraints, ensuring newly generated code passes unit and integration validation suites on the first attempt.
* Prompt Caching Economics: By anchoring static corporate guidelines, CSS templates, and structural specifications at the root of the MCP context window, VBenchAI triggers Anthropic's Prompt Caching protocol. This drops repetitive input token processing costs by up to 90%, allowing 100+ engineers to work simultaneously with negligible API overhead.

4. The VBenchAI Viewport (Optional UI Layer)
For project managers, scrum masters, and directors who need to see how the 100+ engineers are tracking, you expose a lightweight Next.js or React web dashboard that simply reflects the states of the files and tickets.
* The Living V-Graph: A visual command center renders the state of the project. As agents complete requirements, map use cases, design components, and run validations, the nodes on a digital V-graph illuminate in real time.
* Human-in-the-Loop Verification Gate: To eliminate AI hallucinations, senior architects and product owners must review, adjust, and digitally sign off on agent-generated designs and requirements before they are committed down the pipeline.
* Project Traceability Statistics: Real-time health states calculated straight out of your systems engineering loop, including Traceability Score (percentage of requirements with matching Gherkin tests) and Recycle Loop Count (tracking unstable architectures or shifting requirements).

5. Deployment, Security, and Commercialization
VBenchAI is built from the ground up for strict enterprise control, keeping intellectual property shielded and predictable.
* 100% Internal Hosting: The entire platform—including the web front-end, PostgreSQL artifact store, and MCP server—deploys entirely within an organization's private corporate network or secure VPC container.
* Data Sovereignty: Zero source code, transaction histories, or meeting transcripts ever leave the local network infrastructure, bypassing network egress fees while maintaining enterprise data compliance.
* Dual-Horizon Monetization: Built first as a frictionless internal tool to empower 100+ engineers, the file-driven architecture allows it to be packaged as a high-ticket, premium Self-Hosted Enterprise Software Product marketed straight to highly regulated, zero-trust industries (Banks, Government, Healthcare).








