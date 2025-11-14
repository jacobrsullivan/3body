"""
Pairwise KS transformation for three-body problem (WP 2.3, Part B).

Applies KS regularization to all three pairwise separations:
    r12 → u12 ∈ ℝ⁴
    r23 → u23 ∈ ℝ⁴
    r31 → u31 ∈ ℝ⁴

Total state space: 12 spinor components (constrained to 9D manifold).

Constraints:
    1. Bilinear relations: L(uᵢⱼ)·uᵢⱼ = rᵢⱼ for each pair
    2. Closure constraint: r12 + r23 + r31 = 0 (triangle closure)
"""

from dataclasses import dataclass
from typing import Tuple, Optional
import numpy as np

from .spinor_vector import SpinorVector
from .ks_transform import KSState, cartesian_to_ks, ks_to_cartesian
from .levi_civita import levi_civita_map, validate_bilinear_relation
from ..coordinates.base import CartesianState, Masses


@dataclass(frozen=True)
class PairwiseSpinorState:
    """
    Pairwise spinor state for three-body problem.

    Each pair (i,j) has its own spinor representation:
        u12: Spinor for r12 = r1 - r2
        u23: Spinor for r23 = r2 - r3
        u31: Spinor for r31 = r3 - r1

    Attributes:
        u12: Spinor for pair (1,2)
        u23: Spinor for pair (2,3)
        u31: Spinor for pair (3,1)
        u12_prime: Velocity spinor for pair (1,2)
        u23_prime: Velocity spinor for pair (2,3)
        u31_prime: Velocity spinor for pair (3,1)
        fictitious_time: s (regularized time)
        real_time: t (physical time, optional)

    Dimension: 12 spinor coordinates + 12 spinor momenta = 24D phase space
    Constraints reduce to 21D (3 bilinear + 3 closure components)
    """

    u12: SpinorVector
    u23: SpinorVector
    u31: SpinorVector
    u12_prime: SpinorVector
    u23_prime: SpinorVector
    u31_prime: SpinorVector
    fictitious_time: float = 0.0
    real_time: Optional[float] = None

    @property
    def spinor_coordinates(self) -> np.ndarray:
        """Stack all spinor coordinates: shape (12,)"""
        return np.concatenate([
            self.u12.to_array(),
            self.u23.to_array(),
            self.u31.to_array()
        ])

    @property
    def spinor_velocities(self) -> np.ndarray:
        """Stack all spinor velocities: shape (12,)"""
        return np.concatenate([
            self.u12_prime.to_array(),
            self.u23_prime.to_array(),
            self.u31_prime.to_array()
        ])

    def to_vector(self) -> np.ndarray:
        """Convert to state vector [u, u']: shape (24,)"""
        return np.concatenate([
            self.spinor_coordinates,
            self.spinor_velocities
        ])

    @classmethod
    def from_vector(
        cls,
        vec: np.ndarray,
        s: float = 0.0,
        t: Optional[float] = None
    ) -> "PairwiseSpinorState":
        """
        Reconstruct from state vector.

        Args:
            vec: State vector [u12, u23, u31, u12', u23', u31'] (24,)
            s: Fictitious time
            t: Real time

        Returns:
            PairwiseSpinorState
        """
        if len(vec) != 24:
            raise ValueError(f"Expected vector of length 24, got {len(vec)}")

        # Extract spinor coordinates
        u12 = SpinorVector(vec[0:4])
        u23 = SpinorVector(vec[4:8])
        u31 = SpinorVector(vec[8:12])

        # Extract spinor velocities
        u12_prime = SpinorVector(vec[12:16])
        u23_prime = SpinorVector(vec[16:20])
        u31_prime = SpinorVector(vec[20:24])

        return cls(
            u12=u12,
            u23=u23,
            u31=u31,
            u12_prime=u12_prime,
            u23_prime=u23_prime,
            u31_prime=u31_prime,
            fictitious_time=s,
            real_time=t
        )

    def to_cartesian(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Convert to Cartesian pairwise separations.

        Returns:
            (r12, r23, r31): Each ∈ ℝ³
        """
        # Transform each pair
        r12 = levi_civita_map(self.u12.to_array(), self.u12.to_array())
        r23 = levi_civita_map(self.u23.to_array(), self.u23.to_array())
        r31 = levi_civita_map(self.u31.to_array(), self.u31.to_array())

        return r12, r23, r31

    def validate_constraints(self, tolerance: float = 1e-10) -> dict:
        """
        Validate constraint satisfaction.

        Constraints:
            1. Bilinear: L(uᵢⱼ)·uᵢⱼ = rᵢⱼ for each pair
            2. Closure: r12 + r23 + r31 = 0

        Args:
            tolerance: Numerical tolerance

        Returns:
            Dictionary with constraint violations
        """
        r12, r23, r31 = self.to_cartesian()

        # Check bilinear relations
        bilinear_12 = validate_bilinear_relation(self.u12.to_array(), r12)
        bilinear_23 = validate_bilinear_relation(self.u23.to_array(), r23)
        bilinear_31 = validate_bilinear_relation(self.u31.to_array(), r31)

        # Check closure
        closure_residual = r12 + r23 + r31
        closure_error = np.linalg.norm(closure_residual)
        closure_satisfied = closure_error < tolerance

        return {
            'bilinear_12': bilinear_12,
            'bilinear_23': bilinear_23,
            'bilinear_31': bilinear_31,
            'closure_satisfied': closure_satisfied,
            'closure_error': closure_error,
            'closure_residual': closure_residual,
            'all_satisfied': (bilinear_12 and bilinear_23 and bilinear_31 and closure_satisfied)
        }


def cartesian_3bp_to_pairwise_ks(
    cartesian_state: CartesianState,
    s: float = 0.0,
    t: Optional[float] = None
) -> PairwiseSpinorState:
    """
    Transform 3BP Cartesian state → pairwise KS spinors.

    Args:
        cartesian_state: Positions and velocities of three bodies
        s: Fictitious time
        t: Real time

    Returns:
        PairwiseSpinorState with spinors for each pair

    Algorithm:
        1. Compute pairwise separations: rᵢⱼ = rᵢ - rⱼ
        2. Compute pairwise velocities: vᵢⱼ = vᵢ - vⱼ
        3. Apply KS transform to each pair independently
    """
    # Extract individual positions and velocities from (3,3) arrays
    r1, r2, r3 = cartesian_state.positions[0], cartesian_state.positions[1], cartesian_state.positions[2]
    v1, v2, v3 = cartesian_state.velocities[0], cartesian_state.velocities[1], cartesian_state.velocities[2]

    # Compute pairwise separations
    r12 = r1 - r2
    r23 = r2 - r3
    r31 = r3 - r1

    # Compute pairwise velocities
    v12 = v1 - v2
    v23 = v2 - v3
    v31 = v3 - v1

    # Apply KS transform to each pair
    ks12 = cartesian_to_ks(r12, v12, s, t)
    ks23 = cartesian_to_ks(r23, v23, s, t)
    ks31 = cartesian_to_ks(r31, v31, s, t)

    return PairwiseSpinorState(
        u12=ks12.u,
        u23=ks23.u,
        u31=ks31.u,
        u12_prime=ks12.u_prime,
        u23_prime=ks23.u_prime,
        u31_prime=ks31.u_prime,
        fictitious_time=s,
        real_time=t
    )


def pairwise_ks_to_cartesian_3bp(
    pairwise_state: PairwiseSpinorState,
    masses: Masses
) -> CartesianState:
    """
    Transform pairwise KS spinors → 3BP Cartesian state.

    Args:
        pairwise_state: Pairwise spinor state
        masses: Mass parameters

    Returns:
        CartesianState with positions and velocities

    Algorithm:
        1. Reconstruct pairwise separations from spinors: rᵢⱼ = L(uᵢⱼ)·uᵢⱼ
        2. Reconstruct pairwise velocities: vᵢⱼ = 2L(uᵢⱼ)·u'ᵢⱼ
        3. Solve for absolute positions using closure constraint
        4. Solve for absolute velocities

    Note:
        Absolute positions determined up to translation.
        We fix center of mass at origin.
    """
    # Get pairwise separations
    r12, r23, r31 = pairwise_state.to_cartesian()

    # Get pairwise velocities
    v12 = 2 * levi_civita_map(pairwise_state.u12.to_array(), pairwise_state.u12_prime.to_array())
    v23 = 2 * levi_civita_map(pairwise_state.u23.to_array(), pairwise_state.u23_prime.to_array())
    v31 = 2 * levi_civita_map(pairwise_state.u31.to_array(), pairwise_state.u31_prime.to_array())

    # Reconstruct absolute positions
    # From rᵢⱼ = rᵢ - rⱼ, we have:
    #   r12 = r1 - r2
    #   r23 = r2 - r3
    #   r31 = r3 - r1
    #
    # These are not independent (r12 + r23 + r31 = 0).
    # We can solve for relative positions, then fix COM.
    #
    # Let's use: r3 = 0 (arbitrary choice), then:
    #   r2 = -r23
    #   r1 = r12 + r2 = r12 - r23

    r3_temp = np.zeros(3)
    r2_temp = -r23
    r1_temp = r12 - r23

    # Shift to center of mass frame
    m1, m2, m3 = masses.m1, masses.m2, masses.m3
    M = m1 + m2 + m3

    r_com = (m1 * r1_temp + m2 * r2_temp + m3 * r3_temp) / M

    r1 = r1_temp - r_com
    r2 = r2_temp - r_com
    r3 = r3_temp - r_com

    # Reconstruct absolute velocities
    # From vᵢⱼ = vᵢ - vⱼ:
    v3_temp = np.zeros(3)
    v2_temp = -v23
    v1_temp = v12 - v23

    # Shift to center of mass frame
    v_com = (m1 * v1_temp + m2 * v2_temp + m3 * v3_temp) / M

    v1 = v1_temp - v_com
    v2 = v2_temp - v_com
    v3 = v3_temp - v_com

    # Create (3,3) arrays for CartesianState
    positions = np.array([r1, r2, r3])
    velocities = np.array([v1, v2, v3])

    return CartesianState(
        positions=positions,
        velocities=velocities
    )


def validate_pairwise_roundtrip(
    cartesian_state: CartesianState,
    masses: Masses,
    tolerance: float = 1e-10
) -> dict:
    """
    Test Cartesian → pairwise KS → Cartesian roundtrip.

    Args:
        cartesian_state: Initial state
        masses: Mass parameters
        tolerance: Numerical tolerance

    Returns:
        Validation results
    """
    # Forward transform
    pairwise_state = cartesian_3bp_to_pairwise_ks(cartesian_state)

    # Check constraints
    constraints = pairwise_state.validate_constraints(tolerance)

    # Backward transform
    reconstructed_state = pairwise_ks_to_cartesian_3bp(pairwise_state, masses)

    # Compare positions
    r1_error = np.linalg.norm(cartesian_state.r1 - reconstructed_state.r1)
    r2_error = np.linalg.norm(cartesian_state.r2 - reconstructed_state.r2)
    r3_error = np.linalg.norm(cartesian_state.r3 - reconstructed_state.r3)

    # Compare velocities
    v1_error = np.linalg.norm(cartesian_state.v1 - reconstructed_state.v1)
    v2_error = np.linalg.norm(cartesian_state.v2 - reconstructed_state.v2)
    v3_error = np.linalg.norm(cartesian_state.v3 - reconstructed_state.v3)

    max_position_error = max(r1_error, r2_error, r3_error)
    max_velocity_error = max(v1_error, v2_error, v3_error)

    roundtrip_success = (
        max_position_error < tolerance and
        max_velocity_error < tolerance
    )

    return {
        'roundtrip_success': roundtrip_success,
        'constraints_satisfied': constraints['all_satisfied'],
        'max_position_error': max_position_error,
        'max_velocity_error': max_velocity_error,
        'position_errors': [r1_error, r2_error, r3_error],
        'velocity_errors': [v1_error, v2_error, v3_error],
        'constraint_details': constraints
    }


def compute_constraint_manifold_dimension() -> dict:
    """
    Compute dimension of constraint manifold.

    Starting dimension: 24 (12 spinor coords + 12 spinor momenta)

    Constraints:
        1. Three bilinear relations (one per pair): 3 constraints
        2. Closure constraint r12 + r23 + r31 = 0: 3 components

    Total constraints: 6 (assuming independence)
    Constraint manifold dimension: 24 - 6 = 18

    Note: This is the phase space dimension.
    Configuration space: 12 - 3 = 9 (from 3 bilinear relations)

    Returns:
        Dictionary with dimension analysis
    """
    return {
        'full_phase_space_dim': 24,
        'num_bilinear_constraints': 3,
        'num_closure_constraints': 3,
        'total_constraints': 6,
        'constrained_phase_space_dim': 18,
        'configuration_space_dim': 12,
        'constrained_configuration_dim': 9,
        'interpretation': 'The pairwise KS lift embeds 3BP in 12D spinor space, constrained to 9D manifold'
    }
