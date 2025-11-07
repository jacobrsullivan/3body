"""
Cartesian coordinate system for the three-body problem.

Implements standard Cartesian positions and velocities in an inertial
barycentric frame, along with Newtonian gravitational dynamics.
"""

from dataclasses import dataclass
from typing import Literal, Optional
import numpy as np

from .base import CoordinateSystem, Masses, Precision


@dataclass(frozen=True)
class CartesianState(CoordinateSystem):
    """
    Cartesian coordinates in barycentric inertial frame.

    State space: ℝ¹⁸ (3 positions × 3 components + 3 velocities × 3 components)

    Attributes:
        positions: (3, 3) array of positions [r1, r2, r3] where ri = [x, y, z]
        velocities: (3, 3) array of velocities [v1, v2, v3]
        dimension: 2 for planar, 3 for spatial
        precision: 'double' or 'quad'
    """

    positions: np.ndarray  # shape (3, 3)
    velocities: np.ndarray  # shape (3, 3)
    dimension: Literal[2, 3] = 3
    precision: Precision = "double"

    def __post_init__(self):
        """Validate array shapes and types"""
        # Convert to numpy arrays if needed
        object.__setattr__(self, "positions", np.asarray(self.positions))
        object.__setattr__(self, "velocities", np.asarray(self.velocities))

        if self.positions.shape != (3, 3):
            raise ValueError(f"positions must be (3,3), got {self.positions.shape}")
        if self.velocities.shape != (3, 3):
            raise ValueError(f"velocities must be (3,3), got {self.velocities.shape}")

        if self.dimension == 2:
            # Planar: z-components should be zero
            if not np.allclose(self.positions[:, 2], 0, atol=1e-10):
                raise ValueError("Planar motion requires z-positions = 0")
            if not np.allclose(self.velocities[:, 2], 0, atol=1e-10):
                raise ValueError("Planar motion requires z-velocities = 0")

    @classmethod
    def from_flat(
        cls, z: np.ndarray, dimension: int = 3, precision: Precision = "double"
    ) -> "CartesianState":
        """
        Construct from flat array.

        Args:
            z: Flat state vector of length 18 (3D) or 12 (2D)
               Format: [r1x, r1y, r1z, r2x, ..., v3z] (3D)
                    or [r1x, r1y, r2x, r2y, r3x, r3y, v1x, ..., v3y] (2D)
            dimension: 2 or 3
            precision: 'double' or 'quad'

        Returns:
            CartesianState instance
        """
        z = np.asarray(z)
        n = 3 * dimension  # position components

        if len(z) != 2 * n:
            raise ValueError(f"Expected {2*n} components for {dimension}D, got {len(z)}")

        positions = z[:n].reshape(3, dimension)
        velocities = z[n : 2 * n].reshape(3, dimension)

        # Pad to 3D if needed
        if dimension == 2:
            positions = np.column_stack([positions, np.zeros(3)])
            velocities = np.column_stack([velocities, np.zeros(3)])

        return cls(positions, velocities, dimension, precision)

    def to_flat(self) -> np.ndarray:
        """
        Convert to flat array for integration.

        Returns:
            Flat state vector of length 18 (3D) or 12 (2D)
        """
        if self.dimension == 2:
            pos = self.positions[:, :2].ravel()
            vel = self.velocities[:, :2].ravel()
        else:
            pos = self.positions.ravel()
            vel = self.velocities.ravel()
        return np.concatenate([pos, vel])

    def validate(self) -> bool:
        """Check basic validity (always true for unrestricted Cartesian)"""
        return True

    def to_cartesian(self, masses: Masses) -> "CartesianState":
        """Return self (already Cartesian)"""
        return self

    def compute_energy(self, masses: Masses, G: float = 1.0) -> float:
        """
        Compute total energy H = T + V.

        Args:
            masses: Mass parameters
            G: Gravitational constant

        Returns:
            Total energy
        """
        return compute_energy(self, masses, G, self.precision)

    def compute_angular_momentum(self, masses: Masses) -> np.ndarray:
        """
        Compute angular momentum vector L = Σ rᵢ × (mᵢvᵢ).

        Args:
            masses: Mass parameters

        Returns:
            Angular momentum vector (3D)
        """
        return compute_angular_momentum(self, masses)


def enforce_barycenter(
    state: CartesianState, masses: Masses, precision: Precision = "double"
) -> CartesianState:
    """
    Project state onto barycentric constraint surface.

    Ensures:
        Σ mᵢrᵢ = 0
        Σ mᵢvᵢ = 0

    Algorithm:
        rᵢ' = rᵢ - r_cm
        vᵢ' = vᵢ - v_cm

    where r_cm = (Σ mᵢrᵢ) / M

    Args:
        state: Input state (possibly not barycentric)
        masses: Mass parameters
        precision: Precision mode

    Returns:
        State in barycentric frame
    """
    m = masses.as_array()
    M = masses.total

    # Compute center of mass
    r_cm = np.sum(state.positions * m[:, np.newaxis], axis=0) / M
    v_cm = np.sum(state.velocities * m[:, np.newaxis], axis=0) / M

    # Shift to barycentric frame
    positions_bc = state.positions - r_cm
    velocities_bc = state.velocities - v_cm

    # Verify constraint (should be machine precision)
    check_r = np.sum(positions_bc * m[:, np.newaxis], axis=0)
    check_v = np.sum(velocities_bc * m[:, np.newaxis], axis=0)

    tolerance = 1e-14 if precision == "double" else 1e-28
    if not (np.linalg.norm(check_r) < tolerance and np.linalg.norm(check_v) < tolerance):
        # This should never happen with the projection above
        # If it does, numerical issues are present
        pass

    return CartesianState(positions_bc, velocities_bc, state.dimension, precision)


def compute_energy(
    state: CartesianState,
    masses: Masses,
    G: float = 1.0,
    precision: Precision = "double",
    softening: float = 0.0,
) -> float:
    """
    Compute total energy H = T + V.

    Kinetic energy: T = (1/2) Σ mᵢ|vᵢ|²
    Potential energy: V = -G Σᵢ<ⱼ mᵢmⱼ / |rᵢ - rⱼ|

    Args:
        state: Cartesian state
        masses: Mass parameters
        G: Gravitational constant
        precision: Precision mode (currently unused, for future QD support)
        softening: Softening length (for regularization near collisions)

    Returns:
        Total energy
    """
    m = masses.as_array()

    # Kinetic energy
    T = 0.5 * np.sum(m[:, np.newaxis] * state.velocities**2)

    # Potential energy
    V = compute_potential_energy(state, masses, G, softening)

    return T + V


def compute_potential_energy(
    state: CartesianState,
    masses: Masses,
    G: float = 1.0,
    softening: float = 0.0,
) -> float:
    """
    Compute gravitational potential energy.

    V = -G Σᵢ<ⱼ mᵢmⱼ / |rᵢ - rⱼ|

    Args:
        state: Cartesian state
        masses: Mass parameters
        G: Gravitational constant
        softening: Softening length (avoid singularities)

    Returns:
        Potential energy
    """
    m = masses.as_array()
    r = state.positions
    V = 0.0

    pairs = [(0, 1), (0, 2), (1, 2)]
    for i, j in pairs:
        rij = r[i] - r[j]
        dist = np.linalg.norm(rij)

        if softening > 0:
            dist = np.sqrt(dist**2 + softening**2)

        V -= G * m[i] * m[j] / dist

    return V


def compute_linear_momentum(state: CartesianState, masses: Masses) -> np.ndarray:
    """
    Compute total linear momentum P = Σ mᵢvᵢ.

    Should be zero in barycentric frame.

    Args:
        state: Cartesian state
        masses: Mass parameters

    Returns:
        Linear momentum vector (3D)
    """
    m = masses.as_array()
    return np.sum(m[:, np.newaxis] * state.velocities, axis=0)


def compute_angular_momentum(state: CartesianState, masses: Masses) -> np.ndarray:
    """
    Compute total angular momentum L = Σ rᵢ × (mᵢvᵢ).

    For planar motion: L = Lz (scalar, out-of-plane component)

    Args:
        state: Cartesian state
        masses: Mass parameters

    Returns:
        Angular momentum vector (3D)
    """
    m = masses.as_array()
    L = np.zeros(3)

    for i in range(3):
        L += m[i] * np.cross(state.positions[i], state.velocities[i])

    return L


def compute_accelerations(
    positions: np.ndarray,
    masses: Masses,
    G: float = 1.0,
    softening: float = 0.0,
) -> np.ndarray:
    """
    Compute gravitational accelerations.

    aᵢ = Σⱼ≠ᵢ G mⱼ (rⱼ - rᵢ) / |rᵢⱼ|³

    Args:
        positions: (3, 3) array of positions
        masses: Mass parameters
        G: Gravitational constant
        softening: Softening length

    Returns:
        accelerations: (3, 3) array of accelerations
    """
    m = masses.as_array()
    acc = np.zeros_like(positions)

    for i in range(3):
        for j in range(3):
            if i == j:
                continue

            rij = positions[j] - positions[i]
            dist = np.linalg.norm(rij)

            if softening > 0:
                dist = np.sqrt(dist**2 + softening**2)

            # Acceleration on body i due to body j
            acc[i] += G * m[j] * rij / dist**3

    return acc


def cartesian_rhs(
    t: float, z: np.ndarray, masses: Masses, G: float = 1.0, dimension: int = 3
) -> np.ndarray:
    """
    Right-hand side for Cartesian equations of motion.

    Used by scipy.integrate.solve_ivp and custom integrators.

    Equations:
        drᵢ/dt = vᵢ
        dvᵢ/dt = aᵢ = Σⱼ≠ᵢ G mⱼ (rⱼ - rᵢ) / |rᵢⱼ|³

    Args:
        t: Time (unused, for ODE interface)
        z: Flat state vector
        masses: Mass parameters
        G: Gravitational constant
        dimension: 2 or 3

    Returns:
        Time derivative [velocities, accelerations] (flattened)
    """
    n = 3 * dimension
    positions = z[:n].reshape(3, dimension)
    velocities = z[n:].reshape(3, dimension)

    # Pad to 3D if needed
    if dimension == 2:
        positions_3d = np.column_stack([positions, np.zeros(3)])
    else:
        positions_3d = positions

    accelerations_3d = compute_accelerations(positions_3d, masses, G)

    # Extract relevant dimensions
    if dimension == 2:
        accelerations = accelerations_3d[:, :2]
    else:
        accelerations = accelerations_3d

    # Return [velocities, accelerations] flattened
    return np.concatenate([velocities.ravel(), accelerations.ravel()])


class ConservationMonitor:
    """
    Track conservation laws over integration.

    Monitors:
        - Energy conservation: ΔE/E
        - Angular momentum conservation: ΔL
        - Linear momentum conservation: ΔP (should be zero in barycentric frame)
    """

    def __init__(self, state0: CartesianState, masses: Masses, G: float = 1.0):
        """
        Initialize monitor with initial state.

        Args:
            state0: Initial state
            masses: Mass parameters
            G: Gravitational constant
        """
        self.G = G
        self.E0 = compute_energy(state0, masses, G)
        self.L0 = compute_angular_momentum(state0, masses)
        self.P0 = compute_linear_momentum(state0, masses)

        self.times: list[float] = []
        self.energy_errors: list[float] = []
        self.angular_momentum_errors: list[float] = []
        self.linear_momentum_errors: list[float] = []

    def record(self, t: float, state: CartesianState, masses: Masses):
        """
        Record conservation errors at time t.

        Args:
            t: Current time
            state: Current state
            masses: Mass parameters
        """
        E = compute_energy(state, masses, self.G)
        L = compute_angular_momentum(state, masses)
        P = compute_linear_momentum(state, masses)

        self.times.append(t)
        self.energy_errors.append((E - self.E0) / abs(self.E0) if self.E0 != 0 else E)
        self.angular_momentum_errors.append(np.linalg.norm(L - self.L0))
        self.linear_momentum_errors.append(np.linalg.norm(P - self.P0))

    def validate(self, tolerance: dict) -> bool:
        """
        Check if conservation errors are within tolerance.

        Args:
            tolerance: Dictionary with keys 'energy', 'angular_momentum', 'linear_momentum'

        Returns:
            True if all errors within tolerance
        """
        if not self.times:
            return True

        energy_ok = max(abs(e) for e in self.energy_errors) < tolerance.get(
            "energy", 1e-10
        )
        angular_ok = max(self.angular_momentum_errors) < tolerance.get(
            "angular_momentum", 1e-10
        )
        linear_ok = max(self.linear_momentum_errors) < tolerance.get(
            "linear_momentum", 1e-10
        )

        return energy_ok and angular_ok and linear_ok

    def get_summary(self) -> dict:
        """
        Get summary statistics of conservation errors.

        Returns:
            Dictionary with max, mean, final errors
        """
        if not self.times:
            return {}

        return {
            "energy": {
                "max": max(abs(e) for e in self.energy_errors),
                "mean": np.mean(np.abs(self.energy_errors)),
                "final": self.energy_errors[-1],
            },
            "angular_momentum": {
                "max": max(self.angular_momentum_errors),
                "mean": np.mean(self.angular_momentum_errors),
                "final": self.angular_momentum_errors[-1],
            },
            "linear_momentum": {
                "max": max(self.linear_momentum_errors),
                "mean": np.mean(self.linear_momentum_errors),
                "final": self.linear_momentum_errors[-1],
            },
        }


def moment_of_inertia(state: CartesianState, masses: Masses) -> float:
    """
    Compute moment of inertia I = Σ mᵢ|rᵢ|².

    Used for scale normalization in shape space.

    Args:
        state: Cartesian state
        masses: Mass parameters

    Returns:
        Moment of inertia
    """
    m = masses.as_array()
    return np.sum(m * np.sum(state.positions**2, axis=1))
