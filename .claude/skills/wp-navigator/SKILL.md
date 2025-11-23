---
name: wp-navigator
description: PRIMARY SKILL for 3Body lift-integrability project Work Package (WP) navigation. Identifies which WP subagent to delegate tasks to. Use for research, implementation, validation, and publication tasks.
---

# 3Body Work Package Navigator

## Project Context

**Mission**: Investigate lift-integrability in the Newtonian three-body problem through higher-dimensional symplectic embedding.

**Hypothesis**: While non-integrable in standard coordinates (Bruns-Poincaré theorem), new conserved quantities may exist in "upstairs" spaces (S¹ lift, KS-Spinor lift).

## Directory Structure (Source of Truth)

```
3body/
├── src/python/              # All implementation code
│   ├── integrators/         # WP1: High-precision trajectory generation
│   ├── coordinates/         # WP2: Coordinate transformations
│   ├── geometry/            # WP2: Connection, curvature, metric
│   ├── lifts/               # WP2: S¹, KS lift constructions
│   ├── symbolic/            # WP3: Symbolic regression, basis functions
│   ├── ml/                  # WP3: Hamiltonian Neural Networks
│   ├── validation/          # WP4: Analytical vetting, Morales-Ramis
│   └── visualization/       # Cross-WP: Plotting utilities
├── tests/                   # Test suites (mirrors src/ structure)
├── data/                    # Trajectory HDF5/Parquet files
├── User-Guides/             # WP-specific usage documentation
├── Project-Design-Docs/     # Implementation plans
└── Claude-Agent-Docs/       # This architecture documentation
```

## Subagent Delegation Matrix

**Use this table to decide which subagent to invoke for a given task:**

| Task Description | Delegate To | Rationale |
|------------------|-------------|-----------|
| Generate trajectories, run QA, package data | `wp1-lab-director` | End-to-end data pipeline |
| Build coordinate systems, lifts, bundles | `wp2-architect` | Geometric construction |
| Compute curvature, test integrability | `wp2-analyst` | Geometric verification |
| Run PDE solver, train HNNs, symbolic regression | `wp3-investigator` | Integral discovery (multi-method) |
| Filter trivial integrals, rank candidates | `wp3-consolidator` | Result deduplication and prioritization |
| Symbolic proofs, Poisson brackets, Galois groups | `wp4-mathematician` | Analytical rigor |
| Monte Carlo sweeps, stress tests, long-time validation | `wp4-stress-tester` | Numerical robustness |
| Write manuscript sections, proofs, LaTeX | `wp5-author` | Publication writing |
| Code cleanup, reproducibility, Zenodo upload | `wp5-librarian` | Archival and release |
| Complex multi-WP research questions | `research-orchestrator` | Meta-level planning |

## Development Rules (MANDATORY)

### 1. Read First, Never Guess
**NEVER** propose changes to code you haven't read. If modifying a file, use `Read` tool first.

**Example Workflow**:
```bash
# WRONG: Directly edit based on memory
Edit src/python/coordinates/jacobi.py ...

# CORRECT: Read, understand, then edit
Read src/python/coordinates/jacobi.py
# [Review current implementation]
Edit src/python/coordinates/jacobi.py ...
```

### 2. Test-Driven Development
Create tests in `tests/` **before** implementation.

**Example Workflow**:
```bash
# Step 1: Write failing test
Write tests/validation/test_new_feature.py

# Step 2: Run test (expect failure)
Bash: pytest tests/validation/test_new_feature.py

# Step 3: Implement feature
Edit src/python/validation/new_feature.py

# Step 4: Verify test passes
Bash: pytest tests/validation/test_new_feature.py
```

### 3. Flight Recorder (Scientific Audit Trail)
All research tasks (WP3, WP4) MUST maintain a `session_log.md` in the task directory.

**Required Format**:
```markdown
# Session Log: [Task Name]
**Agent**: [Subagent Name]
**Date**: [ISO 8601 Timestamp]

## Hypothesis
[What are we testing?]

## Methods Attempted
### Attempt 1: [Method Name]
- **Approach**: [Description]
- **Result**: [Success/Failure/Partial]
- **Evidence**: [File paths, plot paths, metrics]
- **Conclusion**: [Next steps or pivot decision]

### Attempt 2: ...

## Final Recommendation
[Actionable next step based on evidence]
```

**Enforcement**: Subagents MUST NOT report success without citing specific log entries.

## User Guide References

**For detailed usage instructions, consult**:
- `User-Guides/User-Guide-WP1.md` - Integration pipeline
- `User-Guides/User-Guide-WP2.md` - Geometric foundations
- `User-Guides/User-Guide-WP3.md` - Discovery methods
- `User-Guides/User-Guide-WP4.md` - Validation gauntlet
- `User-Guides/User-Guide-WP5.md` - Publication workflow

## Quick Reference: Common Operations

```bash
# Environment setup
mamba activate wp1_env
python verify_setup.py

# Build C++ components (QD library)
./scripts/build_cpp.sh

# Run all tests
./scripts/run_tests.sh

# Production integration run (Tier 1)
snakemake --cores 64 --config tier=1

# Validate a candidate integral
python -m src.python.validation.analytical_vetting --candidate <expr>

# Code formatting
black src/ tests/
flake8 src/ tests/
```

## CRITICAL: Anti-Patterns to Avoid

❌ **Never duplicate code**: Use `from src.python.X import Y`, don't re-implement
❌ **Never commit data files**: `.h5`, `.parquet` go in `.gitignore`
❌ **Never skip tests**: Pre-commit hooks enforce this
❌ **Never use Bash for file ops**: Use Read/Edit/Write tools instead
❌ **Never create docs unprompted**: User explicitly requests .md files

## Session Initialization Checklist

When starting a new session, verify:
1. [ ] Working directory: `/home/user/3body`
2. [ ] Branch: `claude/*` (task-specific)
3. [ ] Environment: `wp1_env` activated
4. [ ] Tests passing: `./scripts/run_tests.sh` shows green
5. [ ] Flight Recorder ready: `session_log.md` created if research task

## Supporting Assets
- `User-Guides/README.md` - Entry point for all user documentation
- `CLAUDE.md` - Project-level persistent instructions
- `Project-Design-Docs/OVERVIEW/` - Theoretical framework
