

# **Exhaustive Developer Guide: claude-code Agentic Systems**

## **Part 1: The Modern claude-code Environment: v2.0, Sonnet 4.5, and Autonomous Operation**

### **Section 1.1: The New Foundation: v2.0 and Sonnet 4.5**

The claude-code local command-line tool has undergone a significant evolution, culminating in version 2.0. This release is not merely an update but a foundational rewrite, effectively repositioning the tool from a simple interactive assistant to a platform for autonomous agentic development.1

The primary driver of this new capability is the integration of the Sonnet 4.5 model.1 This model represents Anthropic's new standard for agentic coding and complex reasoning, demonstrating superior performance on industry benchmarks, including a 77.2% score on the SWE-bench Verified benchmark.3 The terminal user interface (TUI) has also been refreshed in v2.0, featuring improved status visibility and, most practically, a searchable prompt history accessible via $Ctrl+r$, which streamlines the reuse of complex or repetitive commands.1

However, the most profound change enabled by Sonnet 4.5 is the capacity for long-duration coherence. Reports indicate the model can maintain coherent reasoning and task focus for "30+ hours" on complex tasks.4 This capability is the core enabler for the tool's shift in purpose. Previously, AI coding assistants were largely "pair programmers," effective for short-term, interactive, and human-supervised tasks. The extended coherence of Sonnet 4.5 enables a new paradigm: the "autonomous delegate." This allows a developer to assign complex, multi-day tasks—such as a large-scale refactor or new feature implementation—and trust the agent to manage its own state and reasoning over that extended period. The advanced features detailed in this guide, particularly Subagents, Hooks, and Checkpoints, are the control and safety mechanisms built to harness this new, long-running reasoning capability.

### **Section 1.2: The VS Code Extension: The GUI for the Agentic Engine**

In parallel with the v2.0 TUI, Anthropic has released a native VS Code extension (beta).1 This is a critical development for broadening the tool's accessibility beyond terminal-centric power users. It is important to understand that this extension is not a simple wrapper for the CLI 8 but a distinct, rich graphical interface that provides unique features.7

Key features of the VS Code extension include:

* **Native IDE Experience:** A dedicated sidebar panel for interacting with the agent.7
* **Inline Diffs:** The ability to see Claude's proposed code changes in real-time, directly within the editor, which is a significant workflow improvement over the TUI's diff view.1
* **File Management:** Support for @-mentions to add files to context, as well as a system file picker for attachments.7
* **Plan Mode:** A specialized mode that allows the developer to review, edit, and approve Claude's proposed plan of action before execution begins.7

The VS Code extension and the claude-code CLI exist in a symbiotic relationship. The extension serves as the "command center," but the CLI and its associated file-based configuration (\~/.claude/, .claude/) remain the "engine." The agent running inside the VS Code extension consumes and is empowered by the advanced configurations set up via the CLI.7 Custom Subagents, Model Context Protocol (MCP) server connections, and custom Slash Commands (all configured in the file system) become available to the agent within the VS Code UI.9 Therefore, to fully exploit the capabilities of the VS Code extension, a developer must first master the CLI's configuration file-system, which this guide details.

### **Section 1.3: The Checkpoint System: The Safety Net for Autonomy**

Checkpoints are the final pillar of the new claude-code v2.0 foundation.1 This system is the core safety net that makes autonomous operation viable.

**System Design:** The Checkpoint system operates automatically and transparently. claude-code captures and saves the complete state of the relevant code *before* the AI executes any file-editing tool.1 This creates a high-frequency, local "undo" history that tracks every single AI-initiated modification.13

**Practical Usage:** If an agent's actions are undesired, the developer can instantly revert both the code changes and the conversation state to a previous checkpoint. This is accomplished using the /rewind command in the TUI or, more immediately, the $Esc Esc$ key combination.5 These checkpoints are durable and persist across sessions, meaning a developer can safely resume an operation and still have access to their rewind history.11

The introduction of Checkpoints is causally linked to the promotion of autonomous features like Subagents and Hooks.1 Delegating a complex, long-running refactor to an autonomous subagent 1 or enabling automated post-edit Hooks to run tests 1 is an inherently high-risk activity. The agent could misinterpret the goal, "go off the rails," and introduce breaking changes. Checkpoints effectively remove this risk by providing a no-cost, instant rollback mechanism. This system enables the "fearless experimentation" 13 required to confidently delegate significant tasks, transforming the agent from a tool that *suggests* changes to a delegate that *performs* them.

## **Part 2: Architecting Agentic Memory: From CLAUDE.md to Agent Skills**

### **Section 2.1: The CLAUDE.md Hierarchy: Persistent Project Context**

The CLAUDE.md file is the foundational mechanism for providing claude-code with persistent, project-specific context.14 It is a special Markdown file that the tool automatically locates and ingests into the model's context at the beginning of every session.14

System Design: Cascading Context
The tool's memory system is designed as a cascading hierarchy, reading CLAUDE.md files recursively up the directory tree from the current working directory.15 This allows for a powerful, layered approach to context definition:

1. **User-Level (Global):** $HOME/.claude/CLAUDE.md. This file defines a developer's global preferences across all projects (e.g., "I always use 2-space indentation," "My preferred commit message format is...")..16
2. **Project-Level (Root):** \[project-root\]/CLAUDE.md. This is the project's "bible." It should define the core tech stack, high-level architecture, component structure, testing instructions, and repository etiquette (e.g., branch naming conventions).14
3. **Local-Level (CWD):** \[cwd\]/CLAUDE.md. This provides highly specific context for a particular module or task (e.g., in \[project-root\]/api/v2/CLAUDE.md, one might specify: "This module uses pyenv and connects to the staging database. Do not write integration tests.")..15

Best Practices for CLAUDE.md
The CLAUDE.md file is a powerful tool, but its primary weakness is that it is always in context, consuming a static portion of the available token budget.17

* **Keep it Lean:** The root CLAUDE.md should be minimal, ideally under 100 lines.16 It should contain only the most critical, high-level principles.
* **Use as a "Table of Contents":** Do not paste large code blocks or lengthy documentation into CLAUDE.md. Instead, use it as a "bootstrap" file that *points* Claude to other, more detailed documents using the @ import syntax (e.g., "For API design, review @docs/architecture/api-design.md.").17
* **Define "What," Not Just "How":** Include core files, utility functions, style guidelines, testing instructions, and common bash commands or environment setup.14
* **Manage Session Context:** The CLAUDE.md file provides *session* context, but the *conversation* context also grows. Developers should use the /clear command frequently between distinct tasks to reset the conversational history and prevent context bloat.14 Relying on /compact is often less effective, as it can confuse the model with summarized, out-of-date information.18

### **Section 2.2: Modular Knowledge with Agent Skills**

Agent Skills are a more advanced, dynamic, and token-efficient solution to the context problem that CLAUDE.md attempts to solve.19 Skills are a core feature of the underlying Agent SDK and are fully supported within claude-code.21 They are designed to provide the agent with specialized, just-in-time knowledge.

System Design: Progressive Disclosure
The core principle of Agent Skills is "progressive disclosure".21 Unlike CLAUDE.md, which is loaded entirely at the start, Skills are loaded in multiple, on-demand stages. This design is exceptionally token-efficient.

1. **Step 1 (Metadata Load):** On session start, claude-code scans the skill directories (e.g., .claude/skills/, \~/.claude/skills/).23 It loads *only* the YAML frontmatter (the name and description) of each SKILL.md file found.19 This metadata layer is extremely small, allowing the agent to be "aware" of hundreds of skills with minimal token cost.
2. **Step 2 (Skill Invocation):** When the developer submits a prompt, the agent's reasoning process includes scanning the *descriptions* of all loaded skills.21 If the user's task semantically matches a skill's description (e.g., prompt "generate a commit message" matches the git-commit-helper skill's description: "Generate descriptive commit messages by analyzing git diffs") 24, the AI *automatically* triggers that skill.
3. **Step 3 (Context Load):** Only *after* being triggered does the agent load the full Markdown body of the relevant SKILL.md file into its active context.21
4. **Step 4 (Further Disclosure):** The SKILL.md file itself is designed to be a "table of contents".24 It can guide the agent to read *other* bundled files within the skill's directory (e.g., in /scripts, /references, /assets) *only if* they are needed for the specific task.23

Practical Creation (SKILL.md)
A skill is a directory containing a SKILL.md file and any number of supporting asset files.23
**Example:** \~/.claude/skills/jest-expert/SKILL.md:

YAML

\---
name: jest-expert-skill
description: Use when writing or refactoring Jest tests. Provides guidelines for mocks, spies, and asynchronous assertions.
allowed-tools: \# Can restrict tools
\---
\# Jest Testing Workflow Guide

You are an expert in Jest and React Testing Library. Follow these steps:

1.  \*\*Analyze Component:\*\* \`Read\` the component file to understand its props and side effects.
2.  \*\*Identify Mocks:\*\* Mock all external dependencies (modules, API calls). See \`examples/mock-patterns.md\` for standard patterns.
3.  \*\*Write Assertions:\*\* Follow the philosophy in \`reference/testing-philosophy.md\`. Ensure all user-visible behavior is tested.
4.  \*\*Run Tests:\*\* Use the \`Bash\` tool to run \`jest\` on the new test file and debug any failures.

This skill directory would also contain:

* \~/.claude/skills/jest-expert/examples/mock-patterns.md
* \~/.claude/skills/jest-expert/reference/testing-philosophy.md

The @docs/file.md import pattern used in CLAUDE.md 17 is a *manual* form of progressive disclosure; the *user* must remember to reference it or the AI must happen to read it. Agent Skills provide an *automatic, AI-driven* invocation mechanism.19 The agent "remembers" to use the right knowledge at the right time, based on the task. This is a far more scalable and truly "agentic" pattern for knowledge management.

## **Part 3: System Extensibility I: Custom Slash Commands**

### **Section 3.1: File-Based Command Creation**

Custom Slash Commands are the simplest way to create user-driven automation. They are essentially reusable prompt templates stored as Markdown (.md) files that a developer can invoke manually.26

This system uses the same cascading file hierarchy as other configurations:

* **Project Commands:** Stored in .claude/commands/. A file named test.md is invoked as /project:test. These are shared with the team via the repository.27
* **User Commands (Global):** Stored in \~/.claude/commands/. A file named review.md is invoked as /user:review. These are personal to the developer across all projects.27

**Namespacing:** The system supports namespacing through subdirectories. A file at .claude/commands/git/commit.md is invoked as /project:git:commit.27

### **Section 3.2: Injecting Dynamic Context**

The power of Slash Commands comes from their ability to inject dynamic context into the prompt template.

* **Arguments:** The template can capture user input from the command line. $ARGUMENTS captures all text after the command, while $1, $2, etc., capture positional arguments.26
  * **Example:** A file at .claude/commands/fix-issue.md containing Review and fix the bug described in GitHub issue \#$ARGUMENTS..26
  * **Invocation:** /project:fix-issue 123
  * **Resulting Prompt:** "Review and fix the bug described in GitHub issue \#123."
* **Shell Pre-Execution:** This is the most powerful feature of Slash Commands. Any line in the .md file prefixed with an exclamation mark (\!) will be executed as a shell command *before* the prompt is sent to the model. The stdout of the command is then injected directly into the prompt context.28

Practical Example: .claude/commands/smart-commit.md
This command creates a "smart" commit prompt that automatically includes all staged changes.

YAML

\---
description: Create a git commit message based on staged changes.
allowed-tools:
\---
\#\# Context

\-   \*\*Current Branch:\*\*
   \!\`git branch \--show-current\`

\-   \*\*Current Git Status:\*\*
   \!\`git status \--short\`

\-   \*\*Staged Changes (Diff):\*\*
   \!\`git diff \--staged\`

\#\# Your Task

Based on the context above, write a concise, conventional git commit
message for the staged changes.

When the user types /project:smart-commit, the claude-code tool first executes the three git commands and injects their output into the prompt, giving the AI perfect, real-time context to complete the task.

### **Section 3.3: The SlashCommand Tool: AI-Driven Invocation**

A recent update fundamentally changed the role of Slash Commands by introducing the SlashCommand tool.29

Previously, Slash Commands were exclusively *user-driven* tools—simple aliases or shortcuts that a human had to remember to type.26 The SlashCommand tool now allows the *AI agent* to invoke Slash Commands as part of its own autonomous reasoning process.

This change elevates commands from "shortcuts" to "functions." A developer can now create a suite of custom commands (like /project:smart-commit, /project:run-tests, /project:deploy-staging) and the AI can orchestrate them. A developer can give a high-level prompt like, "Review my changes, test them, and commit them." The agent can now reason: "To accomplish this, I will first use the SlashCommand tool to run /project:run-tests. If it succeeds, I will use the SlashCommand tool to invoke /project:smart-commit." This transforms manual shortcuts into a library of AI-callable functions, enabling far more complex, multi-step autonomous workflows.

## **Part 4: System Extensibility II: Designing Multi-Agent Systems with Subagents**

### **Section 4.1: Subagent Architecture: The "Isolated Context" Model**

Subagents are the key to scaling complex, multi-faceted tasks and are a core component of the claude-code agentic system.1 A subagent is a specialized, subordinate AI assistant that an orchestrator (the main claude-code agent) can delegate specific tasks to.

The architecture of subagents is defined by three key differentiators:

1. **Isolated Context:** This is the most critical concept. When a main agent delegates a task to a subagent, that subagent "spins up" with its *own, separate context window*.30 It does *not* see the main conversation history. This is a powerful mechanism for "context preservation".32 The subagent's internal reasoning, tool calls, and failures do not pollute the main agent's context window. The main agent only receives the final, summary result.34
2. **Specialization:** Each subagent is defined by its own system prompt and a potentially restricted set of tools.32 This allows for the creation of a team of domain experts (e.g., a "code-reviewer" agent, a "debugger" agent, a "security-analyst" agent).
3. **Parallelization:** The orchestrator agent can invoke multiple subagents to work on different tasks simultaneously.1 For example, the orchestrator could delegate a frontend task to a "react-subagent" and a backend task to a "django-subagent" in parallel.1

### **Section 4.2: Creating and Managing Subagents**

Developers have two primary methods for creating and managing subagents:

* **Interactive Creation:** The recommended method is to use the built-in TUI. Running the /agents command inside claude-code opens a comprehensive interface to "Create New Agent," as well as view, edit, and delete existing custom agents.32
* **File-Based Definition:** Ultimately, subagents are defined as .md files in either .claude/agents/ (for project-specific agents) or \~/.claude/agents/ (for user-level agents available in all projects).31

File Format Example: .claude/agents/reviewer.md
The subagent definition file uses a YAML frontmatter block followed by a Markdown system prompt.32

YAML

\---
name: code-reviewer
description: Use PROACTIVELY to review code for quality, bugs, and style guide adherence. MUST BE USED before any code is considered "complete".
tools: \# Restricted tool access
model: sonnet \# Can specify a different model
\---
You are an expert code reviewer. Your sole purpose is to analyze code
diffs or files provided to you. Cross-reference the code against
the project's \`CLAUDE.md\` style guide.

If tests are missing, identify exactly what test cases are needed.
If you find style issues, provide the exact corrected code.

Return your review in a structured Markdown list.

### **Section 4.3: Invocation, Delegation, and Cost**

**Invocation:** Subagent invocation is typically *automatic*.31 The main orchestrator agent, when planning its response to a user's prompt, will compare the prompt's intent against the description field of all available subagents. If a match is found, the main agent will use the built-in Task tool to delegate that portion of the work.37

The description field is therefore the single most critical configuration element of a subagent. It is not a description *for* the human user; it is an "API" for the orchestrator AI.

* **Bad Description:** "Helps with code." (Vague, will never be triggered).
* **Good Description:** "Use PROACTIVELY when code changes might impact performance. MUST BE USED for optimization tasks.".31 (Specific, actionable, provides clear invocation criteria for the AI).

**Cost Trade-off:** Subagents are *not* a tool for simple, everyday tasks. Because they must "spin up" an entirely new context, they consume *more* tokens for simple jobs (e.g., creating a git commit) than the main agent would.34

The value of subagents lies in isolating large, "noisy" tasks.34 A task like "Research these 10 API documentation websites and summarize them" might generate 50,000 tokens of intermediate context (page loads, analysis, etc.). By delegating this to a subagent, those 50,000 tokens are kept within the subagent's isolated context.30 The subagent then completes its work, its context is discarded, and it returns only a 500-token summary to the main agent. This preserves the main agent's context window for high-level planning and orchestration.

## **Part 5: Comparative Analysis: Choosing the Right Tool for the Job**

### **Section 5.1: The Context & Extensibility Decision Framework**

A common point of confusion for new claude-code power users is the overlap between the various extensibility systems.20

* When should information go in CLAUDE.md?
* When is a Slash Command better than an Agent Skill?
* What is the real difference between a Skill and a Subagent?

These tools are not interchangeable; they are designed to solve distinct problems related to context, automation, and delegation. The following framework clarifies the architectural purpose of each.

### **Section 5.2: Essential Table 1: Context and Extensibility Feature Comparison**

The decision of which tool to use should be based on four factors: the tool's purpose, its context model, its invocation method, and its token efficiency.

| Feature | Primary Purpose | Context Model | Invocation | Token Efficiency |
| :---- | :---- | :---- | :---- | :---- |
| **CLAUDE.md** 15 | **Persistent Memory** (Project "Bible") | Persistent & Shared (Loaded on Start) | Automatic (On Session Start) | **Low** (Always in context, must be kept lean) |
| **Slash Command** 26 | **Manual Shortcut** (Prompt Alias) | Ephemeral & Injected (Prompt text) | Manual by User (e.g., /my-cmd)*or* AI via SlashCommand tool 29 | **High** (Only the injected prompt text is used) |
| **Agent Skill** 21 | **Autonomous Knowledge** (Reusable Workflow) | Progressive & Shared (Loaded into main context on-demand) | Automatic by AI (Task matches description) 19 | **Very High** (Only metadata is loaded until triggered) |
| **Subagent** 30 | **Autonomous Delegation** (Specialist Worker) | Isolated & Ephemeral (Separate context window) | Automatic by AI (Task matches description) 31 | **Varies** (High initial cost, but protects main context) 34 |

## **Part 6: Automating the Agent Loop: A Developer's Guide to Hooks**

### **Section 6.1: Hook System Design: Deterministic Control**

Hooks are a powerful system for developers to insert deterministic logic into the agent's lifecycle. They are callback functions that execute at specific, predefined events.41

The most critical concept to understand is that Hooks are *not* invoked by the AI. They are invoked by the claude-code *application harness* (the CLI tool itself).42 The AI's reasoning is non-deterministic and creative; Hooks are deterministic and absolute. This means the AI *cannot* decide to "skip" a Hook.

This design makes Hooks the "immune system" of the agent. They are the primary, non-bypassable mechanism for enforcing security rules, quality gates, and policy compliance on the AI's actions.

**Configuration:** Hooks are defined in a settings.json file, which can be located at the user-level (\~/.claude/settings.json) or project-level (.claude/settings.json).44

**Hook Types:**

1. **"command":** Executes a bash command or script.44 This is the most common type. The $CLAUDE\_PROJECT\_DIR environment variable is available to reference scripts within the project.44
2. **"prompt":** Sends a prompt to an LLM for evaluation.44 This is less common and is used for complex, "soft" policy decisions (e.g., sending a PreToolUse command to an LLM to ask, "Is this Bash command dangerous?").

### **Section 6.2: The Hook Lifecycle and Practical Use Cases**

The Hook system is event-driven. A developer defines which events to "listen" for and what action to take. The following table details the most important events in the claude-code lifecycle.

### **Section 6.3: Essential Table 2: Hook Event Lifecycle Reference**

| Hook Event | When It Fires | Key Matchers | Practical Use Case & Example |
| :---- | :---- | :---- | :---- |
| **SessionStart** 41 | When a new session begins or resumes. | N/A | **Environment Setup:** "Warm up" the context. Run a script to pull the latest git changes or list open Jira tickets assigned to the user.45 |
| **UserPromptSubmit** 41 | When the user submits a prompt, *before* Claude processes it. | N/A | **Prompt Validation/Injection:** Block prompts containing sensitive keywords. Automatically inject the current date, time, or git branch into the user's prompt.44 |
| **PreToolUse** 41 | *Before* any tool (e.g., Bash, Edit) executes. | Bash, Edit, Write, Grep, etc. | **Security Gate:** The most important hook. Block dangerous operations. A script that checks the command and exit 1 will *prevent* the tool from running.42 |
| **PostToolUse** 41 | *After* a tool call completes. | Write|Edit 44, Bash | **Automatic Linting / CI:** The key to a local CI loop. After any Write or Edit 44, trigger a hook to run a linter (e.g., check-style.sh). The lint errors are automatically fed back to Claude as the next input.1 |
| **Notification** 41 | When claude-code sends a notification. | permission\_prompt, idle\_prompt 44 | **System Alerts:** Trigger desktop or audio notifications. A script for idle\_prompt could run /path/to/idle-notification.sh to get the user's attention.44 |
| **Stop / SubagentStop** 41 | When the main agent or a subagent finishes responding. | N/A | **Finalization / Automation:** Create a summary of work done. Automatically push changes to a development branch for review.45 |

## **Part 7: Connecting to the World: The Model Context Protocol (MCP)**

### **Section 7.1: Core Concepts and Terminology**

A common query refers to "MCP" as "Master Control Program," which is a reference to science fiction.47 In the Anthropic ecosystem, **MCP** stands for the **Model Context Protocol**.49

MCP is an open-source standard (like HTTP or USB) designed to be the "USB-C port for AI".50 It is a client-server protocol that provides a secure, standardized way for AI applications (like claude-code) to connect to and interact with external tools, databases, and data sources.49

The claude-code agent, by default, has access to the local file system (via Read, Write) and the shell (via Bash).30 This gives it comprehensive access to the *local* codebase. However, it has no access to *private, real-time, external* data. It cannot see the status of "JIRA issue ENG-4521" 53, read a private Confluence document, or check for new alerts in Sentry. MCP is the secure, authenticated bridge that provides this access, effectively giving the agent "senses" in the outside world.55

### **Section 7.2: Connecting and Managing Servers in claude-code**

In this architecture, claude-code acts as an MCP *client*.56 The developer's responsibility is to connect it to various MCP *servers*.

**Adding Servers:** Servers are added via a one-time CLI command. The transport method (http, sse, stdio) is important and specified by the server provider.53

* **Example:** claude mcp add \--transport http sentry https://mcp.sentry.dev/mcp.53

**Authentication (OAuth 2.0):** Most useful MCP servers are not public; they require authentication to access private data (e.g., your team's Jira board). claude-code handles this via a secure OAuth 2.0 flow.53

1. **Add the Server:** Add the server via the CLI (e.g., claude mcp add \--transport sse atlassian https://mcp.atlassian.com/v1/sse).53
2. **Enter the TUI:** Run claude to enter the interactive TUI.
3. **Run /mcp:** Inside the TUI, run the /mcp command. This opens an "authentication manager".53
4. **Authenticate:** Select the server (e.g., "atlassian") and choose "Authenticate."
5. **Browser Flow:** claude-code will provide a URL to open in a browser. The user logs into the external service (e.g., Atlassian) and grants access. The service then redirects back, and claude-code securely stores the resulting authentication token for future use.53

This flow ensures that claude-code can securely and automatically access private data on the user's behalf. Developers should, however, use third-party MCP servers at their own risk and vet their security practices.53

### **Section 7.3: Essential Table 3: Popular MCP Server Integrations**

The true value of MCP is realized when connecting to developer-centric tools. The following table provides the commands and common use cases for the most popular MCP servers.

| Service | claude mcp add Command | Practical Use Cases |
| :---- | :---- | :---- |
| **Atlassian (Jira, Confluence)** | claude mcp add \--transport sse atlassian https://mcp.atlassian.com/v1/sse 53 | "Implement the feature described in JIRA issue ENG-4521." 53 "Summarize the Confluence doc for this epic." 54 |
| **GitHub** | claude mcp add \--transport http github https://api.githubcopilot.com/mcp/ 53 | "Review PR \#456 and suggest improvements." 53 "Create a new issue for the bug we just found." 53 "Show me all open PRs assigned to me." 53 |
| **Sentry** | claude mcp add \--transport http sentry https://mcp.sentry.dev/mcp 53 | "Check Sentry and Statsig to check the usage of the feature in ENG-4521." 53 "Analyze this stack trace from Sentry." |
| **PostgreSQL** | claude mcp add... (via local server) 49 | "Find emails of 10 random users who used feature X, based on our Postgres database." 53 |
| **Google Drive / Slack** | (via official servers) 49 | "Update our standard email template based on the new Figma designs that were posted in Slack." 53 "Read the design doc in Google Drive." 58 |

## **Part 8: Advanced Design Patterns for Autonomous Operation**

### **Section 8.1: The Autonomous Workflow Stack**

True autonomous operation is not the result of a single feature, but the *interlocking* of the entire claude-code agentic stack.1 Each component detailed in this guide plays a specific role.

Consider a complex developer task: "Refactor our legacy authentication module to use the new v3 API, and update all tests."

An autonomous agent would execute this using the full stack:

1. **The Task:** The developer gives the high-level prompt.
2. **The Delegate (Subagent):** The main agent's "Orchestrator" persona recognizes this as a complex task and delegates it to a specialized **Subagent** (e.g., refactor-agent) to keep the main context clean.1
3. **The Knowledge (Agent Skill):** The refactor-agent's system prompt matches the task to an **Agent Skill** (e.g., v3-api-skill). This skill loads the v3 API's rules, patterns, and examples into the subagent's context.21
4. **The Action (Tool):** The subagent uses the Grep, Read, and Edit tools to find and refactor the code.
5. **The Quality Gate (Hook):** A project-level PostToolUse **Hook** is configured to trigger on every Edit event.44 This hook automatically runs the linter and the Jest test suite (check-style.sh && jest).1
6. **The Feedback Loop (Harness):** The linter errors and test failures are piped back into the subagent's context as its next input. The subagent, still guided by its SKILL.md instructions, attempts to fix them, creating a tight "code \-\> test \-\> fix" loop.
7. **The Safety Net (Checkpoint):** The **Checkpoint** system has been automatically saving the code state *before every single edit*.11 When the developer returns, they can review the work. If the agent's entire approach was flawed, a single /rewind 5 reverts the entire operation.

### **Section 8.2: Headless Mode for CI/CD and Automation**

claude-code is not just an interactive tool; it is a fully scriptable agent that adheres to the Unix philosophy.58 By using the \-p (prompt) flag, the tool can be run in a non-interactive "headless" mode, making it a powerful component for automated pipelines.14

**Practical Examples:**

* Git Pre-commit Hook: In .git/hooks/pre-commit, a script can run:
  claude \-p "Fix any lint issues in the staged files and re-stage them.".14
* CI/CD Pipeline Step: As part of a build script:
  claude \-p "If there are new user-facing text strings in this diff, translate them into French, create a new file \\fr.json\`, and raise a PR for @lang-fr-team to review."\`.58
* Live Log Monitoring: By piping stdout into the agent:
  tail \-f app.log | claude \-p "Watch this log stream. If you see an anomaly or a fatal error pattern, use the Slack tool to notify the on-call channel.".58

### **Section 8.3: The "Code Execution with MCP" Pattern**

This is one of the most advanced patterns for claude-code power users, designed to solve the problem of "tool definition bloat" and context window limits.59

**The Problem:** When an agent connects to dozens of MCP servers, the definitions for all their available tools (numbering in the hundreds or thousands) can consume a massive amount of the context window.59 Furthermore, a single tool call (e.g., "get all Jira issues") might return a massive JSON blob that overflows the context or incurs high token costs.59

**The Solution:** Instead of giving the AI *direct tool calls*, the developer presents the MCP servers as *code APIs* within a secure code execution environment.59

**Workflow:**

1. A secure code execution environment (e.g., a sandboxed Python or TypeScript runtime) is provided to the agent.59
2. The developer provides an Agent Skill that acts as API documentation, teaching the AI how to use a custom library (e.g., import { jira, sentry } from 'mcp-apis').
3. The AI is prompted to *write code* to accomplish its task, rather than call a tool.
   * **Bad (Tool Call):** Jira.get\_issues(project='ENG') \-\> Returns 10,000 issues (1MB JSON).
   * **Good (Code Execution):** The AI writes a script:
     TypeScript
     import { jira } from 'mcp-apis';
     let issues \= await jira.getIssues('ENG');
     let filtered \= issues.filter(t \=\> t.open && t.priority \== 'High');
     console.log(filtered.map(t \=\> ({ id: t.id, title: t.title })));
     \`\`\`

4. This code runs in the secure sandbox. The AI can use loops, filters, conditionals, and complex logic *in code*.59
5. Only the *final, small, filtered result* (the stdout of the script) is passed back to the model.

This pattern moves the work of "data processing" from the *LLM* (expensive, slow, token-limited) to the *code execution environment* (cheap, fast, unlimited). This approach has been reported to reduce token usage by over 98% in data-heavy agentic tasks.60

## **Part 9: Security, Safety, and Operational Best Practices**

### **Section 9.1: The Central Risk: claude-code as a Dual-Use Tool**

The features detailed in this guide—autonomous agents, shell access, external data connections, and automated execution—are exceptionally powerful. It is a professional and ethical necessity to acknowledge that these capabilities make claude-code a powerful dual-use tool, one that has been "manipulated" by malicious threat actors.61

Case Study: The 2025 AI-Orchestrated Espionage Campaign
In late 2025, Anthropic disclosed a "highly sophisticated espionage campaign" perpetrated by a group assessed with high confidence to be a Chinese state-sponsored actor.61

* **Vector:** The attackers "manipulated" claude-code, using it as the "central nervous system" for an attack that was "80-90%" autonomous.62
* **Mechanism:** The attackers used the exact features detailed in this guide. They configured claude-code to act as an "autonomous penetration testing orchestrator," using **Subagents** to manage tactical operations and **MCP** tools for command-and-control and data exfiltration.62
* **Impact:** This AI-led attack achieved an "impossible" speed, making thousands of requests per second.61

Other documented misuse includes "vibe hacking" for large-scale data extortion and using the agent's reasoning to develop functional malware.66

This is not a hypothetical risk; it is a *documented failure state* of this exact tool. This means that "security" is not an optional add-on; it is the *central challenge* of agentic development. Mastering the features in this guide requires mastering their safe handling.

### **Section 9.2: Defensive Design: A Principal's Best Practices**

A developer using claude-code must adopt a "zero-trust" posture toward the agent's actions. The following practices are essential.

1. **Master the Bash Tool:** The Bash tool 30 gives the AI sovereign control over the local machine. It is the primary attack vector. The *number one priority* must be to lock it down.
   * **Action:** Implement a PreToolUse Hook 42 for the Bash tool. This hook should execute a script that parses the proposed command and compares it against a strict allow-list of safe commands (e.g., git, ls, cat, jest, npm). Deny *everything else* by having the script exit 1\.
2. **Never Use \--dangerously-skip-permissions Globally:** The default permission prompt 67 is the critical "Human-in-the-Loop" (HITL) safety. The \--dangerously-skip-permissions flag 67 is what enables true autonomy, but it is also what an attacker *needs* to achieve scale.62
   * **Action:** This flag should *only* be used for specific, trusted, headless scripts (e.g., a CI/CD task 14) and *only* when that script's environment is hardened with an iron-clad PreToolUse Hook (see \#1).
3. **Vet Your MCP Servers:** An MCP server gives an external entity tool-call access to your agent.53 A malicious MCP server could escalate privileges or exfiltrate data.
   * **Action:** "Use third party MCP servers at your own risk".53 Vet their security, understand their authentication model 53, and ensure they are from a trusted source.
4. **Embed Policy via Subagents and Skills:** Use the agentic architecture for self-policing.
   * **Action:** Create a security-reviewer **Subagent** 32 with a system prompt that *forces* it to check for common vulnerabilities (XSS, SQLi, etc.). Create an **Agent Skill** 21 for your security policies and give it a description like: "MUST BE USED when writing any code that touches authentication or user input."
5. **Trust, But Verify with Checkpoints:** The AI *will* make mistakes, misunderstand, and "hallucinate".61
   * **Action:** Do not delegate and walk away. Trust the autonomous workflow 1 to *run*, but always verify its *output*. Use the **Checkpoint** system 11 as your primary mechanism to review and, if necessary, rewind 5 the AI's work.

#### **Works cited**

1. Enabling Claude Code to work more autonomously \- Anthropic, accessed November 16, 2025, [https://www.anthropic.com/news/enabling-claude-code-to-work-more-autonomously](https://www.anthropic.com/news/enabling-claude-code-to-work-more-autonomously)
2. Claude 3.7 Sonnet and Claude Code \- Anthropic, accessed November 16, 2025, [https://www.anthropic.com/news/claude-3-7-sonnet](https://www.anthropic.com/news/claude-3-7-sonnet)
3. Claude Sonnet 4.5 \- Anthropic, accessed November 16, 2025, [https://www.anthropic.com/claude/sonnet](https://www.anthropic.com/claude/sonnet)
4. Claude Coded: Sonnet 4.5, Claude Code 2.0, and more., accessed November 16, 2025, [https://www.youtube.com/watch?v=Yct0MvNtdfU](https://www.youtube.com/watch?v=Yct0MvNtdfU)
5. Complete Review & Guide to Claude Code 2.0 \- Skywork.ai, accessed November 16, 2025, [https://skywork.ai/blog/review-guide-claude-code-2-0/](https://skywork.ai/blog/review-guide-claude-code-2-0/)
6. Introducing Claude Sonnet 4.5 \- Anthropic, accessed November 16, 2025, [https://www.anthropic.com/news/claude-sonnet-4-5](https://www.anthropic.com/news/claude-sonnet-4-5)
7. Visual Studio Code \- Claude Code Docs, accessed November 16, 2025, [https://code.claude.com/docs/en/vs-code](https://code.claude.com/docs/en/vs-code)
8. Claude Code \- CLI vs VS Code extension?, accessed November 16, 2025, [https://www.reddit.com/r/Anthropic/comments/1ohtjci/claude\_code\_cli\_vs\_vs\_code\_extension/](https://www.reddit.com/r/Anthropic/comments/1ohtjci/claude_code_cli_vs_vs_code_extension/)
9. Claude Code for VS Code \- Visual Studio Marketplace, accessed November 16, 2025, [https://marketplace.visualstudio.com/items?itemName=anthropic.claude-code](https://marketplace.visualstudio.com/items?itemName=anthropic.claude-code)
10. Claude Code V2.0 \- We got Check Points :O : r/ClaudeAI \- Reddit, accessed November 16, 2025, [https://www.reddit.com/r/ClaudeAI/comments/1ntnwbq/claude\_code\_v20\_we\_got\_check\_points\_o/](https://www.reddit.com/r/ClaudeAI/comments/1ntnwbq/claude_code_v20_we_got_check_points_o/)
11. Checkpointing \- Claude Code Docs, accessed November 16, 2025, [https://code.claude.com/docs/en/checkpointing](https://code.claude.com/docs/en/checkpointing)
12. \[Demo\] New Claude Code Interface : r/ClaudeAI \- Reddit, accessed November 16, 2025, [https://www.reddit.com/r/ClaudeAI/comments/1ntnxut/demo\_new\_claude\_code\_interface/](https://www.reddit.com/r/ClaudeAI/comments/1ntnxut/demo_new_claude_code_interface/)
13. Claude Code Checkpoints: A Developer's Guide to Fearless AI Coding \- Skywork.ai, accessed November 16, 2025, [https://skywork.ai/skypage/en/claude-code-checkpoints-ai-coding/1976917740735229952](https://skywork.ai/skypage/en/claude-code-checkpoints-ai-coding/1976917740735229952)
14. Claude Code: Best practices for agentic coding \- Anthropic, accessed November 16, 2025, [https://www.anthropic.com/engineering/claude-code-best-practices](https://www.anthropic.com/engineering/claude-code-best-practices)
15. Manage Claude's memory \- Claude Code Docs, accessed November 16, 2025, [https://code.claude.com/docs/en/memory](https://code.claude.com/docs/en/memory)
16. Claude Code Best Practices: Memory Management \- Code Centre, accessed November 16, 2025, [https://cuong.io/blog/2025/06/15-claude-code-best-practices-memory-management](https://cuong.io/blog/2025/06/15-claude-code-best-practices-memory-management)
17. Claude Code's Memory: Working with AI in Large Codebases \- Medium, accessed November 16, 2025, [https://medium.com/@tl\_99311/claude-codes-memory-working-with-ai-in-large-codebases-a948f66c2d7e](https://medium.com/@tl_99311/claude-codes-memory-working-with-ai-in-large-codebases-a948f66c2d7e)
18. Claude Code Best Practices \- Use Claude to Its Full Potential \- Shuttle.dev, accessed November 16, 2025, [https://www.shuttle.dev/blog/2025/10/16/claude-code-best-practices](https://www.shuttle.dev/blog/2025/10/16/claude-code-best-practices)
19. Difference between Skills and these: Subagents, Claude.MD and slash commands? \- Reddit, accessed November 16, 2025, [https://www.reddit.com/r/ClaudeCode/comments/1o8t6xe/difference\_between\_skills\_and\_these\_subagents/](https://www.reddit.com/r/ClaudeCode/comments/1o8t6xe/difference_between_skills_and_these_subagents/)
20. Claude Code is awesome but memory handling still confuses me. : r/ClaudeAI \- Reddit, accessed November 16, 2025, [https://www.reddit.com/r/ClaudeAI/comments/1lcjgtc/claude\_code\_is\_awesome\_but\_memory\_handling\_still/](https://www.reddit.com/r/ClaudeAI/comments/1lcjgtc/claude_code_is_awesome_but_memory_handling_still/)
21. Equipping agents for the real world with Agent Skills \- Anthropic, accessed November 16, 2025, [https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
22. Introducing Agent Skills \- Claude, accessed November 16, 2025, [https://www.claude.com/blog/skills](https://www.claude.com/blog/skills)
23. Claude Agent Skills: A First Principles Deep Dive \- Han Lee, accessed November 16, 2025, [https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)
24. Skill authoring best practices \- Claude Docs, accessed November 16, 2025, [https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices)
25. Agent Skills \- Claude Code Docs, accessed November 16, 2025, [https://code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills)
26. Your complete guide to slash commands Claude Code \- eesel AI, accessed November 16, 2025, [https://www.eesel.ai/blog/slash-commands-claude-code](https://www.eesel.ai/blog/slash-commands-claude-code)
27. How to Add Custom Slash Commands in Claude Code \- AI Engineer Guide, accessed November 16, 2025, [https://aiengineerguide.com/blog/claude-code-custom-command/](https://aiengineerguide.com/blog/claude-code-custom-command/)
28. Slash commands \- Claude Code Docs, accessed November 16, 2025, [https://code.claude.com/docs/en/slash-commands](https://code.claude.com/docs/en/slash-commands)
29. Claude Code can invoke your custom slash commands : r/ClaudeAI \- Reddit, accessed November 16, 2025, [https://www.reddit.com/r/ClaudeAI/comments/1noyvmq/claude\_code\_can\_invoke\_your\_custom\_slash\_commands/](https://www.reddit.com/r/ClaudeAI/comments/1noyvmq/claude_code_can_invoke_your_custom_slash_commands/)
30. Building agents with the Claude Agent SDK \- Anthropic, accessed November 16, 2025, [https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
31. Subagents in the SDK \- Claude Docs, accessed November 16, 2025, [https://docs.claude.com/en/api/agent-sdk/subagents](https://docs.claude.com/en/api/agent-sdk/subagents)
32. Subagents \- Claude Code Docs, accessed November 16, 2025, [https://code.claude.com/docs/en/sub-agents](https://code.claude.com/docs/en/sub-agents)
33. Claude Skills vs Subagent: What's the difference? \- eesel AI, accessed November 16, 2025, [https://www.eesel.ai/blog/skills-vs-subagent](https://www.eesel.ai/blog/skills-vs-subagent)
34. Subagents and context : r/ClaudeCode \- Reddit, accessed November 16, 2025, [https://www.reddit.com/r/ClaudeCode/comments/1mqydjn/subagents\_and\_context/](https://www.reddit.com/r/ClaudeCode/comments/1mqydjn/subagents_and_context/)
35. accessed November 16, 2025, [https://medium.com/@ooi\_yee\_fei/building-with-claude-code-subagents-my-beloved-minions-b5a9a4318ba5](https://medium.com/@ooi_yee_fei/building-with-claude-code-subagents-my-beloved-minions-b5a9a4318ba5)
36. disler/claude-code-hooks-mastery \- GitHub, accessed November 16, 2025, [https://github.com/disler/claude-code-hooks-mastery](https://github.com/disler/claude-code-hooks-mastery)
37. Agent design lessons from Claude Code | Jannes' Blog, accessed November 16, 2025, [https://jannesklaas.github.io/ai/2025/07/20/claude-code-agent-design.html](https://jannesklaas.github.io/ai/2025/07/20/claude-code-agent-design.html)
38. use command /agents in claude code : r/ClaudeAI \- Reddit, accessed November 16, 2025, [https://www.reddit.com/r/ClaudeAI/comments/1m8qmxw/use\_command\_agents\_in\_claude\_code/](https://www.reddit.com/r/ClaudeAI/comments/1m8qmxw/use_command_agents_in_claude_code/)
39. When should I use a Skill, a Slash Command, or a Sub-Agent in Claude?, accessed November 16, 2025, [https://www.reddit.com/r/ClaudeAI/comments/1orozs4/when\_should\_i\_use\_a\_skill\_a\_slash\_command\_or\_a/](https://www.reddit.com/r/ClaudeAI/comments/1orozs4/when_should_i_use_a_skill_a_slash_command_or_a/)
40. Claude Skills: Glimpse of Continual Learning?, accessed November 16, 2025, [https://www.youtube.com/watch?v=FOqbS\_llAms](https://www.youtube.com/watch?v=FOqbS_llAms)
41. Get started with Claude Code hooks, accessed November 16, 2025, [https://code.claude.com/docs/en/hooks-guide](https://code.claude.com/docs/en/hooks-guide)
42. Claude Code Hooks Guide — claude\_agent\_sdk v0.6.0 \- Hexdocs, accessed November 16, 2025, [https://hexdocs.pm/claude\_agent\_sdk/hooks\_guide.html](https://hexdocs.pm/claude_agent_sdk/hooks_guide.html)
43. anthropics/claude-agent-sdk-python \- GitHub, accessed November 16, 2025, [https://github.com/anthropics/claude-agent-sdk-python](https://github.com/anthropics/claude-agent-sdk-python)
44. Hooks reference \- Claude Code Docs, accessed November 16, 2025, [https://code.claude.com/docs/en/hooks](https://code.claude.com/docs/en/hooks)
45. A complete guide to hooks in Claude Code: Automating your development workflow, accessed November 16, 2025, [https://www.eesel.ai/blog/hooks-in-claude-code](https://www.eesel.ai/blog/hooks-in-claude-code)
46. How Claude Code Hooks Save Me HOURS Daily \- YouTube, accessed November 16, 2025, [https://www.youtube.com/watch?v=Q4gsvJvRjCU](https://www.youtube.com/watch?v=Q4gsvJvRjCU)
47. AI Agents Using MCP \= Your “Guy in the Chair” | by James Buckhouse | Medium, accessed November 16, 2025, [https://buckhouse.medium.com/ai-agents-using-mcp-your-guy-in-the-chair-f32ac850c60e](https://buckhouse.medium.com/ai-agents-using-mcp-your-guy-in-the-chair-f32ac850c60e)
48. Anthropic is releasing MCP, a framework that allows Claude to run servers \- Reddit, accessed November 16, 2025, [https://www.reddit.com/r/singularity/comments/1gzxg9r/anthropic\_is\_releasing\_mcp\_a\_framework\_that/](https://www.reddit.com/r/singularity/comments/1gzxg9r/anthropic_is_releasing_mcp_a_framework_that/)
49. Introducing the Model Context Protocol \- Anthropic, accessed November 16, 2025, [https://www.anthropic.com/news/model-context-protocol](https://www.anthropic.com/news/model-context-protocol)
50. What is the Model Context Protocol (MCP)? \- Model Context Protocol, accessed November 16, 2025, [https://modelcontextprotocol.io/](https://modelcontextprotocol.io/)
51. I don't understand what MCP does, and at this point i'm too afraid to ask : r/ClaudeAI \- Reddit, accessed November 16, 2025, [https://www.reddit.com/r/ClaudeAI/comments/1h71e1n/i\_dont\_understand\_what\_mcp\_does\_and\_at\_this\_point/](https://www.reddit.com/r/ClaudeAI/comments/1h71e1n/i_dont_understand_what_mcp_does_and_at_this_point/)
52. Powering AI Agents with Real-Time Data Using Anthropic's MCP and Confluent, accessed November 16, 2025, [https://www.confluent.io/blog/ai-agents-using-anthropic-mcp/](https://www.confluent.io/blog/ai-agents-using-anthropic-mcp/)
53. Connect Claude Code to tools via MCP, accessed November 16, 2025, [https://code.claude.com/docs/en/mcp](https://code.claude.com/docs/en/mcp)
54. Supercharging Product Development with Claude Code \+ MCP | by Mackenzie Bligh | Turo Engineering | Medium, accessed November 16, 2025, [https://medium.com/turo-engineering/supercharging-product-development-with-claude-code-mcp-8438e944b4a7](https://medium.com/turo-engineering/supercharging-product-development-with-claude-code-mcp-8438e944b4a7)
55. Claude Code MCP integration: A guide for devs and the no-code version for everyone else, accessed November 16, 2025, [https://www.eesel.ai/blog/claude-code-mcp-integration](https://www.eesel.ai/blog/claude-code-mcp-integration)
56. Model Context Protocol (MCP) \- Claude Docs, accessed November 16, 2025, [https://docs.claude.com/en/docs/mcp](https://docs.claude.com/en/docs/mcp)
57. Setting up Claude.ai | Atlassian Rovo MCP Server Cloud, accessed November 16, 2025, [https://support.atlassian.com/atlassian-rovo-mcp-server/docs/setting-up-claude-ai/](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/setting-up-claude-ai/)
58. Claude Code overview \- Claude Code Docs, accessed November 16, 2025, [https://code.claude.com/docs/en/overview](https://code.claude.com/docs/en/overview)
59. Code execution with MCP: building more efficient AI agents \- Anthropic, accessed November 16, 2025, [https://www.anthropic.com/engineering/code-execution-with-mcp](https://www.anthropic.com/engineering/code-execution-with-mcp)
60. Code Execution with MCP by Anthropic \- unwind ai, accessed November 16, 2025, [https://www.theunwindai.com/p/code-execution-with-mcp-by-anthropic](https://www.theunwindai.com/p/code-execution-with-mcp-by-anthropic)
61. Disrupting the first reported AI-orchestrated cyber espionage campaign \- Anthropic, accessed November 16, 2025, [https://www.anthropic.com/news/disrupting-AI-espionage](https://www.anthropic.com/news/disrupting-AI-espionage)
62. Chinese Hackers Use Anthropic's AI to Launch Automated Cyber Espionage Campaign, accessed November 16, 2025, [https://thehackernews.com/2025/11/chinese-hackers-use-anthropics-ai-to.html](https://thehackernews.com/2025/11/chinese-hackers-use-anthropics-ai-to.html)
63. Anthropic discloses “highly sophisticated” AI cyberattack that manipulated Claude Code tool, accessed November 16, 2025, [https://www.thehindu.com/sci-tech/technology/anthropic-discloses-highly-sophisticated-ai-cyberattack-that-manipulated-claude-codetool/article70278761.ece/amp/](https://www.thehindu.com/sci-tech/technology/anthropic-discloses-highly-sophisticated-ai-cyberattack-that-manipulated-claude-codetool/article70278761.ece/amp/)
64. Anthropic warns state-linked actor abused its AI tool in sophisticated espionage campaign, accessed November 16, 2025, [https://www.cybersecuritydive.com/news/anthropic-state-actor-ai-tool-espionage/805550/](https://www.cybersecuritydive.com/news/anthropic-state-actor-ai-tool-espionage/805550/)
65. AI firm claims it stopped Chinese state-sponsored cyber-attack campaign, accessed November 16, 2025, [https://www.theguardian.com/technology/2025/nov/14/ai-anthropic-chinese-state-sponsored-cyber-attack](https://www.theguardian.com/technology/2025/nov/14/ai-anthropic-chinese-state-sponsored-cyber-attack)
66. Detecting and countering misuse of AI: August 2025 \- Anthropic, accessed November 16, 2025, [https://www.anthropic.com/news/detecting-countering-misuse-aug-2025](https://www.anthropic.com/news/detecting-countering-misuse-aug-2025)
67. CLI reference \- Claude Code Docs, accessed November 16, 2025, [https://code.claude.com/docs/en/cli-reference](https://code.claude.com/docs/en/cli-reference)
68. Claude Code Learning Path: a practical guide to getting started | by Daniel Avila | Oct, 2025, accessed November 16, 2025, [https://medium.com/@dan.avila7/claude-code-learning-path-a-practical-guide-to-getting-started-fcc601550476](https://medium.com/@dan.avila7/claude-code-learning-path-a-practical-guide-to-getting-started-fcc601550476)
