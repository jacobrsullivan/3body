---
name: wp1-diagnose
description: Diagnose WP1 failures, trace runs, and debug issues
---

**Scope**
This skill focuses on troubleshooting WP1: missing outputs, pipeline failures, precision regressions, and environment issues.

**When To Use**
Use this when a run failed, outputs are missing, or results are suspicious.

**Fast Triage Checklist**
1. Run setup verification.
2. Check Snakemake logs and missing targets.
3. Verify HDF5 file integrity and attributes.
4. Check precision targets vs observed drift.

**Commands To Use**
```bash
cd /Users/jacobsullivan/.codex/worktrees/8fe0/3body
python verify_setup.py
ls -la data/tier1/hdf5 | head -n 5
```

**Where To Look**
- Snakemake outputs: /Users/jacobsullivan/.codex/worktrees/8fe0/3body/data/
- Validation report: /Users/jacobsullivan/.codex/worktrees/8fe0/3body/data/tier1/analysis/validation_report.txt
- Integrator code: /Users/jacobsullivan/.codex/worktrees/8fe0/3body/src/python/integrators/
- Chaos indicators: /Users/jacobsullivan/.codex/worktrees/8fe0/3body/src/python/validation/chaos_indicators.py

**Common Failure Modes**
- Missing Python deps or incompatible versions.
- Snakemake not available or wrong environment.
- HDF5 or Parquet library missing.
- Tier2 precision failures due to missing QD.

**Skill Self-Test**
1. Identify the most likely root cause if HDF5 files are missing.
2. Identify where the Jacobi drift calculation lives.
3. Identify which file defines the production pipeline rules.
