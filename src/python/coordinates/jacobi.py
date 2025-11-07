"""
Jacobi coordinate system for the three-body problem.

Implements hierarchical mass-weighted coordinates that decouple
center-of-mass motion from internal dynamics.
"""

from dataclasses import dataclass
from typing import Literal, Tuple
import numpy as np

from .base import CoordinateSystem, Masses, Precision
from .cartesian import (
    CartesianState,
    compute_energy,
    compute_angular_momentum,
    compute_potential_energy,
)


@dataclass(frozen=True)
class JacobiState(CoordinateSystem):
    """
    Jacobi coordinates (hierarchical mass-weighted).

    Coordinates:
        r1 = r₁ - r₂  (relative position of bodies 1-2)
        r2 = r₃ - r_cm,12  (body 3 relative to cm of 1-2)
        r_cm = barycenter position (decoupled)

    Conjugate momenta:
        p1 = μ₁₂ ṙ1
        p2 = μ₃ ṙ2
        p_cm = M ṙ_cm

    Attributes:
        r1: Relative position of bodies 1-2 (3D vector)
        r2: Position of body 3 relative to cm of 1-2 (3D vector)
        r_cm: Barycenter position (3D vector) - should be zero in barycentric frame
        p1: Conjugate momentum to r1 (mass-weighted)
        p2: Conjugate momentum to r2 (mass-weighted)
        p_cm: Conjugate momentum to r_cm (total linear momentum)
        dimension: 2 or 3
    """

    r1: np.ndarray  # shape (3,)
    r2: np.ndarray  # shape (3,)
    r_cm: np.ndarray  # shape (3,)
    p1: np.ndarray  # shape (3,)
    p2: np.ndarray  # shape (3,)
    p_cm: np.ndarray  # shape (3,)
    dimension: Literal[2, 3] = 3

    def __post_init__(self):
        """Validate array shapes"""
        for name in ["r1", "r2", "r_cm", "p1", "p2", "p_cm"]:
            arr = getattr(self, name)
            arr = np.asarray(arr)
            if arr.shape != (3,):
                raise ValueError(f"{name} must be shape (3,), got {arr.shape}")
            object.__setattr__(self, name, arr)

        if self.dimension == 2:
            # Planar: z-components should be zero
            for name in ["r1", "r2", "r_cm", "p1", "p2", "p_cm"]:
                arr = getattr(self, name)
                if not np.isclose(arr[2], 0, atol=1e-10):
                    raise ValueError(f"Planar motion requires {name}[2] = 0")

    @property
    def internal_state(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Return internal DOF only (excluding center-of-mass)"""
        return (self.r1, self.r2, self.p1, self.p2)

    def validate(self) -> bool:
        """
        Check that r_cm and p_cm are zero (barycentric frame).

        Returns:
            True if in barycentric frame
        """
        return np.linalg.norm(self.r_cm) < 1e-14 and np.linalg.norm(self.p_cm) < 1e-14

    def to_cartesian(self, masses: Masses) -> CartesianState:
        """
        Transform to Cartesian coordinates.

        Args:
            masses: Mass parameters

        Returns:
            CartesianState representation
        """
        return jacobi_to_cartesian(self, masses)

    def compute_energy(self, masses: Masses, G: float = 1.0) -> float:
        """
        Compute total energy H = H_internal + H_cm.

        Args:
            masses: Mass parameters
            G: Gravitational constant

        Returns:
            Total energy
        """
        H_internal, H_cm = compute_jacobi_hamiltonian(self, masses, G)
        return H_internal + H_cm

    def compute_angular_momentum(self, masses: Masses) -> np.ndarray:
        """
        Compute angular momentum vector.

        Args:
            masses: Mass parameters

        Returns:
            Angular momentum vector (3D)
        """
        # Convert to Cartesian and compute there
        cart_state = self.to_cartesian(masses)
        return compute_angular_momentum(cart_state, masses)


def cartesian_to_jacobi(state: CartesianState, masses: Masses) -> JacobiState:
    """
    Transform Cartesian → Jacobi coordinates.

    Transformation:
        r_J1 = r1 - r2
        r_J2 = r3 - (m1*r1 + m2*r2) / (m1 + m2)
        r_cm = (m1*r1 + m2*r2 + m3*r3) / M

        p_J1 = μ12 * (v1 - v2)
        p_J2 = μ3 * (v3 - v_cm12)
        p_cm = M * v_cm

    Args:
        state: Cartesian state
        masses: Mass parameters

    Returns:
        JacobiState representation
    """
    r = state.positions
    v = state.velocities

    m1, m2, m3 = masses.m1, masses.m2, masses.m3
    M = masses.total
    mu12 = masses.mu12
    mu3 = masses.mu3

    # Center of mass of bodies 1-2
    r_cm12 = (m1 * r[0] + m2 * r[1]) / (m1 + m2)
    v_cm12 = (m1 * v[0] + m2 * v[1]) / (m1 + m2)

    # Barycenter
    r_cm = (m1 * r[0] + m2 * r[1] + m3 * r[2]) / M
    v_cm = (m1 * v[0] + m2 * v[1] + m3 * v[2]) / M

    # Jacobi positions
    r1 = r[0] - r[1]
    r2 = r[2] - r_cm12

    # Jacobi momenta
    p1 = mu12 * (v[0] - v[1])
    p2 = mu3 * (v[2] - v_cm12)
    p_cm = M * v_cm

    return JacobiState(r1, r2, r_cm, p1, p2, p_cm, state.dimension)


def jacobi_to_cartesian(state: JacobiState, masses: Masses) -> CartesianState:
    """
    Transform Jacobi → Cartesian coordinates (inverse).

    Inverse transformation:
        r1 = r_cm12 + (m2 / (m1 + m2)) * r_J1
        r2 = r_cm12 - (m1 / (m1 + m2)) * r_J1
        r3 = r_cm12 + r_J2

    where r_cm12 = r_cm - (m3 / M) * r_J2

    Args:
        state: Jacobi state
        masses: Mass parameters

    Returns:
        CartesianState representation
    """
    m1, m2, m3 = masses.m1, masses.m2, masses.m3
    M = masses.total
    mu12 = masses.mu12
    mu3 = masses.mu3

    # Solve for r_cm12 from the constraint equations
    r_cm12 = state.r_cm - (m3 / M) * state.r2

    # Cartesian positions
    r1 = r_cm12 + (m2 / (m1 + m2)) * state.r1
    r2 = r_cm12 - (m1 / (m1 + m2)) * state.r1
    r3 = r_cm12 + state.r2

    # Velocities from momenta
    v_J1 = state.p1 / mu12
    v_J2 = state.p2 / mu3
    v_cm = state.p_cm / M

    # Solve for v_cm12
    v_cm12 = v_cm - (m3 / M) * v_J2

    # Cartesian velocities
    v1 = v_cm12 + (m2 / (m1 + m2)) * v_J1
    v2 = v_cm12 - (m1 / (m1 + m2)) * v_J1
    v3 = v_cm12 + v_J2

    positions = np.array([r1, r2, r3])
    velocities = np.array([v1, v2, v3])

    return CartesianState(positions, velocities, state.dimension)


def compute_jacobi_hamiltonian(
    state: JacobiState, masses: Masses, G: float = 1.0
) -> Tuple[float, float]:
    """
    Compute Jacobi Hamiltonian = H_internal + H_cm.

    The Hamiltonian decouples into:
        H_internal: Internal dynamics (relative motion)
        H_cm: Center-of-mass kinetic energy (decoupled)

    Args:
        state: Jacobi state
        masses: Mass parameters
        G: Gravitational constant

    Returns:
        Tuple of (H_internal, H_cm)
    """
    mu12 = masses.mu12
    mu3 = masses.mu3
    M = masses.total

    # Internal kinetic energy
    T_internal = np.linalg.norm(state.p1) ** 2 / (2 * mu12) + np.linalg.norm(
        state.p2
    ) ** 2 / (2 * mu3)

    # Center-of-mass kinetic energy (should be zero in barycentric frame)
    T_cm = np.linalg.norm(state.p_cm) ** 2 / (2 * M)

    # Potential energy (need to express in Jacobi coordinates)
    # Convert back to Cartesian distances
    cart_state = jacobi_to_cartesian(state, masses)
    V = compute_potential_energy(cart_state, masses, G)

    H_internal = T_internal + V
    H_cm = T_cm

    return H_internal, H_cm


def verify_hamiltonian_decoupling(
    state: JacobiState, masses: Masses, epsilon: float = 1e-6
) -> bool:
    """
    Verify that {H_internal, r_cm} = 0 (Poisson bracket).

    Numerical check: perturb r_cm, H_internal should not change.

    Args:
        state: Jacobi state
        masses: Mass parameters
        epsilon: Perturbation size

    Returns:
        True if decoupling verified
    """
    H0, _ = compute_jacobi_hamiltonian(state, masses)

    # Perturb center-of-mass position
    state_perturbed = JacobiState(
        state.r1,
        state.r2,
        state.r_cm + epsilon * np.array([1.0, 0.0, 0.0]),
        state.p1,
        state.p2,
        state.p_cm,
        state.dimension,
    )

    H1, _ = compute_jacobi_hamiltonian(state_perturbed, masses)

    # H_internal should be unchanged
    return abs(H1 - H0) < 1e-12


def test_jacobi_roundtrip(
    masses: Masses, n_samples: int = 100, dimension: int = 3
) -> dict:
    """
    Test Cartesian → Jacobi → Cartesian transformation accuracy.

    Args:
        masses: Mass parameters
        n_samples: Number of random samples to test
        dimension: 2 or 3

    Returns:
        Dictionary with max/mean errors
    """
    errors = []

    for _ in range(n_samples):
        # Random Cartesian state
        if dimension == 3:
            positions = np.random.randn(3, 3)
            velocities = np.random.randn(3, 3)
        else:
            positions = np.column_stack([np.random.randn(3, 2), np.zeros(3)])
            velocities = np.column_stack([np.random.randn(3, 2), np.zeros(3)])

        state_cart = CartesianState(positions, velocities, dimension)

        # Enforce barycenter
        from .cartesian import enforce_barycenter

        state_cart = enforce_barycenter(state_cart, masses)

        # Round trip
        state_jacobi = cartesian_to_jacobi(state_cart, masses)
        state_cart_reconstructed = jacobi_to_cartesian(state_jacobi, masses)

        # Compute error
        pos_error = np.linalg.norm(
            state_cart.positions - state_cart_reconstructed.positions
        )
        vel_error = np.linalg.norm(
            state_cart.velocities - state_cart_reconstructed.velocities
        )

        errors.append(max(pos_error, vel_error))

    return {
        "max_error": max(errors) if errors else 0,
        "mean_error": np.mean(errors) if errors else 0,
        "std_error": np.std(errors) if errors else 0,
    }
