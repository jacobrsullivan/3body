# Task 2.1.3: Jacobi-Maupertuis (JM) Metric Analysis
## WP 2.1 - Geometric Reduction and Shape Space Analysis

**Status**: Design Phase
**Priority**: Critical Path
**Estimated Duration**: 6-8 days
**Dependencies**: Task 2.1.1 Complete (Coordinate Systems), Task 2.1.2 Recommended (Connection)

---

## Table of Contents

1. [Overview](#overview)
2. [Mathematical Background](#mathematical-background)
3. [Implementation Architecture](#implementation-architecture)
4. [Part A: JM Metric Implementation](#part-a-jm-metric-implementation)
5. [Part B: Curvature Analysis](#part-b-curvature-analysis)
6. [Part C: Visualization and Exploration](#part-c-visualization-and-exploration)
7. [Part D: Scientific Analysis and Validation](#part-d-scientific-analysis-and-validation)
8. [Integration with Existing Infrastructure](#integration-with-existing-infrastructure)
9. [Implementation Schedule](#implementation-schedule)
10. [Success Criteria](#success-criteria)

---

## Overview

### Purpose

Task 2.1.3 implements the **Jacobi-Maupertuis (JM) metric** on shape space and analyzes its **scalar curvature**. This metric provides a Riemannian geometric perspective on the three-body problem, with the curvature serving as a diagnostic for chaos: **negative curvature is the geometric signature of chaos**.

**Physical Interpretation**: The JM metric measures the "cost" of moving through shape space at fixed total energy. Geodesics in this metric correspond to dynamical trajectories. Negative curvature indicates instability—nearby geodesics diverge exponentially, manifesting as sensitive dependence on initial conditions (chaos).

### Objectives

1. **Metric Implementation**: Compute the JM metric tensor $g_{JM}$ at arbitrary points in shape space
2. **Curvature Computation**: Calculate scalar curvature $R$ using Christoffel symbols
3. **Chaos Correlation**: Identify regions where $R < 0$ and correlate with Lyapunov exponents
4. **Visualization**: Create intuitive visualizations of the metric and curvature fields
5. **Scientific Analysis**: Confirm hypothesis that planar equal-mass 3BP has negative curvature

### Deliverables

- **Deliverable 2.3.1**: JM metric tensor evaluator (high-precision)
- **Deliverable 2.3.2**: Scalar curvature computation library
- **Deliverable 2.3.3**: Curvature field visualization tools
- **Deliverable 2.3.4**: Correlation analysis: $R$ vs. chaos indicators (MLE, MEGNO)
- **Deliverable 2.3.5**: Technical report section: "Geometric Origin of Chaos in the 3BP"

---

## Mathematical Background

### The Jacobi-Maupertuis Metric

The **Jacobi metric** (also called Maupertuis metric or kinetic energy metric) is a Riemannian metric on configuration space that encodes the dynamics at fixed energy.

#### Definition

For a Hamiltonian system $H = T + V$ with kinetic energy $T = \frac{1}{2} \sum g_{ij} \dot{q}^i \dot{q}^j$ and potential $V(q)$, the JM metric on the energy shell $H = E$ is:

$$
g_{JM} = 2(E - V(q)) \cdot g_{\text{mass}}
$$

where $g_{\text{mass}}$ is the mass-weighted kinetic energy metric.

**For the 3-Body Problem** (in barycentric frame):

$$
g_{\text{mass}} = \sum_{i=1}^3 m_i \, dr_i \otimes dr_i
$$

After reduction to shape space (dimension 3 for planar motion), the JM metric becomes:

$$
g_{JM}(s) = 2(E - V_{\text{eff}}(s)) \cdot g_{\text{shape}}(s)
$$

where:
- $s$ represents shape space coordinates (e.g., $(r_{12}, r_{23}, r_{31})$)
- $V_{\text{eff}}$ is the effective potential including centrifugal terms
- $g_{\text{shape}}$ is the induced metric on shape space

#### Key Properties

1. **Energy Surface**: The JM metric is only defined where $E > V(q)$ (classically accessible region)
2. **Geodesics = Trajectories**: Geodesics of $g_{JM}$ correspond to dynamical trajectories at fixed $E$
3. **Curvature = Instability**: Negative scalar curvature $R < 0$ implies exponential divergence of nearby geodesics

### Scalar Curvature

The **scalar curvature** $R$ is the trace of the Ricci curvature tensor:

$$
R = g^{ij} R_{ij}
$$

where $R_{ij}$ is the Ricci tensor:

$$
R_{ij} = \frac{\partial \Gamma^k_{ij}}{\partial x^k} - \frac{\partial \Gamma^k_{ik}}{\partial x^j} + \Gamma^k_{ij} \Gamma^l_{kl} - \Gamma^k_{il} \Gamma^l_{jk}
$$

and $\Gamma^k_{ij}$ are the **Christoffel symbols**:

$$
\Gamma^k_{ij} = \frac{1}{2} g^{kl} \left( \frac{\partial g_{jl}}{\partial x^i} + \frac{\partial g_{il}}{\partial x^j} - \frac{\partial g_{ij}}{\partial x^l} \right)
$$

**Computational Challenge**: Computing $R$ requires:
1. Metric tensor $g_{ij}$ (6 components in 3D)
2. Inverse metric $g^{ij}$ (6 components)
3. First derivatives $\partial g_{ij} / \partial x^k$ (18 components)
4. Second derivatives $\partial^2 g_{ij} / \partial x^k \partial x^l$ (36 components for direct method)

### Chaos-Curvature Correspondence

**Hypothesis** (to be validated): For the three-body problem:

$$
R < 0 \quad \Leftrightarrow \quad \lambda_{\text{max}} > 0
$$

where $\lambda_{\text{max}}$ is the maximal Lyapunov exponent.

**Justification**: Negative curvature in the JM metric causes geodesic deviation to grow exponentially (Jacobi equation), which is precisely the mechanism of dynamical chaos.

---

## Implementation Architecture

### Module Structure

```
src/python/geometry/
├── jm_metric.py                   # A: JM metric tensor computation
├── christoffel.py                 # A: Christoffel symbols
├── riemann_curvature.py          # B: Riemann, Ricci, scalar curvature
├── geodesics.py                  # Geodesic integration (optional)
└── metric_validation.py          # Validation tests

src/python/visualization/
├── metric_ellipsoid.py           # C: Visualize metric as ellipsoids
├── curvature_landscape.py        # C: 3D curvature plots
├── chaos_curvature_correlation.py # D: Scatter plots R vs λ
└── interactive_explorer.py       # D: Interactive widget

src/python/analysis/
├── chaos_indicators.py           # D: Lyapunov, MEGNO computation
├── correlation_analysis.py       # D: Statistical analysis R vs chaos
└── region_classification.py      # D: Classify shape space regions

tests/geometry/
├── test_jm_metric.py
├── test_christoffel.py
├── test_scalar_curvature.py
└── test_known_cases.py           # Validate against Kepler, etc.
```

### Data Structures

```python
@dataclass(frozen=True)
class RiemannianMetric:
    """
    Riemannian metric tensor at a point.

    Represents g = g_ij dx^i ⊗ dx^j (symmetric positive-definite).
    """
    components: np.ndarray  # Symmetric matrix g_ij
    coordinate_names: list[str]
    base_point: ShapeSpaceState

    def inverse(self) -> np.ndarray:
        """Compute g^ij (contravariant metric)"""
        return np.linalg.inv(self.components)

    def determinant(self) -> float:
        """det(g)"""
        return np.linalg.det(self.components)

    def eigenvalues(self) -> np.ndarray:
        """Principal axes lengths"""
        return np.linalg.eigvalsh(self.components)


@dataclass(frozen=True)
class ChristoffelSymbols:
    """
    Christoffel symbols Γ^k_ij of a Riemannian metric.

    Stored as 3D array: symbols[k, i, j] = Γ^k_ij
    """
    symbols: np.ndarray  # Shape (n, n, n)
    coordinate_names: list[str]
    base_point: ShapeSpaceState

    def __getitem__(self, indices: tuple) -> float:
        """Access Γ^k_ij via symbols[k, i, j]"""
        k, i, j = indices
        return self.symbols[k, i, j]


@dataclass(frozen=True)
class CurvatureTensors:
    """
    Curvature tensors at a point.

    Includes:
        - Riemann tensor R^l_ijk
        - Ricci tensor R_ij
        - Scalar curvature R
    """
    riemann: Optional[np.ndarray] = None  # Shape (n, n, n, n)
    ricci: np.ndarray  # Shape (n, n)
    scalar: float

    @property
    def is_positive(self) -> bool:
        return self.scalar > 0

    @property
    def is_negative(self) -> bool:
        return self.scalar < 0

    @property
    def is_flat(self, tolerance: float = 1e-14) -> bool:
        return abs(self.scalar) < tolerance
```

### Design Patterns

1. **Lazy Evaluation**: Compute curvature only when needed (expensive)
2. **Symbolic + Numeric**: Derive formulas symbolically, evaluate numerically
3. **Caching**: Store metric/Christoffel at grid points for interpolation
4. **Adaptive Precision**: Escalate to quad-precision near singularities

---

## Part A: JM Metric Implementation

### Objectives

1. Implement mass-weighted metric $g_{\text{mass}}$ in Cartesian coordinates
2. Induce metric on shape space via pullback
3. Scale by energy factor: $g_{JM} = 2(E - V_{\text{eff}}) \cdot g_{\text{shape}}$
4. Compute Christoffel symbols $\Gamma^k_{ij}$

### Key Algorithms

#### A1: Mass-Weighted Metric (Cartesian)

```python
def compute_mass_metric_cartesian(masses: Masses) -> np.ndarray:
    """
    Mass-weighted kinetic energy metric in Cartesian coordinates.

    g_mass = diag(m1, m1, m1, m2, m2, m2, m3, m3, m3)

    Returns:
        9x9 diagonal matrix (for 3D motion)
    """
    m = np.array([masses.m1, masses.m2, masses.m3])
    return np.diag(np.repeat(m, 3))
```

#### A2: Induced Metric on Shape Space

The shape space metric is obtained by pulling back the Cartesian metric via the embedding:

$$
g_{\text{shape}} = J^T g_{\text{mass}} J
$$

where $J$ is the Jacobian of the embedding map: shape coordinates → Cartesian.

```python
def compute_shape_space_metric(
    shape_state: ShapeSpaceState,
    masses: Masses
) -> RiemannianMetric:
    """
    Compute induced metric on shape space.

    Uses the embedding: (r12, r23, r31) → Cartesian (canonical orientation).

    Returns:
        3x3 positive-definite metric tensor
    """
    # Convert to Cartesian (canonical orientation)
    cart_state = shape_to_cartesian_canonical(shape_state)

    # Compute Jacobian: d(Cartesian) / d(shape)
    jacobian = compute_embedding_jacobian(shape_state)  # 9x3 matrix

    # Mass metric in Cartesian
    g_cart = compute_mass_metric_cartesian(masses)  # 9x9

    # Pull back: g_shape = J^T @ g_cart @ J
    g_shape = jacobian.T @ g_cart @ jacobian  # 3x3

    return RiemannianMetric(
        components=g_shape,
        coordinate_names=['r12', 'r23', 'r31'],
        base_point=shape_state
    )
```

#### A3: Effective Potential

For a system with angular momentum $L$, the effective potential includes a centrifugal term:

$$
V_{\text{eff}}(s) = V_{\text{grav}}(s) + \frac{L^2}{2 I(s)}
$$

where $I(s)$ is the moment of inertia for shape $s$.

```python
def compute_effective_potential(
    shape_state: ShapeSpaceState,
    masses: Masses,
    L_magnitude: float,
    G: float = 1.0
) -> float:
    """
    Compute V_eff = V_grav + L^2/(2I).

    Args:
        shape_state: Configuration in shape space
        masses: Body masses
        L_magnitude: |L| (conserved angular momentum)
        G: Gravitational constant

    Returns:
        Effective potential (scalar)
    """
    # Gravitational potential
    cart_state = shape_to_cartesian_canonical(shape_state)
    V_grav = compute_potential_energy(cart_state, masses, G)

    # Moment of inertia
    I = compute_moment_of_inertia(cart_state, masses)

    # Centrifugal term
    V_centrifugal = L_magnitude**2 / (2 * I)

    return V_grav + V_centrifugal
```

#### A4: Jacobi-Maupertuis Metric

```python
def compute_jm_metric(
    shape_state: ShapeSpaceState,
    masses: Masses,
    energy: float,
    L_magnitude: float = 0.0
) -> RiemannianMetric:
    """
    Compute JM metric: g_JM = 2(E - V_eff) g_shape.

    Args:
        shape_state: Point in shape space
        masses: Body masses
        energy: Total energy E
        L_magnitude: Angular momentum magnitude

    Returns:
        JM metric tensor (3x3 for planar case)

    Raises:
        ValueError: If E <= V_eff (classically forbidden region)
    """
    # Shape space metric
    g_shape = compute_shape_space_metric(shape_state, masses)

    # Effective potential
    V_eff = compute_effective_potential(shape_state, masses, L_magnitude)

    # Check classical accessibility
    if energy <= V_eff:
        raise ValueError(
            f"Classically forbidden: E={energy:.6f} <= V_eff={V_eff:.6f}"
        )

    # JM metric
    conformal_factor = 2 * (energy - V_eff)
    g_jm = conformal_factor * g_shape.components

    return RiemannianMetric(
        components=g_jm,
        coordinate_names=g_shape.coordinate_names,
        base_point=shape_state
    )
```

#### A5: Christoffel Symbols

```python
def compute_christoffel_symbols(
    metric: RiemannianMetric,
    metric_derivatives: np.ndarray
) -> ChristoffelSymbols:
    """
    Compute Christoffel symbols from metric and its derivatives.

    Γ^k_ij = (1/2) g^kl (∂_i g_jl + ∂_j g_il - ∂_l g_ij)

    Args:
        metric: Metric tensor g_ij (n x n)
        metric_derivatives: ∂g_ij/∂x^k (n x n x n)

    Returns:
        ChristoffelSymbols object
    """
    g = metric.components
    g_inv = metric.inverse()
    dg = metric_derivatives  # dg[k, i, j] = ∂g_ij/∂x^k

    n = g.shape[0]
    christoffel = np.zeros((n, n, n))

    for k in range(n):
        for i in range(n):
            for j in range(n):
                # Sum over l: g^kl (...)
                for l in range(n):
                    term = (dg[i, j, l] + dg[j, i, l] - dg[l, i, j])
                    christoffel[k, i, j] += 0.5 * g_inv[k, l] * term

    return ChristoffelSymbols(
        symbols=christoffel,
        coordinate_names=metric.coordinate_names,
        base_point=metric.base_point
    )
```

### Numerical Derivatives of Metric

Since we can evaluate $g_{ij}(s)$ at any point, we compute derivatives via finite differences:

```python
def compute_metric_derivatives(
    metric_func: Callable[[ShapeSpaceState], RiemannianMetric],
    base_state: ShapeSpaceState,
    epsilon: float = 1e-6
) -> np.ndarray:
    """
    Compute ∂g_ij/∂x^k using central differences.

    Returns:
        3D array dg[k, i, j] = ∂g_ij/∂x^k
    """
    g_base = metric_func(base_state)
    n = g_base.components.shape[0]

    dg = np.zeros((n, n, n))

    for k in range(n):
        # Perturb k-th coordinate
        state_plus = perturb_shape_coordinate(base_state, k, epsilon)
        state_minus = perturb_shape_coordinate(base_state, k, -epsilon)

        g_plus = metric_func(state_plus)
        g_minus = metric_func(state_minus)

        # Central difference
        dg[k, :, :] = (g_plus.components - g_minus.components) / (2 * epsilon)

    return dg
```

---

## Part B: Curvature Analysis

### Objectives

1. Compute Ricci tensor $R_{ij}$ from Christoffel symbols
2. Compute scalar curvature $R = g^{ij} R_{ij}$
3. Analyze spatial distribution of $R$ in shape space
4. Identify chaos-curvature correlation

### Key Algorithms

#### B1: Ricci Tensor

```python
def compute_ricci_tensor(
    christoffel: ChristoffelSymbols,
    christoffel_derivatives: np.ndarray
) -> np.ndarray:
    """
    Compute Ricci tensor R_ij from Christoffel symbols.

    R_ij = ∂_k Γ^k_ij - ∂_j Γ^k_ik + Γ^k_ij Γ^l_kl - Γ^k_il Γ^l_jk

    Args:
        christoffel: Γ^k_ij
        christoffel_derivatives: ∂Γ^k_ij/∂x^l

    Returns:
        Ricci tensor R_ij (n x n symmetric matrix)
    """
    Gamma = christoffel.symbols
    dGamma = christoffel_derivatives  # dGamma[l, k, i, j] = ∂Γ^k_ij/∂x^l

    n = Gamma.shape[0]
    ricci = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            # First two terms: derivatives
            for k in range(n):
                ricci[i, j] += dGamma[k, k, i, j]  # ∂_k Γ^k_ij
                ricci[i, j] -= dGamma[j, k, i, k]  # -∂_j Γ^k_ik

            # Last two terms: quadratic in Christoffel
            for k in range(n):
                for l in range(n):
                    ricci[i, j] += Gamma[k, i, j] * Gamma[l, k, l]
                    ricci[i, j] -= Gamma[k, i, l] * Gamma[l, j, k]

    return ricci
```

#### B2: Scalar Curvature

```python
def compute_scalar_curvature(
    metric: RiemannianMetric,
    ricci: np.ndarray
) -> float:
    """
    Compute scalar curvature R = g^ij R_ij.

    Args:
        metric: Metric tensor g_ij
        ricci: Ricci tensor R_ij

    Returns:
        Scalar curvature (float)
    """
    g_inv = metric.inverse()

    # Trace: R = g^ij R_ij
    R = np.trace(g_inv @ ricci)

    return R
```

#### B3: Complete Curvature Pipeline

```python
def compute_curvature_tensors(
    shape_state: ShapeSpaceState,
    masses: Masses,
    energy: float,
    L_magnitude: float = 0.0
) -> CurvatureTensors:
    """
    Complete pipeline: state → metric → Christoffel → curvature.

    Args:
        shape_state: Point in shape space
        masses, energy, L_magnitude: System parameters

    Returns:
        CurvatureTensors with Ricci and scalar curvature
    """
    # 1. Compute JM metric
    metric = compute_jm_metric(shape_state, masses, energy, L_magnitude)

    # 2. Compute metric derivatives (finite differences)
    metric_func = lambda s: compute_jm_metric(s, masses, energy, L_magnitude)
    dg = compute_metric_derivatives(metric_func, shape_state)

    # 3. Compute Christoffel symbols
    christoffel = compute_christoffel_symbols(metric, dg)

    # 4. Compute Christoffel derivatives (second-order finite differences)
    christoffel_func = lambda s: compute_christoffel_symbols(
        metric_func(s),
        compute_metric_derivatives(metric_func, s)
    )
    dGamma = compute_christoffel_derivatives(christoffel_func, shape_state)

    # 5. Compute Ricci tensor
    ricci = compute_ricci_tensor(christoffel, dGamma)

    # 6. Compute scalar curvature
    R = compute_scalar_curvature(metric, ricci)

    return CurvatureTensors(
        ricci=ricci,
        scalar=R
    )
```

#### B4: Chaos Indicator Correlation

```python
def compute_lyapunov_exponent(
    state0: CartesianState,
    masses: Masses,
    integration_time: float
) -> float:
    """
    Compute maximal Lyapunov exponent for trajectory.

    Uses tangent space integration (variational equations).

    Returns:
        λ_max (positive for chaos)
    """
    # Integrate main trajectory + tangent vector
    # (Implementation details in chaos_indicators.py)
    pass


def correlate_curvature_with_chaos(
    shape_states: list[ShapeSpaceState],
    masses: Masses,
    energy: float
) -> dict:
    """
    Compute R and λ at many points, analyze correlation.

    Returns:
        Dictionary with:
            - curvatures: Array of R values
            - lyapunov_exponents: Array of λ values
            - correlation_coefficient: Pearson r
            - p_value: Statistical significance
    """
    n = len(shape_states)
    curvatures = np.zeros(n)
    lyapunov_exponents = np.zeros(n)

    for i, state in enumerate(shape_states):
        # Scalar curvature
        curv = compute_curvature_tensors(state, masses, energy)
        curvatures[i] = curv.scalar

        # Lyapunov exponent
        cart_state = shape_to_cartesian_canonical(state)
        lyapunov_exponents[i] = compute_lyapunov_exponent(
            cart_state, masses, integration_time=100.0
        )

    # Correlation analysis
    from scipy.stats import pearsonr
    r, p_value = pearsonr(curvatures, lyapunov_exponents)

    return {
        'curvatures': curvatures,
        'lyapunov_exponents': lyapunov_exponents,
        'correlation_coefficient': r,
        'p_value': p_value
    }
```

---

## Part C: Visualization and Exploration

### Objectives

1. Visualize metric tensor as ellipsoids
2. Plot curvature landscapes (3D surfaces)
3. Create interactive exploration tools
4. Generate publication-quality figures

### Key Visualizations

#### C1: Metric Ellipsoids

```python
def plot_metric_ellipsoids(
    masses: Masses,
    energy: float,
    shape_space_grid: np.ndarray
):
    """
    Visualize metric as ellipsoids at grid points.

    The metric tensor defines an ellipsoid at each point—larger ellipsoids
    indicate "easier" motion in that direction.
    """
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    from matplotlib.patches import Ellipse

    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')

    for state in shape_space_grid:
        metric = compute_jm_metric(state, masses, energy)

        # Eigendecomposition
        eigenvalues, eigenvectors = np.linalg.eigh(metric.components)

        # Draw ellipsoid
        draw_ellipsoid_3d(
            ax,
            center=(state.r12, state.r23, state.r31),
            radii=np.sqrt(eigenvalues),
            rotation=eigenvectors,
            color='blue',
            alpha=0.3
        )

    ax.set_xlabel('$r_{12}$')
    ax.set_ylabel('$r_{23}$')
    ax.set_zlabel('$r_{31}$')
    ax.set_title('JM Metric Tensor Field')

    plt.show()
```

#### C2: Curvature Landscape

```python
def plot_curvature_landscape(
    masses: Masses,
    energy: float,
    shape_space_region: tuple
):
    """
    Plot scalar curvature R as a 3D surface.

    Negative regions (R < 0) indicate chaotic dynamics.
    """
    # Create grid
    r12_range, r23_range = shape_space_region
    r12_grid = np.linspace(*r12_range, 50)
    r23_grid = np.linspace(*r23_range, 50)

    R_grid = np.zeros((50, 50))

    for i, r12 in enumerate(r12_grid):
        for j, r23 in enumerate(r23_grid):
            # Fix r31 to satisfy triangle inequality
            r31 = (r12 + r23) / 2.0  # Midpoint (valid if r12 + r23 > r31)

            state = ShapeSpaceState(r12=r12, r23=r23, r31=r31, L=1.0)

            try:
                curv = compute_curvature_tensors(state, masses, energy)
                R_grid[i, j] = curv.scalar
            except ValueError:
                # Classically forbidden or invalid triangle
                R_grid[i, j] = np.nan

    # Plot
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D

    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')

    X, Y = np.meshgrid(r12_grid, r23_grid)
    surf = ax.plot_surface(X, Y, R_grid.T,
                            cmap='RdBu_r',  # Red for negative, blue for positive
                            vmin=-np.nanmax(np.abs(R_grid)),
                            vmax=np.nanmax(np.abs(R_grid)),
                            alpha=0.9)

    # Add zero plane
    ax.plot_surface(X, Y, np.zeros_like(R_grid.T),
                    color='gray', alpha=0.2)

    fig.colorbar(surf, ax=ax, shrink=0.5, label='Scalar Curvature $R$')

    ax.set_xlabel('$r_{12}$')
    ax.set_ylabel('$r_{23}$')
    ax.set_zlabel('$R$')
    ax.set_title('Scalar Curvature Landscape')

    plt.show()
```

#### C3: Interactive Explorer

```python
def create_interactive_curvature_explorer():
    """
    Interactive widget to explore curvature as parameters change.
    """
    import ipywidgets as widgets
    from IPython.display import display

    @widgets.interact(
        m1=widgets.FloatSlider(min=0.5, max=3.0, step=0.1, value=1.0),
        m2=widgets.FloatSlider(min=0.5, max=3.0, step=0.1, value=1.0),
        m3=widgets.FloatSlider(min=0.5, max=3.0, step=0.1, value=1.0),
        energy=widgets.FloatSlider(min=-2.0, max=-0.1, step=0.1, value=-1.0),
        L=widgets.FloatSlider(min=0.0, max=3.0, step=0.1, value=1.0)
    )
    def plot(m1, m2, m3, energy, L):
        masses = Masses(m1, m2, m3)

        # Create sample point
        state = ShapeSpaceState(r12=1.0, r23=1.0, r31=1.0, L=L)

        try:
            curv = compute_curvature_tensors(state, masses, energy, L)

            print(f"Scalar Curvature R = {curv.scalar:.6f}")
            print(f"Sign: {'NEGATIVE (chaotic)' if curv.is_negative else 'POSITIVE (regular)'}")

            # Plot metric eigenvalues
            metric = compute_jm_metric(state, masses, energy, L)
            eigenvals = metric.eigenvalues()

            fig, ax = plt.subplots(figsize=(8, 6))
            ax.bar(['λ₁', 'λ₂', 'λ₃'], eigenvals)
            ax.set_ylabel('Eigenvalue')
            ax.set_title('JM Metric Principal Lengths')
            plt.show()

        except ValueError as e:
            print(f"Error: {e}")
```

---

## Part D: Scientific Analysis and Validation

### Objectives

1. Validate curvature computation against known cases
2. Confirm chaos-curvature correlation hypothesis
3. Classify shape space regions (regular vs. chaotic)
4. Generate scientific publication material

### Validation Test Cases

#### D1: Two-Body Limit

For $m_3 \to 0$, the system reduces to the Kepler problem, which has **zero curvature** (flat space):

```python
def test_kepler_limit():
    """
    Verify R → 0 as m3 → 0 (Kepler problem is integrable).
    """
    m1, m2 = 1.0, 1.0

    curvatures = []
    m3_values = np.logspace(-5, -1, 20)  # 10^-5 to 10^-1

    for m3 in m3_values:
        masses = Masses(m1, m2, m3)
        state = create_test_state()  # Some fixed configuration

        curv = compute_curvature_tensors(state, masses, energy=-1.0)
        curvatures.append(curv.scalar)

    # Should approach zero
    assert abs(curvatures[-1]) < 1e-6, "Curvature should vanish in Kepler limit"

    # Plot convergence
    plt.loglog(m3_values, np.abs(curvatures))
    plt.xlabel('$m_3$')
    plt.ylabel('$|R|$')
    plt.title('Curvature → 0 as $m_3 \\to 0$')
    plt.show()
```

#### D2: Equal Mass Symmetry

For equal masses, curvature should be symmetric under permutations:

```python
def test_equal_mass_symmetry():
    """
    Verify R invariant under body label permutation.
    """
    masses = Masses(1.0, 1.0, 1.0)

    # Three equivalent configurations (permuted labels)
    state1 = ShapeSpaceState(r12=1.0, r23=1.2, r31=1.4, L=1.0)
    state2 = ShapeSpaceState(r12=1.2, r23=1.4, r31=1.0, L=1.0)  # Permuted
    state3 = ShapeSpaceState(r12=1.4, r23=1.0, r31=1.2, L=1.0)  # Permuted

    R1 = compute_curvature_tensors(state1, masses, energy=-1.0).scalar
    R2 = compute_curvature_tensors(state2, masses, energy=-1.0).scalar
    R3 = compute_curvature_tensors(state3, masses, energy=-1.0).scalar

    assert abs(R1 - R2) < 1e-10
    assert abs(R2 - R3) < 1e-10
```

#### D3: Chaos-Curvature Correlation

Main scientific result:

```python
def validate_chaos_curvature_hypothesis():
    """
    Test: R < 0 ⟺ λ_max > 0 (negative curvature ⟺ chaos).

    This is the central scientific validation.
    """
    masses = Masses(1.0, 1.0, 1.0)  # Equal masses
    energy = -1.0

    # Sample 1000 random initial conditions
    n_samples = 1000
    states = generate_random_shape_states(n_samples)

    results = correlate_curvature_with_chaos(states, masses, energy)

    # Extract data
    R = results['curvatures']
    lambda_max = results['lyapunov_exponents']

    # Classification
    chaotic = lambda_max > 0.01  # Threshold for chaos
    negative_curvature = R < 0

    # Confusion matrix
    true_positive = np.sum(chaotic & negative_curvature)
    false_positive = np.sum(~chaotic & negative_curvature)
    true_negative = np.sum(~chaotic & ~negative_curvature)
    false_negative = np.sum(chaotic & ~negative_curvature)

    accuracy = (true_positive + true_negative) / n_samples

    print(f"Chaos-Curvature Correlation Analysis")
    print(f"=" * 50)
    print(f"Correlation coefficient: r = {results['correlation_coefficient']:.4f}")
    print(f"p-value: {results['p_value']:.3e}")
    print(f"\nClassification Accuracy: {accuracy*100:.1f}%")
    print(f"  True Positives:  {true_positive}")
    print(f"  False Positives: {false_positive}")
    print(f"  True Negatives:  {true_negative}")
    print(f"  False Negatives: {false_negative}")

    # Scatter plot
    plt.figure(figsize=(10, 8))
    plt.scatter(R, lambda_max, alpha=0.5, c=chaotic, cmap='RdYlGn_r')
    plt.axvline(0, color='k', linestyle='--', alpha=0.3, label='R=0')
    plt.axhline(0, color='k', linestyle='--', alpha=0.3, label='λ=0')
    plt.xlabel('Scalar Curvature $R$')
    plt.ylabel('Maximal Lyapunov Exponent $\\lambda_{max}$')
    plt.title('Chaos-Curvature Correlation')
    plt.colorbar(label='Chaotic')
    plt.legend()
    plt.show()

    return accuracy > 0.8  # Expect >80% accuracy
```

---

## Integration with Existing Infrastructure

### Dependencies

- **Task 2.1.1**: Shape space coordinates, transformations
- **WP1**: High-precision integrators (for Lyapunov computation)
- **Optional Task 2.1.2**: Connection form (for consistency checks)

### Outputs

- Curvature field data for WP3 (guides symmetry search)
- Chaos classification for region analysis
- Visualizations for scientific publication

---

## Implementation Schedule

### Phase 1: Metric Implementation (2 days)
- **Day 1**: Mass metric, shape space pullback
- **Day 2**: JM metric, Christoffel symbols

### Phase 2: Curvature Computation (2 days)
- **Day 3**: Ricci tensor implementation
- **Day 4**: Scalar curvature, validation tests

### Phase 3: Chaos Indicators (2 days)
- **Day 5**: Lyapunov exponent computation (tangent space integration)
- **Day 6**: Correlation analysis pipeline

### Phase 4: Visualization (1 day)
- **Day 7**: Metric ellipsoids, curvature landscapes

### Phase 5: Scientific Analysis (1 day)
- **Day 8**: Hypothesis validation, publication figures

**Total**: 8 days (can compress to 6 with efficient parallelization)

---

## Success Criteria

### Functional Requirements
- [ ] JM metric computable at arbitrary shape space points
- [ ] Scalar curvature $R$ computed with validated accuracy
- [ ] Chaos-curvature correlation confirmed ($r > 0.7$)
- [ ] All test cases pass (Kepler limit, symmetries)

### Performance Requirements
- [ ] Metric evaluation: < 10 μs per point
- [ ] Curvature evaluation: < 10 ms per point
- [ ] Lyapunov exponent: < 30 seconds per trajectory

### Scientific Requirements
- [ ] Confirm $R < 0$ for planar equal-mass 3BP in chaotic regions
- [ ] Classification accuracy > 80% (R sign predicts chaos)
- [ ] Publication-quality figures generated

### Quality Requirements
- [ ] Test coverage > 95%
- [ ] Complete API documentation
- [ ] Technical report section written

---

## Risk Mitigation

### Risk 1: Numerical Instability in Curvature
**Mitigation**: Second-order finite differences are notoriously unstable. Use:
- Symbolic differentiation (SymPy) where possible
- Richardson extrapolation for improved accuracy
- Adaptive step size based on local metric variation

### Risk 2: Computational Cost
**Mitigation**:
- Curvature requires many function evaluations (expensive)
- Use interpolation from precomputed grid
- Parallelize over grid points

### Risk 3: Weak Chaos-Curvature Correlation
**Mitigation**: If correlation is weak:
- Investigate sectional curvatures (direction-dependent)
- Consider Ricci curvature instead of scalar
- Examine higher-order chaos indicators (MEGNO, FLI)

---

## References

1. Gutzwiller, *Chaos in Classical and Quantum Mechanics* (1990) - Metric geometry
2. Casetti et al., "Geometric approach to Hamiltonian dynamics and statistical mechanics" (2000)
3. Pettini, *Geometry and Topology in Hamiltonian Dynamics* (2007)
4. Hadeler, "Curvature and chaos" (1994)

---

**Document Version**: 1.0
**Last Updated**: 2025-11-13
**Next Review**: After Part A implementation
**Dependencies**: Task 2.1.1 Complete
