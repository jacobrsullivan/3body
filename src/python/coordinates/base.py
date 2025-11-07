"""
Base classes and type definitions for coordinate systems.

Defines the abstract interface that all coordinate systems must implement,
along with shared type definitions and the Masses container.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, TypeAlias
import numpy as np

# Type aliases
Precision: TypeAlias = Literal["double", "quad"]


@dataclass(frozen=True)
class Masses:
    """
    Three-body mass parameters.

    Attributes:
        m1: Mass of body 1
        m2: Mass of body 2
        m3: Mass of body 3

    Properties:
        total: Total mass M = m1 + m2 + m3
        mu12: Reduced mass of bodies 1-2
        mu3: Hierarchical reduced mass for body 3
    """

    m1: float
    m2: float
    m3: float

    def __post_init__(self):
        """Validate masses are positive"""
        if self.m1 <= 0 or self.m2 <= 0 or self.m3 <= 0:
            raise ValueError("All masses must be positive")

    @property
    def total(self) -> float:
        """Total mass M = m1 + m2 + m3"""
        return self.m1 + self.m2 + self.m3

    @property
    def mu12(self) -> float:
        """Reduced mass of bodies 1-2: μ₁₂ = m₁m₂/(m₁+m₂)"""
        return self.m1 * self.m2 / (self.m1 + self.m2)

    @property
    def mu3(self) -> float:
        """Hierarchical reduced mass: μ₃ = (m₁+m₂)m₃/M"""
        return (self.m1 + self.m2) * self.m3 / self.total

    @property
    def mu23(self) -> float:
        """Reduced mass of bodies 2-3: μ₂₃ = m₂m₃/(m₂+m₃)"""
        return self.m2 * self.m3 / (self.m2 + self.m3)

    @property
    def mu13(self) -> float:
        """Reduced mass of bodies 1-3: μ₁₃ = m₁m₃/(m₁+m₃)"""
        return self.m1 * self.m3 / (self.m1 + self.m3)

    def as_array(self) -> np.ndarray:
        """Return masses as numpy array [m1, m2, m3]"""
        return np.array([self.m1, self.m2, self.m3])

    @classmethod
    def equal_masses(cls, m: float = 1.0) -> "Masses":
        """Create equal mass configuration"""
        return cls(m, m, m)

    @classmethod
    def hierarchical(cls, m_large: float, m_small: float) -> "Masses":
        """
        Create hierarchical mass configuration (Sun-Jupiter-asteroid like).

        Args:
            m_large: Mass of the large body (e.g., Sun)
            m_small: Mass of the smaller bodies (e.g., planet and asteroid)

        Returns:
            Masses(m_large, m_small, m_small/1000)
        """
        return cls(m_large, m_small, m_small / 1000)


class CoordinateSystem(ABC):
    """
    Abstract base class for three-body coordinate representations.

    All coordinate systems must implement methods for:
    - Validation of coordinate constraints
    - Conversion to Cartesian coordinates
    - Computation of physical quantities (energy, angular momentum)
    """

    @abstractmethod
    def validate(self) -> bool:
        """
        Check if state satisfies coordinate system constraints.

        Returns:
            True if all constraints are satisfied
        """
        pass

    @abstractmethod
    def to_cartesian(self, masses: Masses) -> "CartesianState":
        """
        Transform to Cartesian coordinates.

        Args:
            masses: Mass parameters

        Returns:
            CartesianState representation
        """
        pass

    @abstractmethod
    def compute_energy(self, masses: Masses, G: float = 1.0) -> float:
        """
        Compute total energy in this coordinate system.

        Args:
            masses: Mass parameters
            G: Gravitational constant (default: 1.0)

        Returns:
            Total energy H = T + V
        """
        pass

    @abstractmethod
    def compute_angular_momentum(self, masses: Masses) -> np.ndarray:
        """
        Compute angular momentum vector.

        Args:
            masses: Mass parameters

        Returns:
            Angular momentum vector L (3D)
        """
        pass


# Forward declaration for type hints
# Actual implementation in cartesian.py
class CartesianState(CoordinateSystem):
    """Cartesian coordinate system (implemented in cartesian.py)"""

    pass
