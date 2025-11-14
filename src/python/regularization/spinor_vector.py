"""
Spinor vector dataclass for KS regularization.

A spinor is a 4D vector u = (u₀, u₁, u₂, u₃) ∈ ℝ⁴ that represents
a 3D position through the bilinear KS transformation.
"""

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class SpinorVector:
    """
    4D spinor representing 3D vector via KS transform.

    Attributes:
        components: (u₀, u₁, u₂, u₃) ∈ ℝ⁴

    Properties:
        - norm_squared: ‖u‖² = Σ uᵢ²
        - radius: r = ‖u‖² (bilinear relation)
    """

    components: np.ndarray  # Shape (4,)

    def __post_init__(self):
        """Validate spinor is 4D"""
        components = np.asarray(self.components)
        if components.shape != (4,):
            raise ValueError(f"Spinor must be 4D, got shape {components.shape}")
        object.__setattr__(self, "components", components)

    @property
    def u0(self) -> float:
        """First component"""
        return self.components[0]

    @property
    def u1(self) -> float:
        """Second component"""
        return self.components[1]

    @property
    def u2(self) -> float:
        """Third component"""
        return self.components[2]

    @property
    def u3(self) -> float:
        """Fourth component"""
        return self.components[3]

    @property
    def norm_squared(self) -> float:
        """‖u‖² = u₀² + u₁² + u₂² + u₃²"""
        return np.dot(self.components, self.components)

    @property
    def norm(self) -> float:
        """‖u‖"""
        return np.sqrt(self.norm_squared)

    @property
    def radius(self) -> float:
        """
        Radius corresponding to this spinor: r = ‖u‖².

        This is the bilinear relation for KS transform.
        """
        return self.norm_squared

    def to_array(self) -> np.ndarray:
        """Convert to numpy array"""
        return self.components.copy()

    def __add__(self, other: "SpinorVector") -> "SpinorVector":
        """Add two spinors"""
        return SpinorVector(self.components + other.components)

    def __sub__(self, other: "SpinorVector") -> "SpinorVector":
        """Subtract two spinors"""
        return SpinorVector(self.components - other.components)

    def __mul__(self, scalar: float) -> "SpinorVector":
        """Scalar multiplication"""
        return SpinorVector(scalar * self.components)

    def __rmul__(self, scalar: float) -> "SpinorVector":
        """Right scalar multiplication"""
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> "SpinorVector":
        """Scalar division"""
        return SpinorVector(self.components / scalar)

    def dot(self, other: "SpinorVector") -> float:
        """Inner product ⟨u, v⟩"""
        return np.dot(self.components, other.components)


def create_spinor(u0: float, u1: float, u2: float, u3: float) -> SpinorVector:
    """
    Create spinor from individual components.

    Args:
        u0, u1, u2, u3: Components

    Returns:
        SpinorVector
    """
    return SpinorVector(np.array([u0, u1, u2, u3]))


def spinor_from_array(arr: np.ndarray) -> SpinorVector:
    """
    Create spinor from numpy array.

    Args:
        arr: Array of length 4

    Returns:
        SpinorVector
    """
    return SpinorVector(arr)


def zero_spinor() -> SpinorVector:
    """Return zero spinor (0, 0, 0, 0)"""
    return SpinorVector(np.zeros(4))


def spinor_norm_squared(spinor: SpinorVector) -> float:
    """Compute ‖u‖²"""
    return spinor.norm_squared


def spinor_norm(spinor: SpinorVector) -> float:
    """Compute ‖u‖"""
    return spinor.norm
