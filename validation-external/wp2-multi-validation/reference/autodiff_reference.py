"""Independent JAX x64 scalar Hamiltonian for WP2-MULTIQ-v1."""

from __future__ import annotations

import jax

jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import numpy as np


def _position(q):
    a, b, c, d = q
    return jnp.array(
        [2.0 * (a * c + b * d), 2.0 * (a * d - b * c), a * a + b * b - c * c - d * d]
    )


def _jacobian(q):
    a, b, c, d = q
    return 2.0 * jnp.array(
        [[c, d, a, b], [d, -c, -b, a], [a, b, -c, -d]]
    )


def hamiltonian(z, local_masses, gravity):
    """Evaluate the independently encoded extended Hamiltonian.

    ``local_masses`` is ordered ``(m_a,m_b,m_c)`` for the active chart.
    """

    q1, q2 = z[:4], z[4:8]
    P1, P2, p_t = z[9:13], z[13:17], z[17]
    m_a, m_b, m_c = local_masses
    mu1 = m_a * m_c / (m_a + m_c)
    mu2 = m_b * m_c / (m_b + m_c)
    r1 = jnp.dot(q1, q1)
    r2 = jnp.dot(q2, q2)
    X1, X2 = _position(q1), _position(q2)
    r3 = jnp.linalg.norm(X1 - X2)
    transformed1 = _jacobian(q1) @ P1
    transformed2 = _jacobian(q2) @ P2
    kinetic1 = jnp.dot(P1, P1) / (8.0 * mu1)
    kinetic2 = jnp.dot(P2, P2) / (8.0 * mu2)
    mixed = jnp.dot(transformed1, transformed2) / (16.0 * m_c)
    return (
        r3
        * (
            r2 * (kinetic1 - gravity * m_a * m_c)
            + r1 * (kinetic2 - gravity * m_b * m_c)
            + mixed
            + p_t * r1 * r2
        )
        - gravity * m_a * m_b * r1 * r2
    )


_GRADIENT = jax.jit(jax.grad(hamiltonian, argnums=0))


def evaluate(
    z: np.ndarray,
    local_masses: np.ndarray,
    gravity: float,
) -> tuple[float, np.ndarray]:
    """Return scalar value and canonical field in production ordering."""

    vector = jnp.asarray(z, dtype=jnp.float64)
    masses = jnp.asarray(local_masses, dtype=jnp.float64)
    value = hamiltonian(vector, masses, float(gravity))
    gradient = _GRADIENT(vector, masses, float(gravity))
    field = jnp.concatenate(
        (
            gradient[9:13],
            gradient[13:17],
            gradient[17:18],
            -gradient[:4],
            -gradient[4:8],
            -gradient[8:9],
        )
    )
    return float(value), np.asarray(field, dtype=np.float64)
