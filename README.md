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
| **WP1** | High-Precision Infrastructure | Qualified (scoped) | WP1-CAT-N3BP-v1 qualifies native production of one 169-member planar N3BP family in full 18D states; other families and a general catalogue remain open |
| **WP2** | Geometric Foundations & Lifts | Qualified (scoped) | WP2-MULTIQ-v1 qualifies a three-chart fixed-energy KS atlas with continuation through every isolated binary-collision channel; triple collision and broader reductions remain open |
| **WP3** | Invariant Discovery (ML + Symbolic) | Qualified bounded null | WP3-MULTI-CAND-v2-KQ-v1 finds no eligible direction after quotienting known `L^2` in its frozen 285-function physical library; this is not a general no-integral theorem |
| **WP4** | Rigorous Validation ("The Gauntlet") | Qualified (project-owned, scoped) | WP4-MR-REPL-v1 exactly reproduces the local planar Morales-Ramis obstruction; WP4-LIFT-NI-v3 transfers it to the spatial model and rules out shell-regular physically admissible meromorphic Liouville families on the qualified KS atlas |
| **WP5** | Consolidation & Publication | Evidence chain ready | Manuscript synthesis, external peer review, and archival release remain pending |

**Overall**: the codebase is an active research prototype with several bounded,
locked qualification records. The records are model-specific and do not combine
into a claim of integrability or a complete/general periodic-orbit catalogue.
See `notes/wp2-multi-wp1-cat-n3bp-result.md`, `notes/wp1-wp2-model-boundary.md`,
`notes/wp4-mr-repl-v1-result.md`, and `notes/wp4-lift-ni-v3-result.md` for the
exact boundaries.

### Current WP1 Evidence

Latest clean-checkout qualification parity on `bobs-mac-mini`: 2026-07-21.

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
- The legacy native candidate comparison remains non-qualifying and is retained
  as historical evidence. It is superseded for the bounded N3BP family claim by
  `WP1-CAT-N3BP-v1` below.

`WP1-CAT-v1-5dc7ad44b78f` separately qualifies an external-orbit-seed-free
continuation component for fixed Earth-Moon planar L1/L2 Lyapunov grids. It
generated 159 corrected, Floquet-labelled candidates with maximum one-period
closure `4.25e-12`. All 300 partitioned JPL rows had a nearest-neighbor native
match within frozen tolerances, selecting 138 distinct native members. This is
sampled family-curve agreement, not one-to-one recovery or catalogue
completeness; the disjoint holdout was execution-reserved, not independently
blinded, and all comparison rows share one strongly-unstable class.

`WP1-CAT-N3BP-v1-605c6dbd59d1` is `PASS` for a native 169-member
`bABabaBAba` planar N3BP family on the frozen two-dimensional mass grid. The
source-free candidate was frozen before restoring the selected external rows.
All 168 exact-mass comparison cases passed their locked development,
calibration, and first-execution holdout gates (84/42/42), including full-state
closure, invariant drift, reduced-planar Floquet diagnostics, one-to-one
Li-Li-Liao/SJTU conformance, and REBOUND cross-integration. This is native
correction and continuation from one disclosed published equal-mass root, not
independent root discovery, completeness, spatial-family production, or a
general N3BP catalogue.

`WP1-RESIDUAL-MAP-v1-9526e09d01ba` maps all 169 qualified members into
publication-gated follow-on tracks: 118 local stable normal-form cases, 51
asymptotic-manifold cases, and one exact higher-variational overlay. The map is
deterministic and independently reproduced. It does not identify an invariant,
establish KAM stability, construct a manifold, or widen the catalogue claim.

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
- `WP2-UPQ-v2-3baea4a70768` is `PASS` for the canonical one-channel
  fixed-energy KS lift of the translation-reduced N3BP. It verifies projection
  of the upstairs Hamiltonian vector field, `S1`/`Xi` structure, projected
  angular momentum, and regular passage through the selected binary collision.
- `WP2-MULTIQ-v1-72c81d86644a` is `PASS` for the fixed-energy extended-
  canonical three-chart, two-spinor KS atlas. It qualifies the `T^2` gauge
  action in each chart, the chart-independent product Sundman law, canonical
  quotient transitions, automatic smallest-pair chart switching, and smooth
  fictitious-time continuation through each isolated binary-collision channel.
  Triple collision, simultaneous pair collisions, nonzero-`Xi` magnetic
  reduction, SO(3) reduction, and additional integrals remain outside scope.
- Earlier one-channel bobs-mini parity verifies the WP1-N3BP, WP2-KS, and
  WP2-UP-v2 locks, passes 160/160 focused tests under Python 3.11, and replays
  development and calibration at 24/24 gates.
- The 2026-07-21 clean checkout also verifies the WP1-CAT-N3BP-v1 and
  WP2-MULTIQ-v1 locks and passes 192/192 relevant tests. This is supplemental
  portability evidence: JAX 0.9.0.1 had to be installed explicitly because the
  frozen repository environment omits that independent-reference dependency.
  Nine older-NumPy matmul warnings are disclosed in
  `notes/wp2-multi-wp1-cat-n3bp-bobs-parity.md`.
- The earlier pairwise-KS composition record remains only a constrained
  kinematic result. The newer multi-chart record supersedes it for the declared
  atlas and isolated-collision claims, but does not claim three decoupled Kepler
  oscillators, triple-collision regularization, or integrability.

The machine-readable records and human reports are under
`validation-external/wp1-n3bp-validation/reports/`,
`validation-external/wp2-ks-validation/reports/`, and
`validation-external/wp2-threebody-validation/reports/`. The new catalogue and
multi-chart records are under
`validation-external/wp1-catalogue-n3bp-validation/reports/` and
`validation-external/wp2-multi-validation/reports/`.

### Current WP3 and WP4 Evidence

- `WP3-UP-CAND-v2` is retained as negative-control evidence only. It failed to
  quotient exact parameter-weighted angular momenta and therefore does not
  establish its advertised finite-library null result.
- `WP3-UP-CAND-v3` replaced approximate value-identity removal with an exact
  rank-30 coefficient quotient: 18 generators of the degree-three `Xi=0`
  constraint ideal and 12 represented angular-momentum parameter-module
  generators. `WP3-UP-CAND-v3-2979adbb0597` passed 15/15 readiness gates and
  produced a basis-invariant bounded null: its backend-guarded minimum
  generalized singular value is `1.63949e-4`, versus the `1e-10` candidate
  threshold, across all 1,090 observable quotient directions.
- That older bounded-null search remains tied to `WP2-UPQ-v2`, the one-channel
  model. It is retained as scoped historical evidence rather than transferred
  to the newer atlas.
- `WP3-MULTI-CAND-v1-225359a13711` is the first qualified search on
  `WP2-MULTIQ-v1-72c81d86644a`. It passed 21/21 readiness gates and found no
  candidate in its frozen shared degree-three quotient.
- The successor physical-library search produced one apparent direction.
  `WP3-MULTI-CAND-v2-RES-v2-1277d77b2a25` proved that it was exactly the known
  total-angular-momentum-squared class. After removing that complete observable
  equivalence class, `WP3-MULTI-CAND-v2-KQ-v1-514be9de7232` found zero further
  candidate subspaces in the frozen 285-function library. Its publication gate
  is `PASS_BOUNDED_NULL_ONLY`; this is not a general nonintegrability theorem.
- `WP4-UP-READY-v3-696827675bff` remains the qualified historical one-channel
  control harness. It did not validate a candidate or establish integrability.
- `WP4-MR-NI-v2-4eb909c77a41` conditionally applies two pinned published
  analyses to the positive-mass planar problem near the nonzero-angular-
  momentum parabolic Lagrange solution. It consumes rather than independently
  rederives the published 4x4 NVE and Galois/monodromy computation and is
  retained as predecessor evidence.
- `WP4-LIFT-NI-v2-8d553cb1fa7f` passes 19/19 gates, 10/10 theorem
  obligations, and 6/6 negative controls. It proves the spatial variational
  subquotient and the KS quotient, Sundman, chart, involution, and shell-rank
  transfers. Conditional on the pinned planar result, it rules out complete
  shell-regular physically admissible meromorphic Liouville families on any
  qualified atlas domain containing the obstructed regular neighborhood.
- `WP4-MR-REPL-v1-2ea23024c64b` replaces the external mathematical premise.
  Two source-disjoint exact implementations derive the parabolic Lagrange
  phase curve, planar variational equation, Whittaker reduction, 4x4 Fuchsian
  NVE, and residue spectra from the declared reduced Hamiltonian. All 10
  theorem obligations, 13 source contracts, 7 published-equivalence checks,
  four exact specializations, and nine adversarial controls pass. The
  positive-mass complete-integrability exceptional set is empty.
- `WP4-LIFT-NI-v3-9ba955931b23` passes all 21 gates, 10 transfer obligations,
  and eight adversarial controls. It reruns the hash-identical v2
  KS/quotient/Sundman/rank/spatial-subquotient certificate and replaces the
  unreplicated planar premise with `WP4-MR-REPL-v1`. The resulting theorem is
  local, meromorphic, fixed-nonzero-angular-momentum, and claim-bounded; it is
  not a statement that no additional integral exists.
- A clean bobs-mac-mini checkout verifies the WP1-CAT, WP3-v3, and WP4-v3
  records and passes 42/42 applicable tests. Its explicitly non-decision full
  WP3 replay has byte-identical input matrices, zero candidates, and a guarded
  lower bound within `3.50e-14` of the authoritative run; older-stack NumPy
  warnings are disclosed in `notes/wp3-up-cand-v3-bobs-parity.md`.
- The same host verifies the WP1-CAT-N3BP-v1, WP2-MULTIQ-v1, and
  WP3-MULTI-CAND-v1 locks and passes the 235/235 multi-chart dependency-chain
  tests. Its Python 3.11/NumPy 2.2 runtime does not match the frozen decision
  runtime, so the search was not replayed and this is non-voting portability
  evidence. Thirty older-stack matmul warnings are disclosed in
  `notes/wp3-multi-cand-v1-bobs-parity.md`.

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

Generates and validates CR3BP and bounded N3BP trajectory data. The scoped
external qualification covers four CR3BP physical systems, Lyapunov/Halo
families, four stability regimes, independent high-precision propagation,
analytic STM/Floquet stability, strict representative correction, and
qualification-aware HDF5/Parquet output. WP1-CAT-v1 additionally qualifies two
fixed native Earth-Moon planar Lyapunov continuation segments.
WP1-CAT-N3BP-v1 qualifies one 169-member planar N3BP family in full 18D states.
General family discovery, other topologies, spatial families, and catalogue
completeness remain outside the qualified claims.

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
- **Multi-chart KS atlas**: qualified fixed-energy three-chart dynamics with a
  product Sundman law, canonical overlap maps, smallest-pair switching, and
  isolated binary-collision continuation in all three physical channels
- **Still exploratory**: mechanical-connection dynamics, cohomological lifts,
  singular rotation charts, triple collision, and hidden-integrability
  constructions

### WP3: Invariant Discovery

Multi-method search for hidden conserved quantities.

The prior parameter-aware campaign is invalidated because it failed a
known-control recovery audit. Qualified searches remove represented known
modules before generalized Lie/value screening, require gauge and chart
agreement, and guard backend-dependent singular values. The latest physical
quotient search resolved its apparent direction as known `L^2`, then found no
further eligible direction in the frozen 285-function library. That bounded
finite-library null does not imply that no additional first integral exists.

- **Symbolic Regression**: Spinor basis (~80 functions), elliptic functions (sn, cn, dn), theta functions
- **Machine Learning**: Hamiltonian Neural Networks, SINDy
- **Multi-Stage Pipeline**: Coordinates all discovery methods with automatic deduplication

### WP4: Rigorous Validation ("The Gauntlet")

Three-stage validation pipeline for candidate integrals:

The v3 readiness campaign verifies the historical one-channel candidate
control harness. No WP3 candidate survived the qualified multi-chart searches,
so candidate-specific qualification remains untriggered. A separately locked
Morales-Ramis and transfer track has now reproduced and qualified a scoped
nonintegrability result for the physical model and for shell-regular physically
admissible families on the KS atlas.

1. **Analytical Vetting (WP4.1)**: Poisson brackets {I, H} = 0, involution tests, functional independence
2. **Morales-Ramis Test (WP4.2)**: Differential Galois theory obstruction
   - Downstairs: `WP4-MR-REPL-v1` independently reproduces the exact local planar obstruction
   - Transfer: `WP4-LIFT-NI-v3` proves the spatial subquotient and shell-regular KS descent obstruction
   - An Abelian variational Galois identity component is necessary for meromorphic Liouville integrability, not sufficient evidence of integrability
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
