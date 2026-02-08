# WP 2.2: S¹ "Untwisting" Lift Construction
## Work Package 2 - Geometric Reduction and Shape Space Analysis
## **AMENDED VERSION - Time Regularization Connections**

**Status**: Design Phase (Amended)
**Priority**: Critical Path for Lift-Integrability Hypothesis
**Estimated Duration**: 10-14 days (extended)
**Dependencies**: Task 2.1.2 Complete (Connection and Curvature)
**Amendment Date**: 2025-11-20
**Amendment**: Explicit discussion of temporal structure in S¹ lift and comparison with time regularization

---

## Table of Contents

1. [Overview](#overview)
2. [Mathematical Background: Spatial vs. Temporal Lifts](#mathematical-background-spatial-vs-temporal-lifts)
3. [Time Parametrization in the S¹ Lift](#time-parametrization-in-the-s1-lift)
4. [Part A: Principal Bundle Construction](#part-a-principal-bundle-construction)
5. [Part B: Extended Symplectic Form](#part-b-extended-symplectic-form)
6. [Part C: Lifted Dynamics and Integration](#part-c-lifted-dynamics-and-integration)
7. [Part D: Integrability Search](#part-d-integrability-search)
8. [Part E: Time Regularization Extension (NEW)](#part-e-time-regularization-extension-new)
9. [Comparison: S¹ Lift vs. KS Regularization (NEW)](#comparison-s1-lift-vs-ks-regularization-new)
10. [Implementation Schedule](#implementation-schedule)
11. [Success Criteria](#success-criteria)

---

## Overview (AMENDED)

### Purpose

WP 2.2 implements the **S¹ "untwisting" lift**—a minimal spatial dimensional increase that attempts to eliminate the magnetic connection by working in an extended phase space. This lift is **primarily spatial** (not temporal), in contrast to the KS lift (WP2.3) which combines spatial and temporal regularization.

**Key Distinction** (AMENDED):
- **S¹ Lift**: Adds spatial fiber, keeps physical time $t$ unchanged
- **KS Lift**: Transforms both space ($r \to u$) and time ($t \to s$)

### Geometric Idea

The connection one-form $\mathcal{A}$ discovered in Task 2.1.2 acts like a "magnetic field" on shape space. The S¹ bundle construction:
1. Adds a **spatial fiber** $S^1$ over each point in shape space
2. Introduces fiber coordinate $\theta \in [0, 2\pi)$ tracking "winding"
3. Creates extended symplectic form $\widetilde{\omega}$ including fiber contribution
4. **Does NOT transform time**—dynamics still evolve in physical time $t$

### Time Treatment in S¹ Lift

**IMPORTANT CLARIFICATION**:

The S¹ lift operates in **physical time** $t$:
$$
\frac{d}{dt}\begin{pmatrix} s \\ \theta \\ p_s \\ p_\theta \end{pmatrix} = \widetilde{X}_H
$$

where:
- $s \in$ Shape Space (base coordinates)
- $\theta \in S^1$ (fiber coordinate)
- Time $t$ remains **un-regularized** (physical clock)
- No Sundman transformation applied

This contrasts with KS lift which uses **fictitious time** $s_{\text{fict}}$ with $dt/ds_{\text{fict}} = r$.

---

## Mathematical Background: Spatial vs. Temporal Lifts

### Two Independent Lift Strategies

There are two distinct ways to "lift" a dynamical system:

#### 1. Spatial Lift (S¹ Bundle)
**Goal**: Eliminate spatial curvature/twist in connections

**Method**:
- Extend configuration space: $Q \to Q \times S^1$
- Add fiber coordinate $\theta$ (angular variable)
- Lift symplectic form to include fiber: $\omega \to \omega + d\theta \wedge dA$

**What it Achieves**:
- "Untwists" magnetic connection in space
- May reveal hidden spatial symmetries
- Does **NOT** regularize collision singularities

**Time Treatment**: Uses physical time $t$ (unchanged)

#### 2. Temporal Lift (Time Regularization)
**Goal**: Eliminate temporal singularities (collisions, divergences)

**Method**:
- Extend with time pair: $(t, E) \in T^*\mathbb{R}$
- Reparametrize: $t \to s$ with $dt/ds = \Omega(q)$
- Rescale Hamiltonian: $H \to \mathcal{K} = \Omega^{-1} H$

**What it Achieves**:
- Regularizes velocity singularities at collisions
- Smooths trajectories in new time coordinate
- Does **NOT** necessarily simplify spatial structure

**Space Treatment**: May keep original spatial coordinates (or combine with spatial lift)

### Can They Be Combined?

**YES**: The two lifts are **independent and compatible**:

**Combined Lift (Maximal)**:
- Configuration: $(q, \theta, s) \in Q \times S^1 \times \mathbb{R}$
- Phase space: $(q, p_q, \theta, p_\theta, s, \mathcal{K})$
- Symplectic form: $\omega_Q + d\theta \wedge dA + d\mathcal{K} \wedge ds$
- **Advantages**:
  - Spatial curvature reduced (from S¹)
  - Temporal singularities regularized (from time reparametrization)
  - Maximum "room" for hidden integrability

**WP2.2 (This Document)**: Implements spatial S¹ lift **only**
**WP2.3 (KS)**: Implements spatial (KS) **and** temporal (Sundman) lift **together**
**Future Work**: Combined S¹ × Time could be explored

---

## Time Parametrization in the S¹ Lift

### Physical Time Evolution

In the S¹ bundle, Hamilton's equations use **physical time** $t$:

**Bundle Coordinates**: $(s, \theta, p_s, p_\theta) \in T^*(S \times S^1)$

**Equations of Motion**:
$$
\frac{ds^i}{dt} = \frac{\partial \widetilde{H}}{\partial p_{s_i}}
$$
$$
\frac{d\theta}{dt} = \frac{\partial \widetilde{H}}{\partial p_\theta}
$$
$$
\frac{dp_{s_i}}{dt} = -\frac{\partial \widetilde{H}}{\partial s^i}
$$
$$
\frac{dp_\theta}{dt} = -\frac{\partial \widetilde{H}}{\partial \theta}
$$

**Key Point**: All derivatives are with respect to physical time $t$, NOT fictitious time.

### Why S¹ Lift Does Not Regularize Collisions

At a collision ($r_{ij} \to 0$):
- Potential still diverges: $V(s) \sim -1/r_{ij} \to -\infty$
- Velocity diverges: $\dot{r}_{ij} \to \infty$ in physical time
- Fiber coordinate $\theta$ cannot "absorb" this singularity
- **Integration fails** if collision occurs

**S¹ lift is NOT a regularization**—it is a geometric transformation for integrability search.

### Hybrid Strategy: S¹ Lift + Time Regularization

**Proposal** (for future work):

Combine S¹ bundle with Sundman time transformation:
1. Spatial lift: Shape space → S¹ bundle (eliminate spatial curvature)
2. Temporal lift: $t \to s$ with $dt/ds = \Omega(s, \theta)$ (regularize collisions)

**Extended Phase Space**:
- Config: $(s, \theta, s_{\text{fict}}) \in S \times S^1 \times \mathbb{R}$
- Phase: $(s, p_s, \theta, p_\theta, s_{\text{fict}}, \mathcal{K}, t, E)$
- Dimension: $(3 + 1 + 1) \times 2 = 10$-dimensional phase space

**Advantages**:
- Benefits of S¹ lift (geometric simplification)
- Benefits of time regularization (collision handling)
- Potentially strongest approach to hidden integrability

**Not Implemented in WP2.2**: This is **pure S¹ lift** without time transformation.

---

## Part A: Principal Bundle Construction

### Bundle Structure (with Time Clarification)

**Principal S¹ Bundle**:
$$
S^1 \hookrightarrow P \xrightarrow{\pi} S
$$

- **Base**: $S$ = Shape space (configuration)
- **Total Space**: $P = S \times S^1$ (extended configuration)
- **Fiber**: $S^1$ = Circle (1D)

**Phase Space**: $T^*P = T^*S \times T^*S^1$
- Coordinates: $(s, \theta, p_s, p_\theta)$
- **Time**: Physical time $t$ (parameter, not coordinate)

### Time as Parameter vs. Coordinate

In the S¹ lift framework:

**Time is a PARAMETER**:
- Trajectories are curves $(s(t), \theta(t), p_s(t), p_\theta(t))$ parametrized by $t$
- $t \in \mathbb{R}$ is **not a phase space coordinate**
- Evolution: $\dot{z} = \widetilde{X}_H(z)$ where $\dot{} = d/dt$

**Contrast with Extended Hamiltonian**:
- In extended formalism: $(q, p, t, E)$ with $t$ as coordinate
- In S¹ lift: $(s, \theta, p_s, p_\theta)$ with $t$ as parameter

This is a **standard** (not extended) Hamiltonian system, just in higher-dimensional space.

---

## Part B: Extended Symplectic Form

### Construction (Time-Independent)

The lifted symplectic form is:
$$
\widetilde{\omega} = \omega_{shape} + d\theta \wedge d(L \cdot \mathcal{A})
$$

**Key Property**: $\widetilde{\omega}$ is **time-independent**:
$$
\frac{d\widetilde{\omega}}{dt} = 0
$$

This contrasts with systems where time transformation couples to symplectic structure.

### Lifted Hamiltonian (Time-Independent)

The Hamiltonian on bundle:
$$
\widetilde{H}(s, \theta, p_s, p_\theta) = H_{red}(s, p_s)
$$

**Crucially**: $\widetilde{H}$ is **independent of both**:
1. Fiber coordinate $\theta$ (gives conservation of $p_\theta$)
2. Time $t$ (gives conservation of $\widetilde{H}$ itself)

**No time transformation**: Hamiltonian keeps same form as reduced system.

---

## Part C: Lifted Dynamics and Integration

### Integration in Physical Time

```python
def integrate_s1_bundle_physical_time(
    initial_state: BundleState,
    t_span: tuple[float, float],
    lifted_hamiltonian: LiftedHamiltonian,
    symplectic_form: ExtendedSymplecticForm
) -> BundleTrajectory:
    """
    Integrate S¹ bundle dynamics in PHYSICAL TIME t.

    Uses standard ODE integrator with t as independent variable.
    NO time regularization applied.

    Args:
        initial_state: Initial bundle state
        t_span: Physical time interval (t_start, t_end)
        lifted_hamiltonian: H̃(s, θ, p_s, p_θ)
        symplectic_form: ω̃

    Returns:
        Trajectory in bundle space, parametrized by physical time t
    """
    from scipy.integrate import solve_ivp

    def rhs(t, z):
        """Hamilton's equations in physical time"""
        state = BundleState.from_vector(z)

        # Compute Hamiltonian vector field
        X_H = hamiltonian_vector_field_bundle(
            state, lifted_hamiltonian, symplectic_form
        )

        return X_H

    # Integrate using physical time t
    z0 = initial_state.to_vector()
    solution = solve_ivp(
        rhs,
        t_span,
        z0,
        method='DOP853',
        dense_output=True
    )

    # Extract trajectory
    states = [BundleState.from_vector(z) for z in solution.y.T]

    return BundleTrajectory(
        times=solution.t,  # Physical times
        states=states
    )
```

### Collision Handling (or Lack Thereof)

**IMPORTANT**: S¹ lift does **NOT** regularize collisions.

```python
def attempt_collision_passage_s1_lift(
    cart_state_near_collision: CartesianState,
    masses: Masses,
    t_span: tuple[float, float]
) -> dict:
    """
    Attempt to integrate through collision with S¹ lift.

    Expected: FAILURE at collision (unless we add time regularization).
    """
    # Convert to shape space
    shape_state = cartesian_to_shape_space(cart_state_near_collision, masses)

    # Lift to S¹ bundle
    bundle_state = lift_to_s1_bundle(shape_state, theta_init=0.0, p_theta_init=0.0)

    # Attempt integration in physical time
    try:
        trajectory = integrate_s1_bundle_physical_time(
            bundle_state,
            t_span,
            lifted_hamiltonian,
            extended_symplectic_form
        )

        result = {
            'success': True,
            'message': "S¹ lift handled collision (unexpected!)",
            'min_radius': compute_min_radius(trajectory)
        }

    except IntegrationError as e:
        result = {
            'success': False,
            'message': "S¹ lift failed at collision (as expected)",
            'error': str(e),
            'reason': "Velocity singularity in physical time"
        }

    return result
```

**Conclusion**: For collision-prone systems, S¹ lift alone is insufficient. Must combine with time regularization or use KS lift (WP2.3).

---

## Part D: Integrability Search

### Conserved Quantities in S¹ Lift

**Standard Integrals**:
1. **Energy**: $E = \widetilde{H}(s, \theta, p_s, p_\theta)$ (time-translation invariance)
2. **Angular Momentum**: $L$ (from spatial rotational symmetry, if present)
3. **Fiber Momentum**: $p_\theta$ (from $\theta$-independence of $\widetilde{H}$)

**Counting**: For planar 3BP:
- Shape space dimension: 3D configuration, 6D phase space
- S¹ lift: 4D configuration, 8D phase space
- Integrability requires: 4 independent integrals
- Have: 3 (E, L, p_θ)
- **Need**: 1 more integral

**Question**: Does S¹ lift reveal a fourth integral not visible in shape space?

---

## Part E: Time Regularization Extension (NEW)

### Proposal: S¹ Lift with Sundman Transformation

To handle collisions while maintaining S¹ structure, we can extend the lift:

**Extended System**:
- Spatial: S¹ bundle (as in standard WP2.2)
- Temporal: Sundman transformation $dt/ds = \Omega(s)$

**Phase Space**: $(s, \theta, p_s, p_\theta, s_{\text{fict}}, \mathcal{K}, t, E)$

**Regularized Hamiltonian on S¹ Bundle**:
$$
\mathcal{K}_{S^1}(s, \theta, p_s, p_\theta) = \Omega(s)^{-1} \cdot \widetilde{H}(s, \theta, p_s, p_\theta)
$$

where $\Omega(s) = f(r_{12}, r_{23}, r_{31})$ is chosen to regularize collisions.

**Equations of Motion** (in fictitious time):
$$
\frac{ds^i}{ds_{\text{fict}}} = \frac{\partial \mathcal{K}_{S^1}}{\partial p_{s_i}}
$$
$$
\frac{d\theta}{ds_{\text{fict}}} = \frac{\partial \mathcal{K}_{S^1}}{\partial p_\theta}
$$

**Time Evolution**:
$$
\frac{dt}{ds_{\text{fict}}} = \Omega(s)
$$

### Implementation Sketch

```python
class S1BundleWithTimeRegularization:
    """
    S¹ bundle lift combined with time regularization.

    Provides both:
        - Spatial geometric simplification (S¹)
        - Temporal collision regularization (Sundman)
    """

    def __init__(self, time_dilation_function):
        self.Omega = time_dilation_function

    def regularized_hamiltonian(
        self,
        bundle_state: BundleState
    ) -> float:
        """
        Regularized Hamiltonian on S¹ bundle.

        K_S1 = Ω⁻¹(s) · H̃(s, θ, p_s, p_θ)
        """
        s = bundle_state.shape_state
        Omega = self.Omega(s)

        H_lifted = self.lifted_hamiltonian(bundle_state)

        return H_lifted / Omega

    def integrate_fictitious_time(
        self,
        initial_state: BundleState,
        s_fict_span: tuple[float, float],
        n_steps: int
    ) -> EnhancedBundleTrajectory:
        """
        Integrate in fictitious time, tracking both s_fict and t.
        """
        # ... implementation similar to KS integrator with time tracking
        pass
```

### Comparison: Three Strategies

| Strategy | Spatial Lift | Temporal Lift | Collision Handling | Integrability Search |
|----------|--------------|---------------|-------------------|----------------------|
| **Shape Space Only** | None | None | ✗ Fails | Limited |
| **S¹ Lift (WP2.2)** | S¹ bundle | None | ✗ Fails | Enhanced |
| **KS Lift (WP2.3)** | KS spinor | Sundman | ✓ Regularized | Enhanced |
| **S¹ + Time (Proposed)** | S¹ bundle | Sundman | ✓ Regularized | Maximized? |

---

## Comparison: S¹ Lift vs. KS Regularization (NEW)

### Fundamental Differences

#### S¹ Lift
**Nature**: Geometric integrability search (NOT regularization)
**Goal**: Eliminate spatial curvature obstructions
**Method**: Add fiber to "untwist" connection
**Time**: Physical time $t$ (unchanged)
**Collision**: NOT handled
**Best for**: Systems without close encounters, integrability analysis

#### KS Regularization
**Nature**: Coupled spatial-temporal regularization
**Goal**: Smooth collisions, enable long-term integration
**Method**: Spinor spatial lift + fictitious time
**Time**: Fictitious time $s$ with $dt/ds = r$
**Collision**: Fully regularized
**Best for**: Collision-prone dynamics, long-term chaos studies

### When to Use Each

**Use S¹ Lift When**:
- Interested in geometric structure of integrability obstructions
- System is well-behaved (no collisions expected)
- Want minimal complexity (4D phase space extension vs. 10D for KS)
- Studying connection curvature effects

**Use KS Regularization When**:
- Collisions or near-collisions occur
- Long-term integration required
- Studying scattering problems
- Need numerical robustness

**Use Both (Future)**:
- Maximum integrability search space
- Collision regularization + geometric untwisting
- Research question: Are they complementary?

---

## Implementation Schedule (AMENDED)

### Phase 1: Bundle Construction (3 days)
- **Day 1**: S¹ bundle data structures, charts
- **Day 2**: Transition functions, validation
- **Day 3**: Unit tests, documentation

### Phase 2: Extended Symplectic Form (2 days)
- **Day 4**: Implement extended form
- **Day 5**: Closedness verification, Poisson brackets

### Phase 3: Lifted Dynamics in Physical Time (3 days)
- **Day 6**: Hamiltonian vector field, equations
- **Day 7**: Integration in physical time $t$
- **Day 8**: Conservation verification, projection tests

### Phase 4: Integrability Analysis (3 days)
- **Day 9**: Three-integral verification, involution tests
- **Day 10**: Fourth integral search
- **Day 11**: Compare with shape space dynamics

### Phase 5: Time Regularization Extension (NEW, Optional, 2 days)
- **Day 12**: Design S¹ + Sundman hybrid system
- **Day 13**: Implement and test hybrid approach

### Phase 6: Documentation (1 day)
- **Day 14**: Technical report, comparative analysis with KS

**Total**: 14 days (extended from 12 with time regularization discussion)

---

## Success Criteria (AMENDED)

### Functional Requirements
- [ ] S¹ bundle correctly constructed (passes cocycle tests)
- [ ] Extended symplectic form is closed: $d\widetilde{\omega} = 0$
- [ ] Fiber momentum $p_\theta$ is conserved during integration **in physical time**
- [ ] Projection π(lifted) = reduced trajectory (error < 1e-10)

### Time-Related Understanding (NEW)
- [ ] **Document distinction**: Physical time (S¹) vs. fictitious time (KS)
- [ ] **Collision behavior**: Demonstrate S¹ lift does NOT regularize (expected failure)
- [ ] **Hybrid design**: Sketch S¹ + time regularization extension
- [ ] **Comparative analysis**: S¹ vs. KS trade-offs documented

### Scientific Requirements
- [ ] **Primary Question**: Is the 3BP integrable on S¹ bundle (excluding collisions)?
  - If YES: Construct action-angle coordinates
  - If NO: Document obstruction, quantify improvement over shape space
- [ ] **Secondary Question**: Would adding time regularization to S¹ lift help?
  - Theoretical analysis of S¹ × Time system
  - Comparison with pure KS approach

### Quality Requirements
- [ ] Test coverage > 95%
- [ ] Complete API documentation
- [ ] Technical report: "S¹ Lift as Geometric Tool vs. KS as Regularization"
- [ ] Visualization: Fiber dynamics, comparison with KS

---

## References (AMENDED)

### S¹ Bundle and Symplectic Reduction
1. Marsden & Ratiu, *Introduction to Mechanics and Symmetry* (1999)
2. Guillemin & Sternberg, *Symplectic Techniques in Physics* (1984)
3. Montgomery, "The connection whose holonomy is the classical adiabatic angles" (1988)
4. Cushman & Bates, *Global Aspects of Classical Integrable Systems* (1997)

### Time Regularization (for Comparison)
5. Sundman (1912): "Mémoire sur le problème des trois corps"
6. Moser (1970): "Regularization of Kepler's problem and the averaging method"
7. Stiefel & Scheifele (1971): *Linear and Regular Celestial Mechanics*

### Hybrid Approaches (Advanced)
8. Ferrer & Osácar (1994): "Harrington's Hamiltonian in the stellar problem"
9. Heggie (1974): "A global regularization of the gravitational N-body problem"
10. Waldvogel (2008): "Quaternions for regularizing Celestial Mechanics"

---

## Appendix: Why S¹ Lift Alone Does Not Regularize

### The Nature of the S¹ Construction

The S¹ lift adds a **spatial fiber**, creating:
$$
P = S \times S^1 \quad (\text{configuration space})
$$

This extends the **spatial geometry** but does **NOT** touch the **temporal structure**.

### What Happens at Collision?

Consider a binary collision where $r_{12} \to 0$:

**In Shape Space**:
- Potential: $V \sim -1/r_{12} \to -\infty$
- Velocity: $|\dot{r}_{12}| \to \infty$ (in physical time $t$)

**In S¹ Bundle**:
- Lift: $(s, \theta) \in S \times S^1$ where $s$ includes $r_{12}$
- Potential: Still $\sim -1/r_{12} \to -\infty$ (fiber doesn't change potential)
- Velocity: Still $|\dot{s}| \to \infty$ (derivatives in physical time $t$)
- **Fiber coordinate $\theta$**: Tracks "winding" but doesn't absorb singularity

**Conclusion**: The S¹ fiber provides **spatial geometric structure** but cannot regularize **temporal singularities** ($d/dt$ divergences).

### What Would Be Needed?

To regularize collisions in S¹ lift, must add **time transformation**:
$$
\frac{dt}{ds_{\text{fict}}} = \Omega(s) \sim r_{12}
$$

Then velocities transform as:
$$
\frac{ds}{dt} \to \frac{ds}{ds_{\text{fict}}} = \frac{ds}{dt} \cdot \frac{dt}{ds_{\text{fict}}} = \dot{s} \cdot r_{12}
$$

The factor $r_{12}$ cancels the divergence, regularizing the system.

**This is precisely what KS does** (with spatial lift as well).

---

**Document Version**: 1.0 (Amended)
**Last Updated**: 2025-11-20
**Amendment**: Explicit treatment of time parametrization, comparison with time regularization, and hybrid S¹ × Time discussion
**Status**: Ready for Implementation (Standard S¹ Lift)
**Future Work**: Explore S¹ + Sundman hybrid for collision-regularized geometric analysis

**Key Takeaway**: S¹ lift is a **geometric tool** for integrability search, not a regularization. For collisions, use KS (spatial+temporal) or consider hybrid S¹ × Time approach.
