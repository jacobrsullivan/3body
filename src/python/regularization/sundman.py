"""
Sundman-type time transformations for regularization.

Implements various strategies for time reparametrization dt/ds = Ω(q),
which is fundamental to the KS regularization scheme.

Mathematical Framework:
    Fictitious time s is related to physical time t by:
        dt/ds = Ω(q)
    where Ω > 0 is the time dilation factor depending on configuration q.

Standard Choices:
    - Two-body: Ω = r = ‖q‖
    - KS transform: Ω = ‖u‖² = r
    - Three-body (sum): Ω = r₁₂ + r₂₃ + r₃₁
    - Three-body (product): Ω = r₁₂ · r₂₃ · r₃₁

Physical Interpretation:
    As collision approached (r → 0), time dilation → 0, meaning physical
    time t advances more slowly relative to fictitious time s. This
    "spreads out" the collision over infinite physical time but finite
    fictitious time, regularizing the dynamics.

References:
    - Sundman (1912): "Mémoire sur le problème des trois corps"
    - Stiefel & Scheifele (1971): Linear and Regular Celestial Mechanics
    - AMENDED_WP2.3-KS-Spinor-Lift-Implementation-Plan.md
"""

from enum import Enum
from typing import Callable, Optional
from dataclasses import dataclass
import numpy as np


class TimeTransformationStrategy(Enum):
    """
    Strategies for global time transformation.

    Each strategy represents a different choice of Ω(q) function.
    """
    # Single-body strategies
    STANDARD = "standard"          # Ω = r (standard Sundman)
    KS_SINGLE = "ks_single"       # Ω = ‖u‖² (for single KS pair)

    # Three-body strategies
    SUM = "sum"                    # Ω = r₁₂ + r₂₃ + r₃₁
    PRODUCT = "product"            # Ω = r₁₂ · r₂₃ · r₃₁
    MIN = "min"                    # Ω = min(r₁₂, r₂₃, r₃₁)
    WEIGHTED_SUM = "weighted_sum"  # Ω = Σ wᵢⱼ rᵢⱼ


@dataclass
class TimeDilationResult:
    """
    Result of time dilation computation.

    Attributes:
        Omega: Time dilation factor dt/ds
        strategy: Strategy used
        radii: Individual radii (if applicable)
        metadata: Additional information
    """
    Omega: float
    strategy: TimeTransformationStrategy
    radii: Optional[tuple] = None
    metadata: Optional[dict] = None

    def validate(self) -> bool:
        """Check if Omega is positive and finite"""
        return self.Omega > 0 and np.isfinite(self.Omega)


def compute_time_dilation_single(
    r: float,
    strategy: TimeTransformationStrategy = TimeTransformationStrategy.STANDARD
) -> float:
    """
    Compute time dilation for single two-body pair.

    Args:
        r: Separation distance
        strategy: Transformation strategy

    Returns:
        Ω = dt/ds

    Raises:
        ValueError: If r ≤ 0
    """
    if r <= 0:
        raise ValueError(f"Radius must be positive, got r={r}")

    if strategy == TimeTransformationStrategy.STANDARD:
        # Standard Sundman: Ω = r
        return r
    elif strategy == TimeTransformationStrategy.KS_SINGLE:
        # For KS: Ω = r (same as standard for single pair)
        return r
    else:
        raise ValueError(f"Strategy {strategy} not valid for single pair")


def compute_time_dilation_threebody(
    r12: float,
    r23: float,
    r31: float,
    strategy: TimeTransformationStrategy = TimeTransformationStrategy.SUM,
    weights: Optional[np.ndarray] = None
) -> TimeDilationResult:
    """
    Compute global time dilation for three-body problem.

    Different strategies trade off regularization strength vs. complexity.

    Args:
        r12, r23, r31: Pairwise distances
        strategy: Choice of time transformation
        weights: Optional weights for WEIGHTED_SUM strategy

    Returns:
        TimeDilationResult with Omega and metadata

    Examples:
        >>> compute_time_dilation_threebody(1.0, 2.0, 3.0, TimeTransformationStrategy.SUM)
        TimeDilationResult(Omega=6.0, strategy=<TimeTransformationStrategy.SUM: 'sum'>, radii=(1.0, 2.0, 3.0), metadata={'min_radius': 1.0, 'max_radius': 3.0})
    """
    # Validate inputs
    if any(r <= 0 for r in [r12, r23, r31]):
        raise ValueError("All radii must be positive")

    radii = (r12, r23, r31)
    metadata = {
        'min_radius': min(radii),
        'max_radius': max(radii),
        'mean_radius': np.mean(radii)
    }

    if strategy == TimeTransformationStrategy.PRODUCT:
        # Strongest regularization (triple zero at triple collision)
        # Best for scenarios with potential triple collisions
        Omega = r12 * r23 * r31
        metadata['description'] = "Product (strongest regularization)"

    elif strategy == TimeTransformationStrategy.SUM:
        # Simple, sufficient for binary collisions
        # Most commonly used in practice
        Omega = r12 + r23 + r31
        metadata['description'] = "Sum (standard for 3BP)"

    elif strategy == TimeTransformationStrategy.MIN:
        # Adapts to closest pair
        # WARNING: Can have discontinuous derivatives
        Omega = min(r12, r23, r31)
        metadata['description'] = "Min (adaptive, but non-smooth)"
        metadata['warning'] = "Non-smooth: not recommended for smooth integrators"

    elif strategy == TimeTransformationStrategy.WEIGHTED_SUM:
        # Mass-weighted (prioritize heavy pairs)
        if weights is None:
            raise ValueError("WEIGHTED_SUM strategy requires weights")
        if len(weights) != 3:
            raise ValueError(f"Weights must have length 3, got {len(weights)}")

        Omega = weights[0]*r12 + weights[1]*r23 + weights[2]*r31
        metadata['description'] = "Weighted sum"
        metadata['weights'] = weights

    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    return TimeDilationResult(
        Omega=Omega,
        strategy=strategy,
        radii=radii,
        metadata=metadata
    )


def compute_time_dilation_from_spinors(
    u12: np.ndarray,
    u23: np.ndarray,
    u31: np.ndarray,
    strategy: TimeTransformationStrategy = TimeTransformationStrategy.SUM
) -> TimeDilationResult:
    """
    Compute time dilation directly from pairwise spinors.

    Uses bilinear relation: rᵢⱼ = ‖uᵢⱼ‖²

    Args:
        u12, u23, u31: Pairwise spinors (4D arrays)
        strategy: Time transformation strategy

    Returns:
        TimeDilationResult
    """
    # Extract radii from spinors
    r12 = np.dot(u12, u12)  # ‖u₁₂‖²
    r23 = np.dot(u23, u23)  # ‖u₂₃‖²
    r31 = np.dot(u31, u31)  # ‖u₃₁‖²

    return compute_time_dilation_threebody(r12, r23, r31, strategy)


class SundmanTransformation:
    """
    Encapsulates a time transformation strategy.

    Provides callable interface for computing Ω(q) along trajectories.
    """

    def __init__(
        self,
        strategy: TimeTransformationStrategy,
        weights: Optional[np.ndarray] = None
    ):
        """
        Initialize transformation.

        Args:
            strategy: Time dilation strategy
            weights: Optional weights (for WEIGHTED_SUM)
        """
        self.strategy = strategy
        self.weights = weights

    def __call__(self, *radii: float) -> float:
        """
        Compute time dilation factor.

        Args:
            *radii: Either 1 radius (single pair) or 3 radii (three-body)

        Returns:
            Ω = dt/ds
        """
        if len(radii) == 1:
            return compute_time_dilation_single(radii[0], self.strategy)
        elif len(radii) == 3:
            result = compute_time_dilation_threebody(
                radii[0], radii[1], radii[2],
                self.strategy,
                self.weights
            )
            return result.Omega
        else:
            raise ValueError(f"Expected 1 or 3 radii, got {len(radii)}")

    def compute_derivative(self, *radii: float) -> np.ndarray:
        """
        Compute gradient of Ω with respect to radii: ∂Ω/∂r

        Useful for Hamiltonian mechanics and integrator implementations.

        Args:
            *radii: Radii (1 or 3)

        Returns:
            Gradient vector ∂Ω/∂r
        """
        if len(radii) == 1:
            # ∂Ω/∂r for single pair
            if self.strategy == TimeTransformationStrategy.STANDARD:
                # Ω = r → ∂Ω/∂r = 1
                return np.array([1.0])
            else:
                raise ValueError(f"Derivative not implemented for {self.strategy}")

        elif len(radii) == 3:
            r12, r23, r31 = radii

            if self.strategy == TimeTransformationStrategy.SUM:
                # Ω = r₁₂ + r₂₃ + r₃₁ → ∂Ω/∂rᵢⱼ = 1
                return np.array([1.0, 1.0, 1.0])

            elif self.strategy == TimeTransformationStrategy.PRODUCT:
                # Ω = r₁₂·r₂₃·r₃₁
                # ∂Ω/∂r₁₂ = r₂₃·r₃₁, etc.
                return np.array([
                    r23 * r31,  # ∂Ω/∂r₁₂
                    r12 * r31,  # ∂Ω/∂r₂₃
                    r12 * r23   # ∂Ω/∂r₃₁
                ])

            elif self.strategy == TimeTransformationStrategy.WEIGHTED_SUM:
                # Ω = w₁r₁₂ + w₂r₂₃ + w₃r₃₁
                return self.weights

            else:
                raise ValueError(f"Derivative not implemented for {self.strategy}")

        else:
            raise ValueError(f"Expected 1 or 3 radii, got {len(radii)}")

    def __repr__(self) -> str:
        return f"SundmanTransformation(strategy={self.strategy.value})"


def integrate_physical_time(
    s_values: np.ndarray,
    Omega_values: np.ndarray,
    t_initial: float = 0.0
) -> np.ndarray:
    """
    Integrate physical time from fictitious time samples.

    Computes: t(s) = t₀ + ∫₀ˢ Ω(s') ds'

    Args:
        s_values: Fictitious time samples
        Omega_values: Time dilation at each s
        t_initial: Initial physical time

    Returns:
        Physical time at each s value

    Example:
        >>> s = np.linspace(0, 1, 11)
        >>> Omega = np.ones_like(s)  # Constant dilation
        >>> t = integrate_physical_time(s, Omega, t_initial=0.0)
        >>> np.allclose(t, s)  # Should equal s for constant Ω=1
        True
    """
    # Trapezoidal rule integration
    ds = np.diff(s_values)
    Omega_avg = (Omega_values[:-1] + Omega_values[1:]) / 2

    dt = Omega_avg * ds
    t_values = np.concatenate([[t_initial], t_initial + np.cumsum(dt)])

    return t_values


def compute_effective_timestep(
    ds: float,
    Omega: float
) -> float:
    """
    Compute effective physical timestep from fictitious step.

    dt = Ω(q) · ds

    Args:
        ds: Fictitious time step
        Omega: Time dilation factor

    Returns:
        Physical time step dt

    Note:
        Near collisions (Ω → 0), physical timestep becomes very small,
        allowing smooth passage through singularities.
    """
    return Omega * ds


def estimate_collision_time_dilation(
    r_approach: float,
    v_approach: float,
    mu: float = 1.0
) -> dict:
    """
    Estimate time dilation near collision approach.

    For Kepler problem, can estimate how Ω behaves as collision approaches.

    Args:
        r_approach: Current separation
        v_approach: Approach velocity (negative for approach)
        mu: Gravitational parameter

    Returns:
        Dictionary with estimates
    """
    # Current time dilation
    Omega_current = r_approach

    # Estimate time to collision (rough)
    if v_approach < 0:
        t_collision_estimate = -r_approach / v_approach
    else:
        t_collision_estimate = float('inf')

    # In fictitious time, collision happens at finite s
    # Rough estimate: s_collision ~ ∫ ds ~ ∫ dt/r
    # For parabolic orbit: s_collision ~ finite

    return {
        'Omega_current': Omega_current,
        'r_approach': r_approach,
        'v_approach': v_approach,
        't_collision_estimate': t_collision_estimate,
        'time_dilation_active': Omega_current < 0.1 * r_approach,
        'approaching_collision': v_approach < 0
    }
