## **0\. Short Summary**

This system wires two agents (Architect \+ Analyst), five skills (Navigator \+ 4 diagram skills), reference templates, and a set of CLI-based “forensic” extractors into a single architecture-as-code pipeline.

* **Goal**: Automatically extract, organize, and document four key architectural abstractions—C4 Context, Sequence, Conceptual ERD, and State Machine—directly from code, infra, traces, and schema, and keep them up to date as part of CI/CD.

* **Form factor**: A `.claude/` folder with:

  1. `agents/` (architect \+ analyst prompts),

  2. `skills/` (project-navigator \+ one skill per abstraction),

  3. `reference/` (rules \+ Mermaid templates),

  4. `scripts/` (forensic extractors),

  5. `settings.json` (Mermaid validation \+ optional drift checks).

* **Workflow**:

  1. **Navigator Skill** classifies the user question into Scope / Time / Data / Logic.

  2. **Architect Agent** runs the relevant skill, which:

     * launches **forensic extractors** (Terraform/IaC, Prisma/JPA, OTel traces, AST/ast-grep) to pull raw evidence from the repo and environment,

     * consolidates that evidence into a **Mermaid diagram** using strict diagram rules.

  3. **Analyst Agent** validates diagrams against abstraction-specific rules and Mermaid syntax, with CLI hooks acting as an “immune system”.

  4. CI compares diagrams against **golden masters** and flags architectural drift on PRs.

This guide goes from directory structure → agents → skills → forensic extractors → hooks → CI integration and includes concrete file skeletons you can copy-paste.

---

# **Comprehensive Implementation Guide**

## **The 4-Abstractions Agent System**

C4 Context (Scope) · Sequence (Time) · Conceptual ERD (Data) · State Machine (Logic)

---

## **1\. System Overview**

### **1.1 Objectives**

This implementation is designed to:

1. **Continuously recover real architecture from artifacts**, not interviews or tribal knowledge. Source of truth is code, infra, telemetry, and schema.

2. **Standardize on four diagrams**, each answering exactly one question:

   * *Scope*: What are we building, and who/what do we talk to? (C4 Context)

   * *Time*: How do pieces talk over time for a specific scenario? (Sequence)

   * *Data*: What data do we hold and how is it related? (Conceptual ERD)

   * *Logic*: What state transitions are legal for a key entity? (State Machine)

3. **Treat diagrams as code**: plain-text Mermaid in the repo, versioned, diff-able, validated, and updated via CI.

4. **Use Claude Skills/Agents idiomatically**:

   * Skills are focused folders with `SKILL.md`, reference files, and optional scripts. ([GitHub](https://github.com/anthropics/skills))

   * Agents are defined once and reused across all abstraction types.

### **1.2 Key Design Principles**

* **Two agents, many skills**: reuse a generic Architect (Builder) and Analyst (Critic) instead of creating separate agents per diagram type.

* **Pointer pattern**: skills point to static templates and rules; they do *not* inline everything into SKILL.md (keeps token usage sane and instructions stable).

* **Forensics first**: diagrams are derived from Terraform, Docker Compose, package manifests, ORM definitions, DDL, OTel traces, and AST analysis—not from vibes.

* **Immune system**: every `.mmd` (Mermaid) change is validated by CLI plus Analyst review before it’s considered “real”.

---

## **2\. Directory & Skill Layout**

### **2.1 Top-Level Structure**

Create (or extend) a `.claude/` folder at the root of your repo:

.claude/
├── agents/
│   ├── agent-architect.md
│   └── agent-analyst.md
├── skills/
│   ├── project-navigator/
│   │   └── SKILL.md
│   ├── diagram-c4/
│   │   ├── SKILL.md
│   │   ├── reference/
│   │   │   ├── rules.md
│   │   │   └── template.mmd
│   │   └── scripts/
│   │       ├── extract\_c4\_from\_terraform.sh
│   │       ├── extract\_c4\_from\_compose.sh
│   │       └── extract\_c4\_from\_manifests.sh
│   ├── diagram-sequence/
│   │   ├── SKILL.md
│   │   ├── reference/
│   │   │   ├── rules.md
│   │   │   └── template.mmd
│   │   └── scripts/
│   │       └── trace\_to\_mermaid.py
│   ├── diagram-erd/
│   │   ├── SKILL.md
│   │   ├── reference/
│   │   │   ├── rules.md
│   │   │   └── template.mmd
│   │   └── scripts/
│   │       ├── prisma\_to\_erd.py
│   │       └── ddl\_to\_erd.sh
│   └── diagram-state/
│       ├── SKILL.md
│       ├── reference/
│       │   ├── rules.md
│       │   └── template.mmd
│       └── scripts/
│           ├── extract\_enums\_with\_ast\_grep.yml
│           └── extract\_transitions\_from\_ast.py
├── settings.json
└── diagrams/          \# Output location (optional but recommended)
    ├── context/
    ├── sequence/
    ├── erd/
    └── state/

This follows the Anthropic Skills structure: each skill is a directory with a `SKILL.md` plus any needed resources/scripts. ([GitHub](https://github.com/anthropics/skills))

### **2.2 Where Diagrams Live**

Recommended convention (so humans and CI can find them):

* `diagrams/context/*.mmd` — C4 context diagrams

* `diagrams/sequence/*.mmd` — Sequence diagrams

* `diagrams/erd/*.mmd` — Conceptual ERDs

* `diagrams/state/*.mmd` — State machines

You can mirror this under `docs/` if you prefer, but be consistent and update hooks accordingly.

---

## **3\. Agents**

You already had a simple version of these; this is the expanded, forensics-aware version.

### **3.1 Architect (Builder) – `.claude/agents/agent-architect.md`**

**Role**: Lead Systems Architect \+ Forensic Extractor

**Tools**: `Read`, `Edit`, `Bash` (and anything else you routinely rely on).

Suggested file:

\---
name: agent-architect
description: Use PROACTIVELY for generating architecture diagrams (C4, Sequence, ERD, State Machines) from code, infra, telemetry, and schema artifacts.
model: claude-3-5-sonnet-20241022
tools:
  \- name: Read
  \- name: Edit
  \- name: Bash
\---

You are the Lead Systems Architect AND forensic extractor for this codebase.

Your primary job is to visualize the system using the "4 Abstractions" framework:

1\. C4 Context diagrams (Scope)
2\. Sequence diagrams (Time)
3\. Conceptual ERDs (Data)
4\. State Machines (Logic)

You MUST derive diagrams from artifacts (code, infra, traces, schemas) whenever possible, not from guesswork or outdated docs.

\#\# Core Responsibilities

1\. \*\*Forensic Extraction\*\*
   \- For any diagram request, FIRST run the appropriate scripts from the active Skill's \`scripts/\` directory using the Bash tool.
   \- Use:
     \- Terraform state, Docker Compose, and manifests for Context.
     \- OpenTelemetry or integration-test traces for Sequence.
     \- ORM definitions or DDL for ERD.
     \- Enums, status fields, and AST analysis for State Machines.

2\. \*\*Template-Driven Diagramming\*\*
   \- Before writing any Mermaid, ALWAYS \`Read\`:
     \- \`reference/rules.md\` for the active Skill.
     \- \`reference/template.mmd\` as the starting scaffold.
   \- Start from the template and adapt; do NOT invent your own syntax.

3\. \*\*Strict Abstraction Boundaries\*\*
   \- C4 Context: People \+ Software Systems ONLY. No protocols, tables, or low-level tech names.
   \- Sequence: Cross-boundary message flows \+ happy and unhappy paths.
   \- ERD: Conceptual entities \+ relationships only (no physical types, PK/FK noise).
   \- State Machine: Single key entity lifecycle with legal transitions only.

4\. \*\*Flight Recorder\*\*
   \- Maintain a forensic log in \`diagrams/session\_log.md\`:
     \- What artifacts you inspected (files, commands).
     \- What assumptions you made.
     \- What you chose NOT to include and why.

5\. \*\*Collaboration with Analyst\*\*
   \- After creating or editing any \`.mmd\` file:
     \- Ask \`agent-analyst\` to review the diagram against \`reference/rules.md\`.
     \- If Analyst rejects it, update the diagram and re-run validation.

\#\# Operational Constraints

\- Output MUST be valid Mermaid within \`\`\`mermaid\`\`\` fences.
\- Prefer small, focused diagrams over kitchen-sink monstrosities.
\- If artifacts contradict existing diagrams, treat artifacts as truth and mark diagrams as outdated in \`session\_log.md\`.

### **3.2 Analyst (Critic) – `.claude/agents/agent-analyst.md`**

**Role**: Senior Reviewer / Architecture Tester

\---
name: agent-analyst
description: Use for reviewing Mermaid diagrams, enforcing 4-Abstractions rules, and catching invalid states or syntax.
model: claude-3-5-sonnet-20241022
\---

You are the Senior Technical Reviewer. You do NOT write diagrams; you break them.

\#\# Core Responsibilities

1\. \*\*Rule Enforcement\*\*
   \- C4 Context:
     \- Reject any mention of protocols, ports, table names, or infra-level details.
     \- Diagram must be understandable by a non-technical stakeholder.
   \- Sequence:
     \- Reject if there is no unhappy path (no \`alt\`/\`else\` for failure).
     \- Reject if obvious external dependencies are missing.
   \- ERD:
     \- Reject physical schema details (VARCHAR, INT, FK/PK, index names).
     \- Reject join tables that should be collapsed into many-to-many relationships.
   \- State Machine:
     \- Reject illegal transitions (e.g., skipping mandatory intermediate states).
     \- Flag dead or unreachable states.

2\. \*\*Syntax Validation\*\*
   \- Check diagrams against \`reference/rules.md\` for the relevant Skill.
   \- Assume the CLI hook has run Mermaid validation, but still sanity-check Mermaid syntax and structure.

3\. \*\*Intent vs Implementation\*\*
   \- Read \`diagrams/session\_log.md\` to understand the Architect's intent.
   \- If the diagram does not match artifact evidence, call that out explicitly.

4\. \*\*Feedback Format\*\*
   \- For each issue, state:
     \- Which rule is violated (quote from \`rules.md\` when useful).
     \- Concrete example from the diagram.
     \- Specific, minimal fix.

You are strict. If in doubt, reject and ask for clarification or additional evidence from artifacts.

---

## **4\. Skills**

Each skill is a focused folder with:

* `SKILL.md` containing:

  * YAML frontmatter: `name`, `description`, optional `version`, `dependencies`. ([Claude Help Center](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills))

  * Clear instructions, workflow, examples, guidelines.

* `reference/rules.md` spelling out constraints and “what not to do”.

* `reference/template.mmd` giving a canonical Mermaid scaffold.

* `scripts/` implementing the forensic extractors (Bash/Python/whatever) that the Architect invokes.

This section gives usable skeletons for SKILL.md and rule/template files.

---

### **4.1 Project Navigator Skill – `.claude/skills/project-navigator/SKILL.md`**

Purpose: Decide which abstraction/skill to load for a given user request.

\---
name: project-navigator
description: PRIMARY SKILL. Classify architecture questions into Scope, Time, Data, or Logic and route to the appropriate 4-Abstractions diagram skill.
version: 1.0.0
\---

\# 4 Abstractions Project Navigator

Use this skill first when the user asks any of:

\- "Help me understand this system"
\- "Draw architecture diagrams"
\- "What does this service talk to?"
\- "How does checkout work?"
\- "What data model do we have?"
\- "What states can an order be in?"

\#\# Decision Matrix

| User intent / phrasing                            | Complexity Type | Diagram             | Delegate to Agent | Skill to Load   |
|--------------------------------------------------|-----------------|---------------------|-------------------|-----------------|
| "What are we building?", "What does it talk to?" | Scope           | C4 Context          | \`agent-architect\` | \`diagram-c4\`    |
| "How does it flow?", "What happens when...?"     | Time            | Sequence Diagram    | \`agent-architect\` | \`diagram-sequence\` |
| "What data do we hold?"                          | Data            | Conceptual ERD      | \`agent-architect\` | \`diagram-erd\`   |
| "What is the lifecycle?", "What states exist?"   | Logic           | State Machine       | \`agent-architect\` | \`diagram-state\` |

\#\# Workflow

1\. Read the user request carefully.
2\. Map it to one complexity type using the table above.
3\. Load the corresponding diagram skill.
4\. Ask \`agent-architect\` to:
   \- Run forensic scripts from that skill.
   \- Generate or update the appropriate Mermaid diagram.
5\. Optionally, ask \`agent-analyst\` to review the resulting diagram.

\#\# Guidelines

\- If the request spans multiple types ("new feature changes flow and data"), split the work:
  \- First Sequence (Time), then ERD (Data), etc.
\- If the user explicitly asks for a specific diagram type, honour that even if the classification would choose differently.

---

### **4.2 C4 Context Skill – `.claude/skills/diagram-c4/SKILL.md`**

#### **SKILL.md skeleton**

\---
name: diagram-c4
description: Use when answering “What are we building and who/what do we interact with?”. Generates C4-style Context diagrams from infra and dependency artifacts.
version: 1.0.0
dependencies:
  \- jq\>=1.6
  \- yq\>=4.0
\---

\# C4 Context Abstraction (Scope)

\#\# Purpose

Produce \*\*high-level context diagrams\*\* answering:
\> What is the System Under Discussion, who uses it, and which external systems does it integrate with?

\#\# Source of Truth

When this Skill is active, ALWAYS derive the diagram from:

1\. \*\*Infrastructure as Code\*\*
   \- \`terraform.tfstate\` for cloud resources and external systems.
   \- \`docker-compose.yml\` and/or Kubernetes manifests for containers and local context. :contentReference\[oaicite:16\]{index=16}
2\. \*\*Dependency Manifests\*\*
   \- \`package.json\`, \`pom.xml\`, \`go.mod\`, etc. for SaaS dependencies (Stripe, SendGrid, etc.). :contentReference\[oaicite:17\]{index=17}
3\. \*\*Version Control History (optional)\*\*
   \- Git temporal coupling to spot logically related components that may belong to same system boundary. :contentReference\[oaicite:18\]{index=18}

\#\# Workflow (for agent-architect)

1\. Run extraction scripts from \`scripts/\`:
   \- \`extract\_c4\_from\_terraform.sh\`
   \- \`extract\_c4\_from\_compose.sh\`
   \- \`extract\_c4\_from\_manifests.sh\`
2\. Combine script outputs into a candidate list of:
   \- People (actors)
   \- Internal software systems (System Under Discussion \+ major subsystems)
   \- External systems (DBs, queues, SaaS APIs, monitoring/alerting).
3\. \`Read\` \`reference/rules.md\` and \`reference/template.mmd\`.
4\. Instantiate a new or updated Mermaid diagram in \`diagrams/context/\<name\>.mmd\`.
5\. Call \`agent-analyst\` to validate.

\#\# Usage Rules (Key)

\- Only show \*\*People\*\* and \*\*Software Systems\*\* (internal vs external).
\- Use plain English descriptions; no protocols, ports, or vendor-specific jargon.
\- If Terraform shows a resource but there is no real traffic (per runtime checks), log it as potential dead dependency in \`session\_log.md\`.

\#\# Example Prompts

\- "Use the C4 Context skill to show all external systems our \`checkout\` service talks to."
\- "Update the system context for our monolith after the new payments microservice was added."

\#\# Guidelines

\- Prefer one diagram per bounded context or top-level service, not one giant enterprise-wide context map.
\- If extraction scripts disagree (e.g., Terraform vs manifests), prefer \*\*runtime \+ state\*\* and log the discrepancy.

#### **`reference/rules.md` (C4)**

You already had an early version; here’s a stricter one blending your guide \+ forensic reality.

\# C4 Context Rules

1\. Purpose
   \- Define the boundaries of the System Under Discussion (SUD) and its external interactions.

2\. Audience
   \- Non-technical stakeholders should be able to read this without explanation.

3\. Allowed Elements
   \- People (actors, roles, organizations).
   \- Software systems:
     \- The SUD (primary system).
     \- External systems (SaaS, third-party APIs, external DBs or services owned by other teams).

4\. Forbidden Details
   \- No protocols: no "HTTP", "gRPC", "TCP", "SMTP", "REST", etc.
   \- No physical tech: no "Postgres", "Redis", "Kinesis", "S3", "Lambda", etc.
   \- No internal containers, microservices, databases inside the SUD boundary.

5\. Labeling
   \- Use plain English verbs: "uses", "sends notifications to", "stores user data in", "publishes events to".
   \- System descriptions must be one short sentence in non-technical language.

6\. Consistency Checks
   \- Every external system in the diagram MUST be backed by:
     \- An IaC resource OR
     \- A real dependency (library \+ imports) OR
     \- Runtime network traffic.
   \- If a resource exists in Terraform but has no real usage, note it in \`session\_log.md\` as "Zombie dependency".

#### **`reference/template.mmd` (C4)**

C4Context
title System Context Diagram for \[System Name\]

Person(user, "User", "A person who uses \[System Name\]")
System(system, "\[System Name\]", "High-level description of what the system does")

System\_Ext(ext1, "\[External System 1\]", "What it does for or to the system")
System\_Ext(ext2, "\[External System 2\]", "What it does for or to the system")

Rel(user, system, "Uses")
Rel(system, ext1, "Sends/receives \[business thing\]")
Rel(system, ext2, "Sends/receives \[business thing\]")

---

### **4.3 Sequence Skill – `.claude/skills/diagram-sequence/SKILL.md`**

This one centers on OTel traces \+ integration tests.

\---
name: diagram-sequence
description: Use when answering “How do components interact over time for a scenario?”. Generates Sequence diagrams from traces and integration tests.
version: 1.0.0
dependencies:
  \- python\>=3.10
  \- opentelemetry-exporter\>=\<your-version\>
\---

\# Sequence Diagram Abstraction (Time)

\#\# Purpose

Visualize \*\*runtime interactions over time\*\* for a single scenario (e.g., "Place Order", "Reset Password"):
\- Participants (services, DBs, queues, external APIs).
\- Ordered messages between them.
\- Happy path AND unhappy/error paths.

\#\# Source of Truth

1\. \*\*OpenTelemetry traces\*\* for real scenarios (preferred). :contentReference\[oaicite:21\]{index=21}
2\. \*\*Integration tests\*\* instrumented to emit traces for specific flows.
3\. Logs only as a last resort.

\#\# Workflow (for agent-architect)

1\. Identify the scenario:
   \- Use user prompt plus code (controller, endpoint, or test names).
2\. Run \`scripts/trace\_to\_mermaid.py\` with:
   \- Either a trace ID from OTel
   \- Or a test name that triggers a trace export.
3\. The script outputs canonical Mermaid \`sequenceDiagram\` text into \`diagrams/sequence/\<scenario\>.mmd\`.
4\. \`Read\` \`reference/rules.md\` and \`reference/template.mmd\`.
5\. Adjust the generated diagram to:
   \- Remove low-level noise.
   \- Add \`alt\`/\`else\` blocks for unhappy paths if missing.
   \- Use \`par\` for parallel spans when appropriate.
6\. Call \`agent-analyst\` to validate.

\#\# Usage Rules (Key)

\- Show only cross-boundary messages (network, process, or domain-level calls).
\- Always include at least one unhappy path (timeout, error, invalid input).
\- Use \`par\` for clear parallelism; avoid faking concurrency with sequential arrows.

\#\# Example Prompts

\- "Generate a sequence diagram for the checkout flow (happy \+ payment failure)."
\- "Update the login sequence after we added MFA."

\#\# Guidelines

\- If more than \~6 participants appear, consider splitting or grouping.
\- Keep message labels at business level ("Charge card", "Persist order"), not raw function names.

#### **`reference/rules.md` (Sequence)**

\# Sequence Diagram Rules

1\. Purpose
   \- Make the order of interactions and failure modes explicit for a specific scenario.

2\. Required Structure
   \- Use \`sequenceDiagram\` syntax.
   \- Declare all participants at the top.
   \- Include a clearly labeled starting actor (usually a user or external system).

3\. Mandatory Unhappy Path
   \- Every diagram MUST contain at least one \`alt\` block showing an error or alternative outcome (e.g., payment failure, timeout, validation error).

4\. Concurrency
   \- When traces show overlapping spans with the same parent, wrap them in \`par ... end\`.
   \- Only mark as parallel when truly overlapping.

5\. Content Rules
   \- Messages must be understandable summaries, not raw method names.
   \- Avoid database table and column names; treat DBs as participants.

6\. Trace Fidelity
   \- The diagram must not contradict the trace data:
     \- If a service appears in the trace, it should appear as a participant.
     \- If an external call is critical (payment, email, shipping), it must be included.

#### **`reference/template.mmd` (Sequence)**

sequenceDiagram
    actor U as User
    participant FE as Frontend
    participant API as Backend API
    participant DB as Database
    participant EXT as External Service

    U-\>\>FE: \[User action\]
    FE-\>\>API: \[Request description\]
    API-\>\>DB: \[Read/write operation\]

    alt Happy Path
        DB--\>\>API: \[Success result\]
        API-\>\>EXT: \[External call\]
        EXT--\>\>API: \[Success response\]
        API--\>\>FE: \[Success payload\]
        FE--\>\>U: \[Success UI\]
    else Failure (e.g., external outage)
        DB--\>\>API: \[Success result\]
        API-\>\>EXT: \[External call\]
        EXT--\>\>API: \[Error / timeout\]
        API--\>\>FE: \[Error payload\]
        FE--\>\>U: \[Error UI\]
    end

---

### **4.4 ERD Skill – `.claude/skills/diagram-erd/SKILL.md`**

Conceptual data modeling via ORM or DDL, heavily de-noised.

\---
name: diagram-erd
description: Use when answering “What data do we hold and how is it related?”. Generates \*\*conceptual\*\* ERDs from ORM schemas or database DDL.
version: 1.0.0
dependencies:
  \- prisma\>=\<your-version\>  \# if applicable
  \- python\>=3.10
\---

\# Conceptual ERD Abstraction (Data)

\#\# Purpose

Show \*\*business entities and relationships\*\* only:
\- Nouns: User, Order, Product, Subscription, etc.
\- Relationships: one-to-one, one-to-many, many-to-many.

No physical schema noise.

\#\# Source of Truth

1\. \*\*ORM definitions\*\* (preferred): Prisma schema, JPA/Hibernate entities, Rails models, etc.
2\. \*\*DDL\*\*: database schema (when ORM not available).
3\. Ignore migrations, audit/log tables, and purely technical entities.

\#\# Workflow (for agent-architect)

1\. Detect ORM:
   \- If \`schema.prisma\` exists → run \`scripts/prisma\_to\_erd.py\`.
   \- If JPA/Hibernate annotations exist → run \`scripts/prisma\_to\_erd.py\` equivalent for Java.
   \- Else fallback to \`scripts/ddl\_to\_erd.sh\`.
2\. Extraction must:
   \- Strip technical columns (\`created\_at\`, \`updated\_at\`, \`deleted\_at\`, etc.).
   \- Collapse join tables into many-to-many relationships where appropriate. :contentReference\[oaicite:24\]{index=24}
3\. Script writes an initial \`erDiagram\` into \`diagrams/erd/\<bounded-context\>.mmd\`.
4\. \`Read\` \`reference/rules.md\` and \`reference/template.mmd\`.
5\. Rename entities and relationships to \*\*business language\*\* if needed.
6\. Call \`agent-analyst\` to validate.

\#\# Usage Rules (Key)

\- Do NOT show column types, PK/FK names, or indexes.
\- Use entity names and cardinalities only.
\- Minor technical tables can be omitted entirely.

\#\# Example Prompts

\- "Create a conceptual ERD for our billing context from Prisma."
\- "Update the ERD after adding subscriptions and invoices."

\#\# Guidelines

\- Prefer separate ERDs per domain (“Billing”, “Identity”, “Fulfillment”) instead of one mega-diagram.
\- Use consistent naming with product/business language.

#### **`reference/rules.md` (ERD)**

\# Conceptual ERD Rules

1\. Purpose
   \- Provide a shared vocabulary for business and engineering about core entities and relationships.

2\. Level of Detail
   \- Conceptual/logical level only.
   \- No column types or database engine details.
   \- A few illustrative attributes per entity are allowed but optional.

3\. Relationships
   \- Use Mermaid \`erDiagram\` cardinality:
     \- \`||--o{\` for one-to-many.
     \- \`}o--o{\` for many-to-many.
   \- Join tables that contain only FKs and audit columns MUST be collapsed to many-to-many.

4\. Naming
   \- Use clean business names, not table prefixes or suffixes (\`tbl\_\`, \`\_entity\`, etc.).
   \- Relationship labels should be verbs: "places", "contains", "belongs to".

5\. Consistency with Schema
   \- Every relationship in the ERD should correspond to:
     \- ORM association OR
     \- FK in the schema.
   \- If the data shows violations (e.g., null FK where relationship is modeled mandatory), note it in \`session\_log.md\` as an inconsistency.

#### **`reference/template.mmd` (ERD)**

erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ ORDER\_ITEM : contains
    PRODUCT ||--o{ ORDER\_ITEM : appears\_on

    CUSTOMER {
        string name
        string email
    }

    ORDER {
        date order\_date
        string status
    }

    PRODUCT {
        string sku
        string name
    }

---

### **4.5 State Machine Skill – `.claude/skills/diagram-state/SKILL.md`**

State extraction from enums \+ control flow.

\---
name: diagram-state
description: Use when answering “What actions are legal at each stage of an entity's lifecycle?”. Generates State Machine diagrams from enums and stateful logic.
version: 1.0.0
dependencies:
  \- ast-grep\>=\<your-version\>
  \- python\>=3.10
\---

\# State Machine Abstraction (Logic)

\#\# Purpose

Make implicit state machines explicit for ONE core entity at a time:
\- Order, Ticket, UserAccount, Subscription, etc.
\- States \+ allowed transitions \+ terminal states.

\#\# Target Selection

Prioritize entities that:
\- Have 3+ meaningful states.
\- Drive critical business logic.
\- Are currently implemented via enums or tangled booleans.

\#\# Source of Truth

1\. Enum definitions & status fields.
2\. Control flow that mutates those fields (if/switch blocks, service methods).
3\. For legacy code: combinations of boolean flags analyzed symbolically. :contentReference\[oaicite:26\]{index=26}

\#\# Workflow (for agent-architect)

1\. Choose the entity (from prompt or from code inspection).
2\. Run:
   \- \`extract\_enums\_with\_ast\_grep.yml\` to list candidate state enums.
   \- \`extract\_transitions\_from\_ast.py\` to extract \`(old\_state, new\_state, event)\` tuples.
3\. Script writes \`stateDiagram-v2\` skeleton to \`diagrams/state/\<entity\>.mmd\`.
4\. \`Read\` \`reference/rules.md\` and \`reference/template.mmd\`.
5\. Clean up:
   \- Remove unreachable or unused states.
   \- Merge duplicated or purely technical states if needed.
   \- Label transitions with business events.
6\. Call \`agent-analyst\` to validate.

\#\# Usage Rules (Key)

\- Only one entity per diagram.
\- State names must be meaningful to the business (not “STATE\_3”).
\- No UI flows; this is entity lifecycle, not navigation.

\#\# Example Prompts

\- "Extract the order status state machine from our checkout service."
\- "Show the allowed transitions for a user account (activation, suspension, closure)."

\#\# Guidelines

\- If the current implementation uses multiple booleans, model the \*\*intended\*\* single-state machine and highlight any contradictory combinations in \`session\_log.md\`.

#### **`reference/rules.md` (State)**

\# State Machine Rules

1\. Scope
   \- One diagram per core entity (e.g., Order, Ticket, UserAccount).
   \- Do not model entire UIs or workflows as state machines here.

2\. Structure
   \- Use \`stateDiagram-v2\`.
   \- Mark a single initial state (\`\[\*\] \--\> ...\`) and any terminal states (\`... \--\> \[\*\]\`).

3\. Transition Rules
   \- Every arrow must be backed by code that mutates the state.
   \- Illegal transitions (forbidden by business rules) must NOT appear.
   \- If code allows a transition that business rules forbid, mark it in \`session\_log.md\`.

4\. Consistency Checks
   \- Detect:
     \- Dead states (no outgoing transitions) that are not intended terminal states.
     \- Unreachable states (no incoming transitions).
   \- Flag them in review.

5\. Naming
   \- Prefer names like \`Draft\`, \`PendingPayment\`, \`Paid\`, \`Shipped\` over generic identifiers.

#### **`reference/template.mmd` (State)**

stateDiagram-v2
    \[\*\] \--\> Draft

    Draft \--\> PendingPayment : checkout order
    PendingPayment \--\> Paid : payment success
    PendingPayment \--\> Cancelled : user cancels / timeout
    Paid \--\> Shipped : ship order
    Shipped \--\> Delivered : confirm delivery
    Paid \--\> Cancelled : refund

    Cancelled \--\> \[\*\]
    Delivered \--\> \[\*\]

---

## **5\. Forensic Extraction Scripts (Conceptual Design)**

You don’t have to implement all of these on day one, but this is the target design. All of this is drawn from the “Automated Forensic Architecture Recovery” report.

### **5.1 C4 Scripts**

* `extract_c4_from_terraform.sh`

  * Input: `terraform.tfstate`

  * Uses `jq` to:

    * Enumerate resources like `aws_db_instance`, `aws_sqs_queue`, `google_sql_database_instance`, `pagerduty_service`, etc.

    * Emit a JSON list of `{name, type, inferred_role}` (e.g., DB, queue, monitoring).

  * Optionally derive edges from security groups \+ IAM policies (who can talk to whom).

* `extract_c4_from_compose.sh`

  * Input: `docker-compose.yml`

  * Uses `yq` to:

    * Enumerate services and mark those built from local context as internal containers.

    * Identify infra containers (e.g., `postgres`, `redis`) as dependencies.

    * Output candidate internal/external systems and networks.

* `extract_c4_from_manifests.sh`

  * Inputs: `package.json`, `pom.xml`, `go.mod`, etc.

  * Uses manifest parsing \+ a mapping table of libraries → external services (e.g., `stripe-node` → Stripe, `@sendgrid` → SendGrid).

  * Outputs a list of SaaS-style external systems.

The Architect then merges these into a single view, filters based on runtime evidence (if available), and maps them to C4 elements.

### **5.2 Sequence Script**

* `trace_to_mermaid.py`

  * Input: OTel trace JSON for a single scenario (from production or a test run).

  * Steps:

    1. Collect unique `service.name` values → Mermaid `participant` declarations.

    2. Sort spans by start time.

    3. For each span, map parent/child service pairs to `A->>B: operationName`.

    4. Optionally generate return arrows with HTTP status codes.

    5. Detect overlapping child spans of the same parent and wrap in `par ... end`.

    6. Emit `sequenceDiagram` text.

Architect then trims noise and adds explicit alt/else blocks.

### **5.3 ERD Scripts**

* `prisma_to_erd.py`

  * Input: `schema.prisma`.

  * Steps:

    * Parse models and relations.

    * Remove technical fields (`created_at`, `updated_at`, etc.).

    * Identify and collapse join models (only FKs \+ audit fields).

    * Output Mermaid `erDiagram` blocks.

* `ddl_to_erd.sh`

  * Inputs: DB DDL (e.g. `pg_dump --schema-only`).

  * Use SchemaSpy or similar to:

    * Extract tables, PKs, FKs.

    * Apply key-only view: show entities and relationships without full column list.

### **5.4 State Scripts**

* `extract_enums_with_ast_grep.yml`

  * AST-grep rules to identify enum definitions and status-like fields.

* `extract_transitions_from_ast.py`

  * Looks for control-flow patterns where state changes conditionally (if/switch blocks).

  * Outputs `(from_state, to_state, event_source)` tuples to be turned into stateDiagram transitions.

---

## **6\. Hooks & Immune System – `.claude/settings.json`**

You already had a basic Mermaid validator hook; this extends it and brings it closer to architecture-as-code.

{
  "commands": {
    "validate-mermaid": {
      "command": "mmdc \-i \\"$1\\" \-o /dev/null",
      "description": "Validates Mermaid syntax using mermaid-cli"
    },
    "diff-diagram": {
      "command": "git diff \--exit-code \-- \\"$1\\" || echo \\"DIAGRAM\_CHANGED\\"",
      "description": "Detects if a diagram changed compared to main"
    }
  },
  "hooks": {
    "PostToolUse": {
      "command": "if \[\[ \\"$TOOL\_NAME\\" \== \\"Write\\" && \\"$FILE\_PATH\\" \== \*.mmd \]\]; then mmdc \-i \\"$FILE\_PATH\\" \-o /dev/null || echo \\"MERMAID SYNTAX ERROR: Please fix the diagram syntax.\\"; fi"
    }
  }
}

You can add more specialized hooks later (e.g., state-machine reachability checks or ERD consistency linters), but start with syntax validation.

---

## **7\. CI/CD Integration (Architecture-as-Code)**

Borrowing from the “Architecture-as-Code pipeline” concept:

1. **On every PR / main build**:

   * Run forensic extractors for each abstraction (as applicable).

   * Regenerate diagrams under `diagrams/`.

2. **Compare vs main branch**:

   * If a diagram’s structure changes materially (new node, new edge, new state), flag:

     * A comment on the PR: “Architectural change detected in `<diagram>`; please review.”

3. **Golden Masters for critical flows**:

   * For key scenarios (e.g., checkout, signup), keep golden master sequence diagrams.

   * If generated sequence diagram for the scenario differs from golden master, require manual review.

4. **Fail-fast policies** (optional):

   * Fail the build if:

     * Mermaid validation fails.

     * Analyst-style checks (run via linter scripts) find illegal state transitions or missing unhappy paths.

This makes architectural changes explicit, reviewable, and testable—same status as code changes.

---

## **8\. Implementation Plan (Pragmatic Rollout)**

If you don’t want to boil the ocean in one go, roll it out like this:

1. **Phase 0 – Skeleton**

   * Create `.claude/agents/` with Architect \+ Analyst as above.

   * Add `project-navigator` and `diagram-*` skills with basic `rules.md` and `template.mmd`, even before scripts are perfect.

   * Wire `settings.json` with Mermaid validation.

2. **Phase 1 – Manual-forensic, Script-light**

   * Architect still reads Terraform/Prisma/OTel manually using `Read`/`Bash`.

   * Scripts are placeholders or “helpers”, not full automation.

   * Goal: prove the workflow and validate that the four diagrams actually help your team.

3. **Phase 2 – Scripted Extraction**

   * Implement `extract_*` and `trace_to_mermaid.py` scripts incrementally.

   * Start with one bounded context or service to avoid thrash.

   * Put scripts under test (unit tests using canned traces and schemas).

4. **Phase 3 – CI Integration**

   * Add jobs to generate diagrams on PR.

   * Add failing conditions for syntax errors and mis-aligned state machines/ERDs.

5. **Phase 4 – Enforcement & Governance**

   * Require updated diagrams when:

     * New external dependency is added.

     * New entity or major state is added.

   * Make diagram diffs part of architectural review criteria.

Don’t lie to yourself: the forensic automation isn’t trivial. But you can get value with a manual-first, script-second approach and evolve toward full automation.

---

## **9\. Example Usage Flows**

### **9.1 “What are we building?” – C4 Context**

1. User: “Show me the system context for our `billing-service`.”

2. Navigator → `diagram-c4`.

3. Architect:

   * Runs Terraform \+ Compose \+ manifest scripts.

   * Reads C4 rules \+ template.

   * Writes/updates `diagrams/context/billing-service.mmd`.

   * Logs extraction steps in `session_log.md`.

4. Analyst:

   * Rejects any protocol or vendor-specific detail.

   * Confirms all externals appear in infra/manifest evidence.

### **9.2 “How does checkout work?” – Sequence**

1. User: “Generate a sequence diagram for checkout, including when Stripe is down.”

2. Navigator → `diagram-sequence`.

3. Architect:

   * Runs `trace_to_mermaid.py` for the “checkout” trace/test.

   * Adds alt block for “Stripe down” if not auto-detected.

4. Analyst:

   * Enforces presence of unhappy path.

   * Checks participants and messages against trace evidence.

…and similarly for ERD (data) and State Machines (logic).

---
