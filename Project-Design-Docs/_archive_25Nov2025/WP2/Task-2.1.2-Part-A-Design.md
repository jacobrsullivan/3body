# Task 2.1.2 Part A: Connection Form Computation - Detailed Design

**Task**: WP 2.1.2 - Computation of the "Magnetic Twist" (Connection and Curvature)
**Part**: A - Connection Form Computation
**Status**: Design Phase
**Estimated Duration**: 3 days
**Dependencies**: Task 2.1.1 Complete (Shape Space Coordinates)

---

## Table of Contents

1. [Overview](#overview)
2. [Mathematical Foundations](#mathematical-foundations)
3. [A1: Locked Inertia Tensor](#a1-locked-inertia-tensor)
4. [A2: Shape Space Vector Field Lifts](#a2-shape-space-vector-field-lifts)
5. [A3: Connection Coefficient Computation](#a3-connection-coefficient-computation)
6. [A4: Gauge Transformations](#a4-gauge-transformations)
7. [A5: Validation and Testing](#a5-validation-and-testing)
8. [Implementation Details](#implementation-details)
9. [Performance Optimization](#performance-optimization)
10. [Integration Guide](#integration-guide)

---

## Overview

### Purpose

Part A implements the core machinery for computing the **mechanical connection one-form** $\mathcal{A}$ on shape space. The connection encodes how the system automatically rotates when you change its shape while conserving angular momentum—a phenomenon central to the geometric structure of the reduced three-body problem.

### What is the Mechanical Connection?

**Physical Intuition**: Imagine holding two masses in your hands and moving them closer together while keeping the total angular momentum fixed. The third mass will automatically start rotating. The connection $\mathcal{A}$ quantifies this "automatic rotation" induced by shape changes.

**Mathematical Definition**: The connection is a one-form $\mathcal{A} = \mathcal{A}_i ds^i$ on shape space that measures the infinitesimal rotation $\omega$ induced by a shape velocity $\dot{s}$:

$$
\omega = \mathcal{A}(\dot{s})
$$

### Key Components

This part implements three main computational components:

1. **Locked Inertia Tensor**: $I_{\text{locked}}(s)$ - the inertia tensor when shape is "frozen"
2. **Shape Space Lifts**: Maps from shape space tangent vectors to angular velocities
3. **Connection Coefficients**: $\mathcal{A}_i(s)$ - the components of the connection one-form

### Deliverables

- `src/python/geometry/locked_inertia.py` - Locked inertia tensor computation
- `src/python/geometry/shape_lifts.py` - Shape space vector field lifts
- `src/python/geometry/connection.py` - Connection form evaluator
- Complete test suite with validation against known cases
- Performance target: <100 μs per connection evaluation

---

## Mathematical Foundations

### The Reduced Phase Space

After symplectic reduction by translations and rotations (Task 2.1.1), we have:

**Base Space**: Shape space $S$ with coordinates $(r_{12}, r_{23}, r_{31})$ (planar case)

**Reduced Symplectic Form**:
$$
\omega_{\text{red}} = \omega_{\text{shape}} - d(L \cdot \mathcal{A})
$$

where:
- $\omega_{\text{shape}}$ is the naive symplectic form on shape space
- $L$ is the conserved angular momentum (labels the reduced space)
- $\mathcal{A}$ is the **mechanical connection** (what we're computing)

### Momentum Map and Connection

The connection arises from the momentum map for the rotation group $SO(3)$:

$$
\mu: T^*M \to \mathfrak{so}(3)^* \cong \mathbb{R}^3
$$

For the three-body problem:
$$
\mu(r, v) = \mathbf{L} = \sum_{i=1}^3 m_i \mathbf{r}_i \times \mathbf{v}_i
$$

The connection is the "dual" of this momentum map on the reduced space.

### Connection via Locked Inertia

**Key Formula** (Marsden & Ratiu): The connection can be computed using the locked inertia tensor:

$$
\mathcal{A}(\delta s) = I_{\text{locked}}^{-1}(s) \cdot \frac{\partial \mathbf{L}}{\partial s} \cdot \delta s
$$

where:
- $I_{\text{locked}}(s)$ is the inertia tensor with shape fixed
- $\frac{\partial \mathbf{L}}{\partial s}$ measures how angular momentum depends on shape

**Intuition**:
1. Change shape by $\delta s$
2. This induces a change in angular momentum $\delta L = \frac{\partial L}{\partial s} \delta s$
3. To keep $L$ fixed, we must rotate with angular velocity $\omega = I^{-1} \delta L$
4. This $\omega$ is the connection: $\mathcal{A}(\delta s) = \omega$

### Coordinate Representation

In shape space coordinates $(r_{12}, r_{23}, r_{31})$:

$$
\mathcal{A} = \mathcal{A}_{r_{12}} dr_{12} + \mathcal{A}_{r_{23}} dr_{23} + \mathcal{A}_{r_{31}} dr_{31}
$$

We need to compute the three coefficients $\mathcal{A}_{r_{ij}}$.

---

## A1: Locked Inertia Tensor

### Definition

The **locked inertia tensor** is the moment of inertia when the shape is held fixed (bodies can only rotate rigidly):

$$
I_{\alpha\beta} = \sum_{i=1}^3 m_i \left( |\mathbf{r}_i|^2 \delta_{\alpha\beta} - r_i^\alpha r_i^\beta \right)
$$

where $\mathbf{r}_i$ are positions in the barycentric frame.

**Physical Meaning**: This is the resistance to rotation when bodies are "locked" at fixed relative positions.

### Implementation Strategy

```python
# File: src/python/geometry/locked_inertia.py

import numpy as np
from dataclasses import dataclass
from typing import Optional

from ..coordinates.cartesian import CartesianState
from ..coordinates.base import Masses


@dataclass(frozen=True)
class InertiaTensor:
    """
    3×3 inertia tensor in barycentric frame.

    Attributes:
        components: Symmetric 3×3 matrix I_αβ
        configuration: The CartesianState it corresponds to
    """
    components: np.ndarray  # (3, 3) symmetric
    configuration: CartesianState

    def __post_init__(self):
        """Validate symmetry"""
        assert self.components.shape == (3, 3), "Must be 3×3"
        assert np.allclose(self.components, self.components.T), "Must be symmetric"

    @property
    def eigenvalues(self) -> np.ndarray:
        """Principal moments of inertia"""
        return np.linalg.eigvalsh(self.components)

    @property
    def eigenvectors(self) -> np.ndarray:
        """Principal axes"""
        eigenvals, eigenvecs = np.linalg.eigh(self.components)
        return eigenvecs

    @property
    def trace(self) -> float:
        """Tr(I) = sum of diagonal elements"""
        return np.trace(self.components)

    def inverse(self) -> np.ndarray:
        """I^{-1} for computing angular velocities"""
        return np.linalg.inv(self.components)

    def angular_velocity_from_momentum(self, L: np.ndarray) -> np.ndarray:
        """
        Compute ω from L via L = I ω.

        Args:
            L: Angular momentum vector (3,)

        Returns:
            ω: Angular velocity vector (3,)
        """
        return self.inverse() @ L


def compute_locked_inertia_tensor(
    state: CartesianState,
    masses: Masses,
    precision: str = 'double'
) -> InertiaTensor:
    """
    Compute locked inertia tensor I_αβ for a configuration.

    Formula:
        I_αβ = Σᵢ mᵢ (|rᵢ|² δ_αβ - rᵢ^α rᵢ^β)

    This is computed in the barycentric frame (state should already be
    in barycentric coordinates from Task 2.1.1 reduction).

    Args:
        state: Cartesian state (must be barycentric)
        masses: Body masses
        precision: 'double' or 'quad' for high precision

    Returns:
        InertiaTensor object

    Raises:
        AssertionError: If state is not barycentric
    """
    # Verify barycentric (center of mass at origin)
    m = np.array([masses.m1, masses.m2, masses.m3])
    com = np.sum(state.positions * m[:, np.newaxis], axis=0) / masses.total

    assert np.linalg.norm(com) < 1e-14, "State must be barycentric"

    # Initialize inertia tensor
    if precision == 'quad':
        # Use quad-precision if needed (via mpmath or similar)
        I = np.zeros((3, 3), dtype=np.float128)
    else:
        I = np.zeros((3, 3))

    # Compute tensor components
    for i in range(3):
        r_i = state.positions[i]  # Position vector
        m_i = m[i]                 # Mass

        r_squared = np.dot(r_i, r_i)

        # Diagonal terms: I_αα = Σ mᵢ |rᵢ|² - Σ mᵢ (rᵢ^α)²
        for alpha in range(3):
            I[alpha, alpha] += m_i * (r_squared - r_i[alpha]**2)

        # Off-diagonal: I_αβ = -Σ mᵢ rᵢ^α rᵢ^β
        for alpha in range(3):
            for beta in range(alpha + 1, 3):
                I[alpha, beta] -= m_i * r_i[alpha] * r_i[beta]
                I[beta, alpha] = I[alpha, beta]  # Symmetry

    return InertiaTensor(
        components=I,
        configuration=state
    )
```

### Alternative Formula (Outer Product Form)

For numerical efficiency, we can use:

$$
I = \sum_{i=1}^3 m_i \left( |\mathbf{r}_i|^2 \mathbb{I}_3 - \mathbf{r}_i \otimes \mathbf{r}_i \right)
$$

```python
def compute_locked_inertia_tensor_vectorized(
    state: CartesianState,
    masses: Masses
) -> InertiaTensor:
    """
    Vectorized computation (faster for batch operations).

    Uses outer product formulation.
    """
    m = np.array([masses.m1, masses.m2, masses.m3])
    r = state.positions  # (3, 3) array

    # Compute |rᵢ|² for each body
    r_squared = np.sum(r**2, axis=1)  # (3,)

    # Initialize tensor
    I = np.zeros((3, 3))

    # Vectorized accumulation
    for i in range(3):
        I += m[i] * (r_squared[i] * np.eye(3) - np.outer(r[i], r[i]))

    return InertiaTensor(components=I, configuration=state)
```

### Special Cases and Validation

#### Test Case 1: Collinear Configuration

For three bodies on a line (e.g., x-axis), the inertia tensor should be diagonal with one zero eigenvalue (rotation about the line has no inertia):

```python
def test_collinear_inertia():
    """Test that collinear config has one zero eigenvalue."""
    # Place bodies on x-axis
    positions = np.array([
        [-1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0]
    ])

    masses = Masses(1.0, 1.0, 1.0)

    # Enforce barycenter
    from ..coordinates.cartesian import enforce_barycenter
    state = CartesianState(positions, np.zeros((3, 3)), dimension=3)
    state = enforce_barycenter(state, masses)

    I_tensor = compute_locked_inertia_tensor(state, masses)
    eigenvals = I_tensor.eigenvalues

    # One eigenvalue should be zero (or very small)
    min_eigenval = np.min(np.abs(eigenvals))
    assert min_eigenval < 1e-14, "Collinear should have zero eigenvalue"
```

#### Test Case 2: Equilateral Triangle

For an equilateral triangle in the xy-plane, the inertia tensor should have:
- $I_{zz}$ largest (rotation about z-axis)
- $I_{xx} = I_{yy}$ (symmetry)
- Off-diagonal terms zero (principal axes align with body frame)

```python
def test_equilateral_inertia():
    """Test equilateral triangle inertia properties."""
    R = 1.0
    angles = np.array([0, 2*np.pi/3, 4*np.pi/3])

    positions = R * np.column_stack([
        np.cos(angles),
        np.sin(angles),
        np.zeros(3)
    ])

    masses = Masses(1.0, 1.0, 1.0)
    state = CartesianState(positions, np.zeros((3, 3)), dimension=2)
    state = enforce_barycenter(state, masses)

    I_tensor = compute_locked_inertia_tensor(state, masses)
    I = I_tensor.components

    # Check symmetry: I_xx = I_yy
    assert np.abs(I[0, 0] - I[1, 1]) < 1e-14

    # Check I_zz > I_xx (planar config)
    assert I[2, 2] > I[0, 0]

    # Check off-diagonal small (approx principal axes)
    off_diag = np.abs(I - np.diag(np.diag(I)))
    assert np.max(off_diag) < 1e-12
```

#### Test Case 3: Scaling Property

Inertia scales as $I \sim m r^2$. Scaling all distances by $\lambda$ should scale $I$ by $\lambda^2$:

```python
def test_inertia_scaling():
    """Test I(λr) = λ² I(r)."""
    positions = np.random.randn(3, 3)
    masses = Masses(1.0, 1.5, 2.0)

    state1 = CartesianState(positions, np.zeros((3, 3)), dimension=3)
    state1 = enforce_barycenter(state1, masses)

    I1 = compute_locked_inertia_tensor(state1, masses)

    # Scale by λ = 2
    lambda_scale = 2.0
    state2 = CartesianState(lambda_scale * positions, np.zeros((3, 3)), dimension=3)
    state2 = enforce_barycenter(state2, masses)

    I2 = compute_locked_inertia_tensor(state2, masses)

    # Should have I2 = λ² I1
    assert np.allclose(I2.components, lambda_scale**2 * I1.components)
```

---

## A2: Shape Space Vector Field Lifts

### The Lifting Problem

**Question**: Given a tangent vector $v = (\delta r_{12}, \delta r_{23}, \delta r_{31})$ in shape space, what angular velocity $\omega$ does it induce?

**Answer**: We need to "lift" $v$ to the full phase space and compute the corresponding rotation.

### Geometric Picture

```
Full Phase Space (Cartesian)
    ↓ [Reduction]
Shape Space
    ↑ [Lift - what we're computing]
Tangent Space TS (shape velocities)
```

The lift is not unique—we choose the "horizontal lift" that preserves angular momentum.

### Mathematical Formulation

Given shape coordinates $s = (r_{12}, r_{23}, r_{31})$ and a shape velocity $\dot{s} = (\dot{r}_{12}, \dot{r}_{23}, \dot{r}_{31})$:

1. **Reconstruct Cartesian**: Convert $(s, \dot{s})$ to Cartesian $(r_i, \dot{r}_i)$ (non-unique due to gauge freedom)
2. **Compute Angular Momentum**: $\mathbf{L} = \sum m_i \mathbf{r}_i \times \dot{\mathbf{r}}_i$
3. **Extract Rotation**: $\omega = I^{-1} \mathbf{L}$

**Complication**: Step 1 is ambiguous (many Cartesian configs have same shape). We pick a canonical choice (orientation convention from Task 2.1.1).

### Implementation

```python
# File: src/python/geometry/shape_lifts.py

import numpy as np
from typing import Tuple, Optional

from ..coordinates.shape_space import ShapeSpaceState
from ..coordinates.cartesian import CartesianState
from ..coordinates.base import Masses
from .locked_inertia import compute_locked_inertia_tensor


class ShapeSpaceVectorFieldLift:
    """
    Lifts tangent vectors from shape space to angular velocities.

    This class handles the ambiguity in lift by fixing a canonical
    orientation (e.g., body 1-2 axis along x-axis).
    """

    def __init__(
        self,
        masses: Masses,
        orientation_convention: str = 'align_12_x_axis'
    ):
        """
        Initialize lifter.

        Args:
            masses: Body masses
            orientation_convention: How to fix orientation gauge
                - 'align_12_x_axis': r₁₂ along positive x-axis
                - 'align_principal_axes': Diagonalize inertia tensor
        """
        self.masses = masses
        self.orientation_convention = orientation_convention

    def lift_to_angular_velocity(
        self,
        shape_state: ShapeSpaceState,
        shape_velocity: np.ndarray
    ) -> np.ndarray:
        """
        Lift shape velocity to angular velocity.

        Args:
            shape_state: Current point in shape space
            shape_velocity: Tangent vector δs = (δr₁₂, δr₂₃, δr₃₁)

        Returns:
            ω: Angular velocity vector (3,)
        """
        # Step 1: Convert shape to canonical Cartesian
        cart_state = self._shape_to_cartesian_canonical(shape_state)

        # Step 2: Compute derivative of positions w.r.t. shape
        # For small δs, how do Cartesian positions change?
        dri_ds = self._compute_position_jacobian(shape_state)  # (9, 3)

        # Step 3: Induced Cartesian velocities
        # δrᵢ = (∂rᵢ/∂s) δs
        cart_velocities = (dri_ds @ shape_velocity).reshape(3, 3)

        # Step 4: Compute angular momentum from these velocities
        L = self._compute_angular_momentum(cart_state.positions, cart_velocities)

        # Step 5: Convert L to ω via I ω = L
        I_tensor = compute_locked_inertia_tensor(cart_state, self.masses)
        omega = I_tensor.angular_velocity_from_momentum(L)

        return omega

    def _shape_to_cartesian_canonical(
        self,
        shape_state: ShapeSpaceState
    ) -> CartesianState:
        """
        Convert shape to Cartesian with canonical orientation.

        For planar case with 'align_12_x_axis':
            - Place r₁₂ along positive x-axis
            - Choose r₃ position to match r₂₃, r₃₁
        """
        if self.orientation_convention == 'align_12_x_axis':
            return self._align_12_x_axis(shape_state)
        else:
            raise NotImplementedError(f"Convention {self.orientation_convention}")

    def _align_12_x_axis(self, shape_state: ShapeSpaceState) -> CartesianState:
        """
        Canonical choice: r₁₂ = (r₁₂, 0, 0).

        This fixes the SO(2) gauge freedom in the plane.
        """
        r12, r23, r31 = shape_state.r12, shape_state.r23, shape_state.r31

        # Triangle inequality check
        assert r12 + r23 > r31 and r23 + r31 > r12 and r31 + r12 > r23

        # Place body 1 and 2 on x-axis
        # Use barycentric: m₁ r₁ + m₂ r₂ + m₃ r₃ = 0

        # Simplified for equal masses (generalize later):
        # r₁ = (r₁₂/2, 0, 0)
        # r₂ = (-r₁₂/2, 0, 0)
        # r₃ determined by r₂₃ and r₃₁

        m1, m2, m3 = self.masses.m1, self.masses.m2, self.masses.m3
        m_total = self.masses.total

        # Parameterize: place r₁ at (x₁, 0, 0), r₂ at (x₂, 0, 0)
        # Constraint: x₁ - x₂ = r₁₂ and m₁ x₁ + m₂ x₂ + m₃ x₃ = 0

        # Solve linear system (implementation details)
        # ...

        positions = self._solve_triangle_positions(r12, r23, r31, self.masses)

        return CartesianState(
            positions=positions,
            velocities=np.zeros((3, 3)),
            dimension=2  # Planar
        )

    def _compute_position_jacobian(
        self,
        shape_state: ShapeSpaceState
    ) -> np.ndarray:
        """
        Compute Jacobian ∂rᵢ/∂s.

        Returns:
            (9, 3) matrix where columns are ∂rᵢ/∂r₁₂, ∂rᵢ/∂r₂₃, ∂rᵢ/∂r₃₁
        """
        # Use finite differences for now (can derive analytically later)
        epsilon = 1e-8
        n_shape_coords = 3
        n_cart_coords = 9  # 3 bodies × 3 components

        jacobian = np.zeros((n_cart_coords, n_shape_coords))

        for j in range(n_shape_coords):
            # Perturb j-th shape coordinate
            shape_plus = self._perturb_shape(shape_state, j, epsilon)
            shape_minus = self._perturb_shape(shape_state, j, -epsilon)

            cart_plus = self._shape_to_cartesian_canonical(shape_plus)
            cart_minus = self._shape_to_cartesian_canonical(shape_minus)

            # Central difference
            dr_ds_j = (cart_plus.positions - cart_minus.positions).ravel() / (2 * epsilon)
            jacobian[:, j] = dr_ds_j

        return jacobian

    def _compute_angular_momentum(
        self,
        positions: np.ndarray,
        velocities: np.ndarray
    ) -> np.ndarray:
        """
        Compute L = Σ mᵢ rᵢ × vᵢ.

        Args:
            positions: (3, 3) array
            velocities: (3, 3) array

        Returns:
            L: Angular momentum vector (3,)
        """
        m = np.array([self.masses.m1, self.masses.m2, self.masses.m3])
        L = np.zeros(3)

        for i in range(3):
            L += m[i] * np.cross(positions[i], velocities[i])

        return L
```

### Validation: Gauge Independence

The angular velocity $\omega$ should be independent of the orientation gauge choice:

```python
def test_gauge_independence():
    """
    Test that ω is independent of orientation convention.

    Try two different conventions:
    1. Align r₁₂ with x-axis
    2. Align r₂₃ with x-axis

    Should get same ω (up to coordinate rotation).
    """
    shape_state = ShapeSpaceState(r12=1.0, r23=1.2, r31=1.4, L=1.0)
    shape_velocity = np.array([0.1, -0.05, 0.02])  # Arbitrary

    masses = Masses(1.0, 1.0, 1.0)

    # Convention 1
    lifter1 = ShapeSpaceVectorFieldLift(masses, 'align_12_x_axis')
    omega1 = lifter1.lift_to_angular_velocity(shape_state, shape_velocity)

    # Convention 2
    lifter2 = ShapeSpaceVectorFieldLift(masses, 'align_23_x_axis')
    omega2 = lifter2.lift_to_angular_velocity(shape_state, shape_velocity)

    # Magnitudes should agree
    assert np.abs(np.linalg.norm(omega1) - np.linalg.norm(omega2)) < 1e-12
```

---

## A3: Connection Coefficient Computation

### Algorithm

Now we can compute the connection coefficients:

$$
\mathcal{A}_{r_{ij}} = \mathbf{L} \cdot \omega_{r_{ij}}
$$

where $\omega_{r_{ij}}$ is the angular velocity induced by $\delta r_{ij} = 1$ (unit tangent vector).

```python
# File: src/python/geometry/connection.py

import numpy as np
from dataclasses import dataclass
from typing import Callable, Optional

from ..coordinates.shape_space import ShapeSpaceState
from ..coordinates.base import Masses
from .shape_lifts import ShapeSpaceVectorFieldLift


@dataclass(frozen=True)
class ConnectionForm:
    """
    Mechanical connection one-form on shape space.

    Represents A = A_i dx^i where x^i are shape coordinates.

    Attributes:
        coefficients: Components [A_r12, A_r23, A_r31]
        coordinate_names: ['r12', 'r23', 'r31']
        base_point: Shape space state where evaluated
        angular_momentum: L (conserved angular momentum)
    """
    coefficients: np.ndarray  # (3,)
    coordinate_names: list[str]
    base_point: ShapeSpaceState
    angular_momentum: float

    def evaluate(self, tangent_vector: np.ndarray) -> float:
        """
        Evaluate A(v) for tangent vector v.

        Args:
            tangent_vector: (δr₁₂, δr₂₃, δr₃₁)

        Returns:
            A(v) = A_i v^i (scalar)
        """
        return np.dot(self.coefficients, tangent_vector)

    def magnitude(self) -> float:
        """‖A‖ = √(A_i A_i)"""
        return np.linalg.norm(self.coefficients)


def compute_connection_form(
    shape_state: ShapeSpaceState,
    masses: Masses,
    orientation_convention: str = 'align_12_x_axis'
) -> ConnectionForm:
    """
    Compute connection one-form A at a point in shape space.

    Algorithm:
        1. For each shape coordinate direction i:
           a. Lift unit vector e_i to angular velocity ω_i
           b. Compute A_i = L · ω_i
        2. Return A = A_i dx^i

    Args:
        shape_state: Point in shape space
        masses: Body masses
        orientation_convention: How to fix gauge

    Returns:
        ConnectionForm object
    """
    lifter = ShapeSpaceVectorFieldLift(masses, orientation_convention)

    shape_coords = ['r12', 'r23', 'r31']
    n_coords = len(shape_coords)

    coefficients = np.zeros(n_coords)
    L_magnitude = shape_state.L  # Angular momentum magnitude

    # For each coordinate direction
    for i in range(n_coords):
        # Unit tangent vector in direction i
        e_i = np.zeros(n_coords)
        e_i[i] = 1.0

        # Lift to angular velocity
        omega_i = lifter.lift_to_angular_velocity(shape_state, e_i)

        # Connection coefficient: A_i = L · ω_i
        # (Assuming L is in z-direction for planar case)
        L_vector = np.array([0, 0, L_magnitude])  # Planar: L in z-direction

        coefficients[i] = np.dot(L_vector, omega_i)

    return ConnectionForm(
        coefficients=coefficients,
        coordinate_names=shape_coords,
        base_point=shape_state,
        angular_momentum=L_magnitude
    )
```

### Optimization: Batch Computation

For computing connection at many points (e.g., for visualization), use vectorization:

```python
def compute_connection_field(
    shape_states: list[ShapeSpaceState],
    masses: Masses,
    orientation_convention: str = 'align_12_x_axis'
) -> list[ConnectionForm]:
    """
    Compute connection at multiple points (vectorized where possible).

    Args:
        shape_states: List of N shape space points
        masses: Body masses
        orientation_convention: Gauge fixing

    Returns:
        List of N ConnectionForm objects
    """
    # Pre-compute lifter (shared)
    lifter = ShapeSpaceVectorFieldLift(masses, orientation_convention)

    connections = []

    for state in shape_states:
        conn = compute_connection_form_impl(state, lifter)
        connections.append(conn)

    return connections


def compute_connection_form_impl(
    shape_state: ShapeSpaceState,
    lifter: ShapeSpaceVectorFieldLift
) -> ConnectionForm:
    """
    Internal implementation using pre-constructed lifter.

    Avoids re-creating lifter object for each point.
    """
    # Same as compute_connection_form but reuses lifter
    # (Implementation details)
    pass
```

---

## A4: Gauge Transformations

### What is a Gauge Transformation?

A **gauge transformation** is a change of orientation-fixing convention. Different conventions give different connection coefficients, but physical quantities (like the curvature) are gauge-invariant.

### Transformation Law

Under a gauge transformation $g: S \to SO(2)$ (for planar case):

$$
\mathcal{A}' = \mathcal{A} + dg
$$

where $dg$ is the differential of the gauge function.

**Example**: If we rotate the orientation by angle $\theta(s)$, then:

$$
\mathcal{A}'_i = \mathcal{A}_i + \frac{\partial \theta}{\partial s^i}
$$

### Implementation

```python
def gauge_transform_connection(
    connection: ConnectionForm,
    gauge_function: Callable[[ShapeSpaceState], float],
    epsilon: float = 1e-8
) -> ConnectionForm:
    """
    Apply gauge transformation A' = A + dα.

    Args:
        connection: Original connection
        gauge_function: α(s) - gauge parameter
        epsilon: For numerical derivative

    Returns:
        Transformed connection
    """
    state = connection.base_point

    # Compute derivative of gauge function
    n_coords = len(connection.coefficients)
    d_gauge = np.zeros(n_coords)

    for i in range(n_coords):
        state_plus = perturb_shape_coordinate(state, i, epsilon)
        state_minus = perturb_shape_coordinate(state, i, -epsilon)

        alpha_plus = gauge_function(state_plus)
        alpha_minus = gauge_function(state_minus)

        d_gauge[i] = (alpha_plus - alpha_minus) / (2 * epsilon)

    # Transform: A' = A + dα
    new_coefficients = connection.coefficients + d_gauge

    return ConnectionForm(
        coefficients=new_coefficients,
        coordinate_names=connection.coordinate_names,
        base_point=state,
        angular_momentum=connection.angular_momentum
    )
```

### Validation: Gauge-Invariant Quantities

The **curvature** $\mathcal{F} = d\mathcal{A}$ is gauge-invariant:

$$
\mathcal{F}' = d\mathcal{A}' = d(\mathcal{A} + d\alpha) = d\mathcal{A} + d^2\alpha = d\mathcal{A} = \mathcal{F}
$$

(since $d^2 = 0$)

```python
def test_curvature_gauge_invariance():
    """
    Test that curvature is unchanged under gauge transformation.
    """
    from .curvature import compute_curvature_form

    shape_state = ShapeSpaceState(r12=1.0, r23=1.1, r31=1.05, L=1.0)
    masses = Masses(1.0, 1.0, 1.0)

    # Compute curvature with convention 1
    conn1 = compute_connection_form(shape_state, masses, 'align_12_x_axis')
    F1 = compute_curvature_form(conn1, masses)

    # Apply gauge transformation
    gauge_func = lambda s: 0.1 * s.r12  # Arbitrary gauge
    conn2 = gauge_transform_connection(conn1, gauge_func)

    # Compute curvature with transformed connection
    F2 = compute_curvature_form(conn2, masses)

    # Curvatures should match
    assert np.allclose(F1.matrix, F2.matrix, atol=1e-12)
```

---

## A5: Validation and Testing

### Test Suite Structure

```python
# tests/geometry/test_connection.py

import pytest
import numpy as np

from src.python.coordinates.shape_space import ShapeSpaceState
from src.python.coordinates.base import Masses
from src.python.geometry.connection import compute_connection_form


class TestConnectionForm:
    """Test suite for connection computation."""

    @pytest.fixture
    def equal_mass_system(self):
        """Equal masses (simplest case)."""
        return Masses(1.0, 1.0, 1.0)

    @pytest.fixture
    def equilateral_triangle(self):
        """Equilateral triangle shape."""
        side_length = 1.0
        return ShapeSpaceState(
            r12=side_length,
            r23=side_length,
            r31=side_length,
            L=1.0
        )

    def test_connection_coefficients_real(self, equal_mass_system, equilateral_triangle):
        """Connection coefficients should be real."""
        conn = compute_connection_form(equilateral_triangle, equal_mass_system)

        assert np.all(np.isreal(conn.coefficients))
        assert np.all(np.isfinite(conn.coefficients))

    def test_equilateral_symmetry(self, equal_mass_system):
        """
        For equilateral triangle with equal masses, connection should
        be symmetric under permutations.
        """
        side = 1.0
        state = ShapeSpaceState(r12=side, r23=side, r31=side, L=1.0)

        conn = compute_connection_form(state, equal_mass_system)

        # All coefficients should be equal (by symmetry)
        A_r12, A_r23, A_r31 = conn.coefficients

        assert np.abs(A_r12 - A_r23) < 1e-12
        assert np.abs(A_r23 - A_r31) < 1e-12

    def test_two_body_limit(self):
        """
        As m₃ → 0, connection should reduce to two-body formula.
        """
        m3_values = [0.1, 0.01, 0.001, 0.0001]

        state = ShapeSpaceState(r12=1.0, r23=1.5, r31=1.5, L=1.0)

        connections = []
        for m3 in m3_values:
            masses = Masses(1.0, 1.0, m3)
            conn = compute_connection_form(state, masses)
            connections.append(conn.magnitude())

        # Should converge (test with regression)
        # For true two-body, connection has specific form
        # (Implementation: compare with analytical formula)

    def test_dimensional_analysis(self, equal_mass_system, equilateral_triangle):
        """
        Connection has dimensions [angular momentum / length].

        Scaling lengths by λ should scale A by 1/λ.
        """
        L = 1.0

        # Original
        state1 = ShapeSpaceState(r12=1.0, r23=1.0, r31=1.0, L=L)
        conn1 = compute_connection_form(state1, equal_mass_system)

        # Scaled by λ = 2
        lambda_scale = 2.0
        state2 = ShapeSpaceState(
            r12=lambda_scale * 1.0,
            r23=lambda_scale * 1.0,
            r31=lambda_scale * 1.0,
            L=L
        )
        conn2 = compute_connection_form(state2, equal_mass_system)

        # Should have A₂ = A₁ / λ
        expected = conn1.coefficients / lambda_scale
        assert np.allclose(conn2.coefficients, expected, rtol=1e-10)

    def test_performance_benchmark(self, equal_mass_system):
        """
        Connection evaluation should be fast: <100 μs per point.
        """
        import time

        state = ShapeSpaceState(r12=1.0, r23=1.1, r31=1.05, L=1.0)

        n_trials = 1000

        start = time.perf_counter()
        for _ in range(n_trials):
            conn = compute_connection_form(state, equal_mass_system)
        end = time.perf_counter()

        avg_time = (end - start) / n_trials

        print(f"Average connection computation time: {avg_time * 1e6:.2f} μs")

        assert avg_time < 100e-6, "Should be faster than 100 μs"
```

---

## Implementation Details

### Directory Structure

```
src/python/geometry/
├── __init__.py
├── locked_inertia.py      # A1: Inertia tensor
├── shape_lifts.py          # A2: Vector field lifts
├── connection.py           # A3: Connection form
└── gauge.py                # A4: Gauge transformations
```

### Dependencies

- Task 2.1.1: `coordinates.cartesian`, `coordinates.shape_space`, `coordinates.base`
- NumPy, SciPy
- Optional: SymPy for symbolic validation

---

## Performance Optimization

### Caching Strategy

```python
from functools import lru_cache

@lru_cache(maxsize=1024)
def compute_connection_cached(state_hash, masses_hash):
    """Cached connection computation."""
    # Reconstruct objects from hashes
    state = ShapeSpaceState.from_hash(state_hash)
    masses = Masses.from_hash(masses_hash)

    return compute_connection_form(state, masses)
```

### Profiling Results (Target)

```
Function                        Time (μs)  % Total
---------------------------------------------
compute_connection_form         95         100%
  ├─ locked_inertia_tensor      25         26%
  ├─ shape_to_cartesian         15         16%
  ├─ lift_to_angular_velocity   45         47%
  └─ dot products               10         11%
```

---

## Integration Guide

### Using with Task 2.1.1

```python
from coordinates.shape_space import ShapeSpaceState
from coordinates.base import Masses
from geometry.connection import compute_connection_form

# Create shape state (from Task 2.1.1)
shape_state = ShapeSpaceState(r12=1.0, r23=1.1, r31=1.05, L=1.0)
masses = Masses(1.0, 1.0, 1.0)

# Compute connection
connection = compute_connection_form(shape_state, masses)

print(f"Connection coefficients: {connection.coefficients}")
print(f"Magnitude: {connection.magnitude():.6f}")
```

### Using with Part B (Curvature)

```python
from geometry.curvature import compute_curvature_form

# Compute curvature from connection
curvature = compute_curvature_form(connection, masses)

if curvature.magnitude() > 1e-10:
    print("Non-flat connection → non-integrable!")
```

---

## Success Criteria

### Part A Complete When:

- [ ] Locked inertia tensor implemented and tested
- [ ] Shape space lifts functional
- [ ] Connection coefficients computed correctly
- [ ] All validation tests pass:
  - [ ] Collinear configuration
  - [ ] Equilateral symmetry
  - [ ] Two-body limit
  - [ ] Dimensional scaling
  - [ ] Gauge invariance (curvature)
- [ ] Performance target met (<100 μs)
- [ ] Documentation complete
- [ ] Integration with Task 2.1.1 verified

**Ready to proceed to Part B** when all boxes checked.

---

**Document Version**: 1.0
**Created**: 2025-11-13
**Status**: Design Complete → Ready for Implementation
**Estimated Implementation Time**: 3 days
**Next**: Part B (Curvature Computation)
