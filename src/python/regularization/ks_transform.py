"""
Kustaanheimo-Stiefel transformation for a single two-body pair.

Transforms 3D Cartesian (r, v) ↔ 4D spinor (u, u').

Mathematical Relations:
    Forward:  r = L(u)·u,  v = 2L(u)·u'
    Inverse:  u from r (non-unique), u' from v and u

Time Regularization:
    dt/ds = r = ‖u‖²
"""

from dataclasses import dataclass
from typing import Tuple, Optional
import numpy as np

from .spinor_vector import SpinorVector, create_spinor
from .levi_civita import (
    levi_civita_map,
    levi_civita_matrix,
    inverse_levi_civita_map,
    validate_bilinear_relation,
)


@dataclass(frozen=True)
class KSState:
    """
    State in KS coordinates for a single pair.

    Represents (r, v) ∈ ℝ³ × ℝ³ as (u, u') ∈ ℝ⁴ × ℝ⁴.

    Attributes:
        u: Position spinor
        u_prime: Velocity spinor (du/ds in fictitious time)
        fictitious_time: s (regularized time parameter)
        real_time: t (physical time, optional)
    """

    u: SpinorVector
    u_prime: SpinorVector
    fictitious_time: float = 0.0
    real_time: Optional[float] = None

    @property
    def radius(self) -> float:
        """Current radius: r = ‖u‖²"""
        return self.u.radius

    @property
    def time_derivative(self) -> float:
        """Time dilation factor: dt/ds = r"""
        return self.radius

    def to_cartesian(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert to Cartesian (r, v).

        Returns:
            (position, velocity) each ∈ ℝ³
        """
        u_arr = self.u.to_array()
        u_prime_arr = self.u_prime.to_array()

        # Position: r = L(u)·u
        r = levi_civita_map(u_arr, u_arr)

        # Velocity: v = 2L(u)·u'
        v = 2 * levi_civita_map(u_arr, u_prime_arr)

        return r, v

    def validate(self, r_expected: Optional[np.ndarray] = None) -> bool:
        """
        Validate KS state consistency.

        Args:
            r_expected: Expected Cartesian position (optional)

        Returns:
            True if valid
        """
        r, v = self.to_cartesian()

        # Check bilinear relation
        if not validate_bilinear_relation(self.u.to_array(), r):
            return False

        # Check against expected position if provided
        if r_expected is not None:
            if np.linalg.norm(r - r_expected) > 1e-10:
                return False

        return True


def cartesian_to_ks(
    r: np.ndarray,
    v: np.ndarray,
    s: float = 0.0,
    t: Optional[float] = None
) -> KSState:
    """
    Transform Cartesian (r, v) → KS (u, u').

    Args:
        r: 3D position
        v: 3D velocity
        s: Fictitious time (default: 0)
        t: Real time (optional)

    Returns:
        KSState

    Algorithm:
        1. Find u such that L(u)·u = r (non-unique, choose one branch)
        2. Solve for u' from: 2L(u)·u' = v
           → u' = (1/2) L^T(u) · v / ‖u‖²

    Note:
        The inverse transform is not unique! Different u can give same r.
        We use the geometric construction from Stiefel & Scheifele.
    """
    # Step 1: Find u from r
    u_arr = inverse_levi_civita_map(r)
    u = SpinorVector(u_arr)

    # Step 2: Find u' from v and u
    # From v = 2 L(u)·u', we solve for u':
    #   L(u)·u' = v/2
    # Using L^T(u)·L(u) = ‖u‖² I₄, we get:
    #   u' = (1/2) L^T(u)·v / ‖u‖²

    u_norm_sq = u.norm_squared

    if u_norm_sq < 1e-14:
        # At collision, set u' = 0
        u_prime_arr = np.zeros(4)
    else:
        L = levi_civita_matrix(u_arr)
        # u' = L^T · v / (2 ‖u‖²)
        u_prime_arr = L.T @ v / (2 * u_norm_sq)

    u_prime = SpinorVector(u_prime_arr)

    return KSState(
        u=u,
        u_prime=u_prime,
        fictitious_time=s,
        real_time=t
    )


def ks_to_cartesian(state: KSState) -> Tuple[np.ndarray, np.ndarray]:
    """
    Transform KS (u, u') → Cartesian (r, v).

    Args:
        state: KS state

    Returns:
        (r, v): Position and velocity in ℝ³
    """
    return state.to_cartesian()


def ks_time_step(
    state: KSState,
    ds: float
) -> KSState:
    """
    Advance KS state by fictitious time step ds.

    Simple Euler step (for demonstration; use better integrator in practice).

    Args:
        state: Current KS state
        ds: Fictitious time step

    Returns:
        New KS state
    """
    # Simple Euler: u_new = u + u'·ds
    u_new = state.u + state.u_prime * ds

    # Update times
    dt = state.radius * ds  # Real time increment
    s_new = state.fictitious_time + ds
    t_new = (state.real_time + dt) if state.real_time is not None else None

    # u_prime stays same (first-order approximation)
    # In real integrator, would solve Hamilton's equations

    return KSState(
        u=u_new,
        u_prime=state.u_prime,
        fictitious_time=s_new,
        real_time=t_new
    )


def compute_ks_energy(
    state: KSState,
    mu: float = 1.0
) -> float:
    """
    Compute energy in KS coordinates.

    For two-body problem: H = ½v² - μ/r

    In KS coords: K = 2r(H + μ/r) = 2r·(½v²) = ‖u'‖²·‖u‖²

    Args:
        state: KS state
        mu: Gravitational parameter

    Returns:
        KS energy K
    """
    u_norm_sq = state.u.norm_squared
    u_prime_norm_sq = state.u_prime.norm_squared

    # K = ‖u'‖² · ‖u‖²
    K = u_prime_norm_sq * u_norm_sq

    return K


def validate_ks_roundtrip(
    r: np.ndarray,
    v: np.ndarray,
    tolerance: float = 1e-10
) -> bool:
    """
    Test Cartesian → KS → Cartesian roundtrip.

    Args:
        r: 3D position
        v: 3D velocity
        tolerance: Numerical tolerance

    Returns:
        True if roundtrip is accurate
    """
    # Forward transform
    ks_state = cartesian_to_ks(r, v)

    # Backward transform
    r_reconstructed, v_reconstructed = ks_to_cartesian(ks_state)

    # Compare
    r_error = np.linalg.norm(r - r_reconstructed)
    v_error = np.linalg.norm(v - v_reconstructed)

    return (r_error < tolerance and v_error < tolerance)
