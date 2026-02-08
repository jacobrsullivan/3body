# User Guide: Work Package 3
## Discovery of Candidate Invariants

**Status**: ✅ Complete (All Phases 1-4 implemented)
**Purpose**: Discover hidden conserved quantities in lifted phase spaces using ML + symbolic regression
**Role in Project**: The "discovery engine" that searches for new integrals of motion

---

## Table of Contents

1. [Overview](#overview)
2. [How WP3 Fits into the Overall Project](#how-wp3-fits-into-the-overall-project)
3. [What's Implemented](#whats-implemented)
4. [Quick Start Guide](#quick-start-guide)
5. [Core Components](#core-components)
6. [Available Tests](#available-tests)
7. [Examples and Workflows](#examples-and-workflows)
8. [Mathematical Framework](#mathematical-framework)
9. [References](#references)

---

## Overview

Work Package 3 implements **data-driven discovery** of conserved quantities in the three-body problem. While classical integrals (energy E, angular momentum L) are well-known, WP3 searches for **new** integrals that may exist in the lifted spaces constructed by WP2 (S¹ bundle, KS-Spinor).

### Key Question
*Can machine learning and symbolic regression discover hidden conserved quantities that have eluded 300+ years of analytical investigation?*

### The Discovery Strategy

WP3 uses a **multi-pronged approach**:

1. **Hamiltonian Neural Networks (HNN)**: Learn conserved quantities from trajectory data
2. **Symbolic Regression (PySR)**: Convert learned functions to symbolic expressions
3. **Specialized Basis Functions**: Search in domains where integrals are known to exist (elliptic functions, spinor coordinates, theta functions)
4. **Multi-Stage Pipeline**: Coordinate all methods with candidate ranking and validation

### Scientific Context

The three-body problem has **no general analytical solution**. However:
- **Special cases** (Lagrange points, figure-8 orbit) have known integrals
- **Restricted problem** (CR3BP) has Jacobi constant C
- **Lift-integrability hypothesis**: New integrals may exist "upstairs"

WP3 tests this hypothesis by searching in:
- S¹ bundle: Look for fiber momentum p_θ or related integrals
- KS-Spinor space: Look for spinor-based conserved quantities
- Elliptic/theta function spaces: Exploit quasi-periodic structure

**Reference**: See `Science-Research-Docs/WP3 – Generalized KS Transformations and N-Body Regularizations.pdf`

---

## How WP3 Fits into the Overall Project

```
┌──────────────────────────────────────────────────────────┐
│ WP1: High-Precision Infrastructure                       │
│ • Provides: Trajectory data with ΔC < 10⁻¹⁴              │
└────────────────────┬─────────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────────┐
│ WP2: Geometric Foundations                                │
│ • Provides: Lifted phase spaces (S¹, KS-Spinor)          │
│ • Provides: Connection A, curvature F, JM metric          │
└────────────────────┬─────────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────────┐
│ WP3: Invariant Discovery (THIS GUIDE)                     │
│ ┌────────────────────────────────────────────────────┐   │
│ │ Phase 1 (HIGH): Spinor Basis & Enhanced Validation │   │
│ │ • KS spinor basis (~80 functions)                   │   │
│ │ • Multi-scale conservation testing                  │   │
│ │ • Interpretability scoring                          │   │
│ └──────────────────┬─────────────────────────────────┘   │
│                    ↓                                      │
│ ┌────────────────────────────────────────────────────┐   │
│ │ Phase 2 (MEDIUM): Elliptic Function Basis           │   │
│ │ • Jacobi elliptic functions (sn, cn, dn)            │   │
│ │ • Parameter estimation from quasi-periodic data     │   │
│ │ • Pattern matching + hybrid SINDy                   │   │
│ └──────────────────┬─────────────────────────────────┘   │
│                    ↓                                      │
│ ┌────────────────────────────────────────────────────┐   │
│ │ Phase 3 (MEDIUM): Spinor Search                     │   │
│ │ • Specialized search for spinor integrals           │   │
│ │ • Regularization benefit detection                  │   │
│ │ • Pattern recognition (spinor norms, products)      │   │
│ └──────────────────┬─────────────────────────────────┘   │
│                    ↓                                      │
│ ┌────────────────────────────────────────────────────┐   │
│ │ Phase 4 (LOW): Theta Function Basis                 │   │
│ │ • Jacobi theta functions (θ₁, θ₂, θ₃, θ₄)          │   │
│ │ • Completely integrable systems                     │   │
│ │ • Abel-Jacobi map                                   │   │
│ └──────────────────┬─────────────────────────────────┘   │
│                    ↓                                      │
│ ┌────────────────────────────────────────────────────┐   │
│ │ Multi-Stage Pipeline                                │   │
│ │ • Coordinate all methods                            │   │
│ │ • Rank candidates by confidence                     │   │
│ │ • Triviality & independence checks                  │   │
│ └────────────────────────────────────────────────────┘   │
└────────────────────┬─────────────────────────────────────┘
                     │ Provides: Candidate integrals Ĩ
                     ↓
┌──────────────────────────────────────────────────────────┐
│ WP4: Rigorous Validation                                  │
│ • Analytical vetting (Poisson brackets, independence)     │
│ • Morales-Ramis test (downstairs + upstairs)             │
│ • Statistical validation (Monte Carlo)                    │
└──────────────────────────────────────────────────────────┘
```

**WP3's Critical Role**: Bridges the gap between geometric theory (WP2) and rigorous validation (WP4) by **generating testable hypotheses** about conserved quantities.

---

## What's Implemented

WP3 is **100% complete** with all 4 phases implemented (~5,600 lines of production code + ~2,400 lines of tests).

### File Structure

```
src/python/
├── symbolic/
│   ├── basis_functions.py            # Core polynomial/rational basis
│   ├── spinor_basis.py                # KS spinor basis (~80 functions)
│   ├── elliptic_basis.py              # Jacobi elliptic functions
│   ├── theta_basis.py                 # Jacobi theta functions
│   ├── geometric_invariants.py        # JM metric-based invariants
│   ├── spinor_search.py               # Specialized spinor search
│   ├── elliptic_search.py             # Specialized elliptic search
│   ├── regression_pipeline.py         # SINDy + PySR pipeline
│   ├── multi_stage_pipeline.py        # Coordinated search
│   ├── enhanced_validation.py         # Multi-scale validation
│   ├── interpretability.py            # Function classification
│   ├── candidate_ranking.py           # Ranking & triviality checks
│   ├── simplification.py              # Symbolic simplification
│   └── validation.py                  # Conservation testing
├── symbolic_lifts/
│   ├── s1_symbolic.py                 # Symbolic S¹ lift
│   ├── ks_symbolic.py                 # Symbolic KS-Spinor lift
│   └── common.py                      # Shared symbolic utilities
└── ml/
    ├── conservation_hnn.py            # Hamiltonian Neural Network
    ├── hnn_architecture.py            # HNN model architecture
    ├── hnn_training.py                # HNN training pipeline
    ├── dataset_builder.py             # ML dataset construction
    ├── conservation_loss.py           # Conservation loss functions
    └── independence_test.py           # Functional independence tests

tests/wp3/
├── test_spinor_basis.py               # Spinor basis tests
├── test_elliptic_basis.py             # Elliptic basis tests
├── test_theta_basis.py                # Theta basis tests
├── test_enhanced_validation.py        # Validation tests
├── test_interpretability.py           # Interpretability tests
├── test_specialized_search.py         # Search algorithm tests
├── test_multi_stage_pipeline.py       # Pipeline integration tests
├── test_triviality_and_independence.py # Triviality tests
└── test_end_to_end_known_cases.py     # E2E validation
```

### Implementation Summary

| Phase | Component | Status | Files | Lines |
|-------|-----------|--------|-------|-------|
| **Phase 1** | Spinor Basis | ✅ Complete | 1 | 505 |
| **Phase 1** | Enhanced Validation | ✅ Complete | 1 | 340 |
| **Phase 1** | Interpretability | ✅ Complete | 1 | 550 |
| **Phase 2** | Elliptic Basis | ✅ Complete | 1 | 705 |
| **Phase 2** | Elliptic Search | ✅ Complete | 1 | 470 |
| **Phase 3** | Spinor Search | ✅ Complete | 1 | 355 |
| **Phase 4** | Theta Basis | ✅ Complete | 1 | 420 |
| **Integration** | Multi-Stage Pipeline | ✅ Complete | 1 | 680 |
| **Integration** | Candidate Ranking | ✅ Complete | 1 | 550 |
| **Tests** | All Tests | ✅ Complete | 12 | 2,400 |

**Total**: ~5,600 lines production code + ~2,400 lines tests

---

## Quick Start Guide

### 1. Basic Symbolic Regression Search

```python
from src.python.symbolic.regression_pipeline import SymbolicRegressionPipeline
from src.python.integrators.ias15 import IAS15Integrator
import numpy as np

# Generate trajectory data
mu = 0.012150585609624
integrator = IAS15Integrator(mu=mu)
state0 = np.array([1.15, 0.0, 0.0, 0.0, 0.1, 0.0])
times, states = integrator.integrate(state0, t_span=(0, 100), dt=0.1)

# Create search pipeline
pipeline = SymbolicRegressionPipeline(
    basis_type='polynomial',  # or 'spinor', 'elliptic', 'theta'
    max_complexity=10,
    population_size=100
)

# Search for conserved quantities
results = pipeline.search(times, states, mu=mu)

# Display results
for i, candidate in enumerate(results['candidates']):
    print(f"\nCandidate {i+1}:")
    print(f"  Expression: {candidate['expression']}")
    print(f"  Conservation error: {candidate['conservation_error']:.2e}")
    print(f"  Confidence: {candidate['confidence']:.3f}")
```

### 2. Spinor Basis Search

```python
from src.python.symbolic.spinor_search import search_spinor_integral

# Search for spinor-based integrals
result = search_spinor_integral(
    times=times,
    states=states,
    mu=mu,
    regularization_threshold=0.1  # detect close encounters
)

if result.success:
    print(f"Found spinor integral!")
    print(f"Expression: {result.expression}")
    print(f"Pattern type: {result.pattern_type}")
    print(f"Conservation: {result.conservation_error:.2e}")
else:
    print("No spinor integral found")
```

### 3. Elliptic Function Search

```python
from src.python.symbolic.elliptic_search import search_elliptic_integral, detect_elliptic_signature

# Check if trajectory has elliptic structure
signature = detect_elliptic_signature(times, states)

if signature.is_quasi_periodic:
    print(f"Detected quasi-periodic motion!")
    print(f"Frequencies: {signature.frequencies}")
    print(f"Estimated elliptic parameter m: {signature.elliptic_parameter:.3f}")

    # Search for elliptic integral
    result = search_elliptic_integral(times, states, mu=mu)

    if result.success:
        print(f"\nFound elliptic integral!")
        print(f"Expression: {result.expression}")
        print(f"Elliptic parameter m: {result.m:.4f}")
```

### 4. Multi-Stage Coordinated Search

```python
from src.python.symbolic.multi_stage_pipeline import MultiStageInvariantSearch

# Create coordinated search pipeline
search = MultiStageInvariantSearch(
    stages=['spinor', 'elliptic', 'theta', 'polynomial'],
    max_candidates_per_stage=5,
    enable_ranking=True
)

# Run all stages
results = search.run(times, states, mu=mu)

# Results are ranked by confidence
print("\n=== Top Candidates ===")
for i, candidate in enumerate(results.top_candidates[:3]):
    print(f"\nRank {i+1}:")
    print(f"  Expression: {candidate.expression}")
    print(f"  Method: {candidate.method}")
    print(f"  Confidence: {candidate.confidence:.3f}")
    print(f"  Interpretability: {candidate.interpretability_score:.3f}")
    print(f"  Conservation: {candidate.conservation_error:.2e}")
```

---

## Core Components

### Phase 1: Spinor Basis & Enhanced Validation

#### Spinor Basis
**Location**: `src/python/symbolic/spinor_basis.py`

**Purpose**: KS transformation maps 3D positions to 4D spinors, potentially revealing hidden symmetries.

**Theory**: For position vector **r**, KS spinor **u** satisfies:
```
r = L(u) u  (Levi-Civita matrix)
|r| = |u|²  (bilinear relation)
```

**Basis functions** (~80 total):
1. **Spinor norms**: |u₁|², |u₂|², |u₃|² (= |r₁|, |r₂|, |r₃|)
2. **Inner products**: u₁·u₂, u₂·u₃, u₃·u₁
3. **Quaternion products**: u₁*u₂, u₂*u₃, u₃*u₁ (cross products in spinor space)
4. **Mixed bilinear forms**: various combinations

**Usage**:
```python
from src.python.symbolic.spinor_basis import (
    generate_spinor_basis,
    position_to_spinor,
    spinor_to_position
)

# Convert positions to spinors
r1, r2, r3 = states[:, :3], states[:, 3:6], states[:, 6:9]
u1 = position_to_spinor(r1)
u2 = position_to_spinor(r2)
u3 = position_to_spinor(r3)

# Generate basis functions
basis_funcs = generate_spinor_basis()
print(f"Generated {len(basis_funcs)} spinor basis functions")

# Evaluate basis on trajectory
basis_values = np.array([func(u1, u2, u3) for func in basis_funcs])
```

**Tests**: `tests/wp3/test_spinor_basis.py`

**Reference**: See `Science-Research-Docs/WP3 – Generalized KS Transformations and N-Body Regularizations.pdf`

---

#### Enhanced Validation
**Location**: `src/python/symbolic/enhanced_validation.py`

**Purpose**: Multi-scale validation to distinguish genuine conserved quantities from slowly-varying functions.

**Methods**:
1. **Multi-scale conservation**: Test at dt = 0.01, 0.1, 1.0, 10.0
2. **Quasi-periodic detection**: FFT analysis for periodic/quasi-periodic structure
3. **Long-time stability**: Track drift over 10⁴+ periods

**Usage**:
```python
from src.python.symbolic.enhanced_validation import (
    multi_scale_conservation_test,
    detect_quasi_periodic,
    long_time_stability
)

# Multi-scale conservation
scales = multi_scale_conservation_test(
    candidate_func=lambda state: state[0]**2 + state[1]**2,  # example
    times=times,
    states=states,
    scales=[0.01, 0.1, 1.0, 10.0]
)

for scale, error in scales.items():
    print(f"Scale dt={scale}: conservation error = {error:.2e}")

# Quasi-periodic detection
qp_result = detect_quasi_periodic(times, states)
if qp_result.is_quasi_periodic:
    print(f"Quasi-periodic with frequencies: {qp_result.frequencies}")

# Long-time stability (requires long integration)
stability = long_time_stability(candidate_func, times, states, t_max=10000)
print(f"Long-time drift rate: {stability.drift_rate:.2e} per period")
```

---

#### Interpretability
**Location**: `src/python/symbolic/interpretability.py`

**Purpose**: Classify and score candidate expressions for physical interpretability.

**Function types** (9 categories):
1. **Polynomial**: x², x³, xy, etc.
2. **Rational**: 1/r, 1/(1+r²), etc.
3. **Radical**: √r, ∛(x²+y²), etc.
4. **Trigonometric**: sin, cos, tan
5. **Exponential**: e^x, e^(-r)
6. **Spinor**: |u|², u·v, u×v
7. **Elliptic**: sn, cn, dn
8. **Theta**: θ₁, θ₂, θ₃, θ₄
9. **Mixed**: combinations

**Interpretability scoring** (0-1):
- Simple polynomials: 1.0
- Known special functions: 0.8-0.9
- Complex mixed expressions: 0.3-0.5
- Unrecognized forms: 0.1-0.2

**Usage**:
```python
from src.python.symbolic.interpretability import (
    classify_function,
    interpretability_score,
    detect_physical_symmetry
)

# Classify expression
expr = "u1_norm_sq + u2_norm_sq"  # example spinor expression
func_type = classify_function(expr)
print(f"Function type: {func_type}")  # → 'spinor'

# Score interpretability
score = interpretability_score(expr)
print(f"Interpretability: {score:.3f}")  # → 0.85 (spinor norms are well-understood)

# Detect symmetries
symmetries = detect_physical_symmetry(expr)
print(f"Symmetries: {symmetries}")  # e.g., ['spherical', 'rotation_invariant']
```

**Tests**: `tests/wp3/test_interpretability.py`

---

### Phase 2: Elliptic Function Basis

#### Elliptic Basis
**Location**: `src/python/symbolic/elliptic_basis.py`

**Purpose**: Jacobi elliptic functions naturally describe motion on elliptic curves (doubly periodic).

**Theory**: Jacobi elliptic functions sn(u,m), cn(u,m), dn(u,m) satisfy:
```
sn² + cn² = 1
dn² + m·sn² = 1
```

where m ∈ [0,1] is the **elliptic parameter**.

**Basis functions** (~60-80 total):
1. **Basic**: sn(|r|, m), cn(|r|, m), dn(|r|, m)
2. **Products**: sn·cn, sn·dn, cn·dn
3. **Powers**: sn², cn², dn²
4. **Mixed with coordinates**: r_x · sn(|r|), r_y · cn(|r|)
5. **Complete integrals**: K(m), E(m)

**Usage**:
```python
from src.python.symbolic.elliptic_basis import (
    generate_elliptic_basis,
    jacobi_sn,
    jacobi_cn,
    jacobi_dn,
    estimate_elliptic_parameter
)

# Estimate elliptic parameter from trajectory
m = estimate_elliptic_parameter(times, states)
print(f"Estimated m = {m:.4f}")

# Generate basis with this parameter
basis_funcs = generate_elliptic_basis(m=m)
print(f"Generated {len(basis_funcs)} elliptic basis functions")

# Evaluate on trajectory
r_magnitudes = np.linalg.norm(states[:, :3], axis=1)
sn_vals = jacobi_sn(r_magnitudes, m)
cn_vals = jacobi_cn(r_magnitudes, m)
dn_vals = jacobi_dn(r_magnitudes, m)

# Verify fundamental identity
assert np.allclose(sn_vals**2 + cn_vals**2, 1.0, atol=1e-10)
```

**Tests**: `tests/wp3/test_elliptic_basis.py`

**Reference**: Abramowitz & Stegun (1964), *Handbook of Mathematical Functions*

---

#### Elliptic Search
**Location**: `src/python/symbolic/elliptic_search.py`

**Purpose**: Specialized search pipeline for elliptic integrals.

**Search stages**:
1. **Signature detection**: Check for 2 incommensurable frequencies (FFT)
2. **Parameter estimation**: Estimate m from quasi-periodic data
3. **Pattern matching**: Try known elliptic patterns
4. **Hybrid SINDy**: Sparse regression on polynomial + elliptic basis

**Usage**:
```python
from src.python.symbolic.elliptic_search import (
    search_elliptic_integral,
    elliptic_pattern_match,
    elliptic_sindy_hybrid
)

# Full elliptic search
result = search_elliptic_integral(times, states, mu=mu)

if result.success:
    print(f"Found elliptic integral!")
    print(f"Expression: {result.expression}")
    print(f"Parameter m: {result.m:.4f}")
    print(f"Confidence: {result.confidence:.3f}")

    # Validate
    print(f"Conservation error: {result.conservation_error:.2e}")
else:
    print("No elliptic integral found")
    print(f"Reason: {result.failure_reason}")
```

**Tests**: `tests/wp3/test_specialized_search.py`

---

### Phase 3: Spinor Search

**Location**: `src/python/symbolic/spinor_search.py`

**Purpose**: Specialized search for spinor-based conserved quantities.

**Search pipeline**:
1. **Regularization benefit**: Check if close encounters occur (r < 0.1)
2. **Pattern recognition**: Match to known spinor patterns
3. **Spinor SINDy**: LASSO regression on spinor basis

**Known patterns**:
- **Spinor angular momentum**: L_spinor = Σ u_i × u̇_i
- **Spinor energy**: H_spinor = Σ |u̇_i|²/2 - 1/|u_i|²
- **Bilinear invariants**: u_i · u_j, u_i × u_j

**Usage**:
```python
from src.python.symbolic.spinor_search import (
    search_spinor_integral,
    detect_regularization_benefit,
    spinor_pattern_recognition
)

# Check if regularization would help
has_close_encounters = detect_regularization_benefit(times, states)
print(f"Close encounters detected: {has_close_encounters}")

# Pattern recognition
patterns = spinor_pattern_recognition(times, states)
print(f"Detected patterns: {patterns}")

# Full spinor search
result = search_spinor_integral(times, states, mu=mu)

if result.success:
    print(f"Expression: {result.expression}")
    print(f"Pattern type: {result.pattern_type}")
```

**Tests**: `tests/wp3/test_specialized_search.py::test_spinor_search`

---

### Phase 4: Theta Function Basis

**Location**: `src/python/symbolic/theta_basis.py`

**Purpose**: Jacobi theta functions for **completely integrable** systems.

**Theory**: Theta functions θ_i(z, q) are meromorphic functions with two periods (doubly periodic in complex plane). They arise naturally in completely integrable systems via the Abel-Jacobi map.

**Four Jacobi theta functions**:
```
θ₁(z, q) = 2q^(1/4) sin(z) (1 - 2q cos(2z) + ...)
θ₂(z, q) = 2q^(1/4) cos(z) (1 + 2q cos(2z) + ...)
θ₃(z, q) = 1 + 2q cos(2z) + 2q^4 cos(4z) + ...
θ₄(z, q) = 1 - 2q cos(2z) + 2q^4 cos(4z) + ...
```

where q = e^(iπτ) is the **nome** (depends on elliptic modulus).

**Usage**:
```python
from src.python.symbolic.theta_basis import (
    generate_theta_basis,
    theta1, theta2, theta3, theta4,
    estimate_nome
)

# Estimate nome from trajectory
q = estimate_nome(times, states)
print(f"Estimated nome q = {q:.6f}")

# Generate theta basis
basis_funcs = generate_theta_basis(q=q)

# Evaluate theta functions
z = np.angle(states[:, 0] + 1j * states[:, 1])  # complex argument
theta1_vals = theta1(z, q)
theta2_vals = theta2(z, q)
theta3_vals = theta3(z, q)
theta4_vals = theta4(z, q)

# Verify identity: θ₃² = θ₂² + θ₄²
assert np.allclose(theta3_vals**2, theta2_vals**2 + theta4_vals**2, atol=1e-10)
```

**Tests**: `tests/wp3/test_theta_basis.py`

**Reference**: Whittaker & Watson (1927), *A Course of Modern Analysis*

---

### Multi-Stage Pipeline

**Location**: `src/python/symbolic/multi_stage_pipeline.py`

**Purpose**: Coordinate all search methods and rank candidates.

**Pipeline stages**:
1. **Stage 1 (Spinor)**: Search in spinor basis (if close encounters detected)
2. **Stage 2 (Elliptic)**: Search in elliptic basis (if quasi-periodic)
3. **Stage 3 (Theta)**: Search in theta basis (if completely integrable signature)
4. **Stage 4 (Polynomial)**: Fallback to polynomial/rational basis
5. **Ranking**: Score all candidates by confidence, conservation, interpretability
6. **Triviality filtering**: Remove known integrals (E, L, C)
7. **Independence checking**: Verify candidates are functionally independent

**Usage**:
```python
from src.python.symbolic.multi_stage_pipeline import MultiStageInvariantSearch

# Create pipeline
search = MultiStageInvariantSearch(
    stages=['spinor', 'elliptic', 'theta', 'polynomial'],
    max_candidates_per_stage=5,
    enable_ranking=True,
    enable_triviality_check=True,
    enable_independence_check=True
)

# Run all stages
results = search.run(times, states, mu=mu, energy=energy, angular_momentum=L)

# Top candidates (ranked)
print(f"\nFound {len(results.all_candidates)} total candidates")
print(f"After filtering: {len(results.top_candidates)} non-trivial, independent candidates")

for i, cand in enumerate(results.top_candidates[:5]):
    print(f"\n=== Candidate {i+1} ===")
    print(f"Expression: {cand.expression}")
    print(f"Method: {cand.method}")
    print(f"Confidence: {cand.confidence:.3f}")
    print(f"Conservation: {cand.conservation_error:.2e}")
    print(f"Interpretability: {cand.interpretability_score:.3f}")
    print(f"Is trivial: {cand.is_trivial}")
    print(f"Independent of E,L,C: {cand.is_independent}")
```

**Tests**: `tests/wp3/test_multi_stage_pipeline.py`

---

## Available Tests

### Running Tests

```bash
# All WP3 tests
pytest tests/wp3/ -v

# Specific phase
pytest tests/wp3/test_spinor_basis.py -v
pytest tests/wp3/test_elliptic_basis.py -v

# End-to-end validation
pytest tests/wp3/test_end_to_end_known_cases.py -v

# Performance tests (may be slow)
pytest tests/wp3/ -v -m "not slow"
```

### Test Coverage

| Test File | Purpose | Key Tests |
|-----------|---------|-----------|
| `test_spinor_basis.py` | Spinor basis functions | KS transform, bilinear relation, basis generation |
| `test_elliptic_basis.py` | Elliptic functions | Jacobi sn/cn/dn, identities, parameter estimation |
| `test_theta_basis.py` | Theta functions | θ₁₋₄, identities, nome estimation |
| `test_enhanced_validation.py` | Validation methods | Multi-scale, quasi-periodic, long-time |
| `test_interpretability.py` | Function classification | Type detection, scoring, symmetries |
| `test_specialized_search.py` | Search algorithms | Spinor search, elliptic search |
| `test_multi_stage_pipeline.py` | Pipeline integration | Coordinated search, ranking |
| `test_triviality_and_independence.py` | Filtering | Known integral detection, Jacobian rank |
| `test_end_to_end_known_cases.py` | E2E validation | Lagrange points, figure-8, known integrals |

**Total tests**: ~50 tests across 12 files

---

## Examples and Workflows

### Example 1: Discover Jacobi Constant in CR3BP

```python
from src.python.symbolic.multi_stage_pipeline import MultiStageInvariantSearch
from src.python.integrators.ias15 import IAS15Integrator
import numpy as np

# CR3BP trajectory (should recover Jacobi constant C)
mu = 0.012150585609624
integrator = IAS15Integrator(mu=mu)
state0 = np.array([1.15, 0.0, 0.0, 0.0, 0.1, 0.0])
times, states = integrator.integrate(state0, (0, 100), dt=0.1)

# Search for integrals
search = MultiStageInvariantSearch(stages=['polynomial'])
results = search.run(times, states, mu=mu)

# Should find C = 2Ω - v²
for cand in results.top_candidates:
    if 'omega' in cand.expression.lower() or 'jacobi' in cand.expression.lower():
        print(f"Found Jacobi constant: {cand.expression}")
        print(f"Conservation: {cand.conservation_error:.2e}")
```

### Example 2: Search for Integrals in S¹ Lift

```python
from src.python.lifts.s1_bundle import S1Bundle
from src.python.symbolic.multi_stage_pipeline import MultiStageInvariantSearch

# Create S¹ bundle
bundle = S1Bundle(masses=masses, angular_momentum=1.0)

# Lift trajectory to S¹ bundle
shape_trajectory = [...]  # from WP2
lifted_trajectory = bundle.lift(shape_trajectory)

# Extract lifted states (includes θ coordinate and p_θ momentum)
lifted_times = lifted_trajectory['times']
lifted_states = lifted_trajectory['states']  # (s, θ, p_s, p_θ)

# Search for integrals in lifted space
search = MultiStageInvariantSearch(
    stages=['polynomial', 'spinor'],
    lifted_space=True  # tells pipeline about extra coordinates
)

results = search.run(lifted_times, lifted_states, mu=mu)

# Check if fiber momentum p_θ is conserved
for cand in results.top_candidates:
    if 'p_theta' in cand.expression or cand.expression == 'p[3]':  # p_θ is 4th momentum
        print(f"Fiber momentum p_θ conserved!")
        print(f"Conservation error: {cand.conservation_error:.2e}")
```

### Example 3: KS-Spinor Search for Collision Orbit

```python
from src.python.regularization.ks_transform import ks_transform
from src.python.symbolic.spinor_search import search_spinor_integral

# Generate collision-prone trajectory
state0 = np.array([0.1, 0.0, 0.0, 0.0, 2.0, 0.0])  # high eccentricity
times, states = integrator.integrate(state0, (0, 50), dt=0.01)

# Check for close encounters
min_distance = np.min([
    np.linalg.norm(states[:, :3] - states[:, 3:6], axis=1),  # r₁₂
    np.linalg.norm(states[:, 3:6] - states[:, 6:9], axis=1),  # r₂₃
    np.linalg.norm(states[:, 6:9] - states[:, :3], axis=1)   # r₃₁
])
print(f"Minimum distance: {min_distance:.4f}")

if min_distance < 0.1:
    print("Close encounter detected! Searching in spinor basis...")

    # Spinor search
    result = search_spinor_integral(times, states, mu=mu)

    if result.success:
        print(f"Found spinor integral: {result.expression}")
        print(f"Pattern: {result.pattern_type}")
        print(f"Conservation: {result.conservation_error:.2e}")
```

---

## Mathematical Framework

### The Discovery Problem

**Given**: Trajectory data {(t_i, **x**_i)} with **x** ∈ ℝ^n (phase space)

**Find**: Function I(**x**) such that:
1. **Conservation**: dI/dt = {I, H} = 0 along trajectory
2. **Independence**: I is not a function of known integrals (E, L, C)
3. **Non-triviality**: I is not constant or trivial combination

### Sparse Regression (SINDy)

**Idea**: Express I as sparse linear combination of basis functions:

```
I(x) = Σ c_i φ_i(x)
```

where φ_i are basis functions and most c_i = 0 (sparse).

**Method**: LASSO regression (L1 regularization)
```
min ||Φc - I_data||₂² + λ||c||₁
```

**Advantage**: Automatically selects relevant basis functions.

### Basis Function Libraries

| Basis | Functions | Use Case |
|-------|-----------|----------|
| **Polynomial** | x, y, x², xy, x³, ... | General search |
| **Rational** | 1/r, 1/(1+r²), ... | Gravitational systems |
| **Spinor** | \|u\|², u·v, u×v, ... | Regularized collisions |
| **Elliptic** | sn, cn, dn | Quasi-periodic motion |
| **Theta** | θ₁, θ₂, θ₃, θ₄ | Completely integrable |

### Functional Independence

**Test**: Compute Jacobian of {E, L, C, I}:

```
J = [∂E/∂x  ∂E/∂y  ∂E/∂z  ...]
    [∂L/∂x  ∂L/∂y  ∂L/∂z  ...]
    [∂C/∂x  ∂C/∂y  ∂C/∂z  ...]
    [∂I/∂x  ∂I/∂y  ∂I/∂z  ...]
```

**Criterion**: rank(J) = number of integrals (if independent)

---

## References

### Science Research Documents

1. **`WP3 – Generalized KS Transformations and N-Body Regularizations.pdf`**
   KS transformation theory and spinor regularization.

2. **`Abelianizing Variational Equations in the Three-Body Problem: Constraints and Transformations.pdf`**
   Theoretical framework for lift-integrability.

### Project Design Documents

1. **`Project-Design-Docs/WP3/AMENDED-WP3.3-COMPLETE-IMPLEMENTATION-SUMMARY.md`**
   Complete implementation report for all 4 phases.

2. **`Project-Design-Docs/WP3/WP3.1-ML-Discovery-Summary.md`**
   Machine learning approaches (HNN, SINDy).

3. **`Project-Design-Docs/WP3/WP3.2-Symbolic-Regression-Summary.md`**
   Symbolic regression pipeline details.

4. **`Project-Design-Docs/WP3/AMENDED_WP3.3-Symbolic-Regression-Summary.md`**
   Amended implementation with all 4 phases.

### External References

- **Brunton et al. (2016)**: "Discovering governing equations from data by sparse identification of nonlinear dynamical systems", *PNAS*, 113(15):3932-3937
- **Cranmer et al. (2020)**: "Discovering symbolic models from deep learning with inductive biases", *NeurIPS*
- **Kustaanheimo & Stiefel (1965)**: "Perturbation theory of Kepler motion based on spinor regularization"
- **Abramowitz & Stegun (1964)**: *Handbook of Mathematical Functions*, Chapter 16-17 (Elliptic & Theta functions)

---

## Next Steps

Once you're comfortable with WP3, proceed to:

- **User-Guide-WP4.md**: Rigorous validation of discovered integrals using Morales-Ramis and statistical tests
- **User-Guide-WP5.md**: Publication preparation and reproducibility package

To use WP3 effectively:
1. Start with known cases (Jacobi constant, Lagrange points) to verify the pipeline
2. Use multi-stage search for comprehensive coverage
3. Always validate candidates with WP4 methods before claiming discovery
4. Check interpretability scores to guide analytical investigation

---

**Last Updated**: November 25, 2025
**WP3 Status**: ✅ 100% Complete - All phases implemented and tested
