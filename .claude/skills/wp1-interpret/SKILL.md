---
name: wp1-interpret
description: Interpret WP1 outputs, metrics, and reports
---

**Scope**
This skill explains how to read WP1 outputs and determine whether results look healthy or suspicious.

**When To Use**
Use this when a user asks what WP1 results mean, how to interpret MEGNO or FLI, or how to assess Jacobi drift.

**Primary Outputs**
- HDF5 orbits with attributes and datasets.
- Parquet exports for ML pipelines.
- Validation reports summarizing precision and chaos.

**Key Files**
- /Users/jacobsullivan/.codex/worktrees/8fe0/3body/data/tier1/analysis/validation_report.txt
- /Users/jacobsullivan/.codex/worktrees/8fe0/3body/src/python/validation/chaos_indicators.py
- /Users/jacobsullivan/.codex/worktrees/8fe0/3body/src/python/utils/dynamics.py

**Interpretation Workflow**
1. Check validation report for Jacobi drift statistics.
2. Inspect HDF5 attributes for `chaos_class`, `mean_MEGNO`, `final_FLI`.
3. Cross-check sample trajectories for drift outliers.
4. Confirm Parquet export exists for downstream ML usage.

**What Good Looks Like**
- Jacobi drift aligns with target accuracy for the tier.
- MEGNO and FLI values align with known chaotic vs regular regimes.
- Minimal missing or corrupted HDF5 files.

**Skill Self-Test**
1. Locate where `chaos_class` is stored for each orbit.
2. Explain how Jacobi drift is computed in WP1.
3. Explain expected precision targets for tier1 vs tier2.
