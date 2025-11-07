"""
Coordinate transformation utilities for CR3BP.

Implements transformations between co-rotating and inertial frames,
essential for multi-frame trajectory analysis and validation.
"""

import numpy as np
from typing import Tuple, Union


def rotation_matrix(t: float) -> np.ndarray:
    """
    Create rotation matrix for transformation from rotating to inertial frame.

    In the CR3BP, the co-rotating frame rotates with angular velocity ω=1
    about the z-axis. The rotation matrix R(t) transforms vectors from the
    rotating frame to the inertial (barycentric) frame.

    Args:
        t: Time (in dimensionless units, where orbital period = 2π)

    Returns:
        3x3 rotation matrix R(t)

    Note:
        R(t) = [cos(t)  -sin(t)  0]
               [sin(t)   cos(t)  0]
               [0        0       1]
    """
    cos_t = np.cos(t)
    sin_t = np.sin(t)

    return np.array([
        [cos_t, -sin_t, 0.0],
        [sin_t,  cos_t, 0.0],
        [0.0,    0.0,   1.0]
    ])


def rotation_matrix_derivative(t: float) -> np.ndarray:
    """
    Time derivative of the rotation matrix dR/dt.

    Required for transforming velocities from rotating to inertial frame.

    Args:
        t: Time (in dimensionless units)

    Returns:
        3x3 matrix dR/dt

    Note:
        dR/dt = [-sin(t)  -cos(t)  0]
                [ cos(t)  -sin(t)  0]
                [ 0        0       0]
    """
    cos_t = np.cos(t)
    sin_t = np.sin(t)

    return np.array([
        [-sin_t, -cos_t, 0.0],
        [ cos_t, -sin_t, 0.0],
        [ 0.0,    0.0,   0.0]
    ])


def corotating_to_inertial(
    state_rot: np.ndarray,
    t: float
) -> np.ndarray:
    """
    Transform state from co-rotating to inertial (barycentric) frame.

    The transformation includes:
    - Position: r_inertial = R(t) @ r_rotating
    - Velocity: v_inertial = R(t) @ v_rotating + ω × r_inertial
      where ω = [0, 0, 1] is the angular velocity of the rotating frame

    Args:
        state_rot: State in co-rotating frame [x, y, z, vx, vy, vz]
        t: Time (in dimensionless units)

    Returns:
        State in inertial frame [x, y, z, vx, vy, vz]
    """
    state_rot = np.asarray(state_rot)

    # Extract position and velocity
    r_rot = state_rot[:3]
    v_rot = state_rot[3:6]

    # Get rotation matrix
    R = rotation_matrix(t)

    # Transform position
    r_inertial = R @ r_rot

    # Transform velocity (includes frame rotation effect: ω × r)
    # ω = [0, 0, 1], so ω × r = [-y, x, 0]
    omega_cross_r = np.array([-r_inertial[1], r_inertial[0], 0.0])
    v_inertial = R @ v_rot + omega_cross_r

    return np.concatenate([r_inertial, v_inertial])


def inertial_to_corotating(
    state_inertial: np.ndarray,
    t: float
) -> np.ndarray:
    """
    Transform state from inertial (barycentric) to co-rotating frame.

    This is the inverse of corotating_to_inertial.

    Args:
        state_inertial: State in inertial frame [x, y, z, vx, vy, vz]
        t: Time (in dimensionless units)

    Returns:
        State in co-rotating frame [x, y, z, vx, vy, vz]
    """
    state_inertial = np.asarray(state_inertial)

    # Extract position and velocity
    r_inertial = state_inertial[:3]
    v_inertial = state_inertial[3:6]

    # Get transformation matrices (inverse is transpose for rotation)
    R = rotation_matrix(t)
    R_inv = R.T

    # Transform position
    r_rot = R_inv @ r_inertial

    # Transform velocity (remove frame rotation effect)
    # ω × r_inertial where ω = [0, 0, 1]
    omega_cross_r = np.array([-r_inertial[1], r_inertial[0], 0.0])
    v_rot = R_inv @ (v_inertial - omega_cross_r)

    return np.concatenate([r_rot, v_rot])


def transform_trajectory_to_inertial(
    states_rot: np.ndarray,
    times: np.ndarray
) -> np.ndarray:
    """
    Transform entire trajectory from co-rotating to inertial frame.

    Efficiently processes multiple timesteps.

    Args:
        states_rot: Array of shape (N, 6) with states in rotating frame
        times: Array of shape (N,) with corresponding times

    Returns:
        Array of shape (N, 6) with states in inertial frame
    """
    states_rot = np.asarray(states_rot)
    times = np.asarray(times)

    if states_rot.ndim == 1:
        states_rot = states_rot.reshape(1, -1)

    n_points = len(times)
    states_inertial = np.zeros_like(states_rot)

    for i in range(n_points):
        states_inertial[i] = corotating_to_inertial(states_rot[i], times[i])

    return states_inertial


def transform_trajectory_to_corotating(
    states_inertial: np.ndarray,
    times: np.ndarray
) -> np.ndarray:
    """
    Transform entire trajectory from inertial to co-rotating frame.

    Efficiently processes multiple timesteps.

    Args:
        states_inertial: Array of shape (N, 6) with states in inertial frame
        times: Array of shape (N,) with corresponding times

    Returns:
        Array of shape (N, 6) with states in co-rotating frame
    """
    states_inertial = np.asarray(states_inertial)
    times = np.asarray(times)

    if states_inertial.ndim == 1:
        states_inertial = states_inertial.reshape(1, -1)

    n_points = len(times)
    states_rot = np.zeros_like(states_inertial)

    for i in range(n_points):
        states_rot[i] = inertial_to_corotating(states_inertial[i], times[i])

    return states_rot


def primary_positions_inertial(mu: float, t: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate positions of the two primaries in inertial frame.

    In the CR3BP, the primaries orbit their barycenter with the same period
    as the co-rotating frame rotation. In the inertial frame, they move
    in circles.

    Args:
        mu: Mass parameter (m2 / (m1 + m2))
        t: Time (in dimensionless units)

    Returns:
        Tuple of (r1, r2) where r1, r2 are 3D position vectors

    Note:
        In co-rotating frame:
        - Primary 1 (larger, mass=1-μ) is at [-μ, 0, 0]
        - Primary 2 (smaller, mass=μ) is at [1-μ, 0, 0]
        This ensures barycenter is at origin: (1-μ)*[-μ] + μ*[1-μ] = 0
    """
    cos_t = np.cos(t)
    sin_t = np.sin(t)

    # Primary 1 position (larger mass) in co-rotating: [-μ, 0, 0]
    # Rotated to inertial frame
    r1 = np.array([
        -mu * cos_t,
        -mu * sin_t,
        0.0
    ])

    # Primary 2 position (smaller mass) in co-rotating: [1-μ, 0, 0]
    # Rotated to inertial frame
    r2 = np.array([
        (1 - mu) * cos_t,
        (1 - mu) * sin_t,
        0.0
    ])

    return r1, r2


def verify_transformation_roundtrip(
    state_rot: np.ndarray,
    t: float,
    tolerance: float = 1e-13
) -> bool:
    """
    Verify round-trip transformation accuracy.

    Transforms from rotating -> inertial -> rotating and checks
    if we recover the original state within tolerance.

    Args:
        state_rot: Original state in co-rotating frame
        t: Time
        tolerance: Maximum acceptable error

    Returns:
        True if round-trip error is within tolerance
    """
    state_inertial = corotating_to_inertial(state_rot, t)
    state_recovered = inertial_to_corotating(state_inertial, t)

    error = np.max(np.abs(state_recovered - state_rot))
    return error < tolerance


# Alias for backward compatibility with different signature
def transform_trajectory(times, states, mu, to_inertial=True):
    """
    Transform trajectory between coordinate frames (legacy interface).

    Args:
        times: Array of times
        states: Array of states
        mu: Mass parameter (unused, kept for compatibility)
        to_inertial: If True, transform to inertial, else to corotating

    Returns:
        Transformed states
    """
    if to_inertial:
        return transform_trajectory_to_inertial(states, times)
    else:
        return transform_trajectory_to_corotating(states, times)
