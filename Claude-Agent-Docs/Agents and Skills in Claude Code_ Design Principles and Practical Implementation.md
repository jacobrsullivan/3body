# Agents and Skills in Claude Code: Design Principles and Practical Implementation

# **1\. Overview**

* **Skills** are **progressive-disclosure workflows** that tell the agent *where to look* and *how to work*, without duplicating implementation code. They exist to fix token inefficiency and code-rot.

* **Agents/Subagents** are **delegates with isolated context**. They exist to handle noisy, long-running tasks without polluting the orchestrator’s context, and to enforce policy via specialized personas.

* **Claude Code (and the Agent SDK)** is the **execution harness**:

  * `CLAUDE.md` \= layered, always-on project memory.

  * `.claude/` \= skills, agents, hooks, settings.

  * Hooks, Checkpoints, Slash Commands, MCP \= safety \+ automation \+ I/O.

**From “stuffing instructions into prompts” → to “composable, auditable architecture”:**

* Pointer Skills (no code in markdown)

* Role-based Subagents (few, high-quality, isolated)

* Deterministic Hooks \+ Checkpoints as an “immune system”

Everything below is just that idea unpacked and made buildable.

---

# **2\. Design Principles**

## **2.1 Skills – Progressive Disclosure & Clear Workflows**

### **2.1.1 Purpose: Autonomous knowledge, not static tutorials**

* A **Skill** is for **reusable workflows and domain knowledge** that the *main agent* should load **on demand**, not always.

* Skills exist to solve **token inefficiency** of big CLAUDE.md files and random documentation.

* The **description field is the API**: if it’s vague, the skill will never be invoked. If it clearly states *what* and *when to use*, it becomes an autonomous capability.

### **2.1.2 Progressive disclosure as a hard rule**

Design Skills so that **knowledge is revealed in four layers**:

1. **Metadata layer** (always loaded):

   * YAML frontmatter (`name`, `description`, optional `allowed-tools` for Claude Code).

2. **Skill body layer** (loaded on invocation):

   * Markdown in `SKILL.md` with workflow steps.

3. **Skill asset layer** (loaded as needed):

   * Linked `reference/`, `scripts/`, `templates/`, etc.

4. **Codebase layer** (source of truth):

   * The skill *points at* real project files, not copies them (Pointer Pattern).

If you’re tempted to paste long code into `SKILL.md`, don’t – point at files in `src/`, `docs/`, or `scripts/` instead.

### **2.1.3 “Pointer Pattern”, not “Shadow Codebase”**

* **Bad:** SKILL.md contains canonical examples or full implementations that drift from real code.

* **Good:** SKILL.md explicitly tells Claude *where to read* the current implementation and *which scripts to run*.

Principles:

* **Never** teach syntax or patterns via static code in Skills.

* **Always**:

  * List **libraries / directories** as source of truth.

  * Describe **required scripts** (e.g., `./scripts/generate_migration.sh`).

  * Give **rules**, not code: “Always read the last 3 migrations” etc.

### **2.1.4 Skills as clear workflows, not essays**

* Most useful Skills define a **step-by-step workflow** that drives tool usage (“Read → Analyze → Bash → Fix → Re-test”), not a wall of theory.

* The agent should be able to **copy the checklist as its plan** with minimal adaptation.

Design principles for the SKILL body:

* **Short, structured sections:** `Quick start`, `Workflows`, `References`, `Examples`.

* Explicit “if/then” patterns: “If tests fail, re-run step 2 and 3”.

* Call out tools: “Use `Read` on X”, “Use `Bash` to run Y”.

---

## **2.2 Agents – Dynamic Skill Use & Delegation**

### **2.2.1 Purpose: Isolated workers, not more prompts**

* **Subagents** exist to **isolate noisy work** (debugging, research, large refactors) into their **own context window**, then return a summary.

* They solve **context pollution**, not knowledge access. Skills extend the main agent; subagents quarantine work.

Core principle:

**Skills extend. Subagents isolate. CLAUDE.md anchors.**

### **2.2.2 Role-based consolidation, not agent sprawl**

* You do **not** want “one agent per tiny activity”. That just burns tokens.

* Use **3–4 durable roles**, e.g.:

  * **Builder / Architect** – implementation and refactoring.

  * **Critic / Analyst** – tests, debugging, perf/security checks.

  * **Librarian / Curator** – docs, changelogs, repo hygiene.

  * (+ optionally **Security** specialist.)

Each role:

* Has a **tight, explicit description** (“MUST be used before declaring code complete”, etc.).

* Is allowed only the tools it needs.

* Uses Skills as its knowledge layer (e.g., Builder uses `project-navigator`, `v3-api-skill`, `jest-expert`, etc.).

### **2.2.3 Dynamic skill use inside subagents**

* Subagents **do not replace Skills**. They **consume** them.

* Typical pattern: Orchestrator → refactor-agent (subagent) → refactor-agent automatically invokes `v3-api-skill` and `jest-expert-skill` based on task semantics.

Design principles:

* Subagent prompts should **name the key Skills** they are expected to use (“Use the `project-navigator` and `security-policy-skill` when…”) but still rely on automatic invocation via descriptions.

* Subagents handle **messy loops** (test/fix cycles, log spelunking) and then surface a clean outcome.

### **2.2.4 Flight recorders and auditability**

You want to be able to debug the **agent**, not just the code.

* Principle: **Every long-running subagent keeps a local flight recorder log** (markdown) in its working directory.

* Prompt rule: “Maintain `session_log.md` with timestamped Actions / Results / Reasoning; never declare success without a pointer to a log entry.”

This turns autonomous runs into auditable traces you can review, diff, and post-mortem.

---

## **2.3 Claude Code – Hooks, CLAUDE.md & File Layout**

### **2.3.1 Purpose: Harness, not “personality file”**

Claude Code is the **runtime** that wires everything together:

* **CLAUDE.md hierarchy**: always-on context (user → project → module).

* **.claude directory**: skills, agents, hooks, commands, settings.

* **Hooks**: deterministic guard rails and automation.

* **Checkpoints**: safety net.

* **Slash Commands \+ MCP**: integration and scripted workflows.

### **2.3.2 KISS for CLAUDE.md (“project bible”, not a dump)**

Design principles:

* Keep root `CLAUDE.md` **short** (\<100 lines ideally).

* Use it as:

  * **High-level rules & workflows**

  * **Pointers** to docs / Skills / commands (`@docs/...`, “Use skill X for PDFs”).

* Don’t embed code or full docs; that belongs in real files or Skills.

Think of `CLAUDE.md` as:

“How to work in this repo \+ where things live”
 …not “All knowledge about this repo”.

### **2.3.3 Hooks as “immune system”**

Design principles for hooks:

* Hooks are **deterministic** and **not optional** – triggered by the harness, not by the model.

* Use them to enforce:

  * **Security** (PreToolUse – block dangerous Bash).

  * **Quality gates** (PostToolUse – auto-lint/test after writes).

  * **Automation** (Stop – summarize work, ping services, etc.).

They are your **non-negotiable guard rails** around a creative but untrusted agent.

### **2.3.4 File & directory layout as contract**

At a high level, your filesystem is the ABI between you and the agent:

* Skills live in specific paths (`.claude/skills/`, `~/.claude/skills/`).

* Agents live in `.claude/agents/` or `~/.claude/agents/`.

* Hooks & settings in `.claude/settings*.json`.

* CLAUDE.md hierarchy from `$HOME/.claude/` down to the CWD.

If you keep that structure predictable and shallow, you make the system debuggable and portable.

---

# **3\. Practical Implementation**

Now the same three pillars, but granular and concrete.

---

## **3.1 Skills – Concrete Requirements & Examples**

### **3.1.1 Directory & naming conventions**

**Locations**

* **User-global skills** (personal toolbox):

  * `~/.claude/skills/<skill-name>/SKILL.md`

* **Project skills** (shared with team, committed):

  * `<repo>/.claude/skills/<skill-name>/SKILL.md`

**Naming**

* `name` (frontmatter) and folder name should match:

  * Lowercase, kebab-case: `processing-pdfs`, `project-navigator`, `jest-expert-skill`.

* Avoid “cute” names; favor what-they-do: `security-policy-skill` over `cerberus`.

**Recommended structure per skill**

.claude/skills/processing-pdfs/
├── SKILL.md
├── reference/              \# optional, domain docs
│   ├── forms.md
│   └── extraction-tips.md
├── scripts/                \# optional, deterministic helpers
│   ├── validate\_form.py
│   └── extract\_tables.py
└── templates/              \# optional, fill-in-the-blanks
    └── email\_summary.md

Keep it at 0–1 levels deep; no matryoshka doll directories.

### **3.1.2 SKILL.md schema – minimal but strict**

**Frontmatter requirements**

\---
name: processing-pdfs          \# \<= 64 chars, \[a-z0-9-\]
description: \>
  Extracts text and tables from PDF files, fills forms, and merges documents.
  Use when the user mentions PDFs, document extraction, or PDF forms.
allowed-tools: Read, Write, Bash   \# Claude Code only, optional
\---

Rules:

* `description` is **third-person** and must contain:

  * What the skill does.

  * When Claude should use it (trigger phrases).

* `allowed-tools` is only honored in Claude Code; SDK uses its own config.

**Body template**

\# PDF Processing

\#\# Quick start
1\. Use \`Read\` on the specified PDF file(s).
2\. If the goal mentions "forms" or "fill", follow the \*\*Form workflow\*\*.
3\. If the goal mentions "tables" or "data", follow the \*\*Table extraction workflow\*\*.

\#\# Workflows

\#\#\# Form workflow
1\. Read \`reference/forms.md\` for the most recent rules.
2\. Use \`scripts/validate\_form.py\` to pre-validate fields.
3\. Use \`Write\` to update the filled PDF in \`/tmp/pdf-output/\`.
4\. Log key decisions in \`session\_log.md\` if invoked by a subagent.

\#\#\# Table extraction workflow
1\. Use \`scripts/extract\_tables.py\` to get CSV.
2\. Use the \`analyzing-spreadsheets\` skill if complex analysis is needed.

\#\# References
\- \`reference/forms.md\` – detailed field rules.
\- \`reference/extraction-tips.md\` – OCR and edge cases.

Key requirements:

* Max \~500 lines; anything more belongs in `reference/`.

* Explicit tool calls and file paths.

* Never embed implementation code that should live in `src/`.

### **3.1.3 Pointer-pattern example**

**Bad**

To write a Django migration, use this example:

\`\`\`python
class Migration(migrations.Migration):
    ...

\*\*Good\*\*

\`\`\`markdown
\#\# Source of truth

\- Library: \`src/backend/db/migrations/\`
\- Templates: \`src/backend/factories/migration\_factory.py\`
\- Examples: Read the 3 latest files in \`migrations/versions/\`.

\#\# Usage rules

1\. NEVER guess migration syntax.
2\. ALWAYS read \`migration\_factory.py\` before writing a migration.
3\. ALWAYS use \`./scripts/generate\_migration.sh\` instead of editing files directly.

That’s exactly the pointer pattern you already described.

### **3.1.4 High-value baseline skills to standardize**

From your research and the ecosystem:

Baseline for most repos:

* `project-navigator` – primary map \+ “which subagent to hire” matrix.

* `jest-expert-skill` (or equivalent for your stack) – test-writing workflow.

* `vX-api-skill` – internal API or product-specific rules (v3 auth, etc.).

* `security-policy-skill` – how to handle auth, PII, logging, etc.

* File-format skills: `pdf`, `docx`, `xlsx`, `pptx` if you want “office-document delegate” behavior.

---

## **3.2 Agents – Setup, Roles, and Flight Recorders**

### **3.2.1 Directory layout & scope**

**User-scoped agents**

\~/.claude/agents/
├── code-reviewer.md
└── debugger.md

**Project-scoped agents**

.claude/agents/
├── builder.md
├── analyst.md
└── curator.md

Claude Code \+ the Agent SDK both treat these as discoverable agent definitions; the orchestrator can delegate based on their descriptions.

### **3.2.2 Agent definition template**

Example: `./.claude/agents/builder.md`

\---
name: agent-builder
description: \>
  Use PROACTIVELY for any task involving code creation, refactoring,
  or feature implementation. MUST delegate tests and reviews to other agents.
tools:
  \- Read
  \- Write
  \- Edit
  \- Bash
model: sonnet
\---
You are the Lead Implementor for this project.

\#\# Mandate
1\. Implement features as described by the orchestrator.
2\. Refactor legacy code to match modern patterns.
3\. Maintain test integrity: do not knowingly break existing tests.

\#\# Operating rules
\- Follow the Pointer Pattern: read existing code before writing new code.
\- Use the \`project-navigator\` skill to understand structure and find files.
\- For tests, rely on \`jest-expert-skill\` (or equivalent) for detailed steps.
\- When complete, request \`agent-analyst\` to run tests and debugging.

Requirements:

* `description` is clear enough that the orchestrator can auto-match tasks (“implement”, “refactor”).

* Tools are restricted per persona (e.g., reviewer might not get `Bash`).

### **3.2.3 Standard role pack and when to use each**

**1\. agent-builder (Architect/Implementor)**

* Use when: writing or refactoring code, large feature work.

* Tools: Read, Write/Edit, Bash, Grep.

* Skills: project-navigator, framework-specific skills, jest-expert, API skills.

**2\. agent-analyst (Critic/Tester)**

* Use when: running tests, debugging, perf analysis, security checks.

* Tools: heavy Bash, Read, maybe MCP (Sentry, logs).

* Skills: debugging skill, security-policy, performance-guides.

**3\. agent-curator (Librarian/Doc)**

* Use when: docs updates, changelogs, release notes, ticket updates.

* Tools: Read/Write, MCP (Jira/Confluence/GitHub), minimal Bash.

* Skills: documentation style skill, communication templates.

**4\. security-agent (Optional but smart)**

* Use when: code touches auth, persistence, PII, external I/O.

* Tools: Read, limited Bash (static analyzers, security scripts), MCP (security logs).

### **3.2.4 Flight recorder implementation**

Subagent system prompt addition:

\#\# Flight Recorder Protocol

You MUST maintain \`session\_log.md\` in the current working directory.

Rules:
1\. If \`session\_log.md\` does not exist, create it.
2\. After every major action, append an entry:

   \- \[HH:MM\] \*\*Action\*\*: \<what you did\>
   \- \[HH:MM\] \*\*Result\*\*: \<what happened\>
   \- \[HH:MM\] \*\*Reasoning\*\*: \<why you changed course or chose this path\>

3\. When reporting success or failure, reference at least one log entry.

Practical usage:

* For big refactors: the log is your post-mortem and review artifact.

* For failures: you inspect the log to decide whether to adjust Skills, agent prompts, or hooks.

### **3.2.5 Skill vs Subagent – implementation heuristic**

If you’re about to create something, ask:

* **Does this need an isolated context, persona, and possibly long-running loops?**
   → If **yes**, make a **subagent** that consumes Skills.

* **Is this a reusable, tool-driven workflow, where the main agent should stay in context?**
   → If **yes**, make a **Skill**.

Example:

* “Write and debug Jest tests for any component” → Skill.

* “Research 10 external APIs and summarize trade-offs” → Subagent (researcher).

---

## **3.3 Claude Code – Repo Layout, Hooks, and Glue**

### **3.3.1 Canonical project filesystem layout**

Recommended baseline:

.
├── CLAUDE.md
├── .claude/
│   ├── settings.json
│   ├── settings.local.json        \# gitignored
│   ├── skills/
│   │   ├── project-navigator/
│   │   │   └── SKILL.md
│   │   ├── jest-expert-skill/
│   │   │   ├── SKILL.md
│   │   │   ├── reference/
│   │   │   └── examples/
│   │   └── security-policy-skill/
│   │       └── SKILL.md
│   ├── agents/
│   │   ├── builder.md
│   │   ├── analyst.md
│   │   └── curator.md
│   └── commands/
│       ├── git/
│       │   └── smart-commit.md
│       └── run-tests.md
└── src/...

This layout works for:

* Claude Code (CLI, VSCode).

* Agent SDK (point to repo root with `setting_sources=["user","project"]`).

### **3.3.2 CLAUDE.md content shape**

Simple template:

\# Project Overview
\- What this repo does
\- Core tech stack and key directories

\#\# Workflows
\- Implementing a feature
\- Running tests
\- Adding dependencies

\#\# Agent Instructions
\- Always start by using the \`project-navigator\` skill.
\- For tests, use \`jest-expert-skill\`.
\- For any auth/PII change, use \`security-policy-skill\` and \`security-agent\`.

\#\# Dangerous Areas
\- Do NOT modify \`infra/prod/\` without explicit user confirmation.
\- Migrations must go through \`./scripts/generate\_migration.sh\`.

\#\# Where to Learn More
\- @docs/architecture/overview.md
\- @docs/api/v3-auth.mdx

Keep it lean and pointer-heavy; treat it like an index, not an encyclopedia.

### **3.3.3 Hooks: concrete examples**

**Example 1 – PostToolUse lint/test gate**

`.claude/settings.json`:

{
  "hooks": {
    "PostToolUse": {
      "command": "if \[\[ \\"$TOOL\_NAME\\" \== \\"Edit\\" || \\"$TOOL\_NAME\\" \== \\"Write\\" \]\]; then cd \\"$CLAUDE\_PROJECT\_DIR\\" && ./scripts/auto\_lint\_and\_test.sh \\"$FILE\_PATH\\"; fi"
    }
  }
}

* Any `Edit`/`Write` triggers `auto_lint_and_test.sh`.

* The script’s stdout/stderr is fed back into the model automatically.

**Example 2 – PreToolUse Bash allowlist**

{
  "hooks": {
    "PreToolUse": {
      "command": "cd \\"$CLAUDE\_PROJECT\_DIR\\" && ./scripts/bash\_allowlist.sh \\"$TOOL\_NAME\\" \\"$BASH\_COMMAND\\""
    }
  }
}

`scripts/bash_allowlist.sh` rejects anything not in your whitelist (git, ls, cat, jest, etc.). If the script exits non-zero, the tool call is blocked.

### **3.3.4 Slash commands as callable “functions”**

Place commands here:

* Project: `.claude/commands/...` → `/project:...`

* User: `~/.claude/commands/...` → `/user:...`

Example: `.claude/commands/git/smart-commit.md`:

\---
description: Create a git commit message based on staged changes.
\---
\#\# Context

\*\*Current Branch:\*\*
\!\`git branch \--show-current\`

\*\*Git Status:\*\*
\!\`git status \--short\`

\*\*Staged Diff:\*\*
\!\`git diff \--staged\`

\#\# Task
Write a concise, conventional commit message summarizing these changes.

The agent can call this via the **SlashCommand tool** to automate workflows inside larger tasks (“run tests, then smart-commit if green”).

### **3.3.5 MCP & code execution – only when you really need it**

* Use MCP when the agent needs **real-time external data** (Jira, GitHub, Sentry, DBs).

* For data-heavy tasks, prefer the **“code execution with MCP”** pattern:

  * Teach the agent to write small scripts that use an MCP-backed library.

  * Run scripts in a sandbox and feed only the filtered results back into the model.

This keeps tokens down and keeps agents fast and cheap.

---

## **3.4 Putting It All Together – Minimal Autonomous Stack**

If you want a **minimal but serious** setup that follows all of this:

1. **Repo layout**

   * `CLAUDE.md` with workflows \+ pointers.

   * `.claude/settings.json` with PostToolUse lint/test and PreToolUse Bash gate.

   * `.claude/skills/` with:

     * `project-navigator`

     * `jest-expert-skill`

     * `security-policy-skill`

   * `.claude/agents/` with `builder`, `analyst`, `curator` (and optionally `security-agent`).

2. **Skill design**

   * All Skills follow pointer pattern \+ workflow checklists.

   * No embedded “canonical” code; always point to real files.

3. **Subagent design**

   * 3–4 roles, each with:

     * Clear description (what \+ when \+ must-use rules).

     * Narrow toolset.

     * Flight recorder protocol.

     * Explicit references to key Skills.

4. **Claude Code harness**

   * Hooks enforce security and quality gates.

   * Checkpoints left on, always use `/rewind` if things go sideways.

That gives you a coherent, auditable system instead of a pile of ad-hoc prompts.

If you want, next step can be: **turn this into a concrete “starter repo” skeleton** (ready-to-git-init) that your teams can clone and customize.
