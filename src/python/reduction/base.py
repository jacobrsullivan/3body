"""
Abstract base classes for symplectic reduction.

Defines the interface for reduction operations on Hamiltonian systems.
"""

from abc import ABC, abstractmethod
from typing import Any
import numpy as np

from ..coordinates.cartesian import CartesianState
from ..coordinates.base import Masses


class SymplecticReduction(ABC):
    """
    Abstract base class for symplectic reduction operations.

    A symplectic reduction removes symmetries from a Hamiltonian system
    while preserving the symplectic structure. This is formalized by the
    Marsden-Weinstein reduction theorem.

    Key concepts:
        - Momentum map: μ: M → g* (maps phase space to dual of Lie algebra)
        - Level set: μ⁻¹(c) (states with fixed momentum value)
        - Quotient: M_c = μ⁻¹(c) / G (reduced phase space)

    Subclasses implement specific reductions:
        - TranslationReduction: G = ℝ³ (remove center-of-mass motion)
        - RotationReduction: G = SO(3) (remove rotational motion)
    """

    @abstractmethod
    def momentum_map(self, state: CartesianState, masses: Masses) -> np.ndarray:
        """
        Compute the momentum map value for given state.

        The momentum map is the Noether charge associated with the symmetry.

        Args:
            state: Cartesian state
            masses: Mass parameters

        Returns:
            Momentum map value (element of g*)

        Examples:
            - Translation: momentum_map returns total linear momentum P
            - Rotation: momentum_map returns total angular momentum L
        """
        pass

    @abstractmethod
    def reduce(self, state: CartesianState, masses: Masses) -> Any:
        """
        Perform symplectic reduction on the given state.

        This projects the state onto the constraint surface and fixes
        a gauge (representative of the orbit).

        Args:
            state: Arbitrary Cartesian state
            masses: Mass parameters

        Returns:
            Reduced state (specific type depends on reduction)
        """
        pass

    @abstractmethod
    def validate_constraint(
        self,
        state: CartesianState,
        masses: Masses,
        tolerance: float = 1e-14
    ) -> bool:
        """
        Check if state satisfies the momentum constraint.

        Args:
            state: State to validate
            masses: Mass parameters
            tolerance: Numerical tolerance

        Returns:
            True if constraint is satisfied within tolerance
        """
        pass

    def is_symmetry(
        self,
        state: CartesianState,
        masses: Masses,
        hamiltonian_func,
        epsilon: float = 1e-6,
        tolerance: float = 1e-12
    ) -> bool:
        """
        Verify that the group action is a symmetry of the Hamiltonian.

        Test: Apply group action, check if H changes.

        Args:
            state: Test state
            masses: Mass parameters
            hamiltonian_func: Function computing H(state, masses)
            epsilon: Size of group action parameter
            tolerance: Tolerance for energy difference

        Returns:
            True if H is preserved under group action
        """
        # Compute initial energy
        H0 = hamiltonian_func(state, masses)

        # Apply small group action (implementation-specific)
        state_transformed = self._apply_group_action(state, epsilon)

        # Compute transformed energy
        H1 = hamiltonian_func(state_transformed, masses)

        # Check if energy is preserved
        return abs(H1 - H0) < tolerance

    @abstractmethod
    def _apply_group_action(self, state: CartesianState, epsilon: float) -> CartesianState:
        """
        Apply an infinitesimal group action (for testing).

        Args:
            state: Current state
            epsilon: Size of infinitesimal transformation

        Returns:
            Transformed state
        """
        pass
