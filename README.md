# Three-Body Problem Lift-Integrability Research

**A systematic search for hidden integrability in the Newtonian three-body problem via higher-dimensional symplectic embedding.**

---

## The Central Hypothesis

The three-body problem has resisted analytical solution for over 300 years. Classical proofs (Bruns 1887, Poincare 1890) established its non-integrability in standard coordinates. However, the **lift-integrability hypothesis** proposes that this non-integrability is an artifact of dimensional reduction:

> **Hidden conserved quantities may exist in appropriately constructed "upstairs" spaces that respect the system's geometric structure.**

This project systematically tests this hypothesis through:
1. **High-precision trajectory generation** (WP1)
2. **Geometric lift constructions** (WP2)
3. **ML-driven invariant discovery** (WP3)
4. **Rigorous mathematical validation** (WP4)
5. **Publication preparation** (WP5)

---

## Project Status

| Work Package | Description | Status | Completion |
|--------------|-------------|--------|------------|
| **WP1** | High-Precision Infrastructure | Qualified (scoped) | Separate CR3BP and full Newtonian N3BP propagation qualifications pass; native production-catalogue claim remains open |
| **WP2** | Geometric Foundations & Lifts | Qualified (scoped) | Canonical Kepler/KS and bounded three-body reduction/pairwise-KS composition qualifications pass; reduced N3BP dynamics and integrability claims remain open |
| **WP3** | Invariant Discovery (ML + Symbolic) | Prototype | Imports and collection repaired; publication claims not validated |
| **WP4** | Rigorous Validation ("The Gauntlet") | Prototype | Validation criteria need regenerated evidence |
| **WP5** | Consolidation & Publication | Designed | Pending validated results |

**Overall**: the codebase is an active research prototype with several bounded,
locked qualification records. The records are model-specific and do not combine
into a claim of integrability or native production-scale periodic-orbit catalogue
generation. See `notes/wp1-wp2-model-boundary.md` for the exact boundaries.

### Current WP1 Evidence

Latest clean-checkout validation on `bobs-mac-mini`: 2026-07-19.

- Qualification `WP1Q-v1-937694ba58a8` is `PASS`; development, calibration, and first-execution holdout each passed 39/39 locked gates.
- The pinned JPL source contains 67,218 records across Sun-Earth, Jupiter-Europa, Saturn-Titan, and Earth-Moon. The 400-record corpus covers Lyapunov/Halo families and four stability regimes, split 240/80/80 for development/calibration/holdout.
- Holdout: 80/80 float64 propagations, 36/36 independent 224-bit Taylor-oracle comparisons, 48/48 STM/Floquet cases, and 40/40 perturbed-seed reconstructions succeeded. Stability classification accuracy was 100%.
- `./scripts/run_tests.sh` passes: setup verification, clean collection of 843 tests, 104 focused WP1 tests, and 2/2 CTest QD checks. Bounded Linux/amd64 parity passes 12/12 evidence-bearing tests.
- Qualified Tier 1 regenerated 30 HDF5 orbits and all 630 Parquet rows at target `1e-14`; every artifact contains the qualification ID and hashes. One failed chaos-indicator solve is retained explicitly.
- Qualified Tier 2 regenerated 3 HDF5 orbits and all 9 Parquet rows at target `1e-25` using 160-bit `heyoka.real`; decimal high-precision states are preserved alongside float64 projections. Maximum relative Jacobi drift was `6.53e-28`.
- External JPL validation regenerated with 300 sampled JPL candidates from 21,938 fetched records: closure median `2.30e-11`, Jacobi drift median `4.44e-16`.
- JPL-seeded validation catalogue generated from the same 300 sampled external seeds: 284 accepted rows under closure `<= 1e-8` and absolute Jacobi drift `<= 1e-12`; accepted-catalogue closure median `2.01e-11`, 95th percentile `9.73e-10`, max `6.23e-09`.
- Small-amplitude native Lyapunov seeds now use a guarded differential corrector; the corrected Lyapunov convergence/closure diagnostic reports median closure `1.02e-12` and median Jacobi drift about `1.5e-16`.
- CR3BP rotating-frame reversibility now uses the correct reversing symmetry and passes the short-time `T=1` diagnostic with median position RMS `2.64e-16` and 100% Tier 1 pass rate.
- The legacy native candidate comparison is still not publication-ready as a broad generated catalogue: median state distance `8.37e-01` and median period error `8.90e-01`. The qualified representative corrector does not yet constitute family continuation or production-scale native generation.

The formal decision is in `validation-external/wp1-validation/reports/wp1_qualification_report.md` and `wp1_qualification_record.json`; downstream artifact evidence is in `wp1_qualified_artifact_audit.json`. The earlier Earth-Moon report remains at `wp1_external_validation_report.md`.

### Current Full-State and WP2 Evidence

- `WP1Q-N3BP-v1-892335b25187` is `PASS` for bounded collision-free 18D
  Newtonian three-body propagation. Its independent evidence includes analytic
  Lagrange conics, published rounded figure-eight and unequal-mass SJTU source
  states, and REBOUND IAS15 checkpoint comparisons.
- `WP2KSQ-v1-dc4b342e3bd2` is `PASS` for the canonical isolated
  negative-energy Kepler/KS cotangent lift, `S1` action, `Xi=0` quotient,
  fixed-energy Sundman transform, and regular oscillator. It does not cover a
  pair perturbed by a third body.
- `WP2-3BRQ-v1-d4c0d5d7e2e3` is `PASS` for the downstream composition:
  canonical Jacobi translation reduction, a generic non-collinear SO(3)
  quotient chart, and a constrained kinematic pairwise-KS lift with `S1^3`
  gauge invariance and closure.
- A clean bobs-mini checkout independently verifies all three relevant locks,
  passes 160/160 focused tests under Python 3.11, and replays downstream
  development and calibration at 24/24 gates. The supplemental parity record
  discloses a non-decision-bearing NumPy/Accelerate warning.
- The downstream result does not implement or qualify reduced Hamilton
  equations, a global three-body Sundman time, three decoupled Kepler
  oscillators, collision passage for the full N3BP, or a periodic-orbit
  catalogue.

The machine-readable records and human reports are under
`validation-external/wp1-n3bp-validation/reports/`,
`validation-external/wp2-ks-validation/reports/`, and
`validation-external/wp2-threebody-validation/reports/`.

---

## Quick Start

### 1. Environment Setup

```bash
# Create conda environment
mamba env create -f environment.yml
mamba activate wp1_env

# Install Python dependencies
poetry install

# Verify setup
python verify_setup.py
```

### 2. Build C++ Components

```bash
./scripts/build_cpp.sh
```

### 3. Run Tests

```bash
./scripts/run_tests.sh
```

### 4. Generate Your First Trajectory

```python
from src.python.integrators.ias15 import IAS15Integrator
import numpy as np

mu = 0.012150585609624  # Earth-Moon mass ratio
integrator = IAS15Integrator(mu=mu)
state0 = np.array([1.15, 0.0, 0.0, 0.0, 0.1, 0.0])  # x, y, z, vx, vy, vz

result = integrator.integrate(state0, duration=100.0, output_interval=0.1)
if not result.success:
    raise RuntimeError(result.message)
print(f"Generated {len(result.times)} trajectory points")
```

---

## Project Architecture

```
WP1 (Trajectories) --> WP2 (Geometry) --> WP3 (Discovery) --> WP4 (Validation) --> WP5 (Publication)
```

### WP1: High-Precision Infrastructure

Generates and validates CR3BP trajectory data. The scoped external qualification covers four physical systems, Lyapunov/Halo families, four stability regimes, independent high-precision propagation, analytic STM/Floquet stability, strict representative correction, and qualification-aware HDF5/Parquet output. Production-scale Tier 2 and native family generation/continuation remain outside the qualified claim.

- **Integrators**: IAS15 (adaptive Radau), Yoshida8 (symplectic), AdaptiveSymplectic (float64 prototype with precision guard), HeyokaTaylor (bounded arbitrary-precision Tier 2 smoke)
- **Chaos Detection**: MEGNO, FLI indicators
- **Validation**: Shadow Hamiltonian analysis, time reversibility tests
- **Production Pipeline**: Snakemake workflow for 10^5+ orbit generation

### WP2: Geometric Foundations

The qualified foundation is deliberately narrower than the project hypothesis.

- **Canonical Jacobi split**: Cartesian 18D -> center-of-mass canonical pair
  plus a 12D translation quotient
- **Rotation quotient**: generic non-collinear SO(3) orbit chart in a 9D
  Poisson space; a fixed nonzero angular-momentum magnitude selects an 8D leaf
- **Canonical KS prototype**: qualified isolated negative-energy Kepler
  cotangent lift, quotient, Sundman transform, and oscillator
- **Pairwise KS composition**: qualified 12D constrained kinematic lift of the
  three relative phase states, without a global Sundman or regularized N3BP
  dynamics claim
- **Still exploratory**: mechanical-connection dynamics, cohomological lifts,
  singular rotation charts, and hidden-integrability constructions

### WP3: Invariant Discovery

Multi-method search for hidden conserved quantities.

- **Symbolic Regression**: Spinor basis (~80 functions), elliptic functions (sn, cn, dn), theta functions
- **Machine Learning**: Hamiltonian Neural Networks, SINDy
- **Multi-Stage Pipeline**: Coordinates all discovery methods with automatic deduplication

### WP4: Rigorous Validation ("The Gauntlet")

Three-stage validation pipeline for candidate integrals:

1. **Analytical Vetting (WP4.1)**: Poisson brackets {I, H} = 0, involution tests, functional independence
2. **Morales-Ramis Test (WP4.2)**: Differential Galois theory obstruction
   - Phase I (Downstairs): Expects non-abelian Galois group (classical non-integrability)
   - Phase II (Upstairs): Seeks abelian Galois group (validates lift-integrability)
3. **Numerical Robustness (WP4.3)**: Monte Carlo (10^5 samples), stress tests, long-time validation

### WP5: Consolidation & Publication

Transforms validated results into publication-ready scientific contributions.

- **Target Journals**: Nature/Science (breakthrough), PRL (technical), CMDA (negative results)
- **Reproducibility**: GitHub, Zenodo archival, Docker/conda environments
- **Manuscript Generation**: LaTeX, publication-quality figures, arXiv preprint

---

## Documentation Guide

### For New Users

Start with the **User Guides** for comprehensive, tutorial-style documentation:

```
User-Guides/
├── README.md              # Overview and quick navigation
├── User-Guide-WP1.md      # Trajectory generation
├── User-Guide-WP2.md      # Geometric foundations
├── User-Guide-WP3.md      # Invariant discovery
├── User-Guide-WP4.md      # Validation pipeline
└── User-Guide-WP5.md      # Publication preparation
```

**Recommended reading order**: WP1 -> WP2 -> WP3 -> WP4 -> WP5

### For Implementers

Consult **Project Design Docs** for detailed implementation plans:

```
Project-Design-Docs/
├── OVERVIEW/              # Project overview and theoretical framework
│   ├── Project-Overview.md           # START HERE for project scope
│   ├── KS-Conjectural-Statement.md   # Theoretical hypothesis
│   └── Compute-Requirements-Analysis.md
├── WP1/                   # Trajectory generation specs
├── WP2/                   # Geometric construction specs
├── WP3/                   # Discovery method specs
├── WP4/                   # Validation pipeline specs
├── WP5/                   # Publication pipeline specs
└── Implementation-Status/ # Current progress tracking
```

### For Researchers

Review **Science Research Docs** for mathematical foundations:

```
Science-Research-Docs/
├── WP1 - Foundations: Symplectic Reduction, Moment Maps...
├── WP2 - 2-Body Kepler + KS: Prototype Testbed...
├── WP3 - Generalized KS Transformations...
├── WP4 - Geometric & Cohomological Lifts...
├── Transforming Hamiltonian Variational Equations.pdf
├── Abelianizing Variational Equations...
└── Synthesis/             # Combined analysis
```

---

## Using Claude Code Agents

This project includes 12 specialized AI agents and 11 skills for complex scientific computing tasks.

### Quick Examples

```
"Generate 1000 high-precision trajectories"
→ Routes to wp1-lab-director agent

"Build the KS spinor lift construction"
→ Routes to wp2-architect agent

"Search for conserved quantities"
→ Routes to wp3-investigator agent

"Validate this candidate integral: u1**2 + u2**2"
→ Routes to wp4-mathematician agent

"Prepare manuscript for PRL submission"
→ Routes to wp5-author agent
```

### Agent Architecture

| Agent | Role |
|-------|------|
| `wp1-lab-director` | Trajectory generation and validation |
| `wp2-architect` | Geometric construction (lifts, bundles) |
| `wp2-analyst` | Geometric verification (curvature, integrability) |
| `wp3-investigator` | Integral discovery (PDE, ML, symbolic) |
| `wp3-consolidator` | Result filtering and ranking |
| `wp4-mathematician` | Analytical validation (Morales-Ramis) |
| `wp4-stress-tester` | Numerical robustness testing |
| `wp5-author` | Manuscript writing |
| `wp5-librarian` | Code release and archival |
| `research-orchestrator` | Multi-WP strategic planning |

Agents are defined in `.claude/agents/` and skills in `.claude/skills/`.

---

## Directory Structure

```
3body/
├── src/
│   ├── python/            # Python implementation
│   │   ├── integrators/   # Trajectory integrators
│   │   ├── coordinates/   # Coordinate transforms
│   │   ├── geometry/      # Connection, curvature
│   │   ├── lifts/         # S^1, KS-Spinor lifts
│   │   ├── symbolic/      # Symbolic regression
│   │   ├── ml/            # Neural network discovery
│   │   ├── validation/    # Validation pipeline
│   │   └── publication/   # Manuscript generation
│   └── cpp/               # High-precision C++ (QD library)
├── tests/                 # Test suite
├── notebooks/             # Jupyter notebooks
├── examples/              # Example scripts
├── data/                  # Generated trajectories
├── User-Guides/           # Tutorial documentation
├── Project-Design-Docs/   # Implementation specifications
├── Science-Research-Docs/ # Mathematical foundations
├── Dry-Run/               # Integration test runs
└── .claude/               # Agent definitions and skills
```

---

## Key Commands

```bash
# Environment
mamba activate wp1_env
python verify_setup.py

# Build
./scripts/build_cpp.sh

# Test
./scripts/run_tests.sh
pytest tests/ -v

# Production trajectory generation
snakemake --cores 64 --config tier=1

# Code quality
pre-commit run --all-files
```

---

## Development

### Code Quality

Pre-commit hooks enforce:
- **Black**: Code formatting (line length: 88)
- **Flake8**: Linting
- **Trailing whitespace** and **end-of-file** checks

### Path Handling

**Always work from project root:**

```bash
cd /path/to/3body
python scripts/validate_working_dir.py  # Verify location
```

### Testing

```bash
# Python tests
pytest tests/ -v

# Specific work package
pytest tests/wp3/ -v

# With coverage
pytest tests/ --cov=src/python --cov-report=html
```

---

## Citation

```bibtex
@software{3body_integrability_2025,
  author = {Sullivan, Jacob},
  title = {Three-Body Problem Integrability Research: A Systematic Search
           via Higher-Dimensional Symplectic Embedding},
  year = {2025},
  url = {https://github.com/jacobrsullivan/3body}
}
```

---

## Resources

### Documentation

- [User Guides](User-Guides/README.md) - Start here for tutorials
- [Project Design Docs](Project-Design-Docs/README.md) - Implementation details
- [CLAUDE.md](CLAUDE.md) - Technical reference for development

### Key References

- Bruns (1887), "On the integrals of the many-body problem"
- Poincare (1890), "Sur le probleme des trois corps"
- Morales-Ruiz & Ramis (2001), "Galoisian obstructions to integrability"
- Marsden & Ratiu (1999), *Introduction to Mechanics and Symmetry*

---

**Questions?** Start with [User-Guides/README.md](User-Guides/README.md) or consult the relevant work package guide.
