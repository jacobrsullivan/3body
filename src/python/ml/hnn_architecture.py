"""
Hamiltonian Neural Network architecture (Task 3.2.2, Part B).

This module implements Hamiltonian Neural Networks (HNNs) that learn
scalar Hamiltonian functions H(q, p) and generate symplectic dynamics
via automatic differentiation.

Key idea: Instead of directly predicting dz/dt, learn H(z) such that
    dz/dt = J ∇H(z)
This automatically preserves the symplectic structure.

References:
- Greydanus et al., "Hamiltonian Neural Networks" (2019)
- Toth et al., "Hamiltonian Generative Networks" (2020)
"""

import jax
import jax.numpy as jnp
from flax import linen as nn
from typing import Sequence, Callable, Tuple, Optional
from functools import partial

from .jax_utils import split_state, join_state, hamiltonian_vector_field


class HamiltonianNN(nn.Module):
    """
    Hamiltonian Neural Network.

    Learns scalar Hamiltonian H_θ(z) where z = (q, p).
    Dynamics are then dz/dt = J ∇H_θ(z), automatically preserving
    symplectic structure.

    Architecture:
        Input: z ∈ ℝ^{2n}
        ↓
        Hidden layers: MLP with smooth activations
        ↓
        Output: H ∈ ℝ (scalar energy)

    Attributes:
        hidden_dims: Sizes of hidden layers
        activation: Activation function ('tanh', 'softplus', 'gelu')
        use_layer_norm: Whether to use layer normalization
        use_bias: Whether to use bias in output layer
    """

    hidden_dims: Sequence[int] = (256, 256, 128, 64)
    activation: str = 'tanh'
    use_layer_norm: bool = False
    use_bias: bool = True

    @nn.compact
    def __call__(self, z: jnp.ndarray) -> jnp.ndarray:
        """
        Forward pass: compute H(z).

        Args:
            z: Phase space state (2n,)

        Returns:
            H: Scalar Hamiltonian value

        Example:
            >>> model = HamiltonianNN()
            >>> params = model.init(jax.random.PRNGKey(0), jnp.ones(4))
            >>> z = jnp.array([1.0, 2.0, 3.0, 4.0])
            >>> H = model.apply(params, z)
            >>> print(H.shape)  # () scalar
        """
        x = z

        # Hidden layers
        for i, dim in enumerate(self.hidden_dims):
            x = nn.Dense(
                dim,
                kernel_init=nn.initializers.glorot_normal(),
                bias_init=nn.initializers.zeros,
                name=f'dense_{i}'
            )(x)

            # Optional layer normalization
            if self.use_layer_norm:
                x = nn.LayerNorm(name=f'layernorm_{i}')(x)

            # Activation function
            if self.activation == 'tanh':
                x = nn.tanh(x)
            elif self.activation == 'softplus':
                x = nn.softplus(x)
            elif self.activation == 'gelu':
                x = nn.gelu(x)
            elif self.activation == 'relu':
                x = nn.relu(x)
            else:
                raise ValueError(f"Unknown activation: {self.activation}")

        # Output layer: single scalar
        H = nn.Dense(
            1,
            kernel_init=nn.initializers.glorot_normal(),
            bias_init=nn.initializers.zeros if self.use_bias else None,
            use_bias=self.use_bias,
            name='output'
        )(x)

        return jnp.squeeze(H)  # Return scalar

    def energy(self, params, z: jnp.ndarray) -> float:
        """
        Compute energy (Hamiltonian value).

        Args:
            params: Model parameters
            z: Phase space state (2n,)

        Returns:
            Energy value
        """
        return self.apply(params, z)

    def dynamics(self, params, z: jnp.ndarray) -> jnp.ndarray:
        """
        Compute time derivative dz/dt = J ∇H.

        This is the key method: it computes Hamiltonian dynamics
        via automatic differentiation of the learned Hamiltonian.

        Args:
            params: Model parameters
            z: Phase space state (2n,)

        Returns:
            dz_dt: Time derivative (2n,)

        Example:
            >>> model = HamiltonianNN()
            >>> params = model.init(jax.random.PRNGKey(0), jnp.ones(4))
            >>> z = jnp.array([1.0, 0.0, 0.0, 0.0])
            >>> dz_dt = model.dynamics(params, z)
            >>> print(dz_dt.shape)  # (4,)
        """
        H_func = lambda state: self.apply(params, state)
        return hamiltonian_vector_field(H_func, z)

    def batch_dynamics(self, params, states: jnp.ndarray) -> jnp.ndarray:
        """
        Compute dynamics for batch of states.

        Args:
            params: Model parameters
            states: Batch of states (B, 2n)

        Returns:
            derivatives: Batch of derivatives (B, 2n)
        """
        dynamics_fn = lambda z: self.dynamics(params, z)
        return jax.vmap(dynamics_fn)(states)

    def batch_energy(self, params, states: jnp.ndarray) -> jnp.ndarray:
        """
        Compute energy for batch of states.

        Args:
            params: Model parameters
            states: Batch of states (B, 2n)

        Returns:
            energies: Energy values (B,)
        """
        energy_fn = lambda z: self.energy(params, z)
        return jax.vmap(energy_fn)(states)


class SeparableHNN(nn.Module):
    """
    Separable Hamiltonian Neural Network.

    Assumes H(q, p) = T(p) + V(q) where:
    - T(p) is kinetic energy (function of momenta only)
    - V(q) is potential energy (function of positions only)

    This is a stronger inductive bias than general HNN, but often
    more sample-efficient for mechanical systems.

    Architecture:
        Input: z = (q, p)
        ↓
        Split: q, p
        ↓
        T(p) ←─── MLP ───→ V(q)
        ↓
        H = T + V

    Attributes:
        hidden_dims: Sizes of hidden layers (shared between T and V networks)
        activation: Activation function
    """

    hidden_dims: Sequence[int] = (128, 128, 64)
    activation: str = 'tanh'

    @nn.compact
    def __call__(self, z: jnp.ndarray) -> jnp.ndarray:
        """Compute H(q, p) = T(p) + V(q)."""
        q, p = split_state(z)

        # Kinetic energy network: T(p)
        T = self._kinetic_network(p)

        # Potential energy network: V(q)
        V = self._potential_network(q)

        return T + V

    def _kinetic_network(self, p: jnp.ndarray) -> jnp.ndarray:
        """
        Learn kinetic energy T(p).

        For standard mechanics: T(p) = p^T M^{-1} p / 2
        But we allow network to learn more general form.

        Args:
            p: Momentum (n,)

        Returns:
            T: Kinetic energy (scalar)
        """
        x = p
        for i, dim in enumerate(self.hidden_dims):
            x = nn.Dense(dim, name=f'kinetic_dense_{i}')(x)
            x = nn.tanh(x) if self.activation == 'tanh' else nn.softplus(x)

        T = nn.Dense(1, name='kinetic_output')(x)
        return jnp.squeeze(T)

    def _potential_network(self, q: jnp.ndarray) -> jnp.ndarray:
        """
        Learn potential energy V(q).

        Args:
            q: Configuration (n,)

        Returns:
            V: Potential energy (scalar)
        """
        x = q
        for i, dim in enumerate(self.hidden_dims):
            x = nn.Dense(dim, name=f'potential_dense_{i}')(x)
            x = nn.tanh(x) if self.activation == 'tanh' else nn.softplus(x)

        V = nn.Dense(1, name='potential_output')(x)
        return jnp.squeeze(V)

    def energy(self, params, z: jnp.ndarray) -> float:
        """Compute energy."""
        return self.apply(params, z)

    def dynamics(self, params, z: jnp.ndarray) -> jnp.ndarray:
        """Compute dynamics dz/dt = J ∇H."""
        H_func = lambda state: self.apply(params, state)
        return hamiltonian_vector_field(H_func, z)

    def batch_dynamics(self, params, states: jnp.ndarray) -> jnp.ndarray:
        """Compute dynamics for batch."""
        dynamics_fn = lambda z: self.dynamics(params, z)
        return jax.vmap(dynamics_fn)(states)


class ConstrainedHNN(nn.Module):
    """
    Hamiltonian Neural Network with constraints.

    For systems with constraints (e.g., fixed energy, angular momentum),
    we can enforce them via projection or Lagrange multipliers.

    This is a more advanced architecture for future use.

    Attributes:
        hidden_dims: Hidden layer sizes
        constraint_dim: Number of constraints
        activation: Activation function
    """

    hidden_dims: Sequence[int] = (256, 256, 128)
    constraint_dim: int = 1  # e.g., energy conservation
    activation: str = 'tanh'

    @nn.compact
    def __call__(self, z: jnp.ndarray) -> Tuple[jnp.ndarray, jnp.ndarray]:
        """
        Compute H(z) and constraint violations.

        Returns:
            H: Hamiltonian value
            constraints: Constraint violations (constraint_dim,)
        """
        # Main Hamiltonian network
        x = z
        for i, dim in enumerate(self.hidden_dims):
            x = nn.Dense(dim, name=f'dense_{i}')(x)
            x = nn.tanh(x)

        H = nn.Dense(1, name='hamiltonian')(x)
        H = jnp.squeeze(H)

        # Constraint network (learns constraint violations)
        c = nn.Dense(self.constraint_dim, name='constraints')(x)

        return H, c


def create_hnn_model(
    state_dim: int,
    hidden_dims: Sequence[int] = (256, 256, 128),
    separable: bool = False,
    activation: str = 'tanh',
    use_layer_norm: bool = False,
    seed: int = 42
) -> Tuple[nn.Module, any]:
    """
    Factory function to create and initialize HNN.

    Args:
        state_dim: Dimension of phase space (must be even)
        hidden_dims: Hidden layer sizes
        separable: Use separable H = T + V form
        activation: Activation function
        use_layer_norm: Use layer normalization
        seed: Random seed for initialization

    Returns:
        model: Flax model instance
        params: Initialized parameters

    Example:
        >>> model, params = create_hnn_model(state_dim=4, hidden_dims=(64, 64))
        >>> z = jnp.ones(4)
        >>> H = model.apply(params, z)
        >>> print(H)  # Scalar energy value
    """
    assert state_dim % 2 == 0, "Phase space dimension must be even"

    # Create model
    if separable:
        model = SeparableHNN(hidden_dims=hidden_dims, activation=activation)
    else:
        model = HamiltonianNN(
            hidden_dims=hidden_dims,
            activation=activation,
            use_layer_norm=use_layer_norm
        )

    # Initialize parameters
    rng = jax.random.PRNGKey(seed)
    dummy_input = jnp.ones(state_dim)
    params = model.init(rng, dummy_input)

    return model, params


def count_parameters(params) -> int:
    """
    Count total trainable parameters.

    Args:
        params: Model parameters (PyTree)

    Returns:
        Total number of parameters
    """
    return sum(x.size for x in jax.tree_util.tree_leaves(params))


# Test code
if __name__ == "__main__":
    print("Testing Hamiltonian Neural Network architecture...")

    # Test 1: Create HNN
    print("\n[Test 1] Create HNN model:")
    model, params = create_hnn_model(state_dim=4, hidden_dims=(32, 32), seed=0)
    n_params = count_parameters(params)
    print(f"  State dim: 4")
    print(f"  Hidden dims: (32, 32)")
    print(f"  Total parameters: {n_params:,}")

    # Test 2: Forward pass
    print("\n[Test 2] Forward pass (energy):")
    z = jnp.array([1.0, 0.5, -0.5, 1.0])
    H = model.apply(params, z)
    print(f"  Input: {z}")
    print(f"  Hamiltonian: {H:.6f}")
    print(f"  Type: {type(H)}, Shape: {H.shape}")

    # Test 3: Dynamics
    print("\n[Test 3] Hamiltonian dynamics:")
    dz_dt = model.dynamics(params, z)
    print(f"  dz/dt: {dz_dt}")
    print(f"  Shape: {dz_dt.shape}")

    # Test 4: Batch operations
    print("\n[Test 4] Batch operations:")
    states = jnp.array([[1.0, 0.0, 0.0, 0.0],
                        [0.0, 1.0, 0.0, 0.0],
                        [0.0, 0.0, 1.0, 0.0]])
    energies = model.batch_energy(params, states)
    dynamics = model.batch_dynamics(params, states)
    print(f"  Batch size: {states.shape[0]}")
    print(f"  Energies: {energies}")
    print(f"  Dynamics shape: {dynamics.shape}")

    # Test 5: Separable HNN
    print("\n[Test 5] Separable HNN (H = T + V):")
    sep_model, sep_params = create_hnn_model(
        state_dim=4,
        hidden_dims=(32, 32),
        separable=True,
        seed=1
    )
    H_sep = sep_model.apply(sep_params, z)
    dz_dt_sep = sep_model.dynamics(sep_params, z)
    print(f"  Hamiltonian: {H_sep:.6f}")
    print(f"  Dynamics: {dz_dt_sep}")
    print(f"  Parameters: {count_parameters(sep_params):,}")

    # Test 6: Gradient check
    print("\n[Test 6] Gradient computation:")
    grad_fn = jax.grad(lambda p: model.apply(p, z))
    grads = grad_fn(params)
    total_grad_norm = jnp.sqrt(sum(jnp.sum(g**2) for g in jax.tree_util.tree_leaves(grads)))
    print(f"  Gradient norm: {total_grad_norm:.6f}")
    print(f"  Gradients computable: ✓")

    print("\n✓ All tests passed!")
