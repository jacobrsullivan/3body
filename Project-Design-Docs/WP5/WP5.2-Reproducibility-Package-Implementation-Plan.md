# WP 5.2: Reproducibility Package
## Complete Implementation Plan

**Duration**: 7-10 days
**Prerequisites**: WP 5.1 In Progress (Formal results available)
**Objective**: Create a comprehensive, independently verifiable reproducibility package enabling any researcher to replicate all main results

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Task 5.2.1: Code Organization and Documentation](#task-521-code-organization-and-documentation)
4. [Task 5.2.2: Data Artifact Curation](#task-522-data-artifact-curation)
5. [Task 5.2.3: Computational Environment Specification](#task-523-computational-environment-specification)
6. [Task 5.2.4: Testing and Validation Suite](#task-524-testing-and-validation-suite)
7. [Integration Strategy](#integration-strategy)
8. [Publication and Archival](#publication-and-archival)
9. [Deliverables](#deliverables)

---

## Overview

### Purpose

WP 5.2 creates a **gold-standard reproducibility package** that enables independent verification of all results. In an era of replication crises, this package ensures our work meets the highest standards of open science.

### The Reproducibility Standard

**Any researcher with this package should be able to**:

1. **Reproduce Main Results**: Generate all figures and tables in the paper
2. **Verify Claims**: Run validation tests independently
3. **Extend Methods**: Apply techniques to new problems
4. **Understand Implementation**: Comprehend all technical details

**Guiding Principle**: "Reproducibility by Default, Not by Request"

---

## Architecture

### Four-Task Pipeline

```
WP 5.2: Reproducibility Package (4 parallel + sequential tasks)
│
├── Task 5.2.1: Code Organization and Documentation (3-4 days)
│   ├── Repository structure design
│   ├── Code cleanup and refactoring
│   ├── API documentation (docstrings)
│   └── User guides and tutorials
│
├── Task 5.2.2: Data Artifact Curation (2-3 days)
│   ├── Select representative datasets
│   ├── Format and compress data
│   ├── Generate metadata
│   └── Archive with DOI
│
├── Task 5.2.3: Computational Environment (1-2 days)
│   ├── Dependency specification
│   ├── Docker container (optional)
│   ├── Conda environment
│   └── CI/CD setup
│
└── Task 5.2.4: Testing and Validation Suite (2-3 days)
    ├── Unit tests
    ├── Integration tests
    ├── Validation tests (reproduce main results)
    └── Performance benchmarks
```

**Dependencies**: Tasks 5.2.1-5.2.3 can overlap; 5.2.4 depends on 5.2.1 completion.

---

## Task 5.2.1: Code Organization and Documentation

**Duration**: 3-4 days
**Objective**: Transform research code into production-quality, documented software

### Implementation Details

#### Part A: Repository Structure Design (0.5 days)

**Canonical Repository Layout**:

```
3body-lift-integrability/
│
├── README.md                          # Project overview, quick start
├── LICENSE                            # MIT or BSD-3-Clause
├── CITATION.cff                       # Citation metadata
├── pyproject.toml / setup.py          # Package configuration
├── requirements.txt                   # Python dependencies
├── environment.yml                    # Conda environment
├── .github/                           # GitHub-specific files
│   ├── workflows/                     # CI/CD pipelines
│   └── ISSUE_TEMPLATE.md              # Bug report template
│
├── src/                               # Source code
│   ├── __init__.py
│   ├── python/
│   │   ├── __init__.py
│   │   ├── wp1_integration/           # High-precision integrators
│   │   │   ├── __init__.py
│   │   │   ├── symplectic.py          # Symplectic integrators
│   │   │   ├── regularization.py      # KS, Sundman time
│   │   │   └── adaptive.py            # Adaptive timestepping
│   │   │
│   │   ├── wp2_geometric/             # Lifts and reductions
│   │   │   ├── __init__.py
│   │   │   ├── coordinates.py         # Coordinate transforms
│   │   │   ├── reduction.py           # Symplectic reduction
│   │   │   ├── s1_bundle.py           # S¹ untwisting lift
│   │   │   ├── ks_spinor.py           # KS-Spinor lift
│   │   │   └── connection.py          # Connection and curvature
│   │   │
│   │   ├── wp3_discovery/             # Invariant discovery
│   │   │   ├── __init__.py
│   │   │   ├── geometric/             # Killing fields
│   │   │   ├── ml/                    # HNN, SympNets
│   │   │   └── symbolic/              # Symbolic regression
│   │   │
│   │   ├── wp4_validation/            # Validation framework
│   │   │   ├── __init__.py
│   │   │   ├── poisson_brackets.py    # Analytical vetting
│   │   │   ├── morales_ramis.py       # MR test
│   │   │   └── monte_carlo.py         # Numerical robustness
│   │   │
│   │   ├── wp5_analysis/              # Result analysis
│   │   │   ├── __init__.py
│   │   │   ├── figures.py             # Figure generation
│   │   │   └── statistics.py          # Statistical analysis
│   │   │
│   │   └── utils/                     # Shared utilities
│   │       ├── __init__.py
│   │       ├── constants.py           # Physical constants
│   │       └── io.py                  # I/O helpers
│   │
│   └── julia/                         # (Optional) High-performance code
│       └── [Julia implementations]
│
├── data/                              # Data artifacts
│   ├── README.md                      # Data documentation
│   ├── trajectories/                  # Sample trajectory data
│   ├── integrals/                     # Discovered invariants
│   ├── validation/                    # Validation results
│   └── raw/                           # Raw data (large, not in repo)
│
├── notebooks/                         # Jupyter notebooks
│   ├── 00_quick_start.ipynb          # 10-minute intro
│   ├── 01_introduction.ipynb         # Background
│   ├── 02_wp1_integration.ipynb      # High-precision integration
│   ├── 03_wp2_lifts.ipynb            # Symplectic lifts
│   ├── 04_wp3_discovery.ipynb        # Invariant discovery
│   ├── 05_wp4_validation.ipynb       # Validation framework
│   ├── 06_main_results.ipynb         # Main theorem verification
│   └── 07_reproduce_figures.ipynb    # Reproduce all paper figures
│
├── tests/                             # Test suite
│   ├── __init__.py
│   ├── test_wp1/                      # WP1 tests
│   ├── test_wp2/                      # WP2 tests
│   ├── test_wp3/                      # WP3 tests
│   ├── test_wp4/                      # WP4 tests
│   └── test_integration/              # Full pipeline tests
│
├── docs/                              # Documentation
│   ├── index.md                       # Documentation homepage
│   ├── installation.md                # Installation guide
│   ├── quickstart.md                  # Quick start tutorial
│   ├── api/                           # API reference
│   │   ├── wp1.md
│   │   ├── wp2.md
│   │   └── ...
│   ├── tutorials/                     # Step-by-step guides
│   │   ├── integration.md
│   │   ├── lifts.md
│   │   └── ...
│   └── theory/                        # Mathematical background
│       ├── symplectic_geometry.md
│       ├── integrability.md
│       └── ...
│
├── scripts/                           # Executable scripts
│   ├── reproduce_main_results.py     # One-click reproduction
│   ├── generate_all_figures.py       # Generate all paper figures
│   ├── run_validation_suite.py       # Run full validation
│   └── benchmark.py                   # Performance benchmarks
│
└── docker/                            # Docker configuration
    ├── Dockerfile                     # Container definition
    └── docker-compose.yml             # Multi-container setup
```

**Design Principles**:
1. **Modular**: Each WP is a separate subpackage
2. **Discoverable**: Clear naming, logical hierarchy
3. **Documented**: README in every major directory
4. **Tested**: Test directory mirrors source structure

---

#### Part B: Code Cleanup and Refactoring (1-2 days)

**Cleanup Checklist**:

**1. Remove Dead Code**:
```bash
# Identify unused functions
pytest --cov=src --cov-report=term-missing

# Remove commented-out code blocks
# Remove debugging print statements
# Remove temporary/experimental code
```

**2. Standardize Code Style**:
```bash
# Format with black (Python)
black src/ tests/

# Lint with flake8
flake8 src/ tests/ --max-line-length=100

# Type hints with mypy
mypy src/ --ignore-missing-imports
```

**3. Refactor for Clarity**:
- Extract magic numbers into constants
- Split long functions (>50 lines) into smaller units
- Use descriptive variable names (no `x1`, `tmp`, `arr`)
- Add type hints to all public functions

**Example Refactoring**:

**Before**:
```python
def f(x, y, t=0.01, n=1000):
    arr = []
    for i in range(n):
        x = x + t * (-y)
        y = y + t * x
        arr.append((x, y))
    return arr
```

**After**:
```python
from typing import List, Tuple
import numpy as np

def integrate_harmonic_oscillator(
    initial_position: float,
    initial_velocity: float,
    timestep: float = 0.01,
    num_steps: int = 1000
) -> List[Tuple[float, float]]:
    """
    Integrate the harmonic oscillator using symplectic Euler.

    Args:
        initial_position: Initial position q(0)
        initial_velocity: Initial velocity p(0)
        timestep: Integration timestep (default: 0.01)
        num_steps: Number of integration steps (default: 1000)

    Returns:
        trajectory: List of (q, p) tuples along trajectory
    """
    trajectory = []
    q, p = initial_position, initial_velocity

    for _ in range(num_steps):
        q += timestep * p
        p += timestep * (-q)
        trajectory.append((q, p))

    return trajectory
```

---

#### Part C: API Documentation (1 day)

**Docstring Standard: NumPy Style**

**Template**:
```python
def poisson_bracket(
    f: sp.Expr,
    g: sp.Expr,
    coordinates: List[sp.Symbol],
    momenta: List[sp.Symbol]
) -> sp.Expr:
    """
    Compute the Poisson bracket {f, g} symbolically.

    The Poisson bracket is defined as:
        {f, g} = Σᵢ (∂f/∂qᵢ ∂g/∂pᵢ - ∂f/∂pᵢ ∂g/∂qᵢ)

    Parameters
    ----------
    f : sympy.Expr
        First function (symbolic expression in q, p)
    g : sympy.Expr
        Second function (symbolic expression in q, p)
    coordinates : list of sympy.Symbol
        Canonical coordinates [q₀, q₁, ..., qₙ]
    momenta : list of sympy.Symbol
        Canonical momenta [p₀, p₁, ..., pₙ]

    Returns
    -------
    bracket : sympy.Expr
        The Poisson bracket {f, g} as a symbolic expression

    Examples
    --------
    >>> import sympy as sp
    >>> q, p = sp.symbols('q p')
    >>> H = p**2 / 2 + q**2 / 2  # Harmonic oscillator
    >>> I = p**2 / 2 - q**2 / 2  # Non-conserved
    >>> pb = poisson_bracket(H, I, [q], [p])
    >>> sp.simplify(pb)
    2*p*q

    Notes
    -----
    - For conservation, the bracket with the Hamiltonian must vanish: {I, H} = 0
    - Antisymmetry: {f, g} = -{g, f}
    - Leibniz rule: {fg, h} = f{g,h} + g{f,h}

    References
    ----------
    .. [1] Arnold, V. I. "Mathematical Methods of Classical Mechanics" (1989)
    """
    bracket = sum(
        sp.diff(f, q) * sp.diff(g, p) - sp.diff(f, p) * sp.diff(g, q)
        for q, p in zip(coordinates, momenta)
    )
    return sp.simplify(bracket)
```

**Coverage Target**: 100% of public API, 80% of internal functions

**Documentation Generation**:
```bash
# Use Sphinx to generate HTML docs
cd docs/
sphinx-apidoc -o api/ ../src/python/
make html

# Host on Read the Docs (automatic from GitHub)
```

---

#### Part D: User Guides and Tutorials (1 day)

**Tutorial Structure**:

**Tutorial 1: Installation and Setup (15 minutes)**
```markdown
# Installation Guide

## Prerequisites
- Python 3.9+
- 8 GB RAM (16 GB recommended)
- Linux, macOS, or Windows with WSL

## Quick Install
```bash
# Clone repository
git clone https://github.com/username/3body-lift-integrability.git
cd 3body-lift-integrability

# Install dependencies
pip install -e .

# Run tests to verify installation
pytest tests/
```

## Verify Installation
```python
import src.python.wp1_integration as wp1
print("Installation successful!")
```
```

**Tutorial 2: Basic Integration (30 minutes)**
- Integrate a simple 3-body trajectory
- Visualize the orbit
- Check energy and angular momentum conservation

**Tutorial 3: Constructing the S¹ Lift (45 minutes)**
- Reduced coordinates
- Computing the connection form
- Lifted Hamiltonian
- Verifying projection

**Tutorial 4: Discovering Integrals (1 hour)**
- Killing field search
- HNN training
- Symbolic regression

**Tutorial 5: Validating an Integral (1 hour)**
- Poisson bracket computation
- Monte Carlo validation
- Morales-Ramis test

**Tutorial 6: Reproducing Paper Results (2 hours)**
- Load discovered integral
- Run validation suite
- Generate all figures

**Format**: Jupyter notebooks in `notebooks/` directory

---

## Task 5.2.2: Data Artifact Curation

**Duration**: 2-3 days
**Objective**: Select, format, and archive datasets for independent verification

### Implementation Details

#### Part A: Dataset Selection (0.5 days)

**Guiding Principles**:
1. **Representativeness**: Cover full parameter space
2. **Manageability**: Balance completeness with file size
3. **Accessibility**: Standard formats (HDF5, CSV, JSON)

**Selected Datasets**:

**Dataset 1: Representative Trajectories** (~1 GB)
- 1000 trajectories covering parameter space
- Format: HDF5 with metadata
- Contents:
  - Initial conditions (mass, E, L, positions, velocities)
  - Trajectory: `(t, q, p, θ, p_θ)` at each timestep
  - Computed integrals: `E(t), L(t), I(t)`
  - Metadata: integrator, timestep, duration

**Dataset 2: Validated Integrals** (~10 MB)
- Symbolic expressions (SymPy format)
- Numerical evaluation functions (Python/Julia)
- Format: JSON + Python pickles
- Contents:
  - Integral expression (symbolic)
  - Evaluation function (callable)
  - Discovery method (geometric/ML/symbolic)
  - Validation results (WP 4.1-4.3 summaries)

**Dataset 3: Validation Results** (~100 MB)
- WP 4.1: Poisson bracket computations
- WP 4.2: Morales-Ramis results
- WP 4.3: Monte Carlo statistics
- Format: CSV (tables), JSON (metadata)

**Dataset 4: Geometric Data** (~500 MB)
- Connection forms `A(q)`
- Curvature two-forms `σ = dA`
- JM metric components `g_JM(q)`
- Format: HDF5 (arrays on meshes)

**Dataset 5: Publication Figures** (~50 MB)
- All figures from paper in high resolution
- Source data for each figure
- Format: PDF/SVG (figures), CSV/JSON (data)

**Total Size**: ~1.7 GB (manageable for Zenodo/Figshare)

---

#### Part B: Data Formatting and Compression (1 day)

**HDF5 Structure** (for trajectories):

```python
import h5py

# Create HDF5 file
with h5py.File('data/trajectories/representative_trajectories.h5', 'w') as f:
    # Metadata
    f.attrs['description'] = 'Representative three-body trajectories'
    f.attrs['num_trajectories'] = 1000
    f.attrs['integrator'] = 'Yoshida8'
    f.attrs['precision'] = 'float64'

    # For each trajectory
    for i in range(1000):
        traj_group = f.create_group(f'trajectory_{i:04d}')

        # Initial conditions
        traj_group.attrs['mass_ratio'] = mu[i]
        traj_group.attrs['energy'] = E[i]
        traj_group.attrs['angular_momentum'] = L[i]
        traj_group.create_dataset('initial_positions', data=q0[i])
        traj_group.create_dataset('initial_momenta', data=p0[i])

        # Trajectory data (time series)
        traj_group.create_dataset('time', data=t[i], compression='gzip')
        traj_group.create_dataset('positions', data=q[i], compression='gzip')
        traj_group.create_dataset('momenta', data=p[i], compression='gzip')
        traj_group.create_dataset('fiber_angle', data=theta[i], compression='gzip')
        traj_group.create_dataset('fiber_momentum', data=p_theta[i], compression='gzip')

        # Conserved quantities
        traj_group.create_dataset('energy', data=E_t[i], compression='gzip')
        traj_group.create_dataset('angular_momentum', data=L_t[i], compression='gzip')
        traj_group.create_dataset('discovered_integral', data=I_t[i], compression='gzip')
```

**Compression**: Use `gzip` compression (level 6) to reduce file size ~3-5x without loss.

**JSON Format** (for symbolic expressions):

```json
{
  "integrals": [
    {
      "id": "I_discovered_1",
      "expression_latex": "\\widetilde{I} = p_\\theta^2 + f(q, p)",
      "expression_sympy": "p_theta**2 + <serialized sympy>",
      "discovery_method": "killing_field_rank_1",
      "validation": {
        "poisson_bracket": {
          "symbolic": "zero",
          "numerical_max": 1.2e-13
        },
        "independence": {
          "jacobian_rank": 4,
          "success_rate": 0.9997
        },
        "conservation": {
          "monte_carlo_success_rate": 0.973,
          "mean_drift": 2.1e-8
        }
      }
    }
  ]
}
```

---

#### Part C: Metadata Generation (0.5 days)

**Create `data/README.md`**:

```markdown
# Data Artifacts

This directory contains curated datasets for reproducing all results.

## Directory Structure

- `trajectories/`: Representative 3-body trajectories (1000 samples)
- `integrals/`: Discovered conserved quantities (symbolic + numerical)
- `validation/`: WP4 validation results (Poisson brackets, Monte Carlo)
- `geometric/`: Connection forms, curvatures, metrics
- `figures/`: Source data for all publication figures

## Dataset Descriptions

### `representative_trajectories.h5` (1.2 GB)

1000 three-body trajectories covering parameter space:
- Mass ratios: 30 values in [1e-3, 0.5]
- Energies: 15 values per mass ratio
- Angular momenta: 10 values per energy

Each trajectory contains:
- Initial conditions (mass, E, L, q0, p0)
- Time series: (t, q, p, θ, p_θ)
- Conserved quantities: E(t), L(t), I(t)
- Duration: 10^4 orbital periods

**Format**: HDF5 with gzip compression
**Access**: `h5py.File('representative_trajectories.h5', 'r')`

[Continue for each dataset...]

## Citation

If you use these data, please cite:
```
[Citation information]
```

## License

Data licensed under CC-BY-4.0. See LICENSE file.
```

**Create `CITATION.cff`** (Citation File Format):

```yaml
cff-version: 1.2.0
message: "If you use this software, please cite it as below."
authors:
  - family-names: "Your Name"
    given-names: "First"
    orcid: "https://orcid.org/0000-0000-0000-0000"
title: "Lift-Integrability in the Three-Body Problem: Code and Data"
version: 1.0.0
doi: 10.5281/zenodo.XXXXXXX
date-released: 2025-11-17
url: "https://github.com/username/3body-lift-integrability"
preferred-citation:
  type: article
  authors:
    - family-names: "Your Name"
      given-names: "First"
  title: "Discovery of Lift-Integrability in the Three-Body Problem"
  journal: "Nature Physics"
  year: 2025
  doi: "10.1038/nphys.XXXX"
```

---

## Task 5.2.3: Computational Environment Specification

**Duration**: 1-2 days
**Objective**: Ensure reproducibility across different computing environments

### Implementation Details

#### Part A: Dependency Management (0.5 days)

**Create `requirements.txt`** (pip):
```
# Core dependencies
numpy>=1.21.0,<2.0.0
scipy>=1.7.0
sympy>=1.9
matplotlib>=3.5.0
h5py>=3.5.0

# Optimization
numba>=0.54.0
jax>=0.3.0  # For ML components

# Machine learning (WP3)
torch>=1.10.0
scikit-learn>=1.0.0

# Symbolic regression (WP3)
pysr>=0.11.0

# Testing
pytest>=7.0.0
pytest-cov>=3.0.0

# Documentation
sphinx>=4.3.0
sphinx-rtd-theme>=1.0.0

# Jupyter
jupyter>=1.0.0
ipykernel>=6.0.0

# Data handling
pandas>=1.3.0
```

**Create `environment.yml`** (conda):
```yaml
name: 3body-integrability
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.9
  - numpy>=1.21
  - scipy>=1.7
  - sympy>=1.9
  - matplotlib>=3.5
  - h5py>=3.5
  - numba>=0.54
  - jax>=0.3
  - pytorch>=1.10
  - scikit-learn>=1.0
  - pytest>=7.0
  - jupyter>=1.0
  - pandas>=1.3
  - pip
  - pip:
      - pysr>=0.11.0
      - sphinx>=4.3.0
      - sphinx-rtd-theme>=1.0.0
```

**Version Pinning Strategy**:
- Pin major versions (avoid breaking changes)
- Allow minor/patch updates (bug fixes)
- Test on Python 3.9, 3.10, 3.11

---

#### Part B: Docker Container (0.5-1 day, optional but recommended)

**Create `docker/Dockerfile`**:

```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy repository
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Run tests to verify environment
RUN pytest tests/ -v

# Default command: start Jupyter
CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
```

**Build and Test**:
```bash
# Build container
docker build -t 3body-integrability:latest -f docker/Dockerfile .

# Run interactively
docker run -it -p 8888:8888 3body-integrability:latest

# Run reproduction script
docker run 3body-integrability:latest python scripts/reproduce_main_results.py
```

**Benefits of Docker**:
- Eliminates "works on my machine" issues
- Ensures exact environment replication
- Easy to run on different platforms (Linux, macOS, Windows)

---

#### Part C: CI/CD Setup (0.5 days)

**Create `.github/workflows/tests.yml`**:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        python-version: ['3.9', '3.10', '3.11']

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .
        pip install pytest pytest-cov

    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

**Result**: Automated testing on every commit, ensuring code quality.

---

## Task 5.2.4: Testing and Validation Suite

**Duration**: 2-3 days
**Objective**: Comprehensive test suite ensuring correctness and reproducibility

### Implementation Details

#### Part A: Unit Tests (1 day)

**Test Structure**: Mirror source code structure in `tests/`

**Example: `tests/test_wp1/test_symplectic.py`**:

```python
import numpy as np
import pytest
from src.python.wp1_integration.symplectic import yoshida8_step

def test_yoshida8_harmonic_oscillator():
    """Test Yoshida8 integrator on harmonic oscillator."""
    # Initial condition
    q0, p0 = 1.0, 0.0
    dt = 0.01
    num_steps = 1000

    # Hamiltonian: H = p²/2 + q²/2
    def force(q):
        return -q

    # Integrate
    q, p = q0, p0
    for _ in range(num_steps):
        q, p = yoshida8_step(q, p, dt, force)

    # Expected: oscillation with period 2π
    # After time T = 10, should return near initial condition
    assert np.abs(q - np.cos(num_steps * dt)) < 1e-10
    assert np.abs(p + np.sin(num_steps * dt)) < 1e-10

def test_yoshida8_energy_conservation():
    """Test energy conservation in Yoshida8 integrator."""
    q0, p0 = 1.0, 0.5
    dt = 0.01
    num_steps = 10000

    def energy(q, p):
        return 0.5 * p**2 + 0.5 * q**2

    def force(q):
        return -q

    E0 = energy(q0, p0)
    q, p = q0, p0

    for _ in range(num_steps):
        q, p = yoshida8_step(q, p, dt, force)

    E_final = energy(q, p)

    # Energy should be conserved to machine precision
    assert np.abs(E_final - E0) / E0 < 1e-12
```

**Coverage Target**: >85% code coverage

---

#### Part B: Integration Tests (0.5 days)

**Test Full Workflows**:

**Example: `tests/test_integration/test_full_pipeline.py`**:

```python
import numpy as np
from src.python.wp1_integration import integrate_trajectory
from src.python.wp2_geometric import construct_s1_lift
from src.python.wp4_validation import compute_poisson_bracket

def test_full_validation_pipeline():
    """Test the complete pipeline: integrate → lift → validate."""

    # Step 1: Integrate a 3-body trajectory
    masses = [1.0, 1.0, 1.0]  # Equal masses
    q0 = np.array([...])  # Initial positions
    p0 = np.array([...])  # Initial velocities
    T = 100.0  # Integration time
    dt = 0.01

    trajectory = integrate_trajectory(masses, q0, p0, T, dt)

    # Step 2: Construct S¹ lift
    lifted_trajectory = construct_s1_lift(trajectory)

    # Step 3: Load discovered integral
    from src.python.wp3_discovery import load_integral
    I_discovered = load_integral('data/integrals/I_main.pkl')

    # Step 4: Validate conservation
    pb = compute_poisson_bracket(I_discovered, lifted_hamiltonian)

    assert np.abs(pb) < 1e-10, "Poisson bracket not conserved"

    # Check conservation along trajectory
    I_values = [I_discovered.evaluate(state) for state in lifted_trajectory]
    drift = (max(I_values) - min(I_values)) / I_values[0]

    assert drift < 1e-6, f"Integral drift {drift} exceeds tolerance"
```

---

#### Part C: Validation Tests (Reproduce Main Results) (1 day)

**Create `scripts/reproduce_main_results.py`**:

```python
"""
Reproduce all main results from the paper.

This script runs the complete validation pipeline and generates
key figures and tables, verifying that the published results
can be independently reproduced.
"""

import numpy as np
import matplotlib.pyplot as plt
from src.python.wp3_discovery import load_integral
from src.python.wp4_validation import (
    validate_conservation,
    validate_independence,
    run_monte_carlo
)

def main():
    print("="*60)
    print("Reproducing Main Results")
    print("="*60)

    # Load discovered integral
    print("\n[1/5] Loading discovered integral...")
    I = load_integral('data/integrals/I_main.pkl')
    print(f"  Loaded: {I.expression_latex}")

    # Test 1: Poisson bracket (symbolic)
    print("\n[2/5] Validating conservation (Poisson bracket)...")
    pb_result = validate_conservation(I, method='symbolic')
    print(f"  Result: {pb_result.is_zero_symbolic}")
    assert pb_result.is_zero_symbolic or pb_result.numerical_max < 1e-12

    # Test 2: Functional independence
    print("\n[3/5] Validating functional independence...")
    indep_result = validate_independence(I)
    print(f"  Jacobian rank increases: {indep_result.success_rate:.2%}")
    assert indep_result.success_rate > 0.99

    # Test 3: Monte Carlo validation
    print("\n[4/5] Running Monte Carlo validation (10^4 trajectories)...")
    mc_result = run_monte_carlo(I, num_trajectories=10000)
    print(f"  Success rate: {mc_result.success_rate:.2%}")
    print(f"  Mean drift: {mc_result.mean_drift:.2e}")
    assert mc_result.success_rate > 0.95

    # Test 4: Generate key figure
    print("\n[5/5] Generating Figure 1 (conservation plot)...")
    fig, ax = plt.subplots(figsize=(8, 6))
    # [Code to generate figure]
    plt.savefig('output/figure1_reproduced.pdf')
    print("  Saved: output/figure1_reproduced.pdf")

    print("\n" + "="*60)
    print("SUCCESS: All main results reproduced!")
    print("="*60)

if __name__ == '__main__':
    main()
```

**Usage**:
```bash
python scripts/reproduce_main_results.py
```

**Expected Output**:
```
============================================================
Reproducing Main Results
============================================================

[1/5] Loading discovered integral...
  Loaded: \widetilde{I} = p_\theta^2 + ...

[2/5] Validating conservation (Poisson bracket)...
  Result: True

[3/5] Validating functional independence...
  Jacobian rank increases: 99.97%

[4/5] Running Monte Carlo validation (10^4 trajectories)...
  Success rate: 97.3%
  Mean drift: 2.1e-8

[5/5] Generating Figure 1 (conservation plot)...
  Saved: output/figure1_reproduced.pdf

============================================================
SUCCESS: All main results reproduced!
============================================================
```

---

## Integration Strategy

### Reproducibility Certification

**Three-Level Verification**:

**Level 1: Local Verification** (Developer)
- Run test suite: `pytest tests/ -v`
- Run reproduction script: `python scripts/reproduce_main_results.py`
- Verify all figures regenerate correctly

**Level 2: Independent Verification** (Collaborator)
- Clone repository on clean machine
- Follow installation instructions
- Run reproduction script
- Compare outputs to published results

**Level 3: Community Verification** (Post-Publication)
- Public GitHub repository
- Archived dataset with DOI
- Docker container ensures environment
- Community can file issues if problems arise

---

## Publication and Archival

### Part A: GitHub Repository

**Repository Setup**:
1. Create public GitHub repo: `username/3body-lift-integrability`
2. Add comprehensive README with badges:
   - CI/CD status
   - Test coverage
   - DOI badge (from Zenodo)
   - License badge
3. Add topics/tags: `three-body-problem`, `integrability`, `symplectic-geometry`
4. Enable GitHub Discussions for community Q&A
5. Create release (v1.0.0) corresponding to publication

---

### Part B: Data Archival (Zenodo/Figshare)

**Zenodo Workflow**:

1. **Prepare Archive**:
   ```bash
   # Create compressed archive
   tar -czf 3body-data-v1.0.tar.gz data/
   ```

2. **Upload to Zenodo**:
   - Go to zenodo.org
   - Upload archive
   - Fill metadata:
     - Title: "Data for: Lift-Integrability in the Three-Body Problem"
     - Authors: [Your name and collaborators]
     - Description: [Describe datasets]
     - Keywords: three-body problem, integrability, symplectic geometry
     - License: CC-BY-4.0

3. **Obtain DOI**:
   - Zenodo assigns DOI: e.g., `10.5281/zenodo.7654321`
   - Add DOI to README and CITATION.cff

4. **Link to GitHub**:
   - Add Zenodo badge to README
   - Update data README with DOI link

---

## Deliverables

### Primary Outputs

1. **Public GitHub Repository**:
   - URL: `https://github.com/username/3body-lift-integrability`
   - Complete source code (all WPs)
   - Documentation (API + tutorials)
   - Test suite (>85% coverage)
   - CI/CD pipeline

2. **Archived Dataset with DOI**:
   - Zenodo/Figshare archive (~2 GB)
   - DOI for citation
   - Metadata and README

3. **Docker Container**:
   - Dockerfile in repository
   - Published to Docker Hub (optional)
   - One-command environment setup

4. **Reproducibility Certification**:
   - `scripts/reproduce_main_results.py` succeeds
   - All tests pass on CI/CD
   - Independent verification by collaborator

### Supporting Materials

5. **Documentation Website**:
   - Hosted on Read the Docs or GitHub Pages
   - API reference, tutorials, theory
   - Searchable, versioned

6. **Jupyter Notebooks**:
   - 6-7 tutorial notebooks
   - Interactive exploration of methods
   - Can run in Google Colab (optional)

---

## Timeline

### Day-by-Day Breakdown

**Days 1-3**: Task 5.2.1 (Code Organization)
- Day 1: Repository restructuring, cleanup
- Day 2: Docstring documentation (API)
- Day 3: Tutorial notebooks

**Days 4-5**: Task 5.2.2 (Data Curation)
- Day 4: Select datasets, format HDF5/JSON
- Day 5: Generate metadata, prepare archive

**Day 6**: Task 5.2.3 (Environment)
- Day 6: requirements.txt, Dockerfile, CI/CD

**Days 7-9**: Task 5.2.4 (Testing)
- Day 7: Unit tests
- Day 8: Integration tests
- Day 9: Validation tests, reproduction script

**Day 10**: Publication and Review
- Day 10: GitHub release, Zenodo upload, final checks

**Total**: 10 days

---

## Success Criteria

### Minimum Success
- [ ] Public GitHub repository with complete code
- [ ] Basic documentation (README, docstrings)
- [ ] Test suite with >70% coverage
- [ ] Data available (even if not archived with DOI)

### Target Success
- [ ] Comprehensive documentation (API + tutorials)
- [ ] Test suite with >85% coverage
- [ ] Data archived on Zenodo with DOI
- [ ] Docker container available
- [ ] Independent verification by one collaborator

### Stretch Success
- [ ] Test coverage >95%
- [ ] Documentation with interactive notebooks (Binder/Colab)
- [ ] CI/CD on multiple platforms (Linux, macOS, Windows)
- [ ] Community engagement (GitHub stars >50, discussions active)
- [ ] Featured on software archives (JOSS, papers with code)

---

## References

### Reproducibility Best Practices
1. Sandve, G. K. et al. "Ten Simple Rules for Reproducible Computational Research" PLoS Comp Bio (2013)
2. Wilson, G. et al. "Good enough practices in scientific computing" PLoS Comp Bio (2017)
3. Stodden, V. et al. "Toward Reproducible Computational Research" (2014)

### Software Engineering
4. Martin, R. C. "Clean Code: A Handbook of Agile Software Craftsmanship" (2008)
5. Wilson, G. et al. "Best Practices for Scientific Computing" PLoS Biology (2014)

### Documentation
6. van Rossum, G. "PEP 257 -- Docstring Conventions" (2001)
7. NumPy Documentation Guide (numpy.org/doc)

---

**Document Version**: 1.0
**Created**: 2025-11-17
**Status**: Complete Implementation Plan
**Dependencies**: WP 5.1 In Progress
**Next**: WP 5.3 Publication Preparation
