"""
Model utilities for Hamiltonian Neural Networks (Task 3.2.2, Part D).

This module provides utility functions for:
- Checkpointing (save/load models)
- Trajectory integration with learned dynamics
- Energy conservation verification
- Model comparison and benchmarking
"""

import jax
import jax.numpy as jnp
import pickle
from pathlib import Path
from typing import Tuple, Dict, Optional, Callable
import numpy as np

from .hnn_training import TrainState
from .jax_utils import runge_kutta_4_step


def count_parameters(params) -> int:
    """
    Count total trainable parameters.

    Args:
        params: Model parameters (PyTree)

    Returns:
        Total number of parameters

    Example:
        >>> from .hnn_architecture import create_hnn_model
        >>> model, params = create_hnn_model(state_dim=4)
        >>> n = count_parameters(params)
        >>> print(f"Parameters: {n:,}")
    """
    return sum(x.size for x in jax.tree_util.tree_leaves(params))


def save_checkpoint(
    state: TrainState,
    filepath: str,
    metadata: Optional[Dict] = None
):
    """
    Save model checkpoint.

    Args:
        state: Training state
        filepath: Path to save checkpoint
        metadata: Optional metadata dict

    Example:
        >>> save_checkpoint(state, 'checkpoints/model_epoch_100.pkl',
        ...                 metadata={'epoch': 100, 'loss': 0.001})
    """
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

    checkpoint = {
        'params': state.params,
        'step': state.step,
        'opt_state': state.opt_state,
        'metadata': metadata or {}
    }

    with open(filepath, 'wb') as f:
        pickle.dump(checkpoint, f)

    print(f"Checkpoint saved: {filepath}")


def load_checkpoint(filepath: str) -> Tuple[Dict, Dict]:
    """
    Load model checkpoint.

    Args:
        filepath: Path to checkpoint file

    Returns:
        params: Model parameters
        metadata: Checkpoint metadata

    Example:
        >>> params, metadata = load_checkpoint('checkpoints/model.pkl')
        >>> print(metadata['epoch'])
    """
    with open(filepath, 'rb') as f:
        checkpoint = pickle.load(f)

    params = checkpoint['params']
    metadata = checkpoint.get('metadata', {})

    print(f"Checkpoint loaded: {filepath}")
    if metadata:
        print(f"  Metadata: {metadata}")

    return params, metadata


def integrate_trajectory_learned(
    model,
    params,
    z0: jnp.ndarray,
    t_span: Tuple[float, float],
    dt: float,
    method: str = 'rk4'
) -> Tuple[jnp.ndarray, jnp.ndarray]:
    """
    Integrate trajectory using learned HNN dynamics.

    Args:
        model: Trained HNN model
        params: Model parameters
        z0: Initial state (2n,)
        t_span: (t_start, t_end)
        dt: Timestep
        method: Integration method ('euler', 'rk4')

    Returns:
        times: Time array (N,)
        states: State array (N, 2n)

    Example:
        >>> from .hnn_architecture import create_hnn_model
        >>> model, params = create_hnn_model(state_dim=4)
        >>> z0 = jnp.array([1.0, 0.0, 0.0, 1.0])
        >>> times, states = integrate_trajectory_learned(
        ...     model, params, z0, (0, 10), dt=0.1
        ... )
    """
    times = jnp.arange(t_span[0], t_span[1], dt)
    states = [z0]

    z = z0
    for i in range(len(times) - 1):
        # Compute dynamics
        dz_dt = model.dynamics(params, z)

        # Integration step
        if method == 'euler':
            z_next = z + dt * dz_dt
        elif method == 'rk4':
            dynamics_fn = lambda state: model.dynamics(params, state)
            z_next = runge_kutta_4_step(dynamics_fn, z, dt)
        else:
            raise ValueError(f"Unknown method: {method}")

        states.append(z_next)
        z = z_next

    states = jnp.array(states)
    return times, states


def verify_energy_conservation(
    model,
    params,
    z0: jnp.ndarray,
    t_span: Tuple[float, float],
    dt: float
) -> Dict:
    """
    Verify energy conservation along integrated trajectory.

    For Hamiltonian systems, H should be conserved: dH/dt = 0.

    Args:
        model: Trained HNN
        params: Model parameters
        z0: Initial state
        t_span: Time span
        dt: Timestep

    Returns:
        results: Dict with energy drift metrics

    Example:
        >>> results = verify_energy_conservation(model, params, z0, (0, 100), 0.1)
        >>> print(f"Energy drift: {results['relative_drift']:.2e}")
    """
    # Integrate trajectory
    times, states = integrate_trajectory_learned(model, params, z0, t_span, dt)

    # Compute energy at each timestep
    energies = model.batch_energy(params, states)

    # Energy conservation metrics
    E0 = energies[0]
    absolute_drift = jnp.abs(energies - E0)
    relative_drift = jnp.max(absolute_drift) / (jnp.abs(E0) + 1e-14)
    mean_drift = jnp.mean(absolute_drift) / (jnp.abs(E0) + 1e-14)

    results = {
        'initial_energy': float(E0),
        'final_energy': float(energies[-1]),
        'max_absolute_drift': float(jnp.max(absolute_drift)),
        'relative_drift': float(relative_drift),
        'mean_relative_drift': float(mean_drift),
        'times': np.array(times),
        'energies': np.array(energies)
    }

    return results


def compare_dynamics(
    model,
    params,
    true_dynamics: Callable,
    test_states: jnp.ndarray
) -> Dict:
    """
    Compare learned dynamics with true dynamics.

    Args:
        model: Trained HNN
        params: Model parameters
        true_dynamics: Function computing true dz/dt
        test_states: Test states (N, 2n)

    Returns:
        comparison: Dict with error metrics

    Example:
        >>> def true_dyn(z):  # Harmonic oscillator
        ...     q, p = z[:len(z)//2], z[len(z)//2:]
        ...     return jnp.concatenate([p, -q])
        >>> states = jnp.random.normal(jax.random.PRNGKey(0), (100, 4))
        >>> comparison = compare_dynamics(model, params, true_dyn, states)
        >>> print(f"Mean error: {comparison['mean_error']:.4f}")
    """
    # Predict dynamics
    predicted = model.batch_dynamics(params, test_states)

    # True dynamics
    true = jax.vmap(true_dynamics)(test_states)

    # Compute errors
    errors = predicted - true
    absolute_errors = jnp.abs(errors)
    relative_errors = absolute_errors / (jnp.abs(true) + 1e-10)

    comparison = {
        'mean_error': float(jnp.mean(absolute_errors)),
        'max_error': float(jnp.max(absolute_errors)),
        'mean_relative_error': float(jnp.mean(relative_errors)),
        'rmse': float(jnp.sqrt(jnp.mean(errors**2))),
        'num_samples': len(test_states)
    }

    return comparison


def benchmark_model(
    model,
    params,
    test_states: jnp.ndarray,
    num_runs: int = 100
) -> Dict:
    """
    Benchmark model inference speed.

    Args:
        model: HNN model
        params: Model parameters
        test_states: Test states (N, 2n)
        num_runs: Number of benchmark runs

    Returns:
        benchmark: Dict with timing results

    Example:
        >>> states = jnp.ones((1000, 4))
        >>> bench = benchmark_model(model, params, states, num_runs=100)
        >>> print(f"Inference time: {bench['mean_time_ms']:.2f} ms")
    """
    import time

    # Warm-up (JIT compilation)
    _ = model.batch_dynamics(params, test_states)

    # Benchmark
    times = []
    for _ in range(num_runs):
        start = time.time()
        _ = model.batch_dynamics(params, test_states)
        _ = jax.block_until_ready(_)  # Wait for computation
        elapsed = time.time() - start
        times.append(elapsed)

    times = np.array(times)

    benchmark = {
        'mean_time_ms': float(np.mean(times) * 1000),
        'std_time_ms': float(np.std(times) * 1000),
        'min_time_ms': float(np.min(times) * 1000),
        'max_time_ms': float(np.max(times) * 1000),
        'batch_size': len(test_states),
        'throughput_samples_per_sec': float(len(test_states) / np.mean(times)),
        'num_runs': num_runs
    }

    return benchmark


def visualize_phase_portrait(
    model,
    params,
    z0_list,
    t_span: Tuple[float, float],
    dt: float,
    save_path: Optional[str] = None
):
    """
    Visualize phase space trajectories.

    Args:
        model: Trained HNN
        params: Model parameters
        z0_list: List of initial conditions
        t_span: Time span
        dt: Timestep
        save_path: Optional path to save figure

    Example:
        >>> z0_list = [jnp.array([1, 0, 0, 1]), jnp.array([0, 1, 1, 0])]
        >>> visualize_phase_portrait(model, params, z0_list, (0, 20), 0.1)
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available for visualization")
        return

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    for z0 in z0_list:
        # Integrate
        times, states = integrate_trajectory_learned(model, params, z0, t_span, dt)

        n = len(z0) // 2
        q = states[:, :n]
        p = states[:, n:]

        # Plot q vs p for first dimension
        axes[0].plot(q[:, 0], p[:, 0], alpha=0.7)
        axes[0].set_xlabel('q₀')
        axes[0].set_ylabel('p₀')
        axes[0].set_title('Phase Portrait (dim 0)')
        axes[0].grid(alpha=0.3)

        # Plot energy over time
        energies = model.batch_energy(params, states)
        axes[1].plot(times, energies, alpha=0.7)

    axes[1].set_xlabel('Time')
    axes[1].set_ylabel('Energy')
    axes[1].set_title('Energy Conservation')
    axes[1].grid(alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Figure saved: {save_path}")
    else:
        plt.show()

    plt.close()


# Test code
if __name__ == "__main__":
    print("Testing model utilities...")

    from .hnn_architecture import create_hnn_model
    from .jax_utils import split_state, join_state

    # Create test model
    print("\n[1] Creating test model...")
    model, params = create_hnn_model(state_dim=4, hidden_dims=(32, 32), seed=0)
    n_params = count_parameters(params)
    print(f"  Parameters: {n_params:,}")

    # Test checkpointing
    print("\n[2] Testing checkpointing...")
    from .hnn_training import create_train_state
    state = create_train_state(model, params)
    save_checkpoint(state, 'test_checkpoint.pkl', metadata={'test': True})
    loaded_params, metadata = load_checkpoint('test_checkpoint.pkl')
    print(f"  Checkpoint loaded successfully")

    # Test trajectory integration
    print("\n[3] Testing trajectory integration...")
    z0 = jnp.array([1.0, 0.0, 0.0, 1.0])
    times, states = integrate_trajectory_learned(model, params, z0, (0, 5), dt=0.1)
    print(f"  Integrated trajectory: {len(times)} timesteps")
    print(f"  Initial state: {z0}")
    print(f"  Final state: {states[-1]}")

    # Test energy conservation
    print("\n[4] Testing energy conservation check...")
    results = verify_energy_conservation(model, params, z0, (0, 10), dt=0.1)
    print(f"  Initial energy: {results['initial_energy']:.6f}")
    print(f"  Final energy: {results['final_energy']:.6f}")
    print(f"  Relative drift: {results['relative_drift']:.2e}")

    # Test dynamics comparison
    print("\n[5] Testing dynamics comparison...")

    def harmonic_dynamics(z):
        q, p = split_state(z)
        return join_state(p, -q)

    test_states = jax.random.normal(jax.random.PRNGKey(0), (100, 4))
    comparison = compare_dynamics(model, params, harmonic_dynamics, test_states)
    print(f"  Mean error: {comparison['mean_error']:.6f}")
    print(f"  RMSE: {comparison['rmse']:.6f}")

    # Test benchmarking
    print("\n[6] Testing model benchmark...")
    bench = benchmark_model(model, params, test_states, num_runs=10)
    print(f"  Mean inference time: {bench['mean_time_ms']:.2f} ms")
    print(f"  Throughput: {bench['throughput_samples_per_sec']:.1f} samples/sec")

    print("\n✓ All utility tests passed!")

    # Cleanup
    import os
    if os.path.exists('test_checkpoint.pkl'):
        os.remove('test_checkpoint.pkl')
