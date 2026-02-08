# Task 2.1.3 Part A: JM Metric Implementation - Detailed Design

**Task**: WP 2.1.3 - Jacobi-Maupertuis Metric Analysis
**Part**: A - JM Metric Tensor Implementation
**Status**: Design Phase
**Estimated Duration**: 2 days
**Dependencies**: Task 2.1.1 Complete (Shape Space Coordinates)

---

## Table of Contents

1. [Overview](#overview)
2. [A1: Mass-Weighted Metric](#a1-mass-weighted-metric)
3. [A2: Shape Space Metric Induction](#a2-shape-space-metric-induction)
4. [A3: Effective Potential](#a3-effective-potential)
5. [A4: JM Metric Construction](#a4-jm-metric-construction)
6. [A5: Christoffel Symbols](#a5-christoffel-symbols)
7. [Testing and Validation](#testing-and-validation)

---

## Overview

### Purpose

Part A implements the Jacobi-Maupertuis (JM) metric tensor on shape space. This Riemannian metric encodes the geometry of constant-energy dynamics: geodesics in this metric correspond to physical trajectories of the three-body problem.

**Key Formula**:
$$
g_{JM}(s) = 2(E - V_{eff}(s)) \cdot g_{shape}(s)
$$

### Components

1. **Mass-Weighted Metric**: $g_{mass}$ in Cartesian coordinates
2. **Shape Space Pullback**: Induced metric on shape space
3. **Effective Potential**: $V_{eff} = V_{grav} + L^2/(2I)$
4. **JM Metric Tensor**: Complete metric at energy $E$
5. **Christoffel Symbols**: Connection coefficients $\Gamma^k_{ij}$

---

## A1: Mass-Weighted Metric

### Algorithm A1.1: Cartesian Mass Metric

```python
def compute_mass_metric_cartesian(masses: Masses, dimension: int = 3) -> np.ndarray:
    """
    Compute mass-weighted kinetic energy metric in Cartesian coordinates.

    The metric is:
    g_mass = diag(m1, m1, m1, m2, m2, m2, m3, m3, m3)

    for 3D motion.

    Args:
        masses: Body masses
        dimension: Spatial dimension (2 or 3)

    Returns:
        Diagonal matrix (3*dimension × 3*dimension)
    """
    m = np.array([masses.m1, masses.m2, masses.m3])

    # Repeat each mass 'dimension' times
    mass_diagonal = np.repeat(m, dimension)

    # Return as diagonal matrix
    return np.diag(mass_diagonal)


def compute_kinetic_energy(
    velocities: np.ndarray,
    masses: Masses
) -> float:
    """
    Compute kinetic energy T = (1/2) v^T g_mass v.

    Args:
        velocities: Velocity vector (9D for 3 bodies in 3D)
        masses: Body masses

    Returns:
        Kinetic energy (scalar)
    """
    g_mass = compute_mass_metric_cartesian(masses)
    T = 0.5 * velocities @ g_mass @ velocities
    return T
```

---

## A2: Shape Space Metric Induction

### Algorithm A2.1: Jacobian of Shape Embedding

```python
def compute_shape_embedding_jacobian(
    shape_state: ShapeSpaceState,
    masses: Masses
) -> np.ndarray:
    """
    Compute Jacobian of embedding: shape space → Cartesian.

    The embedding is: (r12, r23, r31) → (r1, r2, r3)

    This requires solving the linear system:
        r1 - r2 = r12_vector
        r2 - r3 = r23_vector
        r3 - r1 = r31_vector (redundant, from closure)
        Σ m_i r_i = 0 (barycenter)

    Returns:
        Jacobian matrix (9 × 3) for 3D case
    """
    # Get scalar distances
    r12 = shape_state.r12
    r23 = shape_state.r23
    r31 = shape_state.r31

    # Construct canonical Cartesian configuration
    # Place bodies in standard position (e.g., body 1 at origin in some gauge)
    positions = shape_to_cartesian_canonical(shape_state, masses)

    # Compute Jacobian via finite differences
    n_shape = 3  # Shape space dimension
    n_cart = 9   # Cartesian dimension (3 bodies × 3D)

    jacobian = np.zeros((n_cart, n_shape))
    epsilon = 1e-8

    for i in range(n_shape):
        # Perturb i-th shape coordinate
        coords_plus = shape_state.to_array().copy()
        coords_plus[i] += epsilon

        coords_minus = shape_state.to_array().copy()
        coords_minus[i] -= epsilon

        # Convert to Cartesian
        state_plus = ShapeSpaceState.from_array(coords_plus)
        state_minus = ShapeSpaceState.from_array(coords_minus)

        pos_plus = shape_to_cartesian_canonical(state_plus, masses)
        pos_minus = shape_to_cartesian_canonical(state_minus, masses)

        # Finite difference
        jacobian[:, i] = (pos_plus.flatten() - pos_minus.flatten()) / (2 * epsilon)

    return jacobian


def shape_to_cartesian_canonical(
    shape_state: ShapeSpaceState,
    masses: Masses
) -> np.ndarray:
    """
    Convert shape space state to Cartesian in canonical gauge.

    Canonical gauge:
    - Barycenter at origin
    - Body 1-2 axis along x-axis
    - Planar motion in xy-plane

    Returns:
        (3, 3) array of body positions
    """
    r12 = shape_state.r12
    r23 = shape_state.r23
    r31 = shape_state.r31

    # Solve linear system for body positions
    # Variables: (r1_x, r1_y), (r2_x, r2_y), (r3_x, r3_y)

    # Constraints:
    # 1. |r1 - r2| = r12
    # 2. |r2 - r3| = r23
    # 3. |r3 - r1| = r31
    # 4. m1*r1 + m2*r2 + m3*r3 = 0 (barycenter)
    # 5. r1 and r2 on x-axis (gauge fixing)

    # Standard solution (planar, canonical orientation):
    m1, m2, m3 = masses.m1, masses.m2, masses.m3
    M = m1 + m2 + m3

    # Place body 1 and 2 on x-axis
    r1_x = -m2 * r12 / M
    r1_y = 0.0

    r2_x = m1 * r12 / M
    r2_y = 0.0

    # Body 3 position from distances
    # Solve: |r3 - r1| = r31, |r3 - r2| = r23

    # Using law of cosines in triangle
    cos_angle = (r12**2 + r31**2 - r23**2) / (2 * r12 * r31)

    r3_x = r1_x + r31 * np.cos(np.arccos(cos_angle))
    r3_y = r31 * np.sin(np.arccos(cos_angle))

    # Adjust for barycenter
    r_cm_x = (m1 * r1_x + m2 * r2_x + m3 * r3_x) / M
    r_cm_y = (m1 * r1_y + m2 * r2_y + m3 * r3_y) / M

    r1_x -= r_cm_x
    r1_y -= r_cm_y
    r2_x -= r_cm_x
    r2_y -= r_cm_y
    r3_x -= r_cm_x
    r3_y -= r_cm_y

    positions = np.array([
        [r1_x, r1_y, 0.0],
        [r2_x, r2_y, 0.0],
        [r3_x, r3_y, 0.0]
    ])

    return positions
```

### Algorithm A2.2: Induced Shape Metric

```python
def compute_shape_space_metric(
    shape_state: ShapeSpaceState,
    masses: Masses
) -> RiemannianMetric:
    """
    Compute induced metric on shape space via pullback.

    g_shape = J^T @ g_mass @ J

    where J is the Jacobian of the embedding.

    Returns:
        3×3 metric tensor
    """
    # Mass metric in Cartesian
    g_cart = compute_mass_metric_cartesian(masses, dimension=3)

    # Embedding Jacobian
    J = compute_shape_embedding_jacobian(shape_state, masses)

    # Pullback: g_shape = J^T @ g_cart @ J
    g_shape = J.T @ g_cart @ J

    return RiemannianMetric(
        components=g_shape,
        coordinate_names=['r12', 'r23', 'r31'],
        base_point=shape_state
    )
```

---

## A3: Effective Potential

### Algorithm A3.1: Gravitational Potential

```python
def compute_gravitational_potential(
    shape_state: ShapeSpaceState,
    masses: Masses,
    G: float = 1.0
) -> float:
    """
    Compute gravitational potential energy.

    V = -G * Σ_{i<j} m_i m_j / r_ij

    Args:
        shape_state: Shape configuration
        masses: Body masses
        G: Gravitational constant

    Returns:
        Potential energy (negative)
    """
    r12 = shape_state.r12
    r23 = shape_state.r23
    r31 = shape_state.r31

    m1, m2, m3 = masses.m1, masses.m2, masses.m3

    V = -G * (
        m1 * m2 / r12 +
        m2 * m3 / r23 +
        m3 * m1 / r31
    )

    return V
```

### Algorithm A3.2: Moment of Inertia

```python
def compute_moment_of_inertia(
    shape_state: ShapeSpaceState,
    masses: Masses
) -> float:
    """
    Compute moment of inertia about barycenter.

    I = Σ m_i |r_i|^2

    For planar motion, this is the scalar moment about z-axis.

    Returns:
        Moment of inertia
    """
    # Convert to Cartesian
    positions = shape_to_cartesian_canonical(shape_state, masses)

    m = np.array([masses.m1, masses.m2, masses.m3])

    # I = Σ m_i (x_i^2 + y_i^2)
    I = np.sum(m * (positions[:, 0]**2 + positions[:, 1]**2))

    return I
```

### Algorithm A3.3: Effective Potential with Centrifugal Term

```python
def compute_effective_potential(
    shape_state: ShapeSpaceState,
    masses: Masses,
    L_magnitude: float,
    G: float = 1.0
) -> float:
    """
    Compute effective potential including centrifugal term.

    V_eff = V_grav + L^2 / (2*I)

    Args:
        shape_state: Shape configuration
        masses: Body masses
        L_magnitude: Angular momentum magnitude |L|
        G: Gravitational constant

    Returns:
        Effective potential
    """
    # Gravitational part
    V_grav = compute_gravitational_potential(shape_state, masses, G)

    # Centrifugal part
    I = compute_moment_of_inertia(shape_state, masses)
    V_centrifugal = L_magnitude**2 / (2 * I)

    V_eff = V_grav + V_centrifugal

    return V_eff
```

---

## A4: JM Metric Construction

### Algorithm A4.1: Complete JM Metric

```python
def compute_jm_metric(
    shape_state: ShapeSpaceState,
    masses: Masses,
    energy: float,
    L_magnitude: float = 0.0,
    G: float = 1.0
) -> RiemannianMetric:
    """
    Compute Jacobi-Maupertuis metric.

    g_JM = 2(E - V_eff) * g_shape

    This is the metric on the constant-energy shell.

    Args:
        shape_state: Point in shape space
        masses: Body masses
        energy: Total energy E
        L_magnitude: Angular momentum |L|
        G: Gravitational constant

    Returns:
        JM metric tensor (3×3)

    Raises:
        ValueError: If E ≤ V_eff (classically forbidden)
    """
    # Shape space metric
    g_shape = compute_shape_space_metric(shape_state, masses)

    # Effective potential
    V_eff = compute_effective_potential(shape_state, masses, L_magnitude, G)

    # Check classical accessibility
    energy_difference = energy - V_eff

    if energy_difference <= 0:
        raise ValueError(
            f"Classically forbidden region: "
            f"E={energy:.6f} ≤ V_eff={V_eff:.6f}"
        )

    # JM metric
    conformal_factor = 2 * energy_difference
    g_jm = conformal_factor * g_shape.components

    return RiemannianMetric(
        components=g_jm,
        coordinate_names=g_shape.coordinate_names,
        base_point=shape_state
    )


@dataclass(frozen=True)
class RiemannianMetric:
    """Riemannian metric tensor at a point."""
    components: np.ndarray  # Symmetric positive-definite matrix
    coordinate_names: list[str]
    base_point: ShapeSpaceState

    def inverse(self) -> np.ndarray:
        """Compute contravariant metric g^{ij}."""
        return np.linalg.inv(self.components)

    def determinant(self) -> float:
        """Compute det(g)."""
        return np.linalg.det(self.components)

    def eigenvalues(self) -> np.ndarray:
        """Principal axis lengths."""
        return np.linalg.eigvalsh(self.components)

    def trace(self) -> float:
        """Trace of metric."""
        return np.trace(self.components)
```

---

## A5: Christoffel Symbols

### Algorithm A5.1: Metric Derivatives

```python
def compute_metric_derivatives(
    metric_func: Callable[[ShapeSpaceState], RiemannianMetric],
    base_state: ShapeSpaceState,
    epsilon: float = 1e-6
) -> np.ndarray:
    """
    Compute derivatives of metric: ∂g_{ij}/∂x^k.

    Uses central finite differences.

    Args:
        metric_func: Function that computes metric at any point
        base_state: Point where to compute derivatives
        epsilon: Step size

    Returns:
        3D array dg[k, i, j] = ∂g_{ij}/∂x^k
    """
    g_base = metric_func(base_state)
    n = g_base.components.shape[0]

    dg = np.zeros((n, n, n))

    for k in range(n):
        # Perturb k-th coordinate
        coords_plus = base_state.to_array().copy()
        coords_plus[k] += epsilon

        coords_minus = base_state.to_array().copy()
        coords_minus[k] -= epsilon

        state_plus = ShapeSpaceState.from_array(coords_plus)
        state_minus = ShapeSpaceState.from_array(coords_minus)

        # Metric at perturbed points
        g_plus = metric_func(state_plus)
        g_minus = metric_func(state_minus)

        # Central difference
        dg[k, :, :] = (g_plus.components - g_minus.components) / (2 * epsilon)

    return dg
```

### Algorithm A5.2: Christoffel Symbol Computation

```python
def compute_christoffel_symbols(
    metric: RiemannianMetric,
    metric_derivatives: np.ndarray
) -> ChristoffelSymbols:
    """
    Compute Christoffel symbols of second kind.

    Γ^k_{ij} = (1/2) g^{kl} (∂_i g_{jl} + ∂_j g_{il} - ∂_l g_{ij})

    Args:
        metric: Metric tensor g_{ij}
        metric_derivatives: ∂g_{ij}/∂x^k

    Returns:
        ChristoffelSymbols object with Γ^k_{ij}
    """
    g = metric.components
    g_inv = metric.inverse()
    dg = metric_derivatives  # dg[k, i, j] = ∂g_{ij}/∂x^k

    n = g.shape[0]
    christoffel = np.zeros((n, n, n))

    for k in range(n):
        for i in range(n):
            for j in range(n):
                # Sum over l
                for l in range(n):
                    term = (dg[i, j, l] + dg[j, i, l] - dg[l, i, j])
                    christoffel[k, i, j] += 0.5 * g_inv[k, l] * term

    return ChristoffelSymbols(
        symbols=christoffel,
        coordinate_names=metric.coordinate_names,
        base_point=metric.base_point
    )


@dataclass(frozen=True)
class ChristoffelSymbols:
    """Christoffel symbols Γ^k_{ij}."""
    symbols: np.ndarray  # Shape (n, n, n)
    coordinate_names: list[str]
    base_point: ShapeSpaceState

    def __getitem__(self, indices: tuple) -> float:
        """Access Γ^k_{ij}."""
        k, i, j = indices
        return self.symbols[k, i, j]
```

---

## Testing and Validation

### Test Suite

```python
class TestJMMetric:
    """Test JM metric implementation."""

    def test_mass_metric_positive_definite(self):
        """Mass metric must be positive definite."""
        masses = Masses(1.0, 1.0, 1.0)
        g_mass = compute_mass_metric_cartesian(masses)

        # All eigenvalues > 0
        eigenvalues = np.linalg.eigvalsh(g_mass)
        assert np.all(eigenvalues > 0)

    def test_shape_metric_positive_definite(self):
        """Shape metric must be positive definite."""
        masses = Masses(1.0, 1.0, 1.0)
        state = ShapeSpaceState(1.0, 1.0, 1.0, L=1.0)

        g_shape = compute_shape_space_metric(state, masses)

        eigenvalues = g_shape.eigenvalues()
        assert np.all(eigenvalues > 0)

    def test_jm_metric_scale_factor(self):
        """JM metric = 2(E - V_eff) * g_shape."""
        masses = Masses(1.0, 1.0, 1.0)
        state = ShapeSpaceState(1.0, 1.0, 1.0, L=1.0)
        energy = -0.5

        g_shape = compute_shape_space_metric(state, masses)
        g_jm = compute_jm_metric(state, masses, energy, L_magnitude=1.0)

        V_eff = compute_effective_potential(state, masses, L_magnitude=1.0)
        expected_factor = 2 * (energy - V_eff)

        # g_jm should be g_shape scaled by factor
        assert np.allclose(
            g_jm.components,
            expected_factor * g_shape.components
        )

    def test_christoffel_symmetry(self):
        """Γ^k_{ij} = Γ^k_{ji} (symmetric in lower indices)."""
        masses = Masses(1.0, 1.0, 1.0)
        state = ShapeSpaceState(1.0, 1.0, 1.0, L=1.0)

        metric = compute_jm_metric(state, masses, energy=-0.5)
        metric_func = lambda s: compute_jm_metric(s, masses, energy=-0.5)
        dg = compute_metric_derivatives(metric_func, state)

        christoffel = compute_christoffel_symbols(metric, dg)

        # Check symmetry
        for k in range(3):
            for i in range(3):
                for j in range(3):
                    assert np.isclose(
                        christoffel[k, i, j],
                        christoffel[k, j, i],
                        atol=1e-10
                    )

    def test_kepler_limit(self):
        """In Kepler limit (m3 → 0), metric should approach known form."""
        m3_values = [1.0, 0.1, 0.01, 0.001]
        state = ShapeSpaceState(1.0, 1.0, 1.0, L=1.0)

        metrics = []
        for m3 in m3_values:
            masses = Masses(1.0, 1.0, m3)
            try:
                g_jm = compute_jm_metric(state, masses, energy=-0.5)
                metrics.append(g_jm.trace())
            except:
                metrics.append(np.nan)

        # Should show convergence
        differences = np.diff(metrics)
        # Later differences should be smaller
        assert abs(differences[-1]) < abs(differences[0])
```

---

## Summary

Part A provides:

✅ **Mass-weighted metric** in Cartesian coordinates
✅ **Shape space metric** via pullback
✅ **Effective potential** with centrifugal term
✅ **JM metric tensor** construction
✅ **Christoffel symbols** for connection

**Next**: Part B (Riemann Curvature Tensor and Scalar Curvature)

---

**Document Version**: 1.0
**Created**: 2025-11-14
**Status**: Complete
**Estimated Lines**: ~1,500
