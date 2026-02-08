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
| **WP1** | High-Precision Infrastructure | Complete | 100% |
| **WP2** | Geometric Foundations & Lifts | Partial | ~70% |
| **WP3** | Invariant Discovery (ML + Symbolic) | Complete | 100% |
| **WP4** | Rigorous Validation ("The Gauntlet") | Complete | 100% |
| **WP5** | Consolidation & Publication | Designed | Pending Results |

**Overall**: ~80% complete. Infrastructure and discovery pipelines are operational. Publication awaits validation of candidate integrals.

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

times, states = integrator.integrate(state0, t_span=(0, 100), dt=0.1)
print(f"Generated {len(times)} trajectory points")
```

---

## Project Architecture

```
WP1 (Trajectories) --> WP2 (Geometry) --> WP3 (Discovery) --> WP4 (Validation) --> WP5 (Publication)
```

### WP1: High-Precision Infrastructure

Generates validated CR3BP trajectory catalogues with unprecedented precision.

- **Integrators**: IAS15 (adaptive Radau), Yoshida8 (symplectic), AdaptiveSymplectic (double-double precision)
- **Chaos Detection**: MEGNO, FLI indicators
- **Validation**: Shadow Hamiltonian analysis, time reversibility tests
- **Production Pipeline**: Snakemake workflow for 10^5+ orbit generation

### WP2: Geometric Foundations

Creates the mathematical framework for lifting phase space.

- **Coordinate Systems**: Cartesian (18D) -> Jacobi (15D) -> Shape Space (12D)
- **Mechanical Connection**: Computes connection 1-form A and curvature 2-form F
- **S^1 Bundle Lift**: Minimal cohomological "untwisting" of connection
- **KS-Spinor Lift**: Kustaanheimo-Stiefel regularization for collision handling

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
