---
name: wp1-understand
description: Understand WP1 scope, architecture, and data flow
---

**Scope**
This skill orients you to WP1 (High-Precision Infrastructure) so you can explain what it does, where to find key files, and how data moves through the pipeline.

**When To Use**
Use this when the user asks for a WP1 overview, architecture map, data flow, or asks where to find WP1 code and outputs.

**Quick Start**
1. Read the WP1 user guide for the authoritative overview.
2. Read the repo README for the project-level flow.
3. Inspect the WP1 pipeline entrypoint and core modules.

**Primary References**
- /Users/jacobsullivan/.codex/worktrees/8fe0/3body/User-Guides/User-Guide-WP1.md
- /Users/jacobsullivan/.codex/worktrees/8fe0/3body/README.md
- /Users/jacobsullivan/.codex/worktrees/8fe0/3body/Snakefile

**WP1 System Map (Explainable Summary)**
1. Inputs
2. Integrators
3. Validation and chaos indicators
4. Pipeline orchestration
5. Outputs and reports

**Key WP1 Code Locations**
- /Users/jacobsullivan/.codex/worktrees/8fe0/3body/src/python/integrators/
- /Users/jacobsullivan/.codex/worktrees/8fe0/3body/src/python/validation/chaos_indicators.py
- /Users/jacobsullivan/.codex/worktrees/8fe0/3body/src/python/validation/shadow_hamiltonian.py
- /Users/jacobsullivan/.codex/worktrees/8fe0/3body/src/python/validation/time_reversibility.py
- /Users/jacobsullivan/.codex/worktrees/8fe0/3body/src/python/utils/dynamics.py
- /Users/jacobsullivan/.codex/worktrees/8fe0/3body/src/python/orbits/periodic_families.py

**WP1 Output Locations**
- /Users/jacobsullivan/.codex/worktrees/8fe0/3body/data/tier1/
- /Users/jacobsullivan/.codex/worktrees/8fe0/3body/data/tier2/
- /Users/jacobsullivan/.codex/worktrees/8fe0/3body/data/tier1/analysis/validation_report.txt

**Explainable Data Flow**
1. Parameter sampling produces initial conditions.
2. Integrators generate trajectories and states.
3. Chaos indicators compute MEGNO and FLI.
4. Results are stored in HDF5 and exported to Parquet.
5. Validation report summarizes Jacobi drift and chaos classes.

**Skill Self-Test**
1. Identify which file defines the production WP1 pipeline.
2. Identify where HDF5 and Parquet outputs are written.
3. Identify the core modules for integrators and chaos indicators.
