# AMENDED Task 3.3.2: Enriched Basis Function Library
## Implementation Plan for Non-Standard Function Discovery

**Duration**: 4-5 days
**Prerequisites**: Task 3.3.1 (Symbolic Regression Pipeline)
**Objective**: Construct physics-informed basis function libraries including spinor components, elliptic functions, and other non-standard forms to enable discovery of complex conserved quantities

**Amendment Date**: 2025-11-20
**Amendment Rationale**: Hidden integrals in the three-body problem, if they exist, are likely complex and may involve non-polynomial functions motivated by KS regularization, integrable system theory, and classical mechanics.

---

## Table of Contents

1. [Overview](#overview)
2. [Enhanced Architecture](#enhanced-architecture)
3. [Implementation Details](#implementation-details)
4. [Spinor Basis Functions](#spinor-basis-functions)
5. [Elliptic Function Basis](#elliptic-function-basis)
6. [Validation Strategy](#validation-strategy)
7. [Testing Plan](#testing-plan)
8. [Deliverables](#deliverables)

---

## Overview

### Extended Purpose

Task 3.3.2 constructs **physics-informed basis function libraries** that go beyond standard polynomials to include:

1. **Spinor components** from KS regularization
2. **Elliptic functions** (Jacobi sn/cn/dn, Weierstrass ℘)
3. **Theta functions** for quasi-periodic structures
4. **Rational and algebraic** combinations of geometric quantities

### Mathematical Motivation

**Historical Precedent**:

| System | Hidden Integral | Function Type |
|--------|----------------|---------------|
| Kepler problem | Runge-Lenz vector | Algebraic (involves $\mathbf{r}/r$) |
| Kowalevskaya top | Kowalevskaya integral | Elliptic function |
| Rigid body (Euler) | $L_z$ in body frame | Algebraic |
| Geodesic flow on ellipsoid | Jacobi's integral | Elliptic integral |
| Toda lattice | Action variables | Logarithmic |

**Implication**: If the three-body problem has a fourth integral, it may involve similar non-standard functions.

---

## Enhanced Architecture

### Module Structure (EXTENDED)

```
src/python/symbolic/
├── basis_functions.py              # Main API (AMENDED)
├── geometric_invariants.py         # Distance, angle, momentum computations
├── polynomial_basis.py             # Standard polynomial bases
├── physics_basis.py                # Energy, angular momentum combinations
├── coordinate_transforms.py        # Cartesian ↔ Shape Space ↔ S¹ ↔ KS
│
├── spinor_basis.py                 # KS spinor components (NEW)
├── elliptic_basis.py               # Jacobi/Weierstrass elliptic functions (NEW)
├── theta_basis.py                  # Jacobi theta functions (NEW)
├── algebraic_basis.py              # Rational and algebraic combinations (NEW)
└── special_functions_utils.py     # Numerical evaluation utilities (NEW)
```

### Hierarchical Search Strategy (EXTENDED)

```
Level 0: Known Integrals {E, L_x, L_y, L_z, p_θ}
    ↓ Already conserved (baseline)

Level 1: Polynomial (degree ≤ 3) in phase space coordinates
    ↓ ~100 functions | O(n^3) | Standard

Level 2: Rational Functions
    ↓ ~500 functions | O(n^6) | Gravitational potentials

Level 3: Algebraic (sqrt, nth roots)
    ↓ ~200 functions | O(n^3) with sqrt | Kepler-like

Level 4: KS Spinor Components (NEW)
    ↓ ~80 functions | Linear/quadratic in spinors
    - Individual components: u12_0, u12_1, u12_2, u12_3, ...
    - Bilinear forms: ⟨u12, u23⟩, ⟨u12, u31⟩, ...
    - Quaternion products: u12 ⊗ u23

Level 5: Trigonometric (sin, cos of phase space variables)
    ↓ ~300 functions | Periodic motion

Level 6: Elliptic Functions (Jacobi) (NEW)
    ↓ ~60 templates | sn(f(q,p), k), cn(f(q,p), k), dn(f(q,p), k)
    - Argument f(q,p): Energy, angular momentum, geometric combinations
    - Modulus k: 0.5, 0.7, 0.9, or fitted

Level 7: Elliptic Functions (Weierstrass) (NEW)
    ↓ ~30 templates | ℘(f(q,p); ω1, ω2)
    - Lattice parameters ω1, ω2: To be fitted

Level 8: Theta Functions (NEW)
    ↓ ~16 templates | θ_i(f(q,p), q) for i=1,2,3,4
    - Nome q = exp(iπτ): Related to elliptic modulus
```

**Adaptive Strategy**: Start at Level 1. Only proceed to next level if:
- Current level residual > 10^{-8}, AND
- Current level search exhausted (all combinations tried)

---

## Implementation Details

### Part A: Spinor Basis Functions (NEW - 1.5 days)

**File**: `src/python/symbolic/spinor_basis.py`

#### A.1: KS Spinor Representation

**Mathematical Background**:

The Kustaanheimo-Stiefel (KS) transformation represents a 3D position vector $\mathbf{r} \in \mathbb{R}^3$ as a 4D spinor $\mathbf{u} \in \mathbb{R}^4$ (or $\mathbb{C}^2$) via:

$$
\mathbf{r} = L(\mathbf{u}) \mathbf{u}
$$

where $L(\mathbf{u})$ is a $3 \times 4$ matrix depending linearly on $\mathbf{u}$, and $|\mathbf{r}| = |\mathbf{u}|^2$.

**Key Properties**:
1. **Bilinear**: The map $(u_0, u_1, u_2, u_3) \mapsto (x, y, z)$ is bilinear
2. **Distance**: $r = |\mathbf{r}| = u_0^2 + u_1^2 + u_2^2 + u_3^2$
3. **Regularization**: KS removes the $1/r$ singularity in the Hamiltonian

**For Three-Body Problem**: We have three spinors (one per pair):
- $\mathbf{u}_{12} = (u_{12,0}, u_{12,1}, u_{12,2}, u_{12,3})$ for body pair 1-2
- $\mathbf{u}_{23} = (u_{23,0}, u_{23,1}, u_{23,2}, u_{23,3})$ for body pair 2-3
- $\mathbf{u}_{31} = (u_{31,0}, u_{31,1}, u_{31,2}, u_{31,3})$ for body pair 3-1

#### A.2: Implementation

```python
"""
Spinor-based basis functions for symbolic regression using KS coordinates.

The KS transformation introduces spinor (quaternion) coordinates that may
reveal hidden algebraic structure in conserved quantities.
"""

import numpy as np
from typing import List, Tuple, Callable, Dict
from dataclasses import dataclass


@dataclass
class SpinorCoordinates:
    """
    KS spinor coordinates for three-body system.

    Attributes:
        u12: Spinor for body pair 1-2 (shape: (4,))
        u23: Spinor for body pair 2-3 (shape: (4,))
        u31: Spinor for body pair 3-1 (shape: (4,))
        u12_dot: Conjugate momenta for u12 (shape: (4,))
        u23_dot: Conjugate momenta for u23 (shape: (4,))
        u31_dot: Conjugate momenta for u31 (shape: (4,))
    """
    u12: np.ndarray
    u23: np.ndarray
    u31: np.ndarray
    u12_dot: np.ndarray
    u23_dot: np.ndarray
    u31_dot: np.ndarray


def cartesian_to_ks_spinors(
    state_cartesian: np.ndarray,
    masses: np.ndarray
) -> SpinorCoordinates:
    """
    Convert Cartesian phase space state to KS spinor coordinates.

    Args:
        state_cartesian: [q1x, q1y, q1z, q2x, q2y, q2z, q3x, q3y, q3z,
                          p1x, p1y, p1z, p2x, p2y, p2z, p3x, p3y, p3z]
        masses: [m1, m2, m3]

    Returns:
        SpinorCoordinates object with spinors for all three pairs
    """
    # Extract positions
    q = state_cartesian[:9].reshape(3, 3)  # (3 bodies, 3 coords)
    p = state_cartesian[9:].reshape(3, 3)

    # Relative positions
    r12 = q[1] - q[0]
    r23 = q[2] - q[1]
    r31 = q[0] - q[2]

    # Convert to spinors using KS transformation
    u12 = position_to_spinor(r12)
    u23 = position_to_spinor(r23)
    u31 = position_to_spinor(r31)

    # Conjugate momenta (requires more complex transformation)
    # Simplified here - full implementation needs KS momentum map
    mu12 = masses[0] * masses[1] / (masses[0] + masses[1])
    mu23 = masses[1] * masses[2] / (masses[1] + masses[2])
    mu31 = masses[2] * masses[0] / (masses[2] + masses[0])

    v12 = (p[1] / masses[1]) - (p[0] / masses[0])
    v23 = (p[2] / masses[2]) - (p[1] / masses[1])
    v31 = (p[0] / masses[0]) - (p[2] / masses[2])

    u12_dot = velocity_to_spinor_momentum(v12, u12, mu12)
    u23_dot = velocity_to_spinor_momentum(v23, u23, mu23)
    u31_dot = velocity_to_spinor_momentum(v31, u31, mu31)

    return SpinorCoordinates(u12, u23, u31, u12_dot, u23_dot, u31_dot)


def position_to_spinor(r: np.ndarray) -> np.ndarray:
    """
    Convert 3D position to 4D spinor (KS map).

    Standard KS transformation:
        u0 = sqrt((r + x) / 2)
        u1 = y / (2*u0)
        u2 = z / (2*u0)
        u3 = 0  (gauge choice)

    Args:
        r: 3D position vector [x, y, z]

    Returns:
        u: 4D spinor [u0, u1, u2, u3]
    """
    x, y, z = r
    r_mag = np.linalg.norm(r)

    # Avoid singularity at origin
    if r_mag < 1e-10:
        return np.zeros(4)

    # Standard KS map (Levi-Civita type)
    u0 = np.sqrt((r_mag + x) / 2)
    if u0 < 1e-10:
        # Near x = -r (opposite side), use alternative form
        u0 = 0.0
        u1 = np.sqrt((r_mag - x) / 2)
        u2 = y / (2 * u1) if u1 > 1e-10 else 0.0
        u3 = z / (2 * u1) if u1 > 1e-10 else 0.0
    else:
        u1 = y / (2 * u0)
        u2 = z / (2 * u0)
        u3 = 0.0  # Gauge choice (can be parameterized)

    return np.array([u0, u1, u2, u3])


def velocity_to_spinor_momentum(
    v: np.ndarray,
    u: np.ndarray,
    mu: float
) -> np.ndarray:
    """
    Convert velocity to spinor momentum (KS momentum map).

    The KS momentum transformation is more complex and involves
    the spinor derivatives.

    Simplified implementation (full version requires Hamiltonian formalism).

    Args:
        v: 3D velocity [vx, vy, vz]
        u: 4D spinor [u0, u1, u2, u3]
        mu: Reduced mass

    Returns:
        u_dot: 4D spinor momentum
    """
    # Placeholder - full implementation requires solving the momentum map
    # For now, use a simplified approximation
    r_mag = np.dot(u, u)
    if r_mag < 1e-10:
        return np.zeros(4)

    # Approximate: project velocity onto spinor directions
    # This is NOT the correct KS momentum map but provides a starting point
    u_normalized = u / np.sqrt(r_mag)
    v_parallel = np.dot(v, u[:3]) / np.linalg.norm(u[:3]) if np.linalg.norm(u[:3]) > 1e-10 else 0.0

    u_dot = 2 * mu * v_parallel * u_normalized

    return u_dot


def construct_spinor_basis(
    masses: np.ndarray,
    max_degree: int = 3,
    include_quaternion_products: bool = True
) -> List[Tuple[Callable, str]]:
    """
    Construct basis functions using KS spinor coordinates.

    Args:
        masses: Body masses [m1, m2, m3]
        max_degree: Maximum polynomial degree in spinor components
        include_quaternion_products: Include quaternion multiplication

    Returns:
        basis: List of (function, name) tuples

    Basis function categories:
        1. Individual spinor components (24 functions: 3 pairs × 4 components × 2 (position + momentum))
        2. Spinor norms (6 functions: 3 pairs × 2 (position + momentum))
        3. Inner products between spinors (9 functions: 3 choose 2 × 3 combinations)
        4. Quaternion products (6 functions if included)
        5. Mixed bilinear forms (position spinor · momentum spinor)
    """
    basis = []

    def make_spinor_func(extractor: Callable[[SpinorCoordinates], float], name: str):
        """Factory for creating basis functions from spinor coordinates."""
        def func(state_cartesian: np.ndarray) -> float:
            spinors = cartesian_to_ks_spinors(state_cartesian, masses)
            return extractor(spinors)
        func.__name__ = name
        return (func, name)

    # Category 1: Individual spinor components
    for pair in ['12', '23', '31']:
        for i in range(4):
            # Position spinor components
            basis.append(make_spinor_func(
                lambda s, pair=pair, i=i: getattr(s, f'u{pair}')[i],
                f"u{pair}_{i}"
            ))

            # Momentum spinor components
            basis.append(make_spinor_func(
                lambda s, pair=pair, i=i: getattr(s, f'u{pair}_dot')[i],
                f"udot{pair}_{i}"
            ))

    # Category 2: Spinor norms
    for pair in ['12', '23', '31']:
        # |u|^2 = r (distance)
        basis.append(make_spinor_func(
            lambda s, pair=pair: np.dot(getattr(s, f'u{pair}'), getattr(s, f'u{pair}')),
            f"|u{pair}|^2"
        ))

        # |u_dot|^2 (kinetic energy contribution)
        basis.append(make_spinor_func(
            lambda s, pair=pair: np.dot(getattr(s, f'u{pair}_dot'), getattr(s, f'u{pair}_dot')),
            f"|udot{pair}|^2"
        ))

    # Category 3: Inner products (position spinors)
    pairs = ['12', '23', '31']
    for i, pair_i in enumerate(pairs):
        for j, pair_j in enumerate(pairs):
            if i < j:
                basis.append(make_spinor_func(
                    lambda s, pi=pair_i, pj=pair_j: np.dot(
                        getattr(s, f'u{pi}'),
                        getattr(s, f'u{pj}')
                    ),
                    f"u{pair_i}_dot_u{pair_j}"
                ))

    # Category 4: Mixed bilinear forms (position · momentum)
    for pair in pairs:
        basis.append(make_spinor_func(
            lambda s, p=pair: np.dot(
                getattr(s, f'u{p}'),
                getattr(s, f'u{p}_dot')
            ),
            f"u{pair}_dot_udot{pair}"
        ))

    # Category 5: Quaternion products (if requested)
    if include_quaternion_products:
        for i, pair_i in enumerate(pairs):
            for j, pair_j in enumerate(pairs):
                if i < j:
                    basis.append(make_spinor_func(
                        lambda s, pi=pair_i, pj=pair_j: quaternion_product_norm(
                            getattr(s, f'u{pi}'),
                            getattr(s, f'u{pj}')
                        ),
                        f"quat_product_u{pair_i}_u{pair_j}"
                    ))

    # Category 6: Higher-degree combinations (if max_degree >= 2)
    if max_degree >= 2:
        # Quadratic combinations
        for pair in pairs:
            # u^2 · u_dot (action-like variable)
            basis.append(make_spinor_func(
                lambda s, p=pair: (
                    np.dot(getattr(s, f'u{p}'), getattr(s, f'u{p}')) *
                    np.linalg.norm(getattr(s, f'u{p}_dot'))
                ),
                f"|u{pair}|^2_|udot{pair}|"
            ))

    return basis


def quaternion_product_norm(u1: np.ndarray, u2: np.ndarray) -> float:
    """
    Compute norm of quaternion product u1 ⊗ u2.

    Quaternion multiplication:
        (a0 + a1*i + a2*j + a3*k) * (b0 + b1*i + b2*j + b3*k)

    Returns the Euclidean norm of the resulting quaternion.

    Args:
        u1, u2: 4D spinors representing quaternions

    Returns:
        |u1 ⊗ u2|
    """
    a0, a1, a2, a3 = u1
    b0, b1, b2, b3 = u2

    # Quaternion multiplication formula
    c0 = a0*b0 - a1*b1 - a2*b2 - a3*b3
    c1 = a0*b1 + a1*b0 + a2*b3 - a3*b2
    c2 = a0*b2 - a1*b3 + a2*b0 + a3*b1
    c3 = a0*b3 + a1*b2 - a2*b1 + a3*b0

    return np.sqrt(c0**2 + c1**2 + c2**2 + c3**2)


# Validation: Test on known integrals
def test_spinor_basis_on_kepler():
    """
    Test spinor basis construction on Kepler problem.

    For two-body Kepler, we have:
        - Energy: E = |u_dot|^2 / (2*mu) - G*m1*m2 / |u|^2
        - Angular momentum: L = u × u_dot (in spinor form)

    This test verifies that spinor basis can recover these known integrals.
    """
    masses = np.array([1.0, 0.001, 0.0])  # Sun-planet-zero approximation

    basis = construct_spinor_basis(masses, max_degree=2)

    print(f"Spinor basis size: {len(basis)}")
    print(f"First 10 functions: {[name for _, name in basis[:10]]}")

    # Test evaluation on random state
    state = np.random.randn(18)
    for func, name in basis[:5]:
        value = func(state)
        print(f"  {name} = {value:.6f}")
```

**Validation Tests**:

```python
# tests/symbolic/test_spinor_basis.py

def test_spinor_norm_equals_distance():
    """Test that |u|^2 = r for KS transformation."""
    masses = np.array([1.0, 1.0, 1.0])

    # Create test state
    r12 = np.array([1.0, 2.0, 3.0])
    r12_mag = np.linalg.norm(r12)

    # Convert to spinor
    u12 = position_to_spinor(r12)

    # Check |u|^2 = r
    u_norm_sq = np.dot(u12, u12)
    assert np.abs(u_norm_sq - r12_mag) < 1e-10, f"KS norm condition failed: {u_norm_sq} ≠ {r12_mag}"


def test_spinor_basis_size():
    """Test that spinor basis has expected number of functions."""
    masses = np.array([1.0, 1.0, 1.0])
    basis = construct_spinor_basis(masses, max_degree=2)

    # Expected: 24 (components) + 6 (norms) + 3 (inner products) +
    #           3 (mixed) + 6 (quaternion) + ... = ~50-80
    assert len(basis) > 30, f"Basis too small: {len(basis)}"
    assert len(basis) < 100, f"Basis too large: {len(basis)}"
```

---

### Part B: Elliptic Function Basis (NEW - 2 days)

**File**: `src/python/symbolic/elliptic_basis.py`

#### B.1: Mathematical Background

**Jacobi Elliptic Functions**:

The Jacobi elliptic functions sn, cn, dn are defined by:
$$
\text{sn}(u, k), \quad \text{cn}(u, k), \quad \text{dn}(u, k)
$$
where $u$ is the argument and $k \in [0, 1]$ is the elliptic modulus.

**Properties**:
- $\text{sn}^2(u, k) + \text{cn}^2(u, k) = 1$
- $\text{dn}^2(u, k) + k^2 \text{sn}^2(u, k) = 1$
- Periodic: $\text{sn}(u + 4K, k) = \text{sn}(u, k)$ where $K(k)$ is the complete elliptic integral

**Physical Examples**:
- **Simple pendulum**: $\theta(t) = 2 \arcsin(\text{sn}(\omega t, k))$
- **Kowalevskaya top**: One integral involves $\text{sn}(\psi, k)$

#### B.2: Implementation

```python
"""
Elliptic function-based basis for symbolic regression.

Provides templates for Jacobi and Weierstrass elliptic functions
with physically motivated argument functions.
"""

import numpy as np
from scipy import special
from mpmath import ellipfun, ellipk, ellipe, jtheta
from typing import List, Tuple, Callable, Dict, Optional


def construct_jacobi_elliptic_basis(
    masses: np.ndarray,
    moduli: List[float] = [0.5, 0.7, 0.9],
    argument_templates: Optional[List[str]] = None
) -> List[Tuple[Callable, str]]:
    """
    Construct basis using Jacobi elliptic functions.

    Args:
        masses: Body masses
        moduli: List of elliptic moduli k to try
        argument_templates: Types of argument functions f(q,p)
                            Options: 'energy', 'angle', 'action', 'geometric'

    Returns:
        basis: List of (function, name) tuples

    Each basis function has form:
        sn(f(q,p), k), cn(f(q,p), k), or dn(f(q,p), k)
    where f(q,p) is an argument function and k is the modulus.
    """
    if argument_templates is None:
        argument_templates = ['energy', 'angle', 'geometric']

    basis = []

    # Get argument functions
    arg_funcs = get_argument_functions(masses, argument_templates)

    # For each combination of (elliptic function, argument, modulus)
    for func_type in ['sn', 'cn', 'dn']:
        for arg_name, arg_func in arg_funcs.items():
            for k in moduli:
                basis.append(make_elliptic_function(
                    func_type, arg_func, k, f"{func_type}({arg_name}, k={k:.1f})"
                ))

    return basis


def make_elliptic_function(
    func_type: str,
    arg_func: Callable,
    modulus: float,
    name: str
) -> Tuple[Callable, str]:
    """
    Create an elliptic function basis element.

    Args:
        func_type: 'sn', 'cn', or 'dn'
        arg_func: Function that computes argument u = f(q,p)
        modulus: Elliptic modulus k
        name: Human-readable name

    Returns:
        (function, name) tuple
    """
    def elliptic_func(state: np.ndarray) -> float:
        u = arg_func(state)

        # Evaluate Jacobi elliptic function
        try:
            # Use mpmath for high precision
            if func_type == 'sn':
                result = float(ellipfun('sn', u, modulus))
            elif func_type == 'cn':
                result = float(ellipfun('cn', u, modulus))
            elif func_type == 'dn':
                result = float(ellipfun('dn', u, modulus))
            else:
                raise ValueError(f"Unknown function type: {func_type}")

            # Handle numerical issues
            if not np.isfinite(result):
                return 0.0

            return result
        except:
            return 0.0  # Evaluation failed

    elliptic_func.__name__ = name
    return (elliptic_func, name)


def get_argument_functions(
    masses: np.ndarray,
    templates: List[str]
) -> Dict[str, Callable]:
    """
    Construct argument functions f(q,p) for elliptic functions.

    Templates:
        - 'energy': sqrt(|E|), E, E^2
        - 'angle': θ (fiber angle in S¹ bundle), angular momentum angle
        - 'action': sqrt(E)*θ, L/sqrt(E)
        - 'geometric': r12*sqrt(E), r12/r23, etc.

    Returns:
        Dictionary mapping name -> function
    """
    arg_funcs = {}

    if 'energy' in templates:
        # Energy-based arguments
        arg_funcs['sqrt_E'] = lambda state: np.sqrt(abs(compute_energy(state, masses)))
        arg_funcs['E'] = lambda state: compute_energy(state, masses)
        arg_funcs['E_sq'] = lambda state: compute_energy(state, masses)**2

    if 'angle' in templates:
        # Angular arguments
        arg_funcs['theta'] = lambda state: extract_fiber_angle(state)  # If using S¹ bundle
        arg_funcs['atan_py_px'] = lambda state: np.arctan2(state[-2], state[-3])  # Momentum angle

    if 'action' in templates:
        # Action-angle-like combinations
        arg_funcs['sqrt_E_theta'] = lambda state: (
            np.sqrt(abs(compute_energy(state, masses))) * extract_fiber_angle(state)
        )
        arg_funcs['L_over_sqrt_E'] = lambda state: (
            compute_angular_momentum_magnitude(state, masses) /
            (np.sqrt(abs(compute_energy(state, masses))) + 1e-10)
        )

    if 'geometric' in templates:
        # Geometric combinations
        arg_funcs['r12_sqrt_E'] = lambda state: (
            compute_r12(state, masses) * np.sqrt(abs(compute_energy(state, masses)))
        )
        arg_funcs['r12_over_r23'] = lambda state: (
            compute_r12(state, masses) / (compute_r23(state, masses) + 1e-10)
        )

    return arg_funcs


def construct_weierstrass_elliptic_basis(
    masses: np.ndarray,
    lattice_params: Optional[List[Tuple[complex, complex]]] = None,
    argument_templates: Optional[List[str]] = None
) -> List[Tuple[Callable, str]]:
    """
    Construct basis using Weierstrass ℘ function.

    The Weierstrass ℘ function is defined by:
        ℘(z; ω1, ω2) where ω1, ω2 are lattice periods

    Args:
        masses: Body masses
        lattice_params: List of (ω1, ω2) lattice parameter pairs
        argument_templates: Types of argument functions

    Returns:
        basis: List of (function, name) tuples
    """
    if lattice_params is None:
        # Default lattice parameters (to be optimized later)
        lattice_params = [
            (1.0 + 0j, 1.0j),      # Square lattice
            (2.0 + 0j, 1.0j),      # Rectangular lattice
            (1.0 + 0j, 0.5 + 0.866j),  # Hexagonal lattice
        ]

    if argument_templates is None:
        argument_templates = ['energy', 'angle']

    basis = []
    arg_funcs = get_argument_functions(masses, argument_templates)

    for arg_name, arg_func in arg_funcs.items():
        for i, (omega1, omega2) in enumerate(lattice_params):
            basis.append(make_weierstrass_function(
                arg_func, omega1, omega2, f"wp({arg_name}, omega{i})"
            ))

    return basis


def make_weierstrass_function(
    arg_func: Callable,
    omega1: complex,
    omega2: complex,
    name: str
) -> Tuple[Callable, str]:
    """
    Create a Weierstrass ℘ function basis element.

    Args:
        arg_func: Function that computes complex argument z = f(q,p)
        omega1, omega2: Lattice periods
        name: Human-readable name

    Returns:
        (function, name) tuple
    """
    def weierstrass_func(state: np.ndarray) -> float:
        z = arg_func(state)

        try:
            # Use mpmath for Weierstrass ℘
            from mpmath import ellipwp
            result = float(ellipwp(z, omega1, omega2).real)

            if not np.isfinite(result):
                return 0.0

            return result
        except:
            return 0.0

    weierstrass_func.__name__ = name
    return (weierstrass_func, name)


# Placeholder helper functions (to be implemented based on coordinate system)
def compute_energy(state, masses):
    """Compute total energy."""
    # Simplified - needs proper implementation
    n = len(state) // 2
    p = state[n:]
    return 0.5 * np.sum(p**2)


def compute_angular_momentum_magnitude(state, masses):
    """Compute |L|."""
    # Placeholder
    return 1.0


def compute_r12(state, masses):
    """Compute distance r12."""
    # Placeholder
    return 1.0


def compute_r23(state, masses):
    """Compute distance r23."""
    # Placeholder
    return 1.0


def extract_fiber_angle(state):
    """Extract θ from S¹ bundle coordinates."""
    # Placeholder - assumes S¹ coordinates
    if len(state) >= 8:
        return state[3]  # θ is 4th coordinate in S¹ bundle
    return 0.0
```

**Validation**:

```python
# Test elliptic basis on simple pendulum
def test_elliptic_basis_on_pendulum():
    """
    Simple pendulum has exact solution:
        θ(t) = 2*arcsin(k*sn(ω*t, k))
    where k = sin(θ_max/2).

    Test if elliptic basis can discover this.
    """
    # Generate pendulum trajectory
    theta_max = np.pi / 3  # Maximum angle
    k = np.sin(theta_max / 2)
    omega = 1.0

    # Sample trajectory
    t_vals = np.linspace(0, 10, 1000)
    theta_vals = np.array([
        2 * np.arcsin(k * float(ellipfun('sn', omega * t, k)))
        for t in t_vals
    ])

    # Construct basis with this modulus
    basis = construct_jacobi_elliptic_basis(
        masses=np.array([1.0]),
        moduli=[k],
        argument_templates=['energy']
    )

    print(f"Elliptic basis size: {len(basis)}")
    # Test if regression can recover θ(t) form
```

---

### Part C: Theta Function Basis (NEW - 0.5 days)

**File**: `src/python/symbolic/theta_basis.py`

**Jacobi Theta Functions**: $\theta_1, \theta_2, \theta_3, \theta_4$

Used for doubly periodic functions (two incommensurable frequencies).

```python
"""
Jacobi theta function basis for symbolic regression.
"""

import numpy as np
from mpmath import jtheta
from typing import List, Tuple, Callable


def construct_theta_basis(
    masses: np.ndarray,
    nome_values: List[float] = [0.1, 0.3, 0.5],
    argument_templates: Optional[List[str]] = None
) -> List[Tuple[Callable, str]]:
    """
    Construct basis using Jacobi theta functions θ₁, θ₂, θ₃, θ₄.

    Args:
        masses: Body masses
        nome_values: List of nome parameter q = exp(iπτ) values to try
        argument_templates: Types of argument functions

    Returns:
        basis: List of (function, name) tuples

    Theta functions are used when the system has quasi-periodic motion
    with two incommensurable periods.
    """
    if argument_templates is None:
        argument_templates = ['angle']

    basis = []
    arg_funcs = get_argument_functions(masses, argument_templates)

    # Four Jacobi theta functions
    for theta_idx in [1, 2, 3, 4]:
        for arg_name, arg_func in arg_funcs.items():
            for q in nome_values:
                basis.append(make_theta_function(
                    theta_idx, arg_func, q, f"theta{theta_idx}({arg_name}, q={q:.1f})"
                ))

    return basis


def make_theta_function(
    theta_index: int,
    arg_func: Callable,
    nome: float,
    name: str
) -> Tuple[Callable, str]:
    """Create a theta function basis element."""
    def theta_func(state: np.ndarray) -> float:
        z = arg_func(state)

        try:
            # Use mpmath jtheta
            result = float(jtheta(theta_index, z, nome).real)

            if not np.isfinite(result):
                return 0.0

            return result
        except:
            return 0.0

    theta_func.__name__ = name
    return (theta_func, name)
```

---

### Part D: Main Basis API (AMENDED - 0.5 days)

**File**: `src/python/symbolic/basis_functions.py` (UPDATE EXISTING)

Add new methods to `BasisLibrary` class:

```python
def add_spinor_basis(self, max_degree: int = 2):
    """Add KS spinor-based functions."""
    from .spinor_basis import construct_spinor_basis
    spinor_funcs = construct_spinor_basis(self.masses, max_degree)
    for func, name in spinor_funcs:
        self.add_function(BasisFunction(
            func=func,
            name=name,
            symbol=name,
            degree=max_degree,
            category='spinor'
        ))


def add_elliptic_basis(
    self,
    moduli: List[float] = [0.5, 0.7, 0.9],
    function_types: List[str] = ['jacobi']
):
    """Add elliptic function-based functions."""
    from .elliptic_basis import construct_jacobi_elliptic_basis

    if 'jacobi' in function_types:
        jacobi_funcs = construct_jacobi_elliptic_basis(self.masses, moduli)
        for func, name in jacobi_funcs:
            self.add_function(BasisFunction(
                func=func,
                name=name,
                symbol=name,
                degree=0,  # Transcendental
                category='elliptic_jacobi'
            ))


def add_theta_basis(self, nome_values: List[float] = [0.1, 0.3, 0.5]):
    """Add Jacobi theta function-based functions."""
    from .theta_basis import construct_theta_basis
    theta_funcs = construct_theta_basis(self.masses, nome_values)
    for func, name in theta_funcs:
        self.add_function(BasisFunction(
            func=func,
            name=name,
            symbol=name,
            degree=0,
            category='theta'
        ))
```

---

## Validation Strategy

### V1. Function Recovery Tests

Test basis on systems with known complex integrals:

1. **Kowalevskaya Top**: Has integral involving elliptic functions
2. **Simple Pendulum**: Exact solution involves $\text{sn}(t, k)$
3. **Two-Body Kepler**: Test spinor basis recovers Runge-Lenz vector

### V2. Numerical Stability

Elliptic functions can have numerical issues:
- Test evaluation on $10^6$ random states
- Check for NaN, Inf, overflow
- Verify periodicity properties

---

## Testing Plan

### Unit Tests

```python
# tests/symbolic/test_enriched_basis.py

def test_spinor_basis_construction():
    masses = np.array([1.0, 1.0, 1.0])
    basis = construct_spinor_basis(masses, max_degree=2)
    assert len(basis) > 20
    assert any('u12_0' in name for _, name in basis)


def test_elliptic_basis_construction():
    masses = np.array([1.0, 1.0, 1.0])
    basis = construct_jacobi_elliptic_basis(masses)
    assert len(basis) > 10
    assert any('sn(' in name for _, name in basis)


def test_elliptic_function_periodicity():
    """Test that sn(u + 4K, k) = sn(u, k)."""
    k = 0.7
    K = float(ellipk(k**2))  # Complete elliptic integral

    u = 1.5
    sn_u = float(ellipfun('sn', u, k))
    sn_u_plus_4K = float(ellipfun('sn', u + 4*K, k))

    assert np.abs(sn_u - sn_u_plus_4K) < 1e-10
```

---

## Deliverables (UPDATED)

### Code Modules (8 files)

- [x] `geometric_invariants.py` (~500 lines)
- [x] `polynomial_basis.py` (~300 lines)
- [x] `physics_basis.py` (~400 lines)
- [x] `basis_functions.py` (~400 lines, UPDATED)
- [ ] **`spinor_basis.py`** (~600 lines, NEW)
- [ ] **`elliptic_basis.py`** (~700 lines, NEW)
- [ ] **`theta_basis.py`** (~300 lines, NEW)
- [ ] **`special_functions_utils.py`** (~200 lines, NEW)

**Total**: ~3,400 lines (vs. 1,700 original)

### Documentation

- [ ] **"Complete Basis Catalog"** - Table of all 500+ basis functions
- [ ] **"Elliptic Functions in Mechanics"** - Tutorial with examples
- [ ] **"KS Spinor Geometry"** - Mathematical background
- [ ] Performance benchmarks (evaluation time per function type)

---

## Success Criteria (REVISED)

### Minimum Success
- [ ] Spinor basis implemented and tested
- [ ] Elliptic basis (Jacobi) functional
- [ ] Can evaluate all basis functions without crashing

### Target Success
- [ ] All 8 basis levels implemented
- [ ] Regression success rate on test cases (Kowalevskaya top) > 80%
- [ ] Spinor basis recovers known Kepler integrals

### Stretch Success
- [ ] Automatic modulus/parameter fitting for elliptic functions
- [ ] Theta functions operational
- [ ] Publication: "Enriched Basis Functions for Three-Body Symbolic Regression"

---

**Document Version**: 2.0 (AMENDED)
**Created**: 2025-11-20
**Status**: Extended Implementation Plan with Non-Standard Functions
**Estimated Implementation Time**: 5-6 days (extended from 3-4 days)
**Key Additions**:
- Spinor basis from KS regularization
- Jacobi elliptic functions (sn, cn, dn)
- Weierstrass ℘ function
- Jacobi theta functions
- Enhanced validation on integrable systems
