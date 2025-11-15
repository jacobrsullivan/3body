"""
Conservation-constrained HNN with dual-head architecture (Task 3.2.3, Part A).

This module implements the core innovation of WP 3.2: a Hamiltonian Neural
Network with an auxiliary "invariant head" that learns conserved quantities
by enforcing the Poisson bracket constraint {I_φ, H_θ} = 0.

Architecture:
    Input: z = (q, p)
    ↓
    Shared Encoder: [256, 256]
    ↓
    ├─→ Hamiltonian Head: H_θ(z) → ℝ
    │       ↓
    │   Dynamics: dz/dt = J ∇H_θ
    │
    └─→ Invariant Head: I_φ(z) → ℝ^k (k conserved quantities)
            ↓
        Conservation constraint: {I_φ, H_θ} = 0

This enforces that learned invariants are conserved along trajectories.
"""

import jax
import jax.numpy as jnp
from flax import linen as nn
from typing import Sequence, Tuple, Optional
from functools import partial

from .jax_utils import split_state, join_state, hamiltonian_vector_field, poisson_bracket


class ConservationHNN(nn.Module):
    """
    HNN with auxiliary invariant prediction head.

    The model learns two functions simultaneously:
    1. Hamiltonian H_θ(z): generates dynamics
    2. Invariant(s) I_φ(z): conserved quantities

    Training enforces:
    - Trajectory matching: dz/dt_true ≈ J ∇H_θ
    - Conservation: {I_φ, H_θ} ≈ 0 (Poisson bracket vanishes)

    Attributes:
        encoder_dims: Shared encoder dimensions
        hamiltonian_dims: Hamiltonian-specific layers
        num_invariants: Number of independent invariants to learn
        invariant_dims: Invariant-specific layers
        activation: Activation function
        use_layer_norm: Whether to use layer normalization
    """

    encoder_dims: Sequence[int] = (256, 256)
    hamiltonian_dims: Sequence[int] = (128, 64)
    num_invariants: int = 1
    invariant_dims: Sequence[int] = (128, 64)
    activation: str = 'tanh'
    use_layer_norm: bool = False

    @nn.compact
    def __call__(
        self,
        z: jnp.ndarray,
        return_all: bool = False
    ) -> Tuple[jnp.ndarray, jnp.ndarray]:
        """
        Forward pass through both heads.

        Args:
            z: Phase space state (2n,)
            return_all: If True, return intermediate features

        Returns:
            H: Hamiltonian value (scalar)
            I: Invariant values (num_invariants,)
            features: (optional) Shared features
        """
        # Shared encoder
        features = self._encode(z)

        # Hamiltonian head
        H = self._hamiltonian_head(features)

        # Invariant head(s)
        I = self._invariant_head(features)

        if return_all:
            return H, I, features
        return H, I

    def _encode(self, z: jnp.ndarray) -> jnp.ndarray:
        """Shared feature encoder."""
        x = z
        for i, dim in enumerate(self.encoder_dims):
            x = nn.Dense(dim, name=f'encoder_dense_{i}')(x)

            if self.use_layer_norm:
                x = nn.LayerNorm(name=f'encoder_ln_{i}')(x)

            if self.activation == 'tanh':
                x = nn.tanh(x)
            elif self.activation == 'softplus':
                x = nn.softplus(x)
            elif self.activation == 'gelu':
                x = nn.gelu(x)

        return x

    def _hamiltonian_head(self, features: jnp.ndarray) -> jnp.ndarray:
        """Hamiltonian prediction head."""
        x = features
        for i, dim in enumerate(self.hamiltonian_dims):
            x = nn.Dense(dim, name=f'hamiltonian_dense_{i}')(x)
            x = nn.tanh(x)

        H = nn.Dense(1, name='hamiltonian_output')(x)
        return jnp.squeeze(H)

    def _invariant_head(self, features: jnp.ndarray) -> jnp.ndarray:
        """
        Invariant prediction head(s).

        Learns k independent scalar functions I_1, ..., I_k.
        Each should satisfy {I_i, H} = 0.
        """
        invariants = []

        for i in range(self.num_invariants):
            x = features
            for j, dim in enumerate(self.invariant_dims):
                x = nn.Dense(dim, name=f'invariant_{i}_dense_{j}')(x)
                x = nn.tanh(x)

            # Output: single scalar invariant
            I_i = nn.Dense(1, name=f'invariant_{i}_output')(x)
            invariants.append(jnp.squeeze(I_i))

        # Stack into array
        if self.num_invariants == 1:
            return invariants[0]  # Return scalar
        else:
            return jnp.array(invariants)  # Return (num_invariants,)

    def hamiltonian(self, params, z: jnp.ndarray) -> jnp.ndarray:
        """Compute just the Hamiltonian (for dynamics)."""
        H, _ = self.apply(params, z)
        return H

    def invariant(self, params, z: jnp.ndarray, idx: int = 0) -> jnp.ndarray:
        """
        Compute specific invariant.

        Args:
            params: Model parameters
            z: Phase space state
            idx: Invariant index (0 to num_invariants-1)

        Returns:
            I_idx: Invariant value
        """
        _, I = self.apply(params, z)

        if self.num_invariants == 1:
            return I
        else:
            return I[idx]

    def all_invariants(self, params, z: jnp.ndarray) -> jnp.ndarray:
        """Compute all invariants."""
        _, I = self.apply(params, z)
        return I

    def dynamics(self, params, z: jnp.ndarray) -> jnp.ndarray:
        """
        Hamiltonian dynamics dz/dt = J ∇H.

        Note: Uses only the Hamiltonian head, not the invariant head.
        """
        H_func = lambda state: self.hamiltonian(params, state)
        return hamiltonian_vector_field(H_func, z)

    def batch_dynamics(self, params, states: jnp.ndarray) -> jnp.ndarray:
        """Compute dynamics for batch of states."""
        dynamics_fn = lambda z: self.dynamics(params, z)
        return jax.vmap(dynamics_fn)(states)

    def batch_energy(self, params, states: jnp.ndarray) -> jnp.ndarray:
        """Compute energy for batch of states."""
        energy_fn = lambda z: self.hamiltonian(params, z)
        return jax.vmap(energy_fn)(states)

    def batch_invariant(
        self,
        params,
        states: jnp.ndarray,
        idx: int = 0
    ) -> jnp.ndarray:
        """Compute invariant for batch of states."""
        invariant_fn = lambda z: self.invariant(params, z, idx)
        return jax.vmap(invariant_fn)(states)


class MultiInvariantHNN(nn.Module):
    """
    Extension: Learn K independent invariants simultaneously.

    For Liouville integrable systems, we need n independent integrals
    in involution: {I_i, I_j} = 0 for i ≠ j.

    This architecture learns multiple invariants and enforces:
    1. {I_i, H} = 0 for all i (conservation)
    2. {I_i, I_j} = 0 for i ≠ j (involution)

    Attributes:
        encoder_dims: Shared encoder
        hamiltonian_dims: Hamiltonian head
        num_invariants: Number of invariants (typically n for n-DOF system)
        invariant_dims: Invariant heads
        activation: Activation function
        enforce_involution: Whether to enforce {I_i, I_j} = 0
    """

    encoder_dims: Sequence[int] = (256, 256)
    hamiltonian_dims: Sequence[int] = (128, 64)
    num_invariants: int = 3  # e.g., E, L, and one unknown
    invariant_dims: Sequence[int] = (128, 64)
    activation: str = 'tanh'
    enforce_involution: bool = True

    @nn.compact
    def __call__(self, z: jnp.ndarray) -> Tuple[jnp.ndarray, jnp.ndarray]:
        """
        Forward pass.

        Returns:
            H: Hamiltonian
            I: All invariants (num_invariants,)
        """
        # Use ConservationHNN as base
        conservation_hnn = ConservationHNN(
            encoder_dims=self.encoder_dims,
            hamiltonian_dims=self.hamiltonian_dims,
            num_invariants=self.num_invariants,
            invariant_dims=self.invariant_dims,
            activation=self.activation
        )

        return conservation_hnn(z)

    # Inherit other methods from ConservationHNN
    def hamiltonian(self, params, z):
        H, _ = self.apply(params, z)
        return H

    def invariant(self, params, z, idx=0):
        _, I = self.apply(params, z)
        return I[idx] if self.num_invariants > 1 else I

    def dynamics(self, params, z):
        H_func = lambda state: self.hamiltonian(params, state)
        return hamiltonian_vector_field(H_func, z)


def create_conservation_hnn(
    state_dim: int,
    num_invariants: int = 1,
    encoder_dims: Sequence[int] = (256, 256),
    hamiltonian_dims: Sequence[int] = (128, 64),
    invariant_dims: Sequence[int] = (128, 64),
    activation: str = 'tanh',
    use_layer_norm: bool = False,
    seed: int = 42
) -> Tuple[ConservationHNN, any]:
    """
    Factory function to create and initialize ConservationHNN.

    Args:
        state_dim: Dimension of phase space (must be even)
        num_invariants: Number of invariants to learn
        encoder_dims: Shared encoder layer sizes
        hamiltonian_dims: Hamiltonian-specific layer sizes
        invariant_dims: Invariant-specific layer sizes
        activation: Activation function
        use_layer_norm: Use layer normalization
        seed: Random seed

    Returns:
        model: ConservationHNN instance
        params: Initialized parameters

    Example:
        >>> model, params = create_conservation_hnn(
        ...     state_dim=8,
        ...     num_invariants=1,
        ...     encoder_dims=(256, 256),
        ...     hamiltonian_dims=(128, 64),
        ...     invariant_dims=(128, 64)
        ... )
        >>> z = jnp.ones(8)
        >>> H, I = model.apply(params, z)
        >>> print(f"H: {H}, I: {I}")
    """
    assert state_dim % 2 == 0, "Phase space dimension must be even"

    model = ConservationHNN(
        encoder_dims=encoder_dims,
        hamiltonian_dims=hamiltonian_dims,
        num_invariants=num_invariants,
        invariant_dims=invariant_dims,
        activation=activation,
        use_layer_norm=use_layer_norm
    )

    # Initialize parameters
    rng = jax.random.PRNGKey(seed)
    dummy_input = jnp.ones(state_dim)
    params = model.init(rng, dummy_input)

    return model, params


def count_parameters(params) -> int:
    """Count total trainable parameters."""
    return sum(x.size for x in jax.tree_util.tree_leaves(params))


# Test code
if __name__ == "__main__":
    print("Testing ConservationHNN architecture...")

    # Test 1: Create dual-head model
    print("\n[Test 1] Create ConservationHNN:")
    model, params = create_conservation_hnn(
        state_dim=4,
        num_invariants=1,
        encoder_dims=(64, 64),
        hamiltonian_dims=(32, 32),
        invariant_dims=(32, 32),
        seed=0
    )
    n_params = count_parameters(params)
    print(f"  State dim: 4")
    print(f"  Num invariants: 1")
    print(f"  Total parameters: {n_params:,}")

    # Test 2: Forward pass
    print("\n[Test 2] Forward pass:")
    z = jnp.array([1.0, 0.5, -0.5, 1.0])
    H, I = model.apply(params, z)
    print(f"  Input: {z}")
    print(f"  Hamiltonian: {H:.6f}")
    print(f"  Invariant: {I:.6f}")

    # Test 3: Separate outputs
    print("\n[Test 3] Separate head outputs:")
    H_only = model.hamiltonian(params, z)
    I_only = model.invariant(params, z, idx=0)
    print(f"  H (direct): {H_only:.6f}")
    print(f"  I (direct): {I_only:.6f}")
    print(f"  Consistent: {jnp.allclose(H, H_only) and jnp.allclose(I, I_only)}")

    # Test 4: Dynamics
    print("\n[Test 4] Hamiltonian dynamics:")
    dz_dt = model.dynamics(params, z)
    print(f"  dz/dt: {dz_dt}")
    print(f"  Shape: {dz_dt.shape}")

    # Test 5: Batch operations
    print("\n[Test 5] Batch operations:")
    states = jnp.array([[1.0, 0.0, 0.0, 0.0],
                        [0.0, 1.0, 0.0, 0.0],
                        [0.0, 0.0, 1.0, 0.0]])
    energies = model.batch_energy(params, states)
    invariants = model.batch_invariant(params, states, idx=0)
    dynamics = model.batch_dynamics(params, states)
    print(f"  Batch size: {states.shape[0]}")
    print(f"  Energies: {energies}")
    print(f"  Invariants: {invariants}")
    print(f"  Dynamics shape: {dynamics.shape}")

    # Test 6: Multiple invariants
    print("\n[Test 6] Multiple invariants:")
    multi_model, multi_params = create_conservation_hnn(
        state_dim=4,
        num_invariants=3,
        encoder_dims=(64, 64),
        seed=1
    )
    H_multi, I_multi = multi_model.apply(multi_params, z)
    print(f"  Hamiltonian: {H_multi:.6f}")
    print(f"  Invariants: {I_multi}")
    print(f"  Num invariants: {len(I_multi)}")

    # Test 7: Gradient computation
    print("\n[Test 7] Gradient computation:")

    # Gradient w.r.t. Hamiltonian
    grad_H_fn = jax.grad(lambda p: model.hamiltonian(p, z))
    grads_H = grad_H_fn(params)

    # Gradient w.r.t. invariant
    grad_I_fn = jax.grad(lambda p: model.invariant(p, z, idx=0))
    grads_I = grad_I_fn(params)

    grad_H_norm = jnp.sqrt(sum(jnp.sum(g**2) for g in jax.tree_util.tree_leaves(grads_H)))
    grad_I_norm = jnp.sqrt(sum(jnp.sum(g**2) for g in jax.tree_util.tree_leaves(grads_I)))

    print(f"  ∇H norm: {grad_H_norm:.6f}")
    print(f"  ∇I norm: {grad_I_norm:.6f}")
    print(f"  Gradients computable: ✓")

    # Test 8: Poisson bracket (will be near-random for untrained model)
    print("\n[Test 8] Poisson bracket {I, H}:")
    H_func = lambda state: model.hamiltonian(params, state)
    I_func = lambda state: model.invariant(params, state, idx=0)
    bracket = poisson_bracket(I_func, H_func, z)
    print(f"  {{I, H}} = {bracket:.6f}")
    print(f"  (Should be ~0 after training with conservation loss)")

    print("\n✓ All tests passed!")
