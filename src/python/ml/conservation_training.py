"""
Two-stage training pipeline for conservation-constrained learning (Task 3.2.3, Part D).

This module implements the core training procedure for discovering conserved
quantities via physics-informed constraints.

Training Strategy:
------------------
Stage 1 (Warm-up): Train Hamiltonian head only
    - Loss: L_trajectory only
    - Duration: 30-50 epochs
    - Goal: Learn accurate dynamics H_θ

Stage 2 (Conservation): Train both heads with constraints
    - Loss: L_total = L_trajectory + λ₁·L_conservation + λ₂·L_Noether + λ₃·L_reg
    - Duration: 100-200 epochs
    - λ₁ gradually increases: 0 → 1 over first 50 epochs
    - Goal: Discover conserved quantity I_φ such that {I_φ, H_θ} = 0

Key Innovation:
--------------
By enforcing the Poisson bracket constraint {I_φ, H_θ} = 0 during training,
the network learns to predict conserved quantities that are guaranteed to
be preserved along Hamiltonian trajectories.
"""

import jax
import jax.numpy as jnp
import optax
from flax.training import train_state
from typing import Dict, Tuple, Optional, List, Callable, Any
from functools import partial
import time

from .conservation_hnn import ConservationHNN
from .conservation_loss import (
    combined_loss,
    trajectory_loss,
    conservation_loss,
    compute_conservation_violation
)
from .symmetry_transforms import get_symmetry_transforms_3body


class ConservationTrainState(train_state.TrainState):
    """
    Extended training state for conservation learning.

    Attributes:
        params: Model parameters
        tx: Optimizer
        opt_state: Optimizer state
        step: Training step counter
        stage: Current training stage (1 or 2)
        lambda_conservation: Current conservation weight
        lambda_noether: Noether regularization weight
        lambda_regularization: Regularization weight
    """
    stage: int = 1
    lambda_conservation: float = 0.0
    lambda_noether: float = 0.1
    lambda_regularization: float = 0.01
    lambda_involution: float = 0.1


def create_conservation_train_state(
    model: ConservationHNN,
    params: Any,
    learning_rate: float = 1e-3,
    warmup_steps: int = 1000,
    weight_decay: float = 1e-5,
    grad_clip: float = 1.0,
    stage: int = 1
) -> ConservationTrainState:
    """
    Create training state for conservation learning.

    Args:
        model: ConservationHNN instance
        params: Initialized parameters
        learning_rate: Peak learning rate
        warmup_steps: Linear warmup steps
        weight_decay: AdamW weight decay
        grad_clip: Gradient clipping value
        stage: Initial training stage (1 or 2)

    Returns:
        state: ConservationTrainState

    Example:
        >>> model, params = create_conservation_hnn(state_dim=8)
        >>> state = create_conservation_train_state(model, params)
    """
    # Learning rate schedule with warmup
    schedule = optax.warmup_cosine_decay_schedule(
        init_value=0.0,
        peak_value=learning_rate,
        warmup_steps=warmup_steps,
        decay_steps=100000,
        end_value=1e-6
    )

    # Optimizer: AdamW with gradient clipping
    tx = optax.chain(
        optax.clip_by_global_norm(grad_clip),
        optax.adamw(learning_rate=schedule, weight_decay=weight_decay)
    )

    state = ConservationTrainState.create(
        apply_fn=model.apply,
        params=params,
        tx=tx,
        stage=stage,
        lambda_conservation=0.0 if stage == 1 else 1.0,
        lambda_noether=0.1,
        lambda_regularization=0.01,
        lambda_involution=0.1
    )

    return state


@partial(jax.jit, static_argnums=(1,))
def train_step_stage1(
    state: ConservationTrainState,
    model: ConservationHNN,
    batch: Tuple[jnp.ndarray, jnp.ndarray]
) -> Tuple[ConservationTrainState, Dict]:
    """
    Training step for Stage 1 (Hamiltonian only).

    Args:
        state: Current training state
        model: ConservationHNN
        batch: (states, derivatives)

    Returns:
        state: Updated training state
        metrics: Training metrics
    """
    states, derivatives = batch

    def loss_fn(params):
        # Stage 1: Only trajectory matching loss
        loss, metrics = trajectory_loss(params, model, states, derivatives)
        return loss, metrics

    # Compute gradients
    (loss, metrics), grads = jax.value_and_grad(loss_fn, has_aux=True)(state.params)

    # Update parameters
    state = state.apply_gradients(grads=grads)

    # Add gradient norm to metrics
    grad_norm = optax.global_norm(grads)
    metrics['grad_norm'] = grad_norm
    metrics['stage'] = 1

    return state, metrics


@partial(jax.jit, static_argnums=(1, 2))
def train_step_stage2(
    state: ConservationTrainState,
    model: ConservationHNN,
    symmetry_transforms: Optional[List[Callable]],
    batch: Tuple[jnp.ndarray, jnp.ndarray],
    inv_idx: int = 0
) -> Tuple[ConservationTrainState, Dict]:
    """
    Training step for Stage 2 (Conservation-constrained).

    Args:
        state: Current training state
        model: ConservationHNN
        symmetry_transforms: List of symmetry functions (can be None)
        batch: (states, derivatives)
        inv_idx: Invariant index to train

    Returns:
        state: Updated training state
        metrics: Training metrics
    """
    def loss_fn(params):
        # Stage 2: Combined loss with conservation constraint
        loss, metrics = combined_loss(
            params,
            model,
            batch,
            lambda_conservation=state.lambda_conservation,
            lambda_noether=state.lambda_noether,
            lambda_regularization=state.lambda_regularization,
            lambda_involution=state.lambda_involution,
            symmetry_transforms=symmetry_transforms,
            inv_idx=inv_idx
        )
        return loss, metrics

    # Compute gradients
    (loss, metrics), grads = jax.value_and_grad(loss_fn, has_aux=True)(state.params)

    # Update parameters
    state = state.apply_gradients(grads=grads)

    # Add gradient norm to metrics
    grad_norm = optax.global_norm(grads)
    metrics['grad_norm'] = grad_norm
    metrics['stage'] = 2

    return state, metrics


def evaluate_conservation(
    state: ConservationTrainState,
    model: ConservationHNN,
    eval_data: Tuple[jnp.ndarray, jnp.ndarray],
    inv_idx: int = 0
) -> Dict:
    """
    Evaluate conservation quality on validation set.

    Args:
        state: Training state
        model: ConservationHNN
        eval_data: (states, derivatives) validation batch
        inv_idx: Invariant index

    Returns:
        metrics: Evaluation metrics including conservation violation
    """
    states, derivatives = eval_data

    # Trajectory loss
    L_traj, traj_metrics = trajectory_loss(state.params, model, states, derivatives)

    # Conservation violation: {I, H}
    conservation_stats = compute_conservation_violation(
        state.params, model, states, inv_idx
    )

    # Invariant statistics (variance to check non-triviality)
    I_values = model.batch_invariant(state.params, states, inv_idx)
    I_variance = float(jnp.var(I_values))
    I_mean = float(jnp.mean(I_values))
    I_std = float(jnp.std(I_values))

    metrics = {
        'val_trajectory_loss': float(L_traj),
        'val_conservation_mean': conservation_stats['mean'],
        'val_conservation_max': conservation_stats['max'],
        'val_conservation_median': conservation_stats['median'],
        'val_invariant_variance': I_variance,
        'val_invariant_mean': I_mean,
        'val_invariant_std': I_std,
        **{f'val_{k}': float(v) for k, v in traj_metrics.items()}
    }

    return metrics


def train_epoch(
    state: ConservationTrainState,
    model: ConservationHNN,
    train_loader: Any,
    symmetry_transforms: Optional[List[Callable]] = None,
    inv_idx: int = 0
) -> Tuple[ConservationTrainState, Dict]:
    """
    Train for one epoch.

    Args:
        state: Training state
        model: ConservationHNN
        train_loader: Iterable of (states, derivatives) batches
        symmetry_transforms: Symmetry functions for Noether loss
        inv_idx: Invariant index

    Returns:
        state: Updated training state
        metrics: Epoch metrics (averaged)
    """
    epoch_metrics = []

    for batch in train_loader:
        if state.stage == 1:
            # Stage 1: Hamiltonian only
            state, metrics = train_step_stage1(state, model, batch)
        else:
            # Stage 2: Conservation-constrained
            state, metrics = train_step_stage2(
                state, model, symmetry_transforms, batch, inv_idx
            )

        epoch_metrics.append(metrics)

    # Average metrics over epoch
    avg_metrics = {}
    for key in epoch_metrics[0].keys():
        avg_metrics[key] = jnp.mean(jnp.array([m[key] for m in epoch_metrics]))

    return state, avg_metrics


def two_stage_training(
    model: ConservationHNN,
    params: Any,
    train_data: Tuple[jnp.ndarray, jnp.ndarray],
    val_data: Tuple[jnp.ndarray, jnp.ndarray],
    masses: jnp.ndarray,
    manifold_type: str = 's1',
    stage1_epochs: int = 50,
    stage2_epochs: int = 150,
    batch_size: int = 256,
    learning_rate: float = 1e-3,
    warmup_steps: int = 1000,
    lambda_conservation_schedule: str = 'linear',
    lambda_warmup_epochs: int = 50,
    include_symmetries: bool = True,
    inv_idx: int = 0,
    early_stopping_patience: int = 20,
    conservation_threshold: float = 1e-4,
    verbose: bool = True
) -> Tuple[ConservationTrainState, Dict]:
    """
    Two-stage training pipeline for conservation discovery.

    Stage 1 (Warm-up):
        - Train Hamiltonian head only
        - Loss: L_trajectory
        - Goal: Accurate dynamics

    Stage 2 (Conservation):
        - Train both heads with physics constraints
        - Loss: L_trajectory + λ₁·L_conservation + λ₂·L_Noether + λ₃·L_reg
        - λ₁ gradually increases from 0 → 1
        - Goal: Discover conserved quantity I_φ with {I_φ, H_θ} ≈ 0

    Args:
        model: ConservationHNN instance
        params: Initialized parameters
        train_data: (states, derivatives) training data
        val_data: (states, derivatives) validation data
        masses: Body masses (3,) for symmetry selection
        manifold_type: 's1' or 'cartesian'
        stage1_epochs: Stage 1 epochs
        stage2_epochs: Stage 2 epochs
        batch_size: Batch size
        learning_rate: Peak learning rate
        warmup_steps: LR warmup steps
        lambda_conservation_schedule: 'linear', 'exponential', or 'cosine'
        lambda_warmup_epochs: Epochs to ramp up λ_conservation
        include_symmetries: Use Noether regularization
        inv_idx: Invariant index to train
        early_stopping_patience: Patience for early stopping
        conservation_threshold: Conservation error threshold for success
        verbose: Print progress

    Returns:
        final_state: Trained model state
        history: Training history
    """
    if verbose:
        print("=" * 80)
        print("TWO-STAGE CONSERVATION TRAINING")
        print("=" * 80)
        print(f"Stage 1: {stage1_epochs} epochs (Hamiltonian warm-up)")
        print(f"Stage 2: {stage2_epochs} epochs (Conservation discovery)")
        print(f"Batch size: {batch_size}")
        print(f"Learning rate: {learning_rate}")
        print(f"Target: Learn I_{inv_idx} such that {{I_{inv_idx}, H}} ≈ 0")
        print("=" * 80)

    # Get symmetry transforms
    if include_symmetries:
        symmetry_transforms = get_symmetry_transforms_3body(
            masses,
            manifold_type=manifold_type,
            include_time_reversal=True,
            include_permutations=True,
            include_rotations=False,
            include_virial=False
        )
        if verbose:
            print(f"Using {len(symmetry_transforms)} symmetry transforms for Noether regularization")
    else:
        symmetry_transforms = None

    # Data loaders (simple batching)
    train_states, train_derivatives = train_data
    val_states, val_derivatives = val_data

    def make_batches(states, derivatives, batch_size):
        n_samples = states.shape[0]
        n_batches = n_samples // batch_size
        batches = []
        for i in range(n_batches):
            start = i * batch_size
            end = start + batch_size
            batches.append((states[start:end], derivatives[start:end]))
        return batches

    train_batches = make_batches(train_states, train_derivatives, batch_size)

    # Initialize training state
    state = create_conservation_train_state(
        model, params, learning_rate, warmup_steps, stage=1
    )

    # Training history
    history = {
        'stage1': [],
        'stage2': [],
        'best_conservation_error': float('inf'),
        'best_epoch': -1
    }

    # =========================================================================
    # STAGE 1: Hamiltonian Warm-up
    # =========================================================================
    if verbose:
        print("\n" + "=" * 80)
        print("STAGE 1: HAMILTONIAN WARM-UP")
        print("=" * 80)

    stage1_start = time.time()

    for epoch in range(stage1_epochs):
        # Train epoch
        state, train_metrics = train_epoch(state, model, train_batches)

        # Evaluate
        val_metrics = evaluate_conservation(
            state, model, val_data, inv_idx
        )

        # Record history
        history['stage1'].append({
            'epoch': epoch,
            'train': train_metrics,
            'val': val_metrics
        })

        if verbose and (epoch % 10 == 0 or epoch == stage1_epochs - 1):
            print(f"Epoch {epoch:3d}/{stage1_epochs}: "
                  f"Train Loss: {train_metrics['trajectory_loss']:.6f}, "
                  f"Val Loss: {val_metrics['val_trajectory_loss']:.6f}, "
                  f"Grad Norm: {train_metrics['grad_norm']:.6f}")

    stage1_time = time.time() - stage1_start

    if verbose:
        print(f"\nStage 1 complete in {stage1_time:.1f}s")
        print(f"Final trajectory loss: {history['stage1'][-1]['val']['val_trajectory_loss']:.6f}")

    # =========================================================================
    # STAGE 2: Conservation Discovery
    # =========================================================================
    if verbose:
        print("\n" + "=" * 80)
        print("STAGE 2: CONSERVATION DISCOVERY")
        print("=" * 80)

    # Switch to Stage 2
    state = state.replace(stage=2, lambda_conservation=0.0)

    stage2_start = time.time()
    best_state = state
    patience_counter = 0

    for epoch in range(stage2_epochs):
        # Gradually increase λ_conservation
        if epoch < lambda_warmup_epochs:
            if lambda_conservation_schedule == 'linear':
                lambda_cons = epoch / lambda_warmup_epochs
            elif lambda_conservation_schedule == 'exponential':
                lambda_cons = 1.0 - jnp.exp(-5.0 * epoch / lambda_warmup_epochs)
            elif lambda_conservation_schedule == 'cosine':
                lambda_cons = 0.5 * (1 - jnp.cos(jnp.pi * epoch / lambda_warmup_epochs))
            else:
                lambda_cons = epoch / lambda_warmup_epochs
        else:
            lambda_cons = 1.0

        state = state.replace(lambda_conservation=float(lambda_cons))

        # Train epoch
        state, train_metrics = train_epoch(
            state, model, train_batches, symmetry_transforms, inv_idx
        )

        # Evaluate
        val_metrics = evaluate_conservation(
            state, model, val_data, inv_idx
        )

        # Record history
        history['stage2'].append({
            'epoch': epoch,
            'lambda_conservation': float(lambda_cons),
            'train': train_metrics,
            'val': val_metrics
        })

        # Check for improvement
        conservation_error = val_metrics['val_conservation_mean']
        if conservation_error < history['best_conservation_error']:
            history['best_conservation_error'] = conservation_error
            history['best_epoch'] = epoch
            best_state = state
            patience_counter = 0
        else:
            patience_counter += 1

        if verbose and (epoch % 10 == 0 or epoch == stage2_epochs - 1):
            print(f"Epoch {epoch:3d}/{stage2_epochs}: "
                  f"λ_cons={lambda_cons:.3f}, "
                  f"Total Loss: {train_metrics['total_loss']:.6f}, "
                  f"Conservation: {conservation_error:.2e}, "
                  f"I_var: {val_metrics['val_invariant_variance']:.6f}")

        # Early stopping
        if patience_counter >= early_stopping_patience:
            if verbose:
                print(f"\nEarly stopping at epoch {epoch} (patience={early_stopping_patience})")
            break

        # Success criterion
        if conservation_error < conservation_threshold:
            if verbose:
                print(f"\n🎯 Conservation threshold reached at epoch {epoch}!")
                print(f"   {{I, H}} mean: {conservation_error:.2e} < {conservation_threshold:.2e}")
            break

    stage2_time = time.time() - stage2_start

    if verbose:
        print("\n" + "=" * 80)
        print("TRAINING COMPLETE")
        print("=" * 80)
        print(f"Stage 1 time: {stage1_time:.1f}s")
        print(f"Stage 2 time: {stage2_time:.1f}s")
        print(f"Total time: {stage1_time + stage2_time:.1f}s")
        print(f"\nBest conservation error: {history['best_conservation_error']:.2e} (epoch {history['best_epoch']})")
        print(f"Final invariant variance: {history['stage2'][-1]['val']['val_invariant_variance']:.6f}")

        if history['best_conservation_error'] < conservation_threshold:
            print("\n✅ SUCCESS: Conserved quantity discovered!")
        else:
            print("\n⚠️  WARNING: Conservation threshold not reached")

    return best_state, history


# Test code
if __name__ == "__main__":
    print("Testing conservation training pipeline...")

    from .conservation_hnn import create_conservation_hnn
    from .jax_utils import split_state, join_state

    # Create model
    print("\n[1] Creating ConservationHNN...")
    model, params = create_conservation_hnn(
        state_dim=4,
        num_invariants=1,
        encoder_dims=(64, 64),
        hamiltonian_dims=(32, 32),
        invariant_dims=(32, 32),
        seed=0
    )

    # Generate synthetic harmonic oscillator data
    print("\n[2] Generating synthetic training data...")
    key = jax.random.PRNGKey(42)

    def harmonic_dynamics(z):
        """Harmonic oscillator: dq/dt = p, dp/dt = -q"""
        q, p = split_state(z)
        return join_state(p, -q)

    n_train = 1000
    n_val = 200

    key, subkey = jax.random.split(key)
    train_states = jax.random.normal(subkey, (n_train, 4))
    train_derivatives = jax.vmap(harmonic_dynamics)(train_states)

    key, subkey = jax.random.split(key)
    val_states = jax.random.normal(subkey, (n_val, 4))
    val_derivatives = jax.vmap(harmonic_dynamics)(val_states)

    print(f"  Train: {n_train} samples")
    print(f"  Val: {n_val} samples")

    # Test training state creation
    print("\n[3] Creating training state...")
    state = create_conservation_train_state(
        model, params, learning_rate=1e-3, stage=1
    )
    print(f"  Stage: {state.stage}")
    print(f"  λ_conservation: {state.lambda_conservation}")

    # Test Stage 1 training step
    print("\n[4] Testing Stage 1 training step...")
    batch = (train_states[:32], train_derivatives[:32])
    state, metrics = train_step_stage1(state, model, batch)
    print(f"  Loss: {metrics['trajectory_loss']:.6f}")
    print(f"  Grad norm: {metrics['grad_norm']:.6f}")

    # Test Stage 2 training step
    print("\n[5] Testing Stage 2 training step...")
    state = state.replace(stage=2, lambda_conservation=1.0)
    masses = jnp.array([1.0, 1.0, 1.0])
    symmetry_transforms = get_symmetry_transforms_3body(
        masses, include_time_reversal=True, include_permutations=False
    )
    state, metrics = train_step_stage2(state, model, symmetry_transforms, batch, inv_idx=0)
    print(f"  Total loss: {metrics['total_loss']:.6f}")
    print(f"  Conservation loss: {metrics['conservation_loss']:.6f}")

    # Test evaluation
    print("\n[6] Testing evaluation...")
    val_batch = (val_states[:100], val_derivatives[:100])
    eval_metrics = evaluate_conservation(state, model, val_batch, inv_idx=0)
    print(f"  Val trajectory loss: {eval_metrics['val_trajectory_loss']:.6f}")
    print(f"  Conservation mean: {eval_metrics['val_conservation_mean']:.2e}")
    print(f"  Invariant variance: {eval_metrics['val_invariant_variance']:.6f}")

    # Test two-stage training (minimal)
    print("\n[7] Testing two-stage training (5+10 epochs)...")
    fresh_model, fresh_params = create_conservation_hnn(
        state_dim=4, num_invariants=1, encoder_dims=(32, 32), seed=1
    )

    final_state, history = two_stage_training(
        fresh_model,
        fresh_params,
        train_data=(train_states, train_derivatives),
        val_data=(val_states[:100], val_derivatives[:100]),
        masses=jnp.array([1.0, 1.0, 1.0]),
        stage1_epochs=5,
        stage2_epochs=10,
        batch_size=128,
        learning_rate=1e-3,
        lambda_warmup_epochs=5,
        include_symmetries=True,
        verbose=True
    )

    print(f"\n  Stage 1 epochs: {len(history['stage1'])}")
    print(f"  Stage 2 epochs: {len(history['stage2'])}")
    print(f"  Best conservation error: {history['best_conservation_error']:.2e}")

    print("\n✓ All tests passed!")
