"""
Translation reduction for 3-body problem.

Implements quotient by ℝ³ translations, enforcing zero total momentum.
This is the first stage of Marsden-Weinstein reduction for the 3BP.

Mathematical Background:
    - Symmetry group: G = ℝ³ (translations in 3D space)
    - Momentum map: μ(state) = sum(m_i * v_i) = total linear momentum P
    - Reduced space: μ⁻¹(0) / ℝ³ = barycentric frame with P = 0

Physical Interpretation:
    The Hamiltonian is invariant under translations (Galilean relativity).
    By Noether's theorem, this implies conservation of total momentum.
    We quotient by translations to remove the trivial center-of-mass motion.

References:
    - Marsden & Ratiu, "Introduction to Mechanics and Symmetry" (1999), §4.2
    - Meyer & Hall, "Introduction to Hamiltonian Dynamical Systems" (2008), §5.2
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional

from ..coordinates.cartesian import CartesianState, compute_energy
from ..coordinates.base import Masses
from .base import SymplecticReduction


@dataclass(frozen=True)
class TranslationReducedState:
    """
    State in translation-reduced phase space.

    This is a Cartesian state with enforced constraints:
        - Center of mass at origin: sum(m_i * r_i) = 0
        - Total momentum zero: sum(m_i * v_i) = 0

    Dimension: 18 → 15 DOF (removed 3 translation DOF)

    Attributes:
        state: Underlying Cartesian state (in barycentric frame)
        masses: Mass parameters

    Note:
        The state is immutable (frozen) to prevent accidental modification
        that could violate constraints.
    """
    state: CartesianState
    masses: Masses

    def __post_init__(self):
        """Validate constraints at construction"""
        assert self._check_barycentric(tolerance=1e-12), \
            "State must be in barycentric frame (center of mass at origin)"
        assert self._check_zero_momentum(tolerance=1e-12), \
            "State must have zero total momentum"

    def _check_barycentric(self, tolerance: float) -> bool:
        """Verify center of mass is at origin"""
        m = np.array([self.masses.m1, self.masses.m2, self.masses.m3])
        r_cm = np.sum(self.state.positions * m[:, np.newaxis], axis=0)
        return np.linalg.norm(r_cm) < tolerance

    def _check_zero_momentum(self, tolerance: float) -> bool:
        """Verify total momentum is zero"""
        m = np.array([self.masses.m1, self.masses.m2, self.masses.m3])
        P = np.sum(m[:, np.newaxis] * self.state.velocities, axis=0)
        return np.linalg.norm(P) < tolerance

    @property
    def dimension(self) -> int:
        """Dimension of reduced phase space"""
        return 15 if self.state.dimension == 3 else 9  # 18-3=15 or 12-3=9

    def compute_energy(self, G: float = 1.0) -> float:
        """
        Compute energy of reduced state.

        Since translation is a symmetry, the reduced Hamiltonian is
        simply the restriction of H to the barycentric frame.

        Args:
            G: Gravitational constant (default: 1.0)

        Returns:
            Total energy H = T + V
        """
        return compute_energy(self.state, self.masses, G=G)

    def compute_angular_momentum(self) -> np.ndarray:
        """
        Compute angular momentum (in barycentric frame).

        L = sum(r_i × m_i * v_i)

        Returns:
            Angular momentum vector (3D)
        """
        from ..coordinates.cartesian import compute_angular_momentum
        return compute_angular_momentum(self.state, self.masses)


class TranslationReduction(SymplecticReduction):
    """
    Symplectic reduction by ℝ³ translations.

    Removes center-of-mass motion from the 3-body problem.

    Algorithm:
        1. Compute center of mass: r_cm, v_cm
        2. Shift to barycentric frame: r_i → r_i - r_cm
        3. Verify constraints: sum(m_i r_i) = 0, sum(m_i v_i) = 0

    The reduced symplectic form is obtained by restricting the standard form
    to the constraint surface. Since translations act freely, there is no
    additional "magnetic" term (unlike rotation reduction).

    Examples:
        >>> from coordinates import CartesianState
        >>> from coordinates.base import Masses
        >>>
        >>> # Create arbitrary state
        >>> positions = np.random.randn(3, 3)
        >>> velocities = np.random.randn(3, 3)
        >>> state = CartesianState(positions, velocities)
        >>> masses = Masses(1.0, 1.0, 1.0)
        >>>
        >>> # Reduce to barycentric frame
        >>> reducer = TranslationReduction()
        >>> reduced = reducer.reduce(state, masses)
        >>>
        >>> # Verify constraints
        >>> assert reducer.validate_constraint(reduced.state, masses)
    """

    def __init__(self, tolerance: float = 1e-14):
        """
        Initialize translation reduction.

        Args:
            tolerance: Tolerance for constraint enforcement (default: 1e-14)
        """
        self.tolerance = tolerance

    def momentum_map(self, state: CartesianState, masses: Masses) -> np.ndarray:
        """
        Compute total linear momentum (momentum map for translations).

        μ_trans(state) = P = sum(m_i * v_i)

        This is the Noether charge for translational symmetry.

        Args:
            state: Cartesian state
            masses: Mass parameters

        Returns:
            P: Total linear momentum vector (3D)

        Note:
            In the barycentric frame, P should be zero (conservation law).
        """
        m = np.array([masses.m1, masses.m2, masses.m3])
        P = np.sum(m[:, np.newaxis] * state.velocities, axis=0)
        return P

    def reduce(self, state: CartesianState, masses: Masses) -> TranslationReducedState:
        """
        Project state onto translation-reduced space.

        Algorithm:
            1. Compute center of mass: r_cm = sum(m_i * r_i) / M
            2. Shift positions: r_i' = r_i - r_cm
            3. Compute momentum: v_cm = sum(m_i * v_i) / M
            4. Shift velocities: v_i' = v_i - v_cm

        Args:
            state: Arbitrary Cartesian state
            masses: Mass parameters

        Returns:
            Reduced state in barycentric frame

        Mathematical Justification:
            This projection is the moment map for the ℝ³ action.
            The quotient μ⁻¹(0) / ℝ³ is represented by choosing the unique
            representative with r_cm = 0.
        """
        m = np.array([masses.m1, masses.m2, masses.m3])
        M = masses.total

        # Compute center of mass
        r_cm = np.sum(state.positions * m[:, np.newaxis], axis=0) / M
        v_cm = np.sum(state.velocities * m[:, np.newaxis], axis=0) / M

        # Shift to barycentric frame
        positions_bc = state.positions - r_cm
        velocities_bc = state.velocities - v_cm

        # Create reduced state
        state_bc = CartesianState(
            positions=positions_bc,
            velocities=velocities_bc,
            dimension=state.dimension,
            precision=state.precision
        )

        return TranslationReducedState(state_bc, masses)

    def validate_constraint(
        self,
        state: CartesianState,
        masses: Masses,
        tolerance: Optional[float] = None
    ) -> bool:
        """
        Check if state satisfies zero momentum constraint.

        Args:
            state: State to validate
            masses: Mass parameters
            tolerance: Override default tolerance (optional)

        Returns:
            True if ||P|| < tolerance
        """
        tol = tolerance if tolerance is not None else self.tolerance
        P = self.momentum_map(state, masses)
        return np.linalg.norm(P) < tol

    def compute_reduced_hamiltonian(
        self,
        state: TranslationReducedState,
        G: float = 1.0
    ) -> float:
        """
        Compute Hamiltonian on reduced space.

        Since translation is a symmetry, the Hamiltonian is unchanged:
            H_red = H_original |_{P=0}

        Args:
            state: Translation-reduced state
            G: Gravitational constant

        Returns:
            Energy (scalar)
        """
        return state.compute_energy(G=G)

    def project_onto_constraint_surface(
        self,
        state: CartesianState,
        masses: Masses
    ) -> CartesianState:
        """
        Project arbitrary state onto zero momentum surface.

        This is the same as reduce() but returns CartesianState directly.

        Args:
            state: Arbitrary state
            masses: Mass parameters

        Returns:
            Projected state with P = 0, r_cm = 0
        """
        reduced = self.reduce(state, masses)
        return reduced.state

    def _apply_group_action(self, state: CartesianState, epsilon: float) -> CartesianState:
        """
        Apply infinitesimal translation (for testing symmetry).

        Transformation: r_i → r_i + epsilon * e_x
        where e_x = (1, 0, 0) is a unit vector.

        Args:
            state: Current state
            epsilon: Size of translation

        Returns:
            Translated state
        """
        translation_vector = np.array([epsilon, 0.0, 0.0])

        return CartesianState(
            positions=state.positions + translation_vector,
            velocities=state.velocities,  # Velocities unchanged
            dimension=state.dimension,
            precision=state.precision
        )


def test_translation_invariance(
    state: CartesianState,
    masses: Masses,
    G: float = 1.0,
    n_tests: int = 10,
    tolerance: float = 1e-13
) -> dict:
    """
    Verify that Hamiltonian is invariant under translations.

    Test: H(r_i, v_i) == H(r_i + a, v_i) for arbitrary translation vector a

    Args:
        state: Test state
        masses: Mass parameters
        G: Gravitational constant
        n_tests: Number of random translations to test
        tolerance: Maximum allowed energy difference

    Returns:
        Dictionary with test results:
            - max_error: Maximum energy difference observed
            - mean_error: Mean energy difference
            - passed: True if all tests passed

    Example:
        >>> state = random_cartesian_state()
        >>> masses = Masses(1.0, 1.0, 1.0)
        >>> result = test_translation_invariance(state, masses)
        >>> assert result['passed']
    """
    E0 = compute_energy(state, masses, G=G)
    errors = []

    for _ in range(n_tests):
        # Random translation
        a = np.random.randn(3)

        # Translate state
        state_translated = CartesianState(
            positions=state.positions + a,
            velocities=state.velocities,
            dimension=state.dimension,
            precision=state.precision
        )

        E1 = compute_energy(state_translated, masses, G=G)
        errors.append(abs(E1 - E0))

    max_error = max(errors)
    mean_error = np.mean(errors)

    return {
        'max_error': max_error,
        'mean_error': mean_error,
        'passed': max_error < tolerance,
        'n_tests': n_tests
    }


def test_momentum_conservation(
    state0: TranslationReducedState,
    integrator,
    t_span: tuple,
    tolerance: float = 1e-12,
    **integrator_kwargs
) -> dict:
    """
    Integrate reduced state and verify P remains zero.

    This tests that numerical integration preserves the momentum constraint.

    Args:
        state0: Initial translation-reduced state
        integrator: Integration function (state, masses, t_span, **kwargs) -> solution
        t_span: (t_start, t_end) time interval
        tolerance: Maximum allowed momentum drift
        **integrator_kwargs: Additional arguments for integrator

    Returns:
        Dictionary with conservation results:
            - max_momentum: Maximum ||P|| during integration
            - mean_momentum: Mean ||P|| over trajectory
            - passed: True if max_momentum < tolerance

    Example:
        >>> from integrators import ias15_integrate
        >>> reduced_state = reducer.reduce(state, masses)
        >>> result = test_momentum_conservation(
        ...     reduced_state, ias15_integrate, (0, 100), rtol=1e-12
        ... )
        >>> assert result['passed']
    """
    # Integrate
    solution = integrator(state0.state, state0.masses, t_span, **integrator_kwargs)

    # Compute momentum at all times
    reduction = TranslationReduction()
    momentum_norms = []

    for state in solution.states:
        P = reduction.momentum_map(state, state0.masses)
        momentum_norms.append(np.linalg.norm(P))

    max_momentum = max(momentum_norms)
    mean_momentum = np.mean(momentum_norms)

    return {
        'max_momentum': max_momentum,
        'mean_momentum': mean_momentum,
        'passed': max_momentum < tolerance,
        'n_timesteps': len(momentum_norms)
    }


def enforce_barycenter(
    state: CartesianState,
    masses: Masses,
    precision: str = 'double'
) -> CartesianState:
    """
    Project state onto barycentric constraint surface.

    This is a convenience function that wraps TranslationReduction.reduce()
    but returns a CartesianState directly.

    Args:
        state: Arbitrary Cartesian state
        masses: Mass parameters
        precision: 'double' or 'quad' (precision of computation)

    Returns:
        State in barycentric frame (P = 0, r_cm = 0)

    Example:
        >>> state = CartesianState(np.random.randn(3,3), np.random.randn(3,3))
        >>> masses = Masses(1.0, 1.0, 1.0)
        >>> state_bc = enforce_barycenter(state, masses)
        >>> # Verify center of mass is at origin
        >>> r_cm = np.sum(state_bc.positions * [m1, m2, m3], axis=0) / M
        >>> assert np.linalg.norm(r_cm) < 1e-14
    """
    reducer = TranslationReduction()
    reduced = reducer.reduce(state, masses)
    return reduced.state
