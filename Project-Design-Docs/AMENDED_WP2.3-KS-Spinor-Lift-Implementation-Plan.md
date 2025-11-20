# WP 2.3: Kustaanheimo-Stiefel (KS) Spinor "Pairwise" Lift
## Work Package 2 - Geometric Reduction and Shape Space Analysis
## **AMENDED VERSION - Time Regularization Fully Integrated**

**Status**: Design Phase (Amended)
**Priority**: Critical Path for Lift-Integrability Hypothesis (Extended)
**Estimated Duration**: 14-17 days (extended for time regularization)
**Dependencies**: WP2.2 Complete or In-Progress (S¹ Lift), Task 2.1.1 (Coordinates)
**Amendment Date**: 2025-11-20
**Amendment**: Comprehensive integration of time regularization throughout implementation

---

## Table of Contents

1. [Overview](#overview)
2. [Mathematical Background: Spatial and Temporal Regularization](#mathematical-background-spatial-and-temporal-regularization)
3. [Implementation Architecture](#implementation-architecture)
4. [Part A: KS Transformation with Time](#part-a-ks-transformation-with-time)
5. [Part B: Pairwise Application with Fictitious Time](#part-b-pairwise-application-with-fictitious-time)
6. [Part C: Time-Regularized Constrained Dynamics](#part-c-time-regularized-constrained-dynamics)
7. [Part D: Integrability Analysis with Temporal Structure](#part-d-integrability-analysis-with-temporal-structure)
8. [Part E: Time-Dependent Hamiltonian Structure (NEW)](#part-e-time-dependent-hamiltonian-structure-new)
9. [Integration with Existing Infrastructure](#integration-with-existing-infrastructure)
10. [Implementation Schedule](#implementation-schedule)
11. [Success Criteria](#success-criteria)

---

## Overview

### Purpose (AMENDED)

WP 2.3 implements the **Kustaanheimo-Stiefel (KS) spinor lift** as a **coupled spatial-temporal regularization**. The KS transformation is not merely a change of spatial coordinates—it is fundamentally a **simultaneous lift in space and time** that:

1. **Spatial Regularization**: Embeds 3D space in 4D spinor space, removing $1/r$ singularities
2. **Temporal Regularization**: Introduces fictitious time $s$ via Sundman transformation $dt/ds = r$
3. **Coupled Structure**: The two regularizations are **inseparable**—each requires the other for complete smoothing of dynamics
4. **Hamiltonian Extension**: Creates extended phase space including time as a dynamical degree of freedom

### The Complete KS Regularization Picture

**Traditional View** (Incomplete):
```
3D Kepler → 4D KS spinor → regularized
```

**Complete View** (WITH TIME):
```
(t, 3D Kepler) → (s, 4D KS spinor) → regularized
     ↓                    ↓
Physical time        Fictitious time
  dt/ds = r          Smooth dynamics
```

**Key Insight**: The KS transformation **requires time reparametrization** to achieve regularization. The spatial lift alone is insufficient—the velocity singularity ($v \to \infty$ as $r \to 0$) remains unless time is also transformed.

### Objectives (AMENDED)

1. **Coupled Regularization**: Implement spatial (KS) and temporal (Sundman) transformations as unified system
2. **Extended Phase Space**: Track $(u, p_u, s, \mathcal{K}, t, E)$ with all conjugate pairs
3. **Fictitious Time Dynamics**: Integrate in regularized time $s$, maintain relation to physical time $t$
4. **Time-Dependent Constraints**: Enforce bilinear constraints with proper temporal scaling
5. **Hamiltonian Structure**: Maintain symplectic structure in extended $(space, time)$ phase space
6. **Integrability with Time**: Search for conserved quantities including temporal integrals

### Deliverables (AMENDED)

- **Deliverable 2.3.1**: KS transformation with explicit time transformation (forward and inverse)
- **Deliverable 2.3.2**: Extended phase space data structures including $(s, \mathcal{K}, t, E)$
- **Deliverable 2.3.3**: Time-regularized RATTLE integrator maintaining both spatial and temporal constraints
- **Deliverable 2.3.4**: Collision regularization with time tracking (validate smooth passage through $r \to 0$)
- **Deliverable 2.3.5**: Conservation monitors for both $E$ (physical energy) and $\mathcal{K}$ (regularized energy)
- **Deliverable 2.3.6**: Integrability analysis including temporal symmetries
- **Deliverable 2.3.7**: Technical report: "Coupled Space-Time Regularization via KS Spinor Geometry"

---

## Mathematical Background: Spatial and Temporal Regularization

### The Two-Fold Singularity Problem

The Kepler problem (and by extension, 3BP near collisions) has **two distinct singularities**:

**1. Position Singularity**: $r \to 0$
- Potential energy: $V = -k/r \to -\infty$
- Force: $F = -k/r^2 \to -\infty$
- **Resolution**: Spatial coordinate change (KS transform)

**2. Velocity Singularity**: $v \to \infty$
- As particles approach, kinetic energy diverges: $T = v^2/2 \to \infty$
- Trajectory becomes infinitely steep in $(t, r)$ coordinates
- **Resolution**: Time reparametrization (Sundman transform)

**Both must be addressed simultaneously** for complete regularization.

### The KS Spatial Transformation (Detailed)

**Bilinear Map**: 3D position is embedded in 4D spinor space via
$$
\mathbf{r} = L(\mathbf{u}) \mathbf{u}
$$
where $\mathbf{u} = (u_0, u_1, u_2, u_3) \in \mathbb{R}^4$ and $L(\mathbf{u})$ is the **Levi-Civita matrix**:
$$
L(\mathbf{u}) = \begin{pmatrix}
u_0 & -u_1 & -u_2 & -u_3 \\
u_1 & u_0 & -u_3 & u_2 \\
u_2 & u_3 & u_0 & -u_1
\end{pmatrix}
$$

**Key Properties**:
1. **Bilinear Relation**: $r = |\mathbf{r}| = |\mathbf{u}|^2$
2. **Velocity Transform**: $\dot{\mathbf{r}} = 2L(\mathbf{u})\dot{\mathbf{u}}$ (in physical time)
3. **Quaternion Structure**: $L(\mathbf{u})$ encodes quaternion multiplication
4. **SO(3) to SU(2) Lift**: KS implements the universal covering $SU(2) \to SO(3)$

**What This Achieves**:
- Collision $r \to 0$ maps to spinor origin $|\mathbf{u}| \to 0$ (coordinate singularity eliminated)
- The transformed potential $\tilde{V}(u) = -k/|\mathbf{u}|^2$ is **still singular** at $u = 0$!
- **Spatial transformation alone is insufficient**

### The Sundman Temporal Transformation (Detailed)

**Fictitious Time**: Introduce new time coordinate $s$ related to physical time $t$ by:
$$
\frac{dt}{ds} = \Omega(q) > 0
$$

**Standard Choice for KS Regularization**:
$$
\frac{dt}{ds} = r = |\mathbf{u}|^2
$$

**Effect on Dynamics**:

Physical time equations:
$$
\frac{d\mathbf{r}}{dt} = \mathbf{v}, \quad m\frac{d\mathbf{v}}{dt} = -\frac{k\mathbf{r}}{r^3}
$$

Fictitious time equations (after applying $d/dt = (1/\Omega) \cdot d/ds$):
$$
\frac{d\mathbf{u}}{ds} = \frac{1}{|\mathbf{u}|^2} \cdot 2L(\mathbf{u})\dot{\mathbf{u}}
$$

**Regularized Hamiltonian**:

Original (physical time): $H = \frac{p^2}{2m} - \frac{k}{r}$

Regularized (fictitious time):
$$
\mathcal{K} = \frac{1}{2m|\mathbf{u}|^2}\sum_{i=0}^3 p_{u_i}^2 - \frac{k}{|\mathbf{u}|^2}
$$

**Key Point**: The factor $1/|\mathbf{u}|^2$ in the kinetic term exactly cancels the singularity in the potential!

### Why the Coupling is Necessary

**Separate transformations fail**:

| Transform | Position Singularity | Velocity Singularity |
|-----------|---------------------|---------------------|
| KS spatial only | ✓ Removed | ✗ Remains ($\dot{u} \to \infty$) |
| Sundman time only | ✗ Remains ($F \to \infty$) | ✓ Removed |
| **KS + Sundman** | **✓ Removed** | **✓ Removed** |

The **combined transform** achieves:
$$
\mathcal{K}(u, p_u) = \frac{|p_u|^2}{2m|\mathbf{u}|^2} - \frac{k}{|\mathbf{u}|^2} = \frac{1}{|\mathbf{u}|^2}\left(\frac{|p_u|^2}{2m} - k\right)
$$

As $|\mathbf{u}| \to 0$:
- Numerator remains bounded (conservation of $\mathcal{K}$)
- Both terms scale identically with $1/|\mathbf{u}|^2$
- **No singularity** in equations of motion

### Extended Phase Space with Time

The full regularized system lives in **extended phase space**:

**Configuration Space**: $Q_{ext} = \mathbb{R}^4 \times \mathbb{R} \times \mathbb{R}$
- $\mathbf{u} \in \mathbb{R}^4$: KS spinor (spatial)
- $s \in \mathbb{R}$: Fictitious time (temporal)
- $t \in \mathbb{R}$: Physical time (parametric)

**Phase Space**: $P_{ext} = T^*Q_{ext} = \mathbb{R}^{4} \times \mathbb{R} \times \mathbb{R} \times \mathbb{R}^4 \times \mathbb{R} \times \mathbb{R}$
- $(u, p_u)$: Spinor position and momenta
- $(s, \mathcal{K})$: Fictitious time and regularized energy
- $(t, E)$: Physical time and physical energy

**Symplectic Form on Extended Space**:
$$
\Omega_{ext} = \sum_{i=0}^3 dp_{u_i} \wedge du_i + d\mathcal{K} \wedge ds + dE \wedge dt
$$

**Constraints**:
1. **Bilinear**: $\Phi_1 = |\mathbf{u}|^2 - r = 0$
2. **Hamiltonian**: $\Phi_2 = \mathcal{K}(u, p_u) - \mathcal{K}_0 = 0$
3. **Time Relation**: $dt/ds = |\mathbf{u}|^2$ (not a constraint, but a first-order ODE)
4. **Energy**: $E = \mathcal{K}/|\mathbf{u}|^2$ (derived from time relation)

**Effective Dimension**:
- Extended phase space: $\dim = 12$ (6 pairs of conjugate variables)
- After constraints and gauge fixing: $\dim = 6$ (same as original Kepler problem)
- **Time degrees of freedom**: Couple to spatial via $dt/ds$ relation

### Three-Body Pairwise Extension with Time

For three bodies, we have **three pairwise KS lifts**, each with its own temporal structure:

**Spatial Lift**:
$$
(r_{12}, r_{23}, r_{31}) \to (u_{12}, u_{23}, u_{31})
$$
where each $u_{ij} \in \mathbb{R}^4$.

**Temporal Structure** (Subtle Point):

**Question**: Do we use **one fictitious time** or **three**?

**Answer**: **One unified fictitious time** $s$ for the entire system, because:
- Physical time $t$ is global (same for all three pairs)
- Fictitious time must map bijectively to physical time
- Different $s_{ij}$ would violate causality

**Unified Time Transformation**:
$$
\frac{dt}{ds} = f(r_{12}, r_{23}, r_{31})
$$

**Standard Choice**:
$$
\frac{dt}{ds} = r_{12} \cdot r_{23} \cdot r_{31}
$$
(product ensures smoothness when any one pair collides)

**Alternative** (sum):
$$
\frac{dt}{ds} = r_{12} + r_{23} + r_{31}
$$

**Trade-off**:
- Product: More regularization power (triple zero at triple collision)
- Sum: Simpler, suffices for binary collisions

**Extended Phase Space for 3BP**:
- Configuration: $(u_{12}, u_{23}, u_{31}, s, t) \in \mathbb{R}^{12} \times \mathbb{R}^2$
- Phase space: $(u, p_u, s, \mathcal{K}, t, E) \in \mathbb{R}^{26}$
- Constraints reduce effective dimension to 12D (6D config space, 12D phase space)

---

## Implementation Architecture (AMENDED)

### Module Structure (Updated with Time)

```
src/python/regularization/
├── __init__.py                    # Package exports
├── ks_transform.py                # A: Single-pair KS (spatial only)
├── ks_time_transform.py           # A: KS with time (NEW)
├── levi_civita.py                 # A: Levi-Civita matrix operations
├── spinor_algebra.py              # A: Quaternion/spinor operations
├── inverse_transform.py           # A: Spinor → Cartesian
├── sundman.py                     # A: Time reparametrization (NEW)
└── extended_phase_space.py        # A: Data structures with time (NEW)

src/python/lifts/
├── ks_pairwise.py                 # B: Pairwise KS for 3BP
├── ks_pairwise_time.py            # B: Pairwise with unified fictitious time (NEW)
├── spinor_coordinates.py          # B: (u12, u23, u31) system
└── constraint_manifold.py         # B: Bilinear + closure + time constraints (UPDATED)

src/python/integration/
├── constrained_integrator.py      # C: RATTLE/SHAKE on constraints
├── fictitious_time_integrator.py  # C: Integration in s with dt/ds tracking (NEW)
├── time_synchronizer.py           # C: Sync physical and fictitious time (NEW)
└── collision_detector.py          # C: Monitor near-collisions

src/python/analysis/
├── ks_integrability.py            # D: Search integrals in spinor coords
├── spinor_symmetries.py           # D: SU(2) structure analysis
├── temporal_symmetries.py         # D: Time translation symmetries (NEW)
├── energy_conservation.py         # D: Monitor E and K separately (NEW)
└── comparison_s1_vs_ks.py         # D: Compare lift strategies

tests/regularization/
├── test_ks_transform.py           # Unit tests
├── test_ks_time_coupling.py       # Test spatial-temporal coupling (NEW)
├── test_bilinear_relation.py      # Validate |u|² = r
├── test_time_relation.py          # Validate dt/ds = r (NEW)
├── test_collision_passage.py      # Integrate through collision
├── test_energy_conservation.py    # Test E vs K conservation (NEW)
└── test_spinor_algebra.py         # Algebraic consistency
```

### Data Structures (AMENDED)

#### Extended State with Time

```python
@dataclass(frozen=True)
class ExtendedKSState:
    """
    Complete KS state including both spatial and temporal variables.

    This represents a point in the extended phase space:
        (u, p_u, s, K, t, E) ∈ T*R^4 × T*R × T*R

    Attributes:
        u: SpinorVector — 4D spinor (spatial configuration)
        p_u: SpinorVector — Conjugate spinor momenta
        s: float — Fictitious time (regularized clock)
        K: float — Regularized energy (conjugate to s)
        t: float — Physical time (observer's clock)
        E: float — Physical energy (conserved Hamiltonian)

    Constraints:
        - Bilinear: |u|² ≈ r (physical radius)
        - Energy: K ≈ E · |u|² (energy scaling with time dilation)
        - Time relation: dt/ds = |u|²
    """
    u: SpinorVector
    p_u: SpinorVector
    s: float
    K: float
    t: float
    E: float

    def __post_init__(self):
        """Validate physical constraints"""
        # Check energy relation
        time_dilation = self.u.norm_squared
        expected_K = self.E * time_dilation

        if abs(self.K - expected_K) > 1e-10:
            warnings.warn(f"Energy constraint violation: K = {self.K}, E·r = {expected_K}")

    @property
    def time_dilation_factor(self) -> float:
        """
        Time dilation factor Ω = dt/ds = |u|².

        This is the "clock ratio" between physical and fictitious time.
        """
        return self.u.norm_squared

    @property
    def physical_radius(self) -> float:
        """Physical radius r = |u|² (from bilinear relation)"""
        return self.u.norm_squared

    def to_vector(self) -> np.ndarray:
        """
        Flatten to vector for integration.

        Returns:
            [u₀, u₁, u₂, u₃, p_u₀, p_u₁, p_u₂, p_u₃, s, K, t, E]
            (12-dimensional state vector)
        """
        return np.concatenate([
            self.u.components,
            self.p_u.components,
            [self.s, self.K, self.t, self.E]
        ])

    @classmethod
    def from_vector(cls, state_vec: np.ndarray) -> 'ExtendedKSState':
        """Construct from flat array"""
        assert len(state_vec) == 12, "Extended KS state must be 12D"

        u = SpinorVector(state_vec[0:4])
        p_u = SpinorVector(state_vec[4:8])
        s, K, t, E = state_vec[8:12]

        return cls(u=u, p_u=p_u, s=s, K=K, t=t, E=E)

    def validate_time_relation(self, tol: float = 1e-12) -> bool:
        """
        Check if time relation is satisfied: K = E · |u|²

        This is the consistency condition from dt/ds = |u|².
        """
        lhs = self.K
        rhs = self.E * self.u.norm_squared
        return abs(lhs - rhs) < tol


@dataclass(frozen=True)
class PairwiseSpinorStateWithTime:
    """
    Complete pairwise spinor state for 3BP with unified time.

    Extended phase space: 26D = 2 × (12 spatial + 1 temporal)
    After constraints: 12D effective phase space

    Time Structure:
        - Single fictitious time s (unified for all three pairs)
        - Single physical time t
        - Time transformation: dt/ds = f(r₁₂, r₂₃, r₃₁)
    """
    # Spatial coordinates (12D configuration)
    u12: SpinorVector
    u23: SpinorVector
    u31: SpinorVector

    # Spatial momenta (12D momenta)
    p_u12: SpinorVector
    p_u23: SpinorVector
    p_u31: SpinorVector

    # Temporal coordinates (2D: fictitious and physical time)
    s: float  # Fictitious time (integration parameter)
    t: float  # Physical time (observer's clock)

    # Energies (2D: regularized and physical)
    K: float  # Regularized energy (conjugate to s)
    E: float  # Physical energy (conserved)

    @property
    def time_dilation_factor(self) -> float:
        """
        Global time dilation Ω = dt/ds.

        Standard choices:
            - Product: Ω = r₁₂ · r₂₃ · r₃₁
            - Sum: Ω = r₁₂ + r₂₃ + r₃₁
            - Min: Ω = min(r₁₂, r₂₃, r₃₁)
        """
        r12 = self.u12.norm_squared
        r23 = self.u23.norm_squared
        r31 = self.u31.norm_squared

        # Use sum (simpler, sufficient for binary collisions)
        return r12 + r23 + r31

    @property
    def individual_radii(self) -> tuple[float, float, float]:
        """Individual pairwise radii (r₁₂, r₂₃, r₃₁)"""
        return (
            self.u12.norm_squared,
            self.u23.norm_squared,
            self.u31.norm_squared
        )

    def check_time_consistency(self, tol: float = 1e-10) -> bool:
        """Verify K ≈ E · Ω (energy-time consistency)"""
        Omega = self.time_dilation_factor
        return abs(self.K - self.E * Omega) < tol

    def to_extended_ks_states(self) -> tuple[ExtendedKSState, ExtendedKSState, ExtendedKSState]:
        """
        Decompose into three extended KS states (one per pair).

        Note: They share the same (s, t) but have pair-specific energies.
        """
        # Energy partitioning (approximate; exact requires solving coupled system)
        K_12 = self.K / 3  # Simple equal partition
        K_23 = self.K / 3
        K_31 = self.K / 3

        return (
            ExtendedKSState(self.u12, self.p_u12, self.s, K_12, self.t, self.E),
            ExtendedKSState(self.u23, self.p_u23, self.s, K_23, self.t, self.E),
            ExtendedKSState(self.u31, self.p_u31, self.s, K_31, self.t, self.E)
        )
```

---

## Part A: KS Transformation with Time

### Objectives (AMENDED)

1. Implement **coupled spatial-temporal transformation**
2. Forward: $(t, r, v) \to (s, u, u')$ with time tracking
3. Inverse: $(s, u, u') \to (t, r, v)$ with time reconstruction
4. Validate **both** bilinear ($|\mathbf{u}|^2 = r$) and time ($dt/ds = r$) relations

### Key Algorithms

#### A1: Extended KS Forward Transform

```python
def cartesian_to_extended_ks(
    t: float,
    position: np.ndarray,
    velocity: np.ndarray,
    energy: float,
    initial_s: float = 0.0
) -> ExtendedKSState:
    """
    Transform Cartesian (t, r, v) to extended KS (s, u, u').

    This performs BOTH spatial and temporal lifts simultaneously.

    Args:
        t: Physical time
        position: 3D position vector
        velocity: 3D velocity vector
        energy: Physical energy E (conserved)
        initial_s: Initial fictitious time (default 0)

    Returns:
        ExtendedKSState with all components

    Algorithm:
        1. Spatial lift: r → u (KS transform)
        2. Compute time dilation: Ω = |u|²
        3. Regularized energy: K = E · Ω
        4. Transform velocity: v → p_u via chain rule
    """
    r = position
    v = velocity
    r_norm = np.linalg.norm(r)

    # Step 1: Spatial KS transform (canonical chart choice)
    if r[2] >= 0:
        # Northern hemisphere chart
        u0 = np.sqrt(r_norm + r[2])
        u1 = r[1] / (np.sqrt(2) * np.sqrt(r_norm + r[2]))
        u2 = -r[0] / (np.sqrt(2) * np.sqrt(r_norm + r[2]))
        u3 = 0.0
    else:
        # Southern hemisphere chart
        u0 = r[1] / (np.sqrt(2) * np.sqrt(r_norm - r[2]))
        u1 = np.sqrt(r_norm - r[2])
        u2 = 0.0
        u3 = -r[0] / (np.sqrt(2) * np.sqrt(r_norm - r[2]))

    u = SpinorVector(np.array([u0, u1, u2, u3]))

    # Step 2: Time dilation
    Omega = u.norm_squared  # = r_norm (should match)
    assert abs(Omega - r_norm) < 1e-12, "Bilinear relation violated"

    # Step 3: Regularized energy
    K = energy * Omega

    # Step 4: Transform velocity to spinor momenta
    # Physical: dr/dt = v
    # Regularized: du/ds = u_prime
    # Chain rule: dr/dt = (dr/du)(du/ds)(ds/dt)
    #           = 2L(u) · u_prime · (1/Omega)
    # Therefore: v = 2L(u) u_prime / Omega
    #           → u_prime = Omega/(2L(u)) · v

    L = levi_civita_matrix(u)

    # Solve: L(u) u_prime = v · Omega / 2
    u_prime_components, _, _, _ = np.linalg.lstsq(
        L, v * Omega / 2, rcond=None
    )

    # Convert to momenta: p_u = mass · u_prime (for Hamiltonian formalism)
    # Here we use unit mass; generalize as needed
    p_u = SpinorVector(u_prime_components)

    return ExtendedKSState(
        u=u,
        p_u=p_u,
        s=initial_s,
        K=K,
        t=t,
        E=energy
    )


def extended_ks_to_cartesian(
    state: ExtendedKSState
) -> tuple[float, np.ndarray, np.ndarray]:
    """
    Inverse transform: Extended KS → Cartesian.

    Returns:
        (t, position, velocity)

    Algorithm:
        1. Spatial inverse: u → r via L(u)u
        2. Time dilation: Ω = |u|²
        3. Velocity: v = 2L(u) u_prime / Ω
    """
    # Spatial inverse
    r = levi_civita_map(state.u, state.u)

    # Time dilation
    Omega = state.u.norm_squared

    # Velocity inverse
    # v = 2L(u) (p_u / mass) / Omega
    v = 2 * levi_civita_map(state.u, state.p_u) / Omega

    return state.t, r, v
```

#### A2: Time Evolution Equations

```python
def extended_ks_rhs(
    state: ExtendedKSState,
    mass: float,
    G: float = 1.0
) -> ExtendedKSState:
    """
    Right-hand side for extended KS equations of motion.

    Returns derivative dstate/ds (in fictitious time).

    Equations in fictitious time s:
        du/ds = ∂H_reg/∂p_u
        dp_u/ds = -∂H_reg/∂u
        dK/ds = ∂H_reg/∂s = 0  (time-translation symmetry)
        dt/ds = Ω(u) = |u|²  (time transformation)
        dE/ds = 0  (energy conservation)

    Regularized Hamiltonian:
        H_reg = |p_u|²/(2m|u|²) - k/|u|² - K
    """
    u = state.u.components
    p_u = state.p_u.components
    r = state.u.norm_squared

    # Compute Hamiltonian derivatives
    # ∂H/∂p_u = p_u / (m r)
    du_ds = p_u / (mass * r)

    # ∂H/∂u = -|p_u|²/(m r²) (∂r/∂u) + k/r² (∂r/∂u)
    #       = [ k - |p_u|²/m ] / r² · u  (using ∂r/∂u = u)
    dp_u_ds = (G * mass - np.dot(p_u, p_u) / mass) / (r**2) * u

    # Temporal evolution
    dK_ds = 0.0  # Conserved
    dt_ds = r  # Time transformation
    dE_ds = 0.0  # Conserved
    ds_ds = 1.0  # Trivial (s is integration parameter)

    return ExtendedKSState(
        u=SpinorVector(du_ds),
        p_u=SpinorVector(dp_u_ds),
        s=ds_ds,
        K=dK_ds,
        t=dt_ds,
        E=dE_ds
    )
```

#### A3: Integration with Time Tracking

```python
def integrate_extended_ks(
    initial_state: ExtendedKSState,
    s_span: tuple[float, float],
    n_steps: int,
    mass: float,
    G: float = 1.0
) -> ExtendedKSTrajectory:
    """
    Integrate extended KS system in fictitious time s.

    Tracks both s (integration parameter) and t (physical time).

    Returns:
        Trajectory with (s, t, u, p_u, K, E) at each point
    """
    from scipy.integrate import solve_ivp

    def rhs_for_integrator(s_current, state_vec):
        """Wrapper for scipy integrator"""
        state = ExtendedKSState.from_vector(state_vec)
        deriv = extended_ks_rhs(state, mass, G)
        return deriv.to_vector()

    # Integrate
    s_start, s_end = s_span
    state0_vec = initial_state.to_vector()

    solution = solve_ivp(
        rhs_for_integrator,
        (s_start, s_end),
        state0_vec,
        method='DOP853',
        max_step=(s_end - s_start) / n_steps,
        dense_output=True
    )

    # Extract trajectory
    states = [ExtendedKSState.from_vector(y) for y in solution.y.T]

    return ExtendedKSTrajectory(
        s_values=solution.t,
        t_values=np.array([s.t for s in states]),
        states=states
    )
```

---

## Part B: Pairwise Application with Fictitious Time

### Objectives (AMENDED)

1. Extend pairwise KS to include **unified fictitious time** for all three pairs
2. Define **global time transformation** $dt/ds = f(r_{12}, r_{23}, r_{31})$
3. Implement constraints including **time-energy consistency**
4. Validate **synchronization** of physical time across all pairs

### Key Algorithms

#### B1: Global Time Transformation Choice

```python
class TimeTransformationStrategy(Enum):
    """
    Strategies for global time transformation in 3BP.
    """
    PRODUCT = "product"  # dt/ds = r₁₂ · r₂₃ · r₃₁
    SUM = "sum"          # dt/ds = r₁₂ + r₂₃ + r₃₁
    MIN = "min"          # dt/ds = min(r₁₂, r₂₃, r₃₁)
    WEIGHTED_SUM = "weighted_sum"  # dt/ds = Σ wᵢⱼ rᵢⱼ


def compute_time_dilation(
    state: PairwiseSpinorStateWithTime,
    strategy: TimeTransformationStrategy = TimeTransformationStrategy.SUM
) -> float:
    """
    Compute global time dilation factor Ω = dt/ds.

    Different strategies trade off regularization strength vs. complexity.

    Args:
        state: Current pairwise spinor state
        strategy: Choice of time transformation

    Returns:
        Omega (time dilation factor)
    """
    r12, r23, r31 = state.individual_radii

    if strategy == TimeTransformationStrategy.PRODUCT:
        # Strongest regularization (triple zero at triple collision)
        # Best for scenarios with potential triple collisions
        Omega = r12 * r23 * r31

    elif strategy == TimeTransformationStrategy.SUM:
        # Simple, sufficient for binary collisions
        # Most commonly used in practice
        Omega = r12 + r23 + r31

    elif strategy == TimeTransformationStrategy.MIN:
        # Adapts to closest pair
        # Can have discontinuous derivatives (problematic)
        Omega = min(r12, r23, r31)

    elif strategy == TimeTransformationStrategy.WEIGHTED_SUM:
        # Mass-weighted (prioritize heavy pairs)
        # Requires mass information
        # Example: w_ij = m_i * m_j
        # (Implementation requires masses)
        raise NotImplementedError("Weighted sum requires mass parameters")

    return Omega
```

#### B2: Time-Energy Consistency Constraint

```python
def evaluate_time_energy_constraint(
    state: PairwiseSpinorStateWithTime,
    strategy: TimeTransformationStrategy = TimeTransformationStrategy.SUM
) -> float:
    """
    Evaluate time-energy consistency constraint.

    Constraint: K = E · Ω(r₁₂, r₂₃, r₃₁)

    This arises from the relation dt/ds = Ω.

    Returns:
        Constraint violation (should be ≈ 0)
    """
    Omega = compute_time_dilation(state, strategy)

    # Constraint function
    g_time_energy = state.K - state.E * Omega

    return g_time_energy
```

---

I'll continue creating the rest of the AMENDED_WP2.3 document. Due to length, let me complete it:

---

## Part C: Time-Regularized Constrained Dynamics

### Objectives (AMENDED)

1. Implement **time-aware RATTLE integrator** maintaining both spatial and temporal constraints
2. Track **both** fictitious time $s$ (integration parameter) and physical time $t$ (observable)
3. Monitor **dual energy conservation**: $E$ (physical) and $\mathcal{K}$ (regularized)
4. Validate collision passage with explicit time dilation verification

### C1: Extended RATTLE with Time Tracking

```python
class TimeRegularizedRATTLE:
    """
    RATTLE integrator extended for time-regularized systems.
    
    Maintains constraints:
        1. Spatial: Bilinear and closure constraints
        2. Temporal: K = E · Ω(u)
        3. Hamiltonian: H_reg = 0 (on energy surface)
    """
    
    def step_with_time(
        self,
        state: PairwiseSpinorStateWithTime,
        ds: float
    ) -> PairwiseSpinorStateWithTime:
        """
        Single step in fictitious time s, tracking physical time t.
        
        Algorithm:
            1. Standard RATTLE step for spatial coordinates
            2. Advance physical time: t_new = t_old + Ω(u) · ds
            3. Update energies maintaining K = E · Ω
            4. Project onto extended constraint manifold
        """
        # Spatial RATTLE step (standard)
        state_spatial = self.rattle_step_spatial(state, ds)
        
        # Time evolution
        Omega = compute_time_dilation(state_spatial)
        dt = Omega * ds
        t_new = state.t + dt
        
        # Energy update (E conserved, K updated)
        E_new = state.E  # Conserved
        K_new = E_new * Omega  # Updated via time dilation
        
        # Construct updated state
        state_new = PairwiseSpinorStateWithTime(
            u12=state_spatial.u12,
            u23=state_spatial.u23,
            u31=state_spatial.u31,
            p_u12=state_spatial.p_u12,
            p_u23=state_spatial.p_u23,
            p_u31=state_spatial.p_u31,
            s=state.s + ds,
            t=t_new,
            K=K_new,
            E=E_new
        )
        
        # Project onto constraints
        return self.project_extended(state_new)
```

### C2: Collision Passage with Time Dilation Monitoring

```python
def integrate_through_collision_with_time(
    initial_state: PairwiseSpinorStateWithTime,
    masses: Masses,
    s_span: tuple[float, float],
    monitor_time_dilation: bool = True
) -> CollisionTrajectory:
    """
    Integrate through collision, tracking time dilation.
    
    Returns trajectory with:
        - s (fictitious time)
        - t (physical time)
        - u (spinor coords)
        - Ω(s) = dt/ds (time dilation factor)
        - E, K (energies)
    """
    integrator = TimeRegularizedRATTLE()
    
    n_steps = 10000
    ds = (s_span[1] - s_span[0]) / n_steps
    
    trajectory = []
    time_dilations = []
    
    state = initial_state
    
    for i in range(n_steps):
        # Record state
        trajectory.append(state)
        
        # Monitor time dilation
        Omega = compute_time_dilation(state)
        time_dilations.append(Omega)
        
        # Check for collision (any r_ij → 0)
        r12, r23, r31 = state.individual_radii
        if min(r12, r23, r31) < 1e-6:
            print(f"Near collision at s={state.s:.4f}, t={state.t:.4f}")
            print(f"  r_min={min(r12, r23, r31):.2e}")
            print(f"  Time dilation Ω={Omega:.2e}")
        
        # Integrate step
        state = integrator.step_with_time(state, ds)
    
    return CollisionTrajectory(
        s_values=[s.s for s in trajectory],
        t_values=[s.t for s in trajectory],
        states=trajectory,
        time_dilations=np.array(time_dilations)
    )
```

---

## Part D: Integrability Analysis with Temporal Structure

### Objectives (AMENDED)

1. Search for integrals including **temporal conserved quantities**
2. Verify **dual energy conservation**: $E$ (physical), $\mathcal{K}$ (regularized)
3. Analyze **time-translation symmetries** (both $t$ and $s$)
4. Compare integrability: spatial-only vs. spatial+temporal lifts

### D1: Temporal Integrals

```python
def identify_temporal_integrals(
    trajectory: ExtendedKSTrajectory
) -> dict:
    """
    Identify conserved quantities related to temporal structure.
    
    Candidate temporal integrals:
        1. E (physical energy) — from t-translation symmetry
        2. K (regularized energy) — from s-translation symmetry
        3. Θ = K · t - E · s — "action-like" combination
        4. Temporal "Casimirs" (if time has gauge structure)
    """
    n = len(trajectory.states)
    
    # Standard energies
    E_values = [s.E for s in trajectory.states]
    K_values = [s.K for s in trajectory.states]
    
    # Mixed temporal integral
    Theta_values = [
        s.K * s.t - s.E * s.s 
        for s in trajectory.states
    ]
    
    # Check conservation
    results = {
        'E': {
            'conserved': np.max(np.abs(E_values - E_values[0])) < 1e-12,
            'drift': np.max(np.abs(E_values - E_values[0]))
        },
        'K': {
            'conserved': np.max(np.abs(K_values - K_values[0])) < 1e-12,
            'drift': np.max(np.abs(K_values - K_values[0]))
        },
        'Theta': {
            'conserved': np.max(np.abs(Theta_values - Theta_values[0])) < 1e-12,
            'drift': np.max(np.abs(Theta_values - Theta_values[0]))
        }
    }
    
    return results
```

### D2: Comparison: Spatial-Only vs. Spatial+Temporal

```python
def compare_regularization_strategies(
    cart_state: CartesianState,
    masses: Masses
) -> dict:
    """
    Compare regularization with and without time transformation.
    
    Tests:
        1. KS spatial only (fixed physical time) — FAILS near collision
        2. KS + Sundman (fictitious time) — SUCCEEDS
    """
    results = {}
    
    # Strategy 1: KS without time regularization
    try:
        traj_spatial_only = integrate_ks_spatial_only(
            cart_state, masses, t_span=(0, 10)
        )
        results['spatial_only'] = {
            'success': True,
            'min_radius': min_radius(traj_spatial_only)
        }
    except IntegrationError as e:
        results['spatial_only'] = {
            'success': False,
            'error': str(e),
            'message': "Velocity singularity at collision"
        }
    
    # Strategy 2: KS + Sundman time regularization
    try:
        traj_full = integrate_ks_with_time(
            cart_state, masses, s_span=(0, 100)
        )
        results['spatial_temporal'] = {
            'success': True,
            'min_radius': min_radius(traj_full),
            'time_dilation_max': max(traj_full.time_dilations)
        }
    except IntegrationError as e:
        results['spatial_temporal'] = {
            'success': False,
            'error': str(e)
        }
    
    # Verdict
    results['conclusion'] = (
        "Time regularization is NECESSARY" 
        if results['spatial_only']['success'] == False 
        else "Time regularization provides advantage"
    )
    
    return results
```

---

## Part E: Time-Dependent Hamiltonian Structure (NEW)

### The Extended Hamiltonian Formalism

The complete regularized system requires treating time as a **dynamical degree of freedom** using the **extended Hamiltonian formalism**.

### E1: Extended Phase Space Structure

**Standard Hamiltonian Mechanics** (time as parameter):
- Phase space: $(q, p) \in T^*Q$
- Hamiltonian: $H(q, p)$
- Evolution: $dq/dt = \partial H/\partial p$, $dp/dt = -\partial H/\partial q$

**Extended Hamiltonian Mechanics** (time as variable):
- Phase space: $(q, p, t, E) \in T^*Q \times T^*\mathbb{R}$
- Extended Hamiltonian (constraint): $\mathcal{H}_{ext} = H(q,p) - E = 0$
- Evolution parameter: Arbitrary parameter $\lambda$ (could be $s$)
- Equations: $dq/d\lambda = \partial \mathcal{H}/\partial p$, etc.

**Why This Works**:
- Energy $E$ becomes a dynamical variable (conjugate momentum to time)
- Hamiltonian constraint defines $(2n+2)$-dimensional extended phase space
- Physical trajectories lie on constraint surface $\mathcal{H}_{ext} = 0$
- Time parametrization freedom allows choosing $\lambda = s$ (fictitious time)

### E2: Contact Manifold Interpretation

The extended phase space has natural **contact structure**:

**Contact Form**:
$$
\alpha = dE - H(q, p) dt = p \cdot dq - (E + H) dt
$$

**Contact Condition**: $\alpha \wedge (d\alpha)^n \neq 0$

**Reeb Vector Field** (generates dynamics):
$$
R = \frac{\partial}{\partial t} + \sum_i \frac{\partial H}{\partial p_i}\frac{\partial}{\partial q_i} - \frac{\partial H}{\partial q_i}\frac{\partial}{\partial p_i}
$$

**Time Reparametrization as Contact Automorphism**:

The transformation $(t, E, q, p) \mapsto (s, \mathcal{K}, u, p_u)$ is a **contact transformation**:
$$
\alpha_{new} = f \cdot \alpha_{old}
$$
where $f = dt/ds = \Omega(u)$ is the conformal factor.

### E3: Dirac-Bergmann Constraint Analysis

The KS system has **first-class constraints** (generating gauge symmetries):

**Primary Constraint** (Hamiltonian):
$$
\Phi_1 = \mathcal{H}_{reg}(u, p_u) - \mathcal{K} \approx 0
$$

**Secondary Constraint** (Bilinear):
$$
\Phi_2 = |u|^2 - r \approx 0
$$

**Constraint Algebra**:
$$
\{\Phi_1, \Phi_2\} = \text{(computed)}
$$

If constraints are **first-class**, they generate gauge transformations:
- $\Phi_1$ generates time translations in $s$
- $\Phi_2$ generates "spinor gauge" transformations (related to $S^1$ action)

**Dirac Brackets**: On constraint surface, use Dirac brackets to obtain reduced symplectic structure.

---

## Integration with Existing Infrastructure

### Dependencies

- **Task 2.1.1**: Cartesian coordinates (for initial conditions and validation)
- **WP1**: High-precision integrators (extend to include time tracking)
- **WP2.2**: S¹ lift (for comparison without full time regularization)

### New Infrastructure Required

1. **Extended State Management**:
   - Data structures tracking $(u, p_u, s, \mathcal{K}, t, E)$
   - Serialization for long-term storage
   - Conversion utilities between representations

2. **Time Synchronization**:
   - Module to maintain consistency between $s$ and $t$
   - Interpolation in physical time (from $s$-sampled data)
   - Time dilation monitoring and diagnostics

3. **Dual Energy Monitoring**:
   - Separate trackers for $E$ and $\mathcal{K}$
   - Validation of relation $\mathcal{K} = E \cdot \Omega$
   - Constraint violation detection and correction

---

## Implementation Schedule (AMENDED)

### Phase 1: Extended Data Structures (2 days)
- **Day 1**: `ExtendedKSState` and `PairwiseSpinorStateWithTime` classes
- **Day 2**: Time transformation strategies, validation tests

### Phase 2: Single-Pair with Time (3 days)
- **Day 3**: Forward transform with time: $(t,r,v) \to (s,u,u')$
- **Day 4**: Inverse transform, round-trip tests
- **Day 5**: Integration with time tracking, validate $dt/ds = r$

### Phase 3: Pairwise Extension with Unified Time (3 days)
- **Day 6**: Pairwise coordinate system with shared $(s,t)$
- **Day 7**: Global time transformation implementation
- **Day 8**: Time-energy constraint validation

### Phase 4: Time-Regularized Integration (4 days)
- **Day 9-10**: Extended RATTLE integrator with time
- **Day 11**: Collision passage tests with time dilation monitoring
- **Day 12**: Dual energy conservation validation

### Phase 5: Temporal Integrability Analysis (3 days)
- **Day 13**: Temporal integral search
- **Day 14**: Compare spatial-only vs. spatial+temporal
- **Day 15**: SU(2) × Time symmetry analysis

### Phase 6: Documentation (2 days)
- **Day 16**: Technical report on coupled regularization
- **Day 17**: Final validation, comparative results

**Total**: 17 days (extended from original 15 days)

---

## Success Criteria (AMENDED)

### Functional Requirements
- [ ] Extended KS transform with time tracking implemented
- [ ] Bilinear relation validated: $r = |\mathbf{u}|^2$ (error < 1e-12)
- [ ] **Time relation validated**: $dt/ds = \Omega(u)$ (error < 1e-12)
- [ ] Pairwise system with unified time functional
- [ ] **Dual energy conservation**: Both $E$ and $\mathcal{K}$ conserved (drift < 1e-10)
- [ ] Time-regularized RATTLE passes all tests

### Scientific Requirements
- [ ] **Collision Regularization with Time**: Integrate through $r_{ij} < 10^{-5}$
  - Track time dilation factor $\Omega(s)$ during approach
  - Verify smooth passage in fictitious time $s$
  - Demonstrate velocity remains bounded in $(s, u)$ coordinates
- [ ] **Temporal Integrability**:
  - Identify conserved quantities related to time structure
  - Test: Does inclusion of time provide additional integrals?
  - Compare number of integrals: KS-only vs. KS+time
- [ ] **Comparative Analysis**:
  - Demonstrate spatial-only KS **fails** at collisions
  - Show spatial+temporal KS **succeeds**
  - Quantify advantage of coupled regularization

### Quality Requirements
- [ ] Test coverage > 95% (including time-related tests)
- [ ] Complete API documentation for extended structures
- [ ] Technical report: "Why Time Regularization is Necessary"
- [ ] Visualization: Time dilation factor $\Omega(s)$ along trajectories

---

## References (AMENDED)

### Original References (Spatial KS)
1. Kustaanheimo & Stiefel (1965): "Perturbation theory based on spinor regularization"
2. Stiefel & Scheifele (1971): *Linear and Regular Celestial Mechanics*
3. Waldvogel (2006): "Quaternions and the perturbed Kepler problem"
4. Aarseth (2003): *Gravitational N-Body Simulations*

### Time Regularization (NEW)
5. **Sundman** (1912): "Mémoire sur le problème des trois corps" — Original time transformation
6. **Levi-Civita** (1920): "Sur la régularisation" — Early regularization theory
7. **Moser** (1970): "Regularization of Kepler's problem" — Modern perspective
8. **Arnol'd** (2006): *Mathematical Aspects of Classical Mechanics* §3.5
9. **Ferrer & Osácar** (1994): "Harrington's Hamiltonian" — Time scaling in stellar problem
10. **Heggie** (1974): "Global regularization of N-body problem"

### Extended Hamiltonian Formalism (NEW)
11. **Dirac** (1964): *Lectures on Quantum Mechanics* — Constraint formalism
12. **Henneaux & Teitelboim** (1992): *Quantization of Gauge Systems* — First-class constraints
13. **Arnold & Givental** (2001): "Symplectic Geometry" §7: Contact geometry
14. **Libermann & Marle** (1987): *Symplectic Geometry* Ch. VIII: Contact manifolds

### Geometric Perspective (NEW)
15. **Montgomery** (1988): "Gauge fields and geometric phases"
16. **Cushman & Bates** (1997): *Global Aspects* Ch. 6: KS as symplectic map
17. **Marsden & Ratiu** (1999): *Mechanics and Symmetry* Ch. 6: Momentum maps

---

## Appendix: Why Spatial and Temporal Regularization Must Be Coupled

### The Failure of Partial Regularization

**Experiment**: Try to regularize collisions using only one transformation:

#### Spatial-Only (KS without time transformation)
- Transform: $r \to u$ (spatial lift)
- Keep: Physical time $t$ (no time transformation)
- Result at collision ($r \to 0$, i.e., $|u| \to 0$):
  - ✓ Potential regular: $V(u) = -k/|u|^2$ has cancellation
  - ✗ **Velocity diverges**: $v = dr/dt \to \infty$
  - ✗ Integration fails due to steep gradients in $(t, u)$ space

#### Temporal-Only (Sundman without spatial lift)
- Transform: $t \to s$ with $dt/ds = r$ (time transformation)
- Keep: Physical coordinates $r$ (no spatial lift)
- Result at collision ($r \to 0$):
  - ✓ Velocity bounded in $s$: $dr/ds = v \cdot (dt/ds) = v \cdot r$ regular
  - ✗ **Force diverges**: $F = -k/r^2 \to -\infty$ in $s$ coordinates
  - ✗ Integration fails due to force singularity

#### Coupled (KS + Sundman)
- Transform: $(t, r) \to (s, u)$ simultaneously
- Result at collision:
  - ✓ Potential regular (from KS)
  - ✓ Velocity regular (from time transformation)
  - ✓ **Complete smoothness**: All derivatives bounded
  - ✓ Integration succeeds through collision

### Mathematical Explanation

The complete regularized Hamiltonian is:
$$
\mathcal{K} = \Omega(u) \cdot H(u) = |u|^{-2} \left[\frac{|p_u|^2}{2m} - k\right]
$$

The factor $|u|^{-2}$ appears from:
1. **Time transformation**: $\Omega^{-1} = 1/|u|^2$ (from $dt/ds = |u|^2$)
2. **Rescaling Hamiltonian**: $\mathcal{K} = \Omega^{-1} H$

This creates exact cancellation:
$$
\mathcal{K}(u \to 0) = \frac{1}{|u|^2}\underbrace{\left[\frac{|p_u|^2}{2m} - k\right]}_{\text{remains finite}}
$$

The numerator stays bounded because:
- As $|u| \to 0$, kinetic energy $|p_u|^2/(2m) \to k$ (energy conservation)
- The combination $[T - V]$ approaches zero, exactly canceling the $1/|u|^2$ divergence

**This cancellation requires BOTH transformations**—neither alone achieves it.

---

**Document Version**: 1.0 (Amended)
**Last Updated**: 2025-11-20
**Amendment**: Comprehensive integration of time regularization as fundamental coupling
**Status**: Ready for Implementation with Extended Time Structures

**Key Amendment**: Time regularization is no longer treated as auxiliary—it is now recognized as **equally fundamental** to spatial regularization. The KS transformation is truly a **4+1 dimensional lift** (4 spatial + 1 temporal), not merely a 3→4 spatial embedding.
