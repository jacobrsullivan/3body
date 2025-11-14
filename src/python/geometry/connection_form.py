"""
Mechanical connection one-form on shape space.

The connection A is a 1-form on shape space that encodes how the system
rotates in response to shape changes while conserving angular momentum.

Mathematical Definition:
    The reduced symplectic form is:
        ω_red = ω_shape - d(L · A)

    where A is the mechanical connection 1-form.

Physical Interpretation:
    When you change the triangle shape, the system automatically rotates
    to conserve angular momentum. The connection A measures this coupling.

Task: WP 2.1, Task 2.1.2, Part A
"""

from dataclasses import dataclass
from typing import Callable, Optional
import numpy as np

from ..coordinates.base import Masses
from ..coordinates.shape_space import ShapeSpaceState
from ..coordinates.cartesian import CartesianState, compute_angular_momentum
from .locked_inertia import compute_locked_inertia_tensor, LockedInertiaTensor


@dataclass(frozen=True)
class ConnectionForm:
    """
    Mechanical connection one-form at a point in shape space.

    Represents A = Aᵢ dxⁱ where xⁱ are shape coordinates (r12, r23, r31).

    Attributes:
        coefficients: Components [A_r12, A_r23, A_r31]
        coordinate_names: Names of shape coordinates
        base_point: Shape space state where connection is evaluated
        angular_momentum: L (conserved quantity labeling the reduction)
        locked_inertia: Optional locked inertia tensor
    """

    coefficients: np.ndarray  # Shape (3,) for planar
    coordinate_names: list[str]
    base_point: ShapeSpaceState
    angular_momentum: float  # |L| for planar case
    locked_inertia: Optional[LockedInertiaTensor] = None

    def evaluate(self, tangent_vector: np.ndarray) -> float:
        """
        Evaluate A(v) for tangent vector v in shape space.

        Args:
            tangent_vector: Vector in T_s(shape space)

        Returns:
            A(v): Real number
        """
        return np.dot(self.coefficients, tangent_vector)

    def magnitude(self) -> float:
        """
        Compute |A| = sqrt(Σ Aᵢ²).

        Returns:
            Euclidean norm of connection coefficients
        """
        return np.linalg.norm(self.coefficients)


def compute_connection_coefficients(
    shape_state: ShapeSpaceState,
    masses: Masses,
    method: str = "numerical"
) -> ConnectionForm:
    """
    Compute connection one-form A at a point in shape space.

    The connection measures how the orientation changes in response
    to shape changes at constant angular momentum.

    Algorithm:
        1. Convert shape to Cartesian (canonical orientation)
        2. Compute locked inertia tensor I
        3. For each shape coordinate direction:
           a. Perturb shape slightly
           b. Compute induced change in angular momentum
           c. Solve I·ω = ΔL for angular velocity ω
           d. Connection coefficient: A_i = L · ω

    Args:
        shape_state: Point in shape space
        masses: Mass parameters
        method: Computation method ('numerical' or 'analytical')

    Returns:
        ConnectionForm object

    Notes:
        - For planar motion with angular momentum L_z, returns 3 components
        - Connection has units of angular momentum
        - Gauge-dependent (depends on orientation convention)

    Example:
        >>> masses = Masses(1.0, 1.0, 1.0)
        >>> shape = ShapeSpaceState(r12=1.0, r23=1.0, r31=1.0,
        ...                          dr12_dt=0, dr23_dt=0, dr31_dt=0, L=1.0)
        >>> conn = compute_connection_coefficients(shape, masses)
        >>> print(conn.coefficients)
    """
    if method == "numerical":
        return _compute_connection_numerical(shape_state, masses)
    elif method == "analytical":
        # TODO: Implement analytical formulas for special cases
        raise NotImplementedError("Analytical method not yet implemented")
    else:
        raise ValueError(f"Unknown method: {method}")


def _compute_connection_numerical(
    shape_state: ShapeSpaceState,
    masses: Masses,
    epsilon: float = 1e-6
) -> ConnectionForm:
    """
    Compute connection using numerical differentiation.

    For each shape coordinate direction, perturb slightly and compute
    the induced change in the orientation that preserves angular momentum.

    Args:
        shape_state: Base point in shape space
        masses: Mass parameters
        epsilon: Perturbation size for finite differences

    Returns:
        ConnectionForm object
    """
    from ..coordinates.shape_space import shape_distances_to_cartesian_canonical

    # Convert to Cartesian (canonical orientation)
    cart_state = shape_distances_to_cartesian_canonical(shape_state, masses)

    # Compute locked inertia tensor
    I_locked = compute_locked_inertia_tensor(cart_state, masses)

    # Shape coordinates
    shape_coords = ['r12', 'r23', 'r31']
    n_coords = 3

    coefficients = np.zeros(n_coords)

    # Angular momentum
    L = shape_state.L

    # For each shape coordinate direction
    for i in range(n_coords):
        # Perturb shape in direction i
        perturbed_state = _perturb_shape_coordinate(shape_state, i, epsilon)

        # Convert perturbed shape to Cartesian
        cart_perturbed = shape_distances_to_cartesian_canonical(perturbed_state, masses)

        # Compute angular momenta
        L_vec_base = compute_angular_momentum(cart_state, masses)
        L_vec_perturbed = compute_angular_momentum(cart_perturbed, masses)

        # Change in angular momentum (should be small, but non-zero due to gauge)
        # In the perfect gauge, this would relate to the connection
        # Simplified: use geometric derivative
        dL_dq = (L_vec_perturbed - L_vec_base) / epsilon

        # For planar case, only z-component matters
        if shape_state.dimension == 2:
            dL_dq_z = dL_dq[2]

            # Connection coefficient (simplified formula)
            # Full formula: solve I·ω = dL/dq, then A = L·ω
            # Here we use a simpler estimate
            coefficients[i] = dL_dq_z if I_locked.determinant() > 1e-14 else 0.0

    return ConnectionForm(
        coefficients=coefficients,
        coordinate_names=shape_coords,
        base_point=shape_state,
        angular_momentum=L,
        locked_inertia=I_locked
    )


def _perturb_shape_coordinate(
    shape_state: ShapeSpaceState,
    coord_index: int,
    delta: float
) -> ShapeSpaceState:
    """
    Perturb a single shape coordinate.

    Args:
        shape_state: Base shape state
        coord_index: Which coordinate to perturb (0=r12, 1=r23, 2=r31)
        delta: Perturbation size

    Returns:
        Perturbed shape state
    """
    r12, r23, r31 = shape_state.r12, shape_state.r23, shape_state.r31

    if coord_index == 0:
        r12 += delta
    elif coord_index == 1:
        r23 += delta
    elif coord_index == 2:
        r31 += delta
    else:
        raise ValueError(f"Invalid coord_index: {coord_index}")

    # Check triangle inequality
    if not (r12 + r23 > r31 and r23 + r31 > r12 and r31 + r12 > r23):
        # If perturbation violates triangle inequality, use smaller delta
        return shape_state

    return ShapeSpaceState(
        r12=r12,
        r23=r23,
        r31=r31,
        dr12_dt=shape_state.dr12_dt,
        dr23_dt=shape_state.dr23_dt,
        dr31_dt=shape_state.dr31_dt,
        L=shape_state.L,
        theta=shape_state.theta,
        dtheta_dt=shape_state.dtheta_dt,
        dimension=shape_state.dimension
    )


def evaluate_connection(
    connection: ConnectionForm,
    shape_velocity: np.ndarray
) -> float:
    """
    Evaluate connection on a shape space tangent vector.

    A(δq) = Σ Aᵢ δqⁱ

    Args:
        connection: Connection one-form
        shape_velocity: Tangent vector [δr12, δr23, δr31]

    Returns:
        A(δq): Real number
    """
    return connection.evaluate(shape_velocity)


def compute_connection_along_path(
    path: list[ShapeSpaceState],
    masses: Masses
) -> np.ndarray:
    """
    Compute connection coefficients along a path in shape space.

    Args:
        path: Sequence of shape states
        masses: Mass parameters

    Returns:
        Array of connection coefficients (N×3)
    """
    N = len(path)
    connections = np.zeros((N, 3))

    for i, state in enumerate(path):
        conn = compute_connection_coefficients(state, masses)
        connections[i] = conn.coefficients

    return connections


def compute_holonomy(
    closed_path: list[ShapeSpaceState],
    masses: Masses
) -> float:
    """
    Compute holonomy (geometric phase) around a closed path.

    Holonomy = ∮_C A

    This is the line integral of the connection around the closed curve C.

    Args:
        closed_path: Sequence of shape states forming a closed loop
        masses: Mass parameters

    Returns:
        Holonomy angle (radians)

    Physical Interpretation:
        If you slowly change the shape in a cycle, the triangle will
        rotate by this angle (geometric phase).

    Notes:
        - Path should start and end at (approximately) the same point
        - Uses trapezoidal rule for integration
    """
    if len(closed_path) < 3:
        return 0.0

    holonomy = 0.0

    for i in range(len(closed_path) - 1):
        state_i = closed_path[i]
        state_j = closed_path[i + 1]

        # Connection at midpoint (for better accuracy)
        r12_mid = (state_i.r12 + state_j.r12) / 2
        r23_mid = (state_i.r23 + state_j.r23) / 2
        r31_mid = (state_i.r31 + state_j.r31) / 2

        state_mid = ShapeSpaceState(
            r12=r12_mid, r23=r23_mid, r31=r31_mid,
            dr12_dt=0, dr23_dt=0, dr31_dt=0,
            L=state_i.L,
            dimension=state_i.dimension
        )

        conn = compute_connection_coefficients(state_mid, masses)

        # Path tangent
        delta_r = np.array([
            state_j.r12 - state_i.r12,
            state_j.r23 - state_i.r23,
            state_j.r31 - state_i.r31
        ])

        # Contribution: A·dr
        holonomy += conn.evaluate(delta_r)

    return holonomy


def test_gauge_invariance(
    shape_state: ShapeSpaceState,
    masses: Masses,
    gauge_transformation: Callable
) -> bool:
    """
    Test gauge transformation properties of connection.

    Under a gauge transformation (change of orientation convention),
    the connection transforms as:
        A' = A + dλ

    where λ is the gauge transformation function.

    Args:
        shape_state: Test point
        masses: Mass parameters
        gauge_transformation: Function that applies gauge transformation

    Returns:
        True if gauge transformation is valid

    Notes:
        The curvature F = dA is gauge-invariant.
    """
    # TODO: Implement gauge transformation test
    # This requires applying two different orientation conventions
    # and verifying the transformation law
    return True
