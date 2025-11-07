"""
CR3BP dynamics and physical calculations.

This module implements the equations of motion for the Circular Restricted
Three-Body Problem (CR3BP) and provides utilities for calculating conserved
quantities and other physical properties.
"""

import numpy as np
from typing import Tuple


def distances_to_primaries(state: np.ndarray, mu: float) -> Tuple[float, float]:
    """
    Calculate distances from a point to the two primary bodies.

    In the CR3BP normalized coordinate system:
    - Primary M1 is located at (-mu, 0, 0)
    - Primary M2 is located at (1-mu, 0, 0)

    Args:
        state: State vector [x, y, z, vx, vy, vz] or position [x, y, z]
        mu: Mass parameter (M2 / (M1 + M2))

    Returns:
        Tuple of (r1, r2) distances to primary and secondary
    """
    # Extract position (handle both state vectors and position vectors)
    if len(state) >= 3:
        x, y, z = state[0], state[1], state[2]
    else:
        raise ValueError("State must have at least 3 components for position")

    # Distance to primary M1 at (-mu, 0, 0)
    r1 = np.sqrt((x + mu) ** 2 + y**2 + z**2)

    # Distance to secondary M2 at (1-mu, 0, 0)
    r2 = np.sqrt((x - 1 + mu) ** 2 + y**2 + z**2)

    return r1, r2


def cr3bp_acceleration(state: np.ndarray, mu: float) -> np.ndarray:
    """
    Calculate acceleration in the CR3BP in the co-rotating frame.

    The equations of motion in the co-rotating frame are:
    ẍ = 2ẏ + x - (1-μ)(x+μ)/r₁³ - μ(x-1+μ)/r₂³
    ÿ = -2ẋ + y - (1-μ)y/r₁³ - μy/r₂³
    z̈ = -(1-μ)z/r₁³ - μz/r₂³

    Args:
        state: State vector [x, y, z, vx, vy, vz] in co-rotating frame
        mu: Mass parameter (M2 / (M1 + M2))

    Returns:
        Acceleration vector [ax, ay, az]
    """
    if len(state) != 6:
        raise ValueError("State must be 6-dimensional [x, y, z, vx, vy, vz]")

    x, y, z = state[0], state[1], state[2]
    vx, vy, vz = state[3], state[4], state[5]  # noqa: F841

    # Calculate distances to primaries
    r1, r2 = distances_to_primaries(state, mu)

    # Avoid division by zero (add small regularization if needed)
    r1_safe = max(r1, 1e-15)
    r2_safe = max(r2, 1e-15)

    # Calculate gravitational terms
    r1_cubed = r1_safe**3
    r2_cubed = r2_safe**3

    # Mass factors
    m1 = 1.0 - mu  # Mass of primary
    m2 = mu  # Mass of secondary

    # Accelerations including Coriolis and centrifugal terms
    ax = 2.0 * vy + x - m1 * (x + mu) / r1_cubed - m2 * (x - 1 + mu) / r2_cubed

    ay = -2.0 * vx + y - m1 * y / r1_cubed - m2 * y / r2_cubed

    az = -m1 * z / r1_cubed - m2 * z / r2_cubed

    return np.array([ax, ay, az])


def cr3bp_potential(state: np.ndarray, mu: float) -> float:
    """
    Calculate the effective potential in the CR3BP co-rotating frame.

    The effective potential includes gravitational and centrifugal terms:
    U = -[(1-μ)/r₁ + μ/r₂ + (x² + y²)/2]

    Args:
        state: State vector [x, y, z, vx, vy, vz] or position [x, y, z]
        mu: Mass parameter

    Returns:
        Effective potential energy
    """
    x, y, z = state[0], state[1], state[2]  # noqa: F841

    # Calculate distances to primaries
    r1, r2 = distances_to_primaries(state, mu)

    # Avoid division by zero
    r1_safe = max(r1, 1e-15)
    r2_safe = max(r2, 1e-15)

    # Gravitational potential
    gravitational = -(1 - mu) / r1_safe - mu / r2_safe

    # Centrifugal potential (from rotating frame)
    centrifugal = -(x**2 + y**2) / 2.0

    return gravitational + centrifugal


def kinetic_energy(state: np.ndarray) -> float:
    """
    Calculate kinetic energy of a particle.

    Args:
        state: State vector [x, y, z, vx, vy, vz]

    Returns:
        Kinetic energy T = (vx² + vy² + vz²)/2
    """
    if len(state) != 6:
        raise ValueError("State must be 6-dimensional")

    vx, vy, vz = state[3], state[4], state[5]
    return 0.5 * (vx**2 + vy**2 + vz**2)


def calculate_jacobi_constant(state: np.ndarray, mu: float) -> float:
    """
    Calculate the Jacobi constant (the only conserved quantity in CR3BP).

    The Jacobi constant is defined as:
    C = x² + y² + 2(1-μ)/r₁ + 2μ/r₂ - (vx² + vy² + vz²)

    This should be conserved throughout the motion in the absence of
    numerical errors.

    Args:
        state: State vector [x, y, z, vx, vy, vz] in co-rotating frame
        mu: Mass parameter (M2 / (M1 + M2))

    Returns:
        Jacobi constant value
    """
    if len(state) != 6:
        raise ValueError("State must be 6-dimensional [x, y, z, vx, vy, vz]")

    x, y, z = state[0], state[1], state[2]  # noqa: F841
    vx, vy, vz = state[3], state[4], state[5]

    # Calculate distances to primaries
    r1, r2 = distances_to_primaries(state, mu)

    # Avoid division by zero
    r1_safe = max(r1, 1e-15)
    r2_safe = max(r2, 1e-15)

    # Jacobi constant formula
    C = (
        x**2
        + y**2
        + 2 * (1 - mu) / r1_safe
        + 2 * mu / r2_safe
        - (vx**2 + vy**2 + vz**2)
    )

    return C


def calculate_energy(state: np.ndarray, mu: float) -> float:
    """
    Calculate total energy in the co-rotating frame.

    E = T + U where T is kinetic energy and U is effective potential

    Args:
        state: State vector [x, y, z, vx, vy, vz]
        mu: Mass parameter

    Returns:
        Total energy
    """
    T = kinetic_energy(state)
    U = cr3bp_potential(state, mu)
    return T + U


def jacobi_drift_metric(
    states: np.ndarray, mu: float
) -> Tuple[float, float, np.ndarray]:
    """
    Calculate Jacobi constant drift over a trajectory.

    Args:
        states: Array of state vectors [N, 6]
        mu: Mass parameter

    Returns:
        Tuple of (initial_jacobi, final_jacobi, jacobi_series)
        where jacobi_series is the time series of Jacobi values
    """
    if states.ndim != 2 or states.shape[1] != 6:
        raise ValueError("States must be array of shape [N, 6]")

    jacobi_series = np.array([calculate_jacobi_constant(state, mu) for state in states])

    initial_jacobi = jacobi_series[0]
    final_jacobi = jacobi_series[-1]

    return initial_jacobi, final_jacobi, jacobi_series


def relative_jacobi_error(states: np.ndarray, mu: float) -> float:
    """
    Calculate relative Jacobi constant error over trajectory.

    Returns |ΔC/C₀| where ΔC is the change in Jacobi constant
    and C₀ is the initial value.

    Args:
        states: Array of state vectors [N, 6]
        mu: Mass parameter

    Returns:
        Relative Jacobi error
    """
    initial_jacobi, final_jacobi, _ = jacobi_drift_metric(states, mu)

    if abs(initial_jacobi) < 1e-15:
        # If initial Jacobi is near zero, use absolute error
        return abs(final_jacobi - initial_jacobi)
    else:
        return abs((final_jacobi - initial_jacobi) / initial_jacobi)


def energy_error_metric(
    states: np.ndarray, mu: float
) -> Tuple[float, float, np.ndarray]:
    """
    Calculate energy error over a trajectory.

    Args:
        states: Array of state vectors [N, 6]
        mu: Mass parameter

    Returns:
        Tuple of (initial_energy, final_energy, energy_series)
    """
    if states.ndim != 2 or states.shape[1] != 6:
        raise ValueError("States must be array of shape [N, 6]")

    energy_series = np.array([calculate_energy(state, mu) for state in states])

    initial_energy = energy_series[0]
    final_energy = energy_series[-1]

    return initial_energy, final_energy, energy_series


def relative_energy_error(states: np.ndarray, mu: float) -> float:
    """
    Calculate relative energy error over trajectory.

    Args:
        states: Array of state vectors [N, 6]
        mu: Mass parameter

    Returns:
        Relative energy error |ΔE/E₀|
    """
    initial_energy, final_energy, _ = energy_error_metric(states, mu)

    if abs(initial_energy) < 1e-15:
        return abs(final_energy - initial_energy)
    else:
        return abs((final_energy - initial_energy) / initial_energy)


def lagrange_points(mu: float) -> np.ndarray:
    """
    Calculate the five Lagrange points for given mass parameter.

    Args:
        mu: Mass parameter (M2 / (M1 + M2))

    Returns:
        Array of shape [5, 3] containing positions of L1-L5 points
    """
    # This is a simplified calculation for the collinear points
    # For precise calculation, one would need to solve the quintic equation

    points = np.zeros((5, 3))

    # L4 and L5 (triangular points) - exact solutions
    points[3] = [0.5 - mu, np.sqrt(3) / 2, 0]  # L4
    points[4] = [0.5 - mu, -np.sqrt(3) / 2, 0]  # L5

    # L1, L2, L3 require numerical solution of quintic
    # Using approximations for now
    gamma = (mu / 3) ** (1 / 3)

    # L1 (between primaries)
    points[0] = [1 - mu - gamma, 0, 0]

    # L2 (beyond secondary)
    points[1] = [1 - mu + gamma, 0, 0]

    # L3 (beyond primary)
    points[2] = [-mu - gamma, 0, 0]

    return points


def zero_velocity_curves(
    mu: float,
    jacobi_constant: float,
    x_range: Tuple[float, float] = (-2, 2),
    y_range: Tuple[float, float] = (-2, 2),
    resolution: int = 200,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate zero velocity curves for given Jacobi constant.

    These curves define the boundary of allowed motion in the CR3BP.

    Args:
        mu: Mass parameter
        jacobi_constant: Value of Jacobi constant
        x_range: Range of x coordinates
        y_range: Range of y coordinates
        resolution: Grid resolution

    Returns:
        Tuple of (X, Y, allowed) where X, Y are meshgrids and
        allowed is boolean array indicating allowed regions
    """
    x = np.linspace(x_range[0], x_range[1], resolution)
    y = np.linspace(y_range[0], y_range[1], resolution)
    X, Y = np.meshgrid(x, y)

    # For each point, check if motion is allowed
    allowed = np.zeros_like(X, dtype=bool)

    for i in range(resolution):
        for j in range(resolution):
            state = np.array([X[i, j], Y[i, j], 0, 0, 0, 0])
            # Motion is allowed if effective potential allows kinetic energy >= 0
            # This occurs when C >= C_eff where C_eff is calculated from position only
            r1, r2 = distances_to_primaries(state, mu)
            r1_safe = max(r1, 1e-15)
            r2_safe = max(r2, 1e-15)

            C_eff = (
                X[i, j] ** 2 + Y[i, j] ** 2 + 2 * (1 - mu) / r1_safe + 2 * mu / r2_safe
            )
            allowed[i, j] = jacobi_constant >= C_eff

    return X, Y, allowed
