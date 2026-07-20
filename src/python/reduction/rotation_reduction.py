"""Legacy orientation gauge fixing for the three-body problem.

Qualification notice: this compatibility module rotates a redundant Cartesian
representative and is not a complete Marsden-Weinstein reduction. Use
``src.python.threebody_reduction`` for the qualified generic SO(3) Poisson
quotient chart, singular-stratum checks, and exact reconstruction metadata.

It rotates a redundant Cartesian state to selected orientation gauges. It was
intended as the second reduction stage.

Mathematical Background:
    - Symmetry group: G = SO(3) (rotations in 3D space)
    - Momentum map: μ(state) = sum(r_i × m_i * v_i) = total angular momentum L
    - Reduced space: μ⁻¹(L₀) / SO(3) = shape space with fixed L

Physical Interpretation:
    The Hamiltonian is invariant under rotations (isotropy of space).
    By Noether's theorem, this implies conservation of angular momentum.
    We quotient by rotations to obtain the "shape dynamics" - how the
    triangle configuration evolves independent of its orientation in space.

Key Insight:
    Unlike translation reduction, rotation reduction introduces a "magnetic"
    term in the reduced symplectic form - the mechanical connection. This
    encodes how the system rotates in response to shape changes.

References:
    - Marsden & Weinstein, "Reduction of symplectic manifolds with symmetry" (1974)
    - Littlejohn & Reinsch, "Gauge fields in the separation of rotations" (1997)
    - Cushman & Bates, "Global Aspects of Classical Integrable Systems" (1997), Ch. 5
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, Literal
from enum import Enum

from ..coordinates.cartesian import CartesianState, compute_angular_momentum
from ..coordinates.base import Masses
from .base import SymplecticReduction
from .translation_reduction import TranslationReducedState


class OrientationConvention(Enum):
    """
    Conventions for fixing orientation (gauge choice).

    When we quotient by SO(3), we must choose a representative from each orbit.
    Different conventions are useful for different applications.
    """
    ALIGN_AXIS_12 = "align_12"
    """Align body 1-2 axis with x-axis (planar: SO(2) rotation)"""

    ALIGN_AXIS_23 = "align_23"
    """Align body 2-3 axis with x-axis"""

    ALIGN_ANGULAR_MOMENTUM = "align_L"
    """Align angular momentum with z-axis (spatial case)"""

    PRINCIPAL_AXES = "principal"
    """Align with principal axes of inertia tensor"""


@dataclass(frozen=True)
class RotationReducedState:
    """
    State in rotation-reduced phase space (shape space).

    This is a state with fixed orientation according to some convention.

    Dimension:
        - Planar: 12 → 7 DOF (removed 3 translation + 2 rotation)
        - Spatial: 18 → 12 DOF (removed 3 translation + 3 rotation)

    Attributes:
        state: Underlying Cartesian state (in canonical orientation)
        masses: Mass parameters
        L: Angular momentum (conserved quantity labeling the reduction)
        orientation_convention: Which convention was used to fix orientation
        theta: Orientation angle that was removed (for reconstruction)

    Note:
        The angular momentum L is a "label" on the reduced space - it's
        conserved and parameterizes which reduction we're on.
    """
    state: CartesianState
    masses: Masses
    L: np.ndarray  # Angular momentum vector (3D)
    orientation_convention: OrientationConvention = OrientationConvention.ALIGN_AXIS_12
    theta: Optional[float] = None  # Rotation angle (planar case)

    @property
    def is_planar(self) -> bool:
        """Check if this is planar motion"""
        return self.state.dimension == 2

    @property
    def L_magnitude(self) -> float:
        """Magnitude of angular momentum"""
        return np.linalg.norm(self.L)

    @property
    def L_z(self) -> float:
        """Out-of-plane component (planar case)"""
        return self.L[2]

    def compute_energy(self, G: float = 1.0) -> float:
        """
        Compute energy of reduced state.

        Since rotation is a symmetry, the reduced Hamiltonian is
        the restriction of H to fixed angular momentum L.

        Args:
            G: Gravitational constant

        Returns:
            Total energy H = T + V
        """
        from ..coordinates.cartesian import compute_energy
        return compute_energy(self.state, self.masses, G=G)


class RotationReduction(SymplecticReduction):
    """
    Symplectic reduction by SO(3) rotations.

    Removes rotational degrees of freedom, reducing to shape space.

    Algorithm:
        1. Compute angular momentum L
        2. Choose canonical orientation (gauge)
        3. Rotate state to canonical form
        4. Return reduced state with L

    The choice of gauge (orientation convention) affects the explicit form
    of the mechanical connection, but not the physical dynamics.

    Examples:
        >>> from coordinates import CartesianState
        >>> from coordinates.base import Masses
        >>> from reduction import TranslationReduction
        >>>
        >>> # Start with arbitrary state
        >>> state = random_cartesian_state()
        >>> masses = Masses(1.0, 1.0, 1.0)
        >>>
        >>> # First reduce by translations
        >>> trans_reducer = TranslationReduction()
        >>> trans_reduced = trans_reducer.reduce(state, masses)
        >>>
        >>> # Then reduce by rotations
        >>> rot_reducer = RotationReduction()
        >>> rot_reduced = rot_reducer.reduce(trans_reduced.state, masses)
        >>>
        >>> # Now we're in shape space!
        >>> print(f"Angular momentum: {rot_reduced.L_magnitude}")
    """

    def __init__(
        self,
        orientation_convention: OrientationConvention = OrientationConvention.ALIGN_AXIS_12,
        tolerance: float = 1e-14
    ):
        """
        Initialize rotation reduction.

        Args:
            orientation_convention: How to fix orientation (default: align 1-2 axis)
            tolerance: Tolerance for constraint enforcement
        """
        self.orientation_convention = orientation_convention
        self.tolerance = tolerance

    def momentum_map(self, state: CartesianState, masses: Masses) -> np.ndarray:
        """
        Compute total angular momentum (momentum map for rotations).

        μ_rot(state) = L = sum(r_i × m_i * v_i)

        This is the Noether charge for rotational symmetry.

        Args:
            state: Cartesian state
            masses: Mass parameters

        Returns:
            L: Total angular momentum vector (3D)

        Note:
            For planar motion, only L_z (out-of-plane component) is non-zero.
        """
        return compute_angular_momentum(state, masses)

    def reduce(
        self,
        state: CartesianState,
        masses: Masses,
        L_target: Optional[np.ndarray] = None
    ) -> RotationReducedState:
        """
        Project state onto rotation-reduced space.

        Algorithm:
            1. Compute current angular momentum L
            2. Choose canonical orientation (according to convention)
            3. Rotate state to canonical orientation
            4. Return reduced state with L and rotation angle

        Args:
            state: Cartesian state (should be in barycentric frame)
            masses: Mass parameters
            L_target: Target angular momentum (for validation, optional)

        Returns:
            Reduced state in canonical orientation

        Raises:
            AssertionError: If state is not in barycentric frame or L doesn't match target
        """
        # Verify barycentric frame (should be done before rotation reduction)
        self._check_barycentric(state, masses)

        # Compute angular momentum
        L = self.momentum_map(state, masses)

        # Validate against target if provided
        if L_target is not None:
            if np.linalg.norm(L - L_target) > self.tolerance:
                raise ValueError(
                    f"Angular momentum mismatch: {L} vs {L_target}"
                )

        # Fix orientation according to convention
        if self.orientation_convention == OrientationConvention.ALIGN_AXIS_12:
            state_canonical, theta = self._align_axis_12(state)

        elif self.orientation_convention == OrientationConvention.ALIGN_ANGULAR_MOMENTUM:
            state_canonical, theta = self._align_angular_momentum(state, L)

        elif self.orientation_convention == OrientationConvention.PRINCIPAL_AXES:
            state_canonical, theta = self._align_principal_axes(state, masses)

        else:
            raise NotImplementedError(
                f"Convention {self.orientation_convention} not implemented"
            )

        return RotationReducedState(
            state=state_canonical,
            masses=masses,
            L=L,
            orientation_convention=self.orientation_convention,
            theta=theta
        )

    def _check_barycentric(self, state: CartesianState, masses: Masses) -> None:
        """
        Verify that state is in barycentric frame.

        Rotation reduction should only be applied after translation reduction.
        """
        m = np.array([masses.m1, masses.m2, masses.m3])
        r_cm = np.sum(state.positions * m[:, np.newaxis], axis=0)
        v_cm = np.sum(state.velocities * m[:, np.newaxis], axis=0)

        if np.linalg.norm(r_cm) > 1e-10:
            raise ValueError(
                f"State is not in barycentric frame: r_cm = {r_cm}\n"
                "Apply translation reduction first!"
            )

        if np.linalg.norm(v_cm) > 1e-10:
            raise ValueError(
                f"State has non-zero total momentum: v_cm = {v_cm}\n"
                "Apply translation reduction first!"
            )

    def _align_axis_12(self, state: CartesianState) -> tuple[CartesianState, float]:
        """
        Align body 1-2 axis with x-axis (planar SO(2) rotation).

        Convention: Rotate so that vector r1 - r2 lies along positive x-axis.

        This is the most common choice for planar problems, as it directly
        reduces the SO(2) rotational freedom.

        Returns:
            state_canonical: Rotated state
            theta: Rotation angle applied (for inverse transformation)
        """
        # Relative position vector
        r12 = state.positions[0] - state.positions[1]

        # Current angle in xy-plane
        theta = np.arctan2(r12[1], r12[0])

        # Rotation matrix (about z-axis, angle -theta to align with x-axis)
        R = self._rotation_matrix_z(-theta)

        # Apply rotation to all positions and velocities
        positions_rot = state.positions @ R.T
        velocities_rot = state.velocities @ R.T

        state_canonical = CartesianState(
            positions=positions_rot,
            velocities=velocities_rot,
            dimension=state.dimension,
            precision=state.precision
        )

        return state_canonical, theta

    def _align_angular_momentum(
        self,
        state: CartesianState,
        L: np.ndarray
    ) -> tuple[CartesianState, Optional[float]]:
        """
        Align angular momentum with z-axis (spatial case).

        For planar motion, L already points in z-direction, so this reduces
        to aligning the configuration in the plane.

        For spatial motion, we apply a rotation to make L = (0, 0, |L|).

        Returns:
            state_canonical: Rotated state
            theta: Rotation angle (planar case) or None (spatial case)
        """
        L_norm = np.linalg.norm(L)

        if L_norm < 1e-14:
            # Zero angular momentum - no preferred direction
            # Fall back to axis alignment
            return self._align_axis_12(state)

        # Normalize L
        L_hat = L / L_norm
        z_hat = np.array([0.0, 0.0, 1.0])

        # Check if already aligned
        if np.linalg.norm(L_hat - z_hat) < 1e-14:
            # Already aligned, now fix remaining SO(2) freedom
            return self._align_axis_12(state)

        # Check if antiparallel (L points in -z direction)
        if np.linalg.norm(L_hat + z_hat) < 1e-14:
            # Flip about x-axis
            R = np.diag([1.0, -1.0, -1.0])
            theta = np.pi
        else:
            # General case: rotate L to align with z
            # Rotation axis: n = L_hat × z_hat
            n = np.cross(L_hat, z_hat)
            n_hat = n / np.linalg.norm(n)

            # Rotation angle
            cos_theta = np.dot(L_hat, z_hat)
            theta = np.arccos(np.clip(cos_theta, -1.0, 1.0))

            # Rodrigues formula for rotation matrix
            R = self._rotation_matrix_axis_angle(n_hat, theta)

        # Apply rotation
        positions_rot = state.positions @ R.T
        velocities_rot = state.velocities @ R.T

        state_intermediate = CartesianState(
            positions=positions_rot,
            velocities=velocities_rot,
            dimension=state.dimension,
            precision=state.precision
        )

        # Fix remaining SO(2) freedom
        return self._align_axis_12(state_intermediate)

    def _align_principal_axes(
        self,
        state: CartesianState,
        masses: Masses
    ) -> tuple[CartesianState, Optional[float]]:
        """
        Align with principal axes of inertia tensor.

        The inertia tensor is:
            I = sum(m_i * (|r_i|² * Id - r_i ⊗ r_i))

        We diagonalize I and rotate to align principal axes with coordinate axes.

        Returns:
            state_canonical: Rotated state
            theta: None (3D rotation, not a single angle)
        """
        # Compute inertia tensor
        I = self._compute_inertia_tensor(state, masses)

        # Diagonalize: I = R Λ R^T
        eigenvalues, eigenvectors = np.linalg.eigh(I)

        # Rotation matrix (eigenvectors are columns)
        # We want R^T to rotate to principal axes
        R = eigenvectors

        # Ensure proper rotation (det = 1)
        if np.linalg.det(R) < 0:
            R[:, 0] *= -1  # Flip first eigenvector

        # Apply rotation
        positions_rot = state.positions @ R.T
        velocities_rot = state.velocities @ R.T

        state_canonical = CartesianState(
            positions=positions_rot,
            velocities=velocities_rot,
            dimension=state.dimension,
            precision=state.precision
        )

        return state_canonical, None

    @staticmethod
    def _compute_inertia_tensor(state: CartesianState, masses: Masses) -> np.ndarray:
        """
        Compute inertia tensor relative to barycenter.

        I = sum(m_i * (|r_i|² * Id - r_i ⊗ r_i))

        Args:
            state: Cartesian state (in barycentric frame)
            masses: Mass parameters

        Returns:
            I: 3×3 inertia tensor
        """
        m = np.array([masses.m1, masses.m2, masses.m3])
        I = np.zeros((3, 3))

        for i in range(3):
            r = state.positions[i]
            r_squared = np.dot(r, r)

            # I_ij = m * (|r|² δ_ij - r_i r_j)
            I += m[i] * (r_squared * np.eye(3) - np.outer(r, r))

        return I

    @staticmethod
    def _rotation_matrix_z(theta: float) -> np.ndarray:
        """
        Rotation matrix about z-axis by angle theta.

        R_z(θ) = [cos θ  -sin θ  0]
                 [sin θ   cos θ  0]
                 [  0       0    1]

        Args:
            theta: Rotation angle (radians)

        Returns:
            R: 3×3 rotation matrix
        """
        c, s = np.cos(theta), np.sin(theta)
        return np.array([
            [c, -s, 0.0],
            [s,  c, 0.0],
            [0.0,  0.0, 1.0]
        ])

    @staticmethod
    def _rotation_matrix_axis_angle(n: np.ndarray, theta: float) -> np.ndarray:
        """
        Rotation matrix about axis n by angle theta (Rodrigues formula).

        R = I + sin(θ) [n]_× + (1 - cos(θ)) [n]_×²

        where [n]_× is the skew-symmetric matrix:
            [n]_× = [  0   -n_z   n_y ]
                    [ n_z    0   -n_x ]
                    [-n_y   n_x    0  ]

        Args:
            n: Unit vector (rotation axis)
            theta: Rotation angle (radians)

        Returns:
            R: 3×3 rotation matrix

        References:
            https://en.wikipedia.org/wiki/Rodrigues%27_rotation_formula
        """
        c, s = np.cos(theta), np.sin(theta)

        # Skew-symmetric matrix [n]_×
        nx = np.array([
            [0.0, -n[2], n[1]],
            [n[2], 0.0, -n[0]],
            [-n[1], n[0], 0.0]
        ])

        # Rodrigues formula
        R = np.eye(3) + s * nx + (1.0 - c) * (nx @ nx)
        return R

    def validate_constraint(
        self,
        state: CartesianState,
        masses: Masses,
        L_target: np.ndarray,
        tolerance: Optional[float] = None
    ) -> bool:
        """
        Check if state has the target angular momentum.

        Args:
            state: State to validate
            masses: Mass parameters
            L_target: Expected angular momentum
            tolerance: Override default tolerance (optional)

        Returns:
            True if ||L - L_target|| < tolerance
        """
        tol = tolerance if tolerance is not None else self.tolerance
        L = self.momentum_map(state, masses)
        return np.linalg.norm(L - L_target) < tol

    def reconstruct_from_reduced(
        self,
        reduced_state: RotationReducedState,
        theta: float
    ) -> CartesianState:
        """
        Reconstruct full Cartesian state from reduced state.

        This applies the inverse rotation to restore the original orientation.

        Args:
            reduced_state: State in canonical orientation
            theta: Rotation angle to apply (for SO(2) case)

        Returns:
            Cartesian state in arbitrary orientation

        Note:
            For spatial (SO(3)) reductions, this only works if the reduction
            was by SO(2) (planar). For full SO(3), we need the full rotation
            matrix, not just an angle.
        """
        if reduced_state.orientation_convention == OrientationConvention.ALIGN_AXIS_12:
            # Inverse rotation about z-axis
            R = self._rotation_matrix_z(theta)
        else:
            raise NotImplementedError(
                f"Reconstruction not implemented for {reduced_state.orientation_convention}"
            )

        positions = reduced_state.state.positions @ R.T
        velocities = reduced_state.state.velocities @ R.T

        return CartesianState(
            positions=positions,
            velocities=velocities,
            dimension=reduced_state.state.dimension,
            precision=reduced_state.state.precision
        )

    def _apply_group_action(self, state: CartesianState, epsilon: float) -> CartesianState:
        """
        Apply infinitesimal rotation (for testing symmetry).

        Transformation: Rotate by small angle epsilon about z-axis.

        Args:
            state: Current state
            epsilon: Rotation angle (radians)

        Returns:
            Rotated state
        """
        R = self._rotation_matrix_z(epsilon)

        return CartesianState(
            positions=state.positions @ R.T,
            velocities=state.velocities @ R.T,
            dimension=state.dimension,
            precision=state.precision
        )


def test_rotation_invariance(
    state: CartesianState,
    masses: Masses,
    G: float = 1.0,
    n_tests: int = 10,
    tolerance: float = 1e-13
) -> dict:
    """
    Verify that Hamiltonian is invariant under rotations.

    Test: H(R·r_i, R·v_i) == H(r_i, v_i) for arbitrary rotation R ∈ SO(3)

    Args:
        state: Test state
        masses: Mass parameters
        G: Gravitational constant
        n_tests: Number of random rotations to test
        tolerance: Maximum allowed energy difference

    Returns:
        Dictionary with test results:
            - max_error: Maximum energy difference observed
            - mean_error: Mean energy difference
            - passed: True if all tests passed
    """
    from ..coordinates.cartesian import compute_energy

    E0 = compute_energy(state, masses, G=G)
    errors = []

    for _ in range(n_tests):
        # Random rotation: sample from SO(3)
        theta = np.random.uniform(0, 2 * np.pi)
        axis = np.random.randn(3)
        axis = axis / np.linalg.norm(axis)

        R = RotationReduction._rotation_matrix_axis_angle(axis, theta)

        # Rotate state
        state_rotated = CartesianState(
            positions=state.positions @ R.T,
            velocities=state.velocities @ R.T,
            dimension=state.dimension,
            precision=state.precision
        )

        E1 = compute_energy(state_rotated, masses, G=G)
        errors.append(abs(E1 - E0))

    max_error = max(errors)
    mean_error = np.mean(errors)

    return {
        'max_error': max_error,
        'mean_error': mean_error,
        'passed': max_error < tolerance,
        'n_tests': n_tests
    }


def test_angular_momentum_conservation(
    state0: RotationReducedState,
    integrator,
    t_span: tuple,
    tolerance: float = 1e-12,
    **integrator_kwargs
) -> dict:
    """
    Integrate reduced state and verify L remains constant.

    This tests that numerical integration preserves angular momentum.

    Args:
        state0: Initial rotation-reduced state
        integrator: Integration function
        t_span: (t_start, t_end) time interval
        tolerance: Maximum allowed angular momentum drift
        **integrator_kwargs: Additional arguments for integrator

    Returns:
        Dictionary with conservation results:
            - max_L_error: Maximum ||L - L0|| during integration
            - mean_L_error: Mean ||L - L0|| over trajectory
            - passed: True if max_L_error < tolerance
    """
    # Integrate
    solution = integrator(state0.state, state0.masses, t_span, **integrator_kwargs)

    # Compute angular momentum at all times
    reduction = RotationReduction()
    L_errors = []

    for state in solution.states:
        L = reduction.momentum_map(state, state0.masses)
        L_errors.append(np.linalg.norm(L - state0.L))

    max_L_error = max(L_errors)
    mean_L_error = np.mean(L_errors)

    return {
        'max_L_error': max_L_error,
        'mean_L_error': mean_L_error,
        'passed': max_L_error < tolerance,
        'n_timesteps': len(L_errors)
    }
