# Decision Matrix: Extended Classification Guide

## Overview

This reference provides extended examples and edge cases for classifying architectural questions into the four abstractions: Scope, Time, Data, Logic.

## Classification Rules

### Scope (C4 Context) - "WHAT exists"
**Focus**: System boundaries, components, external dependencies

**Triggers**:
- "What systems..."
- "What components..."
- "External dependencies"
- "Integration with..."
- "Architecture overview"

**Examples**:
- "What external libraries does the project use?"
- "Show me the system architecture"
- "What are the major components?"
- "What datastores does the system interact with?"

---

### Time (Sequence) - "HOW things interact"
**Focus**: Message flow, temporal ordering, workflows

**Triggers**:
- "How does..."
- "Workflow"
- "Process"
- "Pipeline"
- "Flow"
- "Steps"

**Examples**:
- "How does the validation gauntlet process candidates?"
- "What's the integration workflow?"
- "How do components communicate?"
- "Walk me through the discovery pipeline"

---

### Data (ERD) - "WHAT data exists"
**Focus**: Entity structures, relationships, attributes

**Triggers**:
- "What data..."
- "Data model"
- "Schema"
- "Entities"
- "Relationships"
- "Stored"

**Examples**:
- "What data is stored in HDF5 files?"
- "What's the relationship between trajectories and validation reports?"
- "Show me the data model"
- "What entities represent discovered integrals?"

---

### Logic (State Machine) - "WHAT states/transitions exist"
**Focus**: Entity lifecycle, status, state transitions

**Triggers**:
- "States"
- "Stages"
- "Lifecycle"
- "Status"
- "Transitions"
- "Progression"

**Examples**:
- "What are the validation stages?"
- "What's the lifecycle of a candidate integral?"
- "What states can an integration job have?"
- "How does a trajectory progress through classification?"

---

## Edge Cases and Resolutions

### Case 1: Question Spans Multiple Abstractions

**Q**: "Explain the validation system"

**Resolution**: Offer multiple perspectives:
- Scope: Components involved
- Time: Workflow and message flow
- Data: Validation data structures
- Logic: Validation stage progression

**Action**: Ask user which aspect they want first.

---

### Case 2: Technical Implementation Question

**Q**: "What Python classes implement validation?"

**Resolution**: This is an **implementation** question, not architectural.

**Action**: Clarify scope:
```
This seems like an implementation question. For architectural understanding, I can provide:
- **Scope**: Validation subsystem boundaries
- **Time**: Validation workflow
- **Data**: Validation entities
- **Logic**: Validation stages

For implementation details (classes, functions), I can point you to specific source files. Which would you prefer?
```

---

### Case 3: Performance/Operations Question

**Q**: "Why is integration slow?"

**Resolution**: This is a **debugging** question, not architectural.

**Action**: Redirect:
```
This is a performance troubleshooting question. Architectural diagrams can help identify bottlenecks:
- **Sequence Diagram**: Show where time is spent in workflow
- **State Machine**: Show where jobs get stuck

Would you like me to generate these diagrams to help diagnose the issue?
```

---

### Case 4: Ambiguous Keywords

**Q**: "How is data structured?"

**Analysis**:
- "how" suggests Time (workflow)
- "structured" suggests Data (entity relationships)

**Resolution**: Clarify:
```
This question could mean:
1. **Data Model** (ERD): What entities and relationships exist?
2. **Data Flow** (Sequence): How data moves through the system?

Which aspect are you interested in?
```

---

## Keyword Disambiguation Table

| Keyword | Possible Meanings | Disambiguation |
|---------|------------------|----------------|
| "workflow" | Time (sequence) OR Logic (state progression) | If asks "how", use Time. If asks "what states", use Logic. |
| "structure" | Data (ERD) OR Scope (architecture) | If asks about data, use Data. If asks about systems, use Scope. |
| "process" | Time (workflow) OR Logic (state machine) | If asks about sequence of steps, use Time. If asks about state changes, use Logic. |
| "system" | Scope (components) OR broad (all abstractions) | If asks "what systems", use Scope. If asks "explain system", offer multiple views. |

---

## Classification Confidence Levels

### High Confidence (>90%)
- Clear trigger keywords match one abstraction
- Question structure unambiguous
- User intent obvious

**Action**: Immediately route to appropriate skill

**Example**: "What external dependencies exist?" → Scope (100% confidence)

---

### Medium Confidence (60-90%)
- Multiple abstractions could apply
- Keywords span categories
- Some ambiguity in intent

**Action**: State classification and rationale, proceed unless user corrects

**Example**: "How is validation structured?" → Could be Time or Data
**Response**: "Interpreting as Time (validation workflow). Let me know if you meant data structure instead."

---

### Low Confidence (<60%)
- Very ambiguous question
- No clear trigger keywords
- Could apply to multiple abstractions equally

**Action**: Ask clarifying question before proceeding

**Example**: "Tell me about the system" → Too broad
**Response**: [Ask which aspect user wants to understand]

---

## 3body-Specific Routing Examples

### Scenario: New Researcher Onboarding

**Q**: "I'm new to the project. Where should I start?"

**Routing**:
1. Start with **Scope** (C4 Context) - Show overall architecture
2. Then **Time** (Sequence) - Show key workflows (integration, validation)
3. Optionally **Data** (ERD) - Show core data entities
4. Optionally **Logic** (State Machine) - Show validation stages

---

### Scenario: Code Review Context

**Q**: "I'm reviewing a PR that changes validation logic. What architectural impact should I check?"

**Routing**:
1. **Logic** (State Machine) - Check if validation stages changed
2. **Sequence** (Sequence Diagram) - Check if message flow altered
3. **Data** (ERD) - Check if validation entities changed

---

### Scenario: Debugging Integration

**Q**: "Integration jobs are failing at the MR test stage"

**Routing**:
1. **Logic** (State Machine) - Show job status transitions
2. **Sequence** (Sequence Diagram) - Show MR test invocation flow
3. **Scope** (C4 Context) - Check MR test dependencies

---

## Multi-Diagram Recommendations

Some questions benefit from multiple diagrams:

| User Need | Recommended Diagrams | Order |
|-----------|---------------------|-------|
| Onboarding | Scope → Time → Data | Overview first, then workflows, then data |
| Debugging | Logic → Sequence → Scope | States first, then flow, then dependencies |
| Feature Planning | Data → Logic → Sequence → Scope | Data model first, then state, then flow, then integration |
| Code Review | Logic → Data → Sequence | States first, then data, then interactions |

---

## False Positive Patterns

### Pattern: Question NOT About Architecture

**Indicators**:
- Asks about specific code implementation (class names, function signatures)
- Asks about numeric results or outputs
- Asks about configuration values
- Asks about debugging or troubleshooting

**Example**: "What parameters does IAS15 integrator accept?"

**Action**: This is an API/documentation question, not architectural. Redirect to code or documentation.

---

## Quality Checks

Before routing to diagram skill, verify:

1. ✓ Classification confidence >60%
2. ✓ User intent understood
3. ✓ Appropriate abstraction selected
4. ✓ Specific focus area identified for Architect

If any check fails, ask clarifying question.

---

**Reference Version**: 1.0
**Created**: 2025-11-23
