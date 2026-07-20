"""Independent formula implementation for WP2-UP-v1 qualification."""

from __future__ import annotations

import numpy as np


def _ks_position(q: np.ndarray) -> np.ndarray:
    a, b, c, d = q
    return np.array([2 * (a * c + b * d), 2 * (a * d - b * c), a*a + b*b - c*c - d*d])


def _ks_jacobian(q: np.ndarray) -> np.ndarray:
    a, b, c, d = q
    return 2 * np.array([[c, d, a, b], [d, -c, -b, a], [a, b, -c, -d]])


def project(z: np.ndarray) -> np.ndarray:
    q, lam, Q, p_lam = z[:4], z[4:7], z[7:11], z[11:14]
    radius = float(q @ q)
    rho = _ks_position(q)
    p_rho = _ks_jacobian(q) @ Q / (4 * radius)
    return np.concatenate((rho, lam, p_rho, p_lam))


def evaluate(z: np.ndarray, masses: np.ndarray, gravity: float, energy: float) -> tuple[float, np.ndarray]:
    q, lam, Q, p_lam = z[:4], z[4:7], z[7:11], z[11:14]
    m1, m2, m3 = (float(value) for value in masses)
    m12 = m1 + m2
    total = m12 + m3
    mu12 = m1 * m2 / m12
    mu3 = m3 * m12 / total
    radius = float(q @ q)
    rho = _ks_position(q)
    x23 = lam - (m1 / m12) * rho
    x31 = -lam - (m2 / m12) * rho
    r23 = float(np.linalg.norm(x23))
    r31 = float(np.linalg.norm(x31))
    k12, k23, k31 = gravity*m1*m2, gravity*m2*m3, gravity*m3*m1
    remainder = float(p_lam @ p_lam) / (2*mu3) - k23/r23 - k31/r31 - energy
    hamiltonian = float(Q @ Q) / (8*mu12) - k12 + radius*remainder
    f23 = k23*x23/r23**3
    f31 = k31*x31/r31**3
    grad_rho = -(m1/m12)*f23 - (m2/m12)*f31
    grad_lam = f23 - f31
    q_dot = Q/(4*mu12)
    lam_dot = radius*p_lam/mu3
    Q_dot = -2*q*remainder - radius*_ks_jacobian(q).T@grad_rho
    p_lam_dot = -radius*grad_lam
    return hamiltonian, np.concatenate((q_dot, lam_dot, Q_dot, p_lam_dot))
