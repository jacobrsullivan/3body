# Task 2.1.1 Part C: Integration with WP1 Infrastructure - Detailed Implementation Design

**Task**: WP 2.1.1 - Coordinate Systems and Reduction
**Part**: C - Integration with Existing WP1 Infrastructure
**Status**: Design Phase
**Estimated Duration**: 3 days
**Dependencies**: Part A Complete (Coordinate Systems), Part B Complete (Reduction)

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture & Design Principles](#architecture--design-principles)
3. [C1: Adapt Integrators for General 3BP](#c1-adapt-integrators-for-general-3bp)
4. [C2: Test Cases and Validation Datasets](#c2-test-cases-and-validation-datasets)
5. [C3: Backward Compatibility with CR3BP](#c3-backward-compatibility-with-cr3bp)
6. [C4: Performance Benchmarking](#c4-performance-benchmarking)
7. [Integration & Testing Strategy](#integration--testing-strategy)
8. [Implementation Checklist](#implementation-checklist)

---

## Overview

### Purpose

Part C bridges the coordinate transformation and reduction machinery (Parts A & B) with the high-precision integration infrastructure developed in WP1. This ensures that:

1. **General 3BP integrators** work seamlessly with arbitrary mass ratios
2. **Coordinate-agnostic integration** supports Cartesian, Jacobi, and reduced states
3. **Conservation monitoring** validates energy, momentum preservation throughout long integrations
4. **Backward compatibility** maintains WP1 CR3BP functionality as a special case

### Scope

We implement three main components:

1. **3BP Integrator Adapters**: Generalize WP1 integrators (IAS15, Yoshida8) to arbitrary 3-body systems
2. **Validation Test Suite**: Comprehensive tests using known exact/high-quality solutions
3. **Performance Benchmarking**: Ensure no regression vs. CR3BP, optimize for general case

### Key Design Goals

- **Unified Interface**: Single API for all coordinate systems
- **Conservation Validation**: Automated checks for energy, momentum drift
- **High Precision**: Leverage QD library for critical calculations
- **Extensibility**: Easy to add new integrators or coordinate systems
- **Robustness**: Handle near-collision events gracefully

---

## Architecture & Design Principles

### Module Structure

```
src/python/integrators/
├── __init__.py                 # Package exports
├── base.py                     # Base integrator interface (from WP1)
├── threebody.py                # C1: General 3BP integrator framework
├── ias15_threebody.py          # C1.2: IAS15 adapter for 3BP
├── yoshida8_threebody.py       # C1.3: Yoshida8 adapter for 3BP
└── conservation_monitor.py     # C1.4: High-precision tracking

tests/integration/
├── test_coordinate_transforms.py  # C2.1: Round-trip tests
├── test_reduction.py              # C2.2: Reduction validation
└── validation/
    ├── lagrange_equilibrium.py    # C2.3: Exact solution test
    ├── figure8_orbit.py            # C2.4: Figure-8 validation
    └── cr3bp_limit.py              # C2.5: CR3BP backward compatibility
```

### Design Patterns

1. **Strategy Pattern**: Pluggable integrators via common interface
2. **Adapter Pattern**: Wrap REBOUND/custom backends for unified API
3. **Observer Pattern**: Conservation monitors observe integration progress
4. **Template Method**: Base class defines integration workflow, subclasses implement specifics

### Core Abstractions

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol, TypeVar, Generic
import numpy as np

# Type variables for coordinate systems
StateType = TypeVar('StateType')  # CartesianState, JacobiState, etc.

class ThreeBodyIntegrator(ABC, Generic[StateType]):
    """
    Abstract base for three-body problem integrators.

    Supports arbitrary coordinate systems via generic type.
    """

    @abstractmethod
    def integrate(
        self,
        state0: StateType,
        masses: Masses,
        t_span: tuple[float, float],
        **kwargs
    ) -> IntegrationResult[StateType]:
        """
        Integrate equations of motion.

        Args:
            state0: Initial state (any coordinate system)
            masses: Three-body mass parameters
            t_span: (t_start, t_end)
            **kwargs: Integrator-specific options

        Returns:
            IntegrationResult with trajectory and diagnostics
        """
        pass

    @abstractmethod
    def step(self, state: StateType, masses: Masses, dt: float) -> StateType:
        """Single integration step (for low-level control)"""
        pass


@dataclass
class IntegrationResult(Generic[StateType]):
    """
    Results from integrating 3BP equations.

    Attributes:
        times: Array of time points
        states: List of states at each time
        diagnostics: Conservation errors, step sizes, etc.
        success: Whether integration completed without errors
    """
    times: np.ndarray
    states: list[StateType]
    diagnostics: dict
    success: bool

    @property
    def final_state(self) -> StateType:
        """Final state in trajectory"""
        return self.states[-1]

    def to_array(self) -> np.ndarray:
        """
        Convert states to flat array (for analysis/plotting).

        Returns:
            Array of shape (n_times, state_dim)
        """
        return np.array([state.to_flat() for state in self.states])


@dataclass
class IntegratorOptions:
    """Common options for all integrators"""
    rtol: float = 1e-12          # Relative tolerance
    atol: float = 1e-15          # Absolute tolerance
    max_step: float = np.inf     # Maximum step size
    dense_output: bool = False   # Store intermediate steps
    precision: Literal['double', 'quad'] = 'double'
    conservation_check: bool = True  # Monitor conservation laws
    collision_detection: bool = True  # Detect near-collisions
```

---

## C1: Adapt Integrators for General 3BP

### C1.1: General 3BP Integrator Framework

**Goal**: Create a unified framework that works with any coordinate system.

#### Module: `threebody.py`

```python
"""
General three-body problem integration framework.

Supports arbitrary masses and multiple coordinate representations.
"""

import numpy as np
from typing import Protocol, TypeVar, Callable, Optional
from dataclasses import dataclass

from ..coordinates.cartesian import CartesianState
from ..coordinates.jacobi import JacobiState
from ..coordinates.base import Masses
from .base import BaseIntegrator
from .conservation_monitor import ConservationMonitor


StateType = TypeVar('StateType', CartesianState, JacobiState)


class RightHandSide(Protocol):
    """Protocol for equations of motion"""

    def __call__(self, t: float, state: np.ndarray, masses: Masses) -> np.ndarray:
        """
        Compute derivative dstate/dt.

        Args:
            t: Time
            state: Flat state vector
            masses: Mass parameters

        Returns:
            Derivative vector (same shape as state)
        """
        ...


class ThreeBodyIntegrator(BaseIntegrator):
    """
    Base class for three-body problem integrators.

    Handles coordinate transformations, conservation monitoring,
    and collision detection.
    """

    def __init__(
        self,
        rhs: RightHandSide,
        masses: Masses,
        options: Optional[IntegratorOptions] = None
    ):
        """
        Initialize integrator.

        Args:
            rhs: Right-hand side function (equations of motion)
            masses: Three-body mass parameters
            options: Integration options
        """
        self.rhs = rhs
        self.masses = masses
        self.options = options or IntegratorOptions()

        # Conservation monitor
        if self.options.conservation_check:
            self.monitor = ConservationMonitor(
                masses=masses,
                precision=self.options.precision
            )

    def integrate_cartesian(
        self,
        state0: CartesianState,
        t_span: tuple[float, float],
        n_points: Optional[int] = None
    ) -> IntegrationResult[CartesianState]:
        """
        Integrate in Cartesian coordinates.

        Args:
            state0: Initial Cartesian state
            t_span: (t_start, t_end)
            n_points: Number of output points (default: adaptive)

        Returns:
            IntegrationResult with Cartesian states
        """
        # Convert to flat array
        z0 = state0.to_flat()

        # Define RHS wrapper
        def rhs_flat(t, z):
            return self.rhs(t, z, self.masses)

        # Integrate (delegate to backend)
        solution = self._integrate_backend(
            rhs_flat, z0, t_span, n_points
        )

        # Convert back to CartesianState objects
        states = [
            CartesianState.from_flat(z, dimension=state0.dimension)
            for z in solution.y.T
        ]

        # Monitor conservation
        diagnostics = {}
        if self.options.conservation_check:
            diagnostics = self.monitor.compute_errors(states, self.masses)

        return IntegrationResult(
            times=solution.t,
            states=states,
            diagnostics=diagnostics,
            success=solution.success
        )

    def integrate_jacobi(
        self,
        state0: JacobiState,
        t_span: tuple[float, float],
        n_points: Optional[int] = None
    ) -> IntegrationResult[JacobiState]:
        """
        Integrate in Jacobi coordinates.

        Strategy: Convert to Cartesian, integrate, convert back.
        (More efficient: implement Jacobi RHS directly)

        Args:
            state0: Initial Jacobi state
            t_span: Time span
            n_points: Number of output points

        Returns:
            IntegrationResult with Jacobi states
        """
        from ..coordinates.jacobi import jacobi_to_cartesian, cartesian_to_jacobi

        # Convert to Cartesian
        cart_state0 = jacobi_to_cartesian(state0, self.masses)

        # Integrate in Cartesian
        cart_result = self.integrate_cartesian(cart_state0, t_span, n_points)

        # Convert trajectory to Jacobi
        jacobi_states = [
            cartesian_to_jacobi(cart_state, self.masses)
            for cart_state in cart_result.states
        ]

        return IntegrationResult(
            times=cart_result.times,
            states=jacobi_states,
            diagnostics=cart_result.diagnostics,
            success=cart_result.success
        )

    def integrate_reduced(
        self,
        state0: RotationReducedState,
        t_span: tuple[float, float],
        n_points: Optional[int] = None
    ) -> IntegrationResult[RotationReducedState]:
        """
        Integrate in rotation-reduced coordinates (shape space).

        Note: This requires careful handling of the reduced symplectic structure.
        For now, we lift to Cartesian, integrate, and project back.

        Args:
            state0: Initial reduced state
            t_span: Time span
            n_points: Number of output points

        Returns:
            IntegrationResult with reduced states
        """
        from ..reduction.rotation_reduction import RotationReduction

        # Integrate underlying Cartesian state
        cart_result = self.integrate_cartesian(state0.state, t_span, n_points)

        # Project each state back to reduced space
        reducer = RotationReduction(
            orientation_convention=state0.orientation_convention
        )

        reduced_states = [
            reducer.reduce(cart_state, self.masses, L_target=state0.L)
            for cart_state in cart_result.states
        ]

        return IntegrationResult(
            times=cart_result.times,
            states=reduced_states,
            diagnostics=cart_result.diagnostics,
            success=cart_result.success
        )

    @abstractmethod
    def _integrate_backend(
        self,
        rhs: Callable,
        z0: np.ndarray,
        t_span: tuple[float, float],
        n_points: Optional[int]
    ):
        """
        Backend-specific integration (implemented by subclasses).

        Should return scipy-like solution object with .t, .y, .success
        """
        pass

    def detect_collision(
        self,
        state: CartesianState,
        threshold: float = 1e-3
    ) -> Optional[tuple[int, int]]:
        """
        Check for near-collision events.

        Args:
            state: Current state
            threshold: Distance threshold for collision

        Returns:
            (i, j) if bodies i and j are within threshold, None otherwise
        """
        r = state.positions

        pairs = [(0, 1), (0, 2), (1, 2)]
        for i, j in pairs:
            dist = np.linalg.norm(r[i] - r[j])
            if dist < threshold:
                return (i, j)

        return None


def create_3bp_rhs_cartesian(G: float = 1.0) -> RightHandSide:
    """
    Create right-hand side function for Cartesian 3BP.

    Args:
        G: Gravitational constant

    Returns:
        RHS function compatible with scipy.integrate.solve_ivp
    """
    def rhs(t: float, z: np.ndarray, masses: Masses) -> np.ndarray:
        """
        Cartesian equations of motion.

        Equations:
            dr_i/dt = v_i
            dv_i/dt = sum_{j≠i} G m_j (r_j - r_i) / |r_ij|³
        """
        n_dim = len(z) // 6  # 2 or 3 dimensions
        n = n_dim * 3  # position components

        positions = z[:n].reshape(3, n_dim)
        velocities = z[n:].reshape(3, n_dim)

        # Compute accelerations
        m = np.array([masses.m1, masses.m2, masses.m3])
        accelerations = np.zeros_like(positions)

        for i in range(3):
            for j in range(3):
                if i == j:
                    continue

                rij = positions[j] - positions[i]
                dist = np.linalg.norm(rij)

                # Newton's law: a_i = G m_j (r_j - r_i) / |r_ij|³
                accelerations[i] += G * m[j] * rij / dist**3

        # Return [velocities, accelerations]
        return np.concatenate([velocities.ravel(), accelerations.ravel()])

    return rhs


def create_3bp_rhs_jacobi(G: float = 1.0) -> RightHandSide:
    """
    Create RHS for Jacobi coordinate integration (more efficient).

    Jacobi coordinates naturally separate internal and CM motion.

    Args:
        G: Gravitational constant

    Returns:
        RHS function in Jacobi coordinates
    """
    # TODO: Implement direct Jacobi RHS for efficiency
    # For now, convert to Cartesian RHS
    cart_rhs = create_3bp_rhs_cartesian(G)

    def rhs_jacobi(t: float, z_jacobi: np.ndarray, masses: Masses) -> np.ndarray:
        """RHS in Jacobi coordinates"""
        from ..coordinates.jacobi import jacobi_to_cartesian, cartesian_to_jacobi

        # Convert to Cartesian
        jacobi_state = JacobiState.from_flat(z_jacobi)
        cart_state = jacobi_to_cartesian(jacobi_state, masses)

        # Compute Cartesian derivative
        z_cart = cart_state.to_flat()
        dz_cart = cart_rhs(t, z_cart, masses)

        # Convert derivative back to Jacobi
        # (This requires careful transformation of velocities)
        # Placeholder: return zero (implement proper transformation)
        return np.zeros_like(z_jacobi)

    return rhs_jacobi
```

---

### C1.2: IAS15 Adapter for 3BP

**Goal**: Adapt REBOUND's IAS15 integrator for general 3BP.

#### Module: `ias15_threebody.py`

```python
"""
IAS15 integrator adapter for three-body problem.

Uses REBOUND backend for high-order adaptive integration.
"""

import numpy as np
from typing import Optional
import warnings

from .threebody import ThreeBodyIntegrator, IntegratorOptions, create_3bp_rhs_cartesian
from ..coordinates.cartesian import CartesianState
from ..coordinates.base import Masses


class IAS15ThreeBody(ThreeBodyIntegrator):
    """
    IAS15 adaptive integrator for 3BP.

    Features:
        - 15th-order Gauss-Radau scheme
        - Adaptive time-stepping
        - Excellent energy conservation
        - Non-symplectic (but very accurate)

    Backend: REBOUND library
    """

    def __init__(
        self,
        masses: Masses,
        G: float = 1.0,
        options: Optional[IntegratorOptions] = None
    ):
        """
        Initialize IAS15 integrator.

        Args:
            masses: Three-body mass parameters
            G: Gravitational constant
            options: Integration options
        """
        rhs = create_3bp_rhs_cartesian(G)
        super().__init__(rhs, masses, options)

        self.G = G

        # Check if REBOUND is available
        try:
            import rebound
            self.rebound = rebound
        except ImportError:
            warnings.warn(
                "REBOUND not available. IAS15 will use scipy fallback.",
                RuntimeWarning
            )
            self.rebound = None

    def _integrate_backend(
        self,
        rhs,
        z0: np.ndarray,
        t_span: tuple[float, float],
        n_points: Optional[int]
    ):
        """
        Integrate using REBOUND's IAS15.

        If REBOUND not available, fall back to scipy.
        """
        if self.rebound is not None:
            return self._integrate_rebound(z0, t_span, n_points)
        else:
            return self._integrate_scipy_fallback(rhs, z0, t_span, n_points)

    def _integrate_rebound(
        self,
        z0: np.ndarray,
        t_span: tuple[float, float],
        n_points: Optional[int]
    ):
        """
        Integrate using REBOUND backend.

        REBOUND expects particles, not state vectors, so we convert.
        """
        import rebound

        t_start, t_end = t_span
        dimension = len(z0) // 6  # 2 or 3

        # Create REBOUND simulation
        sim = rebound.Simulation()
        sim.integrator = "ias15"
        sim.G = self.G
        sim.dt = (t_end - t_start) / 1000  # Initial timestep guess

        # Add particles
        positions = z0[:dimension*3].reshape(3, dimension)
        velocities = z0[dimension*3:].reshape(3, dimension)
        masses = [self.masses.m1, self.masses.m2, self.masses.m3]

        for i in range(3):
            # Pad to 3D for REBOUND
            pos_3d = np.zeros(3)
            vel_3d = np.zeros(3)
            pos_3d[:dimension] = positions[i]
            vel_3d[:dimension] = velocities[i]

            sim.add(
                m=masses[i],
                x=pos_3d[0], y=pos_3d[1], z=pos_3d[2],
                vx=vel_3d[0], vy=vel_3d[1], vz=vel_3d[2]
            )

        # Integration loop
        if n_points is None:
            n_points = 1000

        times = np.linspace(t_start, t_end, n_points)
        trajectory = np.zeros((n_points, len(z0)))

        for idx, t in enumerate(times):
            sim.integrate(t)

            # Extract state
            for i in range(3):
                p = sim.particles[i]
                positions[i] = [p.x, p.y, p.z][:dimension]
                velocities[i] = [p.vx, p.vy, p.vz][:dimension]

            trajectory[idx] = np.concatenate([
                positions.ravel(), velocities.ravel()
            ])

        # Return scipy-like object
        class Result:
            def __init__(self, t, y, success):
                self.t = t
                self.y = y
                self.success = success

        return Result(times, trajectory.T, True)

    def _integrate_scipy_fallback(
        self,
        rhs,
        z0: np.ndarray,
        t_span: tuple[float, float],
        n_points: Optional[int]
    ):
        """
        Fallback to scipy.integrate.solve_ivp with DOP853.

        DOP853 is an 8th-order Runge-Kutta method (not as accurate as IAS15).
        """
        from scipy.integrate import solve_ivp

        t_eval = None if n_points is None else np.linspace(t_span[0], t_span[1], n_points)

        solution = solve_ivp(
            rhs,
            t_span,
            z0,
            method='DOP853',
            rtol=self.options.rtol,
            atol=self.options.atol,
            dense_output=self.options.dense_output,
            t_eval=t_eval
        )

        return solution
```

---

### C1.3: Yoshida8 Adapter for 3BP

**Goal**: Adapt symplectic Yoshida8 integrator for general 3BP.

#### Module: `yoshida8_threebody.py`

```python
"""
Yoshida8 symplectic integrator for three-body problem.

8th-order symplectic composition method for separable Hamiltonians.
"""

import numpy as np
from typing import Optional, Callable

from .threebody import ThreeBodyIntegrator, IntegratorOptions
from ..coordinates.cartesian import CartesianState
from ..coordinates.base import Masses


# Yoshida8 coefficients (8th order symplectic integrator)
YOSHIDA8_COEFFICIENTS = [
    # (w, c) pairs for position and momentum updates
    # Derived from Yoshida's composition method
    # Reference: Yoshida (1990), "Construction of higher order symplectic integrators"
    (0.311790812418427e0, 0.1235778652544746),
    (-0.155895406209214e0, 0.2359668527738690),
    (0.0, -0.3594847181283336),
    (0.0, 0.0),  # ... (full coefficients)
    # TODO: Fill in complete Yoshida8 coefficient table
]


class Yoshida8ThreeBody(ThreeBodyIntegrator):
    """
    8th-order symplectic integrator for 3BP.

    Features:
        - Symplectic (preserves phase space volume exactly)
        - Time-reversible
        - Fixed time step
        - Excellent for long-term stability studies

    Limitation: Requires separable Hamiltonian H = T(p) + V(q)
    """

    def __init__(
        self,
        masses: Masses,
        G: float = 1.0,
        dt: float = 0.01,
        options: Optional[IntegratorOptions] = None
    ):
        """
        Initialize Yoshida8 integrator.

        Args:
            masses: Three-body mass parameters
            G: Gravitational constant
            dt: Fixed time step
            options: Integration options
        """
        # Yoshida doesn't need RHS (uses operator splitting)
        super().__init__(None, masses, options)

        self.G = G
        self.dt = dt

    def _integrate_backend(
        self,
        rhs,
        z0: np.ndarray,
        t_span: tuple[float, float],
        n_points: Optional[int]
    ):
        """
        Integrate using Yoshida8 operator splitting.
        """
        t_start, t_end = t_span
        dimension = len(z0) // 6

        # Determine number of steps
        if n_points is None:
            n_steps = int((t_end - t_start) / self.dt)
        else:
            n_steps = n_points - 1
            self.dt = (t_end - t_start) / n_steps

        # Initialize trajectory storage
        times = np.linspace(t_start, t_end, n_steps + 1)
        trajectory = np.zeros((n_steps + 1, len(z0)))
        trajectory[0] = z0

        # Integration loop
        z = z0.copy()
        for step in range(n_steps):
            z = self._yoshida8_step(z, self.dt, dimension)
            trajectory[step + 1] = z

        # Return scipy-like object
        class Result:
            def __init__(self, t, y, success):
                self.t = t
                self.y = y
                self.success = success

        return Result(times, trajectory.T, True)

    def _yoshida8_step(self, z: np.ndarray, dt: float, dimension: int) -> np.ndarray:
        """
        Single Yoshida8 integration step.

        Operator splitting: exp(dt * L) ≈ prod_i exp(c_i * dt * T) exp(w_i * dt * V)
        where L is Liouville operator, T is kinetic, V is potential.

        Args:
            z: Current state [positions, velocities]
            dt: Time step
            dimension: 2 or 3

        Returns:
            Updated state
        """
        n = dimension * 3  # position components
        positions = z[:n].reshape(3, dimension)
        velocities = z[n:].reshape(3, dimension)

        # Apply composition method
        for w_i, c_i in YOSHIDA8_COEFFICIENTS:
            # Drift step: update positions
            positions += c_i * dt * velocities

            # Kick step: update velocities (compute accelerations)
            accelerations = self._compute_accelerations(positions, dimension)
            velocities += w_i * dt * accelerations

        return np.concatenate([positions.ravel(), velocities.ravel()])

    def _compute_accelerations(
        self,
        positions: np.ndarray,
        dimension: int
    ) -> np.ndarray:
        """
        Compute gravitational accelerations.

        a_i = sum_{j≠i} G m_j (r_j - r_i) / |r_ij|³

        Args:
            positions: (3, dimension) array
            dimension: 2 or 3

        Returns:
            accelerations: (3, dimension) array
        """
        m = np.array([self.masses.m1, self.masses.m2, self.masses.m3])
        accelerations = np.zeros_like(positions)

        for i in range(3):
            for j in range(3):
                if i == j:
                    continue

                rij = positions[j] - positions[i]
                dist = np.linalg.norm(rij)

                # Softening to avoid singularities
                softening = 1e-10
                dist_safe = np.sqrt(dist**2 + softening**2)

                accelerations[i] += self.G * m[j] * rij / dist_safe**3

        return accelerations
```

---

### C1.4: High-Precision Conservation Monitoring

**Goal**: Track conservation laws during integration with high precision.

#### Module: `conservation_monitor.py`

```python
"""
Conservation law monitoring for 3BP integration.

Tracks energy, linear momentum, and angular momentum throughout integration.
"""

import numpy as np
from typing import List, Optional
from dataclasses import dataclass, field

from ..coordinates.cartesian import CartesianState, compute_energy
from ..coordinates.cartesian import compute_linear_momentum, compute_angular_momentum
from ..coordinates.base import Masses


@dataclass
class ConservationDiagnostics:
    """
    Conservation error statistics.

    Attributes:
        energy_errors: Relative energy errors at each time
        momentum_errors: Linear momentum magnitude at each time
        angular_momentum_errors: Angular momentum drift at each time
        max_energy_error: Maximum relative energy error
        max_momentum_error: Maximum momentum magnitude
        max_angular_momentum_error: Maximum L drift
    """
    energy_errors: np.ndarray
    momentum_errors: np.ndarray
    angular_momentum_errors: np.ndarray

    @property
    def max_energy_error(self) -> float:
        return np.max(np.abs(self.energy_errors))

    @property
    def max_momentum_error(self) -> float:
        return np.max(self.momentum_errors)

    @property
    def max_angular_momentum_error(self) -> float:
        return np.max(self.angular_momentum_errors)

    def passes_tolerance(
        self,
        energy_tol: float = 1e-12,
        momentum_tol: float = 1e-13,
        angular_momentum_tol: float = 1e-13
    ) -> bool:
        """Check if all conservation errors are within tolerance"""
        return (
            self.max_energy_error < energy_tol and
            self.max_momentum_error < momentum_tol and
            self.max_angular_momentum_error < angular_momentum_tol
        )


class ConservationMonitor:
    """
    Monitor conservation laws during 3BP integration.

    Computes energy, linear momentum, and angular momentum at each step,
    tracking drift from initial values.
    """

    def __init__(
        self,
        masses: Masses,
        G: float = 1.0,
        precision: str = 'double'
    ):
        """
        Initialize conservation monitor.

        Args:
            masses: Three-body mass parameters
            G: Gravitational constant
            precision: 'double' or 'quad' for quad-double arithmetic
        """
        self.masses = masses
        self.G = G
        self.precision = precision

        # Initial values (set on first state)
        self.E0: Optional[float] = None
        self.L0: Optional[np.ndarray] = None
        self.P0: Optional[np.ndarray] = None

    def compute_errors(
        self,
        states: List[CartesianState],
        masses: Masses
    ) -> ConservationDiagnostics:
        """
        Compute conservation errors for trajectory.

        Args:
            states: List of Cartesian states
            masses: Mass parameters

        Returns:
            ConservationDiagnostics object
        """
        n = len(states)
        energy_errors = np.zeros(n)
        momentum_errors = np.zeros(n)
        angular_momentum_errors = np.zeros(n)

        # Set initial values from first state
        self.E0 = compute_energy(states[0], masses, G=self.G, precision=self.precision)
        self.L0 = compute_angular_momentum(states[0], masses)
        self.P0 = compute_linear_momentum(states[0], masses)

        # Compute errors at each time
        for i, state in enumerate(states):
            # Energy error (relative)
            E = compute_energy(state, masses, G=self.G, precision=self.precision)
            energy_errors[i] = abs((E - self.E0) / self.E0) if abs(self.E0) > 1e-15 else abs(E - self.E0)

            # Linear momentum error (absolute magnitude)
            P = compute_linear_momentum(state, masses)
            momentum_errors[i] = np.linalg.norm(P - self.P0)

            # Angular momentum error (absolute)
            L = compute_angular_momentum(state, masses)
            angular_momentum_errors[i] = np.linalg.norm(L - self.L0)

        return ConservationDiagnostics(
            energy_errors=energy_errors,
            momentum_errors=momentum_errors,
            angular_momentum_errors=angular_momentum_errors
        )

    def report(self, diagnostics: ConservationDiagnostics) -> str:
        """
        Generate text report of conservation errors.

        Args:
            diagnostics: ConservationDiagnostics object

        Returns:
            Formatted string report
        """
        report = "Conservation Law Validation Report\n"
        report += "=" * 50 + "\n\n"

        report += f"Energy Conservation:\n"
        report += f"  Max relative error: {diagnostics.max_energy_error:.3e}\n"
        report += f"  Mean relative error: {np.mean(np.abs(diagnostics.energy_errors)):.3e}\n\n"

        report += f"Linear Momentum Conservation:\n"
        report += f"  Max |P - P0|: {diagnostics.max_momentum_error:.3e}\n"
        report += f"  Mean |P - P0|: {np.mean(diagnostics.momentum_errors):.3e}\n\n"

        report += f"Angular Momentum Conservation:\n"
        report += f"  Max |L - L0|: {diagnostics.max_angular_momentum_error:.3e}\n"
        report += f"  Mean |L - L0|: {np.mean(diagnostics.angular_momentum_errors):.3e}\n\n"

        # Pass/fail
        passed = diagnostics.passes_tolerance()
        report += f"Overall Status: {'PASSED' if passed else 'FAILED'}\n"

        return report
```

---

## C2: Test Cases and Validation Datasets

### C2.1: Coordinate Transformation Tests

**Goal**: Validate round-trip accuracy for all coordinate transformations.

#### Module: `tests/integration/test_coordinate_transforms.py`

```python
"""
Integration tests for coordinate transformations.

Tests round-trip accuracy: Cartesian → X → Cartesian
"""

import numpy as np
import pytest

from src.python.coordinates.cartesian import CartesianState, enforce_barycenter
from src.python.coordinates.jacobi import cartesian_to_jacobi, jacobi_to_cartesian
from src.python.coordinates.shape_space import cartesian_to_shape_distances
from src.python.coordinates.base import Masses


class TestRoundTripTransformations:
    """Test coordinate transformation round-trip accuracy"""

    @pytest.fixture
    def random_masses(self):
        """Generate random mass parameters"""
        m1, m2, m3 = np.random.uniform(0.5, 2.0, size=3)
        return Masses(m1, m2, m3)

    @pytest.fixture
    def random_cartesian_state(self, random_masses):
        """Generate random Cartesian state in barycentric frame"""
        positions = np.random.randn(3, 3)
        velocities = np.random.randn(3, 3)

        state = CartesianState(positions, velocities, dimension=3)
        return enforce_barycenter(state, random_masses)

    def test_cartesian_jacobi_roundtrip(self, random_cartesian_state, random_masses):
        """Test Cartesian → Jacobi → Cartesian"""
        state0 = random_cartesian_state

        # Forward transformation
        jacobi_state = cartesian_to_jacobi(state0, random_masses)

        # Backward transformation
        state1 = jacobi_to_cartesian(jacobi_state, random_masses)

        # Check round-trip error
        pos_error = np.linalg.norm(state0.positions - state1.positions)
        vel_error = np.linalg.norm(state0.velocities - state1.velocities)

        assert pos_error < 1e-13, f"Position round-trip error: {pos_error}"
        assert vel_error < 1e-13, f"Velocity round-trip error: {vel_error}"

    def test_cartesian_jacobi_roundtrip_many(self, random_masses):
        """Test round-trip for 1000 random states"""
        errors = []

        for _ in range(1000):
            # Random state
            positions = np.random.randn(3, 3)
            velocities = np.random.randn(3, 3)
            state0 = CartesianState(positions, velocities, dimension=3)
            state0 = enforce_barycenter(state0, random_masses)

            # Round trip
            jacobi_state = cartesian_to_jacobi(state0, random_masses)
            state1 = jacobi_to_cartesian(jacobi_state, random_masses)

            # Compute error
            error = np.linalg.norm(state0.positions - state1.positions)
            errors.append(error)

        max_error = max(errors)
        mean_error = np.mean(errors)

        assert max_error < 1e-13, f"Max error: {max_error}"
        assert mean_error < 1e-14, f"Mean error: {mean_error}"

    def test_shape_space_distances_consistency(self, random_cartesian_state, random_masses):
        """Test that shape distances satisfy triangle inequality"""
        state = random_cartesian_state

        shape = cartesian_to_shape_distances(state, random_masses)

        # Triangle inequality
        assert shape.r12 + shape.r23 >= shape.r31 - 1e-10
        assert shape.r23 + shape.r31 >= shape.r12 - 1e-10
        assert shape.r31 + shape.r12 >= shape.r23 - 1e-10

    @pytest.mark.parametrize("mass_ratio", [1.0, 10.0, 100.0, 1000.0])
    def test_extreme_mass_ratios(self, mass_ratio):
        """Test transformations with extreme mass ratios"""
        masses = Masses(mass_ratio, 1.0, 1.0)

        # Random state
        positions = np.random.randn(3, 3)
        velocities = np.random.randn(3, 3)
        state0 = CartesianState(positions, velocities, dimension=3)
        state0 = enforce_barycenter(state0, masses)

        # Round trip
        jacobi_state = cartesian_to_jacobi(state0, masses)
        state1 = jacobi_to_cartesian(jacobi_state, masses)

        error = np.linalg.norm(state0.positions - state1.positions)
        assert error < 1e-12, f"Error for mass ratio {mass_ratio}: {error}"
```

---

### C2.2: Reduction Validation Tests

**Goal**: Verify that reduction preserves structure and constraints.

#### Module: `tests/integration/test_reduction.py`

```python
"""
Integration tests for symplectic reduction.

Validates momentum conservation and constraint enforcement.
"""

import numpy as np
import pytest

from src.python.coordinates.cartesian import CartesianState
from src.python.coordinates.base import Masses
from src.python.reduction.translation_reduction import TranslationReduction
from src.python.reduction.rotation_reduction import RotationReduction, OrientationConvention


class TestTranslationReduction:
    """Test translation reduction (barycentric projection)"""

    def test_arbitrary_state_to_barycentric(self):
        """Project arbitrary state onto barycentric frame"""
        masses = Masses(1.0, 1.0, 1.0)

        # Random state (NOT in barycentric frame)
        positions = np.random.randn(3, 3) + 10.0  # Offset from origin
        velocities = np.random.randn(3, 3) + 5.0
        state = CartesianState(positions, velocities, dimension=3)

        # Reduce
        reducer = TranslationReduction()
        reduced = reducer.reduce(state, masses)

        # Verify constraints
        assert reduced._check_barycentric(tolerance=1e-14)
        assert reduced._check_zero_momentum(tolerance=1e-14)

    def test_momentum_conservation_during_integration(self):
        """Verify P=0 is maintained during integration"""
        # TODO: Implement after integrators are ready
        pass


class TestRotationReduction:
    """Test rotation reduction (orientation fixing)"""

    def test_align_axis_12(self):
        """Test alignment of body 1-2 axis with x-axis"""
        masses = Masses(1.0, 1.0, 1.0)

        # Random barycentric state
        positions = np.random.randn(3, 3)
        velocities = np.random.randn(3, 3)
        state = CartesianState(positions, velocities, dimension=2)

        # Enforce barycenter
        from src.python.coordinates.cartesian import enforce_barycenter
        state = enforce_barycenter(state, masses)

        # Reduce
        reducer = RotationReduction(OrientationConvention.ALIGN_AXIS_12)
        reduced = reducer.reduce(state, masses)

        # Verify alignment
        r12 = reduced.state.positions[0] - reduced.state.positions[1]
        assert abs(r12[1]) < 1e-14, "Body 1-2 axis should be aligned with x-axis"
        assert r12[0] > 0, "Should point in positive x direction"

    def test_angular_momentum_conservation(self):
        """Verify L is conserved during integration"""
        # TODO: Implement after integrators are ready
        pass
```

---

### C2.3: Lagrange Equilibrium Validation

**Goal**: Test against exact Lagrange equilateral triangle solution.

#### Module: `validation/lagrange_equilibrium.py`

```python
"""
Lagrange equilateral equilibrium configuration.

Exact solution: three equal masses at vertices of equilateral triangle,
rotating rigidly with constant angular velocity.
"""

import numpy as np
from dataclasses import dataclass

from src.python.coordinates.cartesian import CartesianState, enforce_barycenter
from src.python.coordinates.base import Masses


@dataclass
class LagrangeEquilibriumConfig:
    """Configuration for Lagrange equilateral solution"""
    masses: Masses
    radius: float  # Distance from center to each body
    omega: float  # Angular velocity of rotation

    @classmethod
    def from_equal_masses(cls, mass: float = 1.0, radius: float = 1.0):
        """
        Create configuration with three equal masses.

        For equal masses, the angular velocity is:
            ω² = 3 G M / R³ = 3 G (3m) / R³ = 9 G m / R³

        With G=1, m=1, R=1: ω = 3
        """
        masses = Masses(mass, mass, mass)
        omega = np.sqrt(9.0 * mass / radius**3)
        return cls(masses, radius, omega)


def create_lagrange_initial_state(
    config: LagrangeEquilibriumConfig,
    phase: float = 0.0
) -> CartesianState:
    """
    Create initial state for Lagrange equilateral configuration.

    Args:
        config: Configuration parameters
        phase: Initial rotation phase (radians)

    Returns:
        Initial Cartesian state (planar)
    """
    R = config.radius
    omega = config.omega

    # Angles for three vertices of equilateral triangle
    angles = np.array([0, 2*np.pi/3, 4*np.pi/3]) + phase

    # Positions (equilateral triangle)
    positions = R * np.column_stack([
        np.cos(angles),
        np.sin(angles),
        np.zeros(3)
    ])

    # Velocities (circular motion)
    velocities = R * omega * np.column_stack([
        -np.sin(angles),
        np.cos(angles),
        np.zeros(3)
    ])

    state = CartesianState(positions, velocities, dimension=2)
    return enforce_barycenter(state, config.masses)


def validate_lagrange_conservation(
    states: list[CartesianState],
    config: LagrangeEquilibriumConfig
) -> dict:
    """
    Validate conservation laws for Lagrange equilibrium.

    For this exact solution:
    - Energy should be constant
    - Angular momentum should be constant
    - Shape should remain equilateral triangle (constant r12, r23, r31)

    Args:
        states: List of states from integration
        config: Configuration used

    Returns:
        Dictionary with validation results
    """
    from src.python.coordinates.cartesian import compute_energy, compute_angular_momentum
    from src.python.coordinates.shape_space import cartesian_to_shape_distances

    n = len(states)
    energies = np.zeros(n)
    angular_momenta = np.zeros(n)
    distances_12 = np.zeros(n)
    distances_23 = np.zeros(n)
    distances_31 = np.zeros(n)

    for i, state in enumerate(states):
        energies[i] = compute_energy(state, config.masses)
        L = compute_angular_momentum(state, config.masses)
        angular_momenta[i] = np.linalg.norm(L)

        shape = cartesian_to_shape_distances(state, config.masses)
        distances_12[i] = shape.r12
        distances_23[i] = shape.r23
        distances_31[i] = shape.r31

    # Compute relative errors
    energy_error = np.max(np.abs(energies - energies[0])) / abs(energies[0])
    L_error = np.max(np.abs(angular_momenta - angular_momenta[0])) / angular_momenta[0]

    # Shape should remain constant (equilateral triangle)
    shape_error_12 = np.max(np.abs(distances_12 - distances_12[0])) / distances_12[0]
    shape_error_23 = np.max(np.abs(distances_23 - distances_23[0])) / distances_23[0]
    shape_error_31 = np.max(np.abs(distances_31 - distances_31[0])) / distances_31[0]

    return {
        'energy_error': energy_error,
        'angular_momentum_error': L_error,
        'shape_error_max': max(shape_error_12, shape_error_23, shape_error_31),
        'passed': (energy_error < 1e-12 and L_error < 1e-12 and
                   shape_error_12 < 1e-12 and shape_error_23 < 1e-12 and shape_error_31 < 1e-12)
    }
```

---

### C2.4: Figure-8 Orbit Validation

**Goal**: Test using the famous figure-8 periodic orbit (Chenciner-Montgomery solution).

#### Module: `validation/figure8_orbit.py`

```python
"""
Figure-8 periodic orbit for three equal masses.

This is a famous periodic solution discovered by Chenciner and Montgomery (2000).
"""

import numpy as np

from src.python.coordinates.cartesian import CartesianState
from src.python.coordinates.base import Masses


# High-precision initial conditions for Figure-8 orbit
# Reference: Chenciner & Montgomery (2000)
# Units: G = 1, M_total = 3
FIGURE8_IC = {
    # Body 1
    'r1': np.array([0.97000436, -0.24308753, 0.0]),
    'v1': np.array([0.466203685, 0.43236573, 0.0]),

    # Body 2
    'r2': np.array([-0.97000436, 0.24308753, 0.0]),
    'v2': np.array([0.466203685, 0.43236573, 0.0]),

    # Body 3
    'r3': np.array([0.0, 0.0, 0.0]),
    'v3': np.array([-0.93240737, -0.86473146, 0.0]),

    # Period
    'T': 6.32591398
}


def create_figure8_initial_state() -> tuple[CartesianState, Masses, float]:
    """
    Create initial state for Figure-8 orbit.

    Returns:
        (initial_state, masses, period)
    """
    masses = Masses(1.0, 1.0, 1.0)

    positions = np.array([
        FIGURE8_IC['r1'],
        FIGURE8_IC['r2'],
        FIGURE8_IC['r3']
    ])

    velocities = np.array([
        FIGURE8_IC['v1'],
        FIGURE8_IC['v2'],
        FIGURE8_IC['v3']
    ])

    state = CartesianState(positions, velocities, dimension=2)
    period = FIGURE8_IC['T']

    return state, masses, period


def validate_figure8_periodicity(
    states: list[CartesianState],
    times: np.ndarray,
    period: float,
    tolerance: float = 1e-6
) -> dict:
    """
    Validate that orbit is periodic.

    Check that state after one period matches initial state.

    Args:
        states: List of states from integration
        times: Array of time points
        period: Expected period
        tolerance: Tolerance for periodicity check

    Returns:
        Dictionary with validation results
    """
    # Find state closest to one period
    idx_period = np.argmin(np.abs(times - period))

    state0 = states[0]
    state_period = states[idx_period]

    # Compute difference
    pos_diff = np.linalg.norm(state0.positions - state_period.positions)
    vel_diff = np.linalg.norm(state0.velocities - state_period.velocities)

    max_diff = max(pos_diff, vel_diff)

    return {
        'position_difference': pos_diff,
        'velocity_difference': vel_diff,
        'max_difference': max_diff,
        'passed': max_diff < tolerance
    }
```

---

### C2.5: CR3BP Limit Validation

**Goal**: Verify that 3BP reduces to CR3BP when one mass → 0.

#### Module: `validation/cr3bp_limit.py`

```python
"""
Verify that general 3BP reduces to CR3BP in the limit m3 → 0.

This ensures backward compatibility with WP1.
"""

import numpy as np

from src.python.coordinates.cartesian import CartesianState
from src.python.coordinates.base import Masses


def compare_3bp_to_cr3bp(
    m1: float,
    m2: float,
    m3_values: list[float],
    initial_state_3bp: CartesianState,
    integration_time: float
) -> dict:
    """
    Compare 3BP trajectories as m3 → 0 with CR3BP.

    As m3 → 0, the general 3BP should converge to the CR3BP solution.

    Args:
        m1, m2: Primary and secondary masses (fixed)
        m3_values: List of test mass values (decreasing)
        initial_state_3bp: Initial 3BP state
        integration_time: How long to integrate

    Returns:
        Dictionary with convergence analysis
    """
    # TODO: Implement after integrators are ready
    # This will require:
    # 1. Integrate 3BP for each m3 value
    # 2. Integrate CR3BP (from WP1)
    # 3. Compare trajectories, show convergence as m3 → 0

    pass
```

---

## C3: Backward Compatibility with CR3BP

### Goal

Ensure that WP1's CR3BP functionality is preserved as a special case of the general 3BP framework.

### Implementation Strategy

```python
# In src/python/integrators/threebody.py

def create_cr3bp_from_3bp(m1: float, m2: float, m3_epsilon: float = 1e-10):
    """
    Create CR3BP-like system using general 3BP framework.

    Sets m3 to very small value to approximate test particle.

    Args:
        m1, m2: Primary masses
        m3_epsilon: Test particle mass (very small)

    Returns:
        Masses object suitable for CR3BP approximation
    """
    return Masses(m1, m2, m3_epsilon)


def validate_cr3bp_compatibility():
    """
    Test that 3BP integrators reproduce WP1 CR3BP results.

    Comparison points:
    - Lagrange points (L1, L2, L3, L4, L5)
    - Periodic orbits (halo, Lyapunov)
    - Invariant manifolds
    """
    # Load WP1 reference solutions
    # Integrate with 3BP framework (m3 → 0)
    # Compare trajectories
    pass
```

---

## C4: Performance Benchmarking

### Goal

Measure performance and ensure no regression compared to WP1.

### Benchmark Suite

```python
# In tests/validation/test_performance.py

import time
import numpy as np
from src.python.integrators.ias15_threebody import IAS15ThreeBody
from src.python.coordinates.cartesian import CartesianState
from src.python.coordinates.base import Masses


def benchmark_cartesian_integration():
    """Benchmark Cartesian integration speed"""
    masses = Masses(1.0, 1.0, 1.0)

    # Random initial state
    positions = np.random.randn(3, 3)
    velocities = np.random.randn(3, 3)
    state0 = CartesianState(positions, velocities, dimension=3)

    # Benchmark
    integrator = IAS15ThreeBody(masses)

    t_start = time.perf_counter()
    result = integrator.integrate_cartesian(state0, (0, 100), n_points=10000)
    t_end = time.perf_counter()

    elapsed = t_end - t_start

    print(f"Cartesian integration: {elapsed:.3f} seconds")
    print(f"  {10000 / elapsed:.1f} steps/second")

    return elapsed


def benchmark_coordinate_transformations():
    """Benchmark transformation speed"""
    from src.python.coordinates.jacobi import cartesian_to_jacobi, jacobi_to_cartesian

    masses = Masses(1.0, 1.0, 1.0)
    n_transforms = 10000

    # Generate random states
    states = [
        CartesianState(np.random.randn(3, 3), np.random.randn(3, 3), dimension=3)
        for _ in range(n_transforms)
    ]

    # Benchmark Cartesian → Jacobi
    t_start = time.perf_counter()
    for state in states:
        jacobi_state = cartesian_to_jacobi(state, masses)
    t_end = time.perf_counter()

    elapsed_forward = t_end - t_start

    print(f"Cartesian → Jacobi: {elapsed_forward * 1e6 / n_transforms:.1f} μs per transform")

    return elapsed_forward / n_transforms


# Target performance benchmarks:
# - Cartesian integration: > 1000 steps/second
# - Coordinate transform: < 50 μs per transform
# - Energy computation: < 10 μs per state
```

---

## Integration & Testing Strategy

### Test Suite Structure

```
tests/
├── unit/
│   ├── test_threebody_integrator.py      # Base framework
│   ├── test_ias15_threebody.py           # IAS15 adapter
│   └── test_yoshida8_threebody.py        # Yoshida8 adapter
├── integration/
│   ├── test_coordinate_transforms.py      # C2.1
│   └── test_reduction.py                  # C2.2
└── validation/
    ├── lagrange_equilibrium.py            # C2.3
    ├── figure8_orbit.py                   # C2.4
    ├── cr3bp_limit.py                     # C2.5
    └── test_performance.py                # C4
```

### Continuous Integration

Add to `.github/workflows/`:

```yaml
name: WP2.1.1 Part C Tests

on: [push, pull_request]

jobs:
  test-integration:
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

      - name: Run integrator tests
        run: |
          pytest tests/unit/test_threebody_integrator.py -v
          pytest tests/unit/test_ias15_threebody.py -v

      - name: Run validation tests
        run: |
          pytest tests/validation/ -v

      - name: Run performance benchmarks
        run: |
          pytest tests/validation/test_performance.py --benchmark
```

---

## Implementation Checklist

### C1: Integrator Adaptation
- [ ] `ThreeBodyIntegrator` base class
- [ ] `create_3bp_rhs_cartesian()` function
- [ ] `create_3bp_rhs_jacobi()` function (optimized)
- [ ] `integrate_cartesian()` method
- [ ] `integrate_jacobi()` method
- [ ] `integrate_reduced()` method
- [ ] Collision detection
- [ ] IAS15 REBOUND adapter
- [ ] IAS15 scipy fallback
- [ ] Yoshida8 implementation
- [ ] Yoshida8 coefficient table
- [ ] `ConservationMonitor` class
- [ ] Conservation diagnostics report

### C2: Validation Tests
- [ ] Round-trip transformation tests (1000+ random states)
- [ ] Extreme mass ratio tests
- [ ] Translation reduction validation
- [ ] Rotation reduction validation
- [ ] Lagrange equilibrium initial conditions
- [ ] Lagrange conservation validation
- [ ] Figure-8 initial conditions (high precision)
- [ ] Figure-8 periodicity test
- [ ] CR3BP limit convergence test

### C3: Backward Compatibility
- [ ] CR3BP approximation factory function
- [ ] WP1 comparison tests
- [ ] Lagrange point validation
- [ ] Periodic orbit validation

### C4: Performance
- [ ] Integration speed benchmark
- [ ] Transformation speed benchmark
- [ ] Memory profiling
- [ ] Performance regression tests
- [ ] Optimization using Numba (if needed)

### Documentation
- [ ] API documentation for all integrators
- [ ] Validation report with plots
- [ ] Performance benchmark report
- [ ] Tutorial notebook: "Integrating the 3BP"

---

## Success Criteria

### Functional Requirements
- [ ] All coordinate systems integrate correctly
- [ ] Conservation laws satisfied to target tolerance:
  - Energy: |ΔE|/E < 1e-12
  - Momentum: |P| < 1e-13
  - Angular momentum: |ΔL| < 1e-13
- [ ] Lagrange equilibrium maintains shape for 100+ periods
- [ ] Figure-8 orbit returns to initial state after one period (error < 1e-6)
- [ ] CR3BP limit converges as m3 → 0

### Performance Requirements
- [ ] Integration speed: > 1000 steps/second
- [ ] Coordinate transformation: < 50 μs per transform
- [ ] No regression vs. WP1 CR3BP performance

### Quality Requirements
- [ ] Test coverage > 95%
- [ ] All validation tests pass
- [ ] Documentation complete
- [ ] CI/CD pipeline green

---

## Next Steps

After completing Part C:

1. **Part D: Documentation**
   - Technical report consolidating Parts A, B, C
   - Tutorial notebook demonstrating full pipeline
   - API reference documentation

2. **Task 2.1.2: Mechanical Connection**
   - Complete connection form computation
   - Curvature analysis
   - Geometric obstruction to integrability

3. **Task 2.1.3: JM Metric**
   - Implement Jacobi-Maupertuis metric on shape space
   - Geodesic flow analysis

---

## References

### Numerical Integration
1. Rein & Spiegel, "IAS15: A fast, adaptive, high-order integrator for gravitational dynamics" (2015)
2. Yoshida, "Construction of higher order symplectic integrators" (1990)
3. Hairer, Lubich, Wanner, *Geometric Numerical Integration* (2006)

### Validation Solutions
4. Chenciner & Montgomery, "A remarkable periodic solution of the three-body problem" (2000)
5. Meyer & Hall, *Hamiltonian Dynamical Systems and the N-Body Problem* (2008)

### Software Engineering
6. REBOUND documentation: https://rebound.readthedocs.io
7. SciPy ODE solvers: https://docs.scipy.org/doc/scipy/reference/integrate.html

---

**Document Version**: 1.0
**Created**: 2025-11-10
**Status**: Design Complete → Ready for Implementation
