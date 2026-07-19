# User Guide: Work Package 1
## High-Fidelity CR3BP Trajectory Catalogue

**Status**: Scoped external qualification PASS; native production-catalogue generation remains unqualified
**Purpose**: Establish high-precision infrastructure for three-body problem integration and validation
**Role in Project**: Foundation for all subsequent work packages

> **Current status (2026-07-19)**: Qualification `WP1Q-v1-937694ba58a8` passes all 39 gates on development, calibration, and a locked first-execution holdout. The campaign uses a pinned 67,218-record NASA/JPL source snapshot and a 400-record corpus spanning four systems, Lyapunov/Halo families, and four stability regimes. The canonical gate collects 843 tests, passes 104 focused WP1 tests and 2/2 QD CTests, and bounded Linux/amd64 parity passes 12/12 evidence-bearing tests. Qualified Tier 1/Tier 2 artifacts preserve all rows and embed the qualification hashes. Production-scale Tier 2 and native WP1-generated family continuation/catalogue validation remain publication blockers. See `../notes/wp1-qualification-plan.md` and the formal report under `../validation-external/wp1-validation/reports/`.

---

## Table of Contents

1. [Overview](#overview)
2. [How WP1 Fits into the Overall Project](#how-wp1-fits-into-the-overall-project)
3. [What's Implemented](#whats-implemented)
4. [Quick Start Guide](#quick-start-guide)
5. [Core Components](#core-components)
6. [Available Tests](#available-tests)
7. [Examples and Workflows](#examples-and-workflows)
8. [Technical Details](#technical-details)
9. [References](#references)

---

## Overview

Work Package 1 provides the **computational foundation** for investigating hidden integrability in the three-body problem. It implements high-precision numerical integration, chaos detection, validation frameworks, and a production pipeline for generating large-scale trajectory catalogues.

### Key Question
*How do we reliably integrate three-body trajectories with sufficient precision to detect subtle conserved quantities?*

### Scientific Context

The Circular Restricted Three-Body Problem (CR3BP) describes the motion of a massless particle under the gravitational influence of two massive bodies in circular orbits. While non-integrable in general (proven by Bruns and Poincaré), this project searches for **lift-integrability**: the hypothesis that new conserved quantities may exist in appropriately constructed higher-dimensional spaces.

**Reference**: See `Science-Research-Docs/WP1 – Foundations: Symplectic Reduction, Moment Maps, Principal Bundles, Magnetic Terms.pdf` for the mathematical foundations.

---

## How WP1 Fits into the Overall Project

The 3-body integrability research project follows this progression:

```
┌──────────────────────────────────────────────────────────┐
│ WP1: High-Precision Infrastructure (THIS GUIDE)          │
│ • Symplectic integrators (IAS15, Yoshida8, Adaptive)    │
│ • Chaos detection (MEGNO, FLI)                           │
│ • Validation framework (shadow Hamiltonian, reversibility)│
│ • Production pipeline for trajectory catalogues          │
└────────────────────┬─────────────────────────────────────┘
                     │ Provides: High-fidelity trajectories
                     ↓
┌──────────────────────────────────────────────────────────┐
│ WP2: Geometric Foundations                                │
│ • Coordinate transformations & symplectic reduction       │
│ • S¹ bundle construction                                  │
│ • KS-Spinor regularization                                │
└────────────────────┬─────────────────────────────────────┘
                     │ Provides: Lifted phase spaces
                     ↓
┌──────────────────────────────────────────────────────────┐
│ WP3: Invariant Discovery                                  │
│ • Machine learning + symbolic regression                  │
│ • Search for new conserved quantities                     │
└────────────────────┬─────────────────────────────────────┘
                     │ Provides: Candidate integrals
                     ↓
┌──────────────────────────────────────────────────────────┐
│ WP4: Rigorous Validation                                  │
│ • Analytical vetting (Poisson brackets)                   │
│ • Morales-Ramis test (differential Galois theory)        │
│ • Statistical validation across parameter space           │
└────────────────────┬─────────────────────────────────────┘
                     │ Provides: Validated results
                     ↓
┌──────────────────────────────────────────────────────────┐
│ WP5: Publication & Dissemination                          │
│ • Formal proof construction                               │
│ • Reproducibility package                                 │
│ • Manuscript preparation                                  │
└──────────────────────────────────────────────────────────┘
```

**WP1's Critical Role**: Without high-precision trajectories and robust validation, we cannot distinguish genuine conserved quantities from numerical artifacts. WP1 ensures that downstream analysis (WP3-4) operates on trustworthy data.

---

## What's Implemented

WP1 has a **passing scoped qualification**. The environment, QD build, focused acceptance gate, external multi-system campaign, independent high-precision oracle, analytic STM/Floquet path, strict representative differential correction, and qualification-aware artifact writers are operational. Native WP1-generated family continuation and a production-scale periodic-orbit catalogue are not qualified yet.

### File Structure

```
src/python/
├── integrators/
│   ├── ias15.py                    # 15th-order adaptive Radau integrator
│   ├── yoshida8.py                 # 8th-order symplectic integrator
│   ├── adaptive_symplectic.py      # Adaptive symplectic with error control
│   └── dense_output.py             # Adaptive output density
├── validation/
│   ├── chaos_indicators.py         # MEGNO & FLI chaos detection
│   ├── shadow_hamiltonian.py       # Backward error analysis
│   └── time_reversibility.py       # Forward-backward integration tests
├── utils/
│   ├── dynamics.py                 # CR3BP equations of motion
│   ├── coordinates.py              # Coordinate transformations
│   └── poincare.py                 # Poincaré section utilities
├── ml/
│   ├── sobol_sampling.py           # Low-discrepancy sampling
│   └── parquet_export.py           # ML-ready data export
├── orbits/
│   └── periodic_families.py        # Known periodic orbit library
├── pipeline/
│   └── adaptive_sampling.py        # Gradient-based refinement
└── regularization/
    └── automatic_switching.py      # Cartesian ↔ KS switching

tests/
├── test_integrators.py             # Integration accuracy tests
├── test_dynamics.py                # CR3BP dynamics tests
├── test_yoshida8.py                # Symplectic integrator tests
└── validation/
    └── test_chaos_indicators.py    # Chaos detection tests

Snakefile                            # Production pipeline orchestration
```

### Precision Tiers

**Tier 1** (Standard Precision):
- Target: ΔC < 10⁻¹⁴ (Jacobi constant drift)
- Integrator: IAS15 (adaptive Radau)
- Use case: 10⁵ orbit catalogue
- Speed: ~50 periods/second

**Tier 2** (Ultra-High Precision):
- Target: ΔC < 10⁻²⁵
- Current bounded smoke: `HeyokaTaylorIntegrator` with 160-bit `heyoka.real`
- Smoke result: 3 orbits, max relative Jacobi drift `6.53e-28`, pass rate `100.0%`
- Remaining gap: production-scale Tier 2 catalogue and final publication scope are not yet validated

**External/JPL-Seeded Catalogue**:
- Source: normalized JPL Earth-Moon periodic-orbit records
- Current sample: 300 stratified seeds from 21,938 records
- Accepted output: `validation-external/wp1-validation/results/jpl_seeded_catalog.parquet`
- Acceptance thresholds: closure `<= 1e-8`, absolute Jacobi drift `<= 1e-12`
- Current result: 284 accepted rows; accepted-catalogue closure median `2.01e-11`, 95th percentile `9.73e-10`, max `6.23e-09`
- Scope: publishable as external-seeded validation evidence only, not as a native WP1-generated periodic catalogue

**Formal Multi-System Qualification**:
- Qualification ID: `WP1Q-v1-937694ba58a8`
- Source: 67,218 pinned NASA/JPL records across four CR3BP systems
- Corpus: 400 content-addressed records; 240 development, 80 calibration, 80 locked holdout
- Coverage: Lyapunov/Halo, L1/L2, north/south Halo branches, four stability regimes
- Decisions: development 39/39, calibration 39/39, holdout 39/39 gates passed
- Holdout case counts: 80 float64, 36 independent 224-bit oracle, 48 stability, 40 reconstruction
- Stability classification: 100%; reconstruction success: 100%
- Evidence: `validation-external/wp1-validation/reports/wp1_qualification_report.md`
- Boundary: validates the declared methods and bounded output path, not native production-scale catalogue generation

---

## Quick Start Guide

### 1. Environment Setup

```bash
# Navigate to project
cd /home/user/3body

# Activate conda environment
mamba activate wp1_env

# Verify setup
python verify_setup.py
```

**Expected output**: All checks pass (Python 3.11, QD library, numpy, scipy, rebound)

### 2. Run a Simple Integration

```python
from src.python.utils.dynamics import cr3bp_dynamics
from src.python.integrators.ias15 import IAS15Integrator
import numpy as np

# Earth-Moon mass ratio
mu = 0.012150585609624

# Initial state: prograde circular orbit near L2
state0 = np.array([1.15, 0.0, 0.0, 0.0, 0.1, 0.0])

# Jacobi constant
C = 3.1

# Integrate for 10 periods
integrator = IAS15Integrator(mu=mu)
times, states = integrator.integrate(
    state0=state0,
    t_span=(0, 10 * 2*np.pi),
    dt=0.1
)

print(f"Final time: {times[-1]:.2f}")
print(f"Final state: {states[-1]}")
```

### 3. Verify Conservation

```python
from src.python.utils.dynamics import jacobi_constant

# Compute Jacobi constant along trajectory
C_values = [jacobi_constant(state, mu) for state in states]

# Check drift
C_drift = max(C_values) - min(C_values)
print(f"Jacobi constant drift: {C_drift:.2e}")
# Expected: < 1e-14 for IAS15
```

### 4. Detect Chaos

```python
from src.python.validation.chaos_indicators import create_cr3bp_chaos_analyzer

# Create chaos analyzer
analyzer = create_cr3bp_chaos_analyzer(mu=mu)

# Analyze orbit
result = analyzer.analyze(
    state0=state0,
    t_max=100 * 2*np.pi,  # 100 periods
    dt=0.1
)

print(f"MEGNO: {result['megno']:.3f}")  # ~2.0 = regular, >2.5 = chaotic
print(f"FLI: {result['fli']:.3f}")      # <3.0 = regular, >4.0 = chaotic
print(f"Classification: {result['classification']}")  # 'regular' or 'chaotic'
```

---

## Core Components

### 1. Numerical Integrators

#### IAS15 (Adaptive Radau)
**Location**: `src/python/integrators/ias15.py`

**Strengths**:
- Excellent energy conservation (< 1e-15 relative drift)
- Adaptive timestep control
- Arbitrary duration integration

**Usage**:
```python
from src.python.integrators.ias15 import IAS15Integrator

integrator = IAS15Integrator(mu=0.012150585609624)
times, states = integrator.integrate(
    state0=initial_state,
    t_span=(0, 100),
    dt=0.1  # output timestep (internal timestep is adaptive)
)
```

**Tests**: `tests/test_integrators.py::test_ias15_energy_conservation`

#### Yoshida8 (Symplectic)
**Location**: `src/python/integrators/yoshida8.py`

**Strengths**:
- Preserves Hamiltonian structure exactly
- Excellent long-term stability
- 8th-order accuracy

**Usage**:
```python
from src.python.integrators.yoshida8 import Yoshida8Integrator

integrator = Yoshida8Integrator(mu=0.012150585609624)
times, states = integrator.integrate(
    state0=initial_state,
    t_span=(0, 1000),
    dt=0.01  # fixed timestep
)
```

**Tests**: `tests/test_yoshida8.py::test_symplectic_energy_conservation`

#### AdaptiveSymplectic (Current Float64 Prototype)
**Location**: `src/python/integrators/adaptive_symplectic.py`

**Strengths**:
- Symplectic + adaptive timestep
- Sundman time transformation (natural adaptivity near close encounters)
- Error control with step doubling
- Current float64 path completes short probes at realistic tolerances such as `1e-14`
- Requests below the float64 floor fail immediately instead of producing false-positive Tier 2 reports

**Usage**:
```python
from src.python.integrators.adaptive_symplectic import AdaptiveSymplecticIntegrator

integrator = AdaptiveSymplecticIntegrator(
    mu=0.012150585609624,
    order=6,  # 4 or 6
    error_tolerance=1e-14,
    sundman_strategy='sum'  # 'sum', 'product', or 'min'
)
result = integrator.integrate(
    initial_state=initial_state,
    duration=100,
    output_interval=1.0,
)
```

#### HeyokaTaylor (Bounded Tier 2 Smoke)
**Location**: `src/python/integrators/heyoka_taylor.py`

**Strengths**:
- Uses `heyoka.real` arbitrary-precision Taylor integration
- Records high-precision Jacobi drift in `IntegrationResult.stats`
- Supports the current bounded Tier 2 smoke at target `1e-25`

**Usage**:
```python
from src.python.integrators.heyoka_taylor import HeyokaTaylorIntegrator

integrator = HeyokaTaylorIntegrator(
    mu=0.012150585609624,
    tolerance=1e-25,
    precision_bits=160,
)
result = integrator.integrate(
    initial_state=initial_state,
    duration=1.0,
    output_interval=0.5,
)
print(result.stats["jacobi_relative_drift"])
```

**Reference**: See `Project-Design-Docs/WP1/WP1-Implementation-Complete-22ndNov2025.md` for full implementation details.

---

### 2. Chaos Detection

#### MEGNO Indicator
**Location**: `src/python/validation/chaos_indicators.py`

**Theory**: Mean Exponential Growth of Nearby Orbits. For regular motion, MEGNO → 2.0. For chaotic motion, MEGNO grows linearly with time.

**Usage**:
```python
from src.python.validation.chaos_indicators import MEGNOIndicator

indicator = MEGNOIndicator(dynamics_func=cr3bp_dynamics, mu=mu)
megno_value = indicator.compute(
    state0=initial_state,
    t_max=100,
    dt=0.01
)
print(f"MEGNO: {megno_value:.3f}")
# ~2.0 = regular, >2.5 = chaotic
```

**Tests**: `tests/validation/test_chaos_indicators.py::test_megno_regular_vs_chaotic`

#### FLI Indicator
**Location**: `src/python/validation/chaos_indicators.py`

**Theory**: Fast Lyapunov Indicator. Tracks logarithmic growth of deviation vector.

**Usage**:
```python
from src.python.validation.chaos_indicators import FLIIndicator

indicator = FLIIndicator(dynamics_func=cr3bp_dynamics, mu=mu)
fli_value = indicator.compute(
    state0=initial_state,
    t_max=50,  # shorter than MEGNO
    dt=0.01
)
print(f"FLI: {fli_value:.3f}")
# <3.0 = regular, >4.0 = chaotic
```

---

### 3. Validation Framework

#### Shadow Hamiltonian Analysis
**Location**: `src/python/validation/shadow_hamiltonian.py`

**Theory**: Backward error analysis. A symplectic integrator exactly conserves a "shadow Hamiltonian" H̃ = H + h²·H₂ + O(h⁴), where h is the timestep.

**Usage**:
```python
from src.python.validation.shadow_hamiltonian import ShadowHamiltonianAnalyzer

analyzer = ShadowHamiltonianAnalyzer(dynamics_func=cr3bp_dynamics)
result = analyzer.analyze(
    times=times,
    states=states,
    dt=0.01
)
print(f"H₂ correction: {result['H2']:.3e}")
print(f"Shadow Hamiltonian drift: {result['drift_rate']:.3e}")
# Current Tier 2 smoke drift is measured directly by HeyokaTaylorIntegrator.
```

**Reference**: See `Science-Research-Docs/Explanation_DoubleDoubleArithmetic.md` for precision requirements.

#### Time Reversibility Tests
**Location**: `src/python/validation/time_reversibility.py`

**Theory**: Symplectic integrators should be time-reversible: integrating forward then backward should return to the initial state.

**Usage**:
```python
from src.python.validation.time_reversibility import TimeReversibilityTester

tester = TimeReversibilityTester(integrator=yoshida8_integrator)
result = tester.test_reversibility(
    state0=initial_state,
    t_half=50.0,  # integrate to t=50, then back to t=0
    dt=0.01
)
print(f"RMS position error: {result['rms_pos_error']:.3e}")
print(f"RMS velocity error: {result['rms_vel_error']:.3e}")
# Should be < 1e-20 for Tier 2
```

---

### 4. Production Pipeline

#### Snakemake Orchestration
**Location**: `Snakefile`

**Purpose**: Scalable pipeline for generating 10⁵+ orbit catalogue with parallel execution.

**Pipeline stages**:
1. **Parameter Generation**: Sobol sequence sampling of (μ, C, initial conditions)
2. **Parallel Integration**: Per-orbit integration with automatic integrator selection
3. **Chaos Analysis**: Compute MEGNO & FLI for each orbit
4. **Aggregation**: Collect results into HDF5 + Parquet formats
5. **Validation**: Generate quality reports

**Usage**:
```bash
# Dry run (show what would be executed)
snakemake -n

# Run with 8 cores
snakemake --cores 8

# Run specific target
snakemake tier1_complete --cores 8

# Generate validation report
snakemake validation_report
```

**Configuration**: Edit `config` section in `Snakefile` to adjust:
- Number of samples (default: 10⁵ for Tier 1, 10⁴ for Tier 2)
- Output directory
- Precision targets
- Parallel cores

---

## Available Tests

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_integrators.py -v

# Specific test function
pytest tests/test_integrators.py::test_ias15_energy_conservation -v

# Skip slow tests
pytest -m "not slow"
```

### Key Test Files

| Test File | Purpose | Key Tests |
|-----------|---------|-----------|
| `test_integrators.py` | Integration accuracy | Energy conservation, timestep control |
| `test_dynamics.py` | CR3BP dynamics | Jacobi constant, equations of motion |
| `test_yoshida8.py` | Symplectic integrator | Long-term stability, reversibility |
| `validation/test_chaos_indicators.py` | Chaos detection | MEGNO/FLI on known cases |
| `test_qd_python.py` | QD library | Double-double arithmetic precision |

### Test Coverage

**Current**: 51 test files with ~100+ test functions
**Coverage**: ~80% (unit + integration tests)

**To run with coverage**:
```bash
pytest tests/ --cov=src/python --cov-report=html
```

---

## Examples and Workflows

### Example 1: Generate Lyapunov Orbit Family

```python
from src.python.orbits.periodic_families import LyapunovOrbitGenerator
import matplotlib.pyplot as plt

# Generate Lyapunov orbits around L2
generator = LyapunovOrbitGenerator(mu=0.012150585609624, lagrange_point='L2')

# Generate family with 20 members
orbits = generator.generate_family(
    Az_range=(0.01, 0.1),  # amplitude range
    num_orbits=20
)

# Plot x-y projection
for orbit in orbits:
    plt.plot(orbit['states'][:, 0], orbit['states'][:, 1])
plt.xlabel('x (rotating frame)')
plt.ylabel('y (rotating frame)')
plt.title('Lyapunov Orbit Family (Earth-Moon L2)')
plt.grid(True)
plt.show()
```

**Reference**: See `examples/` directory for more examples.

### Example 2: Poincaré Section

```python
from src.python.utils.poincare import PoincareSection

# Define y=0 section (vy > 0)
section = PoincareSection.create_standard_section('y_zero', mu=mu)

# Compute crossings
crossings = section.compute_crossings(times, states)

# Plot return map
x_crossings = [c['state'][0] for c in crossings]
vx_crossings = [c['state'][3] for c in crossings]

plt.scatter(x_crossings, vx_crossings, s=1)
plt.xlabel('x')
plt.ylabel('vx')
plt.title('Poincaré Section (y=0, vy>0)')
plt.show()
```

### Example 3: Adaptive Sampling

```python
from src.python.pipeline.adaptive_sampling import AdaptiveSampler

# Initial coarse grid
initial_samples = generate_initial_grid(n=1000)

# Compute some metric (e.g., Jacobi constant drift)
metrics = [compute_metric(sample) for sample in initial_samples]

# Adaptively refine high-gradient regions
sampler = AdaptiveSampler(refinement_factor=4)
refined_samples = sampler.refine(
    samples=initial_samples,
    metrics=metrics,
    num_refinements=3
)

print(f"Initial: {len(initial_samples)} samples")
print(f"Refined: {len(refined_samples)} samples")
```

---

## Technical Details

### CR3BP Equations of Motion

**Rotating frame** (co-rotating with primaries):

```
ẍ - 2ẏ = ∂Ω/∂x
ÿ + 2ẋ = ∂Ω/∂y
z̈      = ∂Ω/∂z

Ω(x,y,z) = (x² + y²)/2 + (1-μ)/r₁ + μ/r₂ + μ(1-μ)/2
```

where:
- μ = mass ratio (m₂/(m₁+m₂))
- r₁ = distance to primary 1
- r₂ = distance to primary 2

**Jacobi constant** (conserved quantity):
```
C = 2Ω(x,y,z) - (ẋ² + ẏ² + ż²)
```

**Implementation**: `src/python/utils/dynamics.py`

---

### QD Library (Double-Double Arithmetic)

**Precision**: ~31 decimal digits (vs. 15 for IEEE double)

**Usage** (when needed for Tier 2):
```python
from src.python.qd_python import dd_real

# Create double-double values
a = dd_real(1.0)
b = dd_real(3.0)
c = a / b  # 0.333...333 to 31 digits

# Convert back to float
float_val = float(c)
```

**Reference**: See `Science-Research-Docs/Explanation_DoubleDoubleArithmetic.md`

---

### Performance Characteristics

| Component | Speed | Precision | Use Case |
|-----------|-------|-----------|----------|
| IAS15 | 50 periods/s | ΔC ~ 1e-15 | Tier 1 catalogue |
| Yoshida8 | 250 periods/s | ΔC ~ 1e-8 | Long-term symplectic |
| AdaptiveSymplectic | Probe-dependent | Float64 path with guard | Symplectic prototype |
| HeyokaTaylor | Smoke-scale | ΔC < 1e-25 in bounded smoke | Tier 2 high-precision validation subset |
| MEGNO | 10 periods/s | N/A | Chaos detection |

**Benchmarking**: Use `benchmarks/cr3bp_smoke.yaml` with `scripts/run_benchmark.py`

---

## References

### Science Research Documents

1. **`WP1 – Foundations: Symplectic Reduction, Moment Maps, Principal Bundles, Magnetic Terms.pdf`**
   Mathematical foundations for symplectic geometry and reduction theory.

2. **`Explanation_REBOUND.md`**
   Details on the REBOUND library (used for IAS15 integrator).

3. **`Explanation_DoubleDoubleArithmetic.md`**
   Explanation of QD library and double-double arithmetic.

### Project Design Documents

1. **`Project-Design-Docs/WP1/WP1-Implementation-Complete-22ndNov2025.md`**
   Complete implementation report with all technical details.

2. **`Project-Design-Docs/WP1/WP1-Gap-Fixing-Plan-22ndNov2025.md`**
   Implementation plan showing how gaps were identified and resolved.

3. **`Project-Design-Docs/WP1/WP1-Phase-1/WP1-Phase-1-TechnicalReadme.md`**
   Phase 1 technical documentation.

### External References

- **IAS15**: Rein & Spiegel (2015), "IAS15: A fast, adaptive, high-order integrator for gravitational dynamics", MNRAS 446:1424-1437
- **Yoshida (1990)**: "Construction of higher order symplectic integrators"
- **REBOUND**: https://rebound.readthedocs.io/
- **QD Library**: http://crd-legacy.lbl.gov/~dhbailey/mpdist/

---

## Next Steps

Once you're comfortable with WP1, proceed to:

- **User-Guide-WP2.md**: Geometric foundations and lift constructions
- **User-Guide-WP3.md**: Discovery of candidate invariants using ML + symbolic regression
- **User-Guide-WP4.md**: Rigorous validation using Morales-Ramis and statistical tests
- **User-Guide-WP5.md**: Publication preparation and reproducibility

---

**Last Updated**: July 19, 2026
**WP1 Status**: Scoped external qualification PASS; native generation and production-scale blockers remain
