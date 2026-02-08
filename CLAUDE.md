# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a scientific computing project investigating **lift-integrability** in the Newtonian three-body problem through higher-dimensional symplectic embedding. The central hypothesis: while the three-body problem is non-integrable in standard coordinates (Bruns-Poincaré theorem), new conserved quantities may exist in appropriately constructed "upstairs" spaces.

The project consists of 5 Work Packages (WP1-5):
- **WP1**: High-precision trajectory generation and validation infrastructure
- **WP2**: Geometric reduction, mechanical connection, and lift constructions (S¹, KS-Spinor)
- **WP3**: Invariant discovery via symbolic regression, ML, and specialized basis searches
- **WP4**: Rigorous validation (Poisson brackets, Morales-Ramis test, statistical robustness)
- **WP5**: Consolidation, manuscript preparation, and reproducibility

## Development Environment

### Setup
```bash
# 1. Create conda environment (system-level dependencies)
mamba env create -f environment.yml
mamba activate wp1_env

# 2. Install Python dependencies via Poetry
poetry install

# 3. Verify setup
python verify_setup.py
```

### Building C++ Components
```bash
# Build all C++ components (QD library wrappers, benchmarks)
./scripts/build_cpp.sh

# Outputs go to build/ directory
# Key executables: qd_comprehensive_test, qd_benchmark, verify_qd
```

### Running Tests
```bash
# Run all tests (Python + C++)
./scripts/run_tests.sh

# Run Python tests only
pytest tests/ -v

# Run specific test file
pytest tests/validation/test_kovacic.py -v

# Run tests with coverage
pytest tests/ --cov=src/python --cov-report=html
```

### Code Quality
Pre-commit hooks automatically run before commits:
- **Black**: Code formatting (max line length: 88)
- **Flake8**: Linting (ignores E203 for Black compatibility)
- **Trailing whitespace** and **end-of-file** checks

If hooks fail, they auto-fix files. Stage changes and re-commit.

To run manually:
```bash
pre-commit run --all-files
```

## Repo-Specific Git/SSH Note

For this repo, use the `id_jacob` SSH key without changing global SSH config. Set a repo-local SSH command:

```bash
git config core.sshCommand "ssh -i ~/.ssh/id_jacob -o IdentitiesOnly=yes"
```

## Working Directory and Path Handling

### Critical Rule: Always Work from Project Root

**All commands, scripts, and Claude Code sessions MUST start from the project root directory:**

```bash
cd /path/to/3body  # Project root
pwd  # Should show: /path/to/3body (NOT a subdirectory!)
```

### Validation Before Starting

**Always validate your working directory before any operations:**

```bash
# Automated validation
python scripts/validate_working_dir.py

# Manual verification
test -f CLAUDE.md && test -d src/python && echo "✅ Correct" || echo "❌ Wrong directory"

# From git
cd $(git rev-parse --show-toplevel)
```

### Path Handling Best Practices

#### 1. Use Absolute Paths for File Operations

```python
# ✅ CORRECT - Absolute path
file_path = "/Users/username/3body/Dry-Run/24thNov2025-DryRun/config.yaml"

# ❌ WRONG - Relative path (fragile, depends on working directory)
file_path = "Dry-Run/24thNov2025-DryRun/config.yaml"
```

#### 2. Resolve Paths from Project Root in Scripts

```python
from pathlib import Path

# Method 1: From script location (adjust parents[N] for nesting depth)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Method 2: From git
import subprocess
result = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                       capture_output=True, text=True, check=True)
PROJECT_ROOT = Path(result.stdout.strip())

# Build paths from root
config_path = PROJECT_ROOT / "Dry-Run" / "configs" / "config.yaml"
```

#### 3. Validate Working Directory in All Scripts

**Add this to the start of all Python scripts:**

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

# Validate working directory
PROJECT_ROOT = Path.cwd()
if not (PROJECT_ROOT / "CLAUDE.md").exists():
    print(f"ERROR: Must run from project root")
    print(f"Current: {PROJECT_ROOT}")
    print(f"Expected: /path/to/3body")
    print(f"\nFix: cd /path/to/3body")
    sys.exit(1)

print(f"✓ Working directory: {PROJECT_ROOT}")
```

### Why This Matters

**Path confusion causes:**
- Files created in wrong locations
- Import errors for Python modules
- Test discovery failures
- Broken relative path references
- Confusing nested directory structures

**Always verify before executing:**
1. Run `pwd` - should show project root
2. Run `python scripts/validate_working_dir.py` - should pass
3. Proceed with confidence

### Recovery from Wrong Directory

If you find yourself in a subdirectory:

```bash
# Option 1: Navigate to root
cd /path/to/3body

# Option 2: Use git (if in repository)
cd $(git rev-parse --show-toplevel)

# Option 3: Navigate up manually
cd ../..  # Adjust as needed

# Then verify
python scripts/validate_working_dir.py
```

## Architecture: The "Validation Gauntlet"

The codebase is structured around a **three-stage validation pipeline** where candidate integrals must pass progressively rigorous tests:

### Stage 1: Discovery (WP3)
**Location**: `src/python/symbolic/`, `src/python/ml/`

Candidate integrals are discovered via:
- **Symbolic Regression**: Specialized function bases (spinor, elliptic, theta functions)
- **Neural Networks**: Hamiltonian Neural Networks learn conserved quantities
- **PDE Methods**: Solve Hamilton-Jacobi equations for generating functions

**Key modules**:
- `symbolic/spinor_basis.py`: ~80 spinor functions for KS-lifted phase space
- `symbolic/elliptic_basis.py`: Jacobi elliptic functions (sn, cn, dn) for quasi-periodic motion
- `symbolic/theta_basis.py`: Theta functions for complete integrability proofs
- `symbolic/multi_stage_pipeline.py`: Coordinates all discovery methods

### Stage 2: Analytical Vetting (WP4.1)
**Location**: `src/python/validation/analytical_vetting.py`

Tests Liouville integrability criteria:
1. **Conservation**: `{I, H} = 0` (Poisson bracket with Hamiltonian)
2. **Involution**: `{I_i, I_j} = 0` (all pairs commute)
3. **Independence**: Jacobian rank = number of integrals (no redundancy)

**Implementation note**: Uses symbolic differentiation (SymPy) + numerical verification on trajectories.

### Stage 3: Morales-Ramis Test (WP4.2)
**Location**: `src/python/validation/morales_ramis_validator.py`, `kovacic.py`

Differential Galois Theory obstruction test:
- **Phase I (Downstairs)**: Compute variational equations along periodic orbits. Non-abelian identity component → classical non-integrability (expected to fail).
- **Phase II (Upstairs)**: Repeat in lifted space. Abelian identity component → validates lift-integrability hypothesis (looking for this).

**Key algorithm**: Kovacic's algorithm classifies 2nd-order linear ODEs by their Galois groups.

### Stage 4: Numerical Robustness (WP4.3)
**Location**: `src/python/validation/monte_carlo_validator.py`, `stress_tester.py`

Statistical validation across parameter space:
- Monte Carlo sweep: 10⁵-10⁶ trajectories
- Stress tests: collisions, chaos, high eccentricity, escape scenarios
- Long-time validation: Shadow Hamiltonian analysis for symplectic integrator backward error

## Critical Architectural Patterns

### 1. Coordinate System Hierarchy
**Location**: `src/python/coordinates/`

The project uses multiple coordinate systems with explicit transformations:

```
Cartesian (18D) → Jacobi (15D) → Shape Space (12D) → Lifted Spaces
```

- **Cartesian**: `(r₁, r₂, r₃, p₁, p₂, p₃)` - 3 bodies in 3D
- **Jacobi**: Eliminates center-of-mass (3 translational symmetries)
- **Shape Space**: Further eliminates rotations (3 additional symmetries)
- **S¹ Lift**: Adds 1D fiber to "untwist" mechanical connection
- **KS-Spinor Lift**: Adds 4D spinor coordinates for collision regularization

**Rule**: Always use `coordinates/transforms.py` for conversions. Never implement transformations inline—symplectic structure must be preserved exactly.

### 2. Symplectic Integration Hierarchy
**Location**: `src/python/integrators/`

Three integrators for different precision/speed trade-offs:

| Integrator | Precision | Speed | Use Case |
|------------|-----------|-------|----------|
| `ias15.py` | Standard (ε ~ 10⁻¹⁴) | Fast | Tier 1 (exploration) |
| `adaptive_symplectic.py` | High (ε ~ 10⁻²⁵) | Medium | Tier 2 (validation) |
| `yoshida8.py` | Standard | Fastest | Benchmarks |

**Double-double arithmetic**: Tier 2 uses QD library (31 decimal digits) for energy conservation < 10⁻²⁵.

**Regularization**: For close encounters (r < 0.01 Hill radii), integrators automatically switch to regularized coordinates (Levi-Civita 2D, KS 3D). See `src/python/regularization/`.

### 3. Geometric Object Construction Pattern
**Location**: `src/python/geometry/`

Geometric objects (connection, curvature, metric) follow a standard pipeline:

```python
# 1. Compute in Shape Space
from src.python.geometry.connection_form import MechanicalConnection
A = MechanicalConnection()
connection = A.compute(q_shape, v_shape)  # Shape space coords

# 2. Compute curvature (exterior derivative)
from src.python.geometry.curvature_form import CurvatureForm
F = CurvatureForm()
curvature = F.compute(q_shape)  # F = dA + A ∧ A

# 3. Lift to bundle
from src.python.lifts.s1_lift import S1LiftConstructor
lift = S1LiftConstructor()
A_lifted = lift.lift_connection(A)
```

**Critical**: Geometric objects are functions on configuration/phase space, not constants. Always evaluate at specific states.

### 4. Validation Data Flow
**Location**: `src/python/validation/`

All validation functions follow a standard interface:

```python
def validate_candidate(
    candidate_integral: Callable,
    test_trajectories: List[Trajectory],
    symbolic_form: Optional[sympy.Expr] = None
) -> ValidationReport:
    """
    Returns ValidationReport with:
    - passed: bool
    - metrics: dict (conservation error, rank deficiency, etc.)
    - plots: list of matplotlib figures
    - latex_summary: str (for manuscript)
    """
```

**Usage pattern**: Chain validators sequentially; early failure → stop cascade.

## Work Package-Specific Guidance

### WP1: High-Precision Integration
**Entry point**: `src/python/integrators/`

**Production pipeline**: Use `Snakefile` for large-scale runs:
```bash
# Tier 1: 10⁵ orbits, double precision
snakemake --cores 64 --config tier=1

# Tier 2: 10⁴ orbits, double-double precision
snakemake --cores 32 --config tier=2
```

Outputs HDF5 files → `data/tierN/hdf5/`, then converts to Parquet for ML (see `src/python/ml/parquet_export.py`).

**Chaos indicators**: Always compute MEGNO/FLI alongside trajectories (see `src/python/validation/chaos_indicators.py`). These classify orbits as regular/chaotic for stratified validation.

### WP2: Geometric Foundations
**Entry point**: `src/python/geometry/`, `src/python/lifts/`

**Key distinction**:
- **Mechanical connection** (A): Describes how rotations couple to translations. Computed from locked inertia tensor.
- **Symplectic connection**: On principal bundles. Used for lift constructions.

**Symbolic vs. Numerical**:
- Use `src/python/symbolic_lifts/ks_symbolic.py` for analytical Hamiltonian derivations (SymPy)
- Use `src/python/lifts/ks_regularization.py` for numerical integration in lifted space

**Visualization**: `src/python/visualization/` provides standardized plots:
- `connection_plots.py`: Vector field plots of connection 1-form
- `curvature_plots.py`: Heatmaps of curvature 2-form
- `metric_plots.py`: Geodesic deviation (chaos-curvature correlation)

### WP3: Invariant Discovery
**Entry point**: `src/python/symbolic/multi_stage_pipeline.py`

**Three-stage search**:
1. **Stage 1**: Spinor basis (~80 functions) → catches KS-lifted polynomial integrals
2. **Stage 2**: Elliptic basis (sn, cn, dn) → catches quasi-periodic integrals
3. **Stage 3**: Theta basis (θ₁₋₄) → targets complete integrability

**Coordinate all methods**: Pipeline runs symbolic regression, PDE solvers, and HNNs in parallel, then deduplicates results.

**Interpretability**: Use `src/python/symbolic/interpretability.py` to simplify discovered expressions (factorization, trigonometric identities).

### WP4: Validation
**Entry point**: `src/python/validation/analytical_vetting.py`

**Validation order** (do not skip stages):
1. Analytical vetting (WP4.1) - fastest, catches obvious issues
2. Morales-Ramis test (WP4.2) - theoretical obstruction, expensive
3. Monte Carlo robustness (WP4.3) - slowest, final confirmation

**Periodic orbit library**: `src/python/validation/periodic_orbits.py` provides known solutions:
- Lagrange L4/L5 (equilateral triangle)
- Euler collinear
- Figure-8 choreography
- Broucke orbits

Use these as test cases before validating novel candidates.

### WP5: Consolidation
**See**: `User-Guides/` for publication-ready documentation, `WP5-GAPS-FIX-PLAN.md` for remaining deliverables.

## Common Pitfalls

### 1. Coordinate System Confusion
**Problem**: Mixing Cartesian momenta with Jacobi coordinates.

**Solution**: Always check `state.coord_system` attribute. Use explicit transforms:
```python
from src.python.coordinates.transforms import cartesian_to_jacobi
state_jacobi = cartesian_to_jacobi(state_cartesian)
```

### 2. Symplectic Structure Violation
**Problem**: Manually editing state vectors without preserving symplectic form.

**Solution**: Use integrator methods or coordinate transform functions. If implementing new transforms, verify:
```python
from src.python.validation.conservation_validator import check_symplectic_form
assert check_symplectic_form(M_transform) < 1e-14
```

### 3. Regularization Threshold Tuning
**Problem**: Close encounters cause integration failures, but regularization too early wastes computation.

**Solution**: Use adaptive switching in `src/python/regularization/automatic_switching.py`. Default threshold: r < 0.01 Hill radii, backed by shadow Hamiltonian monitoring.

### 4. Double-Double Arithmetic Overhead
**Problem**: Tier 2 integrations are slow (~3-4× slower than double).

**Solution**: Only use double-double for:
- Final validation runs (not exploration)
- Orbits that fail Tier 1 precision (|ΔC/C| > 10⁻¹⁴)
- Morales-Ramis test (variational equations need high precision)

Exploration → use Tier 1 (standard double).

## Key Dependencies

### High-Precision Arithmetic
- **QD library** (C++): Provides `dd_real` (double-double, 31 digits). Built via CMake.
- **mpmath** (Python): Arbitrary precision fallback. Slower than QD, use only for symbolic validation.

### Symbolic Computation
- **SymPy**: All symbolic derivatives, Poisson brackets, Hamiltonian manipulations
- **SageMath** (optional): For Galois group computations in Morales-Ramis test

### Numerical Integration
- **REBOUND**: IAS15 integrator (adaptive 15th order)
- **Custom**: Adaptive symplectic integrator in `src/python/integrators/adaptive_symplectic.py`

### Machine Learning
- **PySR**: Symbolic regression (Julia backend)
- **PyTorch**: Hamiltonian Neural Networks
- **JAX**: Automatic differentiation for geometric computations

## Data Management

### Trajectory Storage
```
data/
├── tier1/           # 10⁵ orbits, |ΔC/C| < 10⁻¹⁴
│   ├── hdf5/        # Raw integration output (hierarchical by μ, C)
│   └── parquet/     # ML-ready format (flattened table)
└── tier2/           # 10⁴ orbits, |ΔC/C| < 10⁻²⁵
    ├── hdf5/
    └── parquet/
```

**Access pattern**:
```python
import h5py
with h5py.File('data/tier1/hdf5/orbit_mu05_C30_0042.h5', 'r') as f:
    t = f['time'][:]
    q = f['positions'][:]
    p = f['momenta'][:]
    megno = f.attrs['megno']
```

### Reproducibility
- All random sampling uses **Sobol sequences** (deterministic quasi-random)
- Lock random seeds in config: `src/python/ml/sobol_sampling.py`
- Tier 2 subset (100 orbits) has reference checksums: `reference/tier2_subset_seed42.npy`

## Documentation Structure

### Design Documents
- `Project-Design-Docs/OVERVIEW/`: High-level plans and theoretical framework
- `Project-Design-Docs/WP[1-5]/`: Task-specific implementation plans
- `Project-Design-Docs/Implementation-Status/`: Progress tracking

**Naming convention**:
- `AMENDED_` prefix: Revised documents with significant updates
- `WP[N].[M]` format: Work Package N, task M

### User Guides
- `User-Guides/User-Guide-WP[1-5].md`: Comprehensive usage guides for each work package
- `docs/WP2-USER-GUIDE.md`: Detailed geometric foundations tutorial

### Claude Agent Documentation
- `Claude-Agent-Docs/WPSkillsDocs/`: Skills and subagent definitions for each WP
- `Claude-Agent-Docs/4AbstractionAgentDocs/`: Agent architecture patterns

## Testing Philosophy

### Test Organization
```
tests/
├── python/              # Environment and basic functionality
├── regularization/      # WP1 time regularization
├── symbolic_lifts/      # WP2 lift constructions
├── wp3/                 # WP3 symbolic regression
└── validation/          # WP4 validation gauntlet
```

### Test Patterns
1. **Known solutions**: Test on Lagrange points, Figure-8 (exact solutions)
2. **Reversibility**: Integrate forward → reverse → backward, check |Δq| < 10⁻²⁰
3. **Conservation**: Monitor Jacobi constant drift over 10⁵ periods
4. **Symplectic structure**: Verify 2-form preserved by integrators

### Running Specific Tests
```bash
# Test KS symbolic Hamiltonian
pytest tests/symbolic_lifts/test_ks_symbolic.py -v

# Test Morales-Ramis validator
pytest tests/validation/test_morales_ramis_validator.py -v

# Test all WP3 components
pytest tests/wp3/ -v
```

## Performance Considerations

### Parallelization
- Use `Snakemake` for trajectory generation (embarrassingly parallel)
- Monte Carlo validation: Built-in multiprocessing in `monte_carlo_validator.py`
- Symbolic regression: PySR automatically uses multiple cores

### Memory Management
- Trajectories: Store only states at Poincaré section crossings (not every timestep)
- Dense output: Enable only for visualization, not validation (see `src/python/integrators/dense_output.py`)
- HDF5 compression: Use gzip level 6 for archival

### Profiling
```bash
# Profile Python code
python -m cProfile -o profile.stats scripts/run_benchmark.py
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"

# Benchmark C++ QD operations
./build/qd_benchmark
```

## Git Workflow

### Branch Naming
- Feature branches: `feature/wp2-ks-lift`
- Bug fixes: `bugfix/precision-overflow`
- Claude Code branches: `claude/<description>-<id>` (auto-generated)

### Pre-commit Failures
If pre-commit hooks modify files:
1. Review changes: `git diff`
2. Stage modified files: `git add <files>`
3. Re-commit: `git commit` (reuse message)

### Large Files
- Do not commit data files (`.h5`, `.parquet`) → add to `.gitignore`
- Exception: `reference/tier2_subset_seed42.npy` (100 orbits, ~8 MB, for reproducibility)

## Additional Resources

- **Theory background**: See `Science-Research-Docs/` for papers, lecture notes
- **Implementation reports**: `Project-Design-Docs/WP4/COMPLETE-IMPLEMENTATION-REPORT.md`
- **Gap analysis**: `WP5-GAPS-FIX-PLAN.md` for remaining deliverables
- **User guides**: Start with `User-Guides/README.md`

## Quick Command Reference

```bash
# Environment
mamba activate wp1_env
python verify_setup.py

# Build
./scripts/build_cpp.sh

# Test
./scripts/run_tests.sh
pytest tests/ -v

# Integration
snakemake --cores 64 --config tier=1  # Production run

# Validation
python examples/validate_chaos_indicators.py
python -m src.python.validation.analytical_vetting --candidate <expr>

# Formatting
black src/ tests/
flake8 src/ tests/

# Documentation
cd User-Guides && ls User-Guide-*.md
```
