"""
Christoffel symbols and metric derivatives.

Christoffel symbols Γ^k_ij are the connection coefficients of the
Levi-Civita connection (unique torsion-free metric-compatible connection).

Mathematical Definition:
    Γ^k_ij = (1/2) g^kl (∂g_jl/∂x^i + ∂g_il/∂x^j - ∂g_ij/∂x^l)

These are needed to compute geodesics and curvature tensors.

Task: WP 2.1, Task 2.1.3, Part A
"""

from dataclasses import dataclass
from typing import Callable, Optional
import numpy as np

from ..coordinates.base import Masses
from ..coordinates.shape_space import ShapeSpaceState
from .jm_metric import RiemannianMetric, compute_jm_metric


@dataclass(frozen=True)
class ChristoffelSymbols:
    """
    Christoffel symbols Γ^k_ij of a Riemannian metric.

    Attributes:
        symbols: 3D array where symbols[k, i, j] = Γ^k_ij
        coordinate_names: Names of coordinates
        base_point: Shape space state where symbols are evaluated
    """

    symbols: np.ndarray  # Shape (n, n, n)
    coordinate_names: list[str]
    base_point: ShapeSpaceState

    def __getitem__(self, indices: tuple) -> float:
        """
        Access Γ^k_ij via christoffel[k, i, j].

        Args:
            indices: (k, i, j)

        Returns:
            Γ^k_ij
        """
        k, i, j = indices
        return self.symbols[k, i, j]

    def geodesic_equation_rhs(self, velocity: np.ndarray) -> np.ndarray:
        """
        Compute RHS of geodesic equation: -Γ^k_ij v^i v^j.

        The geodesic equation is:
            d²x^k/dt² + Γ^k_ij (dx^i/dt)(dx^j/dt) = 0

        Args:
            velocity: dx^i/dt (tangent vector)

        Returns:
            Acceleration: -Γ^k_ij v^i v^j
        """
        n = self.symbols.shape[0]
        acceleration = np.zeros(n)

        for k in range(n):
            for i in range(n):
                for j in range(n):
                    acceleration[k] -= self.symbols[k, i, j] * velocity[i] * velocity[j]

        return acceleration


def compute_metric_derivatives(
    metric_func: Callable[[ShapeSpaceState], RiemannianMetric],
    base_state: ShapeSpaceState,
    epsilon: float = 1e-6
) -> np.ndarray:
    """
    Compute ∂g_ij/∂x^k using central finite differences.

    Args:
        metric_func: Function that computes metric at any state
        base_state: Point where to compute derivatives
        epsilon: Step size for finite differences

    Returns:
        3D array dg where dg[k, i, j] = ∂g_ij/∂x^k

    Notes:
        - Uses central differences for better accuracy
        - May be numerically unstable for small epsilon
        - Richardson extrapolation could improve accuracy
    """
    g_base = metric_func(base_state)
    n = g_base.components.shape[0]

    dg = np.zeros((n, n, n))

    for k in range(n):
        # Perturb k-th coordinate
        state_plus = _perturb_shape_coordinate(base_state, k, epsilon)
        state_minus = _perturb_shape_coordinate(base_state, k, -epsilon)

        try:
            g_plus = metric_func(state_plus)
            g_minus = metric_func(state_minus)

            # Central difference: ∂g_ij/∂x^k
            dg[k, :, :] = (g_plus.components - g_minus.components) / (2 * epsilon)

        except ValueError:
            # Perturbed state may be invalid
            # Try one-sided difference
            try:
                g_plus = metric_func(state_plus)
                dg[k, :, :] = (g_plus.components - g_base.components) / epsilon
            except:
                # Give up, leave as zero
                pass

    return dg


def _perturb_shape_coordinate(
    shape_state: ShapeSpaceState,
    coord_index: int,
    delta: float
) -> ShapeSpaceState:
    """Perturb a single shape coordinate."""
    r12, r23, r31 = shape_state.r12, shape_state.r23, shape_state.r31

    if coord_index == 0:
        r12 += delta
    elif coord_index == 1:
        r23 += delta
    elif coord_index == 2:
        r31 += delta

    # Check triangle inequality
    if not (r12 + r23 > r31 and r23 + r31 > r12 and r31 + r12 > r23):
        raise ValueError("Triangle inequality violated")

    return ShapeSpaceState(
        r12=r12, r23=r23, r31=r31,
        dr12_dt=shape_state.dr12_dt,
        dr23_dt=shape_state.dr23_dt,
        dr31_dt=shape_state.dr31_dt,
        L=shape_state.L,
        theta=shape_state.theta,
        dtheta_dt=shape_state.dtheta_dt,
        dimension=shape_state.dimension
    )


def compute_christoffel_symbols(
    metric: RiemannianMetric,
    metric_derivatives: np.ndarray
) -> ChristoffelSymbols:
    """
    Compute Christoffel symbols from metric and its derivatives.

    Formula:
        Γ^k_ij = (1/2) g^kl (∂g_jl/∂x^i + ∂g_il/∂x^j - ∂g_ij/∂x^l)

    Args:
        metric: Metric tensor g_ij
        metric_derivatives: ∂g_ij/∂x^k (3D array)

    Returns:
        ChristoffelSymbols object

    Example:
        >>> # At some shape space point
        >>> g = compute_jm_metric(state, masses, energy, L)
        >>> metric_func = lambda s: compute_jm_metric(s, masses, energy, L)
        >>> dg = compute_metric_derivatives(metric_func, state)
        >>> christoffel = compute_christoffel_symbols(g, dg)
        >>> print(christoffel[0, 1, 2])  # Γ^0_12
    """
    g = metric.components
    g_inv = metric.inverse()
    dg = metric_derivatives  # dg[k, i, j] = ∂g_ij/∂x^k

    n = g.shape[0]
    christoffel = np.zeros((n, n, n))

    # Γ^k_ij = (1/2) g^kl (∂_i g_jl + ∂_j g_il - ∂_l g_ij)
    for k in range(n):
        for i in range(n):
            for j in range(n):
                # Sum over l
                sum_val = 0.0
                for l in range(n):
                    term = (
                        dg[i, j, l] +  # ∂g_jl/∂x^i
                        dg[j, i, l] -  # ∂g_il/∂x^j
                        dg[l, i, j]    # ∂g_ij/∂x^l
                    )
                    sum_val += g_inv[k, l] * term

                christoffel[k, i, j] = 0.5 * sum_val

    return ChristoffelSymbols(
        symbols=christoffel,
        coordinate_names=metric.coordinate_names,
        base_point=metric.base_point
    )


def compute_christoffel_derivatives(
    christoffel_func: Callable[[ShapeSpaceState], ChristoffelSymbols],
    base_state: ShapeSpaceState,
    epsilon: float = 1e-6
) -> np.ndarray:
    """
    Compute ∂Γ^k_ij/∂x^l using finite differences.

    This is needed for computing the Ricci tensor.

    Args:
        christoffel_func: Function that computes Christoffel symbols
        base_state: Point where to compute derivatives
        epsilon: Step size

    Returns:
        4D array dGamma where dGamma[l, k, i, j] = ∂Γ^k_ij/∂x^l

    Notes:
        - This is computationally expensive (second derivatives of metric)
        - Numerical stability can be an issue
        - Consider using symbolic differentiation for analytical cases
    """
    Gamma_base = christoffel_func(base_state)
    n = Gamma_base.symbols.shape[0]

    dGamma = np.zeros((n, n, n, n))

    for l in range(n):
        # Perturb l-th coordinate
        state_plus = _perturb_shape_coordinate(base_state, l, epsilon)
        state_minus = _perturb_shape_coordinate(base_state, l, -epsilon)

        try:
            Gamma_plus = christoffel_func(state_plus)
            Gamma_minus = christoffel_func(state_minus)

            # Central difference
            dGamma[l, :, :, :] = (Gamma_plus.symbols - Gamma_minus.symbols) / (2 * epsilon)

        except ValueError:
            # Perturbed state invalid, try one-sided
            try:
                Gamma_plus = christoffel_func(state_plus)
                dGamma[l, :, :, :] = (Gamma_plus.symbols - Gamma_base.symbols) / epsilon
            except:
                pass

    return dGamma


def validate_christoffel_symmetry(
    christoffel: ChristoffelSymbols,
    tolerance: float = 1e-12
) -> dict:
    """
    Validate symmetry property: Γ^k_ij = Γ^k_ji.

    This must hold for the Levi-Civita connection (torsion-free).

    Args:
        christoffel: Christoffel symbols to validate
        tolerance: Numerical tolerance

    Returns:
        Dictionary with validation results
    """
    Gamma = christoffel.symbols
    n = Gamma.shape[0]

    max_asymmetry = 0.0
    asymmetric_count = 0

    for k in range(n):
        for i in range(n):
            for j in range(i+1, n):  # Only check upper triangle
                diff = abs(Gamma[k, i, j] - Gamma[k, j, i])
                max_asymmetry = max(max_asymmetry, diff)

                if diff > tolerance:
                    asymmetric_count += 1

    symmetric = (max_asymmetry < tolerance)

    return {
        'symmetric': symmetric,
        'max_asymmetry': max_asymmetry,
        'asymmetric_pairs': asymmetric_count,
        'tolerance': tolerance
    }


def integrate_geodesic(
    initial_state: ShapeSpaceState,
    initial_velocity: np.ndarray,
    masses: Masses,
    energy: float,
    L_magnitude: float,
    t_span: tuple,
    n_steps: int = 1000
) -> tuple:
    """
    Integrate geodesic in JM metric.

    Solves:
        d²x^k/dt² + Γ^k_ij (dx^i/dt)(dx^j/dt) = 0

    Args:
        initial_state: Starting point in shape space
        initial_velocity: Initial tangent vector dx/dt
        masses: Mass parameters
        energy: Total energy
        L_magnitude: Angular momentum
        t_span: (t_start, t_end)
        n_steps: Number of integration steps

    Returns:
        Tuple of (times, states, velocities)

    Notes:
        - Geodesics in JM metric = dynamical trajectories at fixed E
        - Uses RK4 integration
        - May fail near metric singularities
    """
    from scipy.integrate import solve_ivp

    def geodesic_rhs(t, y):
        """RHS of geodesic equation as first-order system"""
        # y = [x, dx/dt] where x are shape coordinates
        n = 3
        x = y[:n]  # Shape coordinates
        v = y[n:]  # Velocities

        # Reconstruct shape state
        state = ShapeSpaceState(
            r12=x[0], r23=x[1], r31=x[2],
            dr12_dt=v[0], dr23_dt=v[1], dr31_dt=v[2],
            L=L_magnitude,
            dimension=2
        )

        try:
            # Compute metric
            metric = compute_jm_metric(state, masses, energy, L_magnitude)

            # Compute metric derivatives
            metric_func = lambda s: compute_jm_metric(s, masses, energy, L_magnitude)
            dg = compute_metric_derivatives(metric_func, state)

            # Compute Christoffel symbols
            christoffel = compute_christoffel_symbols(metric, dg)

            # Geodesic acceleration
            acceleration = christoffel.geodesic_equation_rhs(v)

            # Return [velocity, acceleration]
            return np.concatenate([v, acceleration])

        except (ValueError, np.linalg.LinAlgError):
            # Metric singular or invalid state
            return np.zeros(2 * n)

    # Initial conditions
    r0 = np.array([initial_state.r12, initial_state.r23, initial_state.r31])
    v0 = initial_velocity
    y0 = np.concatenate([r0, v0])

    # Integrate
    sol = solve_ivp(
        geodesic_rhs,
        t_span,
        y0,
        method='RK45',
        t_eval=np.linspace(t_span[0], t_span[1], n_steps),
        rtol=1e-10,
        atol=1e-12
    )

    # Extract results
    times = sol.t
    n = 3
    states = sol.y[:n, :].T
    velocities = sol.y[n:, :].T

    return times, states, velocities
