# Flight Recorder: Session Log Template

**Document Version**: 1.0
**Date**: 2025-11-23
**Purpose**: Standard template for scientific audit trails in research tasks

---

## What is the Flight Recorder?

The **Flight Recorder** is a scientific audit trail that documents research hypotheses, methods attempted, results, and decision-making rationale. It ensures reproducibility and transparency in the research process.

## When to Use

**REQUIRED** for all research tasks (WP3 and WP4):
- Discovery methods (symbolic regression, PDE solvers, HNNs)
- Validation pipelines (analytical vetting, Morales-Ramis tests, Monte Carlo)
- Any exploratory or experimental work where hypotheses are being tested

**NOT REQUIRED** for:
- Routine implementation tasks (adding tests, refactoring code)
- Documentation updates
- Build and deployment tasks

## Template

Copy this template to create your session log:

```markdown
# Flight Recorder: [Task Name]

**Agent**: [Subagent Name, e.g., wp3-investigator]
**Session ID**: [UUID or timestamp]
**Date**: [ISO 8601, e.g., 2025-11-23T14:32:00Z]
**Status**: [In Progress / Completed / Blocked]

---

## Objective
[1-2 sentence description of research goal]

**Hypothesis**: [Specific, testable claim]

**Success Criteria**: [Quantitative metrics, e.g., "Conservation error < 10^-12"]

---

## Experimental Log

### Experiment 1: [Method Name]
**Timestamp**: [ISO 8601]

**Approach**:
- [Detailed description of method]
- [Parameters used]
- [Data sources]

**Execution**:
```bash
# Commands run
python -m src.python.symbolic.multi_stage_pipeline --basis spinor --timeout 12h
```

**Results**:
- **Outcome**: [Success / Partial / Failure]
- **Metrics**: [Quantitative results, e.g., "Found 47 candidates, 45 trivial"]
- **Evidence**:
  - Data: `discovery_logs/spinor_candidates.csv`
  - Plots: `discovery_logs/pareto_front.png`
  - Logs: `discovery_logs/pysr_output.log`

**Analysis**:
[Interpretation of results]

**Conclusion**:
- [Key finding]
- [Next step or pivot decision]

---

### Experiment 2: [Method Name]
[Same structure as Experiment 1]

---

## Summary

**Successful Hypotheses**: [List validated claims]

**Failed Hypotheses**: [List rejected claims with reasons]

**Open Questions**: [Remaining uncertainties]

**Recommended Next Steps**: [Actionable items for continuation]

---

## Artifacts
[Table of all generated files]

| File Path | Type | Description |
|-----------|------|-------------|
| `discovery_logs/candidates.csv` | Data | 47 candidate integrals |
| `discovery_logs/pareto_front.png` | Plot | Complexity vs. Error |
| `validation_reports/poisson_test.md` | Report | Analytical vetting results |
```

## Example Session Log

See below for a complete example:

```markdown
# Flight Recorder: Spinor Basis Symbolic Regression

**Agent**: wp3-investigator
**Session ID**: 2025-11-23-143227-uuid4
**Date**: 2025-11-23T14:32:27Z
**Status**: Completed

---

## Objective
Search for novel conserved quantities in KS spinor coordinates using symbolic regression with spinor basis functions.

**Hypothesis**: Polynomial combinations of KS spinor coordinates (u₁, u₂, u₃, u₄) may yield new first integrals beyond the known Jacobi constant C and angular momentum L.

**Success Criteria**:
- Find at least 1 candidate with conservation error < 10^-12
- Candidate must be non-trivial (not a linear combination of C, L)
- Computational cost < 12 hours on 64 cores

---

## Experimental Log

### Experiment 1: Spinor Basis Symbolic Regression
**Timestamp**: 2025-11-23T14:35:00Z

**Approach**:
- Tool: PySR (Julia backend) with custom spinor basis
- Basis functions: 80 spinor polynomials from `src/python/symbolic/spinor_basis.py`
- Dataset: 10,000 trajectories from `data/tier1/parquet/mu05_C30/`
- Max complexity: 15 operations
- Population size: 1000, iterations: 100

**Execution**:
```bash
python -m src.python.symbolic.multi_stage_pipeline \
  --basis spinor \
  --data data/tier1/parquet/mu05_C30/ \
  --max_complexity 15 \
  --timeout_hours 12 \
  --output discovery_logs/spinor_results.csv
```

**Results**:
- **Outcome**: Partial Success
- **Metrics**:
  - Total candidates: 127
  - After trivial filtering: 3 novel candidates
  - Best conservation error: 3.2 × 10^-13
  - Runtime: 8.3 hours
- **Evidence**:
  - Data: `discovery_logs/spinor_candidates.csv`
  - Plots: `discovery_logs/pareto_complexity_error.png`
  - Logs: `discovery_logs/pysr_stdout.log`

**Analysis**:
Of 127 candidates, 124 were trivial (combinations of C, L, or coordinate artifacts). The 3 novel candidates are:
1. `u1**2 + u2**2 - u3**2 - u4**2` (conservation error: 3.2e-13, complexity: 7)
2. `(u1*u3 + u2*u4)**2` (conservation error: 8.1e-12, complexity: 9)
3. Complex expression involving cross terms (conservation error: 2.4e-11, complexity: 14)

**Conclusion**:
- Candidate #1 is most promising (simple, low error)
- Need to verify it's not equivalent to known integral via coordinate transform
- Next step: Analytical vetting (WP4.1)

---

## Summary

**Successful Hypotheses**:
- Spinor basis can discover non-trivial candidates (3 found)
- Computational cost within budget (8.3h < 12h)

**Failed Hypotheses**:
- None explicitly failed, but success rate (3/127 = 2.4%) is lower than expected

**Open Questions**:
- Is candidate #1 genuinely new or a disguised classical integral?
- Would elliptic or theta basis yield better results?

**Recommended Next Steps**:
1. Delegate to `wp4-mathematician`: Analytical vetting of candidate #1
2. If #1 fails, try candidate #2
3. If both fail, consider elliptic basis search (WP3 Stage 2)

---

## Artifacts

| File Path | Type | Description |
|-----------|------|-------------|
| `discovery_logs/spinor_candidates.csv` | Data | All 127 candidates with metrics |
| `discovery_logs/pareto_complexity_error.png` | Plot | Pareto front visualization |
| `discovery_logs/pysr_stdout.log` | Log | Full PySR output |
| `discovery_logs/top3_candidates.md` | Report | Detailed analysis of top 3 |
```

## Enforcement

All WP3 and WP4 subagents have the following requirement in their system prompts:

```markdown
## FLIGHT RECORDER ENFORCEMENT

You MUST maintain a `session_log.md` in your working directory.

**Before starting work**:
1. Create `session_log.md` using the Flight Recorder template
2. Document your objective and hypothesis

**During work**:
1. Log each experiment attempt (method, parameters, commands)
2. Record results with file paths as evidence

**Before reporting completion**:
1. Update session log with final summary
2. In your report to the orchestrator, cite specific log entries (e.g., "See session_log.md, Experiment 3")

**CRITICAL**: Do NOT claim success without citing evidence in the Flight Recorder.
```

## File Location

Session logs should be created in:
- **WP3 Discovery**: `discovery_logs/session_log_[date].md`
- **WP4 Validation**: `validation_reports/session_log_[date].md`
- **Multi-WP Research**: `research_strategy/session_log_[date].md`

## Benefits

1. **Reproducibility**: Other researchers can understand and replicate your work
2. **Auditability**: Peer reviewers can trace decision-making rationale
3. **Knowledge Preservation**: Negative results documented (not lost)
4. **Pivot Decisions**: Evidence-based justification for research direction changes
5. **Manuscript Writing**: Session logs become supplementary material

## Related Documentation

- Implementation Plan: `Claude-Agent-Docs/WPSkillsDocs/Implementation-Plan-Agents-for-3Body.MD`
- User Guides: `User-Guides/User-Guide-WP[3-4].md`
- Settings: `.claude/settings.json` (automation hooks)
