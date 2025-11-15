"""
Training loop and optimization for Hamiltonian Neural Networks (Task 3.2.2, Part B).

This module implements training procedures for HNNs, including:
- Loss functions (trajectory matching)
- Optimization with Optax
- Training loops with validation
- Checkpointing and logging
"""

import jax
import jax.numpy as jnp
import optax
from flax.training import train_state
from typing import Dict, Tuple, Callable, Optional, Any
from functools import partial
import time


class TrainState(train_state.TrainState):
    """
    Extended train state with additional metrics.

    Attributes:
        step: Training step counter
        apply_fn: Model apply function
        params: Model parameters
        tx: Optimizer
        opt_state: Optimizer state
        batch_stats: Optional batch statistics (e.g., for batch norm)
    """
    batch_stats: Optional[Dict] = None


def create_train_state(
    model,
    params,
    learning_rate: float = 1e-3,
    weight_decay: float = 1e-5,
    grad_clip: float = 1.0,
    schedule_type: str = 'exponential'
) -> TrainState:
    """
    Create optimizer and training state.

    Args:
        model: Flax model
        params: Initialized parameters
        learning_rate: Initial learning rate
        weight_decay: Weight decay (L2 regularization)
        grad_clip: Gradient clipping threshold
        schedule_type: Learning rate schedule ('constant', 'exponential', 'cosine')

    Returns:
        TrainState with optimizer
    """
    # Learning rate schedule
    if schedule_type == 'exponential':
        schedule = optax.exponential_decay(
            init_value=learning_rate,
            transition_steps=1000,
            decay_rate=0.99
        )
    elif schedule_type == 'cosine':
        schedule = optax.cosine_decay_schedule(
            init_value=learning_rate,
            decay_steps=10000
        )
    else:  # constant
        schedule = learning_rate

    # Optimizer chain
    optimizer = optax.chain(
        optax.clip_by_global_norm(grad_clip),  # Gradient clipping
        optax.adamw(learning_rate=schedule, weight_decay=weight_decay)
    )

    return TrainState.create(
        apply_fn=model.apply,
        params=params,
        tx=optimizer
    )


@partial(jax.jit, static_argnums=(1,))
def trajectory_loss_fn(
    params,
    model,
    states: jnp.ndarray,
    derivatives: jnp.ndarray
) -> Tuple[jnp.ndarray, Dict]:
    """
    Compute loss for trajectory prediction.

    Loss: ||dz/dt_true - dz/dt_predicted||^2

    Args:
        params: Model parameters
        model: HNN model
        states: Batch of states (B, 2n)
        derivatives: True time derivatives (B, 2n)

    Returns:
        loss: Scalar loss
        metrics: Dictionary of metrics
    """
    # Predict dynamics via HNN
    predicted_derivatives = model.batch_dynamics(params, states)

    # Mean squared error
    squared_errors = (predicted_derivatives - derivatives) ** 2
    loss = jnp.mean(squared_errors)

    # Additional metrics
    max_error = jnp.max(jnp.abs(predicted_derivatives - derivatives))
    mean_abs_error = jnp.mean(jnp.abs(predicted_derivatives - derivatives))

    # Component-wise errors (position vs momentum)
    n = states.shape[1] // 2
    q_error = jnp.mean(squared_errors[:, :n])
    p_error = jnp.mean(squared_errors[:, n:])

    metrics = {
        'loss': loss,
        'max_error': max_error,
        'mean_abs_error': mean_abs_error,
        'q_error': q_error,
        'p_error': p_error
    }

    return loss, metrics


@jax.jit
def train_step(
    state: TrainState,
    batch: Tuple[jnp.ndarray, jnp.ndarray],
    model
) -> Tuple[TrainState, Dict]:
    """
    Single training step with gradient descent.

    Args:
        state: Current train state
        batch: (states, derivatives) tuple
        model: HNN model

    Returns:
        new_state: Updated train state
        metrics: Training metrics
    """
    states, derivatives = batch

    # Compute loss and gradients
    (loss, metrics), grads = jax.value_and_grad(
        trajectory_loss_fn,
        has_aux=True
    )(state.params, model, states, derivatives)

    # Update parameters
    state = state.apply_gradients(grads=grads)

    # Add gradient norm to metrics
    grad_norm = jnp.sqrt(sum(jnp.sum(g**2) for g in jax.tree_util.tree_leaves(grads)))
    metrics['grad_norm'] = grad_norm

    return state, metrics


def train_epoch(
    state: TrainState,
    train_dataset,
    model,
    batch_size: int
) -> Tuple[TrainState, Dict]:
    """
    Train for one epoch.

    Args:
        state: Current train state
        train_dataset: Training dataset (should have batch_iterator method)
        model: HNN model
        batch_size: Batch size

    Returns:
        state: Updated train state
        epoch_metrics: Aggregated metrics
    """
    epoch_metrics = []

    # Iterate over batches
    for batch in train_dataset.batch_iterator(batch_size):
        state, metrics = train_step(state, batch, model)
        epoch_metrics.append(metrics)

    # Aggregate metrics
    aggregated = {}
    for key in epoch_metrics[0].keys():
        values = [m[key] for m in epoch_metrics]
        aggregated[key] = float(jnp.mean(jnp.array(values)))

    return state, aggregated


@jax.jit
def eval_step(
    params,
    model,
    states: jnp.ndarray,
    derivatives: jnp.ndarray
) -> Dict:
    """
    Evaluation step (no gradient computation).

    Args:
        params: Model parameters
        model: HNN model
        states: Batch of states
        derivatives: True derivatives

    Returns:
        metrics: Evaluation metrics
    """
    _, metrics = trajectory_loss_fn(params, model, states, derivatives)
    return metrics


def evaluate(
    state: TrainState,
    model,
    val_dataset,
    batch_size: int
) -> Dict:
    """
    Evaluate model on validation set.

    Args:
        state: Train state
        model: HNN model
        val_dataset: Validation dataset
        batch_size: Batch size

    Returns:
        val_metrics: Aggregated validation metrics
    """
    val_metrics = []

    for batch in val_dataset.batch_iterator(batch_size):
        states, derivatives = batch
        metrics = eval_step(state.params, model, states, derivatives)
        val_metrics.append(metrics)

    # Aggregate
    aggregated = {}
    for key in val_metrics[0].keys():
        values = [m[key] for m in val_metrics]
        aggregated[key] = float(jnp.mean(jnp.array(values)))

    return aggregated


def train_hnn(
    model,
    params,
    train_dataset,
    val_dataset,
    num_epochs: int = 100,
    batch_size: int = 256,
    learning_rate: float = 1e-3,
    weight_decay: float = 1e-5,
    eval_every: int = 5,
    verbose: bool = True
) -> Tuple[TrainState, Dict]:
    """
    Train HNN on trajectory data.

    Args:
        model: HNN model
        params: Initial parameters
        train_dataset: Training data
        val_dataset: Validation data
        num_epochs: Number of training epochs
        batch_size: Batch size
        learning_rate: Initial learning rate
        weight_decay: Weight decay coefficient
        eval_every: Evaluate every N epochs
        verbose: Print progress

    Returns:
        final_state: Trained model state
        history: Training history (losses, metrics)
    """
    # Create training state
    state = create_train_state(model, params, learning_rate, weight_decay)

    # Training history
    history = {
        'train_loss': [],
        'val_loss': [],
        'train_metrics': [],
        'val_metrics': [],
        'epoch_times': []
    }

    if verbose:
        print("=" * 70)
        print("TRAINING HAMILTONIAN NEURAL NETWORK")
        print("=" * 70)
        print(f"Epochs: {num_epochs}")
        print(f"Batch size: {batch_size}")
        print(f"Learning rate: {learning_rate}")
        print(f"Weight decay: {weight_decay}")
        print("=" * 70)

    # Training loop
    for epoch in range(num_epochs):
        epoch_start = time.time()

        # Train for one epoch
        state, train_metrics = train_epoch(state, train_dataset, model, batch_size)

        epoch_time = time.time() - epoch_start

        # Record metrics
        history['train_loss'].append(train_metrics['loss'])
        history['train_metrics'].append(train_metrics)
        history['epoch_times'].append(epoch_time)

        # Validation
        if (epoch + 1) % eval_every == 0:
            val_metrics = evaluate(state, model, val_dataset, batch_size)
            history['val_loss'].append(val_metrics['loss'])
            history['val_metrics'].append(val_metrics)

            if verbose:
                print(f"\nEpoch {epoch + 1}/{num_epochs}:")
                print(f"  Train Loss: {train_metrics['loss']:.6f}")
                print(f"  Val Loss: {val_metrics['loss']:.6f}")
                print(f"  Max Error: {val_metrics['max_error']:.6f}")
                print(f"  Grad Norm: {train_metrics['grad_norm']:.4f}")
                print(f"  Time: {epoch_time:.2f}s")
        elif verbose and (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch + 1}/{num_epochs}: "
                  f"Loss = {train_metrics['loss']:.6f}, "
                  f"Time = {epoch_time:.2f}s")

    if verbose:
        print("\n" + "=" * 70)
        print("TRAINING COMPLETE")
        print("=" * 70)
        final_train_loss = history['train_loss'][-1]
        final_val_loss = history['val_loss'][-1] if history['val_loss'] else 0.0
        print(f"Final train loss: {final_train_loss:.6f}")
        if history['val_loss']:
            print(f"Final val loss: {final_val_loss:.6f}")
        total_time = sum(history['epoch_times'])
        print(f"Total training time: {total_time:.1f}s ({total_time/60:.1f}min)")

    return state, history


# Simplified dataset iterator (placeholder - would use real HDF5 dataset)
class SimpleDatasetIterator:
    """Simple dataset iterator for testing."""

    def __init__(self, states, derivatives):
        self.states = states
        self.derivatives = derivatives

    def batch_iterator(self, batch_size):
        """Yield batches of data."""
        n_samples = len(self.states)
        indices = jnp.arange(n_samples)

        # Shuffle indices
        perm = jax.random.permutation(jax.random.PRNGKey(0), indices)

        for i in range(0, n_samples, batch_size):
            batch_indices = perm[i:i + batch_size]
            yield (self.states[batch_indices], self.derivatives[batch_indices])


# Test code
if __name__ == "__main__":
    print("Testing HNN training...")

    from .hnn_architecture import create_hnn_model
    from .jax_utils import split_state, join_state

    # Generate synthetic data (harmonic oscillator)
    print("\n[1] Generating synthetic training data (harmonic oscillator)...")

    def harmonic_dynamics(z):
        """True dynamics: dq/dt = p, dp/dt = -q"""
        q, p = split_state(z)
        return join_state(p, -q)

    # Generate 1000 samples
    n_samples = 1000
    key = jax.random.PRNGKey(42)

    states = jax.random.normal(key, (n_samples, 4))  # Random initial states
    derivatives = jax.vmap(harmonic_dynamics)(states)  # True derivatives

    print(f"  Generated {n_samples} samples")
    print(f"  State shape: {states.shape}")
    print(f"  Derivatives shape: {derivatives.shape}")

    # Split train/val
    n_train = 800
    train_states = states[:n_train]
    train_derivs = derivatives[:n_train]
    val_states = states[n_train:]
    val_derivs = derivatives[n_train:]

    train_dataset = SimpleDatasetIterator(train_states, train_derivs)
    val_dataset = SimpleDatasetIterator(val_states, val_derivs)

    # Create model
    print("\n[2] Creating HNN model...")
    model, params = create_hnn_model(state_dim=4, hidden_dims=(32, 32), seed=0)
    print(f"  Model created with state_dim=4, hidden_dims=(32, 32)")

    # Train
    print("\n[3] Training HNN...")
    final_state, history = train_hnn(
        model,
        params,
        train_dataset,
        val_dataset,
        num_epochs=20,
        batch_size=64,
        learning_rate=1e-3,
        eval_every=5,
        verbose=True
    )

    # Test prediction
    print("\n[4] Testing predictions...")
    test_z = jnp.array([1.0, 0.0, 0.0, 0.0])
    true_dz_dt = harmonic_dynamics(test_z)
    pred_dz_dt = model.dynamics(final_state.params, test_z)

    print(f"  Test state: {test_z}")
    print(f"  True dynamics: {true_dz_dt}")
    print(f"  Predicted dynamics: {pred_dz_dt}")
    print(f"  Error: {jnp.linalg.norm(pred_dz_dt - true_dz_dt):.6f}")

    print("\n✓ Training test completed!")
