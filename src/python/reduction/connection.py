"""
Mechanical connection for shape space dynamics.

The mechanical connection is a 1-form on shape space that measures how
the system rotates in response to shape changes. It is the key geometric
structure arising from symplectic reduction by SO(3).

Mathematical Background:
    When we reduce by rotations, the reduced symplectic form is NOT simply
    the quotient of the original form. Instead:

        ω_red = ω_shape - d(L · A)

    where A is the mechanical connection - a 1-form on shape space.

Physical Interpretation:
    The connection A encodes the "rotational response" to shape changes.
    When you change the shape of the triangle (e.g., lengthen one side),
    the system automatically rotates to conserve angular momentum. This
    coupling is measured by A.

Curvature:
    The curvature F = dA measures the obstruction to integrability.
    If F = 0 (flat connection), the system may be integrable.
    If F ≠ 0, there is genuine geometric complexity.

Note:
    This is infrastructure for Task 2.1.2. The full implementation
    of the connection form computation will be completed there.

References:
    - Littlejohn & Reinsch, "Gauge fields in the separation of rotations
      and internal motions in the n-body problem" (1997)
    - Marsden & Ratiu, "Introduction to Mechanics and Symmetry" (1999), §4.3
    - Montgomery, "Gauge theory of the falling cat" (1993)
"""

import numpy as np
from typing import Optional, Callable
from dataclasses import dataclass

from ..coordinates.cartesian import CartesianState
from ..coordinates.base import Masses
from .rotation_reduction import RotationReducedState


@dataclass
class ConnectionData:
    """
    Data structure holding connection form information.

    Attributes:
        A: Connection 1-form (vector in shape space dual)
        F: Curvature 2-form (antisymmetric matrix)
        locked_inertia_tensor: Moment of inertia in body frame
    """
    A: Optional[np.ndarray] = None
    F: Optional[np.ndarray] = None
    locked_inertia_tensor: Optional[np.ndarray] = None


class MechanicalConnection:
    """
    Mechanical connection one-form on shape space.

    The connection A is a 1-form on shape space that encodes the
    coupling between shape changes and rotations.

    Reduced symplectic form:
        ω_red = ω_shape - d(L · A)

    where L is the angular momentum (constant on each reduced space).

    The connection can be computed via:
        A(δshape) = locked_inertia_tensor^{-1} · (body angular momentum change)

    This requires:
        1. Lifting shape velocity to configuration space
        2. Computing induced change in angular momentum
        3. Inverting the locked inertia tensor

    Note:
        Full implementation is deferred to Task 2.1.2. This module provides
        the interface and placeholder implementation.

    Examples:
        >>> masses = Masses(1.0, 1.0, 1.0)
        >>> connection = MechanicalConnection(masses)
        >>>
        >>> # For a reduced state
        >>> reduced_state = ...  # RotationReducedState
        >>> connection.compute_connection_form(reduced_state)
        ConnectionData(A=..., F=..., ...)
    """

    def __init__(self, masses: Masses, tolerance: float = 1e-14):
        """
        Initialize mechanical connection calculator.

        Args:
            masses: Mass parameters
            tolerance: Numerical tolerance
        """
        self.masses = masses
        self.tolerance = tolerance

    def compute_connection_form(
        self,
        reduced_state: RotationReducedState,
        shape_velocity: Optional[np.ndarray] = None
    ) -> ConnectionData:
        """
        Compute connection one-form A.

        If shape_velocity is provided, returns A(shape_velocity).
        Otherwise, returns the full connection form.

        Args:
            reduced_state: Current reduced state
            shape_velocity: Tangent vector in shape space (optional)

        Returns:
            ConnectionData with connection information

        Note:
            This is a placeholder implementation. Full computation
            will be implemented in Task 2.1.2.

        Mathematical Details:
            The connection is computed via the "amended potential" method:

            1. Locked inertia tensor:
               I_locked = sum(m_i * (|r_i|² Id - r_i ⊗ r_i))

            2. Connection form:
               A_i(δq) = (I_locked^{-1})_ij * (∂L_j / ∂q_k) * δq_k

            where q are shape coordinates and L is angular momentum.
        """
        # Placeholder implementation
        # TODO: Implement in Task 2.1.2

        # Compute locked inertia tensor
        I_locked = self._compute_locked_inertia_tensor(reduced_state.state)

        # Placeholder: return zero connection
        if shape_velocity is not None:
            A_value = np.zeros(3)  # Should be scalar for planar, vector for spatial
        else:
            A_value = None

        return ConnectionData(
            A=A_value,
            F=None,  # Curvature computed separately
            locked_inertia_tensor=I_locked
        )

    def compute_curvature(
        self,
        reduced_state: RotationReducedState
    ) -> np.ndarray:
        """
        Compute curvature of connection: F = dA.

        The curvature is a 2-form on shape space, measuring the
        obstruction to finding a flat (integrable) connection.

        Mathematically: F_ij = ∂A_j/∂q_i - ∂A_i/∂q_j

        This is analogous to the magnetic field in electromagnetism:
        the curl of the vector potential.

        Args:
            reduced_state: Current reduced state

        Returns:
            F: Curvature 2-form (antisymmetric matrix)

        Note:
            Placeholder implementation. Full computation in Task 2.1.2.

        References:
            - Marsden et al., "The Hamiltonian structure of the Maxwell-
              Vlasov equations" (1982)
            - Montgomery, "Gauge theory of the falling cat" (1993)
        """
        # Placeholder: return zero curvature
        # TODO: Implement numerical differentiation of A in Task 2.1.2

        shape_dim = 3 if reduced_state.is_planar else 6
        return np.zeros((shape_dim, shape_dim))

    def _compute_locked_inertia_tensor(self, state: CartesianState) -> np.ndarray:
        """
        Compute locked inertia tensor (moment of inertia in body frame).

        I_locked = sum(m_i * (|r_i|² Id - r_i ⊗ r_i))

        This is the inertia tensor relative to the barycenter.

        Args:
            state: Cartesian state (should be in canonical orientation)

        Returns:
            I: 3×3 inertia tensor
        """
        m = np.array([self.masses.m1, self.masses.m2, self.masses.m3])
        I = np.zeros((3, 3))

        for i in range(3):
            r = state.positions[i]
            r_squared = np.dot(r, r)

            # I_ij = m * (|r|² δ_ij - r_i r_j)
            I += m[i] * (r_squared * np.eye(3) - np.outer(r, r))

        return I

    def parallel_transport(
        self,
        reduced_state0: RotationReducedState,
        reduced_state1: RotationReducedState,
        path: Optional[Callable] = None
    ) -> float:
        """
        Compute parallel transport along a path in shape space.

        This measures the holonomy - how much the system rotates when
        you move around a closed loop in shape space.

        Holonomy = ∮_path A

        If the curvature F ≠ 0, the holonomy depends on the path
        (non-integrable geometric phase).

        Args:
            reduced_state0: Initial reduced state
            reduced_state1: Final reduced state
            path: Parameterized path in shape space (optional)

        Returns:
            Holonomy angle (for planar case)

        Note:
            Placeholder. Full implementation in Task 2.1.2.

        Physical Example:
            For the three-body problem, if you slowly change the shape
            from equilateral → collinear → equilateral, the triangle
            will rotate by a geometric phase angle (the holonomy).

        References:
            - Montgomery, "The geometric phase of the three-body problem" (1998)
        """
        # Placeholder implementation
        return 0.0

    def compute_gauge_transformation(
        self,
        old_convention,
        new_convention
    ) -> np.ndarray:
        """
        Compute gauge transformation between orientation conventions.

        When we change the gauge (orientation-fixing convention), the
        connection transforms as:
            A' = A + dλ

        where λ is the gauge transformation function.

        Args:
            old_convention: Original orientation convention
            new_convention: New orientation convention

        Returns:
            λ: Gauge transformation function (as a vector)

        Note:
            The curvature F = dA is gauge-invariant.
            Different gauges give different A, but same F.

        Placeholder for Task 2.1.2.
        """
        # Placeholder
        return np.zeros(3)

    def verify_symplectic_structure(
        self,
        reduced_state: RotationReducedState,
        tolerance: Optional[float] = None
    ) -> dict:
        """
        Verify that the reduced symplectic form is closed and non-degenerate.

        Checks:
            1. Closedness: d(ω_red) = 0 (by Stokes theorem on small loops)
            2. Non-degeneracy: det(ω_red) ≠ 0

        Args:
            reduced_state: Reduced state to test
            tolerance: Numerical tolerance (optional)

        Returns:
            Dictionary with verification results:
                - closed: True if dω_red ≈ 0
                - nondegenerate: True if det(ω_red) ≠ 0
                - closure_error: Numerical measure of d(ω_red)

        Note:
            Full implementation in Task 2.1.2 with symplectic integration tests.
        """
        tol = tolerance if tolerance is not None else self.tolerance

        # Placeholder
        return {
            'closed': True,
            'nondegenerate': True,
            'closure_error': 0.0,
            'note': 'Placeholder implementation - full verification in Task 2.1.2'
        }


def compute_geometric_phase(
    trajectory: list[RotationReducedState],
    masses: Masses
) -> float:
    """
    Compute geometric (Berry) phase along a closed trajectory in shape space.

    The geometric phase is:
        φ_geom = ∮_C A = ∫∫_S F

    where C is the closed curve and S is any surface bounded by C.
    By Stokes theorem, this equals the integral of curvature over S.

    This is the holonomy of the mechanical connection.

    Args:
        trajectory: Sequence of reduced states forming a closed loop
        masses: Mass parameters

    Returns:
        Geometric phase angle (radians)

    Physical Interpretation:
        If you slowly deform the three-body configuration in a cycle
        (e.g., equilateral → isosceles → collinear → isosceles → equilateral),
        the triangle will rotate by φ_geom even though you returned to
        the same shape. This is a purely geometric effect.

    Note:
        Placeholder implementation. Full computation in Task 2.1.2.

    References:
        - Montgomery, "The geometric phase of the three-body problem" (1998)
        - Guichardet, "On rotation and vibration motions of molecules" (1984)
    """
    # Placeholder: compute path integral of A
    # This requires integrating the connection along the trajectory

    connection = MechanicalConnection(masses)
    phase = 0.0

    # Discrete approximation: sum A(Δq_i)
    for i in range(len(trajectory) - 1):
        state_i = trajectory[i]
        state_j = trajectory[i + 1]

        # Compute shape change
        # delta_shape = shape(state_j) - shape(state_i)

        # Evaluate connection
        # A_i = connection.compute_connection_form(state_i, delta_shape)

        # Accumulate: φ += A_i
        pass

    return phase


def compute_hannay_angle(
    trajectory: list[RotationReducedState],
    masses: Masses
) -> float:
    """
    Compute Hannay angle for adiabatic motion in shape space.

    The Hannay angle is the classical analog of Berry phase.
    For slow (adiabatic) cyclic shape changes, the orientation
    drifts by the Hannay angle.

    Hannay angle = ∮ A · dq / ∮ ω_shape

    where the denominator is the action integral (to account for
    the rate of shape change).

    Args:
        trajectory: Adiabatic closed trajectory in shape space
        masses: Mass parameters

    Returns:
        Hannay angle (radians)

    Note:
        Placeholder for Task 2.1.2.

    References:
        - Hannay, "Angle variable holonomy in adiabatic excursion" (1985)
        - Berry, "Classical adiabatic angles and quantal adiabatic phase" (1985)
    """
    # Placeholder
    return 0.0
