# User Guide: Work Package 4
## Rigorous Validation and Falsification ("The Gauntlet")

**Status**: ✅ 100% Complete (All validation infrastructure implemented)
**Purpose**: Subject candidate integrals from WP3 to rigorous analytical and numerical tests
**Role in Project**: The "quality control" that distinguishes genuine discovery from numerical artifact

---

## Table of Contents

1. [Overview](#overview)
2. [How WP4 Fits into the Overall Project](#how-wp4-fits-into-the-overall-project)
3. [What's Implemented](#whats-implemented)
4. [Quick Start Guide](#quick-start-guide)
5. [Core Components](#core-components)
6. [Available Tests](#available-tests)
7. [Examples and Workflows](#examples-and-workflows)
8. [The Validation Gauntlet](#the-validation-gauntlet)
9. [Mathematical Framework](#mathematical-framework)
10. [References](#references)

---

## Overview

Work Package 4 implements **rigorous validation** of candidate conserved quantities discovered by WP3. The three-body problem has a 200+ year history of false claims of integrability. WP4 ensures that **only rigorously validated results** proceed to publication (WP5).

### Key Questions

1. *Is the candidate truly conserved, or just slowly varying?*
   → Answer: Multi-scale conservation testing + symbolic Poisson brackets

2. *Is it functionally independent of known integrals (E, L, C)?*
   → Answer: Jacobian rank test on 10⁴+ sample points

3. *Does it Poisson-commute with other integrals?*
   → Answer: Symbolic or numerical computation of {I, J}

4. *Is the system compatible with Morales-Ramis theory?*
   → Answer: Differential Galois group analysis (downstairs non-abelian, upstairs abelian)

5. *Does conservation hold across the entire parameter space?*
   → Answer: Monte Carlo validation over 10⁵+ initial conditions

### Scientific Context

**Morales-Ramis Theorem**: If a Hamiltonian system is integrable, then the differential Galois group of its Normal Variational Equations (NVE) along any particular solution must have an abelian identity component.

**Contrapositive**: If the Galois group is non-abelian, the system is **not integrable**.

**For Lift-Integrability**:
- **Downstairs** (reduced space): Expect non-abelian → confirms classical non-integrability
- **Upstairs** (lifted space): Expect abelian → validates lift-integrability hypothesis

**Reference**: See `Science-Research-Docs/Abelianizing Variational Equations in the Three-Body Problem.pdf`

---

## How WP4 Fits into the Overall Project

```
┌──────────────────────────────────────────────────────────┐
│ WP3: Invariant Discovery                                  │
│ • Provides: Candidate integrals Ĩ₁, Ĩ₂, ..., Ĩₙ          │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ↓
┌──────────────────────────────────────────────────────────┐
│ WP4: Rigorous Validation (THIS GUIDE)                     │
│                                                            │
│ ┌────────────────────────────────────────────────────┐   │
│ │ WP 4.1: Analytical Vetting                          │   │
│ │ ┌──────────────────────────────────────────────┐   │   │
│ │ │ Task 4.1.1: Poisson Bracket (Conservation)   │   │   │
│ │ │ • Compute {Ĩ, H̃} symbolically or numerically │   │   │
│ │ │ • Threshold: |{Ĩ, H̃}| < 10⁻¹²               │   │   │
│ │ │ • Kill Switch: If not conserved → REJECT     │   │   │
│ │ └──────────────────────────────────────────────┘   │   │
│ │ ┌──────────────────────────────────────────────┐   │   │
│ │ │ Task 4.1.2: Involution Test                  │   │   │
│ │ │ • Verify {Ĩ, E} = 0, {Ĩ, L} = 0              │   │   │
│ │ │ • For multiple integrals: {Ĩᵢ, Ĩⱼ} = 0      │   │   │
│ │ │ • Threshold: |{·,·}| < 10⁻¹⁰                 │   │   │
│ │ └──────────────────────────────────────────────┘   │   │
│ │ ┌──────────────────────────────────────────────┐   │   │
│ │ │ Task 4.1.3: Functional Independence          │   │   │
│ │ │ • Jacobian rank test on 10⁴ sample states    │   │   │
│ │ │ • rank(∇E, ∇L, ∇C, ∇Ĩ) must increase by 1   │   │   │
│ │ │ • Pass rate: >99% of samples                 │   │   │
│ │ └──────────────────────────────────────────────┘   │   │
│ └────────────────────┬───────────────────────────────┘   │
│                      │ Survivors only                     │
│                      ↓                                     │
│ ┌────────────────────────────────────────────────────┐   │
│ │ WP 4.2: Complete Morales-Ramis Test (AMENDED)      │   │
│ │ ┌──────────────────────────────────────────────┐   │   │
│ │ │ PHASE I: Downstairs (Defensive Falsification)│   │   │
│ │ │ • Compute NVE along periodic orbits          │   │   │
│ │ │ • Apply Kovacic algorithm                    │   │   │
│ │ │ • Verify: Galois group NON-ABELIAN          │   │   │
│ │ │ • Confirms: Classical non-integrability      │   │   │
│ │ └──────────────────────────────────────────────┘   │   │
│ │ ┌──────────────────────────────────────────────┐   │   │
│ │ │ PHASE II: Upstairs (Compatibility Test) ⭐   │   │   │
│ │ │ • Lift periodic orbits to S¹/KS space       │   │   │
│ │ │ • Compute NVE in lifted coordinates          │   │   │
│ │ │ • Apply Kovacic algorithm upstairs           │   │   │
│ │ │ • Verify: Galois group ABELIAN              │   │   │
│ │ │ • Validates: Lift-integrability hypothesis   │   │   │
│ │ └──────────────────────────────────────────────┘   │   │
│ │ • Verdict: abelian upstairs + WP3 integrals?     │   │
│ │   → SUCCESS | non-abelian → SPURIOUS           │   │
│ └────────────────────┬───────────────────────────────┘   │
│                      │ Validated candidates               │
│                      ↓                                     │
│ ┌────────────────────────────────────────────────────┐   │
│ │ WP 4.3: Numerical Robustness & Generalization      │   │
│ │ • Monte Carlo: 10⁵ initial conditions             │   │
│ │ • Stress testing: near-collisions, high chaos      │   │
│ │ • Long-time: 10⁴-10⁶ periods                      │   │
│ │ • Statistical validation: drift < ε_H              │   │
│ └────────────────────────────────────────────────────┘   │
└────────────────────┬─────────────────────────────────────┘
                     │ Publication-ready results
                     ↓
┌──────────────────────────────────────────────────────────┐
│ WP5: Publication & Dissemination                          │
│ • Formal proof construction                               │
│ • Reproducibility package                                 │
│ • Manuscript preparation                                  │
└──────────────────────────────────────────────────────────┘
```

**WP4's Critical Role**: Acts as the **gatekeeper** between discovery and publication. Only candidates passing all three stages (4.1, 4.2, 4.3) are considered validated.

---

## What's Implemented

WP4 is **100% complete** with full validation infrastructure.

### File Structure

```
src/python/validation/
├── analytical_vetting.py          # WP 4.1: Analytical tests
│   ├── PoissonBracketValidator    # Task 4.1.1
│   ├── InvolutionTester           # Task 4.1.2
│   └── IndependenceTester         # Task 4.1.3
│
├── morales_ramis_validator.py     # WP 4.2: Morales-Ramis test
│   ├── MoralesRamisValidator      # Main validator
│   ├── DownstairsNVE              # Phase I (reduced space)
│   └── UpstairsNVE                # Phase II (lifted space)
│
├── variational_equations.py       # NVE computation
│   ├── compute_nve_matrix         # Compute ∇²H (Hessian)
│   ├── integrate_variational      # Integrate δx(t)
│   └── extract_monodromy_matrix   # For periodic orbits
│
├── kovacic.py                      # Kovacic algorithm
│   ├── kovacic_algorithm          # Determine Galois group
│   ├── check_abelian              # Test if abelian
│   └── compute_differential_galois_group
│
├── monte_carlo_validator.py        # WP 4.3: Numerical robustness
│   ├── MonteCarloValidator        # Large-scale testing
│   ├── ParameterSpaceSweep        # Systematic sampling
│   └── StatisticalSummary         # Results aggregation
│
├── stress_tester.py                # Extreme scenarios
│   ├── CollisionStressTester      # Near r→0 testing
│   ├── ChaoticRegionTester        # High Lyapunov regions
│   └── EscapeOrbitTester          # Unbounded motion
│
├── long_time_validator.py          # Long integration
│   ├── LongTimeConservationTest   # Track drift over 10⁴-10⁶ periods
│   └── ShadowHamiltonianComparison # Compare with integrator error
│
├── conservation_validator.py       # Conservation testing
├── poisson_brackets.py             # Poisson bracket computation
├── independence_tester.py          # Functional independence
├── involution_tester.py            # Involution testing
├── compatibility_test.py           # Morales-Ramis compatibility
├── periodic_orbits.py              # Periodic orbit library
├── upstairs_variational.py         # Upstairs NVE computation
└── statistical_reporter.py         # Validation reports

tests/validation/
├── test_kovacic.py                 # Kovacic algorithm tests
├── test_periodic_orbits.py         # Periodic orbit tests
├── test_lagrange_equilibrium.py    # Lagrange point tests
└── test_chaos_indicators.py        # Chaos detection tests
```

### Implementation Status

| Component | Status | Files | Purpose |
|-----------|--------|-------|---------|
| **WP 4.1** (Analytical) | ✅ Complete | 5 files | Poisson brackets, involution, independence |
| **WP 4.2 Phase I** (Downstairs MR) | ✅ Complete | 4 files | NVE, Kovacic, non-abelian test |
| **WP 4.2 Phase II** (Upstairs MR) | ✅ Complete | 3 files | Upstairs NVE, abelian test |
| **WP 4.3** (Numerical) | ✅ Complete | 4 files | Monte Carlo, stress tests, long-time |
| **Infrastructure** | ✅ Complete | 6 files | Periodic orbits, reporting, utilities |

---

## Quick Start Guide

### 1. Analytical Vetting (WP 4.1)

```python
from src.python.validation.analytical_vetting import (
    PoissonBracketValidator,
    InvolutionTester,
    IndependenceTester
)

# Candidate integral from WP3
def candidate_integral(state, mu):
    """Example: Jacobi constant"""
    x, y, z, vx, vy, vz = state
    r1 = np.sqrt((x + mu)**2 + y**2 + z**2)
    r2 = np.sqrt((x - 1 + mu)**2 + y**2 + z**2)
    Omega = 0.5 * (x**2 + y**2) + (1 - mu) / r1 + mu / r2
    return 2 * Omega - (vx**2 + vy**2 + vz**2)

# Task 4.1.1: Test conservation {I, H} = 0
pb_validator = PoissonBracketValidator(mu=0.012150585609624)
result = pb_validator.test_conservation(
    integral_func=candidate_integral,
    num_samples=1000
)
print(f"Conservation test: {result.passed}")
print(f"Max Poisson bracket: {result.max_poisson_bracket:.2e}")

# Task 4.1.2: Test involution {I, E} = 0, {I, L} = 0
inv_tester = InvolutionTester(mu=0.012150585609624)
result = inv_tester.test_involution(
    integral_func=candidate_integral,
    known_integrals=['energy', 'angular_momentum']
)
print(f"Involution test: {result.passed}")
for integral, pb_value in result.poisson_brackets.items():
    print(f"  {{I, {integral}}} = {pb_value:.2e}")

# Task 4.1.3: Test independence
ind_tester = IndependenceTester(mu=0.012150585609624)
result = ind_tester.test_independence(
    integral_func=candidate_integral,
    known_integrals=['energy', 'angular_momentum', 'jacobi_constant'],
    num_samples=10000
)
print(f"Independence test: {result.passed}")
print(f"Jacobian rank increased: {result.rank_increased}")
print(f"Pass rate: {result.pass_rate:.1%}")
```

### 2. Morales-Ramis Test (WP 4.2)

```python
from src.python.validation.morales_ramis_validator import MoralesRamisValidator
from src.python.validation.periodic_orbits import get_lagrange_l4_orbit

# Get a periodic orbit (e.g., Lagrange L4 equilateral configuration)
periodic_orbit = get_lagrange_l4_orbit(mu=0.012150585609624)

# Create Morales-Ramis validator
mr_validator = MoralesRamisValidator(mu=0.012150585609624)

# PHASE I: Downstairs (reduced space)
print("=== PHASE I: Downstairs Morales-Ramis Test ===")
downstairs_result = mr_validator.test_downstairs(
    periodic_orbit=periodic_orbit
)
print(f"Downstairs Galois group: {downstairs_result.galois_group}")
print(f"Is abelian: {downstairs_result.is_abelian}")
print(f"Expected: NON-ABELIAN (confirms classical obstruction)")

# PHASE II: Upstairs (S¹ lift or KS-Spinor)
print("\n=== PHASE II: Upstairs Morales-Ramis Test ===")
upstairs_result = mr_validator.test_upstairs(
    periodic_orbit=periodic_orbit,
    lift_type='s1_bundle'  # or 'ks_spinor'
)
print(f"Upstairs Galois group: {upstairs_result.galois_group}")
print(f"Is abelian: {upstairs_result.is_abelian}")
print(f"Expected: ABELIAN (validates lift-integrability)")

# Compatibility verdict
if not downstairs_result.is_abelian and upstairs_result.is_abelian:
    print("\n✓ LIFT-INTEGRABILITY COMPATIBLE!")
    print("  Downstairs: non-abelian (classical obstruction)")
    print("  Upstairs: abelian (lift removes obstruction)")
else:
    print("\n✗ Not compatible with lift-integrability hypothesis")
```

### 3. Monte Carlo Validation (WP 4.3)

```python
from src.python.validation.monte_carlo_validator import MonteCarloValidator

# Create Monte Carlo validator
mc_validator = MonteCarloValidator(
    integral_func=candidate_integral,
    mu=0.012150585609624,
    num_samples=100000
)

# Run validation across parameter space
print("Running Monte Carlo validation (100,000 samples)...")
result = mc_validator.validate(
    param_ranges={
        'x': (0.5, 1.5),
        'y': (-0.5, 0.5),
        'vx': (-0.5, 0.5),
        'vy': (0.0, 1.0)
    },
    integration_time=100.0  # 100 time units
)

# Statistical summary
print(f"\nConservation statistics:")
print(f"  Mean error: {result.mean_error:.2e}")
print(f"  Median error: {result.median_error:.2e}")
print(f"  95th percentile: {result.percentile_95:.2e}")
print(f"  Pass rate (error < 1e-10): {result.pass_rate:.1%}")

# Stress testing
print(f"\nStress test results:")
print(f"  Near-collision tests: {result.collision_tests_passed}/{result.collision_tests_total}")
print(f"  Chaotic region tests: {result.chaos_tests_passed}/{result.chaos_tests_total}")
print(f"  Escape orbit tests: {result.escape_tests_passed}/{result.escape_tests_total}")
```

---

## Core Components

### WP 4.1: Analytical Vetting

#### Task 4.1.1: Poisson Bracket (Conservation)
**Location**: `src/python/validation/poisson_brackets.py`

**Theory**: For conserved quantity I:
```
dI/dt = {I, H} = Σ (∂I/∂qᵢ ∂H/∂pᵢ - ∂I/∂pᵢ ∂H/∂qᵢ)
```

Conservation requires {I, H} = 0.

**Implementation**:
- **Symbolic** (if expression available): Use SymPy to compute {I, H} symbolically
- **Numerical** (fallback): Finite difference approximation

**Usage**:
```python
from src.python.validation.poisson_brackets import compute_poisson_bracket

# Symbolic (preferred)
import sympy as sp
x, y, vx, vy = sp.symbols('x y vx vy')
I_expr = x**2 + y**2  # example
H_expr = (vx**2 + vy**2) / 2 + x**2 * y**2  # example
pb_symbolic = compute_poisson_bracket(I_expr, H_expr, symbolic=True)
print(f"{{I, H}} = {pb_symbolic}")

# Numerical
state = np.array([1.0, 0.5, 0.0, 0.3, 0.5, 0.0])
pb_numerical = compute_poisson_bracket(
    integral_func=candidate_integral,
    hamiltonian_func=hamiltonian,
    state=state,
    mu=mu
)
print(f"{{I, H}} ≈ {pb_numerical:.2e}")
```

**Acceptance threshold**: |{I, H}| < 10⁻¹² (symbolic zero or quad precision)

---

#### Task 4.1.2: Involution Test
**Location**: `src/python/validation/involution_tester.py`

**Theory**: For integrability, all integrals must mutually Poisson-commute:
```
{I₁, I₂} = 0,  {I₁, I₃} = 0,  {I₂, I₃} = 0, ...
```

**Liouville Integrability**: n-DOF system needs n independent integrals in involution.

**Usage**:
```python
from src.python.validation.involution_tester import test_involution

# Test if new integral I commutes with E, L, C
result = test_involution(
    integrals=[
        ('Energy', energy_func),
        ('Angular Momentum', angular_momentum_func),
        ('Jacobi Constant', jacobi_constant_func),
        ('New Integral', candidate_integral)
    ],
    mu=mu,
    num_samples=1000
)

print("Involution matrix (Poisson brackets):")
print(result.involution_matrix)
# Expected output (if in involution):
# [[0,   0,   0,   0  ]
#  [0,   0,   0,   0  ]
#  [0,   0,   0,   0  ]
#  [0,   0,   0,   0  ]]

print(f"All in involution: {result.all_commute}")
```

**Acceptance threshold**: |{Iᵢ, Iⱼ}| < 10⁻¹⁰

---

#### Task 4.1.3: Functional Independence
**Location**: `src/python/validation/independence_tester.py`

**Theory**: Integrals I₁, ..., Iₖ are functionally independent if their gradients are linearly independent:

```
rank([∇I₁, ∇I₂, ..., ∇Iₖ]) = k
```

**Test**: Compute Jacobian matrix at many points, check rank.

**Usage**:
```python
from src.python.validation.independence_tester import test_functional_independence

# Test if new integral is independent of E, L, C
result = test_functional_independence(
    integrals=[energy_func, angular_momentum_func, jacobi_constant_func, candidate_integral],
    mu=mu,
    num_samples=10000,
    tolerance=1e-6  # rank tolerance
)

print(f"Jacobian rank: {result.rank}")
print(f"Expected rank (if independent): {len(integrals)}")
print(f"Pass rate: {result.pass_rate:.1%}")  # % of samples where rank = len(integrals)

if result.pass_rate > 0.99:
    print("✓ New integral is functionally independent!")
else:
    print("✗ New integral is likely dependent on known integrals")
```

**Acceptance threshold**: Pass rate >99% (rank increases by 1 at >99% of sample points)

---

### WP 4.2: Morales-Ramis Test

#### PHASE I: Downstairs (Reduced Space)
**Location**: `src/python/validation/morales_ramis_validator.py`

**Purpose**: Prove the 3BP is non-integrable in reduced (downstairs) coordinates.

**Steps**:
1. **Select periodic orbit**: E.g., Lagrange L4 equilateral configuration
2. **Compute NVE**: Normal Variational Equations along this orbit
   ```
   δẍ = ∇²H(x(t)) δx
   ```
   where x(t) is the periodic orbit and δx is perturbation.

3. **Apply Kovacic algorithm**: Determine differential Galois group from NVE
4. **Check**: Is Galois group abelian?

**Expected result**: **NON-ABELIAN** → confirms Bruns/Poincaré (3BP is not integrable downstairs)

**Usage**:
```python
from src.python.validation.variational_equations import compute_nve_along_orbit
from src.python.validation.kovacic import apply_kovacic_algorithm
from src.python.validation.periodic_orbits import get_lagrange_l4_orbit

# 1. Get periodic orbit
orbit = get_lagrange_l4_orbit(mu=0.012150585609624)

# 2. Compute NVE
nve_matrix = compute_nve_along_orbit(
    orbit=orbit,
    mu=mu,
    coordinate_system='reduced'  # shape space
)

# 3. Apply Kovacic algorithm
galois_result = apply_kovacic_algorithm(nve_matrix)

print(f"Galois group: {galois_result.group_name}")
print(f"Is abelian: {galois_result.is_abelian}")
# Expected: False (SL(2,C) or non-abelian subgroup)
```

**Mathematical details**: See `src/python/validation/kovacic.py` for Kovacic algorithm implementation.

---

#### PHASE II: Upstairs (Lifted Space) ⭐ CRITICAL
**Location**: `src/python/validation/upstairs_variational.py`

**Purpose**: Test if the lifted system (S¹ bundle or KS-Spinor) has abelian Galois structure.

**Steps**:
1. **Lift periodic orbit**: From shape space to S¹ bundle or KS-Spinor space
2. **Compute upstairs NVE**: Using extended Hamiltonian H̃ and extended symplectic form ω̃
3. **Apply Kovacic upstairs**: Determine Galois group in lifted coordinates
4. **Check**: Is Galois group abelian?

**Expected result (if lift-integrable)**: **ABELIAN** → validates lift-integrability hypothesis

**Usage**:
```python
from src.python.validation.upstairs_variational import compute_upstairs_nve
from src.python.lifts.s1_bundle import S1Bundle

# 1. Lift orbit to S¹ bundle
bundle = S1Bundle(masses=masses, angular_momentum=1.0)
lifted_orbit = bundle.lift_orbit(orbit)

# 2. Compute upstairs NVE
upstairs_nve = compute_upstairs_nve(
    lifted_orbit=lifted_orbit,
    lift_type='s1_bundle',
    mu=mu
)

# 3. Apply Kovacic algorithm upstairs
galois_upstairs = apply_kovacic_algorithm(upstairs_nve)

print(f"Upstairs Galois group: {galois_upstairs.group_name}")
print(f"Is abelian: {galois_upstairs.is_abelian}")
# Expected (if lift-integrable): True (abelian)
```

**Compatibility verdict**:
| Downstairs | Upstairs | WP3 Integrals | Verdict |
|------------|----------|---------------|---------|
| Non-abelian | Abelian | Found | ✓ **LIFT-INTEGRABLE** |
| Non-abelian | Non-abelian | Found | ✗ Spurious (artifacts) |
| Non-abelian | Abelian | Not found | ⚠ Integrals exist but missed |
| Non-abelian | Non-abelian | Not found | ○ Negative result confirmed |

---

#### Kovacic Algorithm
**Location**: `src/python/validation/kovacic.py`

**Purpose**: Determine the differential Galois group of a second-order linear ODE.

**Input**: Second-order ODE of the form:
```
y'' + a(x) y' + b(x) y = 0
```

**Output**: Galois group (SL(2,C), abelian subgroup, or finite)

**Usage**:
```python
from src.python.validation.kovacic import kovacic_algorithm

# Example: Harmonic oscillator y'' + ω²y = 0
a_coeff = lambda x: 0  # no y' term
b_coeff = lambda x: 1  # ω² = 1

result = kovacic_algorithm(a_coeff, b_coeff)
print(f"Galois group: {result.group}")
print(f"Is abelian: {result.is_abelian}")
# Expected: Abelian (harmonic oscillator is integrable)
```

**Tests**: `tests/validation/test_kovacic.py`

**Reference**: Kovacic, J. J. (1986), "An algorithm for solving second order linear homogeneous differential equations", *Journal of Symbolic Computation*, 2(1):3-43

---

### WP 4.3: Numerical Robustness

#### Monte Carlo Validation
**Location**: `src/python/validation/monte_carlo_validator.py`

**Purpose**: Test conservation across large ensemble of initial conditions.

**Method**:
1. Sample 10⁵ initial conditions (Sobol sequence for low discrepancy)
2. Integrate each for T periods
3. Measure conservation error: ΔI = max|I(t)| - min|I(t)|
4. Statistical analysis: mean, median, 95th percentile, pass rate

**Usage**:
```python
from src.python.validation.monte_carlo_validator import MonteCarloValidator

validator = MonteCarloValidator(
    integral_func=candidate_integral,
    mu=0.012150585609624,
    num_samples=100000
)

result = validator.validate(
    param_ranges={
        'x': (0.5, 1.5), 'y': (-0.5, 0.5), 'z': (0.0, 0.0),
        'vx': (-0.5, 0.5), 'vy': (0.0, 1.0), 'vz': (0.0, 0.0)
    },
    integration_time=100.0,
    tolerance=1e-10
)

print(f"Pass rate: {result.pass_rate:.1%}")
print(f"Mean conservation error: {result.mean_error:.2e}")
print(f"95th percentile error: {result.percentile_95:.2e}")
```

**Acceptance threshold**:
- Pass rate >95% (conservation error < 10⁻¹⁰)
- Mean error < 10⁻¹¹
- Drift rate < integrator error

---

#### Stress Testing
**Location**: `src/python/validation/stress_tester.py`

**Purpose**: Test in extreme scenarios.

**Test cases**:
1. **Near-collisions**: r₁₂, r₂₃, or r₃₁ < 0.01
2. **Chaotic regions**: High Lyapunov exponent (λ > 0.1)
3. **Escape orbits**: Unbounded motion (C < 0)

**Usage**:
```python
from src.python.validation.stress_tester import StressTester

tester = StressTester(integral_func=candidate_integral, mu=mu)

# Near-collision test
collision_result = tester.test_near_collisions(
    num_tests=1000,
    min_distance=0.01
)
print(f"Collision tests passed: {collision_result.pass_rate:.1%}")

# Chaotic region test
chaos_result = tester.test_chaotic_regions(
    num_tests=1000,
    min_lyapunov=0.1
)
print(f"Chaos tests passed: {chaos_result.pass_rate:.1%}")
```

---

#### Long-Time Validation
**Location**: `src/python/validation/long_time_validator.py`

**Purpose**: Verify conservation holds over extremely long integrations (10⁴-10⁶ periods).

**Comparison with shadow Hamiltonian**: For symplectic integrators, energy drift should match shadow Hamiltonian error. Conservation error for candidate integral should be similar.

**Usage**:
```python
from src.python.validation.long_time_validator import LongTimeValidator

validator = LongTimeValidator(integral_func=candidate_integral, mu=mu)

result = validator.validate(
    state0=initial_state,
    num_periods=10000,
    integrator='yoshida8'  # symplectic
)

print(f"Integration time: {result.total_time:.2f}")
print(f"Conservation drift: {result.drift:.2e}")
print(f"Energy drift: {result.energy_drift:.2e}")
print(f"Drift ratio (I/E): {result.drift / result.energy_drift:.3f}")

if abs(result.drift / result.energy_drift) < 10:
    print("✓ Conservation error comparable to integrator error")
else:
    print("✗ Conservation error exceeds expected integrator error")
```

**Acceptance threshold**: Drift ratio < 10 (conservation error within 10× of energy error)

---

## Available Tests

### Running Tests

```bash
# All validation tests
pytest tests/validation/ -v

# Kovacic algorithm
pytest tests/validation/test_kovacic.py -v

# Periodic orbits
pytest tests/validation/test_periodic_orbits.py -v

# Lagrange equilibria
pytest tests/validation/test_lagrange_equilibrium.py -v

# Integration tests (may be slow)
pytest tests/validation/ -v -m "not slow"
```

### Test Coverage

| Test File | Purpose | Key Tests |
|-----------|---------|-----------|
| `test_kovacic.py` | Kovacic algorithm | Harmonic oscillator (abelian), 3BP (non-abelian) |
| `test_periodic_orbits.py` | Periodic orbit library | Lagrange L4/L5, Lyapunov, Halo orbits |
| `test_lagrange_equilibrium.py` | Equilibrium points | L1-L5 locations, stability |
| `test_chaos_indicators.py` | MEGNO/FLI | Regular vs. chaotic classification |

---

## Examples and Workflows

### Example 1: Complete Validation of Jacobi Constant

```python
# WP3 "discovers" Jacobi constant (known result, validation test)
def jacobi_constant(state, mu):
    x, y, z, vx, vy, vz = state
    r1 = np.sqrt((x + mu)**2 + y**2 + z**2)
    r2 = np.sqrt((x - 1 + mu)**2 + y**2 + z**2)
    Omega = 0.5 * (x**2 + y**2) + (1 - mu) / r1 + mu / r2
    return 2 * Omega - (vx**2 + vy**2 + vz**2)

mu = 0.012150585609624

print("=== WP 4.1: Analytical Vetting ===")

# Task 4.1.1: Conservation
from src.python.validation.analytical_vetting import PoissonBracketValidator
pb_val = PoissonBracketValidator(mu=mu)
result = pb_val.test_conservation(jacobi_constant, num_samples=1000)
print(f"4.1.1 Conservation: {result.passed} (max PB = {result.max_poisson_bracket:.2e})")

# Task 4.1.2: Involution
from src.python.validation.involution_tester import InvolutionTester
inv_val = InvolutionTester(mu=mu)
result = inv_val.test_involution(jacobi_constant, ['energy', 'angular_momentum'])
print(f"4.1.2 Involution: {result.passed}")

# Task 4.1.3: Independence (C should be independent of E and L)
from src.python.validation.independence_tester import IndependenceTester
ind_val = IndependenceTester(mu=mu)
result = ind_val.test_independence(jacobi_constant, ['energy', 'angular_momentum'], num_samples=10000)
print(f"4.1.3 Independence: {result.passed} (pass rate = {result.pass_rate:.1%})")

print("\n=== WP 4.2: Morales-Ramis Test ===")

# Get periodic orbit
from src.python.validation.periodic_orbits import get_lagrange_l4_orbit
orbit = get_lagrange_l4_orbit(mu=mu)

# Downstairs (should be non-abelian)
from src.python.validation.morales_ramis_validator import MoralesRamisValidator
mr_val = MoralesRamisValidator(mu=mu)
downstairs = mr_val.test_downstairs(orbit)
print(f"4.2 Phase I (Downstairs): Galois group is {'abelian' if downstairs.is_abelian else 'non-abelian'}")

# Upstairs (in S¹ lift, C is not a new integral, so test would fail)
# But we can test the lift structure
upstairs = mr_val.test_upstairs(orbit, lift_type='s1_bundle')
print(f"4.2 Phase II (Upstairs): Galois group is {'abelian' if upstairs.is_abelian else 'non-abelian'}")

print("\n=== WP 4.3: Numerical Robustness ===")

# Monte Carlo
from src.python.validation.monte_carlo_validator import MonteCarloValidator
mc_val = MonteCarloValidator(jacobi_constant, mu=mu, num_samples=10000)  # reduced for speed
result = mc_val.validate(
    param_ranges={'x': (0.5, 1.5), 'y': (-0.5, 0.5), 'vx': (-0.5, 0.5), 'vy': (0.0, 1.0)},
    integration_time=50.0
)
print(f"4.3 Monte Carlo: Pass rate = {result.pass_rate:.1%}, Mean error = {result.mean_error:.2e}")

print("\n=== VERDICT ===")
if all([result.passed for result in [pb_val.last_result, inv_val.last_result, ind_val.last_result]]):
    print("✓ Jacobi constant is a VALIDATED conserved quantity!")
else:
    print("✗ Validation failed")
```

---

### Example 2: Validate S¹ Fiber Momentum

```python
# Test if p_θ (fiber momentum in S¹ bundle) is conserved

from src.python.lifts.s1_bundle import S1Bundle

# Create S¹ bundle
bundle = S1Bundle(masses=masses, angular_momentum=1.0)

# Define fiber momentum
def fiber_momentum(lifted_state, mu):
    """Extract p_θ from lifted state (s, θ, p_s, p_θ)"""
    return lifted_state[7]  # assuming p_θ is at index 7

# Lift trajectory
shape_trajectory = [...]  # from WP2
lifted_trajectory = bundle.lift(shape_trajectory)

# Run validation
from src.python.validation.analytical_vetting import PoissonBracketValidator

pb_val = PoissonBracketValidator(mu=mu, lifted_space=True)
result = pb_val.test_conservation(fiber_momentum, trajectory=lifted_trajectory)

if result.passed:
    print("✓ Fiber momentum p_θ is conserved!")
    print("  This is a NEW integral (beyond E, L, C)!")
else:
    print("✗ Fiber momentum not conserved")
    print(f"  Max Poisson bracket: {result.max_poisson_bracket:.2e}")
```

---

## The Validation Gauntlet

### Decision Flow

```
Candidate Integral Ĩ from WP3
    ↓
┌─────────────────────────────┐
│ Stage 1: Conservation Test  │
│ {Ĩ, H̃} = 0 ?                │
└──────────┬──────────────────┘
           │ NO → REJECT
           ↓ YES
┌─────────────────────────────┐
│ Stage 2: Involution Test    │
│ {Ĩ, E} = 0, {Ĩ, L} = 0 ?    │
└──────────┬──────────────────┘
           │ NO → REJECT
           ↓ YES
┌─────────────────────────────┐
│ Stage 3: Independence Test  │
│ rank(∇E,∇L,∇C,∇Ĩ) = 4 ?    │
└──────────┬──────────────────┘
           │ NO → REJECT (dependent)
           ↓ YES
┌─────────────────────────────┐
│ Stage 4: Morales-Ramis I    │
│ Downstairs non-abelian ?    │
└──────────┬──────────────────┘
           │ NO → ERROR (contradicts Bruns/Poincaré)
           ↓ YES
┌─────────────────────────────┐
│ Stage 5: Morales-Ramis II   │
│ Upstairs abelian ?          │
└──────────┬──────────────────┘
           │ NO → REJECT (spurious integral)
           ↓ YES
┌─────────────────────────────┐
│ Stage 6: Monte Carlo        │
│ Pass rate >95% ?            │
└──────────┬──────────────────┘
           │ NO → REJECT (not universal)
           ↓ YES
┌─────────────────────────────┐
│ Stage 7: Stress Tests       │
│ All scenarios pass ?        │
└──────────┬──────────────────┘
           │ NO → REJECT (not robust)
           ↓ YES
┌─────────────────────────────┐
│ Stage 8: Long-Time          │
│ Drift < 10×ε_H ?            │
└──────────┬──────────────────┘
           │ NO → REJECT (secular drift)
           ↓ YES
┌─────────────────────────────┐
│ ✓ VALIDATED INTEGRAL        │
│ Proceed to WP5 Publication  │
└─────────────────────────────┘
```

**Only candidates passing ALL 8 stages are considered publication-ready.**

---

## Mathematical Framework

### Normal Variational Equations (NVE)

For a trajectory x(t) satisfying ẋ = ∇H(x), the NVE describe the evolution of infinitesimal perturbations δx:

```
d/dt (δx) = ∇²H(x(t)) · δx
```

where ∇²H is the Hessian (second derivative matrix) of the Hamiltonian.

**Monodromy matrix**: For a periodic orbit with period T, the monodromy matrix M is:
```
M = solution of NVE at t=T with δx(0) = I
```

**Floquet multipliers**: Eigenvalues of M determine stability.

### Differential Galois Theory

**Picard-Vessiot theory**: Linear ODEs have an associated differential Galois group (analogous to Galois group in algebra).

**Morales-Ramis Theorem**: If a Hamiltonian system is integrable, then the identity component of the differential Galois group of the NVE (along any particular solution) is abelian.

**Contrapositive**: Non-abelian → Not integrable.

### Liouville Integrability

**Liouville's Theorem**: A Hamiltonian system with n degrees of freedom is completely integrable if:
1. There exist n independent integrals of motion I₁, ..., Iₙ
2. They are in involution: {Iᵢ, Iⱼ} = 0 for all i,j
3. The integrals are functionally independent

**Action-angle variables**: For integrable systems, canonical transformation to (θ, I) where I are constant (actions) and θ evolve linearly (angles).

---

## References

### Science Research Documents

1. **`Abelianizing Variational Equations in the Three-Body Problem: Constraints and Transformations.pdf`**
   Theoretical framework for upstairs Morales-Ramis test.

2. **`WP4 – Geometric & Cohomological Lifts in Triatomic and Three-Body Systems.pdf`**
   Cohomological aspects of lift-integrability.

3. **`Transforming Hamiltonian Variational Equations.pdf`**
   Variational equations in different coordinate systems.

### Project Design Documents

1. **`Project-Design-Docs/WP4/AMENDED_WP4-Complete-Overview.md`**
   Complete WP4 architecture with Phase II amendment.

2. **`Project-Design-Docs/WP4/WP4.1-Analytical-Vetting-Implementation-Plan.md`**
   Detailed plan for Poisson brackets, involution, independence.

3. **`Project-Design-Docs/WP4/AMENDED_WP4.2-Morales-Ramis-Implementation-Plan.md`**
   Two-phase Morales-Ramis test plan.

4. **`Project-Design-Docs/WP4/WP4.3-Numerical-Robustness-Implementation-Plan.md`**
   Monte Carlo and stress testing plan.

5. **`Project-Design-Docs/WP4/COMPLETE-IMPLEMENTATION-REPORT.md`**
   Full implementation status report.

### External References

- **Morales-Ruiz, J. J., & Ramis, J. P.** (2001), "Galoisian obstructions to integrability of Hamiltonian systems", *Methods and Applications of Analysis*, 8(1):33-96
- **Kovacic, J. J.** (1986), "An algorithm for solving second order linear homogeneous differential equations", *Journal of Symbolic Computation*, 2(1):3-43
- **Ziglin, S. L.** (1983), "Branching of solutions and nonexistence of first integrals in Hamiltonian mechanics. I", *Functional Analysis and Its Applications*, 16(3):181-189

---

## Next Steps

Once you've validated candidate integrals, proceed to:

- **User-Guide-WP5.md**: Publication preparation, formal proof construction, reproducibility package

**Critical reminder**: WP4 is the gatekeeper. Never skip validation steps. The scientific community depends on rigorous vetting to distinguish genuine discovery from artifact.

---

**Last Updated**: November 25, 2025
**WP4 Status**: ✅ 100% Complete - All validation infrastructure operational
