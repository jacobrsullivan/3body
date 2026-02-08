---
name: wp3-basis-functions
description: >
  Specialized basis function libraries for invariant discovery in the three-body problem.
  Use when: (1) working with KS spinor coordinates and spinor basis functions, 
  (2) using Jacobi elliptic functions (sn, cn, dn) for quasi-periodic motion,
  (3) using Jacobi theta functions for integrable systems, (4) generating polynomial/rational
  basis libraries, (5) estimating parameters (elliptic m, theta nome q) from trajectory data,
  (6) selecting the appropriate basis for a given trajectory type, (7) evaluating special
  functions along trajectories, (8) detecting trajectory signatures (close encounters,
  quasi-periodic, integrable), or (9) preparing basis functions for SINDy/PySR regression.
  Triggers on requests involving spinor basis, KS transformation, Jacobi elliptic sn cn dn,
  theta functions, elliptic parameter m, nome q, quasi-periodic detection, basis generation,
  regularization benefit, or specialized function evaluation.
---

# WP3 Basis Functions

Specialized basis function libraries for discovering hidden conserved quantities in lifted phase spaces.

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     BASIS FUNCTION SELECTION                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Trajectory Analysis                                                       │
│         │                                                                   │
│         ▼                                                                   │
│   ┌─────────────┐   Yes    ┌─────────────────┐                             │
│   │Close        ├─────────►│ SPINOR BASIS    │ ~80 functions               │
│   │encounters?  │          │ KS regularized  │ Collision-safe              │
│   └──────┬──────┘          └─────────────────┘                             │
│          │ No                                                               │
│          ▼                                                                  │
│   ┌─────────────┐   Yes    ┌─────────────────┐                             │
│   │Quasi-       ├─────────►│ ELLIPTIC BASIS  │ ~60 functions               │
│   │periodic?    │          │ sn, cn, dn      │ Estimate m from data        │
│   └──────┬──────┘          └─────────────────┘                             │
│          │ No                                                               │
│          ▼                                                                  │
│   ┌─────────────┐   Yes    ┌─────────────────┐                             │
│   │Integrable   ├─────────►│ THETA BASIS     │ ~40 functions               │
│   │signature?   │          │ θ₁, θ₂, θ₃, θ₄  │ Estimate nome q             │
│   └──────┬──────┘          └─────────────────┘                             │
│          │ No                                                               │
│          ▼                                                                  │
│   ┌─────────────────────┐                                                   │
│   │ POLYNOMIAL BASIS    │ ~50 functions (default fallback)                 │
│   │ x, y, x², xy, ...   │                                                  │
│   └─────────────────────┘                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Key Concepts

| Basis | Functions | Use Case | Key Parameter |
|-------|-----------|----------|---------------|
| **Spinor** | \|u\|², u·v, u×v (~80) | Close encounters r < 0.1 | None (coordinate transform) |
| **Elliptic** | sn, cn, dn (~60) | Quasi-periodic motion | m ∈ [0,1] elliptic parameter |
| **Theta** | θ₁, θ₂, θ₃, θ₄ (~40) | Completely integrable | q = e^(iπτ) nome |
| **Polynomial** | x, y, x², xy, ... (~50) | General/fallback | max_degree |

## Quick Start

```python
from src.python.symbolic.basis_functions import select_basis
from src.python.symbolic.spinor_basis import generate_spinor_basis
from src.python.symbolic.elliptic_basis import generate_elliptic_basis

# Automatic basis selection based on trajectory
basis_funcs, basis_type, params = select_basis(times, states)
print(f"Selected {basis_type} basis with {len(basis_funcs)} functions")

# Or manually select spinor basis for close encounters
spinor_basis = generate_spinor_basis()
print(f"Spinor basis: {len(spinor_basis)} functions")

# Or elliptic basis with estimated parameter
from src.python.symbolic.elliptic_basis import estimate_elliptic_parameter
m = estimate_elliptic_parameter(times, states)
elliptic_basis = generate_elliptic_basis(m=m)
print(f"Elliptic basis (m={m:.4f}): {len(elliptic_basis)} functions")
```

---

## Spinor Basis

**Location**: `src/python/symbolic/spinor_basis.py`

The KS transformation maps 3D positions to 4D spinors, potentially revealing hidden symmetries invisible in Cartesian coordinates.

### Theory

```
Position → Spinor mapping:
r = L(u) · u     (Levi-Civita matrix)
|r| = |u|²       (bilinear relation - fundamental identity)

Inverse is multi-valued (S¹ gauge freedom)
```

### Basis Functions (~80 total)

1. **Spinor norms** (3): |u₁|², |u₂|², |u₃|² (equal to |r₁|, |r₂|, |r₃|)
2. **Inner products** (3): u₁·u₂, u₂·u₃, u₃·u₁
3. **Quaternion products** (6): components of u₁×u₂, u₂×u₃, u₃×u₁
4. **Mixed bilinear forms** (~20): uᵢ·L(uⱼ)·uₖ combinations
5. **Momentum products** (~24): pᵤ·u, pᵤ·pᵤ, mixed terms
6. **Higher order** (~24): |u|⁴, (u·v)², etc.

### Usage

```python
from src.python.symbolic.spinor_basis import (
    generate_spinor_basis,
    position_to_spinor,
    spinor_to_position,
    levi_civita_matrix
)
import numpy as np

# Convert positions to spinors (for 3-body problem)
r1, r2, r3 = states[:, :3], states[:, 3:6], states[:, 6:9]
u1 = position_to_spinor(r1)  # N × 4 array
u2 = position_to_spinor(r2)
u3 = position_to_spinor(r3)

# Verify bilinear relation
r1_norm = np.linalg.norm(r1, axis=1)
u1_norm_sq = np.sum(u1**2, axis=1)
assert np.allclose(r1_norm, u1_norm_sq), "Bilinear relation violated!"

# Generate basis functions
basis_funcs = generate_spinor_basis()
print(f"Generated {len(basis_funcs)} spinor basis functions")

# Evaluate all basis functions on trajectory
basis_values = np.zeros((len(basis_funcs), len(times)))
for i, func in enumerate(basis_funcs):
    basis_values[i] = func(u1, u2, u3)
```

### When to Use Spinor Basis

```python
from src.python.symbolic.spinor_search import detect_regularization_benefit

# Check if spinor basis would help
has_close_encounters = detect_regularization_benefit(times, states, threshold=0.1)

if has_close_encounters:
    print("Close encounters detected - use spinor basis!")
    # Spinor coordinates regularize the collision singularity
else:
    print("No close encounters - spinor basis optional")
```

**Reference**: See `references/spinor-basis-theory.md` for full mathematical derivation.

---

## Elliptic Basis

**Location**: `src/python/symbolic/elliptic_basis.py`

Jacobi elliptic functions naturally describe quasi-periodic motion with two incommensurable frequencies.

### Theory

The three Jacobi elliptic functions satisfy fundamental identities:

```
sn²(u, m) + cn²(u, m) = 1
dn²(u, m) + m·sn²(u, m) = 1
```

where m ∈ [0,1] is the **elliptic parameter** (modulus squared).

### Limiting Cases

| m value | sn(u,m) | cn(u,m) | dn(u,m) | Motion type |
|---------|---------|---------|---------|-------------|
| m → 0 | sin(u) | cos(u) | 1 | Circular (harmonic) |
| m → 1 | tanh(u) | sech(u) | sech(u) | Hyperbolic (separatrix) |
| 0 < m < 1 | elliptic | elliptic | elliptic | Quasi-periodic |

### Basis Functions (~60 total)

1. **Basic** (3): sn(|r|, m), cn(|r|, m), dn(|r|, m)
2. **Products** (3): sn·cn, sn·dn, cn·dn
3. **Powers** (9): sn², cn², dn², sn³, ...
4. **Mixed with coordinates** (~20): rₓ·sn(|r|), rᵧ·cn(|r|), ...
5. **Complete integrals** (2): K(m), E(m)
6. **Ratio forms** (~20): sn/cn, cn/dn, etc.

### Parameter Estimation

```python
from src.python.symbolic.elliptic_basis import (
    generate_elliptic_basis,
    estimate_elliptic_parameter,
    jacobi_sn, jacobi_cn, jacobi_dn
)

# Estimate elliptic parameter from trajectory oscillations
m = estimate_elliptic_parameter(times, states)
print(f"Estimated elliptic parameter m = {m:.4f}")

# Interpretation
if m < 0.1:
    print("Nearly circular motion (m ≈ 0)")
elif m > 0.9:
    print("Highly eccentric, near separatrix (m ≈ 1)")
else:
    print(f"Quasi-periodic motion with eccentricity signature")

# Generate basis with estimated parameter
basis = generate_elliptic_basis(m=m)

# Evaluate Jacobi functions along trajectory
r_mag = np.linalg.norm(states[:, :3], axis=1)
sn_vals = jacobi_sn(r_mag, m)
cn_vals = jacobi_cn(r_mag, m)
dn_vals = jacobi_dn(r_mag, m)

# Verify fundamental identity
assert np.allclose(sn_vals**2 + cn_vals**2, 1.0, atol=1e-10)
```

### Quasi-Periodic Detection

```python
from src.python.symbolic.elliptic_search import detect_elliptic_signature

# Detect quasi-periodic structure via FFT
signature = detect_elliptic_signature(times, states)

if signature.is_quasi_periodic:
    print(f"Quasi-periodic motion detected!")
    print(f"Frequencies: {signature.frequencies}")
    print(f"Frequency ratio: {signature.frequency_ratio:.4f}")
    print(f"Suggested m: {signature.elliptic_parameter:.4f}")
```

**Reference**: See `references/elliptic-functions.md` for theory and identities.

---

## Theta Basis

**Location**: `src/python/symbolic/theta_basis.py`

Jacobi theta functions appear in completely integrable systems via the Abel-Jacobi map.

### Theory

Four theta functions θᵢ(z, q) parameterized by nome q = e^(iπτ):

```
θ₁(z, q) = 2q^(1/4) sin(z) ∏ₙ (1 - 2q²ⁿcos(2z) + q⁴ⁿ)(1 - q²ⁿ)
θ₂(z, q) = 2q^(1/4) cos(z) ∏ₙ (1 + 2q²ⁿcos(2z) + q⁴ⁿ)(1 - q²ⁿ)
θ₃(z, q) = ∏ₙ (1 + 2qⁿcos(2z) + q²ⁿ)(1 - q²ⁿ)
θ₄(z, q) = ∏ₙ (1 - 2qⁿcos(2z) + q²ⁿ)(1 - q²ⁿ)
```

### Key Identity

```
θ₃⁴ = θ₂⁴ + θ₄⁴   (Jacobi's quartic identity)
```

### Basis Functions (~40 total)

1. **Basic** (4): θ₁, θ₂, θ₃, θ₄
2. **Products** (6): θᵢ·θⱼ pairs
3. **Squares** (4): θ₁², θ₂², θ₃², θ₄²
4. **Ratios** (12): θᵢ/θⱼ combinations
5. **Derivatives** (4): θ'₁, θ'₂, θ'₃, θ'₄
6. **Mixed** (~10): combinations with coordinates

### Usage

```python
from src.python.symbolic.theta_basis import (
    generate_theta_basis,
    theta1, theta2, theta3, theta4,
    estimate_nome
)

# Estimate nome from trajectory
q = estimate_nome(times, states)
print(f"Estimated nome |q| = {abs(q):.6f}")

if abs(q) > 0.9:
    print("Warning: Nome near 1, convergence may be slow")

# Generate theta basis
basis = generate_theta_basis(q=q)

# Evaluate theta functions
# z = complex argument (typically angle-like coordinate)
z = np.angle(states[:, 0] + 1j * states[:, 1])
t1 = theta1(z, q)
t2 = theta2(z, q)
t3 = theta3(z, q)
t4 = theta4(z, q)

# Verify Jacobi identity (quartic form)
lhs = t3**4
rhs = t2**4 + t4**4
assert np.allclose(lhs, rhs, atol=1e-8), "Jacobi identity failed"
```

**Reference**: See `references/theta-functions.md` for complete theory.

---

## Polynomial Basis

**Location**: `src/python/symbolic/basis_functions.py`

Standard polynomial and rational basis for general-purpose search.

```python
from src.python.symbolic.basis_functions import (
    generate_polynomial_basis,
    generate_rational_basis,
    generate_combined_basis
)

# Polynomial basis up to degree 4
poly_basis = generate_polynomial_basis(
    variables=['x', 'y', 'z', 'vx', 'vy', 'vz'],
    max_degree=4
)
print(f"Polynomial basis: {len(poly_basis)} terms")

# Rational terms (gravitational-style)
rational_basis = generate_rational_basis(
    variables=['r12', 'r23', 'r31'],
    max_degree=2
)  # Includes 1/r, 1/r², etc.

# Combined basis
full_basis = generate_combined_basis(
    polynomial_degree=3,
    include_rational=True,
    include_trig=False
)
```

---

## Automatic Basis Selection

```python
def select_basis_automatically(times, states, mu=None):
    """
    Automatically select optimal basis based on trajectory analysis.
    
    Returns:
        basis_funcs: List of basis functions
        basis_type: 'spinor', 'elliptic', 'theta', or 'polynomial'
        params: Dict of estimated parameters
    """
    from src.python.symbolic.spinor_search import detect_regularization_benefit
    from src.python.symbolic.elliptic_search import detect_elliptic_signature
    from src.python.symbolic.theta_basis import detect_integrability_signature
    
    params = {}
    
    # Priority 1: Check for close encounters
    if detect_regularization_benefit(times, states, threshold=0.1):
        from src.python.symbolic.spinor_basis import generate_spinor_basis
        print("✓ Close encounters detected → Spinor basis")
        return generate_spinor_basis(), 'spinor', params
    
    # Priority 2: Check for quasi-periodic motion
    qp = detect_elliptic_signature(times, states)
    if qp.is_quasi_periodic:
        from src.python.symbolic.elliptic_basis import generate_elliptic_basis
        params['m'] = qp.elliptic_parameter
        print(f"✓ Quasi-periodic motion → Elliptic basis (m={params['m']:.4f})")
        return generate_elliptic_basis(m=params['m']), 'elliptic', params
    
    # Priority 3: Check for integrability signature
    integ = detect_integrability_signature(times, states)
    if integ.is_integrable:
        from src.python.symbolic.theta_basis import generate_theta_basis
        params['q'] = integ.nome
        print(f"✓ Integrable signature → Theta basis (q={abs(params['q']):.6f})")
        return generate_theta_basis(q=params['q']), 'theta', params
    
    # Default: Polynomial
    from src.python.symbolic.basis_functions import generate_polynomial_basis
    print("→ Default polynomial basis")
    return generate_polynomial_basis(max_degree=4), 'polynomial', params

# Usage
basis, basis_type, params = select_basis_automatically(times, states, mu)
```

---

## Downstream Usage

### For SINDy Regression

```python
from src.python.symbolic.regression_pipeline import SINDyRegressor

# Use selected basis in SINDy
sindy = SINDyRegressor(
    basis_functions=basis_funcs,  # From selection above
    threshold=0.1,
    alpha=0.01
)

result = sindy.fit(times, states)
print(f"Found: {result.expression}")
```

### For Multi-Stage Pipeline

```python
from src.python.symbolic.multi_stage_pipeline import MultiStageInvariantSearch

# Pipeline automatically uses appropriate bases
search = MultiStageInvariantSearch(
    stages=['spinor', 'elliptic', 'theta', 'polynomial'],
    max_candidates_per_stage=5
)

results = search.run(times, states, mu=mu)
```

---

## Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Spinor transform fails | Zero or NaN positions | Filter invalid states |
| Elliptic m out of range | Not quasi-periodic | Use polynomial basis |
| Theta nome \|q\| ≈ 1 | Convergence slow | Use elliptic basis instead |
| Too many basis functions | Memory/speed | Reduce max_degree or filter |
| Basis values NaN | Evaluation outside domain | Check coordinate ranges |

### Diagnostic Function

```python
def diagnose_basis_issues(basis_funcs, states):
    """Check for common basis evaluation problems."""
    issues = []
    
    for i, func in enumerate(basis_funcs):
        try:
            vals = func(states)
            if np.any(np.isnan(vals)):
                issues.append(f"Function {i}: NaN values")
            if np.any(np.isinf(vals)):
                issues.append(f"Function {i}: Infinite values")
            if np.std(vals) < 1e-15:
                issues.append(f"Function {i}: Nearly constant")
        except Exception as e:
            issues.append(f"Function {i}: Error - {str(e)}")
    
    if not issues:
        print("✓ All basis functions evaluate correctly")
    else:
        for issue in issues:
            print(f"⚠ {issue}")
    
    return len(issues) == 0
```

---

## Tests

```bash
# All basis function tests
pytest tests/wp3/test_spinor_basis.py -v
pytest tests/wp3/test_elliptic_basis.py -v
pytest tests/wp3/test_theta_basis.py -v

# Specific tests
pytest tests/wp3/test_spinor_basis.py::test_bilinear_relation -v
pytest tests/wp3/test_elliptic_basis.py::test_jacobi_identity -v
```

---

## References

- `references/spinor-basis-theory.md` - KS transformation and spinor mathematics
- `references/elliptic-functions.md` - Jacobi elliptic function theory
- `references/theta-functions.md` - Jacobi theta function theory
- `src/python/symbolic/spinor_basis.py` - Spinor implementation
- `src/python/symbolic/elliptic_basis.py` - Elliptic implementation
- `src/python/symbolic/theta_basis.py` - Theta implementation
- Abramowitz & Stegun (1964), *Handbook of Mathematical Functions*, Ch. 16-17
- Kustaanheimo & Stiefel (1965), "Perturbation theory of Kepler motion based on spinor regularization"
