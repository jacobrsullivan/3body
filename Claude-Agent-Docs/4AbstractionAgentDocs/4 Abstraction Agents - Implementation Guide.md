# **Comprehensive Implementation Guide: The 4 Abstractions Agents**

This guide implements a scalable agentic system for generating **C4 Context**, **Sequence**, **Conceptual ERD**, and **State Machine** diagrams in MermaidJS.

It adheres to the **Optimized Architecture v2.1**:

1. **Consolidated Roles**: Uses agent-architect (Builder) and agent-analyst (Critic) instead of one agent per diagram type.
2. **Pointer Pattern**: Skills point to static reference files (templates) rather than containing the instructions themselves.
3. **Immune System**: Includes a Hook to validate Mermaid syntax automatically.

## **1\. Directory Structure**

Ensure your project (or global .claude folder) is structured like this to enable the system:

.claude/
├── agents/
│   ├── agent-architect.md       \# The Builder (Draws the diagrams)
│   └── agent-analyst.md         \# The Critic (Reviews against the 4 rules)
├── skills/
│   ├── project-navigator/       \# Entry point
│   │   └── SKILL.md
│   ├── diagram-c4/              \# Abstraction 1: Scope
│   │   ├── SKILL.md
│   │   └── reference/
│   │       ├── rules.md
│   │       └── template.mmd
│   ├── diagram-sequence/        \# Abstraction 2: Time
│   │   ├── SKILL.md
│   │   └── reference/
│   │       ├── rules.md
│   │       └── template.mmd
│   ├── diagram-erd/             \# Abstraction 3: Data
│   │   ├── SKILL.md
│   │   └── reference/
│   │       ├── rules.md
│   │       └── template.mmd
│   └── diagram-state/           \# Abstraction 4: Logic
│       ├── SKILL.md
│       └── reference/
│           ├── rules.md
│           └── template.mmd
└── settings.json                \# Hooks configuration

## **2\. The Subagents (Roles)**

We avoid creating agent-c4 or agent-erd. Instead, we create a generic **Architect** who uses specific **Skills** to perform the work.

### **2.1 The Architect (Builder)**

**File:** .claude/agents/agent-architect.md

\---
name: agent-architect
description: Use PROACTIVELY for generating architecture diagrams, C4 models, ERDs, sequence diagrams, or state machines.
model: claude-3-5-sonnet-20241022
tools:
  \- name: Edit
  \- name: Read
  \- name: Bash
\---
You are the Lead Systems Architect. Your goal is to visualize complex systems using the "4 Abstractions" framework.

\#\# Your Mandate
1\. \*\*Visualize\*\*: Transform text descriptions or code into MermaidJS diagrams.
2\. \*\*Strict Adherence\*\*: You must follow the specific constraints of the requested abstraction (Scope, Time, Data, or Logic).
3\. \*\*Pointer Pattern\*\*: Before drawing, ALWAYS \`Read\` the reference templates in the loaded skill to ensure syntax correctness.

\#\# Operational Constraints
\- \*\*Output\*\*: Always generate valid MermaidJS code inside \`\`\`mermaid\`\`\` blocks.
\- \*\*Flight Recorder\*\*: Log your design decisions in \`session\_log.md\` before finalizing the diagram.
\- \*\*Validation\*\*: After writing a diagram, ask \`agent-analyst\` to review it against the rules.

### **2.2 The Analyst (Critic)**

**File:** .claude/agents/agent-analyst.md

\---
name: agent-analyst
description: Use for reviewing diagrams, validating logic, or auditing Mermaid syntax against the "4 Abstractions" rules.
model: claude-3-5-sonnet-20241022
\---
You are the Senior Technical Reviewer. You do not write code; you break it.

\#\# Your Mandate
1\. \*\*Audit\*\*: Review Mermaid diagrams created by \`agent-architect\`.
2\. \*\*Enforce Rules\*\*:
   \- \*\*C4\*\*: Reject if it contains protocol details (HTTP/SQL) or tech specs.
   \- \*\*Sequence\*\*: Reject if it lacks "Unhappy Paths" or alternative flows (\`alt\`/\`opt\`).
   \- \*\*ERD\*\*: Reject if it contains physical schema details (Varchar, FKs).
   \- \*\*State Machine\*\*: Reject if it allows illegal transitions.
3\. \*\*Validate\*\*: Ensure the Mermaid syntax compiles.

\#\# Operational Protocol
\- If you find an error, reject the diagram and explain exactly \*which\* rule was violated.
\- Reference the \`session\_log.md\` to understand the Architect's intent.

## **3\. The Skills (Pointer Pattern)**

These skills do not teach the agent *how* to diagram; they point the agent to the *Source of Truth* files.

### **3.1 Abstraction 1: C4 Context (Scope)**

**File:** .claude/skills/diagram-c4/SKILL.md

\---
name: diagram-c4
description: Use when asking "What are we building?". Generates C4 Context diagrams to define System Scope.
\---
\# C4 Context Abstraction (Scope)

\#\# Source of Truth
\- \*\*Rules\*\*: Read \`reference/rules.md\` for the strict "No Technical Details" policy.
\- \*\*Template\*\*: Copy the structure from \`reference/template.mmd\`.

\#\# Usage
1\. Use \`C4Context\` syntax.
2\. Focus on \*\*People\*\* and \*\*Software Systems\*\*.
3\. \*\*Forbidden\*\*: Do not use protocols (HTTP, TCP), database technologies, or internal container details.

**File:** .claude/skills/diagram-c4/reference/rules.md

\# C4 Context Rules
1\. \*\*Purpose\*\*: Defines system boundaries.
2\. \*\*Audience\*\*: Non-technical (CEO, Product Manager).
3\. \*\*The Rule\*\*: Plain English only. No "JSON", "REST", "Postgres". Use "Sends email", "Stores user data".

**File:** .claude/skills/diagram-c4/reference/template.mmd

C4Context
    title System Context Diagram for \[System Name\]

    Person(user, "User", "A user of the system")
    System(system, "Our System", "The core system boundaries")
    System\_Ext(mail, "Email System", "Sends notifications")

    Rel(user, system, "Uses")
    Rel(system, mail, "Sends emails via")

### **3.2 Abstraction 2: Sequence Diagram (Time)**

**File:** .claude/skills/diagram-sequence/SKILL.md

\---
name: diagram-sequence
description: Use when asking "How do pieces talk?". Generates Sequence diagrams for Time & Integration logic.
\---
\# Sequence Diagram Abstraction (Time)

\#\# Source of Truth
\- \*\*Rules\*\*: Read \`reference/rules.md\`. You MUST include Happy and Unhappy paths.
\- \*\*Template\*\*: Use \`reference/template.mmd\`.

\#\# Usage
1\. Use \`sequenceDiagram\` syntax.
2\. Map flow across network boundaries (API, DB, External Service).
3\. \*\*Mandatory\*\*: Use \`alt\` for error states and \`opt\` for optional flows.

**File:** .claude/skills/diagram-sequence/reference/rules.md

\# Sequence Diagram Rules
1\. \*\*Purpose\*\*: Visualizes concurrency and order of operations.
2\. \*\*The Rule\*\*: Always show the "Unhappy Path". What happens if the DB fails? What if the API times out?
3\. \*\*Syntax\*\*: Use \`par\` for parallel tasks and \`critical\` for atomic operations if needed.

**File:** .claude/skills/diagram-sequence/reference/template.mmd

sequenceDiagram
    participant U as User
    participant A as API
    participant D as Database

    U-\>\>A: Request Data
    A-\>\>D: Query ID

    alt Record Found (Happy Path)
        D--\>\>A: Return Data
        A--\>\>U: 200 OK
    else Record Missing (Unhappy Path)
        D--\>\>A: Null
        A--\>\>U: 404 Not Found
    end

### **3.3 Abstraction 3: Conceptual ERD (Data)**

**File:** .claude/skills/diagram-erd/SKILL.md

\---
name: diagram-erd
description: Use when asking "What data do we hold?". Generates Conceptual ERDs.
\---
\# Conceptual ERD Abstraction (Data)

\#\# Source of Truth
\- \*\*Rules\*\*: Read \`reference/rules.md\`. STRICTLY Conceptual—no physical types.
\- \*\*Template\*\*: Use \`reference/template.mmd\`.

\#\# Usage
1\. Use \`erDiagram\` syntax.
2\. \*\*Forbidden\*\*: Do not define \`VARCHAR\`, \`INT\`, \`FK\`, or \`PK\`.
3\. Focus on the \*\*Nouns\*\* and the \*\*Cardinality\*\* (One-to-Many, Many-to-Many).

**File:** .claude/skills/diagram-erd/reference/rules.md

\# Conceptual ERD Rules
1\. \*\*Purpose\*\*: Shared vocabulary between Business and Tech.
2\. \*\*The Rule\*\*: Conceptual level only.
   \- BAD: \`user\_id int\`, \`varchar(255)\`
   \- GOOD: \`string name\`, \`date created\_at\` (or just entity names without fields if high level)
3\. \*\*Relationships\*\*: Verify cardinality ( \`||--|{\` vs \`||--o{\` ).

**File:** .claude/skills/diagram-erd/reference/template.mmd

erDiagram
    USER ||--o{ ORDER : places
    ORDER ||--|{ LINE\_ITEM : contains
    PRODUCT ||--o{ LINE\_ITEM : included\_in

### **3.4 Abstraction 4: State Machine (Logic)**

**File:** .claude/skills/diagram-state/SKILL.md

\---
name: diagram-state
description: Use when asking "What acts are legal?". Generates State Machines for complex entities.
\---
\# State Machine Abstraction (Logic)

\#\# Source of Truth
\- \*\*Rules\*\*: Read \`reference/rules.md\`. Focus on Lifecycle transitions.
\- \*\*Template\*\*: Use \`reference/template.mmd\`.

\#\# Usage
1\. Use \`stateDiagram-v2\` syntax.
2\. Define the lifecycle of a SINGLE key entity (e.g., Order, Ticket, UserSession).
3\. \*\*Critical\*\*: Define specific events that trigger transitions.

**File:** .claude/skills/diagram-state/reference/rules.md

\# State Machine Rules
1\. \*\*Purpose\*\*: Eliminates impossible states and logic errors.
2\. \*\*The Rule\*\*: Only use for core complex entities (Complexity Type: Business Logic).
3\. \*\*Scope\*\*: Do not map the whole UI navigation; map the entity's status changes.

**File:** .claude/skills/diagram-state/reference/template.mmd

stateDiagram-v2
    \[\*\] \--\> Draft
    Draft \--\> Placed : Submit Order
    Placed \--\> Paid : Payment Success
    Placed \--\> Cancelled : User Cancel
    Paid \--\> Shipped : Warehouse Dispatch
    Shipped \--\> \[\*\]

    Cancelled \--\> \[\*\]

## **4\. The Orchestration (Navigator Skill)**

This is the default skill the agent uses to decide which tool to pick.

**File:** .claude/skills/project-navigator/SKILL.md

\---
name: project-navigator
description: PRIMARY SKILL. Use this to identify which "4 Abstractions" tool to use for a request.
\---
\# 4 Abstractions Navigation Map

\#\# Decision Matrix
| User Question / Problem | Abstraction Needed | Delegate To | Skill Trigger |
|-------------------------|--------------------|-------------|---------------|
| "What are we building?" / Scope | \*\*C4 Context\*\* | \`agent-architect\` | \`diagram-c4\` |
| "How does it flow?" / Time | \*\*Sequence Diagram\*\* | \`agent-architect\` | \`diagram-sequence\` |
| "What data is stored?" / Data | \*\*Conceptual ERD\*\* | \`agent-architect\` | \`diagram-erd\` |
| "What is the lifecycle?" / Logic | \*\*State Machine\*\* | \`agent-architect\` | \`diagram-state\` |

\#\# Workflow
1\. Identify the complexity type (Scope, Time, Data, or Logic).
2\. Load the relevant skill.
3\. Architect draws the diagram.
4\. Analyst reviews the diagram.

## **5\. The Immune System (Hooks)**

To ensure the diagrams are actually valid, we configure a hook that runs a syntax check whenever a .mmd file is written.

**File:** .claude/settings.json

{
  "commands": {
    "validate-mermaid": {
      "command": "mmdc \-i \\"$1\\" \-o /dev/null",
      "description": "Validates mermaid syntax using mermaid-cli"
    }
  },
  "hooks": {
    "PostToolUse": {
      "command": "if \[\[ \\"$TOOL\_NAME\\" \== \\"Write\\" && \\"$FILE\_PATH\\" \== \*.mmd \]\]; then mmdc \-i \\"$FILE\_PATH\\" \-o /dev/null || echo \\"MERMAID SYNTAX ERROR: Please fix the diagram syntax.\\"; fi"
    }
  }
}

*(Note: This requires npm install \-g @mermaid-js/mermaid-cli on your machine).*

## **6\. Usage Example**

**User Prompt:**

"I need to design the payment flow for our new app. The user sends a request, we hit Stripe, but sometimes Stripe is down."

**System Behavior:**

1. **Orchestrator**: Recognizes "flow" and "payment flow" → Identifies **Sequence Diagram** (Time Abstraction).
2. **Delegation**: Calls agent-architect with the diagram-sequence skill.
3. **Skill Loading**: agent-architect loads .claude/skills/diagram-sequence/SKILL.md.
4. **Pointer Execution**: Agent reads reference/rules.md and sees it MUST include the "Unhappy Path".
5. **Generation**: Agent writes a Mermaid file including an alt block for "Stripe Down".
6. **Immune System**: The PostToolUse hook runs mmdc to verify the syntax is valid.
7. **Critique**: agent-analyst (if invoked) confirms no database connection details are leaked in the sequence flow if they aren't relevant to the high-level timing.
