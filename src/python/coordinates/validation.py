"""
Validation utilities for coordinate systems.

Provides functions to verify conservation laws, coordinate constraints,
and transformation accuracy.
"""

from typing import Dict, List
import numpy as np

from .base import Masses
from .cartesian import (
    CartesianState,
    compute_energy,
    compute_angular_momentum,
    compute_linear_momentum,
)


def verify_conservation_laws(
    states: List[CartesianState],
    masses: Masses,
    G: float = 1.0,
    tolerances: Dict[str, float] = None,
) -> Dict[str, bool]:
    """
    Verify conservation laws over a trajectory.

    Checks:
        - Energy conservation
        - Angular momentum conservation
        - Linear momentum conservation (should be zero in barycentric frame)

    Args:
        states: List of Cartesian states along trajectory
        masses: Mass parameters
        G: Gravitational constant
        tolerances: Dictionary with 'energy', 'angular_momentum', 'linear_momentum'

    Returns:
        Dictionary indicating which laws are conserved
    """
    if tolerances is None:
        tolerances = {
            "energy": 1e-10,
            "angular_momentum": 1e-12,
            "linear_momentum": 1e-12,
        }

    if not states:
        return {"energy": True, "angular_momentum": True, "linear_momentum": True}

    # Compute conserved quantities
    energies = [compute_energy(s, masses, G) for s in states]
    ang_momenta = [compute_angular_momentum(s, masses) for s in states]
    lin_momenta = [compute_linear_momentum(s, masses) for s in states]

    # Check conservation
    E0 = energies[0]
    L0 = ang_momenta[0]
    P0 = lin_momenta[0]

    energy_conserved = all(
        abs(E - E0) / abs(E0) < tolerances["energy"] if E0 != 0 else abs(E) < tolerances["energy"]
        for E in energies
    )

    angular_conserved = all(
        np.linalg.norm(L - L0) < tolerances["angular_momentum"] for L in ang_momenta
    )

    linear_conserved = all(
        np.linalg.norm(P - P0) < tolerances["linear_momentum"] for P in lin_momenta
    )

    return {
        "energy": energy_conserved,
        "angular_momentum": angular_conserved,
        "linear_momentum": linear_conserved,
    }


def compute_conservation_errors(
    states: List[CartesianState], masses: Masses, G: float = 1.0
) -> Dict[str, Dict[str, float]]:
    """
    Compute conservation error statistics.

    Args:
        states: List of Cartesian states
        masses: Mass parameters
        G: Gravitational constant

    Returns:
        Dictionary with statistics for each conserved quantity
    """
    if not states:
        return {}

    # Compute conserved quantities
    energies = np.array([compute_energy(s, masses, G) for s in states])
    ang_momenta = np.array([compute_angular_momentum(s, masses) for s in states])
    lin_momenta = np.array([compute_linear_momentum(s, masses) for s in states])

    E0 = energies[0]
    L0 = ang_momenta[0]
    P0 = lin_momenta[0]

    # Energy errors
    energy_abs_errors = np.abs(energies - E0)
    energy_rel_errors = (
        energy_abs_errors / abs(E0) if E0 != 0 else energy_abs_errors
    )

    # Angular momentum errors
    ang_mom_errors = np.linalg.norm(ang_momenta - L0, axis=1)

    # Linear momentum errors
    lin_mom_errors = np.linalg.norm(lin_momenta - P0, axis=1)

    return {
        "energy": {
            "initial": float(E0),
            "final": float(energies[-1]),
            "max_abs_error": float(np.max(energy_abs_errors)),
            "max_rel_error": float(np.max(energy_rel_errors)),
            "mean_abs_error": float(np.mean(energy_abs_errors)),
            "drift": float(energies[-1] - E0),
        },
        "angular_momentum": {
            "initial_magnitude": float(np.linalg.norm(L0)),
            "final_magnitude": float(np.linalg.norm(ang_momenta[-1])),
            "max_error": float(np.max(ang_mom_errors)),
            "mean_error": float(np.mean(ang_mom_errors)),
        },
        "linear_momentum": {
            "initial_magnitude": float(np.linalg.norm(P0)),
            "final_magnitude": float(np.linalg.norm(lin_momenta[-1])),
            "max_error": float(np.max(lin_mom_errors)),
            "mean_error": float(np.mean(lin_mom_errors)),
        },
    }


def verify_barycentric_frame(state: CartesianState, masses: Masses, tol: float = 1e-12) -> bool:
    """
    Verify state is in barycentric frame.

    Checks:
        - Σ mᵢrᵢ = 0
        - Σ mᵢvᵢ = 0

    Args:
        state: Cartesian state
        masses: Mass parameters
        tol: Tolerance

    Returns:
        True if in barycentric frame
    """
    m = masses.as_array()

    r_cm = np.sum(state.positions * m[:, np.newaxis], axis=0)
    v_cm = np.sum(state.velocities * m[:, np.newaxis], axis=0)

    return np.linalg.norm(r_cm) < tol and np.linalg.norm(v_cm) < tol


def compute_virial_ratio(state: CartesianState, masses: Masses, G: float = 1.0) -> float:
    """
    Compute virial ratio 2T/|V|.

    For bound orbits, this should oscillate around 1 (averaged over time).

    Args:
        state: Cartesian state
        masses: Mass parameters
        G: Gravitational constant

    Returns:
        Virial ratio
    """
    from .cartesian import compute_potential_energy

    m = masses.as_array()

    # Kinetic energy
    T = 0.5 * np.sum(m[:, np.newaxis] * state.velocities**2)

    # Potential energy
    V = compute_potential_energy(state, masses, G)

    return 2 * T / abs(V) if V != 0 else np.inf


def detect_close_encounters(
    state: CartesianState, threshold: float = 0.1
) -> List[tuple]:
    """
    Detect close encounters between bodies.

    Args:
        state: Cartesian state
        threshold: Distance threshold for close encounter

    Returns:
        List of (i, j, distance) tuples for close pairs
    """
    r = state.positions
    close_encounters = []

    pairs = [(0, 1), (0, 2), (1, 2)]
    for i, j in pairs:
        dist = np.linalg.norm(r[i] - r[j])
        if dist < threshold:
            close_encounters.append((i, j, dist))

    return close_encounters


def check_collision(state: CartesianState, collision_radius: float = 1e-6) -> bool:
    """
    Check if any two bodies have collided.

    Args:
        state: Cartesian state
        collision_radius: Minimum allowed separation

    Returns:
        True if collision detected
    """
    r = state.positions

    pairs = [(0, 1), (0, 2), (1, 2)]
    for i, j in pairs:
        dist = np.linalg.norm(r[i] - r[j])
        if dist < collision_radius:
            return True

    return False


def compute_characteristic_timescale(masses: Masses, G: float = 1.0, scale: float = 1.0) -> float:
    """
    Compute characteristic orbital timescale.

    Uses T ~ √(a³/GM) for typical scale a.

    Args:
        masses: Mass parameters
        G: Gravitational constant
        scale: Typical length scale

    Returns:
        Characteristic time
    """
    M = masses.total
    return np.sqrt(scale**3 / (G * M))
