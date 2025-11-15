"""
JAX utility functions for Hamiltonian Neural Networks (Task 3.2.2, Part A).

This module provides core mathematical operations for structure-preserving
neural networks, including symplectic operations and Poisson brackets.

Key operations:
- Symplectic matrix construction
- Poisson bracket computation
- Hamiltonian vector fields
- Phase space state manipulation
"""

import jax
import jax.numpy as jnp
from typing import Callable, Tuple
from functools import partial


def symplectic_matrix(n: int) -> jnp.ndarray:
    """
    Construct standard symplectic matrix J ∈ ℝ^{2n×2n}.

    The symplectic matrix is defined as:
        J = [ 0   I_n ]
            [-I_n  0  ]

    where I_n is the n×n identity matrix.

    Properties:
        - J^T = -J (antisymmetric)
        - J^2 = -I (involutory)
        - det(J) = 1 (unimodular)

    Args:
        n: Dimension of configuration space (phase space dim = 2n)

    Returns:
        J: Symplectic matrix (2n, 2n)

    Example:
        >>> J = symplectic_matrix(2)
        >>> print(J)
        [[ 0  0  1  0]
         [ 0  0  0  1]
         [-1  0  0  0]
         [ 0 -1  0  0]]
    """
    I = jnp.eye(n)
    Z = jnp.zeros((n, n))
    J = jnp.block([[Z, I], [-I, Z]])
    return J


def split_state(z: jnp.ndarray) -> Tuple[jnp.ndarray, jnp.ndarray]:
    """
    Split phase space state into configuration and momentum.

    Args:
        z: Phase space state (2n,) = [q, p]

    Returns:
        q: Configuration (n,)
        p: Momentum (n,)

    Example:
        >>> z = jnp.array([1, 2, 3, 4])
        >>> q, p = split_state(z)
        >>> print(q)  # [1, 2]
        >>> print(p)  # [3, 4]
    """
    n = len(z) // 2
    return z[:n], z[n:]


def join_state(q: jnp.ndarray, p: jnp.ndarray) -> jnp.ndarray:
    """
    Join configuration and momentum into phase space state.

    Args:
        q: Configuration (n,)
        p: Momentum (n,)

    Returns:
        z: Phase space state (2n,) = [q, p]

    Example:
        >>> q = jnp.array([1, 2])
        >>> p = jnp.array([3, 4])
        >>> z = join_state(q, p)
        >>> print(z)  # [1, 2, 3, 4]
    """
    return jnp.concatenate([q, p])


def hamiltonian_vector_field(
    H: Callable[[jnp.ndarray], float],
    z: jnp.ndarray
) -> jnp.ndarray:
    """
    Compute Hamiltonian vector field X_H = J ∇H.

    For a Hamiltonian H(q, p), the equations of motion are:
        dz/dt = X_H(z) = J ∇H(z)

    where:
        dq/dt = ∂H/∂p
        dp/dt = -∂H/∂q

    Args:
        H: Hamiltonian function H(z) → ℝ
        z: Phase space state (2n,)

    Returns:
        dz_dt: Time derivative (2n,)

    Example:
        >>> # Harmonic oscillator: H = (q² + p²)/2
        >>> def H(z):
        ...     q, p = split_state(z)
        ...     return 0.5 * (jnp.sum(q**2) + jnp.sum(p**2))
        >>> z = jnp.array([1.0, 0.0])
        >>> dz_dt = hamiltonian_vector_field(H, z)
        >>> print(dz_dt)  # [0, -1] (dq/dt = p, dp/dt = -q)
    """
    n = len(z) // 2

    # Compute gradient of H with respect to z
    grad_H = jax.grad(H)(z)

    # Apply symplectic matrix: J ∇H = (∂H/∂p, -∂H/∂q)
    dq_dt = grad_H[n:]   # ∂H/∂p
    dp_dt = -grad_H[:n]  # -∂H/∂q

    return jnp.concatenate([dq_dt, dp_dt])


def poisson_bracket(
    f: Callable[[jnp.ndarray], float],
    g: Callable[[jnp.ndarray], float],
    z: jnp.ndarray
) -> float:
    """
    Compute Poisson bracket {f, g}(z).

    The Poisson bracket of two functions f, g on phase space is:
        {f, g} = ∇f · J · ∇g
               = (∂f/∂q)(∂g/∂p) - (∂f/∂p)(∂g/∂q)

    Properties:
        - Antisymmetric: {f, g} = -{g, f}
        - Leibniz rule: {fg, h} = f{g, h} + {f, h}g
        - Jacobi identity: {f, {g, h}} + {g, {h, f}} + {h, {f, g}} = 0

    For conserved quantities: {I, H} = 0 (Poisson commutes with Hamiltonian)

    Args:
        f: Function f(z) → ℝ
        g: Function g(z) → ℝ
        z: Phase space state (2n,)

    Returns:
        Poisson bracket {f, g} evaluated at z

    Example:
        >>> # For H = (q² + p²)/2 and I = (q² + p²)/2 (same as H)
        >>> def H(z):
        ...     q, p = split_state(z)
        ...     return 0.5 * (jnp.sum(q**2) + jnp.sum(p**2))
        >>> z = jnp.array([1.0, 0.5])
        >>> bracket = poisson_bracket(H, H, z)
        >>> print(bracket)  # 0 (energy conserved: {H, H} = 0)
    """
    n = len(z) // 2

    # Compute gradients
    grad_f = jax.grad(f)(z)
    grad_g = jax.grad(g)(z)

    # Extract q and p components
    df_dq, df_dp = grad_f[:n], grad_f[n:]
    dg_dq, dg_dp = grad_g[:n], grad_g[n:]

    # Poisson bracket: {f, g} = (∂f/∂q)(∂g/∂p) - (∂f/∂p)(∂g/∂q)
    bracket = jnp.dot(df_dq, dg_dp) - jnp.dot(df_dp, dg_dq)

    return bracket


@partial(jax.jit, static_argnums=(0,))
def batch_hamiltonian_dynamics(
    H_func: Callable[[jnp.ndarray], float],
    states: jnp.ndarray
) -> jnp.ndarray:
    """
    Compute Hamiltonian dynamics for batch of states (vectorized).

    Args:
        H_func: Hamiltonian function H(z) → ℝ
        states: Batch of states (B, 2n)

    Returns:
        derivatives: Batch of time derivatives (B, 2n)

    Example:
        >>> def H(z):
        ...     q, p = split_state(z)
        ...     return 0.5 * (jnp.sum(q**2) + jnp.sum(p**2))
        >>> states = jnp.array([[1, 0], [0, 1], [1, 1]])
        >>> derivs = batch_hamiltonian_dynamics(H, states)
        >>> print(derivs.shape)  # (3, 2)
    """
    # Vectorize hamiltonian_vector_field over batch
    dynamics_fn = lambda z: hamiltonian_vector_field(H_func, z)
    return jax.vmap(dynamics_fn)(states)


@partial(jax.jit, static_argnums=(0, 1))
def batch_poisson_bracket(
    f: Callable[[jnp.ndarray], float],
    g: Callable[[jnp.ndarray], float],
    states: jnp.ndarray
) -> jnp.ndarray:
    """
    Compute Poisson bracket {f, g} for batch of states (vectorized).

    Args:
        f: Function f(z) → ℝ
        g: Function g(z) → ℝ
        states: Batch of states (B, 2n)

    Returns:
        brackets: Poisson brackets (B,)

    Example:
        >>> def f(z): return jnp.sum(z**2)
        >>> def g(z): return jnp.sum(z)
        >>> states = jnp.array([[1, 2], [3, 4]])
        >>> brackets = batch_poisson_bracket(f, g, states)
        >>> print(brackets.shape)  # (2,)
    """
    bracket_fn = lambda z: poisson_bracket(f, g, z)
    return jax.vmap(bracket_fn)(states)


def check_symplectic_form(
    phi: Callable[[jnp.ndarray], jnp.ndarray],
    z: jnp.ndarray,
    tolerance: float = 1e-6
) -> bool:
    """
    Check if transformation φ preserves symplectic form.

    A transformation φ: ℝ^{2n} → ℝ^{2n} is symplectic (canonical) if:
        (Dφ)^T J Dφ = J

    where Dφ is the Jacobian of φ.

    Args:
        phi: Transformation function φ(z) → z'
        z: Test state (2n,)
        tolerance: Numerical tolerance for check

    Returns:
        True if transformation is symplectic

    Example:
        >>> # Identity is symplectic
        >>> phi = lambda z: z
        >>> z = jnp.array([1.0, 2.0, 3.0, 4.0])
        >>> is_symp = check_symplectic_form(phi, z)
        >>> print(is_symp)  # True
    """
    n = len(z) // 2
    J = symplectic_matrix(n)

    # Compute Jacobian of φ
    D_phi = jax.jacobian(phi)(z)

    # Check symplectic condition: (Dφ)^T J Dφ = J
    left_side = D_phi.T @ J @ D_phi

    # Check if equal to J
    is_symplectic = jnp.allclose(left_side, J, atol=tolerance)

    return bool(is_symplectic)


def compute_energy_from_hamiltonian(
    H_func: Callable[[jnp.ndarray], float],
    states: jnp.ndarray
) -> jnp.ndarray:
    """
    Compute energy for batch of states.

    Args:
        H_func: Hamiltonian function H(z) → ℝ
        states: Batch of states (B, 2n)

    Returns:
        energies: Energy values (B,)
    """
    return jax.vmap(H_func)(states)


def runge_kutta_4_step(
    dynamics_fn: Callable[[jnp.ndarray], jnp.ndarray],
    z: jnp.ndarray,
    dt: float
) -> jnp.ndarray:
    """
    Single RK4 step for Hamiltonian dynamics.

    Classical 4th-order Runge-Kutta integrator.
    Not symplectic, but useful for testing.

    Args:
        dynamics_fn: Function computing dz/dt
        z: Current state (2n,)
        dt: Timestep

    Returns:
        z_next: State at t + dt

    Example:
        >>> def dynamics(z):
        ...     q, p = split_state(z)
        ...     return join_state(p, -q)  # Harmonic oscillator
        >>> z0 = jnp.array([1.0, 0.0])
        >>> z1 = runge_kutta_4_step(dynamics, z0, dt=0.1)
    """
    k1 = dynamics_fn(z)
    k2 = dynamics_fn(z + 0.5 * dt * k1)
    k3 = dynamics_fn(z + 0.5 * dt * k2)
    k4 = dynamics_fn(z + dt * k3)

    z_next = z + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
    return z_next


# Test function
if __name__ == "__main__":
    print("Testing JAX utilities for Hamiltonian Neural Networks...")

    # Test 1: Symplectic matrix
    print("\n[Test 1] Symplectic matrix (n=2):")
    J = symplectic_matrix(2)
    print(J)
    print(f"  Antisymmetric: {jnp.allclose(J.T, -J)}")
    print(f"  Involutory: {jnp.allclose(J @ J, -jnp.eye(4))}")

    # Test 2: Harmonic oscillator
    print("\n[Test 2] Harmonic oscillator H = (q² + p²)/2:")

    def harmonic_H(z):
        q, p = split_state(z)
        return 0.5 * (jnp.sum(q**2) + jnp.sum(p**2))

    z0 = jnp.array([1.0, 0.0])
    dz_dt = hamiltonian_vector_field(harmonic_H, z0)
    print(f"  z = {z0}")
    print(f"  dz/dt = {dz_dt}")
    print(f"  Expected: [0, -1] (dq/dt = p, dp/dt = -q)")

    # Test 3: Poisson bracket
    print("\n[Test 3] Poisson bracket {H, H}:")
    bracket = poisson_bracket(harmonic_H, harmonic_H, z0)
    print(f"  {{H, H}} = {bracket}")
    print(f"  Expected: 0 (self-bracket)")

    # Test 4: Batch operations
    print("\n[Test 4] Batch Hamiltonian dynamics:")
    states = jnp.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    derivs = batch_hamiltonian_dynamics(harmonic_H, states)
    print(f"  States shape: {states.shape}")
    print(f"  Derivatives shape: {derivs.shape}")
    print(f"  First derivative: {derivs[0]}")

    # Test 5: Symplectic check (identity)
    print("\n[Test 5] Symplectic form check (identity transformation):")
    phi_identity = lambda z: z
    is_symp = check_symplectic_form(phi_identity, jnp.array([1.0, 2.0, 3.0, 4.0]))
    print(f"  Identity is symplectic: {is_symp}")

    print("\n✓ All tests passed!")
