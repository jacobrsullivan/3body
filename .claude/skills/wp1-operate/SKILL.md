---
name: wp1-operate
description: Operate WP1 pipelines, runs, and validations
---

**Scope**
This skill helps you run WP1 end-to-end: environment setup, build steps, smoke runs, and production Snakemake pipelines.

**When To Use**
Use this when the user wants to run WP1, generate trajectories, or execute the production pipeline.

**Preflight Checks**
1. Verify Python and deps.
2. Verify C++ build if required.
3. Run a quick integration smoke test.

**Canonical Commands**
```bash
cd /Users/jacobsullivan/.codex/worktrees/8fe0/3body
python verify_setup.py
./scripts/build_cpp.sh
./scripts/run_tests.sh
```

**Run A Minimal WP1 Integration**
Use the example in the README or User-Guide-WP1 to integrate a short trajectory and check Jacobi drift.

**Production Pipeline (Snakemake)**
```bash
cd /Users/jacobsullivan/.codex/worktrees/8fe0/3body
snakemake --cores 64 --config tier=1
snakemake --cores 32 --config tier=2
```

**Outputs To Expect**
- /Users/jacobsullivan/.codex/worktrees/8fe0/3body/data/tier1/hdf5/*.h5
- /Users/jacobsullivan/.codex/worktrees/8fe0/3body/data/tier1/parquet/tier1.parquet
- /Users/jacobsullivan/.codex/worktrees/8fe0/3body/data/tier1/analysis/validation_report.txt

**Common Gotchas**
- Missing HDF5 or Parquet libs in the Python environment.
- Snakemake not installed in the active environment.
- QD or double-double requirements for tier2.

**Skill Self-Test**
1. Run `python verify_setup.py` and confirm all checks pass.
2. Confirm that a Snakemake tier1 run creates `data/tier1/complete.flag`.
3. Confirm that validation report exists after the run.
