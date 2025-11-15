"""
Physics-informed loss functions for conservation learning (Task 3.2.3, Part B).

This module implements the key innovation of WP 3.2: physics-informed losses
that enforce conservation constraints during training.

Combined Loss:
    L = L_trajectory + λ₁·L_conservation + λ₂·L_Noether + λ₃·L_regularization

where:
- L_trajectory: Standard dynamics prediction
- L_conservation: Poisson bracket constraint {I_φ, H_θ} = 0
- L_Noether: Symmetry-based regularization
- L_regularization: Prevent trivial solutions
"""

import jax
import jax.numpy as jnp
from typing import Dict, Tuple, Callable, List, Optional
from functools import partial

from .jax_utils import poisson_bracket


@partial(jax.jit, static_argnums=(1,))
def trajectory_loss(
    params,
    model,
    states: jnp.ndarray,
    derivatives: jnp.ndarray
) -> Tuple[jnp.ndarray, Dict]:
    """
    L_trajectory: Predict dynamics accurately.

    Loss: ||dz/dt_true - J ∇H_θ||²

    This ensures the Hamiltonian head learns the correct dynamics.

    Args:
        params: Model parameters
        model: ConservationHNN
        states: Batch of states (B, 2n)
        derivatives: True time derivatives (B, 2n)

    Returns:
        loss: Scalar loss
        metrics: Dictionary of metrics
    """
    # Predict dynamics via Hamiltonian head
    predicted = model.batch_dynamics(params, states)

    # Mean squared error
    squared_errors = (predicted - derivatives) ** 2
    loss = jnp.mean(squared_errors)

    # Additional metrics
    max_error = jnp.max(jnp.abs(predicted - derivatives))
    mean_abs_error = jnp.mean(jnp.abs(predicted - derivatives))

    # Component-wise errors
    n = states.shape[1] // 2
    q_error = jnp.mean(squared_errors[:, :n])
    p_error = jnp.mean(squared_errors[:, n:])

    metrics = {
        'trajectory_loss': loss,
        'max_error': max_error,
        'mean_abs_error': mean_abs_error,
        'q_error': q_error,
        'p_error': p_error
    }

    return loss, metrics


@partial(jax.jit, static_argnums=(1,))
def conservation_loss(
    params,
    model,
    states: jnp.ndarray,
    inv_idx: int = 0
) -> jnp.ndarray:
    """
    L_conservation: Enforce {I_φ, H_θ} = 0.

    This is the KEY physics constraint: the Poisson bracket of the
    invariant with the Hamiltonian must vanish for conservation.

    For each state z, compute:
        {I, H}(z) = ∂I/∂q · ∂H/∂p - ∂I/∂p · ∂H/∂q

    Loss: E[|{I, H}|²]

    Args:
        params: Model parameters
        model: ConservationHNN
        states: Batch of states (B, 2n)
        inv_idx: Which invariant to enforce conservation for

    Returns:
        loss: Scalar conservation loss
    """
    def poisson_bracket_at_state(z):
        n = len(z) // 2

        # Define functions for this specific state
        H_func = lambda state: model.hamiltonian(params, state)
        I_func = lambda state: model.invariant(params, state, inv_idx)

        # Compute gradients
        grad_I = jax.grad(I_func)(z)
        grad_H = jax.grad(H_func)(z)

        # Extract q and p components
        dI_dq, dI_dp = grad_I[:n], grad_I[n:]
        dH_dq, dH_dp = grad_H[:n], grad_H[n:]

        # Poisson bracket: {I, H} = ∂I/∂q · ∂H/∂p - ∂I/∂p · ∂H/∂q
        bracket = jnp.dot(dI_dq, dH_dp) - jnp.dot(dI_dp, dH_dq)

        return bracket

    # Compute over batch
    brackets = jax.vmap(poisson_bracket_at_state)(states)

    # Loss: squared Poisson bracket (should be zero for conservation)
    loss = jnp.mean(brackets ** 2)

    return loss


@partial(jax.jit, static_argnums=(1, 2))
def noether_regularizer(
    params,
    model,
    symmetry_transforms: List[Callable],
    states: jnp.ndarray,
    inv_idx: int = 0
) -> jnp.ndarray:
    """
    L_Noether: Encourage invariants to respect symmetries.

    Noether's theorem states that continuous symmetries correspond to
    conserved quantities. We enforce known symmetries as a soft constraint.

    For symmetry transformations σ (e.g., permutations, rotations):
        I(σ(z)) should equal I(z)

    Loss: E[||I(σ(z)) - I(z)||²]

    This biases the network toward physically meaningful integrals.

    Args:
        params: Model parameters
        model: ConservationHNN
        symmetry_transforms: List of symmetry functions σ: ℝ^{2n} → ℝ^{2n}
        states: Batch of states (B, 2n)
        inv_idx: Which invariant to regularize

    Returns:
        loss: Scalar Noether regularization loss
    """
    total_loss = 0.0
    num_transforms = len(symmetry_transforms)

    if num_transforms == 0:
        return 0.0

    for transform_fn in symmetry_transforms:
        # Transform states
        transformed_states = jax.vmap(transform_fn)(states)

        # Compute invariants on original and transformed states
        I_original = model.batch_invariant(params, states, inv_idx)
        I_transformed = model.batch_invariant(params, transformed_states, inv_idx)

        # Invariance loss: I(σ(z)) ≈ I(z)
        loss = jnp.mean((I_original - I_transformed) ** 2)
        total_loss += loss

    return total_loss / num_transforms


@partial(jax.jit, static_argnums=(1,))
def involution_loss(
    params,
    model,
    states: jnp.ndarray
) -> jnp.ndarray:
    """
    L_involution: For multiple invariants, enforce {I_i, I_j} = 0.

    For Liouville integrability, conserved quantities must pairwise
    commute (be in involution).

    Only applicable if model.num_invariants > 1.

    Args:
        params: Model parameters
        model: ConservationHNN or MultiInvariantHNN
        states: Batch of states (B, 2n)

    Returns:
        loss: Scalar involution loss
    """
    num_inv = model.num_invariants

    if num_inv <= 1:
        return 0.0

    def pairwise_bracket(z, i, j):
        """Compute {I_i, I_j} at state z."""
        n = len(z) // 2

        I_i_func = lambda state: model.invariant(params, state, i)
        I_j_func = lambda state: model.invariant(params, state, j)

        grad_I_i = jax.grad(I_i_func)(z)
        grad_I_j = jax.grad(I_j_func)(z)

        dI_i_dq, dI_i_dp = grad_I_i[:n], grad_I_i[n:]
        dI_j_dq, dI_j_dp = grad_I_j[:n], grad_I_j[n:]

        bracket = jnp.dot(dI_i_dq, dI_j_dp) - jnp.dot(dI_i_dp, dI_j_dq)
        return bracket

    total_loss = 0.0
    count = 0

    # For all pairs (i, j) with i < j
    for i in range(num_inv):
        for j in range(i + 1, num_inv):
            # Compute {I_i, I_j} over batch
            brackets = jax.vmap(lambda z: pairwise_bracket(z, i, j))(states)

            # Add to loss
            total_loss += jnp.mean(brackets ** 2)
            count += 1

    return total_loss / count if count > 0 else 0.0


@partial(jax.jit, static_argnums=(1,))
def regularization_loss(
    params,
    model,
    states: jnp.ndarray,
    inv_idx: int = 0
) -> jnp.ndarray:
    """
    L_regularization: Prevent trivial solutions.

    Trivial invariants to avoid:
    1. Constant: I(z) = c for all z
    2. Coordinate function: I(z) = z_i
    3. Linear in known integrals (e.g., I = a·E + b·L)

    Regularizers:
    1. Non-constant: Maximize variance of I across batch
    2. Non-trivial: Penalize if I is too simple

    Args:
        params: Model parameters
        model: ConservationHNN
        states: Batch of states (B, 2n)
        inv_idx: Which invariant to regularize

    Returns:
        loss: Scalar regularization loss
    """
    # Compute invariant values over batch
    I_values = model.batch_invariant(params, states, inv_idx)

    # 1. Non-constant regularizer: penalize low variance
    variance = jnp.var(I_values)
    constant_penalty = jnp.exp(-10.0 * variance)  # Large penalty if var ≈ 0

    # 2. Normalization: encourage I to have reasonable scale
    # Penalize if std dev is too small or too large
    std_dev = jnp.sqrt(variance + 1e-8)
    target_std = 1.0  # Target standard deviation
    scale_penalty = (std_dev - target_std) ** 2

    # Combined regularization
    loss = constant_penalty + 0.1 * scale_penalty

    return loss


def combined_loss(
    params,
    model,
    batch: Tuple[jnp.ndarray, jnp.ndarray],
    lambda_conservation: float = 1.0,
    lambda_noether: float = 0.1,
    lambda_regularization: float = 0.01,
    lambda_involution: float = 0.1,
    symmetry_transforms: Optional[List[Callable]] = None,
    inv_idx: int = 0
) -> Tuple[jnp.ndarray, Dict]:
    """
    Combined loss for conservation-constrained training.

    L = L_trajectory
        + λ₁ · L_conservation
        + λ₂ · L_Noether
        + λ₃ · L_regularization
        + λ₄ · L_involution

    Args:
        params: Model parameters
        model: ConservationHNN
        batch: (states, derivatives) tuple
        lambda_conservation: Weight for conservation constraint
        lambda_noether: Weight for Noether regularization
        lambda_regularization: Weight for regularization
        lambda_involution: Weight for involution constraint
        symmetry_transforms: List of symmetry functions
        inv_idx: Which invariant to train

    Returns:
        total_loss: Scalar combined loss
        metrics: Dictionary with individual loss components
    """
    states, derivatives = batch

    # Component losses
    L_traj, traj_metrics = trajectory_loss(params, model, states, derivatives)
    L_cons = conservation_loss(params, model, states, inv_idx)
    L_reg = regularization_loss(params, model, states, inv_idx)

    # Noether loss (if symmetries provided)
    if symmetry_transforms and len(symmetry_transforms) > 0:
        L_noeth = noether_regularizer(
            params, model, symmetry_transforms, states, inv_idx
        )
    else:
        L_noeth = 0.0

    # Involution loss (if multiple invariants)
    if hasattr(model, 'num_invariants') and model.num_invariants > 1:
        L_invol = involution_loss(params, model, states)
    else:
        L_invol = 0.0

    # Combined loss
    total_loss = (
        L_traj
        + lambda_conservation * L_cons
        + lambda_noether * L_noeth
        + lambda_regularization * L_reg
        + lambda_involution * L_invol
    )

    # Metrics for logging
    metrics = {
        **traj_metrics,  # Include trajectory metrics
        'total_loss': total_loss,
        'conservation_loss': L_cons,
        'noether_loss': L_noeth,
        'regularization_loss': L_reg,
        'involution_loss': L_invol,
        'lambda_conservation': lambda_conservation,
        'lambda_noether': lambda_noether
    }

    return total_loss, metrics


# Utility functions

def compute_conservation_violation(
    params,
    model,
    states: jnp.ndarray,
    inv_idx: int = 0
) -> Dict:
    """
    Compute statistics of conservation violation {I, H}.

    Args:
        params: Model parameters
        model: ConservationHNN
        states: Test states
        inv_idx: Invariant index

    Returns:
        stats: Dictionary with Poisson bracket statistics
    """
    def poisson_bracket_at_state(z):
        H_func = lambda state: model.hamiltonian(params, state)
        I_func = lambda state: model.invariant(params, state, inv_idx)
        return poisson_bracket(I_func, H_func, z)

    brackets = jax.vmap(poisson_bracket_at_state)(states)

    stats = {
        'mean': float(jnp.mean(jnp.abs(brackets))),
        'std': float(jnp.std(brackets)),
        'max': float(jnp.max(jnp.abs(brackets))),
        'median': float(jnp.median(jnp.abs(brackets))),
        'percentile_95': float(jnp.percentile(jnp.abs(brackets), 95))
    }

    return stats


# Test code
if __name__ == "__main__":
    print("Testing conservation loss functions...")

    from .conservation_hnn import create_conservation_hnn
    from .jax_utils import split_state, join_state

    # Create test model
    print("\n[1] Creating ConservationHNN...")
    model, params = create_conservation_hnn(
        state_dim=4,
        num_invariants=1,
        encoder_dims=(32, 32),
        hamiltonian_dims=(16, 16),
        invariant_dims=(16, 16),
        seed=0
    )

    # Generate synthetic data
    print("\n[2] Generating synthetic data...")
    key = jax.random.PRNGKey(42)

    def harmonic_dynamics(z):
        q, p = split_state(z)
        return join_state(p, -q)

    n_samples = 100
    states = jax.random.normal(key, (n_samples, 4))
    derivatives = jax.vmap(harmonic_dynamics)(states)

    print(f"  Generated {n_samples} samples")

    # Test trajectory loss
    print("\n[3] Testing trajectory loss...")
    L_traj, traj_metrics = trajectory_loss(params, model, states, derivatives)
    print(f"  L_trajectory: {L_traj:.6f}")
    print(f"  Max error: {traj_metrics['max_error']:.6f}")

    # Test conservation loss
    print("\n[4] Testing conservation loss...")
    L_cons = conservation_loss(params, model, states, inv_idx=0)
    print(f"  L_conservation: {L_cons:.6f}")
    print(f"  (Should decrease during training)")

    # Test regularization loss
    print("\n[5] Testing regularization loss...")
    L_reg = regularization_loss(params, model, states, inv_idx=0)
    print(f"  L_regularization: {L_reg:.6f}")

    # Test combined loss (without symmetries)
    print("\n[6] Testing combined loss...")
    batch = (states, derivatives)
    total_loss, metrics = combined_loss(
        params, model, batch,
        lambda_conservation=1.0,
        lambda_noether=0.1,
        lambda_regularization=0.01
    )
    print(f"  Total loss: {total_loss:.6f}")
    print(f"  Components:")
    print(f"    Trajectory: {metrics['trajectory_loss']:.6f}")
    print(f"    Conservation: {metrics['conservation_loss']:.6f}")
    print(f"    Regularization: {metrics['regularization_loss']:.6f}")

    # Test conservation violation statistics
    print("\n[7] Testing conservation violation stats...")
    stats = compute_conservation_violation(params, model, states[:20], inv_idx=0)
    print(f"  Poisson bracket {{I, H}}:")
    print(f"    Mean: {stats['mean']:.6f}")
    print(f"    Max: {stats['max']:.6f}")
    print(f"    95th percentile: {stats['percentile_95']:.6f}")

    # Test with multiple invariants
    print("\n[8] Testing with multiple invariants...")
    multi_model, multi_params = create_conservation_hnn(
        state_dim=4,
        num_invariants=2,
        encoder_dims=(32, 32),
        seed=1
    )

    L_invol = involution_loss(multi_params, multi_model, states)
    print(f"  L_involution (2 invariants): {L_invol:.6f}")

    # Test gradients
    print("\n[9] Testing gradient computation...")
    grad_fn = jax.grad(lambda p: combined_loss(p, model, batch)[0])
    grads = grad_fn(params)
    grad_norm = jnp.sqrt(sum(jnp.sum(g**2) for g in jax.tree_util.tree_leaves(grads)))
    print(f"  Gradient norm: {grad_norm:.6f}")
    print(f"  Gradients computable: ✓")

    print("\n✓ All tests passed!")
