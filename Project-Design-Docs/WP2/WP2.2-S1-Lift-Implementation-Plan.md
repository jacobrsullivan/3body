# WP 2.2: S¹ "Untwisting" Lift Construction
## Work Package 2 - Geometric Reduction and Shape Space Analysis

**Status**: Design Phase
**Priority**: Critical Path for Lift-Integrability Hypothesis
**Estimated Duration**: 10-12 days
**Dependencies**: Task 2.1.2 Complete (Connection and Curvature)

---

## Table of Contents

1. [Overview](#overview)
2. [Mathematical Background](#mathematical-background)
3. [Implementation Architecture](#implementation-architecture)
4. [Part A: Principal Bundle Construction](#part-a-principal-bundle-construction)
5. [Part B: Extended Symplectic Form](#part-b-extended-symplectic-form)
6. [Part C: Lifted Dynamics and Integration](#part-c-lifted-dynamics-and-integration)
7. [Part D: Integrability Search](#part-d-integrability-search)
8. [Integration with Existing Infrastructure](#integration-with-existing-infrastructure)
9. [Implementation Schedule](#implementation-schedule)
10. [Success Criteria](#success-criteria)

---

## Overview

### Purpose

WP 2.2 implements the **S¹ "untwisting" lift** — a minimal dimensional increase that attempts to eliminate the magnetic connection by working in an extended phase space. This is the first concrete test of the **lift-integrability hypothesis**: that the three-body problem may be integrable "upstairs" in a higher-dimensional space, even though it's non-integrable "downstairs" in shape space.

**Geometric Idea**: The connection one-form $\mathcal{A}$ discovered in Task 2.1.2 acts like a "magnetic field" on shape space. By constructing a principal S¹ bundle and introducing a compensating "gauge field," we can create a new phase space where dynamics becomes simpler—potentially integrable.

**Physical Interpretation**: The S¹ fiber represents the "twist" or "winding" accumulated as we move through shape space. By explicitly tracking this winding as a new coordinate, we "untwist" the dynamics.

### Objectives

1. **Bundle Construction**: Build principal S¹ bundle $P = S \times S^1$ over shape space $S$
2. **Connection Form Extension**: Lift the connection $\mathcal{A}$ to bundle space as $\widetilde{\mathcal{A}}$
3. **Symplectic Extension**: Define extended symplectic form $\widetilde{\omega}$ on total space
4. **Lifted Hamiltonian**: Construct Hamiltonian flow on $P$
5. **Integrability Test**: Search for additional integrals of motion (beyond energy, angular momentum)
6. **Validation**: Compare lifted dynamics with original reduced dynamics via projection

### Deliverables

- **Deliverable 2.2.1**: S¹ bundle data structures and coordinate charts
- **Deliverable 2.2.2**: Extended symplectic form evaluator
- **Deliverable 2.2.3**: Lifted Hamiltonian integrator
- **Deliverable 2.2.4**: Integral search algorithms (candidate functions + validation)
- **Deliverable 2.2.5**: Projection validation: $\pi(\text{lifted trajectory}) = \text{reduced trajectory}$
- **Deliverable 2.2.6**: Technical report: "S¹ Lift Integrability Analysis"

---

## Mathematical Background

### The Problem: Non-Integrable Reduced Dynamics

From Task 2.1.2, we know:
- Shape space has dimension $\dim(S) = 3$ (planar case after rotation reduction)
- The reduced symplectic form is: $\omega_{\text{red}} = \omega_{\text{shape}} - d(L \cdot \mathcal{A})$
- The curvature $\mathcal{F} = d\mathcal{A} \neq 0$ obstructs integrability

For integrability, we need:
- 3 independent integrals in involution: $\{F_1, F_2, F_3\} = 0$
- Only have 2: Energy $E$ and angular momentum $L$
- Need 1 more, but $\mathcal{F} \neq 0$ suggests none exists "downstairs"

### The Solution: Lift to Principal Bundle

**Construction**: Define a principal S¹ bundle:
$$
S^1 \hookrightarrow P \xrightarrow{\pi} S
$$

where:
- Base space: $S$ = shape space (3D)
- Total space: $P = S \times S^1$ (4D)
- Fiber: $S^1 = \mathbb{R}/2\pi\mathbb{Z}$ (circle, 1D)
- Projection: $\pi(s, \theta) = s$

**Coordinates on Total Space**: $(s, \theta)$ where:
- $s = (r_{12}, r_{23}, r_{31})$ ∈ shape space
- $\theta$ ∈ $[0, 2\pi)$ = fiber coordinate ("gauge phase")

### Extended Symplectic Form

The key idea: extend the symplectic form to include the fiber:

$$
\widetilde{\omega} = \omega_{\text{shape}} + d\theta \wedge d(L \cdot \mathcal{A})
$$

**Remarkable Property**: This new form is **closed** even though the reduced form was not!

$$
d\widetilde{\omega} = d\omega_{\text{shape}} - d\theta \wedge d^2(L \cdot \mathcal{A}) = 0
$$

(since $d^2 = 0$ and $\omega_{\text{shape}}$ is closed)

**Physical Interpretation**: The fiber coordinate $\theta$ "absorbs" the curvature. The lifted space is symplectically simpler than the reduced space.

### Lifted Hamiltonian

The Hamiltonian on the bundle is simply the pullback:

$$
\widetilde{H}(s, \theta, p_s, p_\theta) = H_{\text{red}}(s, p_s)
$$

**Key Point**: $\widetilde{H}$ is **independent of $\theta$**! This immediately gives us:

$$
\{p_\theta, \widetilde{H}\} = -\frac{\partial \widetilde{H}}{\partial \theta} = 0
$$

So $p_\theta$ (conjugate momentum to fiber coordinate) is a **conserved quantity**—the third integral we need!

### Integrability Hypothesis

**Hypothesis**: In the S¹ lifted space, the system has:
1. Energy $E$ (from original Hamiltonian)
2. Angular momentum $L$ (from rotational symmetry)
3. Fiber momentum $p_\theta$ (new integral from S¹ symmetry)

If these three are in involution and functionally independent, the system is **integrable on $P$**.

**Test**: Compute Poisson brackets $\{E, L\}$, $\{E, p_\theta\}$, $\{L, p_\theta\}$ and verify = 0.

---

## Implementation Architecture

### Module Structure

```
src/python/lifts/
├── __init__.py                    # Package exports
├── s1_bundle.py                   # A: Principal S¹ bundle
├── bundle_coordinates.py          # A: Chart and transition functions
├── extended_symplectic.py         # B: Symplectic form on total space
├── lifted_hamiltonian.py          # C: Hamiltonian flow on bundle
├── connection_lift.py             # Helper: Lift connection to bundle
└── validation.py                  # Projection and consistency checks

src/python/integration/
├── bundle_integrator.py           # C: Integrate on S¹ × Shape Space
└── adaptive_bundle_step.py        # C: Adaptive stepping with constraints

src/python/analysis/
├── integral_search.py             # D: Search for additional integrals
├── poisson_bracket.py             # D: Compute {F, G} on bundle
├── functional_independence.py     # D: Test linear independence
└── involution_test.py             # D: Verify integrability conditions

tests/lifts/
├── test_s1_bundle.py              # Unit tests for bundle
├── test_extended_symplectic.py    # Symplectic form validation
├── test_lifted_dynamics.py        # Integration tests
└── test_integrability.py          # Scientific validation
```

### Data Structures

```python
@dataclass(frozen=True)
class BundleState:
    """
    State in the S¹ bundle P = Shape Space × S¹.

    Attributes:
        shape_state: Base space coordinates (r12, r23, r31)
        theta: Fiber coordinate (angle ∈ [0, 2π))
        shape_momenta: Momenta conjugate to shape coordinates
        p_theta: Momentum conjugate to fiber coordinate
    """
    shape_state: ShapeSpaceState
    theta: float  # Fiber coordinate ∈ [0, 2π)
    shape_momenta: np.ndarray  # (3,) for planar case
    p_theta: float  # Fiber momentum

    def __post_init__(self):
        """Normalize theta to [0, 2π)"""
        object.__setattr__(self, 'theta', self.theta % (2 * np.pi))

    @property
    def dimension(self) -> int:
        """Phase space dimension: 2 × (3 + 1) = 8"""
        return 2 * (len(self.shape_momenta) + 1)

    def to_vector(self) -> np.ndarray:
        """Flatten to vector [s, θ, p_s, p_θ]"""
        shape_coords = self.shape_state.to_array()
        return np.concatenate([
            shape_coords,
            [self.theta],
            self.shape_momenta,
            [self.p_theta]
        ])


@dataclass(frozen=True)
class ExtendedSymplecticForm:
    """
    Extended symplectic form on S¹ bundle.

    ω̃ = ω_shape + dθ ∧ d(L·A)
    """
    base_form: np.ndarray  # ω_shape (matrix in shape space)
    connection: ConnectionForm  # A from Task 2.1.2
    angular_momentum: float  # L (conserved)

    def evaluate(
        self,
        tangent_vector_1: np.ndarray,
        tangent_vector_2: np.ndarray
    ) -> float:
        """
        Evaluate ω̃(v₁, v₂) for tangent vectors.

        Args:
            tangent_vector_1, tangent_vector_2: Vectors in T(S × S¹)
                Format: [δs, δθ, δp_s, δp_θ]

        Returns:
            ω̃(v₁, v₂) (scalar)
        """
        # Split into shape and fiber components
        δs1, δθ1 = tangent_vector_1[:3], tangent_vector_1[3]
        δs2, δθ2 = tangent_vector_2[:3], tangent_vector_2[3]

        # Base form contribution: ω_shape(δs1, δs2)
        base_contrib = δs1 @ self.base_form @ δs2

        # Connection contribution: dθ ∧ d(L·A)
        # = δθ1 · d(L·A)(δs2) - δθ2 · d(L·A)(δs1)
        dA_1 = self.connection.derivative(δs1)
        dA_2 = self.connection.derivative(δs2)

        connection_contrib = self.angular_momentum * (
            δθ1 * dA_2 - δθ2 * dA_1
        )

        return base_contrib + connection_contrib


@dataclass(frozen=True)
class LiftedHamiltonian:
    """
    Hamiltonian on S¹ bundle (pullback of reduced Hamiltonian).

    H̃(s, θ, p_s, p_θ) = H_red(s, p_s)
    """
    reduced_hamiltonian: Callable  # H_red from shape space
    masses: Masses
    energy: float

    def evaluate(self, state: BundleState) -> float:
        """
        Evaluate H̃ at bundle state.

        Note: Independent of θ and p_θ!
        """
        return self.reduced_hamiltonian(
            state.shape_state,
            state.shape_momenta,
            self.masses,
            self.energy
        )

    def is_theta_independent(self) -> bool:
        """Verify ∂H̃/∂θ = 0"""
        return True  # By construction
```

---

## Part A: Principal Bundle Construction

### Objectives

1. Implement S¹ bundle data structures
2. Define local coordinate charts
3. Implement transition functions between charts
4. Validate bundle structure (cocycle conditions)

### Key Algorithms

#### A1: Bundle State Management

```python
class S1Bundle:
    """
    Principal S¹ bundle over shape space.

    P = S × S¹ where S is the 3D shape space (planar case).
    """

    def __init__(self, base_manifold: ShapeSpace):
        """
        Initialize S¹ bundle.

        Args:
            base_manifold: Shape space (base of bundle)
        """
        self.base = base_manifold
        self.fiber_dimension = 1  # S¹ is 1-dimensional

    @property
    def total_dimension(self) -> int:
        """Dimension of total space = dim(base) + dim(fiber)"""
        return self.base.dimension + self.fiber_dimension

    def create_state(
        self,
        shape_state: ShapeSpaceState,
        theta: float,
        shape_momenta: np.ndarray,
        p_theta: float
    ) -> BundleState:
        """
        Create a state in the bundle.

        Args:
            shape_state: Point in shape space
            theta: Fiber coordinate (angle)
            shape_momenta: Momenta in base space
            p_theta: Fiber momentum

        Returns:
            BundleState
        """
        return BundleState(
            shape_state=shape_state,
            theta=theta,
            shape_momenta=shape_momenta,
            p_theta=p_theta
        )

    def project_to_base(self, bundle_state: BundleState) -> ShapeSpaceState:
        """
        Projection π: P → S.

        Simply drop the fiber coordinate.
        """
        return bundle_state.shape_state

    def fiber_over_point(
        self,
        base_point: ShapeSpaceState
    ) -> list[BundleState]:
        """
        Return fiber π⁻¹(s) over a base point.

        This is a circle: all states with fixed shape, varying θ.

        Args:
            base_point: Point in shape space

        Returns:
            List of states representing fiber (discrete sample)
        """
        n_fiber_points = 100
        theta_values = np.linspace(0, 2*np.pi, n_fiber_points, endpoint=False)

        return [
            BundleState(
                shape_state=base_point,
                theta=theta,
                shape_momenta=np.zeros(3),  # Zero momenta
                p_theta=0.0
            )
            for theta in theta_values
        ]
```

#### A2: Local Trivialization

For a principal bundle, we need coordinate charts $U \times S^1$ covering the total space:

```python
class BundleChart:
    """
    Local coordinate chart for S¹ bundle.

    Chart: φ: π⁻¹(U) → U × S¹
    where U ⊂ Shape Space is an open set.
    """

    def __init__(
        self,
        base_chart_domain: Callable[[ShapeSpaceState], bool],
        name: str = "Chart"
    ):
        """
        Initialize chart.

        Args:
            base_chart_domain: Function determining if point is in U
            name: Chart identifier
        """
        self.domain = base_chart_domain
        self.name = name

    def is_in_domain(self, state: BundleState) -> bool:
        """Check if state is in chart domain"""
        return self.domain(state.shape_state)

    def coordinates(self, state: BundleState) -> tuple:
        """
        Chart map: state → (s, θ) coordinates.

        Args:
            state: Point in bundle

        Returns:
            (shape_coords, theta) tuple
        """
        if not self.is_in_domain(state):
            raise ValueError(f"State not in domain of {self.name}")

        return (state.shape_state.to_array(), state.theta)

    def from_coordinates(
        self,
        shape_coords: np.ndarray,
        theta: float
    ) -> BundleState:
        """
        Inverse chart map: (s, θ) → state.

        Args:
            shape_coords: Shape space coordinates
            theta: Fiber coordinate

        Returns:
            BundleState
        """
        shape_state = ShapeSpaceState.from_array(shape_coords)

        return BundleState(
            shape_state=shape_state,
            theta=theta,
            shape_momenta=np.zeros(len(shape_coords)),
            p_theta=0.0
        )
```

#### A3: Transition Functions

When two charts overlap, we need transition functions:

```python
def compute_transition_function(
    chart1: BundleChart,
    chart2: BundleChart,
    state: BundleState
) -> tuple[np.ndarray, float]:
    """
    Transition function between overlapping charts.

    For a principal S¹ bundle, transition functions have form:
        (s, θ) ↦ (s, θ + α(s))

    where α(s) is a "gauge transformation."

    Args:
        chart1, chart2: Overlapping charts
        state: Point in overlap region

    Returns:
        (shape_coords, theta_transformed) in chart2 coordinates
    """
    # Verify state is in overlap
    assert chart1.is_in_domain(state) and chart2.is_in_domain(state)

    # Get coordinates in chart1
    shape_coords, theta1 = chart1.coordinates(state)

    # Compute gauge transformation α(s)
    # (This depends on how charts are defined; for trivial bundle, α = 0)
    alpha = compute_gauge_transformation(shape_coords, chart1, chart2)

    # Transform fiber coordinate
    theta2 = (theta1 + alpha) % (2 * np.pi)

    return shape_coords, theta2


def compute_gauge_transformation(
    shape_coords: np.ndarray,
    chart1: BundleChart,
    chart2: BundleChart
) -> float:
    """
    Compute gauge transformation α(s) between charts.

    For S¹ bundle over contractible base, can choose α = 0 (trivial bundle).
    For non-contractible base, α may be non-trivial.

    Args:
        shape_coords: Point in shape space
        chart1, chart2: Charts

    Returns:
        Gauge transformation angle α
    """
    # For now: trivial bundle (contractible shape space)
    return 0.0
```

### Validation Tests

#### A4: Bundle Structure Validation

```python
def test_projection_property():
    """
    Verify π ∘ φ⁻¹ = projection to first factor.

    For chart φ: π⁻¹(U) → U × S¹, we should have π(φ⁻¹(s, θ)) = s.
    """
    bundle = S1Bundle(ShapeSpace())
    chart = BundleChart(lambda s: True)  # Trivial chart over all of S

    # Create random bundle state
    shape_state = random_shape_state()
    theta = np.random.uniform(0, 2*np.pi)
    state = bundle.create_state(shape_state, theta, np.zeros(3), 0.0)

    # Project to base
    projected = bundle.project_to_base(state)

    # Should equal original shape_state
    assert np.allclose(
        projected.to_array(),
        shape_state.to_array()
    )


def test_fiber_structure():
    """
    Verify fiber π⁻¹(s) is diffeomorphic to S¹.

    All points in fiber should project to same base point.
    """
    bundle = S1Bundle(ShapeSpace())
    base_point = random_shape_state()

    fiber = bundle.fiber_over_point(base_point)

    # All should project to base_point
    for state in fiber:
        projected = bundle.project_to_base(state)
        assert np.allclose(
            projected.to_array(),
            base_point.to_array()
        )

    # Fiber should have S¹ topology (closed loop)
    theta_values = [s.theta for s in fiber]
    assert min(theta_values) >= 0
    assert max(theta_values) < 2*np.pi
    # Should be approximately evenly distributed
```

---

## Part B: Extended Symplectic Form

### Objectives

1. Implement extended symplectic form $\widetilde{\omega}$
2. Verify closedness: $d\widetilde{\omega} = 0$
3. Verify non-degeneracy
4. Compute Poisson brackets on bundle

### Key Algorithms

#### B1: Extended Symplectic Form Evaluation

```python
def compute_extended_symplectic_form(
    bundle_state: BundleState,
    connection: ConnectionForm,
    angular_momentum: float
) -> ExtendedSymplecticForm:
    """
    Compute extended symplectic form at a bundle point.

    ω̃ = ω_shape + dθ ∧ d(L·A)

    Args:
        bundle_state: Point in bundle
        connection: Connection one-form from Task 2.1.2
        angular_momentum: Conserved L

    Returns:
        ExtendedSymplecticForm object
    """
    # Base symplectic form on shape space
    # (This is the canonical form: dp ∧ dq)
    n = len(bundle_state.shape_momenta)
    omega_shape = np.block([
        [np.zeros((n, n)), np.eye(n)],
        [-np.eye(n), np.zeros((n, n))]
    ])

    return ExtendedSymplecticForm(
        base_form=omega_shape,
        connection=connection,
        angular_momentum=angular_momentum
    )
```

#### B2: Closedness Verification

```python
def verify_extended_form_closed(
    extended_form: ExtendedSymplecticForm,
    bundle_state: BundleState,
    epsilon: float = 1e-6
) -> bool:
    """
    Verify dω̃ = 0 numerically.

    Uses Stokes' theorem on small 3D region.

    Args:
        extended_form: Symplectic form to test
        bundle_state: Base point for test
        epsilon: Size of test region

    Returns:
        True if closed (within numerical tolerance)
    """
    # Create small 3-cube around bundle_state
    # Integrate ω̃ over boundary (2D surfaces)
    boundary_integral = compute_boundary_integral_2form(
        extended_form,
        bundle_state,
        epsilon
    )

    # If dω̃ = 0, boundary integral should vanish
    return abs(boundary_integral) < 1e-10


def compute_exterior_derivative_2form(
    form: ExtendedSymplecticForm,
    bundle_state: BundleState
) -> np.ndarray:
    """
    Compute dω̃ (should be zero).

    For a 2-form in n dimensions, dω is a 3-form.

    Returns:
        Components of dω̃ (should all be ≈ 0)
    """
    # Compute using Cartan's formula: dω = exterior derivative
    # (Implementation requires careful indexing)

    # For our specific form ω̃ = ω_shape + dθ ∧ d(L·A):
    # d(ω_shape) = 0 (canonical form is closed)
    # d(dθ ∧ d(L·A)) = dθ ∧ d²(L·A) = 0 (since d² = 0)

    # Therefore dω̃ = 0 exactly!
    return np.zeros((4, 4, 4))  # 3-form components (all zero)
```

#### B3: Poisson Brackets on Bundle

```python
def poisson_bracket_on_bundle(
    f: Callable[[BundleState], float],
    g: Callable[[BundleState], float],
    state: BundleState,
    symplectic_form: ExtendedSymplecticForm
) -> float:
    """
    Compute {f, g} with respect to extended symplectic form.

    {f, g} = ω̃(X_f, X_g)

    where X_f is the Hamiltonian vector field of f.

    Args:
        f, g: Functions on bundle
        state: Point where to evaluate bracket
        symplectic_form: Extended form

    Returns:
        {f, g} (scalar)
    """
    # Compute gradients (covector)
    df = compute_gradient(f, state)
    dg = compute_gradient(g, state)

    # Convert to Hamiltonian vector fields using symplectic form
    # X_f = ω̃⁻¹(df, ·)
    omega_matrix = symplectic_form.to_matrix()
    omega_inv = np.linalg.inv(omega_matrix)

    X_f = omega_inv @ df
    X_g = omega_inv @ dg

    # Poisson bracket: {f, g} = ω̃(X_f, X_g) = df(X_g)
    bracket = df @ X_g

    return bracket
```

---

## Part C: Lifted Dynamics and Integration

### Objectives

1. Implement Hamiltonian equations on bundle
2. Integrate bundle dynamics
3. Verify conservation of fiber momentum $p_\theta$
4. Project back to shape space and compare

### Key Algorithms

#### C1: Hamilton's Equations on Bundle

```python
def hamiltonian_vector_field_bundle(
    state: BundleState,
    lifted_hamiltonian: LiftedHamiltonian,
    symplectic_form: ExtendedSymplecticForm
) -> np.ndarray:
    """
    Compute Hamiltonian vector field on bundle.

    Hamilton's equations: ẋ = ω̃⁻¹(dH̃)

    Args:
        state: Current bundle state
        lifted_hamiltonian: H̃
        symplectic_form: ω̃

    Returns:
        Derivative [ṡ, θ̇, ṗ_s, ṗ_θ]
    """
    # Compute gradient of Hamiltonian
    dH = compute_gradient(
        lambda s: lifted_hamiltonian.evaluate(s),
        state
    )

    # Symplectic form (as matrix)
    omega = symplectic_form.to_matrix()
    omega_inv = np.linalg.inv(omega)

    # Vector field: X_H̃ = ω̃⁻¹(dH̃)
    X_H = omega_inv @ dH

    return X_H


def integrate_bundle_dynamics(
    initial_state: BundleState,
    lifted_hamiltonian: LiftedHamiltonian,
    symplectic_form: ExtendedSymplecticForm,
    t_span: tuple[float, float],
    **integrator_options
) -> BundleTrajectory:
    """
    Integrate dynamics on S¹ bundle.

    Args:
        initial_state: Initial condition
        lifted_hamiltonian: H̃
        symplectic_form: ω̃
        t_span: (t_start, t_end)

    Returns:
        Trajectory in bundle space
    """
    from scipy.integrate import solve_ivp

    # Define ODE: dz/dt = X_H̃(z)
    def rhs(t, z):
        state = BundleState.from_vector(z)
        return hamiltonian_vector_field_bundle(
            state, lifted_hamiltonian, symplectic_form
        )

    # Integrate
    z0 = initial_state.to_vector()
    solution = solve_ivp(
        rhs,
        t_span,
        z0,
        method='DOP853',  # High-order adaptive method
        **integrator_options
    )

    # Convert to trajectory
    states = [BundleState.from_vector(z) for z in solution.y.T]

    return BundleTrajectory(
        times=solution.t,
        states=states,
        initial_state=initial_state
    )
```

#### C2: Conservation Verification

```python
def verify_conservation_on_bundle(
    trajectory: BundleTrajectory,
    lifted_hamiltonian: LiftedHamiltonian
) -> dict:
    """
    Verify conservation laws on bundle trajectory.

    Should conserve:
        1. Energy: H̃ = constant
        2. Fiber momentum: p_θ = constant (since ∂H̃/∂θ = 0)

    Args:
        trajectory: Integrated trajectory
        lifted_hamiltonian: Hamiltonian

    Returns:
        Dictionary with conservation errors
    """
    n = len(trajectory.states)

    energies = np.zeros(n)
    fiber_momenta = np.zeros(n)

    for i, state in enumerate(trajectory.states):
        energies[i] = lifted_hamiltonian.evaluate(state)
        fiber_momenta[i] = state.p_theta

    # Compute drifts
    energy_drift = np.max(np.abs(energies - energies[0]))
    p_theta_drift = np.max(np.abs(fiber_momenta - fiber_momenta[0]))

    return {
        'energy_drift': energy_drift,
        'energy_relative': energy_drift / abs(energies[0]),
        'p_theta_drift': p_theta_drift,
        'p_theta_conserved': p_theta_drift < 1e-12,
        'energies': energies,
        'fiber_momenta': fiber_momenta
    }
```

#### C3: Projection to Reduced Dynamics

```python
def project_bundle_trajectory(
    bundle_trajectory: BundleTrajectory
) -> ShapeSpaceTrajectory:
    """
    Project bundle trajectory to shape space.

    This should match the original reduced dynamics.

    Args:
        bundle_trajectory: Trajectory in S¹ × Shape Space

    Returns:
        Trajectory in Shape Space only
    """
    projected_states = [
        state.shape_state
        for state in bundle_trajectory.states
    ]

    return ShapeSpaceTrajectory(
        times=bundle_trajectory.times,
        states=projected_states
    )


def validate_projection_consistency(
    lifted_trajectory: BundleTrajectory,
    reduced_trajectory: ShapeSpaceTrajectory
) -> dict:
    """
    Verify π(lifted) = reduced.

    The projection of bundle dynamics should equal reduced dynamics.

    Args:
        lifted_trajectory: Trajectory on bundle
        reduced_trajectory: Original reduced trajectory

    Returns:
        Validation results
    """
    projected = project_bundle_trajectory(lifted_trajectory)

    # Compare state-by-state
    max_error = 0.0
    errors = []

    for lifted_state, reduced_state in zip(
        projected.states,
        reduced_trajectory.states
    ):
        error = np.linalg.norm(
            lifted_state.to_array() - reduced_state.to_array()
        )
        errors.append(error)
        max_error = max(max_error, error)

    return {
        'max_projection_error': max_error,
        'mean_projection_error': np.mean(errors),
        'consistent': max_error < 1e-10
    }
```

---

## Part D: Integrability Search

### Objectives

1. Verify three integrals: $E$, $L$, $p_\theta$
2. Check functional independence
3. Verify involution: $\{F_i, F_j\} = 0$
4. Search for additional (fourth) integral
5. If integrable: construct action-angle coordinates

### Key Algorithms

#### D1: Integral Verification

```python
def verify_basic_integrals(
    trajectory: BundleTrajectory,
    lifted_hamiltonian: LiftedHamiltonian
) -> dict:
    """
    Verify the three candidate integrals.

    F₁ = H̃ (energy)
    F₂ = L (angular momentum)
    F₃ = p_θ (fiber momentum)

    Args:
        trajectory: Test trajectory
        lifted_hamiltonian: Hamiltonian

    Returns:
        Dictionary with conservation statistics
    """
    n = len(trajectory.states)

    F1 = np.zeros(n)  # Energy
    F2 = np.zeros(n)  # Angular momentum
    F3 = np.zeros(n)  # Fiber momentum

    for i, state in enumerate(trajectory.states):
        F1[i] = lifted_hamiltonian.evaluate(state)
        F2[i] = state.shape_state.L  # Angular momentum in base
        F3[i] = state.p_theta

    # Check conservation
    results = {
        'F1_conserved': np.max(np.abs(F1 - F1[0])) < 1e-12,
        'F2_conserved': np.max(np.abs(F2 - F2[0])) < 1e-12,
        'F3_conserved': np.max(np.abs(F3 - F3[0])) < 1e-12,
        'F1_drift': np.max(np.abs(F1 - F1[0])),
        'F2_drift': np.max(np.abs(F2 - F2[0])),
        'F3_drift': np.max(np.abs(F3 - F3[0]))
    }

    return results
```

#### D2: Functional Independence

```python
def test_functional_independence(
    integrals: list[Callable],
    state: BundleState
) -> bool:
    """
    Test if integrals F₁, F₂, F₃ are functionally independent.

    Criterion: Gradients dF₁, dF₂, dF₃ are linearly independent.

    Args:
        integrals: List of integral functions
        state: Point where to test

    Returns:
        True if independent
    """
    n = len(integrals)
    gradients = np.zeros((n, state.dimension))

    for i, F in enumerate(integrals):
        gradients[i] = compute_gradient(F, state)

    # Check rank
    rank = np.linalg.matrix_rank(gradients, tol=1e-10)

    return rank == n


def compute_gradient_matrix(
    integrals: list[Callable],
    states: list[BundleState]
) -> np.ndarray:
    """
    Compute gradient matrix at multiple points.

    Returns:
        (n_states, n_integrals, state_dim) array
    """
    n_states = len(states)
    n_integrals = len(integrals)
    state_dim = states[0].dimension

    gradients = np.zeros((n_states, n_integrals, state_dim))

    for i, state in enumerate(states):
        for j, F in enumerate(integrals):
            gradients[i, j] = compute_gradient(F, state)

    return gradients
```

#### D3: Involution Test

```python
def verify_involution(
    integrals: list[Callable],
    state: BundleState,
    symplectic_form: ExtendedSymplecticForm
) -> dict:
    """
    Verify {Fᵢ, Fⱼ} = 0 for all i, j.

    This is a necessary condition for integrability.

    Args:
        integrals: List of integral functions [F₁, F₂, F₃]
        state: Point where to test
        symplectic_form: Extended form

    Returns:
        Dictionary with Poisson brackets
    """
    n = len(integrals)
    brackets = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            brackets[i, j] = poisson_bracket_on_bundle(
                integrals[i],
                integrals[j],
                state,
                symplectic_form
            )

    # Check antisymmetry
    antisymmetric = np.allclose(brackets, -brackets.T, atol=1e-10)

    # Check all brackets vanish
    max_bracket = np.max(np.abs(brackets))
    in_involution = max_bracket < 1e-10

    return {
        'bracket_matrix': brackets,
        'antisymmetric': antisymmetric,
        'max_bracket': max_bracket,
        'in_involution': in_involution,
        'pairs': {
            f'{{F{i}, F{j}}}': brackets[i, j]
            for i in range(n) for j in range(i+1, n)
        }
    }
```

#### D4: Search for Fourth Integral

If the system is super-integrable, there may be a fourth independent integral:

```python
def search_fourth_integral(
    trajectory: BundleTrajectory,
    candidate_functions: list[Callable]
) -> Optional[Callable]:
    """
    Search for additional integral beyond F₁, F₂, F₃.

    Strategy: Test candidate functions for conservation.

    Args:
        trajectory: Test trajectory
        candidate_functions: List of trial functions

    Returns:
        Fourth integral (if found), else None
    """
    for candidate in candidate_functions:
        # Evaluate along trajectory
        values = [candidate(state) for state in trajectory.states]

        # Check conservation
        drift = np.max(np.abs(values - values[0]))

        if drift < 1e-12:
            # Potential fourth integral!
            # Verify functional independence with F₁, F₂, F₃
            if test_functional_independence(
                [F1, F2, F3, candidate],
                trajectory.states[0]
            ):
                return candidate

    return None


def generate_candidate_integrals() -> list[Callable]:
    """
    Generate candidate functions for fourth integral.

    Strategies:
        - Polynomial combinations of coordinates
        - Derived from symmetries
        - Inspired by Kepler problem (eccentricity vector, etc.)
    """
    candidates = []

    # Linear combinations
    def linear_combo(a, b, c):
        return lambda state: (
            a * state.shape_state.r12 +
            b * state.shape_state.r23 +
            c * state.shape_state.r31
        )

    # Add various linear combinations
    for a, b, c in itertools.product([-1, 0, 1], repeat=3):
        if (a, b, c) != (0, 0, 0):
            candidates.append(linear_combo(a, b, c))

    # Quadratic forms
    def quadratic(state):
        r = np.array([
            state.shape_state.r12,
            state.shape_state.r23,
            state.shape_state.r31
        ])
        return np.dot(r, r)

    candidates.append(quadratic)

    # Add more sophisticated candidates...

    return candidates
```

---

## Integration with Existing Infrastructure

### Dependencies

- **Task 2.1.1**: Shape space coordinates, transformations
- **Task 2.1.2**: Connection form $\mathcal{A}$ (critical input)
- **WP1**: High-precision integrators

### Outputs to Future Work

- Bundle state trajectories for analysis
- Integrability classification results
- If integrable: action-angle variables for WP3
- If non-integrable: motivation for WP2.3 (KS lift—higher dimensional)

---

## Implementation Schedule

### Phase 1: Bundle Construction (3 days)
- **Day 1**: S¹ bundle data structures, charts
- **Day 2**: Transition functions, validation
- **Day 3**: Unit tests, documentation

### Phase 2: Extended Symplectic Form (2 days)
- **Day 4**: Implement extended form
- **Day 5**: Closedness verification, Poisson brackets

### Phase 3: Lifted Dynamics (3 days)
- **Day 6**: Hamiltonian vector field, equations
- **Day 7**: Integration on bundle
- **Day 8**: Conservation verification, projection tests

### Phase 4: Integrability Analysis (3 days)
- **Day 9**: Three-integral verification, involution tests
- **Day 10**: Fourth integral search
- **Day 11**: Action-angle construction (if integrable)

### Phase 5: Documentation (1 day)
- **Day 12**: Technical report, visualizations, results summary

**Total**: 12 days

---

## Success Criteria

### Functional Requirements
- [ ] S¹ bundle correctly constructed (passes cocycle tests)
- [ ] Extended symplectic form is closed: $d\widetilde{\omega} = 0$
- [ ] Fiber momentum $p_\theta$ is conserved during integration
- [ ] Projection π(lifted) = reduced trajectory (error < 1e-10)

### Mathematical Requirements
- [ ] Three integrals identified: $H$, $L$, $p_\theta$
- [ ] Functional independence verified
- [ ] Involution verified: $\{F_i, F_j\} = 0$
- [ ] Classification: integrable or non-integrable on bundle

### Scientific Requirements
- [ ] **Primary Question**: Is the 3BP integrable on S¹ bundle?
  - If YES: Construct action-angle coordinates, proceed to WP3
  - If NO: Document obstruction, proceed to WP2.3 (KS lift)
- [ ] Compare complexity: bundle dynamics vs. reduced dynamics
- [ ] Quantify advantage: Does lift simplify geometry? (curvature, chaos indicators)

### Quality Requirements
- [ ] Test coverage > 95%
- [ ] Complete API documentation
- [ ] Technical report section written
- [ ] Visualization of fiber dynamics

---

## Risk Mitigation

### Risk 1: Lift May Not Be Integrable
**Likelihood**: Medium
**Impact**: High (contradicts hypothesis)

**Mitigation**:
- This is a scientific hypothesis—negative result is valid
- If non-integrable, proceed to WP2.3 (KS lift, higher-dimensional)
- Document the obstruction: What prevents integrability on S¹ bundle?

### Risk 2: Computational Cost of 4D Integration
**Likelihood**: Low
**Impact**: Medium

**Mitigation**:
- 4D phase space (8D total) is manageable
- Use symplectic integrators (preserve structure)
- Parallelize over initial conditions

### Risk 3: Numerical Errors in Symplectic Form
**Likelihood**: Medium
**Impact**: Medium

**Mitigation**:
- Use high-precision arithmetic where needed
- Validate closedness explicitly (Stokes' theorem)
- Cross-check with symbolic computation (SymPy)

### Risk 4: Finding Fourth Integral is Hard
**Likelihood**: High
**Impact**: Low (not required for progress)

**Mitigation**:
- Focus on verifying three standard integrals
- Fourth integral (if exists) would make system super-integrable (bonus)
- If not found, still validates 3-integral structure

---

## References

### Geometric Mechanics
1. Marsden & Ratiu, *Introduction to Mechanics and Symmetry* (1999) - Chapter on principal bundles
2. Guillemin & Sternberg, *Symplectic Techniques in Physics* (1984)
3. Montgomery, "The connection whose holonomy is the classical adiabatic angles of Hannay and Berry" (1988)

### Lift Constructions
4. Cushman & Bates, *Global Aspects of Classical Integrable Systems* (1997) - S¹ reduction
5. Moser, "Regularization of Kepler's problem and the averaging method" (1970)

### Three-Body Problem
6. Meyer & Hall, *Introduction to Hamiltonian Dynamical Systems* (2008)

---

## Appendix: Expected Outcomes

### Scenario 1: Integrable on S¹ Bundle ✅

**Implication**: Lift-integrability hypothesis confirmed!

**Next Steps**:
- Construct action-angle variables explicitly
- Verify Liouville tori foliation
- Use for solution characterization (WP3)
- Skip WP2.3 (unnecessary)

### Scenario 2: Non-Integrable on S¹ Bundle ⚠️

**Implication**: S¹ lift is insufficient (as expected for general 3BP)

**Analysis**:
- Why did lift fail? Compute residual curvature/obstruction
- Is system "closer" to integrable? (quantify via chaos indicators)
- Does fiber momentum $p_\theta$ provide partial decoupling?

**Next Steps**:
- Proceed to WP2.3 (KS-Spinor lift—4D fiber, 7D total)
- Higher-dimensional lift may eliminate obstruction

### Scenario 3: Partial Integrability 🤔

**Implication**: Exists integrable submanifold (e.g., equal masses, collinear)

**Analysis**:
- Characterize integrable region
- Study bifurcations at boundary
- Compare with known exact solutions

---

**Document Version**: 1.0
**Last Updated**: 2025-11-13
**Next Review**: After Part A implementation
**Dependencies**: Task 2.1.2 Complete (Connection $\mathcal{A}$)
**Status**: Ready for Implementation
