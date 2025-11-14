"""
S¹ principal bundle over shape space (WP 2.2, Part A).

Implements the total space P = Shape Space × S¹ where the fiber S¹ represents
the "twist" or "winding" accumulated as we move through shape space.

Mathematical Structure:
    S¹ ↪ P → S

where:
    - P = S × S¹ (total space, 4D)
    - S = shape space (base, 3D)
    - S¹ = circle fiber (1D)
    - π: P → S is the projection
"""

from dataclasses import dataclass
from typing import Optional, Callable, List
import numpy as np

from ..coordinates.base import Masses
from ..coordinates.shape_space import ShapeSpaceState


@dataclass(frozen=True)
class BundleState:
    """
    State in the S¹ bundle P = Shape Space × S¹.

    This represents a point in the 4D total space, with both
    base (shape) coordinates and fiber (angle) coordinate.

    Phase Space Dimension: 2 × 4 = 8
        - 3 shape coordinates (r12, r23, r31)
        - 1 fiber coordinate (θ)
        - 3 shape momenta (p_r12, p_r23, p_r31)
        - 1 fiber momentum (p_θ)

    Attributes:
        shape_state: Base space coordinates (shape space)
        theta: Fiber coordinate ∈ [0, 2π)
        shape_momenta: Conjugate momenta to shape coordinates
        p_theta: Conjugate momentum to fiber coordinate
    """

    shape_state: ShapeSpaceState
    theta: float  # ∈ [0, 2π)
    shape_momenta: np.ndarray  # (3,)
    p_theta: float

    def __post_init__(self):
        """Normalize theta to [0, 2π) and validate dimensions"""
        # Normalize theta
        normalized_theta = self.theta % (2 * np.pi)
        object.__setattr__(self, 'theta', normalized_theta)

        # Convert momenta to array
        momenta = np.asarray(self.shape_momenta)
        if momenta.shape != (3,):
            raise ValueError(f"shape_momenta must be (3,), got {momenta.shape}")
        object.__setattr__(self, 'shape_momenta', momenta)

    @property
    def configuration_dimension(self) -> int:
        """Dimension of configuration space: 3 (shape) + 1 (fiber) = 4"""
        return 4

    @property
    def phase_space_dimension(self) -> int:
        """Dimension of phase space: 2 × 4 = 8"""
        return 8

    def to_vector(self) -> np.ndarray:
        """
        Flatten to vector [r12, r23, r31, θ, p_r12, p_r23, p_r31, p_θ].

        Returns:
            Flat array of length 8
        """
        shape_coords = np.array([
            self.shape_state.r12,
            self.shape_state.r23,
            self.shape_state.r31
        ])

        return np.concatenate([
            shape_coords,
            [self.theta],
            self.shape_momenta,
            [self.p_theta]
        ])

    @classmethod
    def from_vector(cls, z: np.ndarray, L: float = 1.0) -> "BundleState":
        """
        Construct from flat vector.

        Args:
            z: Flat state vector [q, p] of length 8
            L: Angular momentum (needed for ShapeSpaceState)

        Returns:
            BundleState
        """
        if len(z) != 8:
            raise ValueError(f"Expected vector of length 8, got {len(z)}")

        # Split into coordinates and momenta
        q = z[:4]  # [r12, r23, r31, θ]
        p = z[4:]  # [p_r12, p_r23, p_r31, p_θ]

        # Create shape state
        shape_state = ShapeSpaceState(
            r12=q[0], r23=q[1], r31=q[2],
            dr12_dt=0, dr23_dt=0, dr31_dt=0,  # Will be set from momenta
            L=L,
            dimension=2
        )

        return cls(
            shape_state=shape_state,
            theta=q[3],
            shape_momenta=p[:3],
            p_theta=p[3]
        )

    def to_array(self) -> tuple:
        """Return as tuple for easier access: (shape_coords, theta, momenta, p_theta)"""
        return (
            np.array([self.shape_state.r12, self.shape_state.r23, self.shape_state.r31]),
            self.theta,
            self.shape_momenta,
            self.p_theta
        )


class S1Bundle:
    """
    Principal S¹ bundle over shape space.

    Construction: P = S × S¹
        - S: shape space (base manifold, 3D for planar case)
        - S¹: circle fiber (1D)
        - P: total space (4D)

    The projection π: P → S simply drops the fiber coordinate.
    """

    def __init__(self, masses: Masses):
        """
        Initialize S¹ bundle.

        Args:
            masses: Mass parameters (defines shape space)
        """
        self.masses = masses
        self.base_dimension = 3  # Shape space (planar)
        self.fiber_dimension = 1  # S¹
        self.total_dimension = 4  # S × S¹

    def create_state(
        self,
        shape_state: ShapeSpaceState,
        theta: float,
        shape_momenta: np.ndarray,
        p_theta: float
    ) -> BundleState:
        """
        Create a state in the bundle.

        Args:
            shape_state: Point in shape space
            theta: Fiber coordinate (angle)
            shape_momenta: Momenta in base space
            p_theta: Fiber momentum

        Returns:
            BundleState
        """
        return BundleState(
            shape_state=shape_state,
            theta=theta,
            shape_momenta=shape_momenta,
            p_theta=p_theta
        )

    def project_to_base(self, bundle_state: BundleState) -> ShapeSpaceState:
        """
        Projection π: P → S.

        Simply drop the fiber coordinate and fiber momentum.

        Args:
            bundle_state: Point in total space

        Returns:
            Projection to shape space
        """
        return bundle_state.shape_state

    def lift_from_base(
        self,
        base_state: ShapeSpaceState,
        theta: float = 0.0,
        shape_momenta: Optional[np.ndarray] = None,
        p_theta: float = 0.0
    ) -> BundleState:
        """
        Lift a shape space state to bundle.

        This is a section: s: S → P (right inverse of π).

        Args:
            base_state: Point in shape space
            theta: Fiber coordinate to lift to (default: 0)
            shape_momenta: Momenta (default: zeros)
            p_theta: Fiber momentum (default: 0)

        Returns:
            Lifted state in bundle
        """
        if shape_momenta is None:
            shape_momenta = np.zeros(3)

        return BundleState(
            shape_state=base_state,
            theta=theta,
            shape_momenta=shape_momenta,
            p_theta=p_theta
        )

    def fiber_over_point(
        self,
        base_point: ShapeSpaceState,
        n_points: int = 100
    ) -> List[BundleState]:
        """
        Return fiber π⁻¹(s) over a base point.

        The fiber is a circle: all states with fixed shape, varying θ.

        Args:
            base_point: Point in shape space
            n_points: Number of points to sample on fiber

        Returns:
            List of states representing fiber (discrete sample)
        """
        theta_values = np.linspace(0, 2*np.pi, n_points, endpoint=False)

        return [
            BundleState(
                shape_state=base_point,
                theta=theta,
                shape_momenta=np.zeros(3),
                p_theta=0.0
            )
            for theta in theta_values
        ]

    def is_vertical(
        self,
        tangent_vector: np.ndarray,
        tolerance: float = 1e-14
    ) -> bool:
        """
        Check if tangent vector is vertical (tangent to fiber).

        A vector is vertical if it points only in the θ direction:
            v = (0, 0, 0, v_θ, 0, 0, 0, p'_θ)

        Args:
            tangent_vector: Vector in T_p(P) (length 8)
            tolerance: Numerical tolerance

        Returns:
            True if vertical
        """
        if len(tangent_vector) != 8:
            raise ValueError("Tangent vector must have length 8")

        # Check if shape components are zero
        shape_part = tangent_vector[:3]
        shape_momenta_part = tangent_vector[4:7]

        return (
            np.linalg.norm(shape_part) < tolerance and
            np.linalg.norm(shape_momenta_part) < tolerance
        )

    def is_horizontal(
        self,
        tangent_vector: np.ndarray,
        tolerance: float = 1e-14
    ) -> bool:
        """
        Check if tangent vector is horizontal (perpendicular to fiber).

        For a horizontal vector, the fiber components vanish:
            v = (v_r, 0, v_p, 0)

        Args:
            tangent_vector: Vector in T_p(P)
            tolerance: Numerical tolerance

        Returns:
            True if horizontal
        """
        if len(tangent_vector) != 8:
            raise ValueError("Tangent vector must have length 8")

        # Check if fiber components are zero
        theta_part = tangent_vector[3]
        p_theta_part = tangent_vector[7]

        return abs(theta_part) < tolerance and abs(p_theta_part) < tolerance


@dataclass(frozen=True)
class BundleChart:
    """
    Local coordinate chart for S¹ bundle.

    A chart provides a local trivialization:
        φ: π⁻¹(U) → U × S¹

    where U ⊂ Shape Space is an open set.

    Attributes:
        name: Chart identifier
        base_domain: Function determining if shape state is in U
    """

    name: str
    base_domain: Callable[[ShapeSpaceState], bool]

    def is_in_domain(self, state: BundleState) -> bool:
        """Check if bundle state is in chart domain"""
        return self.base_domain(state.shape_state)

    def coordinates(self, state: BundleState) -> tuple:
        """
        Chart map: state → (shape_coords, θ) coordinates.

        Args:
            state: Point in bundle

        Returns:
            (shape_coords, theta) tuple
        """
        if not self.is_in_domain(state):
            raise ValueError(f"State not in domain of {self.name}")

        shape_coords = np.array([
            state.shape_state.r12,
            state.shape_state.r23,
            state.shape_state.r31
        ])

        return (shape_coords, state.theta)

    def from_coordinates(
        self,
        shape_coords: np.ndarray,
        theta: float,
        L: float = 1.0
    ) -> BundleState:
        """
        Inverse chart map: (shape_coords, θ) → state.

        Args:
            shape_coords: Shape space coordinates [r12, r23, r31]
            theta: Fiber coordinate
            L: Angular momentum

        Returns:
            BundleState (with zero momenta)
        """
        shape_state = ShapeSpaceState(
            r12=shape_coords[0],
            r23=shape_coords[1],
            r31=shape_coords[2],
            dr12_dt=0, dr23_dt=0, dr31_dt=0,
            L=L,
            dimension=2
        )

        return BundleState(
            shape_state=shape_state,
            theta=theta,
            shape_momenta=np.zeros(3),
            p_theta=0.0
        )


# Helper functions

def create_bundle_state(
    r12: float,
    r23: float,
    r31: float,
    theta: float,
    p_r12: float = 0.0,
    p_r23: float = 0.0,
    p_r31: float = 0.0,
    p_theta: float = 0.0,
    L: float = 1.0
) -> BundleState:
    """
    Convenience function to create bundle state from individual coordinates.

    Args:
        r12, r23, r31: Shape coordinates
        theta: Fiber coordinate
        p_r12, p_r23, p_r31: Shape momenta
        p_theta: Fiber momentum
        L: Angular momentum

    Returns:
        BundleState
    """
    shape_state = ShapeSpaceState(
        r12=r12, r23=r23, r31=r31,
        dr12_dt=0, dr23_dt=0, dr31_dt=0,
        L=L,
        dimension=2
    )

    return BundleState(
        shape_state=shape_state,
        theta=theta,
        shape_momenta=np.array([p_r12, p_r23, p_r31]),
        p_theta=p_theta
    )


def project_to_base(bundle_state: BundleState) -> ShapeSpaceState:
    """
    Project bundle state to shape space.

    Args:
        bundle_state: State in bundle

    Returns:
        State in shape space
    """
    return bundle_state.shape_state


def create_trivial_chart() -> BundleChart:
    """
    Create trivial chart covering all of shape space.

    This assumes shape space is contractible (topologically trivial).

    Returns:
        BundleChart covering entire shape space
    """
    def always_true(s: ShapeSpaceState) -> bool:
        """All states are in domain"""
        return s.validate()  # Only exclude invalid triangles

    return BundleChart(
        name="TrivialChart",
        base_domain=always_true
    )
