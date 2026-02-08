# Task 2.1.1 Part B: Marsden-Weinstein Symplectic Reduction - Detailed Implementation Design

**Task**: WP 2.1.1 - Coordinate Systems and Reduction
**Part**: B - Marsden-Weinstein Symplectic Reduction
**Status**: Implementation Phase
**Estimated Duration**: 3 days
**Dependencies**: Part A Complete (Coordinate System Implementations)

---

## Table of Contents

1. [Overview](#overview)
2. [Theoretical Background](#theoretical-background)
3. [Architecture & Design Principles](#architecture--design-principles)
4. [B1: Theoretical Foundation](#b1-theoretical-foundation)
5. [B2: Reduction by Translations](#b2-reduction-by-translations)
6. [B3: Reduction by Rotations (SO(3))](#b3-reduction-by-rotations-so3)
7. [Integration & Testing Strategy](#integration--testing-strategy)
8. [Implementation Checklist](#implementation-checklist)

---

## Overview

### Purpose

Part B implements the Marsden-Weinstein symplectic reduction framework for the three-body problem. This machinery removes the trivial symmetries (translations and rotations) to obtain a reduced phase space where the true dynamics occurs.

### Scope

We implement two symplectic reduction operations:

1. **Translation Reduction**: Quotient by $\mathbb{R}^3$ translations (remove center-of-mass motion)
2. **Rotation Reduction**: Quotient by $SO(3)$ rotations (reduce to shape dynamics)

The composition of these reductions yields the **shape space dynamics** - the foundation for discovering hidden integrability.

### Key Design Goals

- **Symplectic Structure Preservation**: Maintain Hamiltonian structure throughout reduction
- **High Precision**: Constraint enforcement to machine precision
- **Flexibility**: Support both zero and non-zero angular momentum reduction
- **Geometric Rigor**: Explicit computation of connection forms and curvature
- **Testability**: Validate conservation laws and symplectic properties numerically

---

## Theoretical Background

### Marsden-Weinstein Reduction

**Setup**: Given a Hamiltonian system $(M, \omega, H)$ with:
- Symplectic manifold $M$ (phase space)
- Symplectic form $\omega$ (non-degenerate closed 2-form)
- Hamiltonian function $H: M \to \mathbb{R}$
- Lie group $G$ acting on $M$ preserving $\omega$ and $H$

**Momentum Map**: $\mu: M \to \mathfrak{g}^*$ (dual of Lie algebra)
- For translations: $\mu_{\text{trans}} = \mathbf{P}$ (total linear momentum)
- For rotations: $\mu_{\text{rot}} = \mathbf{L}$ (total angular momentum)

**Reduction Theorem**: For $c \in \mathfrak{g}^*$, the quotient
$$
M_c = \mu^{-1}(c) / G
$$
inherits a symplectic structure $\omega_{\text{red}}$ making it a Hamiltonian system with reduced Hamiltonian $H_{\text{red}}$.

### Application to 3-Body Problem

**Original Phase Space**: $M = T^*\mathbb{R}^9 \cong \mathbb{R}^{18}$
- 9 position DOF, 9 momentum DOF

**Symmetry Group**: $G = \mathbb{R}^3 \times SO(3)$ (Euclidean group)
- Translations: 3 DOF
- Rotations: 3 DOF

**Reduced Phase Space** (for $\mathbf{P} = 0$, $\mathbf{L} = 0$):
- Planar case: $\dim M_{\text{red}} = 12 - 3 - 2 = 7$ (SO(2) rotation)
- Spatial case: $\dim M_{\text{red}} = 18 - 3 - 3 = 12$

**Key Insight**: The reduced symplectic form encodes the **mechanical connection** - a 1-form that measures the "rotational response" to shape changes. This connection is the key obstruction to integrability.

---

## Architecture & Design Principles

### Module Structure

```
src/python/reduction/
├── __init__.py                    # Package exports
├── base.py                        # Abstract reduction interface
├── translation_reduction.py       # B2: Translation reduction
├── rotation_reduction.py          # B3: Rotation reduction
├── connection.py                  # Mechanical connection computation
└── validation.py                  # Symplectic structure validation

tests/
├── test_translation_reduction.py
├── test_rotation_reduction.py
├── test_connection.py
└── test_symplectic_reduction.py
```

### Design Patterns

1. **Abstract Base Class**: `SymplecticReduction` defines reduction interface
2. **Composition**: Combine translation and rotation reduction for full reduction
3. **Lazy Evaluation**: Compute connection forms on-demand
4. **Numerical Validation**: Explicit checks for symplecticity and conservation

### Core Abstractions

```python
from abc import ABC, abstractmethod
from typing import Protocol
import numpy as np

class SymplecticReduction(ABC):
    """Abstract base for symplectic reduction operations"""

    @abstractmethod
    def reduce(self, state, masses):
        """Perform reduction on given state"""
        pass

    @abstractmethod
    def momentum_map(self, state, masses):
        """Compute momentum map value"""
        pass

    @abstractmethod
    def validate_constraint(self, state, masses, tolerance=1e-14):
        """Verify momentum constraint is satisfied"""
        pass
```

---

## B1: Theoretical Foundation

### The Reduction Process

For the 3-body problem, reduction proceeds in stages:

**Stage 1: Translation Reduction**
- Input: $(r_1, r_2, r_3, v_1, v_2, v_3) \in \mathbb{R}^{18}$
- Constraint: $\mathbf{P} = \sum m_i \mathbf{v}_i = 0$
- Quotient: Work in barycentric frame ($\sum m_i \mathbf{r}_i = 0$)
- Output: Reduced to 15 DOF (18 - 3)

**Stage 2: Rotation Reduction**
- Input: Barycentric state with 15 DOF
- Constraint: $\mathbf{L} = \sum \mathbf{r}_i \times m_i \mathbf{v}_i = \mathbf{L}_0$ (fixed)
- Quotient: Fix orientation (e.g., align body 1-2 with x-axis)
- Output: Shape space with 12 DOF (planar: 7 DOF)

### The Mechanical Connection

The reduced symplectic form is **not** simply the quotient of the original form. Instead:
$$
\omega_{\text{red}} = \omega_{\text{shape}} - d(\mathbf{L} \cdot \mathcal{A})
$$

where $\mathcal{A}$ is the **mechanical connection** - a 1-form on shape space encoding rotational coupling.

**Physical Interpretation**: When you change the shape of the triangle, the system automatically rotates to conserve angular momentum. This coupling is measured by $\mathcal{A}$.

**Curvature**: The curvature of $\mathcal{A}$ is the obstruction to integrability:
$$
\mathcal{F} = d\mathcal{A}
$$

If $\mathcal{F} = 0$, the connection is flat and the system may be integrable. If $\mathcal{F} \ne 0$, there is genuine geometric complexity.

---

## B2: Reduction by Translations

### Mathematical Specification

**Momentum Map**:
$$
\mu_{\text{trans}}(\mathbf{r}, \mathbf{v}) = \sum_{i=1}^3 m_i \mathbf{v}_i
$$

**Zero Level Set**: $\mu_{\text{trans}}^{-1}(0) = \{\mathbf{P} = 0\}$ (barycentric frame)

**Reduced Space**: Quotient by $\mathbb{R}^3$ translations
- Equivalence: $(\mathbf{r}_1, \mathbf{r}_2, \mathbf{r}_3) \sim (\mathbf{r}_1 + \mathbf{a}, \mathbf{r}_2 + \mathbf{a}, \mathbf{r}_3 + \mathbf{a})$
- Representative: Choose $\sum m_i \mathbf{r}_i = 0$

### Implementation Design

#### Module: `translation_reduction.py`

```python
"""
Translation reduction for 3-body problem.

Implements quotient by ℝ³ translations, enforcing zero total momentum.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional

from ..coordinates.cartesian import CartesianState
from ..coordinates.base import Masses
from .base import SymplecticReduction


@dataclass(frozen=True)
class TranslationReducedState:
    """
    State in translation-reduced phase space.

    This is a Cartesian state with enforced constraints:
        - Center of mass at origin: sum(m_i * r_i) = 0
        - Total momentum zero: sum(m_i * v_i) = 0

    Dimension: 18 → 15 DOF (removed 3 translation DOF)
    """
    state: CartesianState
    masses: Masses

    def __post_init__(self):
        """Validate constraints"""
        assert self._check_barycentric(tolerance=1e-13), \
            "State must be in barycentric frame"
        assert self._check_zero_momentum(tolerance=1e-13), \
            "State must have zero total momentum"

    def _check_barycentric(self, tolerance: float) -> bool:
        """Verify center of mass is at origin"""
        m = np.array([self.masses.m1, self.masses.m2, self.masses.m3])
        r_cm = np.sum(self.state.positions * m[:, np.newaxis], axis=0)
        return np.linalg.norm(r_cm) < tolerance

    def _check_zero_momentum(self, tolerance: float) -> bool:
        """Verify total momentum is zero"""
        m = np.array([self.masses.m1, self.masses.m2, self.masses.m3])
        P = np.sum(m[:, np.newaxis] * self.state.velocities, axis=0)
        return np.linalg.norm(P) < tolerance


class TranslationReduction(SymplecticReduction):
    """
    Symplectic reduction by ℝ³ translations.

    Removes center-of-mass motion from the 3-body problem.
    """

    def __init__(self, tolerance: float = 1e-14):
        """
        Initialize translation reduction.

        Args:
            tolerance: Tolerance for constraint enforcement
        """
        self.tolerance = tolerance

    def momentum_map(self, state: CartesianState, masses: Masses) -> np.ndarray:
        """
        Compute total linear momentum.

        Args:
            state: Cartesian state
            masses: Mass parameters

        Returns:
            P: Total linear momentum vector (3D)
        """
        m = np.array([masses.m1, masses.m2, masses.m3])
        P = np.sum(m[:, np.newaxis] * state.velocities, axis=0)
        return P

    def reduce(self, state: CartesianState, masses: Masses) -> TranslationReducedState:
        """
        Project state onto translation-reduced space.

        Algorithm:
            1. Compute center of mass: r_cm = sum(m_i * r_i) / M
            2. Shift positions: r_i' = r_i - r_cm
            3. Compute momentum: v_cm = sum(m_i * v_i) / M
            4. Shift velocities: v_i' = v_i - v_cm

        Args:
            state: Arbitrary Cartesian state
            masses: Mass parameters

        Returns:
            Reduced state in barycentric frame
        """
        m = np.array([masses.m1, masses.m2, masses.m3])
        M = masses.total

        # Compute center of mass
        r_cm = np.sum(state.positions * m[:, np.newaxis], axis=0) / M
        v_cm = np.sum(state.velocities * m[:, np.newaxis], axis=0) / M

        # Shift to barycentric frame
        positions_bc = state.positions - r_cm
        velocities_bc = state.velocities - v_cm

        # Create reduced state
        state_bc = CartesianState(
            positions=positions_bc,
            velocities=velocities_bc,
            dimension=state.dimension,
            precision=state.precision
        )

        return TranslationReducedState(state_bc, masses)

    def validate_constraint(
        self,
        state: CartesianState,
        masses: Masses,
        tolerance: Optional[float] = None
    ) -> bool:
        """
        Check if state satisfies zero momentum constraint.

        Args:
            state: State to validate
            masses: Mass parameters
            tolerance: Override default tolerance

        Returns:
            True if constraint is satisfied within tolerance
        """
        tol = tolerance if tolerance is not None else self.tolerance
        P = self.momentum_map(state, masses)
        return np.linalg.norm(P) < tol

    def compute_reduced_hamiltonian(
        self,
        state: TranslationReducedState,
        G: float = 1.0
    ) -> float:
        """
        Compute Hamiltonian on reduced space.

        Since translation is a symmetry, H is unchanged:
            H_red = H_original |_{P=0}

        Args:
            state: Translation-reduced state
            G: Gravitational constant

        Returns:
            Energy (scalar)
        """
        from ..coordinates.cartesian import compute_energy
        return compute_energy(state.state, state.masses, G=G)

    def project_onto_constraint_surface(
        self,
        state: CartesianState,
        masses: Masses
    ) -> CartesianState:
        """
        Project arbitrary state onto zero momentum surface.

        This is the same as reduce() but returns CartesianState.

        Args:
            state: Arbitrary state
            masses: Mass parameters

        Returns:
            Projected state with P = 0
        """
        reduced = self.reduce(state, masses)
        return reduced.state
```

#### Validation Functions

```python
def test_translation_invariance(
    state: CartesianState,
    masses: Masses,
    G: float = 1.0,
    n_tests: int = 10
) -> dict:
    """
    Verify that Hamiltonian is invariant under translations.

    Test: H(r_i, v_i) == H(r_i + a, v_i) for arbitrary a

    Returns:
        Dictionary with max/mean energy differences
    """
    from ..coordinates.cartesian import compute_energy

    E0 = compute_energy(state, masses, G=G)
    errors = []

    for _ in range(n_tests):
        # Random translation
        a = np.random.randn(3)

        # Translate state
        state_translated = CartesianState(
            positions=state.positions + a,
            velocities=state.velocities,
            dimension=state.dimension
        )

        E1 = compute_energy(state_translated, masses, G=G)
        errors.append(abs(E1 - E0))

    return {
        'max_error': max(errors),
        'mean_error': np.mean(errors),
        'passed': max(errors) < 1e-13
    }


def test_momentum_conservation(
    state0: TranslationReducedState,
    integrator,
    t_span: tuple,
    **integrator_kwargs
) -> dict:
    """
    Integrate reduced state and verify P remains zero.

    Args:
        state0: Initial translation-reduced state
        integrator: Integration function
        t_span: (t_start, t_end)

    Returns:
        Dictionary with momentum drift statistics
    """
    # Integrate
    solution = integrator(state0.state, state0.masses, t_span, **integrator_kwargs)

    # Compute momentum at all times
    reduction = TranslationReduction()
    momentum_norms = []

    for state in solution.states:
        P = reduction.momentum_map(state, state0.masses)
        momentum_norms.append(np.linalg.norm(P))

    return {
        'max_momentum': max(momentum_norms),
        'mean_momentum': np.mean(momentum_norms),
        'passed': max(momentum_norms) < 1e-12
    }
```

---

## B3: Reduction by Rotations (SO(3))

### Mathematical Specification

**Momentum Map**:
$$
\mu_{\text{rot}}(\mathbf{r}, \mathbf{v}) = \sum_{i=1}^3 \mathbf{r}_i \times m_i \mathbf{v}_i
$$

**Fixed Angular Momentum Level Set**: $\mu_{\text{rot}}^{-1}(\mathbf{L}_0)$
- Standard case: $\mathbf{L}_0 = 0$ (zero angular momentum)
- General case: $\mathbf{L}_0 \ne 0$ (moving frame)

**Reduced Space**: Quotient by $SO(3)$ rotations
- Planar: Quotient by $SO(2)$ (single rotation angle)
- Spatial: Quotient by full $SO(3)$ (3 Euler angles)

### Implementation Design

#### Module: `rotation_reduction.py`

```python
"""
Rotation reduction for 3-body problem.

Implements quotient by SO(3) rotations, fixing orientation.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, Literal
from enum import Enum

from ..coordinates.cartesian import CartesianState
from ..coordinates.base import Masses
from .base import SymplecticReduction
from .translation_reduction import TranslationReducedState


class OrientationConvention(Enum):
    """Conventions for fixing orientation"""
    ALIGN_AXIS_12 = "align_12"      # Align bodies 1-2 with x-axis
    ALIGN_AXIS_23 = "align_23"      # Align bodies 2-3 with x-axis
    ALIGN_ANGULAR_MOMENTUM = "align_L"  # Align L with z-axis (spatial)
    PRINCIPAL_AXES = "principal"    # Align with principal axes of inertia


@dataclass(frozen=True)
class RotationReducedState:
    """
    State in rotation-reduced phase space (shape space).

    This is a state with fixed orientation according to some convention.

    Attributes:
        state: Underlying Cartesian state (in canonical orientation)
        masses: Mass parameters
        L: Angular momentum (conserved quantity labeling the reduction)
        orientation_convention: Which convention was used
        theta: Orientation angle that was removed (for reconstruction)
    """
    state: CartesianState
    masses: Masses
    L: np.ndarray  # Angular momentum vector (3D)
    orientation_convention: OrientationConvention = OrientationConvention.ALIGN_AXIS_12
    theta: Optional[float] = None  # For planar case: SO(2) angle

    @property
    def is_planar(self) -> bool:
        """Check if this is planar motion"""
        return self.state.dimension == 2

    @property
    def L_magnitude(self) -> float:
        """Magnitude of angular momentum"""
        return np.linalg.norm(self.L)

    @property
    def L_z(self) -> float:
        """Out-of-plane component (planar case)"""
        return self.L[2]


class RotationReduction(SymplecticReduction):
    """
    Symplectic reduction by SO(3) rotations.

    Removes rotational degrees of freedom, reducing to shape space.
    """

    def __init__(
        self,
        orientation_convention: OrientationConvention = OrientationConvention.ALIGN_AXIS_12,
        tolerance: float = 1e-14
    ):
        """
        Initialize rotation reduction.

        Args:
            orientation_convention: How to fix orientation
            tolerance: Tolerance for constraint enforcement
        """
        self.orientation_convention = orientation_convention
        self.tolerance = tolerance

    def momentum_map(self, state: CartesianState, masses: Masses) -> np.ndarray:
        """
        Compute total angular momentum.

        L = sum_i r_i × (m_i * v_i)

        Args:
            state: Cartesian state
            masses: Mass parameters

        Returns:
            L: Total angular momentum vector (3D)
        """
        m = np.array([masses.m1, masses.m2, masses.m3])
        L = np.zeros(3)

        for i in range(3):
            L += m[i] * np.cross(state.positions[i], state.velocities[i])

        return L

    def reduce(
        self,
        state: CartesianState,
        masses: Masses,
        L_target: Optional[np.ndarray] = None
    ) -> RotationReducedState:
        """
        Project state onto rotation-reduced space.

        Algorithm:
            1. Compute current angular momentum L
            2. Choose canonical orientation (according to convention)
            3. Rotate state to canonical orientation
            4. Return reduced state with L and rotation angle

        Args:
            state: Cartesian state (should be barycentric)
            masses: Mass parameters
            L_target: Target angular momentum (for validation)

        Returns:
            Reduced state in canonical orientation
        """
        # Compute angular momentum
        L = self.momentum_map(state, masses)

        # Validate against target if provided
        if L_target is not None:
            assert np.linalg.norm(L - L_target) < self.tolerance, \
                f"Angular momentum mismatch: {L} vs {L_target}"

        # Fix orientation
        if self.orientation_convention == OrientationConvention.ALIGN_AXIS_12:
            state_canonical, theta = self._align_axis_12(state)
        elif self.orientation_convention == OrientationConvention.ALIGN_ANGULAR_MOMENTUM:
            state_canonical, theta = self._align_angular_momentum(state, L)
        else:
            raise NotImplementedError(
                f"Convention {self.orientation_convention} not implemented"
            )

        return RotationReducedState(
            state=state_canonical,
            masses=masses,
            L=L,
            orientation_convention=self.orientation_convention,
            theta=theta
        )

    def _align_axis_12(self, state: CartesianState) -> tuple[CartesianState, float]:
        """
        Align body 1-2 axis with x-axis (planar SO(2) rotation).

        Returns:
            state_canonical: Rotated state
            theta: Rotation angle applied
        """
        # Relative position vector
        r12 = state.positions[0] - state.positions[1]

        # Current angle in xy-plane
        theta = np.arctan2(r12[1], r12[0])

        # Rotation matrix (about z-axis, angle -theta)
        R = self._rotation_matrix_z(-theta)

        # Apply rotation
        positions_rot = state.positions @ R.T
        velocities_rot = state.velocities @ R.T

        state_canonical = CartesianState(
            positions=positions_rot,
            velocities=velocities_rot,
            dimension=state.dimension,
            precision=state.precision
        )

        return state_canonical, theta

    def _align_angular_momentum(
        self,
        state: CartesianState,
        L: np.ndarray
    ) -> tuple[CartesianState, Optional[float]]:
        """
        Align angular momentum with z-axis (spatial case).

        For planar motion, L already points in z-direction.
        For spatial motion, apply rotation to align L with z-axis.

        Returns:
            state_canonical: Rotated state
            theta: Rotation angle (None for spatial)
        """
        L_norm = np.linalg.norm(L)

        if L_norm < 1e-14:
            # Zero angular momentum - no preferred direction
            # Use another convention (e.g., align axis 1-2)
            return self._align_axis_12(state)

        # Normalize L
        L_hat = L / L_norm
        z_hat = np.array([0, 0, 1])

        # Check if already aligned
        if np.linalg.norm(L_hat - z_hat) < 1e-14:
            return state, 0.0

        # Rotation axis: n = L_hat × z_hat
        n = np.cross(L_hat, z_hat)
        n_norm = np.linalg.norm(n)

        if n_norm < 1e-14:
            # L is antiparallel to z (flip sign)
            R = np.diag([1, 1, -1])
            theta = np.pi
        else:
            n_hat = n / n_norm

            # Rotation angle
            cos_theta = np.dot(L_hat, z_hat)
            theta = np.arccos(np.clip(cos_theta, -1, 1))

            # Rodrigues formula for rotation matrix
            R = self._rotation_matrix_axis_angle(n_hat, theta)

        # Apply rotation
        positions_rot = state.positions @ R.T
        velocities_rot = state.velocities @ R.T

        state_canonical = CartesianState(
            positions=positions_rot,
            velocities=velocities_rot,
            dimension=state.dimension,
            precision=state.precision
        )

        return state_canonical, theta

    @staticmethod
    def _rotation_matrix_z(theta: float) -> np.ndarray:
        """
        Rotation matrix about z-axis by angle theta.

        R_z(θ) = [cos θ  -sin θ  0]
                 [sin θ   cos θ  0]
                 [  0       0    1]
        """
        c, s = np.cos(theta), np.sin(theta)
        return np.array([
            [c, -s, 0],
            [s,  c, 0],
            [0,  0, 1]
        ])

    @staticmethod
    def _rotation_matrix_axis_angle(n: np.ndarray, theta: float) -> np.ndarray:
        """
        Rotation matrix about axis n by angle theta (Rodrigues formula).

        R = I + sin(θ) [n]× + (1 - cos(θ)) [n]×²

        where [n]× is the skew-symmetric matrix of n.
        """
        c, s = np.cos(theta), np.sin(theta)

        # Skew-symmetric matrix
        nx = np.array([
            [0, -n[2], n[1]],
            [n[2], 0, -n[0]],
            [-n[1], n[0], 0]
        ])

        # Rodrigues formula
        R = np.eye(3) + s * nx + (1 - c) * (nx @ nx)
        return R

    def validate_constraint(
        self,
        state: CartesianState,
        masses: Masses,
        L_target: np.ndarray,
        tolerance: Optional[float] = None
    ) -> bool:
        """
        Check if state has the target angular momentum.

        Args:
            state: State to validate
            masses: Mass parameters
            L_target: Expected angular momentum
            tolerance: Override default tolerance

        Returns:
            True if constraint is satisfied within tolerance
        """
        tol = tolerance if tolerance is not None else self.tolerance
        L = self.momentum_map(state, masses)
        return np.linalg.norm(L - L_target) < tol

    def reconstruct_from_reduced(
        self,
        reduced_state: RotationReducedState,
        theta: float
    ) -> CartesianState:
        """
        Reconstruct full Cartesian state from reduced state.

        This applies the inverse rotation to restore the original orientation.

        Args:
            reduced_state: State in canonical orientation
            theta: Rotation angle to apply

        Returns:
            Cartesian state in arbitrary orientation
        """
        if reduced_state.orientation_convention == OrientationConvention.ALIGN_AXIS_12:
            # Inverse rotation about z-axis
            R = self._rotation_matrix_z(theta)
        else:
            raise NotImplementedError()

        positions = reduced_state.state.positions @ R.T
        velocities = reduced_state.state.velocities @ R.T

        return CartesianState(
            positions=positions,
            velocities=velocities,
            dimension=reduced_state.state.dimension,
            precision=reduced_state.state.precision
        )
```

#### Mechanical Connection

```python
"""
Mechanical connection for shape space dynamics.

The connection A measures how the system rotates in response to shape changes.
"""

import numpy as np
from typing import Callable

from ..coordinates.cartesian import CartesianState
from ..coordinates.base import Masses
from .rotation_reduction import RotationReducedState


class MechanicalConnection:
    """
    Mechanical connection one-form on shape space.

    The connection A is a 1-form on shape space that encodes the
    coupling between shape changes and rotations.

    Reduced symplectic form:
        ω_red = ω_shape - d(L · A)

    where L is the angular momentum.
    """

    def __init__(self, masses: Masses):
        """
        Initialize connection.

        Args:
            masses: Mass parameters
        """
        self.masses = masses

    def compute_connection_form(
        self,
        reduced_state: RotationReducedState,
        shape_velocity: np.ndarray
    ) -> float:
        """
        Compute connection one-form A evaluated on shape velocity.

        A(δshape) = angular velocity induced by shape change δshape

        Args:
            reduced_state: Current reduced state
            shape_velocity: Tangent vector in shape space

        Returns:
            A(shape_velocity): Real number (rate of rotation)
        """
        # This is a complex calculation requiring:
        # 1. Lift shape_velocity to Cartesian tangent space
        # 2. Compute induced rotation using locked inertia tensor
        # 3. Project onto angular momentum direction

        # Placeholder implementation
        # TODO: Implement full calculation in Task 2.1.2
        return 0.0

    def compute_curvature(
        self,
        reduced_state: RotationReducedState
    ) -> np.ndarray:
        """
        Compute curvature of connection: F = dA.

        The curvature measures the obstruction to integrability.

        Returns:
            F: 2-form on shape space (represented as matrix)
        """
        # Placeholder - full implementation in Task 2.1.2
        return np.zeros((3, 3))
```

---

## Integration & Testing Strategy

### Test Suite Structure

```
tests/
├── unit/
│   ├── test_translation_reduction.py    # Translation reduction
│   ├── test_rotation_reduction.py       # Rotation reduction
│   └── test_connection.py               # Mechanical connection
├── integration/
│   ├── test_full_reduction.py           # Compose translation + rotation
│   ├── test_conservation.py             # P=0, L=const verification
│   └── test_symplectic_structure.py     # Verify ω_red is symplectic
└── validation/
    ├── test_lagrange_reduced.py         # Lagrange equilibrium in shape space
    └── test_figure8_reduced.py          # Figure-8 in shape space
```

### Key Test Cases

#### 1. Translation Reduction Tests

```python
def test_barycenter_projection():
    """Arbitrary state → barycentric frame"""
    # Random state
    state = random_cartesian_state()
    masses = Masses(1.0, 1.0, 1.0)

    # Reduce
    reducer = TranslationReduction()
    reduced = reducer.reduce(state, masses)

    # Verify P = 0
    P = reducer.momentum_map(reduced.state, masses)
    assert np.linalg.norm(P) < 1e-14

def test_translation_invariance():
    """H(r) = H(r + a) for any translation a"""
    state = random_cartesian_state()
    masses = Masses(1.0, 1.5, 2.0)

    E0 = compute_energy(state, masses)

    # Translate by random vector
    a = np.random.randn(3)
    state_translated = translate_state(state, a)

    E1 = compute_energy(state_translated, masses)

    assert abs(E1 - E0) < 1e-14
```

#### 2. Rotation Reduction Tests

```python
def test_orientation_fixing():
    """State → canonical orientation"""
    state = random_barycentric_state()
    masses = Masses(1.0, 1.0, 1.0)

    reducer = RotationReduction(OrientationConvention.ALIGN_AXIS_12)
    reduced = reducer.reduce(state, masses)

    # Verify body 1-2 axis is aligned with x-axis
    r12 = reduced.state.positions[0] - reduced.state.positions[1]
    assert abs(r12[1]) < 1e-14  # y-component should be zero
    assert r12[0] > 0             # x-component should be positive

def test_angular_momentum_conservation():
    """L remains constant during evolution"""
    state0 = random_barycentric_state()
    masses = Masses(1.0, 1.0, 1.0)

    reducer = RotationReduction()
    L0 = reducer.momentum_map(state0, masses)

    # Integrate for some time
    solution = integrate(state0, masses, t_span=(0, 10))

    # Check L at all times
    for state in solution.states:
        L = reducer.momentum_map(state, masses)
        assert np.linalg.norm(L - L0) < 1e-12
```

#### 3. Symplectic Structure Tests

```python
def test_symplectic_form_closure():
    """Verify dω_red = 0 (closedness)"""
    # Compute ω_red on small patch of reduced space
    # Verify Stokes theorem: ∫_∂patch ω = ∫_patch dω = 0
    pass

def test_symplectic_form_nondegeneracy():
    """Verify ω_red is non-degenerate"""
    # Compute matrix representation of ω_red
    # Verify det(ω) ≠ 0
    pass
```

---

## Implementation Checklist

### B2: Translation Reduction
- [ ] `TranslationReducedState` dataclass
- [ ] `TranslationReduction` class
- [ ] Momentum map computation
- [ ] Barycenter projection algorithm
- [ ] Reduced Hamiltonian verification
- [ ] Translation invariance tests
- [ ] Momentum conservation tests
- [ ] High-precision constraint enforcement

### B3: Rotation Reduction
- [ ] `RotationReducedState` dataclass
- [ ] `RotationReduction` class
- [ ] Angular momentum momentum map
- [ ] Orientation-fixing algorithms:
  - [ ] Align axis 1-2 with x-axis (SO(2))
  - [ ] Align L with z-axis (SO(3))
- [ ] Rotation matrix utilities (Rodrigues formula)
- [ ] State reconstruction from reduced state
- [ ] Angular momentum conservation tests
- [ ] Orientation fixing validation

### B3.4: Mechanical Connection (Infrastructure)
- [ ] `MechanicalConnection` class
- [ ] Connection form computation (placeholder)
- [ ] Curvature computation (placeholder)
- [ ] Documentation for Task 2.1.2 handoff

### Integration & Validation
- [ ] Compose translation + rotation reduction
- [ ] Full reduction test (18 DOF → 7 DOF planar)
- [ ] Symplectic structure validation
- [ ] Lagrange equilibrium in shape space
- [ ] Performance benchmarks
- [ ] Complete API documentation

---

## Next Steps

After completing Part B:

1. **Part C**: Integrate with WP1 infrastructure
   - Adapt integrators to work with reduced states
   - Validate conservation laws in long integrations

2. **Task 2.1.2**: Complete mechanical connection implementation
   - Full computation of connection form A
   - Curvature calculation
   - Geometric analysis

3. **Part D**: Documentation
   - Technical report on reduction
   - Tutorial notebook demonstrating reduction

---

## References

### Geometric Mechanics
1. Marsden & Ratiu, *Introduction to Mechanics and Symmetry* (1999)
2. Marsden & Weinstein, "Reduction of symplectic manifolds with symmetry" (1974)
3. Cushman & Bates, *Global Aspects of Classical Integrable Systems* (1997)

### Three-Body Problem
4. Meyer & Hall, *Introduction to Hamiltonian Dynamical Systems* (2008)
5. Littlejohn & Reinsch, "Gauge fields in the separation of rotations and internal motions" (1997)

---

**Document Version**: 1.0
**Created**: 2025-11-09
**Status**: Design Complete → Ready for Implementation
