"""
Locked inertia tensor for the three-body problem.

The locked inertia tensor is the moment of inertia when shape is held fixed.
It is a key component in computing the mechanical connection.

Mathematical Definition:
    I_locked = Σ mᵢ (|rᵢ|² Id - rᵢ ⊗ rᵢ)

Physical Interpretation:
    This is the inertia tensor in the body frame (relative to barycenter).
    It measures the resistance to rotation at fixed shape.
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np

from ..coordinates.base import Masses
from ..coordinates.cartesian import CartesianState


@dataclass(frozen=True)
class LockedInertiaTensor:
    """
    Locked inertia tensor at a configuration.

    Attributes:
        tensor: 3×3 symmetric positive-definite matrix
        eigenvalues: Principal moments of inertia
        eigenvectors: Principal axes
        trace: Tr(I) = Σ mᵢ|rᵢ|²
        determinant: det(I)
    """

    tensor: np.ndarray  # 3×3 matrix
    eigenvalues: Optional[np.ndarray] = None
    eigenvectors: Optional[np.ndarray] = None

    def __post_init__(self):
        """Compute eigendecomposition if not provided"""
        if self.eigenvalues is None or self.eigenvectors is None:
            eigenvalues, eigenvectors = np.linalg.eigh(self.tensor)
            object.__setattr__(self, "eigenvalues", eigenvalues)
            object.__setattr__(self, "eigenvectors", eigenvectors)

    @property
    def trace(self) -> float:
        """Trace of inertia tensor"""
        return np.trace(self.tensor)

    @property
    def determinant(self) -> float:
        """Determinant of inertia tensor"""
        return np.linalg.det(self.tensor)

    def inverse(self) -> np.ndarray:
        """
        Compute inverse inertia tensor.

        Returns:
            I^{-1} (3×3 matrix)
        """
        return np.linalg.inv(self.tensor)

    def is_positive_definite(self, tolerance: float = 1e-14) -> bool:
        """
        Check if tensor is positive definite.

        Returns:
            True if all eigenvalues > tolerance
        """
        return np.all(self.eigenvalues > tolerance)


def compute_locked_inertia_tensor(
    state: CartesianState,
    masses: Masses,
    compute_eigen: bool = True
) -> LockedInertiaTensor:
    """
    Compute locked inertia tensor I = Σ mᵢ (|rᵢ|² Id - rᵢ ⊗ rᵢ).

    This is the inertia tensor in the body frame (barycentric coordinates).

    Args:
        state: Cartesian state (should be in barycentric frame)
        masses: Mass parameters
        compute_eigen: Whether to compute eigendecomposition

    Returns:
        LockedInertiaTensor object

    Notes:
        - State must be in barycentric frame (Σ mᵢrᵢ = 0)
        - Tensor is symmetric and positive semi-definite
        - For non-collinear configurations, tensor is positive definite

    Example:
        >>> masses = Masses(1.0, 1.0, 1.0)
        >>> positions = np.array([[1, 0, 0], [-0.5, 0.866, 0], [-0.5, -0.866, 0]])
        >>> velocities = np.zeros((3, 3))
        >>> state = CartesianState(positions, velocities)
        >>> I = compute_locked_inertia_tensor(state, masses)
        >>> print(I.tensor)
    """
    m = masses.as_array()
    r = state.positions
    I = np.zeros((3, 3))

    for i in range(3):
        r_i = r[i]
        r_squared = np.dot(r_i, r_i)

        # I += mᵢ (|rᵢ|² Id - rᵢ ⊗ rᵢ)
        I += m[i] * (r_squared * np.eye(3) - np.outer(r_i, r_i))

    if compute_eigen:
        eigenvalues, eigenvectors = np.linalg.eigh(I)
        return LockedInertiaTensor(I, eigenvalues, eigenvectors)
    else:
        return LockedInertiaTensor(I)


def compute_angular_velocity_from_shape_change(
    state: CartesianState,
    masses: Masses,
    shape_velocity: np.ndarray,
    L_magnitude: float = 0.0
) -> np.ndarray:
    """
    Compute angular velocity induced by shape change at constant angular momentum.

    When the shape changes (e.g., one side lengthens), the system must rotate
    to conserve angular momentum. This function computes the induced ω.

    Mathematical Formula:
        I_locked · ω = ∂L/∂q · dq/dt

    where q are shape coordinates and dq/dt is the shape velocity.

    Args:
        state: Current Cartesian state
        masses: Mass parameters
        shape_velocity: Velocity in shape space (dr12/dt, dr23/dt, dr31/dt)
        L_magnitude: Total angular momentum magnitude

    Returns:
        ω: Angular velocity vector (3D)

    Notes:
        This is a simplified implementation. Full version requires computing
        ∂L/∂q numerically or analytically.
    """
    # Compute locked inertia tensor
    I_locked = compute_locked_inertia_tensor(state, masses)

    # TODO: Implement full computation of ∂L/∂q
    # For now, return zero as placeholder
    omega = np.zeros(3)

    return omega


def compute_moment_of_inertia_planar(
    state: CartesianState,
    masses: Masses
) -> float:
    """
    Compute planar moment of inertia I = Σ mᵢ|rᵢ|².

    This is Tr(I_locked)/2 for planar motion.

    Args:
        state: Cartesian state (planar)
        masses: Mass parameters

    Returns:
        I: Moment of inertia (scalar)
    """
    m = masses.as_array()
    r = state.positions

    I = 0.0
    for i in range(3):
        I += m[i] * np.dot(r[i], r[i])

    return I


def validate_inertia_tensor_properties(
    I: LockedInertiaTensor,
    tolerance: float = 1e-14
) -> dict:
    """
    Validate mathematical properties of inertia tensor.

    Checks:
        1. Symmetry: I = I^T
        2. Positive definiteness: all eigenvalues > 0
        3. Perpendicular eigenvectors: eigenvectors are orthonormal

    Args:
        I: Locked inertia tensor
        tolerance: Numerical tolerance

    Returns:
        Dictionary with validation results
    """
    results = {}

    # Check symmetry
    symmetry_error = np.linalg.norm(I.tensor - I.tensor.T)
    results['symmetric'] = symmetry_error < tolerance
    results['symmetry_error'] = symmetry_error

    # Check positive definiteness
    results['positive_definite'] = I.is_positive_definite(tolerance)
    results['min_eigenvalue'] = np.min(I.eigenvalues)

    # Check orthonormality of eigenvectors
    V = I.eigenvectors
    should_be_identity = V.T @ V
    orthonormality_error = np.linalg.norm(should_be_identity - np.eye(3))
    results['eigenvectors_orthonormal'] = orthonormality_error < tolerance
    results['orthonormality_error'] = orthonormality_error

    # Overall validity
    results['valid'] = (
        results['symmetric'] and
        results['positive_definite'] and
        results['eigenvectors_orthonormal']
    )

    return results
