"""Source-disjoint reference for WP2-SO3-LEAF-v1.

This file intentionally imports no project production module.
"""

from __future__ import annotations

import numpy as np


def quotient_to_leaf(vector: np.ndarray) -> np.ndarray:
    r, x, y, u1, u2, u3, v1, v2, v3 = np.asarray(vector, dtype=float)
    ell = np.cross([r, 0.0, 0.0], [u1, u2, u3]) + np.cross(
        [x, y, 0.0], [v1, v2, v3]
    )
    return np.array([r, x, y, u1, v1, v2, *ell])


def leaf_to_quotient(vector: np.ndarray) -> np.ndarray:
    r, x, y, pr, px, py, lx, ly, lz = np.asarray(vector, dtype=float)
    v3 = lx / y
    u3 = -(ly + x * v3) / r
    u2 = (lz - x * py + y * px) / r
    return np.array([r, x, y, pr, u2, u3, px, py, v3])


def energy(vector: np.ndarray, masses: np.ndarray, gravity: float) -> float:
    q = leaf_to_quotient(vector)
    r, x, y, u1, u2, u3, v1, v2, v3 = q
    m1, m2, m3 = np.asarray(masses, dtype=float)
    m12 = m1 + m2
    mu1 = m1 * m2 / m12
    mu2 = m3 * m12 / (m12 + m3)
    kinetic = (u1 * u1 + u2 * u2 + u3 * u3) / (2.0 * mu1)
    kinetic += (v1 * v1 + v2 * v2 + v3 * v3) / (2.0 * mu2)
    d23 = np.hypot(x - (m1 / m12) * r, y)
    d31 = np.hypot(x + (m2 / m12) * r, y)
    potential = -gravity * (
        m1 * m2 / r + m2 * m3 / d23 + m3 * m1 / d31
    )
    return float(kinetic + potential)


def finite_gradient(
    vector: np.ndarray,
    masses: np.ndarray,
    gravity: float,
    step: float = 1e-6,
) -> np.ndarray:
    vector = np.asarray(vector, dtype=float)
    result = np.empty(9)
    for index in range(9):
        scale = max(1.0, abs(float(vector[index])))
        offset = np.zeros(9)
        offset[index] = step * scale
        result[index] = (
            energy(vector + offset, masses, gravity)
            - energy(vector - offset, masses, gravity)
        ) / (2.0 * offset[index])
    return result


def poisson(vector: np.ndarray, *, reverse_body_sign: bool = False) -> np.ndarray:
    lx, ly, lz = np.asarray(vector, dtype=float)[6:]
    result = np.zeros((9, 9))
    result[:3, 3:6] = np.eye(3)
    result[3:6, :3] = -np.eye(3)
    body = np.array(
        [[0.0, -lz, ly], [lz, 0.0, -lx], [-ly, lx, 0.0]]
    )
    result[6:, 6:] = -body if reverse_body_sign else body
    return result


def finite_hamiltonian_flow(
    vector: np.ndarray,
    masses: np.ndarray,
    gravity: float,
    *,
    reverse_body_sign: bool = False,
) -> np.ndarray:
    return poisson(vector, reverse_body_sign=reverse_body_sign) @ finite_gradient(
        vector, masses, gravity
    )
