"""Clean-room Jacobi/body-frame reference with no production imports."""

from __future__ import annotations

from typing import Any

import numpy as np
import sympy as sp


def jacobi_reduce(
    positions: np.ndarray,
    velocities: np.ndarray,
    masses: np.ndarray,
) -> dict[str, np.ndarray]:
    positions = np.asarray(positions, dtype=float)
    velocities = np.asarray(velocities, dtype=float)
    masses = np.asarray(masses, dtype=float)
    m1, m2, m3 = masses
    m12 = m1 + m2
    total = m12 + m3
    center = np.sum(masses[:, None] * positions, axis=0) / total
    center_velocity = np.sum(masses[:, None] * velocities, axis=0) / total
    rho = positions[1] - positions[0]
    center12 = (m1 * positions[0] + m2 * positions[1]) / m12
    velocity12 = (m1 * velocities[0] + m2 * velocities[1]) / m12
    lambda_vector = positions[2] - center12
    mu12 = m1 * m2 / m12
    mu3_12 = m3 * m12 / total
    return {
        "center": center,
        "total_momentum": total * center_velocity,
        "rho": rho,
        "lambda": lambda_vector,
        "p_rho": mu12 * (velocities[1] - velocities[0]),
        "p_lambda": mu3_12 * (velocities[2] - velocity12),
    }


def jacobi_reconstruct(reduced: dict[str, np.ndarray], masses: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    masses = np.asarray(masses, dtype=float)
    m1, m2, m3 = masses
    m12 = m1 + m2
    total = m12 + m3
    center = reduced["center"]
    center_velocity = reduced["total_momentum"] / total
    rho = reduced["rho"]
    lambda_vector = reduced["lambda"]
    mu12 = m1 * m2 / m12
    mu3_12 = m3 * m12 / total
    relative12_velocity = reduced["p_rho"] / mu12
    lambda_velocity = reduced["p_lambda"] / mu3_12
    center12 = center - (m3 / total) * lambda_vector
    positions = np.array(
        [
            center12 - (m2 / m12) * rho,
            center12 + (m1 / m12) * rho,
            center + (m12 / total) * lambda_vector,
        ]
    )
    velocity12 = center_velocity - (m3 / total) * lambda_velocity
    velocities = np.array(
        [
            velocity12 - (m2 / m12) * relative12_velocity,
            velocity12 + (m1 / m12) * relative12_velocity,
            center_velocity + (m12 / total) * lambda_velocity,
        ]
    )
    return positions, velocities


def body_frame(rho: np.ndarray, lambda_vector: np.ndarray) -> np.ndarray:
    e1 = rho / np.linalg.norm(rho)
    normal = np.cross(rho, lambda_vector)
    e3 = normal / np.linalg.norm(normal)
    e2 = np.cross(e3, e1)
    return np.column_stack((e1, e2, e3))


def newtonian_energy_lie(
    positions: np.ndarray,
    velocities: np.ndarray,
    accelerations: np.ndarray,
    masses: np.ndarray,
    gravitational_constant: float,
) -> float:
    """Differentiate inertial Newtonian energy without production helpers."""

    positions = np.asarray(positions, dtype=float)
    velocities = np.asarray(velocities, dtype=float)
    accelerations = np.asarray(accelerations, dtype=float)
    masses = np.asarray(masses, dtype=float)
    kinetic_derivative = float(
        np.sum(masses[:, None] * velocities * accelerations)
    )
    potential_derivative = 0.0
    for first, second in ((0, 1), (0, 2), (1, 2)):
        displacement = positions[second] - positions[first]
        velocity = velocities[second] - velocities[first]
        potential_derivative += (
            gravitational_constant
            * masses[first]
            * masses[second]
            * float(np.dot(displacement, velocity))
            / np.linalg.norm(displacement) ** 3
        )
    return kinetic_derivative + potential_derivative


def exact_canonical_residual() -> list[list[str]]:
    m1, m2, m3 = sp.symbols("m1 m2 m3", positive=True)
    m12 = m1 + m2
    total = m12 + m3
    coordinate = sp.Matrix(
        [
            [m1 / total, m2 / total, m3 / total],
            [-1, 1, 0],
            [-m1 / m12, -m2 / m12, 1],
        ]
    )
    momentum = coordinate.inv().T
    zero = sp.zeros(3)
    transform = sp.diag(coordinate, momentum)
    symplectic = zero.row_join(sp.eye(3)).col_join((-sp.eye(3)).row_join(zero))
    residual = sp.simplify(transform * symplectic * transform.T - symplectic)
    return [[str(sp.simplify(value)) for value in row] for row in residual.tolist()]


def implementation_contract() -> dict[str, Any]:
    return {
        "imports_production": False,
        "coordinate_derivation": "direct center-of-mass and relative definitions",
        "canonical_check": "exact symbolic cotangent matrix",
    }
