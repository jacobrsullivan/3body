# Task 2.1.1 Part A: Coordinate Systems - Detailed Implementation Design

**Task**: WP 2.1.1 - Coordinate Systems and Reduction
**Part**: A - Coordinate System Implementations
**Status**: Design Phase
**Estimated Duration**: 4 days
**Dependencies**: WP1 Complete

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture & Design Principles](#architecture--design-principles)
3. [A1: Cartesian Coordinate System](#a1-cartesian-coordinate-system)
4. [A2: Jacobi Coordinate System](#a2-jacobi-coordinate-system)
5. [A3: Shape Space Coordinate System](#a3-shape-space-coordinate-system)
6. [Integration & Testing Strategy](#integration--testing-strategy)
7. [Performance Considerations](#performance-considerations)
8. [Implementation Checklist](#implementation-checklist)

---

## Overview

### Purpose

Part A implements the foundational coordinate system infrastructure for the general three-body problem (3BP). This forms the basis for all subsequent geometric reduction and shape space analysis in WP2.

### Scope

We implement three coordinate representations:
1. **Cartesian**: Standard inertial frame coordinates (baseline representation)
2. **Jacobi**: Hierarchical mass-weighted coordinates (decouples center-of-mass)
3. **Shape Space**: Gauge-invariant coordinates on the quotient by translations/rotations

### Key Design Goals

- **High Precision**: Support both double and quad-double (QD) arithmetic
- **Type Safety**: Strong typing with validation at boundaries
- **Performance**: Vectorized operations for batch transformations
- **Extensibility**: Easy to add new coordinate systems or dimensions (2D/3D)
- **Testability**: Clear separation of concerns, comprehensive unit tests

---

## Architecture & Design Principles

### Module Structure

```
src/python/coordinates/
├── __init__.py              # Package exports
├── base.py                  # Abstract base classes
├── cartesian.py             # A1: Cartesian implementation
├── jacobi.py                # A2: Jacobi implementation
├── shape_space.py           # A3: Shape space implementation
├── transforms.py            # Coordinate transformation registry
└── validation.py            # Conservation law checkers

tests/
├── test_cartesian.py
├── test_jacobi.py
├── test_shape_space.py
└── test_transforms.py
```

### Design Patterns

1. **Abstract Base Class**: `CoordinateSystem` defines the interface
2. **Factory Pattern**: `CoordinateTransform.register()` for transformation registry
3. **Strategy Pattern**: Pluggable precision backends (double vs QD)
4. **Dataclass Pattern**: Immutable state representations with validation

### Core Abstractions

```python
# Base class for all coordinate systems
class CoordinateSystem(ABC):
    """Abstract base for 3BP coordinate representations"""

    @abstractmethod
    def validate(self) -> bool:
        """Check if state satisfies coordinate constraints"""
        pass

    @abstractmethod
    def to_cartesian(self) -> CartesianState:
        """Transform to Cartesian coordinates"""
        pass

    @abstractmethod
    def compute_energy(self, masses: Masses) -> float:
        """Compute total energy in this coordinate system"""
        pass

    @abstractmethod
    def compute_angular_momentum(self, masses: Masses) -> np.ndarray:
        """Compute angular momentum vector"""
        pass
```

### Type Definitions

```python
from typing import TypeAlias, Literal
import numpy.typing as npt

# Precision backends
Precision: TypeAlias = Literal['double', 'quad']

# Array types
Vec3: TypeAlias = npt.NDArray[np.float64]  # 3D vector
Vec3QD: TypeAlias = npt.NDArray['qd_real']  # Quad-double 3D vector

# Mass specification
@dataclass(frozen=True)
class Masses:
    """Three-body mass parameters"""
    m1: float
    m2: float
    m3: float

    @property
    def total(self) -> float:
        return self.m1 + self.m2 + self.m3

    @property
    def mu12(self) -> float:
        """Reduced mass of bodies 1-2"""
        return self.m1 * self.m2 / (self.m1 + self.m2)

    @property
    def mu3(self) -> float:
        """Hierarchical reduced mass for body 3"""
        return (self.m1 + self.m2) * self.m3 / self.total
```

---

## A1: Cartesian Coordinate System

### Mathematical Specification

**State Space**: $\mathbb{R}^{18}$ (3 positions × 3 components + 3 velocities × 3 components)

**State Vector**:
$$
\mathbf{z}_{\text{cart}} = (\mathbf{r}_1, \mathbf{r}_2, \mathbf{r}_3, \mathbf{v}_1, \mathbf{v}_2, \mathbf{v}_3)
$$

**Constraints** (Barycentric frame):
$$
\sum_{i=1}^3 m_i \mathbf{r}_i = \mathbf{0}, \quad \sum_{i=1}^3 m_i \mathbf{v}_i = \mathbf{0}
$$

**Hamiltonian**:
$$
H = \frac{1}{2}\sum_{i=1}^3 m_i |\mathbf{v}_i|^2 - \sum_{1 \le i < j \le 3} \frac{G m_i m_j}{|\mathbf{r}_i - \mathbf{r}_j|}
$$

### Data Structures

```python
@dataclass(frozen=True)
class CartesianState:
    """
    Cartesian coordinates in barycentric inertial frame.

    Attributes:
        positions: (3, 3) array of positions [m]
                   positions[i] = [x, y, z] for body i
        velocities: (3, 3) array of velocities [m/s]
        dimension: 2 for planar, 3 for spatial
        precision: 'double' or 'quad'
    """
    positions: np.ndarray  # shape (3, 3)
    velocities: np.ndarray  # shape (3, 3)
    dimension: Literal[2, 3] = 3
    precision: Precision = 'double'

    def __post_init__(self):
        """Validate array shapes and types"""
        assert self.positions.shape == (3, 3)
        assert self.velocities.shape == (3, 3)
        if self.dimension == 2:
            # Planar: z-components should be zero
            assert np.allclose(self.positions[:, 2], 0)
            assert np.allclose(self.velocities[:, 2], 0)

    @classmethod
    def from_flat(cls, z: np.ndarray, dimension: int = 3) -> 'CartesianState':
        """
        Construct from flat array [r1x, r1y, r1z, ..., v3z].

        Args:
            z: Flat state vector of length 18 (3D) or 12 (2D)
        """
        n = 3 * dimension  # position components
        positions = z[:n].reshape(3, dimension)
        velocities = z[n:2*n].reshape(3, dimension)

        # Pad to 3D if needed
        if dimension == 2:
            positions = np.column_stack([positions, np.zeros(3)])
            velocities = np.column_stack([velocities, np.zeros(3)])

        return cls(positions, velocities, dimension)

    def to_flat(self) -> np.ndarray:
        """Convert to flat array for integration"""
        if self.dimension == 2:
            pos = self.positions[:, :2].ravel()
            vel = self.velocities[:, :2].ravel()
        else:
            pos = self.positions.ravel()
            vel = self.velocities.ravel()
        return np.concatenate([pos, vel])

    def validate(self) -> bool:
        """Check constraints (should be overridden for barycentric)"""
        return True
```

### Core Functions

#### A1.1: Barycentric Enforcement

```python
def enforce_barycenter(
    state: CartesianState,
    masses: Masses,
    precision: Precision = 'double'
) -> CartesianState:
    """
    Project state onto barycentric constraint surface.

    Ensures:
        sum_i m_i r_i = 0
        sum_i m_i v_i = 0

    Algorithm:
        r_i' = r_i - r_cm
        v_i' = v_i - v_cm

    where r_cm = (sum_i m_i r_i) / M_total
    """
    m = np.array([masses.m1, masses.m2, masses.m3])
    M = masses.total

    # Compute center of mass
    r_cm = np.sum(state.positions * m[:, np.newaxis], axis=0) / M
    v_cm = np.sum(state.velocities * m[:, np.newaxis], axis=0) / M

    # Shift to barycentric frame
    positions_bc = state.positions - r_cm
    velocities_bc = state.velocities - v_cm

    # Verify constraint (should be machine precision)
    check_r = np.sum(positions_bc * m[:, np.newaxis], axis=0)
    check_v = np.sum(velocities_bc * m[:, np.newaxis], axis=0)

    if precision == 'double':
        assert np.linalg.norm(check_r) < 1e-14
        assert np.linalg.norm(check_v) < 1e-14

    return CartesianState(positions_bc, velocities_bc,
                          state.dimension, precision)
```

#### A1.2: Hamiltonian and Equations of Motion

```python
def compute_energy(
    state: CartesianState,
    masses: Masses,
    G: float = 1.0,
    precision: Precision = 'double'
) -> float:
    """
    Compute total energy H = T + V.

    Kinetic energy: T = (1/2) sum_i m_i |v_i|^2
    Potential energy: V = -G sum_{i<j} m_i m_j / |r_i - r_j|
    """
    m = np.array([masses.m1, masses.m2, masses.m3])

    # Kinetic energy
    T = 0.5 * np.sum(m[:, np.newaxis] * state.velocities**2)

    # Potential energy
    V = 0.0
    r = state.positions
    pairs = [(0, 1), (0, 2), (1, 2)]

    for i, j in pairs:
        rij = r[i] - r[j]
        dist = np.linalg.norm(rij)
        if precision == 'quad':
            # Use QD library for distance calculation
            dist = qd_norm(rij)

        # Softened potential to avoid singularities (optional)
        # dist = np.sqrt(dist**2 + softening**2)

        V -= G * m[i] * m[j] / dist

    return T + V


def compute_accelerations(
    positions: np.ndarray,
    masses: Masses,
    G: float = 1.0,
    softening: float = 0.0
) -> np.ndarray:
    """
    Compute gravitational accelerations a_i = sum_{j != i} G m_j (r_j - r_i) / |r_ij|^3

    Args:
        positions: (3, 3) array of positions
        masses: Mass parameters
        G: Gravitational constant
        softening: Softening length (for regularization)

    Returns:
        accelerations: (3, 3) array of accelerations
    """
    m = np.array([masses.m1, masses.m2, masses.m3])
    acc = np.zeros_like(positions)

    for i in range(3):
        for j in range(3):
            if i == j:
                continue

            rij = positions[j] - positions[i]
            dist = np.linalg.norm(rij)

            if softening > 0:
                dist = np.sqrt(dist**2 + softening**2)

            # Acceleration on body i due to body j
            acc[i] += G * m[j] * rij / dist**3

    return acc


def cartesian_rhs(
    t: float,
    z: np.ndarray,
    masses: Masses,
    G: float = 1.0
) -> np.ndarray:
    """
    Right-hand side for Cartesian equations of motion.

    Used by scipy.integrate.solve_ivp and custom integrators.

    Equations:
        dr_i/dt = v_i
        dv_i/dt = a_i = sum_{j != i} G m_j (r_j - r_i) / |r_ij|^3
    """
    n = len(z) // 2
    positions = z[:n].reshape(3, -1)
    velocities = z[n:].reshape(3, -1)

    accelerations = compute_accelerations(positions, masses, G)

    # Return [velocities, accelerations] flattened
    return np.concatenate([velocities.ravel(), accelerations.ravel()])
```

#### A1.3: Conservation Laws

```python
def compute_linear_momentum(
    state: CartesianState,
    masses: Masses
) -> np.ndarray:
    """
    Compute total linear momentum P = sum_i m_i v_i.

    Should be zero in barycentric frame.
    """
    m = np.array([masses.m1, masses.m2, masses.m3])
    return np.sum(m[:, np.newaxis] * state.velocities, axis=0)


def compute_angular_momentum(
    state: CartesianState,
    masses: Masses
) -> np.ndarray:
    """
    Compute total angular momentum L = sum_i r_i × (m_i v_i).

    For planar motion: L = L_z (scalar, out-of-plane component)
    """
    m = np.array([masses.m1, masses.m2, masses.m3])
    L = np.zeros(3)

    for i in range(3):
        L += m[i] * np.cross(state.positions[i], state.velocities[i])

    return L


class ConservationMonitor:
    """Track conservation laws over integration"""

    def __init__(self, state0: CartesianState, masses: Masses):
        self.E0 = compute_energy(state0, masses)
        self.L0 = compute_angular_momentum(state0, masses)
        self.P0 = compute_linear_momentum(state0, masses)

        self.times = []
        self.energy_errors = []
        self.angular_momentum_errors = []
        self.linear_momentum_errors = []

    def record(self, t: float, state: CartesianState, masses: Masses):
        """Record conservation errors at time t"""
        E = compute_energy(state, masses)
        L = compute_angular_momentum(state, masses)
        P = compute_linear_momentum(state, masses)

        self.times.append(t)
        self.energy_errors.append((E - self.E0) / abs(self.E0))
        self.angular_momentum_errors.append(np.linalg.norm(L - self.L0))
        self.linear_momentum_errors.append(np.linalg.norm(P - self.P0))

    def validate(self, tolerance: dict) -> bool:
        """Check if conservation errors are within tolerance"""
        return (
            max(abs(e) for e in self.energy_errors) < tolerance['energy']
            and max(self.angular_momentum_errors) < tolerance['angular_momentum']
            and max(self.linear_momentum_errors) < tolerance['linear_momentum']
        )
```

### Testing Strategy

```python
# tests/test_cartesian.py

class TestCartesianState:
    """Test CartesianState dataclass"""

    def test_construction_from_flat(self):
        """Test flat array → CartesianState"""
        z = np.random.randn(18)
        state = CartesianState.from_flat(z, dimension=3)
        z_reconstructed = state.to_flat()
        np.testing.assert_allclose(z, z_reconstructed)

    def test_planar_constraint(self):
        """Planar states should have z=0"""
        z = np.random.randn(12)
        state = CartesianState.from_flat(z, dimension=2)
        assert np.allclose(state.positions[:, 2], 0)
        assert np.allclose(state.velocities[:, 2], 0)


class TestBarycentricEnforcement:
    """Test barycentric frame projection"""

    def test_arbitrary_state_projection(self):
        """Arbitrary state → barycentric frame"""
        # Random state (not in barycentric frame)
        state = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        masses = Masses(1.0, 1.0, 1.0)

        # Enforce barycenter
        state_bc = enforce_barycenter(state, masses)

        # Check constraints
        P = compute_linear_momentum(state_bc, masses)
        assert np.linalg.norm(P) < 1e-14

        m = np.array([masses.m1, masses.m2, masses.m3])
        r_cm = np.sum(state_bc.positions * m[:, np.newaxis], axis=0)
        assert np.linalg.norm(r_cm) < 1e-14


class TestConservationLaws:
    """Test energy, momentum conservation"""

    def test_energy_conservation_lagrange_equilibrium(self):
        """Lagrange equilateral triangle conserves energy exactly"""
        # Set up equilateral triangle rotating with angular velocity ω
        R = 1.0  # radius
        omega = np.sqrt(3.0)  # angular velocity for equal masses
        masses = Masses(1.0, 1.0, 1.0)

        # Initial positions (equilateral triangle)
        angles = np.array([0, 2*np.pi/3, 4*np.pi/3])
        positions = R * np.column_stack([
            np.cos(angles), np.sin(angles), np.zeros(3)
        ])

        # Initial velocities (circular motion)
        velocities = R * omega * np.column_stack([
            -np.sin(angles), np.cos(angles), np.zeros(3)
        ])

        state0 = CartesianState(positions, velocities, dimension=2)
        state0 = enforce_barycenter(state0, masses)

        E0 = compute_energy(state0, masses)

        # Integrate for one period
        T = 2 * np.pi / omega
        # ... (integration code) ...

        E_final = compute_energy(state_final, masses)

        # Energy should be conserved to integrator tolerance
        assert abs(E_final - E0) / abs(E0) < 1e-12
```

---

## A2: Jacobi Coordinate System

### Mathematical Specification

**Jacobi Coordinates** (3-body hierarchical):
$$
\begin{aligned}
\mathbf{r}_{J,1} &= \mathbf{r}_1 - \mathbf{r}_2 \\
\mathbf{r}_{J,2} &= \mathbf{r}_3 - \mathbf{r}_{\text{cm},12} \\
\mathbf{r}_{J,3} &= \mathbf{r}_{\text{cm}} = \frac{m_1 \mathbf{r}_1 + m_2 \mathbf{r}_2 + m_3 \mathbf{r}_3}{M}
\end{aligned}
$$

**Conjugate Momenta**:
$$
\begin{aligned}
\mathbf{p}_{J,1} &= \mu_{12} \dot{\mathbf{r}}_{J,1} \\
\mathbf{p}_{J,2} &= \mu_3 \dot{\mathbf{r}}_{J,2} \\
\mathbf{p}_{J,3} &= M \dot{\mathbf{r}}_{J,3}
\end{aligned}
$$

**Hamiltonian Decomposition**:
$$
H = H_{\text{internal}}(\mathbf{r}_{J,1}, \mathbf{r}_{J,2}, \mathbf{p}_{J,1}, \mathbf{p}_{J,2}) + \frac{|\mathbf{p}_{J,3}|^2}{2M}
$$

### Data Structures

```python
@dataclass(frozen=True)
class JacobiState:
    """
    Jacobi coordinates (hierarchical mass-weighted).

    Attributes:
        r1: Relative position of bodies 1-2 (3D vector)
        r2: Position of body 3 relative to cm of 1-2 (3D vector)
        r_cm: Barycenter position (3D vector) - decoupled
        p1: Conjugate momentum to r1 (mass-weighted)
        p2: Conjugate momentum to r2 (mass-weighted)
        p_cm: Conjugate momentum to r_cm (total linear momentum)
        dimension: 2 or 3
    """
    r1: np.ndarray  # shape (3,)
    r2: np.ndarray  # shape (3,)
    r_cm: np.ndarray  # shape (3,)
    p1: np.ndarray  # shape (3,)
    p2: np.ndarray  # shape (3,)
    p_cm: np.ndarray  # shape (3,)
    dimension: Literal[2, 3] = 3

    @property
    def internal_state(self) -> tuple:
        """Return internal DOF only (excluding center-of-mass)"""
        return (self.r1, self.r2, self.p1, self.p2)

    def validate(self) -> bool:
        """Check that r_cm and p_cm are zero (barycentric frame)"""
        return (np.linalg.norm(self.r_cm) < 1e-14 and
                np.linalg.norm(self.p_cm) < 1e-14)
```

### Core Functions

#### A2.1: Coordinate Transformations

```python
def cartesian_to_jacobi(
    state: CartesianState,
    masses: Masses
) -> JacobiState:
    """
    Transform Cartesian → Jacobi coordinates.

    Transformation:
        r_J1 = r1 - r2
        r_J2 = r3 - (m1*r1 + m2*r2) / (m1 + m2)
        r_cm = (m1*r1 + m2*r2 + m3*r3) / M

        p_J1 = mu12 * (v1 - v2)
        p_J2 = mu3 * (v3 - v_cm12)
        p_cm = M * v_cm
    """
    r = state.positions
    v = state.velocities

    m1, m2, m3 = masses.m1, masses.m2, masses.m3
    M = masses.total
    mu12 = masses.mu12
    mu3 = masses.mu3

    # Center of mass of bodies 1-2
    r_cm12 = (m1 * r[0] + m2 * r[1]) / (m1 + m2)
    v_cm12 = (m1 * v[0] + m2 * v[1]) / (m1 + m2)

    # Barycenter
    r_cm = (m1 * r[0] + m2 * r[1] + m3 * r[2]) / M
    v_cm = (m1 * v[0] + m2 * v[1] + m3 * v[2]) / M

    # Jacobi positions
    r1 = r[0] - r[1]
    r2 = r[2] - r_cm12

    # Jacobi momenta
    p1 = mu12 * (v[0] - v[1])
    p2 = mu3 * (v[2] - v_cm12)
    p_cm = M * v_cm

    return JacobiState(r1, r2, r_cm, p1, p2, p_cm, state.dimension)


def jacobi_to_cartesian(
    state: JacobiState,
    masses: Masses
) -> CartesianState:
    """
    Transform Jacobi → Cartesian coordinates (inverse).

    Inverse transformation:
        r1 = r_cm12 + (m2 / (m1 + m2)) * r_J1
        r2 = r_cm12 - (m1 / (m1 + m2)) * r_J1
        r3 = r_cm12 + r_J2

    where r_cm12 is determined from r_cm and r_J2.
    """
    m1, m2, m3 = masses.m1, masses.m2, masses.m3
    M = masses.total

    # Inverse formulas (solving linear system)
    r_cm12 = state.r_cm - (m3 / M) * state.r2

    r1 = r_cm12 + (m2 / (m1 + m2)) * state.r1
    r2 = r_cm12 - (m1 / (m1 + m2)) * state.r1
    r3 = r_cm12 + state.r2

    # Velocities from momenta
    mu12 = masses.mu12
    mu3 = masses.mu3

    v_J1 = state.p1 / mu12
    v_J2 = state.p2 / mu3
    v_cm = state.p_cm / M

    v_cm12 = v_cm - (m3 / M) * v_J2

    v1 = v_cm12 + (m2 / (m1 + m2)) * v_J1
    v2 = v_cm12 - (m1 / (m1 + m2)) * v_J1
    v3 = v_cm12 + v_J2

    positions = np.array([r1, r2, r3])
    velocities = np.array([v1, v2, v3])

    return CartesianState(positions, velocities, state.dimension)
```

#### A2.2: Jacobi Hamiltonian

```python
def compute_jacobi_hamiltonian(
    state: JacobiState,
    masses: Masses,
    G: float = 1.0
) -> tuple[float, float]:
    """
    Compute Jacobi Hamiltonian = H_internal + H_cm.

    Returns:
        H_internal: Internal dynamics (relative motion)
        H_cm: Center-of-mass kinetic energy (decoupled)
    """
    mu12 = masses.mu12
    mu3 = masses.mu3
    M = masses.total

    # Internal kinetic energy
    T_internal = (np.linalg.norm(state.p1)**2 / (2 * mu12) +
                  np.linalg.norm(state.p2)**2 / (2 * mu3))

    # Center-of-mass kinetic energy (should be zero in barycentric frame)
    T_cm = np.linalg.norm(state.p_cm)**2 / (2 * M)

    # Potential energy (need to express in Jacobi coordinates)
    # Convert back to Cartesian distances
    cart_state = jacobi_to_cartesian(state, masses)
    V = compute_potential_energy(cart_state, masses, G)

    H_internal = T_internal + V
    H_cm = T_cm

    return H_internal, H_cm


def verify_hamiltonian_decoupling(
    state: JacobiState,
    masses: Masses,
    epsilon: float = 1e-6
) -> bool:
    """
    Verify that {H_internal, r_cm} = 0 (Poisson bracket).

    Numerical check: perturb r_cm, H_internal should not change.
    """
    H0, _ = compute_jacobi_hamiltonian(state, masses)

    # Perturb center-of-mass position
    state_perturbed = JacobiState(
        state.r1, state.r2, state.r_cm + epsilon * np.array([1, 0, 0]),
        state.p1, state.p2, state.p_cm, state.dimension
    )

    H1, _ = compute_jacobi_hamiltonian(state_perturbed, masses)

    # H_internal should be unchanged
    return abs(H1 - H0) < 1e-12
```

#### A2.3: Validation

```python
def test_jacobi_roundtrip(
    masses: Masses,
    n_samples: int = 1000
) -> dict:
    """
    Test Cartesian → Jacobi → Cartesian transformation accuracy.

    Returns:
        Dictionary with max/mean errors
    """
    errors = []

    for _ in range(n_samples):
        # Random Cartesian state
        state_cart = CartesianState(
            positions=np.random.randn(3, 3),
            velocities=np.random.randn(3, 3)
        )
        state_cart = enforce_barycenter(state_cart, masses)

        # Round trip
        state_jacobi = cartesian_to_jacobi(state_cart, masses)
        state_cart_reconstructed = jacobi_to_cartesian(state_jacobi, masses)

        # Compute error
        pos_error = np.linalg.norm(
            state_cart.positions - state_cart_reconstructed.positions
        )
        vel_error = np.linalg.norm(
            state_cart.velocities - state_cart_reconstructed.velocities
        )

        errors.append(max(pos_error, vel_error))

    return {
        'max_error': max(errors),
        'mean_error': np.mean(errors),
        'std_error': np.std(errors)
    }
```

### Extension: Arbitrary Hierarchies

```python
class JacobiHierarchy(Enum):
    """Hierarchical grouping options"""
    MASSES_12_3 = "Group bodies 1-2, then add 3"
    MASSES_23_1 = "Group bodies 2-3, then add 1"
    MASSES_13_2 = "Group bodies 1-3, then add 2"


def choose_optimal_hierarchy(masses: Masses) -> JacobiHierarchy:
    """
    Choose hierarchical structure based on mass ratios.

    Strategy:
        - If one mass >> others: group the two smaller masses
        - If two masses similar: group those two
        - Default: group m1-m2
    """
    m = np.array([masses.m1, masses.m2, masses.m3])

    # Find most massive body
    i_max = np.argmax(m)

    if m[i_max] > 10 * np.min(m):
        # Hierarchical system: group the two smaller masses
        if i_max == 0:
            return JacobiHierarchy.MASSES_23_1
        elif i_max == 1:
            return JacobiHierarchy.MASSES_13_2
        else:
            return JacobiHierarchy.MASSES_12_3
    else:
        # Democratic masses: default grouping
        return JacobiHierarchy.MASSES_12_3
```

---

## A3: Shape Space Coordinate System

### Mathematical Specification

**Shape Space**: Quotient $\mathbb{R}^{3N} / (\mathbb{R}^3 \times SO(3))$

**Dimension** (planar 3BP):
- Original: 12 DOF (3 bodies × 2D × 2)
- Quotient: 12 - 3 (translation) - 2 (rotation) = 7 DOF

**Coordinate Representations**:

1. **Relative Distances**: $(r_{12}, r_{23}, r_{31})$ - 3D shape space
2. **Normalized Coordinates**: Oriented triangle with unit scale
3. **Complex Shape Variable**: $z = (r_3 - r_1) / (r_2 - r_1) \in \mathbb{C}$

### Data Structures

```python
@dataclass(frozen=True)
class ShapeSpaceState:
    """
    Shape space coordinates (quotient by translations and rotations).

    Multiple representations available:
        - distances: (r12, r23, r31) - gauge-invariant
        - complex_var: z = (r3 - r1) / (r2 - r1) - planar only
        - oriented_triangle: Canonical orientation + shape parameters
    """
    # Primary representation: relative distances
    r12: float  # distance between bodies 1-2
    r23: float  # distance between bodies 2-3
    r31: float  # distance between bodies 3-1

    # Velocities (time derivatives of distances)
    dr12_dt: float
    dr23_dt: float
    dr31_dt: float

    # Angular momentum (conserved quantity, label on reduced space)
    L: float  # For planar: scalar angular momentum

    # Orientation angle (if not fully reduced)
    theta: Optional[float] = None  # SO(2) angle for planar
    dtheta_dt: Optional[float] = None

    dimension: Literal[2, 3] = 2

    def validate(self) -> bool:
        """Check triangle inequality"""
        return (
            self.r12 + self.r23 >= self.r31 and
            self.r23 + self.r31 >= self.r12 and
            self.r31 + self.r12 >= self.r23
        )

    @property
    def perimeter(self) -> float:
        """Total perimeter of triangle"""
        return self.r12 + self.r23 + self.r31

    @property
    def area(self) -> float:
        """Area of triangle (Heron's formula)"""
        s = self.perimeter / 2
        return np.sqrt(s * (s - self.r12) * (s - self.r23) * (s - self.r31))


@dataclass(frozen=True)
class ComplexShapeState:
    """
    Complex shape variable for planar 3BP.

    Definition: z = (r3 - r1) / (r2 - r1) ∈ ℂ

    Properties:
        - Im(z) > 0: positive orientation
        - |z| related to distance ratios
        - arg(z) related to angles
    """
    z: complex  # Complex shape variable
    z_dot: complex  # Time derivative
    L: float  # Angular momentum

    def validate(self) -> bool:
        """Check that Im(z) > 0 (positive orientation)"""
        return np.imag(self.z) > 0

    def to_distances(self, scale: float = 1.0) -> tuple:
        """Convert to relative distances (r12, r23, r31)"""
        # Scale is ambiguous in shape space
        # Need additional information (e.g., moment of inertia)
        r12 = scale
        r13 = scale * abs(self.z)
        r23 = scale * abs(self.z - 1)
        return (r12, r23, r13)
```

### Core Functions

#### A3.1: Transformations to Shape Space

```python
def cartesian_to_shape_distances(
    state: CartesianState,
    masses: Masses
) -> ShapeSpaceState:
    """
    Transform Cartesian → Shape Space (distance representation).

    Computes:
        r_ij = |r_i - r_j|
        dr_ij/dt = (r_ij · v_ij) / |r_ij|
    where v_ij = v_i - v_j
    """
    r = state.positions
    v = state.velocities

    # Compute distances
    r12_vec = r[0] - r[1]
    r23_vec = r[1] - r[2]
    r31_vec = r[2] - r[0]

    r12 = np.linalg.norm(r12_vec)
    r23 = np.linalg.norm(r23_vec)
    r31 = np.linalg.norm(r31_vec)

    # Compute distance velocities
    v12_vec = v[0] - v[1]
    v23_vec = v[1] - v[2]
    v31_vec = v[2] - v[0]

    dr12_dt = np.dot(r12_vec, v12_vec) / r12 if r12 > 0 else 0.0
    dr23_dt = np.dot(r23_vec, v23_vec) / r23 if r23 > 0 else 0.0
    dr31_dt = np.dot(r31_vec, v31_vec) / r31 if r31 > 0 else 0.0

    # Compute angular momentum
    L = compute_angular_momentum(state, masses)
    L_z = L[2] if state.dimension == 2 else np.linalg.norm(L)

    return ShapeSpaceState(
        r12, r23, r31,
        dr12_dt, dr23_dt, dr31_dt,
        L_z, dimension=state.dimension
    )


def cartesian_to_complex_shape(
    state: CartesianState,
    masses: Masses
) -> ComplexShapeState:
    """
    Transform Cartesian → Complex shape variable (planar only).

    Definition:
        z = (r3 - r1) / (r2 - r1)

    Requires: planar motion (dimension = 2)
    """
    assert state.dimension == 2, "Complex shape only for planar motion"

    r = state.positions[:, :2]  # Extract x, y components
    v = state.velocities[:, :2]

    # Complex positions
    z1 = r[0, 0] + 1j * r[0, 1]
    z2 = r[1, 0] + 1j * r[1, 1]
    z3 = r[2, 0] + 1j * r[2, 1]

    # Complex velocities
    v1 = v[0, 0] + 1j * v[0, 1]
    v2 = v[1, 0] + 1j * v[1, 1]
    v3 = v[2, 0] + 1j * v[2, 1]

    # Shape variable
    z_shape = (z3 - z1) / (z2 - z1)

    # Time derivative (quotient rule)
    numerator_dot = v3 - v1
    denominator = z2 - z1
    denominator_dot = v2 - v1

    z_shape_dot = (numerator_dot * denominator -
                   (z3 - z1) * denominator_dot) / (denominator**2)

    # Angular momentum
    L = compute_angular_momentum(state, masses)
    L_z = L[2]

    return ComplexShapeState(z_shape, z_shape_dot, L_z)
```

#### A3.2: Canonical Orientation

```python
def compute_canonical_orientation(
    state: CartesianState,
    method: str = 'align_axis'
) -> tuple[CartesianState, float]:
    """
    Rotate state to canonical orientation.

    Methods:
        - 'align_axis': Align body 1-2 axis with x-axis
        - 'align_angular_momentum': Align L with z-axis (spatial)
        - 'principal_axes': Align with principal axes of inertia

    Returns:
        state_canonical: Rotated state
        theta: Rotation angle applied (for inverse)
    """
    if method == 'align_axis':
        # Rotate so that r1-r2 lies along x-axis
        r12_vec = state.positions[0] - state.positions[1]
        r12_vec_2d = r12_vec[:2]  # x, y components

        # Current angle
        theta = np.arctan2(r12_vec_2d[1], r12_vec_2d[0])

        # Rotation matrix (about z-axis)
        c, s = np.cos(-theta), np.sin(-theta)
        R = np.array([
            [c, -s, 0],
            [s,  c, 0],
            [0,  0, 1]
        ])

        # Apply rotation
        positions_rot = state.positions @ R.T
        velocities_rot = state.velocities @ R.T

        return CartesianState(positions_rot, velocities_rot,
                              state.dimension), theta

    else:
        raise NotImplementedError(f"Method {method} not implemented")


def oriented_triangle_coordinates(
    state: CartesianState,
    masses: Masses
) -> dict:
    """
    Compute oriented triangle representation.

    Returns dictionary with:
        - distances: (r12, r23, r31)
        - angles: (alpha, beta, gamma) - interior angles
        - orientation: theta (angle of axis 1-2 from x-axis)
        - scale: overall scale (e.g., moment of inertia)
    """
    state_canonical, theta = compute_canonical_orientation(state, 'align_axis')

    r = state_canonical.positions

    # Distances
    r12 = np.linalg.norm(r[0] - r[1])
    r23 = np.linalg.norm(r[1] - r[2])
    r31 = np.linalg.norm(r[2] - r[0])

    # Angles (law of cosines)
    alpha = np.arccos((r12**2 + r31**2 - r23**2) / (2 * r12 * r31))
    beta = np.arccos((r12**2 + r23**2 - r31**2) / (2 * r12 * r23))
    gamma = np.pi - alpha - beta

    # Scale (moment of inertia)
    I = compute_moment_of_inertia(state, masses)

    return {
        'distances': (r12, r23, r31),
        'angles': (alpha, beta, gamma),
        'orientation': theta,
        'scale': I
    }
```

#### A3.3: Shape Space Metric

```python
def compute_mass_metric(
    state: CartesianState,
    masses: Masses
) -> np.ndarray:
    """
    Compute mass-weighted metric tensor.

    g = sum_i m_i dr_i ⊗ dr_i

    In Cartesian coordinates, this is diagonal:
        g_ij = m_i δ_ij (for positions of body i)
    """
    m = np.array([masses.m1, masses.m2, masses.m3])

    # Metric is 9x9 (3 bodies × 3 coordinates)
    g = np.zeros((9, 9))

    for i in range(3):
        for d in range(3):  # dimensions
            idx = 3 * i + d
            g[idx, idx] = m[i]

    return g


def compute_shape_space_metric(
    shape_state: ShapeSpaceState,
    masses: Masses
) -> np.ndarray:
    """
    Compute induced metric on shape space (quotient metric).

    This is the metric tensor in (r12, r23, r31) coordinates.
    Requires pulling back the mass metric via the embedding.

    Returns:
        g_shape: 3x3 metric tensor
    """
    # Convert to Cartesian (with arbitrary position/orientation)
    # This is ambiguous - we fix it by placing in canonical form
    cart_state = shape_distances_to_cartesian_canonical(shape_state)

    # Compute Jacobian: d(Cartesian) / d(shape)
    # This requires numerical differentiation or symbolic computation
    J = compute_shape_jacobian(shape_state)

    # Pull back metric: g_shape = J^T @ g_cart @ J
    g_cart = compute_mass_metric(cart_state, masses)
    g_shape = J.T @ g_cart @ J

    return g_shape


def shape_distances_to_cartesian_canonical(
    shape_state: ShapeSpaceState
) -> CartesianState:
    """
    Reconstruct Cartesian state from shape distances (canonical orientation).

    Canonical form:
        - Body 1 at origin
        - Body 2 on positive x-axis at distance r12
        - Body 3 in xy-plane with positive y-coordinate

    Returns:
        Cartesian state (positions only, velocities require additional info)
    """
    r12, r23, r31 = shape_state.r12, shape_state.r23, shape_state.r31

    # Body 1 at origin
    r1 = np.array([0.0, 0.0, 0.0])

    # Body 2 on x-axis
    r2 = np.array([r12, 0.0, 0.0])

    # Body 3: solve triangle
    # r31^2 = x3^2 + y3^2
    # r23^2 = (x3 - r12)^2 + y3^2
    # Solving: x3 = (r31^2 - r23^2 + r12^2) / (2 * r12)
    x3 = (r31**2 - r23**2 + r12**2) / (2 * r12)
    y3 = np.sqrt(r31**2 - x3**2)
    r3 = np.array([x3, y3, 0.0])

    positions = np.array([r1, r2, r3])

    # Velocities: need additional information (distance velocities)
    # This is complex - requires solving linear system
    # For now, return zero velocities (incomplete transformation)
    velocities = np.zeros((3, 3))

    return CartesianState(positions, velocities, dimension=2)
```

### Testing Strategy

```python
# tests/test_shape_space.py

class TestShapeDistances:
    """Test distance representation"""

    def test_triangle_inequality(self):
        """All valid states should satisfy triangle inequality"""
        state = ShapeSpaceState(
            r12=1.0, r23=1.0, r31=1.5,
            dr12_dt=0.0, dr23_dt=0.0, dr31_dt=0.0,
            L=1.0
        )
        assert state.validate()

        # Invalid triangle
        invalid = ShapeSpaceState(
            r12=1.0, r23=1.0, r31=3.0,  # violates inequality
            dr12_dt=0.0, dr23_dt=0.0, dr31_dt=0.0,
            L=1.0
        )
        assert not invalid.validate()

    def test_equilateral_triangle(self):
        """Equilateral triangle has all sides equal"""
        masses = Masses(1.0, 1.0, 1.0)

        # Set up equilateral triangle in Cartesian
        R = 1.0
        angles = np.array([0, 2*np.pi/3, 4*np.pi/3])
        positions = R * np.column_stack([
            np.cos(angles), np.sin(angles), np.zeros(3)
        ])
        velocities = np.zeros((3, 3))

        state_cart = CartesianState(positions, velocities, dimension=2)
        state_cart = enforce_barycenter(state_cart, masses)

        # Convert to shape space
        shape = cartesian_to_shape_distances(state_cart, masses)

        # All sides should be equal
        side_length = np.sqrt(3) * R
        assert abs(shape.r12 - side_length) < 1e-10
        assert abs(shape.r23 - side_length) < 1e-10
        assert abs(shape.r31 - side_length) < 1e-10


class TestComplexShape:
    """Test complex shape variable (planar)"""

    def test_orientation_independence(self):
        """Shape variable should be invariant under rotation"""
        masses = Masses(1.0, 1.0, 1.0)

        # Random planar state
        positions = np.random.randn(3, 3)
        positions[:, 2] = 0  # planar
        velocities = np.random.randn(3, 3)
        velocities[:, 2] = 0

        state = CartesianState(positions, velocities, dimension=2)
        state = enforce_barycenter(state, masses)

        z1 = cartesian_to_complex_shape(state, masses).z

        # Rotate by angle theta
        theta = np.pi / 4
        c, s = np.cos(theta), np.sin(theta)
        R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

        state_rot = CartesianState(
            positions @ R.T,
            velocities @ R.T,
            dimension=2
        )

        z2 = cartesian_to_complex_shape(state_rot, masses).z

        # Shape variable should differ by phase e^{i*theta}
        # Actually, for the definition z = (r3-r1)/(r2-r1), it rotates
        # So we check |z1| = |z2| (magnitude preserved)
        assert abs(abs(z1) - abs(z2)) < 1e-10
```

---

## Integration & Testing Strategy

### Test Suite Structure

```
tests/
├── unit/
│   ├── test_cartesian.py          # CartesianState tests
│   ├── test_jacobi.py              # JacobiState tests
│   ├── test_shape_space.py         # ShapeSpaceState tests
│   └── test_conservation.py        # Conservation law tests
├── integration/
│   ├── test_transformations.py     # Round-trip tests
│   ├── test_lagrange_equilibrium.py  # Known solution
│   └── test_figure8.py             # Figure-8 orbit
└── validation/
    ├── test_precision.py           # Double vs quad-double
    └── test_performance.py         # Benchmark timings
```

### Continuous Integration Checks

```yaml
# .github/workflows/coordinate_systems.yml

name: Coordinate Systems Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: |
          pytest tests/test_cartesian.py --cov=src/python/coordinates/cartesian
          pytest tests/test_jacobi.py --cov=src/python/coordinates/jacobi
          pytest tests/test_shape_space.py --cov=src/python/coordinates/shape_space

      - name: Check coverage
        run: |
          pytest --cov=src/python/coordinates --cov-report=term-missing --cov-fail-under=95

      - name: Run validation tests
        run: |
          pytest tests/integration/ -v
```

---

## Performance Considerations

### Optimization Strategies

1. **Vectorization**: Batch transformations for multiple states
   ```python
   def cartesian_to_jacobi_batch(
       states: np.ndarray,  # shape (N, 18)
       masses: Masses
   ) -> np.ndarray:  # shape (N, 18)
       """Vectorized transformation for N states"""
       # Use NumPy broadcasting
       pass
   ```

2. **JIT Compilation**: Use Numba for hot loops
   ```python
   from numba import jit

   @jit(nopython=True)
   def compute_accelerations_fast(positions, masses):
       # Numba-optimized version
       pass
   ```

3. **Caching**: Memoize expensive calculations
   ```python
   from functools import lru_cache

   @lru_cache(maxsize=128)
   def compute_shape_metric(r12, r23, r31, masses_tuple):
       # Cached metric computation
       pass
   ```

### Performance Benchmarks

Target timings (single state, double precision):
- Cartesian → Jacobi: < 10 μs
- Jacobi → Cartesian: < 10 μs
- Cartesian → Shape: < 50 μs
- Energy/momentum computation: < 5 μs

---

## Implementation Checklist

### A1: Cartesian Coordinates
- [ ] `CartesianState` dataclass with validation
- [ ] Flat array ↔ structured state conversion
- [ ] Barycenter enforcement function
- [ ] Energy computation (double and QD)
- [ ] Angular momentum computation
- [ ] Linear momentum computation
- [ ] Acceleration calculator
- [ ] RHS for integrators
- [ ] `ConservationMonitor` class
- [ ] Unit tests (>95% coverage)
- [ ] Lagrange equilibrium validation

### A2: Jacobi Coordinates
- [ ] `JacobiState` dataclass
- [ ] Reduced mass calculations
- [ ] Cartesian → Jacobi transformation
- [ ] Jacobi → Cartesian transformation
- [ ] Jacobi Hamiltonian (internal + cm)
- [ ] Decoupling verification
- [ ] Round-trip accuracy tests
- [ ] Hierarchical structure selection
- [ ] Performance benchmarks
- [ ] Integration with WP1 integrators

### A3: Shape Space Coordinates
- [ ] `ShapeSpaceState` dataclass
- [ ] `ComplexShapeState` dataclass
- [ ] Cartesian → distance representation
- [ ] Cartesian → complex shape (planar)
- [ ] Canonical orientation function
- [ ] Oriented triangle coordinates
- [ ] Mass metric computation
- [ ] Shape space metric (quotient)
- [ ] Distance → Cartesian (canonical)
- [ ] Triangle inequality validation
- [ ] Visualization tools
- [ ] Unit tests for all representations

### Integration & Documentation
- [ ] Transformation registry (`transforms.py`)
- [ ] Complete API documentation
- [ ] Tutorial Jupyter notebook
- [ ] Validation report
- [ ] Performance benchmark report
- [ ] CI/CD pipeline integration

---

## Next Steps

After completing Part A:

1. **Part B**: Implement Marsden-Weinstein symplectic reduction
2. **Part C**: Integrate with WP1 infrastructure (adapt integrators)
3. **Part D**: Complete documentation and technical report

---

**Document Version**: 1.0
**Created**: 2025-11-07
**Author**: Implementation Team
**Status**: Design Complete → Ready for Implementation
