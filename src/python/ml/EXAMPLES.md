# Conservation Training Examples

Quick reference with copy-paste examples for common use cases.

---

## Example 1: Harmonic Oscillator (2D)

Discover energy E = (q² + p²)/2 for simple harmonic oscillator.

```python
import jax
import jax.numpy as jnp
from ml import (
    create_conservation_hnn,
    two_stage_training,
    get_symmetry_transforms_3body
)

# Generate synthetic data
def harmonic_dynamics(z):
    """2D harmonic oscillator: dq/dt = p, dp/dt = -q"""
    q, p = z[:1], z[1:]
    return jnp.concatenate([p, -q])

key = jax.random.PRNGKey(42)
key, subkey = jax.random.split(key)

# Train: 5000 samples
train_states = jax.random.normal(subkey, (5000, 2)) * 2.0
train_derivatives = jax.vmap(harmonic_dynamics)(train_states)

# Val: 1000 samples
key, subkey = jax.random.split(key)
val_states = jax.random.normal(subkey, (1000, 2)) * 2.0
val_derivatives = jax.vmap(harmonic_dynamics)(val_states)

# Create model
model, params = create_conservation_hnn(
    state_dim=2,
    num_invariants=1,
    encoder_dims=(64, 64),
    hamiltonian_dims=(32, 16),
    invariant_dims=(32, 16),
    seed=0
)

# Train (no symmetries for simplicity)
final_state, history = two_stage_training(
    model, params,
    train_data=(train_states, train_derivatives),
    val_data=(val_states, val_derivatives),
    masses=jnp.array([1.0, 1.0, 1.0]),  # Dummy
    stage1_epochs=30,
    stage2_epochs=100,
    batch_size=256,
    learning_rate=1e-3,
    include_symmetries=False,  # Disable for 2D system
    verbose=True
)

# Extract invariant
test_states = jax.random.normal(jax.random.PRNGKey(123), (500, 2)) * 2.0
I_discovered = model.batch_invariant(final_state.params, test_states, inv_idx=0)

# Compare with true energy E = (q² + p²)/2
E_true = (test_states[:, 0]**2 + test_states[:, 1]**2) / 2

from scipy.stats import pearsonr
corr, _ = pearsonr(I_discovered, E_true)
print(f"\nCorrelation with energy: {corr:.6f}")
# Expected: > 0.99

# Plot
import matplotlib.pyplot as plt
plt.figure(figsize=(10, 4))

plt.subplot(1, 2, 1)
plt.scatter(E_true, I_discovered, alpha=0.5, s=10)
plt.xlabel('True Energy')
plt.ylabel('Discovered Invariant')
plt.title(f'Correlation: {corr:.4f}')

plt.subplot(1, 2, 2)
plt.plot(history['stage2'][-1]['val']['val_conservation_mean'])
plt.xlabel('Epoch')
plt.ylabel('Conservation Error')
plt.yscale('log')
plt.title('Training Progress')

plt.tight_layout()
plt.savefig('harmonic_oscillator_results.png', dpi=150)
print("✅ Saved to harmonic_oscillator_results.png")
```

**Expected output**:
```
Best conservation error: 3.45e-05
Correlation with energy: 0.9987
```

---

## Example 2: Complete 3-Body Pipeline

From data generation to trained model.

### Step 1: Generate Data

```python
from ml import (
    ParameterRanges,
    generate_lhs_samples,
    integrate_batch_parallel,
    TrajectoryDataset,
    augment_dataset
)

# Sample 100 initial conditions
param_ranges = ParameterRanges(
    mass_ratio=(0.1, 0.5),
    mass_3_ratio=(0.1, 1.0),
    energy=(-2.0, -0.5),
    angular_momentum=(1.0, 3.0),
    eccentricity=(0.0, 0.7)
)

initial_conditions = generate_lhs_samples(
    param_ranges,
    num_samples=100,
    seed=42
)

print(f"Generated {len(initial_conditions)} initial conditions")

# Integrate trajectories
trajectories = integrate_batch_parallel(
    initial_conditions,
    t_span=50.0,
    manifold_type='s1',
    num_workers=4
)

# Filter successful
trajectories = [t for t in trajectories if t.success]
print(f"Successfully integrated: {len(trajectories)}/{len(initial_conditions)}")

# Augment via symmetries (if equal masses)
augmented = []
for traj in trajectories:
    augmented.append(traj)
    # Only augment if masses are equal
    if jnp.allclose(traj.initial_condition.masses,
                    traj.initial_condition.masses[0]):
        from ml import augment_via_permutations, augment_via_time_reversal
        augmented.extend(augment_via_permutations(traj))
        augmented.append(augment_via_time_reversal(traj))

print(f"After augmentation: {len(augmented)} trajectories")

# Build HDF5 dataset
dataset = TrajectoryDataset('data/3body_example.h5')
dataset.create_structure(
    train_size=int(0.7 * len(augmented)),
    val_size=int(0.15 * len(augmented)),
    test_size=int(0.15 * len(augmented)),
    trajectory_length=trajectories[0].states.shape[0],
    state_dim=8  # S¹ bundle dimension
)

# Add trajectories
for i, traj in enumerate(augmented):
    if i < int(0.7 * len(augmented)):
        dataset.add_trajectory(traj, split='train')
    elif i < int(0.85 * len(augmented)):
        dataset.add_trajectory(traj, split='validation')
    else:
        dataset.add_trajectory(traj, split='test')

dataset.close()
print("✅ Dataset saved to data/3body_example.h5")
```

### Step 2: Train Model

```python
import h5py
import jax.numpy as jnp
from ml import create_conservation_hnn, two_stage_training

# Load data
with h5py.File('data/3body_example.h5', 'r') as f:
    train_states = jnp.array(f['train/states'][:])
    train_derivatives = jnp.array(f['train/derivatives'][:])
    val_states = jnp.array(f['validation/states'][:])
    val_derivatives = jnp.array(f['validation/derivatives'][:])
    masses = jnp.array(f['train/masses'][0])

print(f"Training: {train_states.shape}")
print(f"Validation: {val_states.shape}")
print(f"Masses: {masses}")

# Create model
model, params = create_conservation_hnn(
    state_dim=8,
    num_invariants=1,
    encoder_dims=(256, 256),
    hamiltonian_dims=(128, 64),
    invariant_dims=(128, 64),
    seed=42
)

# Train
final_state, history = two_stage_training(
    model, params,
    train_data=(train_states, train_derivatives),
    val_data=(val_states, val_derivatives),
    masses=masses,
    manifold_type='s1',
    stage1_epochs=50,
    stage2_epochs=150,
    batch_size=256,
    learning_rate=1e-3,
    include_symmetries=True,
    verbose=True
)

# Save
from ml import save_checkpoint
save_checkpoint(
    final_state,
    'checkpoints/3body_s1_inv0.pkl',
    metadata={
        'masses': masses.tolist(),
        'conservation_error': history['best_conservation_error']
    }
)

print(f"\n✅ Model saved: conservation error = {history['best_conservation_error']:.2e}")
```

### Step 3: Evaluate

```python
from ml import load_checkpoint, evaluate_conservation

# Load model
params, metadata = load_checkpoint('checkpoints/3body_s1_inv0.pkl')
print(f"Loaded model with conservation error: {metadata['conservation_error']:.2e}")

# Load test data
with h5py.File('data/3body_example.h5', 'r') as f:
    test_states = jnp.array(f['test/states'][:1000])
    test_derivatives = jnp.array(f['test/derivatives'][:1000])

# Evaluate
metrics = evaluate_conservation(
    final_state, model, (test_states, test_derivatives), inv_idx=0
)

print("\nTest Set Metrics:")
for key, value in metrics.items():
    print(f"  {key}: {value:.2e}" if isinstance(value, float) else f"  {key}: {value}")
```

---

## Example 3: Multiple Invariants (Integrable System)

Discover k independent invariants for Liouville integrability.

```python
from ml import create_conservation_hnn, two_stage_training, save_checkpoint

# Create model with 2 invariants
model, params = create_conservation_hnn(
    state_dim=4,  # 2D phase space
    num_invariants=2,  # Energy + another invariant
    encoder_dims=(256, 256),
    hamiltonian_dims=(128, 64),
    invariant_dims=(128, 64),
    seed=42
)

# Train first invariant (energy)
print("="*80)
print("TRAINING INVARIANT 0 (Energy)")
print("="*80)

state_inv0, history_inv0 = two_stage_training(
    model, params,
    train_data=(train_states, train_derivatives),
    val_data=(val_states, val_derivatives),
    masses=masses,
    inv_idx=0,  # First invariant
    stage1_epochs=50,
    stage2_epochs=150,
    verbose=True
)

save_checkpoint(state_inv0, 'checkpoints/inv0.pkl')
print(f"Invariant 0 conservation: {history_inv0['best_conservation_error']:.2e}")

# Train second invariant with involution constraint
print("\n" + "="*80)
print("TRAINING INVARIANT 1 (With {I0, I1} = 0 constraint)")
print("="*80)

# Start from previous state
state_inv1, history_inv1 = two_stage_training(
    model, state_inv0.params,  # Use learned parameters from inv0
    train_data=(train_states, train_derivatives),
    val_data=(val_states, val_derivatives),
    masses=masses,
    inv_idx=1,  # Second invariant
    stage1_epochs=30,  # Shorter (H already learned)
    stage2_epochs=150,
    verbose=True
)

# Update involution weight manually if needed
from ml import ConservationTrainState
state_inv1 = state_inv1.replace(lambda_involution=0.5)

save_checkpoint(state_inv1, 'checkpoints/inv1.pkl')
print(f"Invariant 1 conservation: {history_inv1['best_conservation_error']:.2e}")

# Check independence
I0 = model.batch_invariant(state_inv1.params, test_states, inv_idx=0)
I1 = model.batch_invariant(state_inv1.params, test_states, inv_idx=1)

import numpy as np
corr_matrix = np.corrcoef([I0, I1])
print("\nInvariant Correlation Matrix:")
print(corr_matrix)
print(f"Off-diagonal: {abs(corr_matrix[0, 1]):.4f}")

if abs(corr_matrix[0, 1]) < 0.3:
    print("✅ Invariants are independent")
else:
    print("⚠️  Invariants may be redundant")

# Check involution: {I0, I1} ≈ 0
from ml import involution_loss
invol = involution_loss(state_inv1.params, model, test_states, inv_idx_i=0, inv_idx_j=1)
print(f"Involution {{{I0, I1}}}: {invol:.2e}")

if invol < 1e-4:
    print("✅ Invariants are in involution")
```

---

## Example 4: Hyperparameter Search

Grid search over key hyperparameters.

```python
import itertools
from ml import create_conservation_hnn, two_stage_training

# Parameter grid
encoder_sizes = [(128, 128), (256, 256), (512, 512)]
learning_rates = [1e-3, 5e-4, 1e-4]
lambda_regs = [0.01, 0.05, 0.1]

results = []

for encoder_dims, lr, lambda_reg in itertools.product(
    encoder_sizes, learning_rates, lambda_regs
):
    config_name = f"enc{encoder_dims[0]}_lr{lr:.0e}_reg{lambda_reg:.2f}"
    print(f"\n{'='*80}")
    print(f"CONFIG: {config_name}")
    print(f"{'='*80}")

    # Create model
    model, params = create_conservation_hnn(
        state_dim=8,
        num_invariants=1,
        encoder_dims=encoder_dims,
        hamiltonian_dims=(encoder_dims[0]//2, encoder_dims[0]//4),
        invariant_dims=(encoder_dims[0]//2, encoder_dims[0]//4),
        seed=42
    )

    # Train
    try:
        final_state, history = two_stage_training(
            model, params,
            train_data=(train_states, train_derivatives),
            val_data=(val_states, val_derivatives),
            masses=masses,
            stage1_epochs=30,
            stage2_epochs=100,
            learning_rate=lr,
            verbose=False  # Suppress output for grid search
        )

        # Manually update regularization weight
        from ml import ConservationTrainState
        final_state = final_state.replace(lambda_regularization=lambda_reg)

        # Record results
        results.append({
            'config': config_name,
            'encoder_dims': encoder_dims,
            'learning_rate': lr,
            'lambda_regularization': lambda_reg,
            'conservation_error': history['best_conservation_error'],
            'best_epoch': history['best_epoch'],
            'invariant_variance': history['stage2'][-1]['val']['val_invariant_variance']
        })

        print(f"Conservation error: {history['best_conservation_error']:.2e}")

    except Exception as e:
        print(f"FAILED: {e}")
        results.append({
            'config': config_name,
            'conservation_error': float('inf'),
            'error': str(e)
        })

# Find best configuration
import pandas as pd
df = pd.DataFrame(results)
df = df.sort_values('conservation_error')

print("\n" + "="*80)
print("RESULTS (sorted by conservation error)")
print("="*80)
print(df.to_string())

best = df.iloc[0]
print(f"\n🏆 BEST CONFIG: {best['config']}")
print(f"   Conservation error: {best['conservation_error']:.2e}")
print(f"   Learning rate: {best['learning_rate']:.0e}")
print(f"   Encoder: {best['encoder_dims']}")
```

---

## Example 5: Visualizing Training Progress

Plot detailed training metrics.

```python
import matplotlib.pyplot as plt
import numpy as np

# After training
final_state, history = two_stage_training(...)

# Extract metrics
stage1_epochs = [h['epoch'] for h in history['stage1']]
stage1_train_loss = [h['train']['trajectory_loss'] for h in history['stage1']]
stage1_val_loss = [h['val']['val_trajectory_loss'] for h in history['stage1']]

stage2_epochs = [h['epoch'] + len(stage1_epochs) for h in history['stage2']]
stage2_total_loss = [h['train']['total_loss'] for h in history['stage2']]
stage2_traj_loss = [h['train']['trajectory_loss'] for h in history['stage2']]
stage2_cons_loss = [h['train']['conservation_loss'] for h in history['stage2']]
stage2_lambda = [h['lambda_conservation'] for h in history['stage2']]
stage2_val_cons = [h['val']['val_conservation_mean'] for h in history['stage2']]
stage2_inv_var = [h['val']['val_invariant_variance'] for h in history['stage2']]

# Create comprehensive plot
fig, axes = plt.subplots(2, 3, figsize=(15, 8))

# Stage 1: Trajectory loss
axes[0, 0].semilogy(stage1_epochs, stage1_train_loss, label='Train')
axes[0, 0].semilogy(stage1_epochs, stage1_val_loss, label='Val')
axes[0, 0].axvline(len(stage1_epochs), color='red', linestyle='--', alpha=0.5)
axes[0, 0].set_xlabel('Epoch')
axes[0, 0].set_ylabel('Trajectory Loss')
axes[0, 0].set_title('Stage 1: Hamiltonian Learning')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

# Stage 2: Total loss
axes[0, 1].semilogy(stage2_epochs, stage2_total_loss, label='Total')
axes[0, 1].semilogy(stage2_epochs, stage2_traj_loss, label='Trajectory', alpha=0.7)
axes[0, 1].semilogy(stage2_epochs, stage2_cons_loss, label='Conservation', alpha=0.7)
axes[0, 1].set_xlabel('Epoch')
axes[0, 1].set_ylabel('Loss')
axes[0, 1].set_title('Stage 2: Loss Components')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# Stage 2: Conservation error
axes[0, 2].semilogy(stage2_epochs, stage2_val_cons)
axes[0, 2].axhline(1e-4, color='green', linestyle='--', label='Threshold')
axes[0, 2].set_xlabel('Epoch')
axes[0, 2].set_ylabel(r'$\langle |\{I, H\}|^2 \rangle$')
axes[0, 2].set_title('Stage 2: Conservation Violation')
axes[0, 2].legend()
axes[0, 2].grid(True, alpha=0.3)

# Stage 2: Lambda schedule
axes[1, 0].plot(stage2_epochs, stage2_lambda)
axes[1, 0].set_xlabel('Epoch')
axes[1, 0].set_ylabel(r'$\lambda_{conservation}$')
axes[1, 0].set_title('Stage 2: Conservation Weight Schedule')
axes[1, 0].grid(True, alpha=0.3)

# Stage 2: Invariant variance
axes[1, 1].plot(stage2_epochs, stage2_inv_var)
axes[1, 1].axhline(0.01, color='orange', linestyle='--', label='Min threshold')
axes[1, 1].set_xlabel('Epoch')
axes[1, 1].set_ylabel('Invariant Variance')
axes[1, 1].set_title('Stage 2: Non-triviality Check')
axes[1, 1].legend()
axes[1, 1].grid(True, alpha=0.3)

# Summary text
summary_text = f"""
Best Epoch: {history['best_epoch']}
Conservation Error: {history['best_conservation_error']:.2e}
Final Inv Variance: {stage2_inv_var[-1]:.4f}

Stage 1: {len(stage1_epochs)} epochs
Stage 2: {len(stage2_epochs)} epochs
"""
axes[1, 2].text(0.1, 0.5, summary_text, fontsize=12, family='monospace',
                verticalalignment='center')
axes[1, 2].axis('off')
axes[1, 2].set_title('Training Summary')

plt.tight_layout()
plt.savefig('training_progress.png', dpi=150)
print("✅ Saved to training_progress.png")
```

---

## Example 6: Conservation Verification on Test Trajectory

Integrate trajectory and verify invariant conservation.

```python
from ml import integrate_trajectory_learned, load_checkpoint
import jax.numpy as jnp

# Load model
params, metadata = load_checkpoint('checkpoints/3body_s1_inv0.pkl')

# Get initial condition from test set
with h5py.File('data/3body_example.h5', 'r') as f:
    z0 = jnp.array(f['test/states'][0])

# Integrate with learned Hamiltonian
times, traj = integrate_trajectory_learned(
    model, params, z0, t_span=100.0, dt=0.01
)

print(f"Integrated {len(times)} timesteps")

# Compute invariant along trajectory
I_traj = model.batch_invariant(params, traj, inv_idx=0)

# Compute conservation error
I_initial = I_traj[0]
I_drift_abs = jnp.max(jnp.abs(I_traj - I_initial))
I_drift_rel = I_drift_abs / jnp.abs(I_initial)

print(f"\nInvariant conservation:")
print(f"  Initial value: {I_initial:.6f}")
print(f"  Final value: {I_traj[-1]:.6f}")
print(f"  Absolute drift: {I_drift_abs:.2e}")
print(f"  Relative drift: {I_drift_rel:.2e}")

if I_drift_rel < 1e-3:
    print("  ✅ Excellent conservation")
elif I_drift_rel < 1e-2:
    print("  ✓ Good conservation")
else:
    print("  ⚠️  Poor conservation - check model quality")

# Plot
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(15, 4))

# Trajectory in phase space (first 2 coordinates)
axes[0].plot(traj[:, 0], traj[:, 1], linewidth=0.5)
axes[0].scatter(traj[0, 0], traj[0, 1], c='green', s=100, marker='o', label='Start')
axes[0].scatter(traj[-1, 0], traj[-1, 1], c='red', s=100, marker='x', label='End')
axes[0].set_xlabel('$q_1$')
axes[0].set_ylabel('$q_2$')
axes[0].set_title('Phase Space Trajectory')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Invariant vs time
axes[1].plot(times, I_traj)
axes[1].axhline(I_initial, color='red', linestyle='--', label='Initial')
axes[1].set_xlabel('Time')
axes[1].set_ylabel('$I(z)$')
axes[1].set_title('Conserved Quantity')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

# Relative error vs time
axes[2].semilogy(times, jnp.abs((I_traj - I_initial) / I_initial))
axes[2].axhline(1e-3, color='orange', linestyle='--', label='Good threshold')
axes[2].set_xlabel('Time')
axes[2].set_ylabel('Relative Error')
axes[2].set_title('Conservation Violation')
axes[2].legend()
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('trajectory_conservation.png', dpi=150)
print("\n✅ Saved to trajectory_conservation.png")
```

---

## Example 7: Custom Loss Weights During Training

Manually adjust loss weights for specific needs.

```python
from ml import (
    create_conservation_hnn,
    create_conservation_train_state,
    train_epoch,
    evaluate_conservation
)
import jax.numpy as jnp

# Create model and state
model, params = create_conservation_hnn(state_dim=8, num_invariants=1)
state = create_conservation_train_state(model, params, stage=2)

# Custom training loop with dynamic weights
from ml import get_symmetry_transforms_3body

symmetry_transforms = get_symmetry_transforms_3body(masses, manifold_type='s1')

# Simple data loader
def make_batches(states, derivatives, batch_size):
    n = len(states)
    for i in range(0, n, batch_size):
        yield (states[i:i+batch_size], derivatives[i:i+batch_size])

for epoch in range(200):
    # Dynamic weight adjustment
    if epoch < 50:
        # Phase 1: Focus on dynamics
        state = state.replace(
            lambda_conservation=0.0,
            lambda_noether=0.0,
            lambda_regularization=0.0
        )
    elif epoch < 100:
        # Phase 2: Gradually add conservation
        progress = (epoch - 50) / 50
        state = state.replace(
            lambda_conservation=progress,
            lambda_noether=0.1,
            lambda_regularization=0.01
        )
    elif epoch < 150:
        # Phase 3: Strong conservation + regularization
        state = state.replace(
            lambda_conservation=1.0,
            lambda_noether=0.1,
            lambda_regularization=0.1  # Increased
        )
    else:
        # Phase 4: Maximum enforcement
        state = state.replace(
            lambda_conservation=2.0,  # Emphasis on conservation
            lambda_noether=0.5,
            lambda_regularization=0.1
        )

    # Train epoch
    train_batches = list(make_batches(train_states, train_derivatives, 256))
    state, train_metrics = train_epoch(
        state, model, train_batches, symmetry_transforms, inv_idx=0
    )

    # Evaluate every 10 epochs
    if epoch % 10 == 0:
        val_metrics = evaluate_conservation(
            state, model, (val_states[:1000], val_derivatives[:1000]), inv_idx=0
        )
        print(f"Epoch {epoch:3d}: "
              f"λ_cons={state.lambda_conservation:.2f}, "
              f"λ_reg={state.lambda_regularization:.2f}, "
              f"Conservation: {val_metrics['val_conservation_mean']:.2e}")

print("Custom training complete!")
```

---

## Example 8: Comparing ML vs Geometric Invariants

Compare Task 3.2 (ML) with Task 3.1 (geometric).

```python
# Assume WP 3.1 geometric invariant available
# (This is a placeholder - actual integration depends on WP 3.1 implementation)

from ml import load_checkpoint
import jax.numpy as jnp

# Load ML-discovered invariant
params_ml, _ = load_checkpoint('checkpoints/3body_s1_inv0.pkl')

# Load test data
test_states = ...  # (N, 8)

# Compute ML invariant
I_ml = model.batch_invariant(params_ml, test_states, inv_idx=0)

# Compute geometric invariant (placeholder)
# from killing_pde_solver import evaluate_geometric_invariant
# I_geometric = evaluate_geometric_invariant(test_states)

# For demonstration, use energy as "geometric" reference
def compute_energy_s1(state):
    """Compute energy on S¹ bundle"""
    # This is simplified - actual implementation depends on bundle structure
    # ... calculate kinetic + potential energy
    return energy

I_geometric = jax.vmap(compute_energy_s1)(test_states)

# Compare
from scipy.stats import pearsonr, spearmanr
pearson_corr, _ = pearsonr(I_ml, I_geometric)
spearman_corr, _ = spearmanr(I_ml, I_geometric)

print("ML vs Geometric Invariant Comparison:")
print(f"  Pearson correlation: {pearson_corr:.6f}")
print(f"  Spearman correlation: {spearman_corr:.6f}")

if abs(pearson_corr) > 0.95:
    print("  ✅ Strong agreement - likely same invariant")
elif abs(pearson_corr) > 0.7:
    print("  ✓ Moderate agreement - related invariants")
else:
    print("  ⚠️  Weak agreement - different invariants or method issue")

# Scatter plot
import matplotlib.pyplot as plt
plt.figure(figsize=(8, 8))
plt.scatter(I_geometric, I_ml, alpha=0.5, s=10)
plt.xlabel('Geometric Invariant (WP 3.1)')
plt.ylabel('ML Invariant (WP 3.2)')
plt.title(f'Correlation: {pearson_corr:.4f}')

# Add diagonal
lims = [min(plt.xlim()[0], plt.ylim()[0]), max(plt.xlim()[1], plt.ylim()[1])]
plt.plot(lims, lims, 'r--', alpha=0.5, label='Perfect match')
plt.legend()
plt.grid(True, alpha=0.3)

plt.savefig('ml_vs_geometric_comparison.png', dpi=150)
print("✅ Saved to ml_vs_geometric_comparison.png")
```

---

## Quick Command Reference

```python
# Create model
from ml import create_conservation_hnn
model, params = create_conservation_hnn(state_dim=8, num_invariants=1)

# Train
from ml import two_stage_training
final_state, history = two_stage_training(
    model, params, train_data=..., val_data=..., masses=...
)

# Evaluate
from ml import evaluate_conservation
metrics = evaluate_conservation(final_state, model, test_data, inv_idx=0)

# Save/Load
from ml import save_checkpoint, load_checkpoint
save_checkpoint(final_state, 'model.pkl')
params, metadata = load_checkpoint('model.pkl')

# Compute invariant
I = model.batch_invariant(params, states, inv_idx=0)

# Integrate trajectory
from ml import integrate_trajectory_learned
times, traj = integrate_trajectory_learned(model, params, z0, t_span=100.0)
```

---

**End of Examples**

For detailed explanations, see `CONSERVATION_TRAINING_GUIDE.md`.
