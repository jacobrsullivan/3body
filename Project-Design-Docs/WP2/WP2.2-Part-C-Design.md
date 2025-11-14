# WP 2.2 Part C: Lifted Dynamics & Integration - Detailed Design

**Task**: WP 2.2 - S¹ "Untwisting" Lift Construction
**Part**: C - Lifted Dynamics and Integration
**Status**: Design Phase
**Estimated Duration**: 3 days
**Dependencies**: WP 2.2 Parts A & B Complete

---

## Table of Contents

1. [Overview](#overview)
2. [Mathematical Background](#mathematical-background)
3. [Data Structures](#data-structures)
4. [Core Algorithms](#core-algorithms)
5. [Implementation Details](#implementation-details)
6. [Validation Strategy](#validation-strategy)
7. [Performance Targets](#performance-targets)
8. [Integration Points](#integration-points)
9. [Success Criteria](#success-criteria)

---

## Overview

### Purpose

Part C implements the **Hamiltonian dynamics** on the S¹ bundle and provides high-quality numerical integration. This is where we actually solve the equations of motion in the lifted space and verify that:

1. **Conservation**: Fiber momentum $p_\theta$ is conserved
2. **Consistency**: Projection to shape space recovers original dynamics
3. **Advantages**: Lifted dynamics may be simpler/more regular

**Key Question**: Does lifting to the bundle make the three-body problem integrable?

### Mathematical Setup

**Lifted Hamiltonian**: $\widetilde{H}: T^*P \to \mathbb{R}$

$$\widetilde{H}(s, \theta, p_s, p_\theta) = H_{\text{red}}(s, p_s)$$

**Remarkable Property**: $\widetilde{H}$ is **independent of $\theta$**!

This immediately implies:
$$\frac{\partial \widetilde{H}}{\partial \theta} = 0 \quad \Rightarrow \quad \{p_\theta, \widetilde{H}\} = 0$$

So $p_\theta$ is a **conserved quantity** (the third integral we're looking for!).

**Hamilton's Equations** on the bundle:

$$\dot{z}^i = \{\widetilde{H}, z^i\} = \widetilde{\omega}^{ij} \frac{\partial \widetilde{H}}{\partial z^j}$$

where $z = (s, \theta, p_s, p_\theta)$ are bundle coordinates.

### Objectives

1. **Vector Field**: Implement Hamiltonian vector field $X_{\widetilde{H}}$ on bundle
2. **Integration**: Numerical integration of bundle dynamics
3. **Conservation Verification**: Check $p_\theta = \text{const}$, $E = \text{const}$
4. **Projection Validation**: Verify $\pi(\text{lifted trajectory}) = \text{reduced trajectory}$
5. **Comparison**: Compare lifted vs. reduced dynamics (regularity, chaos indicators)
6. **Symplectic Integration**: Preserve symplectic structure during integration

### Deliverables

- `LiftedHamiltonian` class
- `BundleIntegrator` class (symplectic integrator)
- `BundleTrajectory` data structure
- Conservation monitoring
- Projection operators
- Validation framework
- Comparison tools

---

## Mathematical Background

### Hamiltonian Vector Fields

Given Hamiltonian $H$ and symplectic form $\omega$, the **Hamiltonian vector field** $X_H$ is defined by:

$$\omega(X_H, \cdot) = dH$$

In coordinates:
$$X_H^i = \omega^{ij} \frac{\partial H}{\partial z^j}$$

**Hamilton's equations**:
$$\dot{z} = X_H(z)$$

### Lifted Hamiltonian Independence

For our system:
$$\widetilde{H}(s, \theta, p_s, p_\theta) = H_{\text{red}}(s, p_s)$$

Taking derivatives:
$$\frac{\partial \widetilde{H}}{\partial \theta} = 0, \quad \frac{\partial \widetilde{H}}{\partial p_\theta} = 0$$

**Hamilton's equations become**:
\begin{align}
\dot{s}^i &= \widetilde{\omega}^{ij} \frac{\partial \widetilde{H}}{\partial p_j} \\
\dot{\theta} &= \widetilde{\omega}^{\theta j} \frac{\partial \widetilde{H}}{\partial z^j} \\
\dot{p}_i &= -\widetilde{\omega}^{ij} \frac{\partial \widetilde{H}}{\partial s^j} \\
\dot{p}_\theta &= -\widetilde{\omega}^{\theta j} \frac{\partial \widetilde{H}}{\partial s^j} = 0
\end{align}

The last equation shows $p_\theta$ is conserved!

### Symplectic Integration

**Goal**: Preserve the symplectic structure $\widetilde{\omega}$ during numerical integration.

**Standard methods** (RK4, etc.) do NOT preserve symplectic structure → energy drift, spurious dissipation.

**Symplectic integrators** (Verlet, implicit midpoint, etc.) satisfy:
$$\widetilde{\omega}(z_n) = \widetilde{\omega}(z_0)$$

up to roundoff error, ensuring long-term stability and energy conservation.

### Projection to Reduced Dynamics

**Projection**: $\pi: P \to S$ forgets fiber coordinate

$$\pi(s, \theta, p_s, p_\theta) = (s, p_s)$$

**Claim**: If $z(t)$ solves Hamilton's equations on $P$, then $\pi(z(t))$ solves reduced dynamics on $S$.

**Why?** The lifted Hamiltonian is just the pullback of the reduced Hamiltonian, so dynamics project correctly.

**Validation Test**: Integrate both systems, compare projections.

---

## Data Structures

### LiftedHamiltonian

```python
# File: src/python/lifts/lifted_hamiltonian.py

from dataclasses import dataclass
from typing import Callable, Optional
import numpy as np
from .s1_bundle import BundleState
from ..core.masses import Masses

@dataclass(frozen=True)
class LiftedHamiltonian:
    """
    Hamiltonian on S¹ bundle (pullback of reduced Hamiltonian).

    H̃(s, θ, p_s, p_θ) = H_red(s, p_s)

    Key property: Independent of θ and p_θ!
    This immediately gives p_θ as a conserved quantity.

    Attributes:
        reduced_hamiltonian: H_red from shape space dynamics
        masses: Three-body masses
        energy: Total energy (conserved)
        metadata: Optional auxiliary data

    Examples:
        >>> lifted_H = LiftedHamiltonian(H_red, masses, energy=-1.0)
        >>> energy_value = lifted_H.evaluate(bundle_state)
        >>> # Check independence
        >>> lifted_H.is_theta_independent()
        True
    """
    reduced_hamiltonian: Callable
    masses: Masses
    energy: float
    metadata: Optional[dict] = None

    def evaluate(self, state: BundleState) -> float:
        """
        Evaluate H̃ at bundle state.

        Note: Result independent of θ and p_θ by construction!

        Args:
            state: Point in bundle phase space

        Returns:
            H̃(state) (scalar)

        Examples:
            >>> state1 = BundleState(shape, theta=0.0, momenta, p_theta=0.5)
            >>> state2 = BundleState(shape, theta=np.pi, momenta, p_theta=1.5)
            >>> # Should give same result (only shape + shape momenta matter)
            >>> lifted_H.evaluate(state1) == lifted_H.evaluate(state2)
            True
        """
        return self.reduced_hamiltonian(
            state.shape_state,
            state.shape_momenta,
            self.masses,
            self.energy
        )

    def gradient(
        self,
        state: BundleState,
        epsilon: float = 1e-8
    ) -> np.ndarray:
        """
        Compute gradient ∂H̃/∂z via finite differences.

        Returns:
            Gradient vector (8,) = [∂H̃/∂s, ∂H̃/∂θ, ∂H̃/∂p_s, ∂H̃/∂p_θ]

        Note:
            - ∂H̃/∂θ = 0 (theta independence)
            - ∂H̃/∂p_θ = 0 (p_theta independence)

        Examples:
            >>> grad = lifted_H.gradient(state)
            >>> # Check theta independence
            >>> abs(grad[3]) < 1e-12  # ∂H̃/∂θ ≈ 0
            True
            >>> abs(grad[7]) < 1e-12  # ∂H̃/∂p_θ ≈ 0
            True
        """
        H_center = self.evaluate(state)
        gradient = np.zeros(8)  # 8D phase space

        state_vector = state.to_vector()

        for i in range(8):
            # Forward perturbation
            perturbed = state_vector.copy()
            perturbed[i] += epsilon

            state_perturbed = BundleState.from_vector(
                perturbed,
                L=state.shape_state.L
            )

            H_perturbed = self.evaluate(state_perturbed)

            # Finite difference
            gradient[i] = (H_perturbed - H_center) / epsilon

        return gradient

    def is_theta_independent(
        self,
        test_state: BundleState,
        tolerance: float = 1e-10
    ) -> bool:
        """
        Verify ∂H̃/∂θ = 0.

        Args:
            test_state: State where to test
            tolerance: Numerical tolerance

        Returns:
            True if theta-independent

        Examples:
            >>> lifted_H.is_theta_independent(state)
            True
        """
        gradient = self.gradient(test_state)

        # Check ∂H̃/∂θ (index 3) and ∂H̃/∂p_θ (index 7)
        dH_dtheta = abs(gradient[3])
        dH_dp_theta = abs(gradient[7])

        return (dH_dtheta < tolerance) and (dH_dp_theta < tolerance)

    def hamiltonian_vector_field(
        self,
        state: BundleState,
        symplectic_form: 'ExtendedSymplecticForm'
    ) -> np.ndarray:
        """
        Compute Hamiltonian vector field X_H̃ at state.

        X_H̃ = ω̃^{-1}(dH̃)

        Args:
            state: Point in bundle
            symplectic_form: Extended symplectic form

        Returns:
            Vector field [ṡ, θ̇, ṗ_s, ṗ_θ]

        Examples:
            >>> X_H = lifted_H.hamiltonian_vector_field(state, form)
            >>> # ṗ_θ should be ≈ 0 (conservation)
            >>> abs(X_H[7]) < 1e-12
            True
        """
        # Compute gradient dH̃
        dH = self.gradient(state)

        # Get inverse symplectic form
        omega_inv = symplectic_form.inverse(state)

        # Vector field: X = ω^{-1}(dH)
        X_H = omega_inv @ dH

        return X_H


@dataclass
class BundleTrajectory:
    """
    Trajectory in the S¹ bundle.

    Attributes:
        times: Time points [t_0, t_1, ..., t_n]
        states: Bundle states [z(t_0), z(t_1), ..., z(t_n)]
        initial_state: Initial condition
        metadata: Optional auxiliary data (integrator stats, etc.)

    Examples:
        >>> trajectory = BundleTrajectory(
        ...     times=np.linspace(0, 10, 1000),
        ...     states=integrated_states,
        ...     initial_state=z0
        ... )
        >>> trajectory.duration
        10.0
        >>> trajectory.n_points
        1000
    """
    times: np.ndarray
    states: list[BundleState]
    initial_state: BundleState
    metadata: Optional[dict] = None

    def __post_init__(self):
        """Validate trajectory data"""
        if len(self.times) != len(self.states):
            raise ValueError(
                f"times and states must have same length: "
                f"{len(self.times)} vs {len(self.states)}"
            )

        if len(self.times) == 0:
            raise ValueError("Trajectory must have at least one point")

    @property
    def duration(self) -> float:
        """Total time span"""
        return self.times[-1] - self.times[0]

    @property
    def n_points(self) -> int:
        """Number of trajectory points"""
        return len(self.times)

    def evaluate_at_time(
        self,
        t: float,
        interpolation: str = 'linear'
    ) -> BundleState:
        """
        Interpolate trajectory at arbitrary time t.

        Args:
            t: Time value
            interpolation: Method ('linear' or 'cubic')

        Returns:
            Interpolated bundle state

        Examples:
            >>> state_mid = trajectory.evaluate_at_time(5.0)
        """
        from scipy.interpolate import interp1d

        # Extract state vectors
        state_vectors = np.array([s.to_vector() for s in self.states])

        # Interpolate each component
        interpolator = interp1d(
            self.times,
            state_vectors,
            axis=0,
            kind=interpolation,
            bounds_error=True
        )

        interpolated_vector = interpolator(t)

        # Reconstruct bundle state
        return BundleState.from_vector(
            interpolated_vector,
            L=self.initial_state.shape_state.L
        )

    def project_to_shape_space(self) -> 'ShapeSpaceTrajectory':
        """
        Project bundle trajectory to shape space.

        Returns:
            Trajectory in shape space (forgets fiber)

        Examples:
            >>> shape_traj = bundle_traj.project_to_shape_space()
            >>> len(shape_traj.states) == len(bundle_traj.states)
            True
        """
        from ..core.shape_space import ShapeSpaceTrajectory

        projected_states = [state.shape_state for state in self.states]

        return ShapeSpaceTrajectory(
            times=self.times,
            states=projected_states,
            initial_state=self.initial_state.shape_state
        )

    def extract_conserved_quantities(
        self,
        lifted_hamiltonian: LiftedHamiltonian
    ) -> dict:
        """
        Extract conserved quantities along trajectory.

        Returns:
            Dictionary with arrays:
                - energy: H̃(t)
                - p_theta: p_θ(t)
                - angular_momentum: L (constant)

        Examples:
            >>> conserved = trajectory.extract_conserved_quantities(lifted_H)
            >>> conserved['p_theta']  # Should be constant
            array([0.5, 0.5, 0.5, ...])
        """
        n = self.n_points

        energies = np.zeros(n)
        p_theta_values = np.zeros(n)
        L_values = np.zeros(n)

        for i, state in enumerate(self.states):
            energies[i] = lifted_hamiltonian.evaluate(state)
            p_theta_values[i] = state.p_theta
            L_values[i] = state.shape_state.L

        return {
            'times': self.times,
            'energy': energies,
            'p_theta': p_theta_values,
            'angular_momentum': L_values
        }
```

### BundleIntegrator

```python
# File: src/python/lifts/bundle_integrator.py

from typing import Optional, Tuple, Callable
import numpy as np
from scipy.integrate import solve_ivp
from .s1_bundle import BundleState
from .lifted_hamiltonian import LiftedHamiltonian, BundleTrajectory
from .extended_symplectic import ExtendedSymplecticForm

class BundleIntegrator:
    """
    Numerical integrator for Hamiltonian dynamics on S¹ bundle.

    Uses high-order adaptive methods (preferably symplectic).

    Attributes:
        lifted_hamiltonian: H̃ to integrate
        symplectic_form: Extended ω̃
        method: Integration method name
        tolerances: (rtol, atol) for adaptive stepping

    Examples:
        >>> integrator = BundleIntegrator(lifted_H, extended_form)
        >>> trajectory = integrator.integrate(
        ...     initial_state=z0,
        ...     t_span=(0, 100),
        ...     dense_output=True
        ... )
    """

    def __init__(
        self,
        lifted_hamiltonian: LiftedHamiltonian,
        symplectic_form: ExtendedSymplecticForm,
        method: str = 'DOP853',
        rtol: float = 1e-10,
        atol: float = 1e-12
    ):
        """
        Initialize bundle integrator.

        Args:
            lifted_hamiltonian: Hamiltonian to integrate
            symplectic_form: Symplectic structure
            method: Integration method (default: 'DOP853')
                   Options: 'RK45', 'DOP853', 'Radau', 'BDF'
            rtol: Relative tolerance
            atol: Absolute tolerance
        """
        self.lifted_hamiltonian = lifted_hamiltonian
        self.symplectic_form = symplectic_form
        self.method = method
        self.rtol = rtol
        self.atol = atol

    def integrate(
        self,
        initial_state: BundleState,
        t_span: Tuple[float, float],
        n_points: Optional[int] = None,
        dense_output: bool = False,
        events: Optional[list] = None
    ) -> BundleTrajectory:
        """
        Integrate Hamiltonian dynamics on bundle.

        Args:
            initial_state: Initial condition z(t_0)
            t_span: (t_start, t_end)
            n_points: Number of output points (None = adaptive)
            dense_output: Whether to enable dense output
            events: Event functions for termination/detection

        Returns:
            BundleTrajectory object

        Examples:
            >>> z0 = BundleState(...)
            >>> traj = integrator.integrate(z0, (0, 100), n_points=1000)
            >>> len(traj.states)
            1000
        """
        # Define ODE: dz/dt = X_H̃(z)
        def rhs(t, z_vector):
            """Right-hand side: Hamilton's equations"""
            state = BundleState.from_vector(
                z_vector,
                L=initial_state.shape_state.L
            )

            X_H = self.lifted_hamiltonian.hamiltonian_vector_field(
                state,
                self.symplectic_form
            )

            return X_H

        # Initial condition as vector
        z0 = initial_state.to_vector()

        # Time evaluation points
        if n_points is not None:
            t_eval = np.linspace(t_span[0], t_span[1], n_points)
        else:
            t_eval = None

        # Integrate
        solution = solve_ivp(
            rhs,
            t_span,
            z0,
            method=self.method,
            t_eval=t_eval,
            dense_output=dense_output,
            events=events,
            rtol=self.rtol,
            atol=self.atol
        )

        if not solution.success:
            raise RuntimeError(
                f"Integration failed: {solution.message}"
            )

        # Convert to BundleTrajectory
        states = [
            BundleState.from_vector(z, L=initial_state.shape_state.L)
            for z in solution.y.T
        ]

        metadata = {
            'n_evaluations': solution.nfev,
            'success': solution.success,
            'message': solution.message
        }

        return BundleTrajectory(
            times=solution.t,
            states=states,
            initial_state=initial_state,
            metadata=metadata
        )

    def integrate_with_monitoring(
        self,
        initial_state: BundleState,
        t_span: Tuple[float, float],
        n_points: int = 1000,
        monitor_frequency: int = 100
    ) -> Tuple[BundleTrajectory, dict]:
        """
        Integrate with real-time conservation monitoring.

        Args:
            initial_state: Initial condition
            t_span: Time span
            n_points: Number of output points
            monitor_frequency: How often to print status

        Returns:
            (trajectory, monitoring_data)

        Examples:
            >>> traj, monitoring = integrator.integrate_with_monitoring(
            ...     z0, (0, 100), monitor_frequency=10
            ... )
            >>> monitoring['energy_drift']
            1.234e-10
        """
        print(f"Integrating from t={t_span[0]} to t={t_span[1]}...")
        print(f"Method: {self.method}, rtol={self.rtol}, atol={self.atol}")

        # Integrate
        trajectory = self.integrate(
            initial_state,
            t_span,
            n_points=n_points
        )

        print(f"Integration complete: {len(trajectory.states)} points")

        # Extract conserved quantities
        conserved = trajectory.extract_conserved_quantities(
            self.lifted_hamiltonian
        )

        # Compute drifts
        energy_drift = np.max(np.abs(
            conserved['energy'] - conserved['energy'][0]
        ))
        p_theta_drift = np.max(np.abs(
            conserved['p_theta'] - conserved['p_theta'][0]
        ))
        L_drift = np.max(np.abs(
            conserved['angular_momentum'] - conserved['angular_momentum'][0]
        ))

        monitoring_data = {
            'energy': conserved['energy'],
            'p_theta': conserved['p_theta'],
            'angular_momentum': conserved['angular_momentum'],
            'energy_drift': energy_drift,
            'p_theta_drift': p_theta_drift,
            'L_drift': L_drift,
            'energy_relative_drift': energy_drift / abs(conserved['energy'][0]),
            'n_evaluations': trajectory.metadata['n_evaluations']
        }

        print(f"\nConservation Summary:")
        print(f"  Energy drift: {energy_drift:.3e} "
              f"(rel: {monitoring_data['energy_relative_drift']:.3e})")
        print(f"  p_θ drift: {p_theta_drift:.3e}")
        print(f"  L drift: {L_drift:.3e}")

        return trajectory, monitoring_data
```

---

## Core Algorithms

### C1: Hamiltonian Vector Field Evaluation

**Algorithm: Efficient Vector Field Computation**

```python
def compute_hamiltonian_vector_field_fast(
    state: BundleState,
    lifted_H: LiftedHamiltonian,
    symplectic_form: ExtendedSymplecticForm,
    gradient_cache: Optional[dict] = None
) -> np.ndarray:
    """
    Fast computation of X_H̃ = ω̃^{-1}(dH̃).

    Optimizations:
        - Cache symplectic form inverse
        - Cache Hamiltonian gradient structure
        - Exploit sparsity (if present)

    Args:
        state: Current bundle state
        lifted_H: Hamiltonian
        symplectic_form: Extended form
        gradient_cache: Optional gradient cache

    Returns:
        Vector field [ṡ, θ̇, ṗ_s, ṗ_θ]

    Performance:
        - Time: O(n²) for n=dimension (matrix-vector product)
        - Space: O(n²) for cached inverse
        - With caching: O(n²) amortized
    """
    # Compute gradient
    if gradient_cache is not None and id(state) in gradient_cache:
        dH = gradient_cache[id(state)]
    else:
        dH = lifted_H.gradient(state)
        if gradient_cache is not None:
            gradient_cache[id(state)] = dH

    # Get inverse symplectic form (cached internally)
    omega_inv = symplectic_form.inverse(state, use_cache=True)

    # Vector field: X = ω^{-1}(dH)
    X_H = omega_inv @ dH

    return X_H
```

### C2: Symplectic Integration Step

**Algorithm: Implicit Midpoint Rule** (symplectic, order 2)

```python
def symplectic_midpoint_step(
    z_n: np.ndarray,
    dt: float,
    vector_field: Callable,
    max_iterations: int = 10,
    tolerance: float = 1e-12
) -> np.ndarray:
    """
    One step of implicit midpoint rule (symplectic integrator).

    z_{n+1} = z_n + dt · X_H((z_n + z_{n+1})/2)

    Solved via fixed-point iteration.

    Args:
        z_n: Current state
        dt: Time step
        vector_field: Function z ↦ X_H(z)
        max_iterations: Maximum fixed-point iterations
        tolerance: Convergence tolerance

    Returns:
        z_{n+1}: Next state

    Properties:
        - Symplectic: Preserves ω̃
        - Order 2 accuracy: error ~ O(dt³)
        - Unconditionally stable (implicit)

    Performance:
        - Time: O(iter × n²) for n=dimension
        - Typical iterations: 3-5 for small dt
    """
    # Initial guess: explicit Euler step
    z_guess = z_n + dt * vector_field(z_n)

    for iteration in range(max_iterations):
        # Midpoint
        z_mid = 0.5 * (z_n + z_guess)

        # Implicit update
        z_new = z_n + dt * vector_field(z_mid)

        # Check convergence
        error = np.linalg.norm(z_new - z_guess)
        if error < tolerance:
            return z_new

        z_guess = z_new

    # Did not converge
    raise RuntimeError(
        f"Implicit midpoint did not converge after {max_iterations} iterations"
    )
```

### C3: Conservation Monitoring

**Algorithm: Real-Time Conservation Check**

```python
def monitor_conservation_during_integration(
    trajectory: BundleTrajectory,
    lifted_H: LiftedHamiltonian,
    print_frequency: int = 100
) -> dict:
    """
    Monitor conservation of energy, p_θ, L during integration.

    Args:
        trajectory: Integrated trajectory
        lifted_H: Hamiltonian
        print_frequency: Print status every N points

    Returns:
        Dictionary with conservation statistics

    Example Output:
        {
            'energy_conserved': True,
            'p_theta_conserved': True,
            'L_conserved': True,
            'max_energy_drift': 1.2e-10,
            'max_p_theta_drift': 3.4e-13,
            'max_L_drift': 5.6e-14
        }
    """
    n = trajectory.n_points

    # Extract quantities
    conserved = trajectory.extract_conserved_quantities(lifted_H)

    energies = conserved['energy']
    p_theta = conserved['p_theta']
    L = conserved['angular_momentum']

    # Compute drifts
    E_drift = np.max(np.abs(energies - energies[0]))
    p_theta_drift = np.max(np.abs(p_theta - p_theta[0]))
    L_drift = np.max(np.abs(L - L[0]))

    # Check conservation (thresholds)
    energy_conserved = E_drift < 1e-8
    p_theta_conserved = p_theta_drift < 1e-10
    L_conserved = L_drift < 1e-12

    # Print summary
    print("\n=== Conservation Summary ===")
    print(f"Energy: {'✓' if energy_conserved else '✗'} "
          f"(drift = {E_drift:.3e})")
    print(f"p_θ:    {'✓' if p_theta_conserved else '✗'} "
          f"(drift = {p_theta_drift:.3e})")
    print(f"L:      {'✓' if L_conserved else '✗'} "
          f"(drift = {L_drift:.3e})")

    return {
        'energy_conserved': energy_conserved,
        'p_theta_conserved': p_theta_conserved,
        'L_conserved': L_conserved,
        'max_energy_drift': E_drift,
        'max_p_theta_drift': p_theta_drift,
        'max_L_drift': L_drift,
        'energy_values': energies,
        'p_theta_values': p_theta,
        'L_values': L
    }
```

### C4: Projection Validation

**Algorithm: Compare Lifted vs. Reduced Dynamics**

```python
def validate_projection_consistency(
    bundle_trajectory: BundleTrajectory,
    reduced_trajectory: 'ShapeSpaceTrajectory',
    tolerance: float = 1e-8
) -> dict:
    """
    Verify that π(lifted trajectory) = reduced trajectory.

    This tests fundamental consistency: dynamics on bundle
    should project to dynamics on base.

    Args:
        bundle_trajectory: Trajectory on bundle
        reduced_trajectory: Trajectory on shape space
        tolerance: Error tolerance

    Returns:
        Validation results

    Performance:
        - Time: O(n × m) for n points, m=dimension
        - Space: O(n)
    """
    if len(bundle_trajectory.states) != len(reduced_trajectory.states):
        return {
            'consistent': False,
            'error': 'Length mismatch',
            'bundle_length': len(bundle_trajectory.states),
            'reduced_length': len(reduced_trajectory.states)
        }

    n = len(bundle_trajectory.states)
    errors = np.zeros(n)

    for i in range(n):
        # Project bundle state
        bundle_state = bundle_trajectory.states[i]
        projected = bundle_state.shape_state

        # Compare with reduced state
        reduced_state = reduced_trajectory.states[i]

        # Position error
        pos_error = np.linalg.norm(
            projected.to_array() - reduced_state.to_array()
        )

        # Momentum error (if available)
        if hasattr(reduced_state, 'momenta'):
            mom_error = np.linalg.norm(
                bundle_state.shape_momenta - reduced_state.momenta
            )
            errors[i] = max(pos_error, mom_error)
        else:
            errors[i] = pos_error

    max_error = np.max(errors)
    mean_error = np.mean(errors)
    consistent = max_error < tolerance

    return {
        'consistent': consistent,
        'max_error': max_error,
        'mean_error': mean_error,
        'tolerance': tolerance,
        'errors': errors,
        'pass_rate': np.sum(errors < tolerance) / n
    }
```

---

## Implementation Details

### File Organization

```
src/python/lifts/
├── lifted_hamiltonian.py          # LiftedHamiltonian, BundleTrajectory
├── bundle_integrator.py           # BundleIntegrator class
└── projection.py                  # Projection and comparison tools
```

### Integration Methods

**Available methods** (via scipy.integrate.solve_ivp):
1. **'DOP853'**: Dormand-Prince 8(5,3) (recommended for high accuracy)
2. **'RK45'**: Runge-Kutta 4(5) (faster, less accurate)
3. **'Radau'**: Implicit Runge-Kutta (stiff problems)
4. **'BDF'**: Backward differentiation (very stiff)

**Custom symplectic methods** (future work):
- Verlet (leapfrog)
- Implicit midpoint
- Yoshida4 (order 4 symplectic)

### Performance Considerations

- **Sparse matrices**: If Ω has structure, use sparse linear algebra
- **Gradient caching**: Reuse gradients when possible
- **Adaptive stepping**: Let integrator choose dt automatically
- **Parallelization**: Run multiple trajectories in parallel (ensemble)

---

## Validation Strategy

### Unit Tests

```python
# File: tests/lifts/test_lifted_dynamics.py

class TestLiftedHamiltonian:
    """Test lifted Hamiltonian"""

    def test_theta_independence(self):
        """Verify ∂H̃/∂θ = 0"""
        pass

    def test_p_theta_independence(self):
        """Verify ∂H̃/∂p_θ = 0"""
        pass

    def test_hamiltonian_vector_field(self):
        """Test X_H̃ computation"""
        pass


class TestBundleIntegrator:
    """Test numerical integration"""

    def test_short_integration(self):
        """Integrate for short time, check energy conservation"""
        pass

    def test_long_integration(self):
        """Integrate for long time, check p_θ conservation"""
        pass

    def test_projection_consistency(self):
        """Verify π(lifted) = reduced"""
        pass


class TestConservation:
    """Test conservation monitoring"""

    def test_energy_conservation(self):
        """Energy should be conserved"""
        pass

    def test_p_theta_conservation(self):
        """p_θ should be conserved"""
        pass

    def test_L_conservation(self):
        """Angular momentum should be conserved"""
        pass
```

### Integration Tests

```python
def test_full_bundle_integration_workflow():
    """
    End-to-end test: create bundle, integrate, validate.
    """
    # Setup
    masses = Masses(1.0, 1.0, 1.0)
    energy = -1.0
    L = 1.0

    # Initial condition
    shape = ShapeSpaceState(1.0, 1.0, 1.0, L=L)
    momenta = np.array([0.01, -0.005, 0.008])
    p_theta = 0.5

    z0 = BundleState(shape, theta=0.0, shape_momenta=momenta, p_theta=p_theta)

    # Integrate
    integrator = BundleIntegrator(lifted_H, extended_form)
    trajectory = integrator.integrate(z0, (0, 100), n_points=1000)

    # Validate conservation
    monitoring = monitor_conservation_during_integration(trajectory, lifted_H)

    assert monitoring['energy_conserved']
    assert monitoring['p_theta_conserved']
    assert monitoring['L_conserved']

    print("✓ Full bundle integration workflow successful")
```

---

## Performance Targets

| Operation | Complexity | Target Time |
|-----------|-----------|-------------|
| Vector field evaluation | O(n²) | < 100 μs |
| Single integration step | O(n³) | < 500 μs |
| Full trajectory (1000 pts) | O(N × n³) | < 1 s |
| Conservation check | O(N) | < 10 ms |
| Projection validation | O(N × n) | < 50 ms |

Where:
- n = phase space dimension (8 for planar case)
- N = number of trajectory points

---

## Integration Points

### With Parts A & B
```python
from .s1_bundle import BundleState
from .extended_symplectic import ExtendedSymplecticForm
# Use bundle infrastructure and symplectic form
```

### With WP1 (Integration)
```python
from ..integration.symplectic_integrator import SymplecticIntegrator
# May use custom symplectic methods
```

### With Part D (Integrability)
```python
# Trajectories used for integral search and validation
```

---

## Success Criteria

### Part C Complete When:

- [  ] `LiftedHamiltonian` class implemented
- [  ] `BundleIntegrator` functional
- [  ] `BundleTrajectory` data structure complete
- [  ] Integration working for test cases
- [  ] $p_\theta$ conservation verified (drift < 1e-10)
- [  ] Energy conservation verified (rel. drift < 1e-8)
- [  ] Projection validation passing
- [  ] Performance targets met
- [  ] Unit tests passing (>95% coverage)
- [  ] Documentation complete

**Key Validation**: Must demonstrate that:
1. p_θ is conserved during integration
2. Projected dynamics match reduced dynamics
3. Long-term stability (integrate for 100+ periods)

---

**Document Version**: 1.0
**Created**: 2025-11-14
**Status**: Design Complete → Ready for Implementation
**Estimated Implementation Time**: 3 days
**Next**: Part D (Integrability Search)
