"""JAX-autodifferentiated scalar Hamiltonian reference for WP2-UP-v2."""

from __future__ import annotations

import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import numpy as np


def _position(q):
    a, b, c, d = q
    return jnp.array([2*(a*c+b*d), 2*(a*d-b*c), a*a+b*b-c*c-d*d])


def hamiltonian(z, masses, gravity, energy):
    q, lam, Q, p_lam = z[:4], z[4:7], z[7:11], z[11:14]
    m1, m2, m3 = masses
    m12 = m1 + m2
    mu12 = m1*m2/m12
    mu3 = m3*m12/(m12+m3)
    radius = jnp.dot(q, q)
    rho = _position(q)
    x23 = lam-(m1/m12)*rho
    x31 = -lam-(m2/m12)*rho
    remainder = jnp.dot(p_lam,p_lam)/(2*mu3)-gravity*m2*m3/jnp.linalg.norm(x23)-gravity*m3*m1/jnp.linalg.norm(x31)-energy
    return jnp.dot(Q,Q)/(8*mu12)-gravity*m1*m2+radius*remainder


_GRADIENT = jax.jit(jax.grad(hamiltonian, argnums=0))


def evaluate(z: np.ndarray, masses: np.ndarray, gravity: float, energy: float) -> tuple[float, np.ndarray]:
    vector = jnp.asarray(z, dtype=jnp.float64)
    mass_vector = jnp.asarray(masses, dtype=jnp.float64)
    value = hamiltonian(vector, mass_vector, float(gravity), float(energy))
    gradient = _GRADIENT(vector, mass_vector, float(gravity), float(energy))
    field = jnp.concatenate((gradient[7:], -gradient[:7]))
    return float(value), np.asarray(field, dtype=float)
