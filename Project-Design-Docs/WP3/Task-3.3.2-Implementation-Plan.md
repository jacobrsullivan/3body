# Task 3.3.2: Basis Function Optimization Implementation
## Detailed Implementation Plan

**Duration**: 3-4 days
**Prerequisites**: Task 3.3.1 (Symbolic Regression Pipeline)
**Objective**: Construct physics-informed, hierarchical basis function libraries to maximize symbolic regression success while minimizing search space

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Implementation Details](#implementation-details)
4. [Basis Function Design](#basis-function-design)
5. [Validation Strategy](#validation-strategy)
6. [Integration Points](#integration-points)
7. [Testing Plan](#testing-plan)
8. [Deliverables](#deliverables)

---

## Overview

### Purpose

Task 3.3.2 addresses a critical challenge in symbolic regression: **What functions should we search over?**

**Problem**: The space of all possible mathematical expressions is infinite. Searching blindly is computationally intractable and prone to overfitting.

**Solution**: Construct **physics-informed basis function libraries** that:
1. Respect the geometric structure of the three-body problem
2. Include known conserved quantities and their combinations
3. Use hierarchical refinement (start simple, add complexity only if needed)
4. Are coordinate-independent (based on geometric invariants)

### Key Insight

For Hamiltonian systems, conserved quantities typically have special structure:
- **Linear integrals** correspond to symmetries (Noether's theorem)
- **Quadratic integrals** appear in integrable systems (e.g., Runge-Lenz vector)
- **Geometric quantities** (distances, angles, angular momenta) are building blocks

By designing basis functions around these principles, we dramatically improve symbolic regression success rate and interpretability.

---

## Architecture

### Module Structure

```
src/python/symbolic/
├── basis_functions.py              # Main API (this task)
├── geometric_invariants.py         # Distance, angle, momentum computations
├── polynomial_basis.py             # Standard polynomial bases
├── physics_basis.py                # Energy, angular momentum combinations
├── coordinate_transforms.py        # Cartesian ↔ Shape Space ↔ S¹ ↔ KS
└── basis_validation.py             # Test basis completeness
```

### Hierarchical Search Strategy

```
Level 0: Known Integrals {E, L_x, L_y, L_z, p_θ}
    ↓ Already conserved (trivial)
Level 1: Linear in coordinates/momenta {q_i, p_i}
    ↓ ~10-20 functions
Level 2: Quadratic {q_i q_j, q_i p_j, p_i p_j}
    ↓ ~50-100 functions
Level 3: Cubic {q_i q_j q_k, ...}
    ↓ ~200-500 functions (selective)
Level 4: Geometric combinations {r_12·r_23, L·r_12, ...}
    ↓ Physics-motivated
Level 5: Transcendental {sin(θ), sqrt(r), ...}
    ↓ For periodic/scaling structures
```

**Adaptive Strategy**: Start at Level 1. If SINDy fails (residual too large), move to next level.

---

## Implementation Details

### Part A: Geometric Invariants (1.5 days)

**File**: `src/python/symbolic/geometric_invariants.py`

```python
"""
Compute geometric invariants for the three-body problem.

These are coordinate-independent quantities that are natural building blocks
for conserved quantities.
"""

import numpy as np
from typing import Tuple, Dict, Callable
from dataclasses import dataclass


@dataclass
class GeometricQuantities:
    """Collection of geometric invariants for three-body system."""
    # Distances
    r12: float
    r23: float
    r31: float

    # Relative positions (vectors)
    r12_vec: np.ndarray  # Shape: (3,)
    r23_vec: np.ndarray
    r31_vec: np.ndarray

    # Relative velocities
    v12_vec: np.ndarray
    v23_vec: np.ndarray
    v31_vec: np.ndarray

    # Radial velocities (dot products)
    rdot_12: float  # r̂_12 · v_12
    rdot_23: float
    rdot_31: float

    # Angular momentum (per pair)
    L12_vec: np.ndarray  # r_12 × v_12
    L23_vec: np.ndarray
    L31_vec: np.ndarray

    # Total angular momentum
    L_total: np.ndarray  # Shape: (3,)
    L_magnitude: float

    # Energy components (if masses provided)
    kinetic_energy: float
    potential_energy: float
    total_energy: float


def compute_geometric_quantities(
    state: np.ndarray,
    masses: np.ndarray,
    coordinate_system: str = 'cartesian'
) -> GeometricQuantities:
    """
    Compute all geometric invariants from phase space state.

    Args:
        state: Phase space vector
               - Cartesian: [q1x, q1y, q1z, q2x, q2y, q2z, q3x, q3y, q3z,
                             p1x, p1y, p1z, p2x, p2y, p2z, p3x, p3y, p3z]
               - Shape space: [r12, r23, r31, θ, pr12, pr23, pr31, pθ]
        masses: [m1, m2, m3]
        coordinate_system: 'cartesian', 'shape', 's1', or 'ks'

    Returns:
        GeometricQuantities object with all invariants
    """
    # Convert to Cartesian if needed
    if coordinate_system != 'cartesian':
        state = convert_to_cartesian(state, coordinate_system, masses)

    # Extract positions and momenta
    dim = len(state) // 2
    q = state[:dim].reshape(3, 3)  # (3 bodies, 3 coords)
    p = state[dim:].reshape(3, 3)

    # Compute relative positions
    r12_vec = q[1] - q[0]
    r23_vec = q[2] - q[1]
    r31_vec = q[0] - q[2]

    # Distances
    r12 = np.linalg.norm(r12_vec)
    r23 = np.linalg.norm(r23_vec)
    r31 = np.linalg.norm(r31_vec)

    # Velocities (v = p/m in Cartesian coords)
    v1 = p[0] / masses[0]
    v2 = p[1] / masses[1]
    v3 = p[2] / masses[2]

    # Relative velocities
    v12_vec = v2 - v1
    v23_vec = v3 - v2
    v31_vec = v1 - v3

    # Radial velocities
    rdot_12 = np.dot(r12_vec, v12_vec) / r12 if r12 > 1e-10 else 0.0
    rdot_23 = np.dot(r23_vec, v23_vec) / r23 if r23 > 1e-10 else 0.0
    rdot_31 = np.dot(r31_vec, v31_vec) / r31 if r31 > 1e-10 else 0.0

    # Angular momentum (per pair)
    L12_vec = np.cross(r12_vec, masses[0]*masses[1]/(masses[0]+masses[1]) * v12_vec)
    L23_vec = np.cross(r23_vec, masses[1]*masses[2]/(masses[1]+masses[2]) * v23_vec)
    L31_vec = np.cross(r31_vec, masses[2]*masses[0]/(masses[2]+masses[0]) * v31_vec)

    # Total angular momentum
    L_total = np.cross(q[0], p[0]) + np.cross(q[1], p[1]) + np.cross(q[2], p[2])
    L_magnitude = np.linalg.norm(L_total)

    # Energy
    T = 0.5 * np.sum(p**2 / masses[:, None])  # Kinetic
    V = -masses[0]*masses[1]/r12 - masses[1]*masses[2]/r23 - masses[2]*masses[0]/r31  # Potential
    E = T + V

    return GeometricQuantities(
        r12=r12, r23=r23, r31=r31,
        r12_vec=r12_vec, r23_vec=r23_vec, r31_vec=r31_vec,
        v12_vec=v12_vec, v23_vec=v23_vec, v31_vec=v31_vec,
        rdot_12=rdot_12, rdot_23=rdot_23, rdot_31=rdot_31,
        L12_vec=L12_vec, L23_vec=L23_vec, L31_vec=L31_vec,
        L_total=L_total, L_magnitude=L_magnitude,
        kinetic_energy=T, potential_energy=V, total_energy=E
    )


def geometric_basis_functions(
    masses: np.ndarray,
    coordinate_system: str = 'cartesian',
    include_pairs: bool = True,
    include_vectors: bool = False
) -> Dict[str, Callable]:
    """
    Construct basis of geometric invariant functions.

    Returns:
        basis: Dictionary mapping names to functions
               Each function signature: state -> float
    """
    basis = {}

    def make_invariant_func(extractor: Callable[[GeometricQuantities], float], name: str):
        """Factory for creating basis functions from geometric quantities."""
        def func(state: np.ndarray) -> float:
            geom = compute_geometric_quantities(state, masses, coordinate_system)
            return extractor(geom)
        func.__name__ = name
        return func

    # Distances
    basis['r12'] = make_invariant_func(lambda g: g.r12, 'r12')
    basis['r23'] = make_invariant_func(lambda g: g.r23, 'r23')
    basis['r31'] = make_invariant_func(lambda g: g.r31, 'r31')

    # Powers of distances
    basis['r12_sq'] = make_invariant_func(lambda g: g.r12**2, 'r12_sq')
    basis['r23_sq'] = make_invariant_func(lambda g: g.r23**2, 'r23_sq')
    basis['r31_sq'] = make_invariant_func(lambda g: g.r31**2, 'r31_sq')

    # Radial velocities
    basis['rdot_12'] = make_invariant_func(lambda g: g.rdot_12, 'rdot_12')
    basis['rdot_23'] = make_invariant_func(lambda g: g.rdot_23, 'rdot_23')
    basis['rdot_31'] = make_invariant_func(lambda g: g.rdot_31, 'rdot_31')

    # Angular momentum magnitude
    basis['L_mag'] = make_invariant_func(lambda g: g.L_magnitude, 'L_mag')
    basis['L_sq'] = make_invariant_func(lambda g: g.L_magnitude**2, 'L_sq')

    # Energy
    basis['E'] = make_invariant_func(lambda g: g.total_energy, 'E')

    # Pairwise products (if requested)
    if include_pairs:
        basis['r12_r23'] = make_invariant_func(lambda g: g.r12 * g.r23, 'r12_r23')
        basis['r12_r31'] = make_invariant_func(lambda g: g.r12 * g.r31, 'r12_r31')
        basis['r23_r31'] = make_invariant_func(lambda g: g.r23 * g.r31, 'r23_r31')

        # Mixed terms
        basis['r12_rdot12'] = make_invariant_func(lambda g: g.r12 * g.rdot_12, 'r12_rdot12')
        basis['E_L'] = make_invariant_func(lambda g: g.total_energy * g.L_magnitude, 'E_L')

    # Vector dot products (if requested)
    if include_vectors:
        basis['r12_dot_r23'] = make_invariant_func(
            lambda g: np.dot(g.r12_vec, g.r23_vec), 'r12_dot_r23'
        )
        basis['r12_dot_L'] = make_invariant_func(
            lambda g: np.dot(g.r12_vec, g.L_total), 'r12_dot_L'
        )

    return basis


def convert_to_cartesian(
    state: np.ndarray,
    from_system: str,
    masses: np.ndarray
) -> np.ndarray:
    """
    Convert state from various coordinate systems to Cartesian.

    Args:
        state: State vector in specified system
        from_system: 'shape', 's1', or 'ks'
        masses: Body masses

    Returns:
        cartesian_state: State in Cartesian coordinates
    """
    # Placeholder - would call coordinate transformation modules from WP2
    if from_system == 'shape':
        from ..coordinates.shape_space import shape_to_cartesian
        return shape_to_cartesian(state, masses)
    elif from_system == 's1':
        from ..coordinates.s1_bundle import s1_to_cartesian
        return s1_to_cartesian(state, masses)
    elif from_system == 'ks':
        from ..coordinates.ks_coordinates import ks_to_cartesian
        return ks_to_cartesian(state, masses)
    else:
        return state  # Already Cartesian
```

---

### Part B: Polynomial Basis Construction (1 day)

**File**: `src/python/symbolic/polynomial_basis.py`

```python
"""
Standard polynomial basis functions for phase space.
"""

import numpy as np
from typing import List, Tuple, Callable
from itertools import combinations_with_replacement, product


def construct_polynomial_basis(
    dim: int,
    max_degree: int = 3,
    include_constant: bool = True,
    include_cross_terms: bool = True
) -> List[Tuple[Callable, str]]:
    """
    Construct complete polynomial basis up to specified degree.

    Args:
        dim: Phase space dimension (2n for n DOF)
        max_degree: Maximum polynomial degree
        include_constant: Include constant term (1.0)
        include_cross_terms: Include mixed terms (q_i p_j)

    Returns:
        basis: List of (function, name) tuples
    """
    basis = []

    # Degree 0: Constant
    if include_constant:
        basis.append((lambda z: 1.0, "1"))

    # Degree 1: Linear terms z_i
    for i in range(dim):
        basis.append((
            lambda z, idx=i: z[idx],
            f"z{i}"
        ))

    # Degree 2: Quadratic terms
    if max_degree >= 2:
        for i in range(dim):
            for j in range(i, dim):
                if i == j:
                    # z_i^2
                    basis.append((
                        lambda z, idx=i: z[idx]**2,
                        f"z{i}^2"
                    ))
                elif include_cross_terms:
                    # z_i * z_j
                    basis.append((
                        lambda z, i=i, j=j: z[i] * z[j],
                        f"z{i}*z{j}"
                    ))

    # Degree 3: Cubic terms (selective to avoid explosion)
    if max_degree >= 3:
        # Only include selected cubics (not all combinations)
        for i in range(dim):
            # z_i^3
            basis.append((
                lambda z, idx=i: z[idx]**3,
                f"z{i}^3"
            ))

        # Mixed cubics: z_i^2 * z_j for i != j
        if include_cross_terms:
            for i in range(dim):
                for j in range(dim):
                    if i != j:
                        basis.append((
                            lambda z, i=i, j=j: z[i]**2 * z[j],
                            f"z{i}^2*z{j}"
                        ))

    return basis


def construct_harmonic_oscillator_basis(dim: int) -> List[Tuple[Callable, str]]:
    """
    Basis functions natural for harmonic oscillator systems.

    Includes q^2, p^2, and q*p terms.
    """
    n_dof = dim // 2
    basis = []

    # Kinetic energy terms: p_i^2
    for i in range(n_dof):
        p_idx = n_dof + i
        basis.append((
            lambda z, idx=p_idx: z[idx]**2,
            f"p{i}^2"
        ))

    # Potential energy terms: q_i^2
    for i in range(n_dof):
        basis.append((
            lambda z, idx=i: z[idx]**2,
            f"q{i}^2"
        ))

    # Coupling terms: q_i * p_i
    for i in range(n_dof):
        p_idx = n_dof + i
        basis.append((
            lambda z, qi=i, pi=p_idx: z[qi] * z[pi],
            f"q{i}*p{i}"
        ))

    return basis


def construct_kepler_basis(dim: int = 4) -> List[Tuple[Callable, str]]:
    """
    Basis functions for Kepler problem (includes Runge-Lenz vector components).

    For 2D Kepler: dim=4 (q_x, q_y, p_x, p_y)
    """
    basis = []

    # Energy: p^2 - 1/r
    basis.append((
        lambda z: z[2]**2 + z[3]**2 - 1/np.sqrt(z[0]**2 + z[1]**2),
        "E"
    ))

    # Angular momentum: L = q_x p_y - q_y p_x
    basis.append((
        lambda z: z[0]*z[3] - z[1]*z[2],
        "L"
    ))

    # Runge-Lenz components (2D):
    # A_x = p_y L - q_x/r
    # A_y = -p_x L - q_y/r
    basis.append((
        lambda z: z[3]*(z[0]*z[3] - z[1]*z[2]) - z[0]/np.sqrt(z[0]**2 + z[1]**2),
        "RL_x"
    ))
    basis.append((
        lambda z: -z[2]*(z[0]*z[3] - z[1]*z[2]) - z[1]/np.sqrt(z[0]**2 + z[1]**2),
        "RL_y"
    ))

    return basis
```

---

### Part C: Physics-Informed Basis (1 day)

**File**: `src/python/symbolic/physics_basis.py`

```python
"""
Physics-informed basis functions for three-body problem.

Combines known conservation laws and geometric structures.
"""

import numpy as np
from typing import List, Tuple, Callable, Dict

from .geometric_invariants import compute_geometric_quantities, GeometricQuantities


def construct_physics_basis(
    masses: np.ndarray,
    coordinate_system: str = 'cartesian',
    include_energy_powers: bool = True,
    include_angular_momentum: bool = True,
    max_degree: int = 3
) -> List[Tuple[Callable, str]]:
    """
    Construct basis functions based on physical intuition.

    Includes:
    - Known conserved quantities (E, L)
    - Powers and products of conserved quantities
    - Geometric invariants (distances, angles)
    - Combinations motivated by integrable limits

    Args:
        masses: Body masses
        coordinate_system: Coordinate system of input states
        include_energy_powers: Include E, E^2, etc.
        include_angular_momentum: Include L components
        max_degree: Maximum degree for combinations

    Returns:
        basis: List of (function, name) tuples
    """
    basis = []

    # Helper to create basis functions
    def make_func(extractor: Callable[[GeometricQuantities], float], name: str):
        def func(state: np.ndarray) -> float:
            geom = compute_geometric_quantities(state, masses, coordinate_system)
            return extractor(geom)
        func.__name__ = name
        return (func, name)

    # Category 1: Known integrals
    basis.append(make_func(lambda g: g.total_energy, "E"))

    if include_angular_momentum:
        basis.append(make_func(lambda g: g.L_magnitude, "L"))
        basis.append(make_func(lambda g: g.L_total[0], "Lx"))
        basis.append(make_func(lambda g: g.L_total[1], "Ly"))
        basis.append(make_func(lambda g: g.L_total[2], "Lz"))

    # Category 2: Powers of conserved quantities
    if include_energy_powers and max_degree >= 2:
        basis.append(make_func(lambda g: g.total_energy**2, "E^2"))
        basis.append(make_func(lambda g: g.L_magnitude**2, "L^2"))

    if max_degree >= 3:
        basis.append(make_func(lambda g: g.total_energy**3, "E^3"))

    # Category 3: Products of conserved quantities
    if include_energy_powers and include_angular_momentum:
        basis.append(make_func(lambda g: g.total_energy * g.L_magnitude, "E*L"))
        if max_degree >= 2:
            basis.append(make_func(lambda g: g.total_energy**2 * g.L_magnitude, "E^2*L"))
            basis.append(make_func(lambda g: g.total_energy * g.L_magnitude**2, "E*L^2"))

    # Category 4: Shape space coordinates (distances)
    basis.append(make_func(lambda g: g.r12, "r12"))
    basis.append(make_func(lambda g: g.r23, "r23"))
    basis.append(make_func(lambda g: g.r31, "r31"))

    # Category 5: Quadratic shape coordinates
    if max_degree >= 2:
        basis.append(make_func(lambda g: g.r12**2, "r12^2"))
        basis.append(make_func(lambda g: g.r23**2, "r23^2"))
        basis.append(make_func(lambda g: g.r31**2, "r31^2"))

        # Mixed products
        basis.append(make_func(lambda g: g.r12 * g.r23, "r12*r23"))
        basis.append(make_func(lambda g: g.r12 * g.r31, "r12*r31"))
        basis.append(make_func(lambda g: g.r23 * g.r31, "r23*r31"))

    # Category 6: Radial velocities
    basis.append(make_func(lambda g: g.rdot_12, "rdot12"))
    basis.append(make_func(lambda g: g.rdot_23, "rdot23"))
    basis.append(make_func(lambda g: g.rdot_31, "rdot31"))

    # Category 7: Mixed energy-shape terms
    basis.append(make_func(lambda g: g.total_energy * g.r12, "E*r12"))
    basis.append(make_func(lambda g: g.L_magnitude * g.r12, "L*r12"))

    # Category 8: Kepler-like combinations (for limiting cases)
    # Runge-Lenz inspired: L × v - r/|r|
    # Approximate with geometric terms
    basis.append(make_func(
        lambda g: g.L_magnitude * g.rdot_12 - 1/g.r12 if g.r12 > 1e-10 else 0,
        "RL_like_12"
    ))

    return basis


def construct_s1_bundle_basis(
    masses: np.ndarray,
    max_degree: int = 3
) -> List[Tuple[Callable, str]]:
    """
    Basis functions for S¹ bundle coordinates.

    State: (s_1, s_2, s_3, θ, p_s1, p_s2, p_s3, p_θ)

    Key hypothesis: p_θ might be conserved!
    """
    basis = []

    # Known fiber momentum
    basis.append((lambda z: z[7], "p_theta"))

    # Shape coordinates
    for i in range(3):
        basis.append((lambda z, idx=i: z[idx], f"s{i}"))

    # Momenta
    for i in range(3):
        basis.append((lambda z, idx=i+4: z[idx], f"ps{i}"))

    # Fiber angle
    basis.append((lambda z: z[3], "theta"))
    basis.append((lambda z: np.sin(z[3]), "sin(theta)"))
    basis.append((lambda z: np.cos(z[3]), "cos(theta)"))

    # Quadratic terms
    if max_degree >= 2:
        for i in range(3):
            basis.append((lambda z, idx=i: z[idx]**2, f"s{i}^2"))

        # Energy-like: sum of momenta squared
        basis.append((
            lambda z: z[4]**2 + z[5]**2 + z[6]**2,
            "sum_ps^2"
        ))

        # Mixed terms: s_i * p_theta
        for i in range(3):
            basis.append((
                lambda z, si=i, pt=7: z[si] * z[pt],
                f"s{i}*p_theta"
            ))

    return basis
```

---

### Part D: Main Basis API (0.5 days)

**File**: `src/python/symbolic/basis_functions.py`

```python
"""
Main API for basis function construction.

Provides unified interface for all basis types and adaptive refinement.
"""

import numpy as np
from typing import List, Tuple, Callable, Dict, Optional
from enum import Enum

from .polynomial_basis import construct_polynomial_basis, construct_kepler_basis
from .physics_basis import construct_physics_basis, construct_s1_bundle_basis
from .geometric_invariants import geometric_basis_functions


class BasisType(Enum):
    """Basis function library types."""
    POLYNOMIAL = "polynomial"
    GEOMETRIC = "geometric"
    PHYSICS = "physics"
    S1_BUNDLE = "s1_bundle"
    KS_SPINOR = "ks_spinor"
    KEPLER = "kepler"
    CUSTOM = "custom"


def construct_basis_library(
    basis_type: BasisType,
    dim: int,
    masses: np.ndarray,
    coordinate_system: str = 'cartesian',
    max_degree: int = 2,
    **kwargs
) -> List[Tuple[Callable, str]]:
    """
    Unified interface for basis construction.

    Args:
        basis_type: Type of basis to construct
        dim: Phase space dimension
        masses: Body masses [m1, m2, m3]
        coordinate_system: Input coordinate system
        max_degree: Maximum polynomial degree
        **kwargs: Additional arguments for specific basis types

    Returns:
        basis: List of (function, name) tuples

    Example:
        >>> basis = construct_basis_library(
        ...     BasisType.PHYSICS, dim=8, masses=np.array([1, 1, 1]),
        ...     coordinate_system='cartesian', max_degree=2
        ... )
        >>> print(f"Basis size: {len(basis)}")
    """
    if basis_type == BasisType.POLYNOMIAL:
        return construct_polynomial_basis(dim, max_degree, **kwargs)

    elif basis_type == BasisType.GEOMETRIC:
        geom_dict = geometric_basis_functions(masses, coordinate_system, **kwargs)
        return [(func, name) for name, func in geom_dict.items()]

    elif basis_type == BasisType.PHYSICS:
        return construct_physics_basis(masses, coordinate_system, max_degree=max_degree, **kwargs)

    elif basis_type == BasisType.S1_BUNDLE:
        return construct_s1_bundle_basis(masses, max_degree, **kwargs)

    elif basis_type == BasisType.KEPLER:
        return construct_kepler_basis(dim)

    else:
        raise ValueError(f"Unknown basis type: {basis_type}")


class AdaptiveBasisRefinement:
    """
    Adaptive basis refinement strategy.

    Starts with simple basis, adds complexity only if regression fails.
    """

    def __init__(
        self,
        dim: int,
        masses: np.ndarray,
        coordinate_system: str = 'cartesian',
        verbose: bool = False
    ):
        self.dim = dim
        self.masses = masses
        self.coordinate_system = coordinate_system
        self.verbose = verbose

        # Refinement levels
        self.levels = [
            ('Physics-Linear', BasisType.PHYSICS, {'max_degree': 1}),
            ('Physics-Quadratic', BasisType.PHYSICS, {'max_degree': 2}),
            ('Geometric', BasisType.GEOMETRIC, {}),
            ('Physics-Cubic', BasisType.PHYSICS, {'max_degree': 3}),
            ('Polynomial-Quadratic', BasisType.POLYNOMIAL, {'max_degree': 2}),
            ('Polynomial-Cubic', BasisType.POLYNOMIAL, {'max_degree': 3}),
        ]

        self.current_level = 0

    def get_next_basis(self) -> Optional[List[Tuple[Callable, str]]]:
        """
        Get next basis in refinement sequence.

        Returns:
            basis: Next basis to try, or None if exhausted
        """
        if self.current_level >= len(self.levels):
            return None

        name, basis_type, kwargs = self.levels[self.current_level]

        if self.verbose:
            print(f"Refinement Level {self.current_level}: {name}")

        basis = construct_basis_library(
            basis_type,
            self.dim,
            self.masses,
            self.coordinate_system,
            **kwargs
        )

        if self.verbose:
            print(f"  Basis size: {len(basis)} functions")

        self.current_level += 1
        return basis

    def reset(self):
        """Reset to initial level."""
        self.current_level = 0
```

---

## Validation Strategy

### V1: Basis Completeness

**Test**: Does the basis contain known integrals?

```python
def test_basis_contains_energy():
    """Verify that physics basis includes energy."""
    masses = np.array([1.0, 1.0, 1.0])
    basis_list = construct_basis_library(
        BasisType.PHYSICS, dim=18, masses=masses, max_degree=2
    )

    # Check that energy function is in basis
    names = [name for _, name in basis_list]
    assert 'E' in names


def test_basis_contains_angular_momentum():
    """Verify that physics basis includes angular momentum."""
    masses = np.array([1.0, 1.0, 1.0])
    basis_list = construct_basis_library(
        BasisType.PHYSICS, dim=18, masses=masses, max_degree=2
    )

    names = [name for _, name in basis_list]
    assert 'L' in names or 'L_mag' in names
```

### V2: Regression Success Rate

**Test**: Does physics-informed basis improve regression success?

```python
def test_physics_basis_improves_success():
    """Compare polynomial vs. physics basis on Kepler problem."""
    # Known Kepler integral: E
    def E_kepler(z):
        q, p = z[:2], z[2:]
        r = np.linalg.norm(q)
        return 0.5 * np.sum(p**2) - 1/r

    points = generate_test_points(1000, dim=4)

    # Try polynomial basis
    poly_basis = construct_basis_library(BasisType.POLYNOMIAL, dim=4, max_degree=2)
    poly_result = symbolic_regression_sindy(E_kepler, points, poly_basis)

    # Try physics basis (should do better)
    phys_basis = construct_basis_library(BasisType.KEPLER, dim=4)
    phys_result = symbolic_regression_sindy(E_kepler, points, phys_basis)

    assert phys_result.residual < poly_result.residual
```

---

## Integration Points

### With Task 3.3.1 (Symbolic Regression)

```python
# Adaptive refinement workflow
from symbolic.basis_functions import AdaptiveBasisRefinement
from symbolic.regression_pipeline import symbolic_regression_pipeline

# Initialize adaptive refinement
refiner = AdaptiveBasisRefinement(dim=8, masses=masses, verbose=True)

# Try progressively more complex bases
result = None
while True:
    basis = refiner.get_next_basis()
    if basis is None:
        break  # Exhausted all levels

    # Try regression with this basis
    result = symbolic_regression_pipeline(
        I_numerical, sample_points, basis, method=RegressionMethod.SINDY
    )

    if result.success:
        print(f"Success with {refiner.current_level-1} refinement level!")
        break
```

---

## Testing Plan

### Unit Tests

1. **Geometric invariants**: `test_geometric_invariants.py`
   - Distance computations
   - Angular momentum
   - Energy components

2. **Polynomial basis**: `test_polynomial_basis.py`
   - Size scaling with degree
   - Cross-term inclusion

3. **Physics basis**: `test_physics_basis.py`
   - Known integrals present
   - Correct dimensionality

### Integration Tests

4. **Adaptive refinement**: `test_adaptive_refinement.py`
   - Progressive complexity
   - Success on known cases

---

## Deliverables

### Code Modules (5 files)

- [ ] `geometric_invariants.py` (~500 lines)
- [ ] `polynomial_basis.py` (~300 lines)
- [ ] `physics_basis.py` (~400 lines)
- [ ] `basis_functions.py` (~300 lines)
- [ ] `coordinate_transforms.py` (~200 lines, if needed)

**Total**: ~1,700 lines

### Documentation

- [ ] Basis library catalog (table of all available bases)
- [ ] Tutorial: "Choosing the Right Basis for Your Problem"

### Validation

- [ ] Test coverage: >90%
- [ ] Benchmark: Kepler, harmonic oscillator recovery

---

## Success Criteria

### Minimum Success
- [ ] Polynomial and geometric bases implemented
- [ ] Can construct basis for any coordinate system
- [ ] Adaptive refinement functional

### Target Success
- [ ] Physics basis includes all expected terms
- [ ] Regression success rate >70% on test cases
- [ ] Basis size scales reasonably with degree

### Stretch Success
- [ ] Automatic basis selection based on problem symmetries
- [ ] Symbolic basis simplification (remove redundant functions)
- [ ] Publication-ready basis function catalog

---

**Document Version**: 1.0
**Created**: 2025-11-16
**Status**: Complete Implementation Plan
**Estimated Implementation Time**: 3-4 days
