# Dry-Run Testing Infrastructure

## Overview

This directory contains infrastructure for performing end-to-end **Dry-Run** tests of the 3Body lift-integrability system. Dry runs are small-scale, controlled validation tests that verify the entire pipeline works correctly before committing to expensive production runs.

## Purpose

Dry runs serve to validate:

1. **Infrastructure Configuration**: Conda environment, Poetry dependencies, C++ build system
2. **Software Correctness**: All WP1-5 components function as expected
3. **Agent System**: Claude Code skills and subagents execute properly
4. **User Guides**: Documentation is accurate and complete
5. **Data Pipelines**: HDF5 generation, Parquet conversion, file I/O
6. **Integration Workflows**: End-to-end workflows from trajectory generation → validation
7. **Output Logging**: Proper logging, error handling, and diagnostics
8. **Result Verification**: Validation against known solutions and expected behaviors

## When to Run Dry Runs

Execute a dry run in these scenarios:

- **After environment changes**: New dependencies, library updates, system migrations
- **Before production runs**: Validate Tier 1/2 pipelines before launching 10⁴-10⁵ orbit runs
- **After major code changes**: Refactoring, new features, architectural modifications
- **Agent/documentation updates**: Changes to Claude Agent skills or User Guides
- **Reproducibility verification**: Ensure results match reference outputs
- **Onboarding**: New contributors validating their setup

## Directory Structure

```
Dry-Run/
├── README.md                           # This file
├── DDMmmYYYY-DryRun/                   # Date-stamped run folders
│   ├── Dry-Run-Experience-Log.MD       # Detailed test log
│   ├── configs/                        # Test configuration files
│   ├── data/                           # Small-scale test data
│   │   ├── trajectories/               # HDF5 outputs
│   │   └── parquet/                    # Parquet conversions
│   ├── logs/                           # Execution logs
│   ├── results/                        # Validation results
│   └── plots/                          # Diagnostic visualizations
└── reference/                          # Reference outputs for comparison
    └── known_solutions/                # Expected results for test cases
```

## Quick Start Guide

### 1. Create a New Dry-Run Session

```bash
# Create dated folder
DATE=$(date +%dth%b%Y)
mkdir -p Dry-Run/${DATE}-DryRun/{configs,data,logs,results,plots}

# Copy experience log template
cp Dry-Run/24thNov2025-DryRun/Dry-Run-Experience-Log.MD \
   Dry-Run/${DATE}-DryRun/
```

### 2. Environment Verification

```bash
# Activate environment
mamba activate wp1_env

# Verify Python dependencies
python verify_setup.py

# Build C++ components
./scripts/build_cpp.sh

# Run basic tests
./scripts/run_tests.sh
```

Document all output in the Experience Log.

### 3. Define Test Scope

Choose components to test based on your goals:

**Minimal Dry Run** (30 minutes):
- Environment setup
- 10 test trajectories (Tier 1 precision)
- Known solution validation (Lagrange L4/L5)
- Basic conservation checks

**Standard Dry Run** (2-4 hours):
- Full environment + C++ build
- 100 test trajectories (mixed regular/chaotic)
- WP2 geometric computations (connection, curvature)
- WP3 symbolic regression on test basis
- WP4 analytical vetting

**Comprehensive Dry Run** (1 day):
- All Standard components
- 1,000 test trajectories
- Full validation gauntlet (analytical + Morales-Ramis + Monte Carlo)
- Agent system testing (all WP skills)
- Documentation verification (User Guides WP1-5)

### 4. Configure Test Parameters

Create `configs/dry_run_config.yaml`:

```yaml
# Dry-Run Configuration
run_name: "24thNov2025-DryRun"
test_scope: "standard"  # minimal | standard | comprehensive

# Trajectory Parameters
n_trajectories: 100
integration_time: 100.0  # Time units (reduced from production 10^5)
precision: "double"      # Use "double-double" for Tier 2 tests
integrator: "ias15"      # ias15 | adaptive_symplectic | yoshida8

# Test Cases
test_cases:
  - lagrange_l4_l5       # Equilateral triangles
  - euler_collinear      # Collinear solutions
  - figure_eight         # Figure-8 choreography
  - random_sample        # Sobol quasi-random sampling

# Validation Components
validation:
  conservation_check: true
  chaos_indicators: true     # MEGNO, FLI
  analytical_vetting: true   # WP4.1
  morales_ramis: false       # Expensive, only for comprehensive
  monte_carlo: false         # Only for comprehensive

# Output Settings
output:
  save_hdf5: true
  save_parquet: true
  generate_plots: true
  log_level: "INFO"          # DEBUG | INFO | WARNING
```

### 5. Execute Dry Run

Run the automated dry-run script:

```bash
cd Dry-Run/${DATE}-DryRun

# Option A: Use provided script (recommended)
python ../../scripts/run_dry_run.py --config configs/dry_run_config.yaml

# Option B: Manual step-by-step execution
# (Follow steps in User-Guides/User-Guide-WP1.md for trajectory generation,
#  then WP4 validation guides)
```

### 6. Document Results

Fill out the **Dry-Run-Experience-Log.MD** with:

- **Setup phase**: Environment setup, build logs, test results
- **Execution phase**: Trajectory generation logs, timing, resource usage
- **Validation phase**: Conservation errors, validation results, pass/fail status
- **Agent testing**: Skill invocations, subagent performance, documentation accuracy
- **Issues encountered**: Errors, warnings, unexpected behaviors
- **Recommendations**: Configuration changes, code fixes, documentation updates

### 7. Compare Against Reference

```bash
# Compare trajectory checksums
python scripts/compare_trajectories.py \
  --test data/trajectories/orbit_test_0001.h5 \
  --reference ../reference/known_solutions/l4_reference.h5 \
  --tolerance 1e-12

# Verify conservation
python scripts/verify_conservation.py \
  --input data/trajectories/*.h5 \
  --max-error 1e-14
```

## Test Configuration Templates

### Minimal Test Configuration

**Purpose**: Quick smoke test (~30 minutes)

```yaml
n_trajectories: 10
integration_time: 10.0
test_cases: [lagrange_l4_l5]
validation:
  conservation_check: true
  chaos_indicators: false
  analytical_vetting: false
```

**Expected outcomes**:
- All trajectories complete without errors
- Energy conservation: |ΔC/C| < 10⁻¹⁴
- L4/L5 positions stable to < 10⁻¹² over integration time

### Standard Test Configuration

**Purpose**: Validate core pipeline (~2-4 hours)

```yaml
n_trajectories: 100
integration_time: 100.0
test_cases: [lagrange_l4_l5, euler_collinear, figure_eight, random_sample]
validation:
  conservation_check: true
  chaos_indicators: true
  analytical_vetting: true
```

**Expected outcomes**:
- 90%+ trajectories complete successfully
- Regular orbits: |ΔC/C| < 10⁻¹⁴, MEGNO → 2
- Chaotic orbits: MEGNO diverges
- Analytical vetting passes for known integrals (C, angular momentum)

### Comprehensive Test Configuration

**Purpose**: Full system validation before production (~1 day)

```yaml
n_trajectories: 1000
integration_time: 1000.0
precision: "double-double"
test_cases: [lagrange_l4_l5, euler_collinear, figure_eight, broucke_orbits, random_sample]
validation:
  conservation_check: true
  chaos_indicators: true
  analytical_vetting: true
  morales_ramis: true
  monte_carlo: true
```

**Expected outcomes**:
- 85%+ trajectories complete (some random cases may collide/escape)
- Tier 2 precision: |ΔC/C| < 10⁻²⁵
- Full validation gauntlet passes for classical integrals
- Morales-Ramis confirms classical non-integrability (downstairs)
- Monte Carlo validation shows robust conservation across parameter space

## Component-Specific Testing

### WP1: High-Precision Integration

**Test checklist**:
- [ ] IAS15 integrator produces trajectories with |ΔC/C| < 10⁻¹⁴
- [ ] Adaptive symplectic (double-double) achieves |ΔC/C| < 10⁻²⁵
- [ ] Regularization triggers correctly for close encounters (r < 0.01 Hill radii)
- [ ] HDF5 output structure matches schema (time, positions, momenta, attributes)
- [ ] Parquet conversion preserves data integrity

**Commands**:
```bash
# Generate test trajectories
python src/python/integrators/ias15.py --config configs/wp1_test.yaml

# Verify precision
python tests/test_conservation.py --data data/trajectories/*.h5
```

### WP2: Geometric Foundations

**Test checklist**:
- [ ] Mechanical connection computed without numerical issues
- [ ] Curvature form matches expected symmetries
- [ ] S¹ lift Hamiltonian conserved to machine precision
- [ ] KS-Spinor lift regularizes collisions correctly
- [ ] Coordinate transforms preserve symplectic structure

**Commands**:
```bash
# Test geometric computations
pytest tests/symbolic_lifts/ -v

# Visualize connection/curvature
python examples/plot_geometry.py --config configs/wp2_test.yaml
```

### WP3: Invariant Discovery

**Test checklist**:
- [ ] Symbolic regression recovers classical integrals (C, angular momentum)
- [ ] Spinor basis functions evaluate without overflow/underflow
- [ ] Elliptic functions handle edge cases (k → 0, k → 1)
- [ ] Multi-stage pipeline coordinates all discovery methods
- [ ] Interpretability module simplifies discovered expressions

**Commands**:
```bash
# Test on known solutions
python src/python/symbolic/multi_stage_pipeline.py \
  --trajectories data/trajectories/l4_test.h5 \
  --expected-integrals "C, Lz"

# Verify basis functions
pytest tests/wp3/ -v
```

### WP4: Validation Gauntlet

**Test checklist**:
- [ ] Analytical vetting confirms Poisson bracket {C, H} = 0
- [ ] Involution check for classical integrals passes
- [ ] Morales-Ramis test identifies non-abelian Galois group (downstairs)
- [ ] Monte Carlo validation runs without crashes
- [ ] Stress tests handle edge cases (collisions, escape, high eccentricity)

**Commands**:
```bash
# Run validation gauntlet
python src/python/validation/analytical_vetting.py \
  --candidate "C" \
  --trajectories data/trajectories/*.h5

# Morales-Ramis test on periodic orbit
python src/python/validation/morales_ramis_validator.py \
  --orbit data/trajectories/figure_eight.h5
```

### WP5: Consolidation

**Test checklist**:
- [ ] User Guides execute without errors
- [ ] Example scripts produce expected outputs
- [ ] Reproducibility tests match reference checksums
- [ ] Documentation reflects current code state

**Commands**:
```bash
# Verify User Guide examples
cd User-Guides
bash test_user_guide_examples.sh

# Check reproducibility
python scripts/verify_reproducibility.py \
  --reference reference/tier2_subset_seed42.npy \
  --test data/trajectories/
```

## Agent System Testing

### Testing Claude Code Skills

For each WP skill, verify:

1. **Skill invocation**: Skill loads without errors
2. **Documentation accuracy**: Instructions match code implementation
3. **Output quality**: Skill produces correct results
4. **Error handling**: Graceful failure modes

**Example test sequence**:

```
# In Claude Code session:

/skills  # List available skills

# Test WP1 skill
[User]: Use the wp1-precision-integration skill to generate 10 test trajectories

[Expected]: Skill loads → generates trajectories → saves HDF5 → reports results

# Test WP2 skill
[User]: Use the wp2-geometric-library skill to compute the mechanical connection
        for the Lagrange L4 configuration

[Expected]: Skill loads → computes connection → visualizes → returns symbolic form

# Continue for WP3-5 skills...
```

Document results in Experience Log under **Agent Testing** section.

## Common Issues and Troubleshooting

### Issue: Environment activation fails

**Symptom**: `mamba activate wp1_env` produces "environment not found"

**Solution**:
```bash
# Recreate environment
mamba env remove -n wp1_env
mamba env create -f environment.yml
mamba activate wp1_env
poetry install
```

### Issue: C++ build errors

**Symptom**: `./scripts/build_cpp.sh` fails with compilation errors

**Solution**:
```bash
# Clean build
rm -rf build/
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
cd ..
```

### Issue: Integration crashes with close encounters

**Symptom**: Trajectories fail with "Integration stopped: close encounter"

**Expected behavior**: This is normal for some random initial conditions. Regularization should trigger automatically if r < 0.01 Hill radii.

**Verify**:
```bash
# Check regularization logs
grep "Switching to regularized coordinates" logs/integration_*.log
```

If regularization isn't triggering, adjust threshold in `src/python/regularization/automatic_switching.py`.

### Issue: Conservation errors exceed tolerance

**Symptom**: |ΔC/C| > 10⁻¹⁴ for Tier 1 or > 10⁻²⁵ for Tier 2

**Diagnosis**:
1. Check integration time: Very long integrations accumulate error
2. Verify timestep: Adaptive integrator may be using too-large steps
3. Check for close encounters: Regularization may not have triggered
4. Verify arithmetic: Tier 2 requires QD library (double-double)

**Solution**:
```bash
# Reduce tolerance (forces smaller timesteps)
# Edit config: tolerance: 1e-14 → 1e-16

# For Tier 2, verify double-double is enabled
python -c "from src.python.integrators.adaptive_symplectic import DD_AVAILABLE; print(DD_AVAILABLE)"
# Should output: True
```

### Issue: Morales-Ramis test hangs

**Symptom**: `morales_ramis_validator.py` runs for hours without completing

**Cause**: Kovacic's algorithm is expensive for high-order variational equations

**Solution**:
- Use shorter periodic orbits (period < 10 time units)
- Reduce variational equation order (test only first-order variations)
- Skip Morales-Ramis for dry runs; only run for comprehensive validation

### Issue: HDF5 files corrupted

**Symptom**: `h5py.File()` raises "unable to open file"

**Cause**: Integration crashed mid-write

**Solution**:
```bash
# Check file integrity
h5check data/trajectories/*.h5

# Remove corrupted files
find data/trajectories/ -name "*.h5" -size 0 -delete

# Re-run integration with proper error handling
python src/python/integrators/ias15.py --resume-failed
```

## Performance Benchmarks

Expected runtimes for standard dry run (100 trajectories, integration time 100):

| Component | Expected Time | Notes |
|-----------|---------------|-------|
| Environment setup | 5-10 min | First time; ~1 min thereafter |
| C++ build | 2-5 min | Depends on cores |
| Test suite | 5-10 min | Python + C++ tests |
| Trajectory generation (Tier 1) | 30-60 min | IAS15, 100 orbits |
| Trajectory generation (Tier 2) | 2-4 hours | Double-double arithmetic |
| Chaos indicators (MEGNO/FLI) | 10-20 min | Computed alongside integration |
| Analytical vetting | 5-10 min | Fast symbolic checks |
| Morales-Ramis test | 1-3 hours | Expensive; skip for quick tests |
| Monte Carlo validation | 30-60 min | 100 trajectories, parameter sweep |

**Hardware reference**: Benchmarks assume 32-core workstation, 64 GB RAM.

## Success Criteria

A dry run is considered **successful** if:

1. **Environment**: All dependencies install, tests pass
2. **Integration**: ≥90% trajectories complete without errors
3. **Conservation**: Energy conserved to expected precision (10⁻¹⁴ Tier 1, 10⁻²⁵ Tier 2)
4. **Validation**: Known integrals pass analytical vetting
5. **Reproducibility**: Results match reference outputs within tolerance
6. **Documentation**: User Guides execute without errors
7. **Agents**: All WP skills load and produce correct outputs

## Reporting

After completing a dry run, create a summary report:

```markdown
# Dry-Run Summary: [DATE]

**Scope**: [minimal | standard | comprehensive]
**Duration**: [X hours]
**Status**: [SUCCESS | PARTIAL | FAILED]

## Results
- Trajectories generated: X / Y (Z% success)
- Conservation errors: [min, median, max]
- Validation results: [passed / total tests]
- Issues encountered: [count]

## Recommendations
- [ ] Ready for production: [YES | NO]
- [ ] Code changes needed: [list]
- [ ] Documentation updates: [list]
- [ ] Configuration adjustments: [list]
```

Include this summary in the Experience Log.

## Continuous Integration

For automated dry runs in CI/CD:

```yaml
# .github/workflows/dry-run.yml
name: Dry-Run CI

on: [push, pull_request]

jobs:
  minimal-dry-run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup environment
        run: |
          mamba env create -f environment.yml
          mamba activate wp1_env
          poetry install
      - name: Run minimal dry run
        run: |
          python scripts/run_dry_run.py --config Dry-Run/configs/minimal.yaml
      - name: Verify results
        run: |
          python scripts/verify_conservation.py --max-error 1e-14
```

## Archive and Comparison

Preserve dry-run results for historical comparison:

```bash
# Archive completed run
tar -czf Dry-Run/archives/24thNov2025-DryRun.tar.gz \
  Dry-Run/24thNov2025-DryRun/

# Compare with previous run
python scripts/compare_dry_runs.py \
  --current Dry-Run/24thNov2025-DryRun/ \
  --baseline Dry-Run/archives/01stNov2025-DryRun/
```

## Contact and Support

For questions about dry-run procedures:
- Refer to User-Guides: `User-Guides/README.md`
- Check project documentation: `Project-Design-Docs/OVERVIEW/`
- Review implementation reports: `Project-Design-Docs/Implementation-Status/`

---

**Next steps**: Create a dated subfolder, copy the Experience Log template, configure your test parameters, and begin testing!
