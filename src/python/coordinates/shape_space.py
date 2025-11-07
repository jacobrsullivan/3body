"""
Shape space coordinate system for the three-body problem.

Implements coordinates on the quotient space obtained by removing
translations and rotations.
"""

from dataclasses import dataclass
from typing import Literal, Optional, Tuple
import numpy as np

from .base import CoordinateSystem, Masses
from .cartesian import CartesianState, compute_angular_momentum


@dataclass(frozen=True)
class ShapeSpaceState(CoordinateSystem):
    """
    Shape space coordinates (quotient by translations and rotations).

    Primary representation: relative distances (r12, r23, r31)

    Attributes:
        r12: Distance between bodies 1-2
        r23: Distance between bodies 2-3
        r31: Distance between bodies 3-1
        dr12_dt: Time derivative of r12
        dr23_dt: Time derivative of r23
        dr31_dt: Time derivative of r31
        L: Angular momentum (conserved, labels the reduced space)
        theta: Orientation angle (optional, for SO(2) if not fully reduced)
        dtheta_dt: Angular velocity (optional)
        dimension: 2 or 3
    """

    r12: float
    r23: float
    r31: float
    dr12_dt: float
    dr23_dt: float
    dr31_dt: float
    L: float
    theta: Optional[float] = None
    dtheta_dt: Optional[float] = None
    dimension: Literal[2, 3] = 2

    def validate(self) -> bool:
        """Check triangle inequality"""
        return (
            self.r12 + self.r23 >= self.r31
            and self.r23 + self.r31 >= self.r12
            and self.r31 + self.r12 >= self.r23
        )

    def to_cartesian(self, masses: Masses) -> CartesianState:
        """
        Transform to Cartesian coordinates (canonical orientation).

        Note: This is ambiguous - we fix overall translation and rotation.

        Args:
            masses: Mass parameters

        Returns:
            CartesianState in canonical form
        """
        return shape_distances_to_cartesian_canonical(self, masses)

    def compute_energy(self, masses: Masses, G: float = 1.0) -> float:
        """
        Compute energy (requires conversion to Cartesian).

        Args:
            masses: Mass parameters
            G: Gravitational constant

        Returns:
            Total energy (Note: kinetic part incomplete without full velocity info)
        """
        from .cartesian import compute_energy

        cart_state = self.to_cartesian(masses)
        return compute_energy(cart_state, masses, G)

    def compute_angular_momentum(self, masses: Masses) -> np.ndarray:
        """
        Return angular momentum vector.

        Args:
            masses: Mass parameters

        Returns:
            Angular momentum vector (for planar: [0, 0, L])
        """
        if self.dimension == 2:
            return np.array([0.0, 0.0, self.L])
        else:
            # For 3D, need more information
            cart_state = self.to_cartesian(masses)
            return compute_angular_momentum(cart_state, masses)

    @property
    def perimeter(self) -> float:
        """Total perimeter of triangle"""
        return self.r12 + self.r23 + self.r31

    @property
    def area(self) -> float:
        """
        Area of triangle (Heron's formula).

        Returns:
            Area (0 for degenerate triangles)
        """
        s = self.perimeter / 2
        arg = s * (s - self.r12) * (s - self.r23) * (s - self.r31)
        return np.sqrt(max(0, arg))  # Avoid numerical issues


@dataclass(frozen=True)
class ComplexShapeState(CoordinateSystem):
    """
    Complex shape variable for planar 3BP.

    Definition: z = (r3 - r1) / (r2 - r1) ∈ ℂ

    Properties:
        - Im(z) > 0: positive orientation
        - |z| related to distance ratios
        - arg(z) related to angles

    Attributes:
        z: Complex shape variable
        z_dot: Time derivative
        L: Angular momentum
    """

    z: complex
    z_dot: complex
    L: float

    def validate(self) -> bool:
        """Check that Im(z) > 0 (positive orientation)"""
        return np.imag(self.z) > 0

    def to_cartesian(self, masses: Masses) -> CartesianState:
        """
        Transform to Cartesian coordinates.

        Note: Scale is ambiguous in shape space.

        Args:
            masses: Mass parameters

        Returns:
            CartesianState (with arbitrary scale)
        """
        # Use unit scale for simplicity
        return complex_shape_to_cartesian_canonical(self, masses, scale=1.0)

    def compute_energy(self, masses: Masses, G: float = 1.0) -> float:
        """Compute energy (requires Cartesian conversion)"""
        from .cartesian import compute_energy

        cart_state = self.to_cartesian(masses)
        return compute_energy(cart_state, masses, G)

    def compute_angular_momentum(self, masses: Masses) -> np.ndarray:
        """Return angular momentum vector [0, 0, L]"""
        return np.array([0.0, 0.0, self.L])

    def to_distances(self, scale: float = 1.0) -> Tuple[float, float, float]:
        """
        Convert to relative distances (r12, r23, r31).

        Args:
            scale: Overall scale (ambiguous in shape space)

        Returns:
            Tuple of (r12, r23, r31)
        """
        r12 = scale
        r13 = scale * abs(self.z)
        r23 = scale * abs(self.z - 1)
        return (r12, r23, r13)


def cartesian_to_shape_distances(
    state: CartesianState, masses: Masses
) -> ShapeSpaceState:
    """
    Transform Cartesian → Shape Space (distance representation).

    Computes:
        r_ij = |rᵢ - rⱼ|
        dr_ij/dt = (rᵢⱼ · vᵢⱼ) / |rᵢⱼ|

    where vᵢⱼ = vᵢ - vⱼ

    Args:
        state: Cartesian state
        masses: Mass parameters

    Returns:
        ShapeSpaceState representation
    """
    r = state.positions
    v = state.velocities

    # Compute relative position vectors
    r12_vec = r[0] - r[1]
    r23_vec = r[1] - r[2]
    r31_vec = r[2] - r[0]

    # Compute distances
    r12 = np.linalg.norm(r12_vec)
    r23 = np.linalg.norm(r23_vec)
    r31 = np.linalg.norm(r31_vec)

    # Compute relative velocity vectors
    v12_vec = v[0] - v[1]
    v23_vec = v[1] - v[2]
    v31_vec = v[2] - v[0]

    # Compute distance velocities: dr/dt = (r · v) / |r|
    dr12_dt = np.dot(r12_vec, v12_vec) / r12 if r12 > 1e-15 else 0.0
    dr23_dt = np.dot(r23_vec, v23_vec) / r23 if r23 > 1e-15 else 0.0
    dr31_dt = np.dot(r31_vec, v31_vec) / r31 if r31 > 1e-15 else 0.0

    # Compute angular momentum
    L_vec = compute_angular_momentum(state, masses)
    L_z = L_vec[2] if state.dimension == 2 else np.linalg.norm(L_vec)

    return ShapeSpaceState(
        r12, r23, r31, dr12_dt, dr23_dt, dr31_dt, L_z, dimension=state.dimension
    )


def cartesian_to_complex_shape(
    state: CartesianState, masses: Masses
) -> ComplexShapeState:
    """
    Transform Cartesian → Complex shape variable (planar only).

    Definition:
        z = (r3 - r1) / (r2 - r1)

    Args:
        state: Cartesian state (must be planar, dimension=2)
        masses: Mass parameters

    Returns:
        ComplexShapeState representation

    Raises:
        ValueError: If not planar motion
    """
    if state.dimension != 2:
        raise ValueError("Complex shape only defined for planar motion")

    r = state.positions[:, :2]  # Extract x, y components
    v = state.velocities[:, :2]

    # Complex positions
    z1 = r[0, 0] + 1j * r[0, 1]
    z2 = r[1, 0] + 1j * r[1, 1]
    z3 = r[2, 0] + 1j * r[2, 1]

    # Complex velocities
    v1 = v[0, 0] + 1j * v[0, 1]
    v2 = v[1, 0] + 1j * v[1, 1]
    v3 = v[2, 0] + 1j * v[2, 1]

    # Shape variable
    denominator = z2 - z1
    if abs(denominator) < 1e-15:
        raise ValueError("Bodies 1 and 2 are too close for complex shape")

    z_shape = (z3 - z1) / denominator

    # Time derivative (quotient rule)
    numerator_dot = v3 - v1
    denominator_dot = v2 - v1

    z_shape_dot = (numerator_dot * denominator - (z3 - z1) * denominator_dot) / (
        denominator**2
    )

    # Angular momentum
    L_vec = compute_angular_momentum(state, masses)
    L_z = L_vec[2]

    return ComplexShapeState(z_shape, z_shape_dot, L_z)


def compute_canonical_orientation(
    state: CartesianState, method: str = "align_axis"
) -> Tuple[CartesianState, float]:
    """
    Rotate state to canonical orientation.

    Methods:
        - 'align_axis': Align body 1-2 axis with x-axis

    Args:
        state: Cartesian state
        method: Orientation method

    Returns:
        Tuple of (state_canonical, theta) where theta is rotation angle applied

    Raises:
        NotImplementedError: If method not supported
    """
    if method == "align_axis":
        # Rotate so that r1-r2 lies along x-axis
        r12_vec = state.positions[0] - state.positions[1]
        r12_vec_2d = r12_vec[:2]  # x, y components

        # Current angle
        theta = np.arctan2(r12_vec_2d[1], r12_vec_2d[0])

        # Rotation matrix (about z-axis, negative angle to align with x)
        c, s = np.cos(-theta), np.sin(-theta)
        R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

        # Apply rotation
        positions_rot = state.positions @ R.T
        velocities_rot = state.velocities @ R.T

        return CartesianState(positions_rot, velocities_rot, state.dimension), theta

    else:
        raise NotImplementedError(f"Method {method} not implemented")


def shape_distances_to_cartesian_canonical(
    shape_state: ShapeSpaceState, masses: Masses
) -> CartesianState:
    """
    Reconstruct Cartesian state from shape distances (canonical orientation).

    Canonical form:
        - Body 1 at origin
        - Body 2 on positive x-axis at distance r12
        - Body 3 in xy-plane with positive y-coordinate

    Note: Velocities are incomplete (only radial components available)

    Args:
        shape_state: Shape space state
        masses: Mass parameters

    Returns:
        CartesianState (positions complete, velocities approximate)
    """
    r12, r23, r31 = shape_state.r12, shape_state.r23, shape_state.r31

    # Body 1 at origin
    r1 = np.array([0.0, 0.0, 0.0])

    # Body 2 on x-axis
    r2 = np.array([r12, 0.0, 0.0])

    # Body 3: solve triangle using law of cosines
    # r31² = x3² + y3²
    # r23² = (x3 - r12)² + y3²
    # Solving: x3 = (r31² - r23² + r12²) / (2 * r12)
    x3 = (r31**2 - r23**2 + r12**2) / (2 * r12)
    y3_squared = r31**2 - x3**2

    if y3_squared < 0:
        # Degenerate triangle (numerical issues)
        y3 = 0.0
    else:
        y3 = np.sqrt(y3_squared)

    r3 = np.array([x3, y3, 0.0])

    positions = np.array([r1, r2, r3])

    # Enforce barycenter
    m = masses.as_array()
    M = masses.total
    r_cm = np.sum(positions * m[:, np.newaxis], axis=0) / M
    positions = positions - r_cm

    # Velocities: construct from distance velocities
    # This is a complex linear system - simplified approach here
    # For full reconstruction, need to solve constraints
    velocities = np.zeros((3, 3))

    # Approximate velocities from radial components
    # (This is incomplete - full solution requires solving for tangential components)
    # For now, set to zero (position-only reconstruction)

    return CartesianState(positions, velocities, dimension=2)


def complex_shape_to_cartesian_canonical(
    shape_state: ComplexShapeState, masses: Masses, scale: float = 1.0
) -> CartesianState:
    """
    Reconstruct Cartesian state from complex shape variable.

    Canonical form:
        - Body 1 at origin
        - Body 2 at (scale, 0)
        - Body 3 at scale * z

    Args:
        shape_state: Complex shape state
        masses: Mass parameters
        scale: Overall scale (default: 1.0)

    Returns:
        CartesianState (positions only, velocities approximate)
    """
    z = shape_state.z

    # Positions in canonical form
    r1 = np.array([0.0, 0.0, 0.0])
    r2 = np.array([scale, 0.0, 0.0])
    r3 = np.array([scale * np.real(z), scale * np.imag(z), 0.0])

    positions = np.array([r1, r2, r3])

    # Enforce barycenter
    m = masses.as_array()
    M = masses.total
    r_cm = np.sum(positions * m[:, np.newaxis], axis=0) / M
    positions = positions - r_cm

    # Velocities: approximate from z_dot
    # (Incomplete - full reconstruction requires more information)
    velocities = np.zeros((3, 3))

    return CartesianState(positions, velocities, dimension=2)


def oriented_triangle_coordinates(state: CartesianState, masses: Masses) -> dict:
    """
    Compute oriented triangle representation.

    Returns:
        Dictionary with:
            - distances: (r12, r23, r31)
            - angles: (alpha, beta, gamma) - interior angles
            - orientation: theta (angle of axis 1-2 from x-axis)
            - scale: overall scale (moment of inertia)

    Args:
        state: Cartesian state
        masses: Mass parameters

    Returns:
        Dictionary with geometric properties
    """
    state_canonical, theta = compute_canonical_orientation(state, "align_axis")

    r = state_canonical.positions

    # Distances
    r12 = np.linalg.norm(r[0] - r[1])
    r23 = np.linalg.norm(r[1] - r[2])
    r31 = np.linalg.norm(r[2] - r[0])

    # Angles (law of cosines)
    # Angle at vertex i is opposite to side between other two vertices
    def compute_angle(a, b, c):
        """Angle opposite to side c using law of cosines"""
        cos_angle = (a**2 + b**2 - c**2) / (2 * a * b)
        # Clamp to avoid numerical issues
        cos_angle = np.clip(cos_angle, -1, 1)
        return np.arccos(cos_angle)

    alpha = compute_angle(r12, r31, r23)  # Angle at vertex 1
    beta = compute_angle(r12, r23, r31)  # Angle at vertex 2
    gamma = np.pi - alpha - beta  # Angle at vertex 3

    # Scale (moment of inertia)
    from .cartesian import moment_of_inertia

    I = moment_of_inertia(state, masses)

    return {
        "distances": (r12, r23, r31),
        "angles": (alpha, beta, gamma),
        "orientation": theta,
        "scale": I,
    }


def compute_shape_metric(
    shape_state: ShapeSpaceState, masses: Masses
) -> np.ndarray:
    """
    Compute induced metric on shape space (quotient metric).

    This is the metric tensor in (r12, r23, r31) coordinates.

    Note: This is a simplified implementation. Full computation requires
    pulling back the mass metric via the embedding.

    Args:
        shape_state: Shape space state
        masses: Mass parameters

    Returns:
        3x3 metric tensor (approximate)
    """
    # Simplified: use identity metric as approximation
    # Full implementation would require Jacobian computation
    return np.eye(3)
