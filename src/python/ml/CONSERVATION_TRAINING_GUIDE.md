# Conservation-Constrained Training Guide

**Task 3.2.3: Discovering Conserved Quantities via Physics-Informed Neural Networks**

This guide provides practical instructions for using the conservation-constrained training pipeline to discover conserved quantities in Hamiltonian systems.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [End-to-End Example](#end-to-end-example)
3. [Understanding the Output](#understanding-the-output)
4. [Hyperparameter Tuning](#hyperparameter-tuning)
5. [Interpreting Discovered Invariants](#interpreting-discovered-invariants)
6. [Common Pitfalls](#common-pitfalls)
7. [Advanced Usage](#advanced-usage)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Minimal Working Example

```python
from ml import (
    create_conservation_hnn,
    two_stage_training,
    get_symmetry_transforms_3body
)
import jax.numpy as jnp

# 1. Create model
model, params = create_conservation_hnn(
    state_dim=8,              # 4D phase space on S¹ bundle
    num_invariants=1,         # Discover 1 conserved quantity
    seed=42
)

# 2. Prepare data (from Task 3.2.1)
train_states = ...    # (N_train, 8) array
train_derivatives = ...  # (N_train, 8) array
val_states = ...      # (N_val, 8) array
val_derivatives = ...    # (N_val, 8) array

# 3. Train with two-stage pipeline
masses = jnp.array([1.0, 0.5, 0.3])  # Body masses

final_state, history = two_stage_training(
    model, params,
    train_data=(train_states, train_derivatives),
    val_data=(val_states, val_derivatives),
    masses=masses,
    stage1_epochs=50,
    stage2_epochs=150,
    verbose=True
)

# 4. Check results
print(f"Best conservation error: {history['best_conservation_error']:.2e}")
print(f"Discovered at epoch: {history['best_epoch']}")
```

That's it! The pipeline will:
- **Stage 1**: Learn accurate dynamics H_θ
- **Stage 2**: Discover conserved quantity I_φ with {I_φ, H_θ} ≈ 0

---

## End-to-End Example

### Step 1: Generate Training Data

Use Task 3.2.1 data generation pipeline:

```python
from ml import (
    ParameterRanges,
    generate_lhs_samples,
    integrate_batch_parallel,
    TrajectoryDataset
)

# 1.1 Sample initial conditions
param_ranges = ParameterRanges(
    mass_ratio=(0.1, 0.5),
    mass_3_ratio=(0.1, 1.0),
    energy=(-2.0, -0.5),
    angular_momentum=(1.0, 3.0),
    eccentricity=(0.0, 0.7)
)

initial_conditions = generate_lhs_samples(
    param_ranges,
    num_samples=500,
    seed=42
)

# 1.2 Integrate trajectories
trajectories = integrate_batch_parallel(
    initial_conditions,
    t_span=100.0,
    manifold_type='s1',
    num_workers=4
)

# Filter successful trajectories
trajectories = [t for t in trajectories if t.success]
print(f"Successfully integrated: {len(trajectories)} trajectories")

# 1.3 Build dataset
from ml import TrajectoryDataset

dataset = TrajectoryDataset('data/3body_s1_dataset.h5')
dataset.create_structure(
    train_size=400,
    val_size=50,
    test_size=50,
    trajectory_length=10000,
    state_dim=8
)

# Add trajectories
for i, traj in enumerate(trajectories):
    split = 'train' if i < 400 else ('validation' if i < 450 else 'test')
    dataset.add_trajectory(traj, split=split)

dataset.close()
```

### Step 2: Load and Preprocess Data

```python
import h5py
import jax.numpy as jnp

# Load dataset
with h5py.File('data/3body_s1_dataset.h5', 'r') as f:
    train_states = jnp.array(f['train/states'][:])
    train_derivatives = jnp.array(f['train/derivatives'][:])
    val_states = jnp.array(f['validation/states'][:])
    val_derivatives = jnp.array(f['validation/derivatives'][:])

    # Get masses from first trajectory
    masses = jnp.array(f['train/masses'][0])

print(f"Training set: {train_states.shape}")
print(f"Validation set: {val_states.shape}")
print(f"Masses: {masses}")
```

### Step 3: Create and Configure Model

```python
from ml import create_conservation_hnn

# Create ConservationHNN
model, params = create_conservation_hnn(
    state_dim=8,              # S¹ bundle: (x, y, θ, vx, vy, ω)_1,2 or 4D
    num_invariants=1,         # Start with 1 invariant
    encoder_dims=(256, 256),  # Shared encoder
    hamiltonian_dims=(128, 64),
    invariant_dims=(128, 64),
    activation='tanh',        # Smooth activations for physics
    use_layer_norm=False,     # Can help with deep networks
    seed=42
)

# Count parameters
from ml import count_parameters
n_params = count_parameters(params)
print(f"Model has {n_params:,} parameters")
```

### Step 4: Configure Training

```python
from ml import two_stage_training, get_symmetry_transforms_3body

# Get symmetry transforms for 3-body problem
symmetry_transforms = get_symmetry_transforms_3body(
    masses,
    manifold_type='s1',
    include_time_reversal=True,
    include_permutations=True,  # Only if equal masses
    include_rotations=False,     # Optional
    include_virial=False         # Optional for scaling symmetry
)

print(f"Using {len(symmetry_transforms)} symmetry transforms")

# Configure training
training_config = {
    # Data
    'train_data': (train_states, train_derivatives),
    'val_data': (val_states, val_derivatives),
    'masses': masses,
    'manifold_type': 's1',

    # Training schedule
    'stage1_epochs': 50,      # Hamiltonian warm-up
    'stage2_epochs': 150,     # Conservation discovery
    'batch_size': 256,

    # Optimization
    'learning_rate': 1e-3,
    'warmup_steps': 1000,

    # Conservation constraint
    'lambda_conservation_schedule': 'linear',  # or 'exponential', 'cosine'
    'lambda_warmup_epochs': 50,  # Gradually increase λ

    # Symmetries
    'include_symmetries': True,

    # Invariant selection
    'inv_idx': 0,  # Train first invariant

    # Early stopping
    'early_stopping_patience': 20,
    'conservation_threshold': 1e-4,  # Success criterion

    # Verbosity
    'verbose': True
}
```

### Step 5: Train Model

```python
# Run two-stage training
final_state, history = two_stage_training(
    model, params, **training_config
)

# Results
print("\n" + "="*80)
print("TRAINING RESULTS")
print("="*80)
print(f"Best conservation error: {history['best_conservation_error']:.2e}")
print(f"Best epoch: {history['best_epoch']}")
print(f"Stage 1 epochs: {len(history['stage1'])}")
print(f"Stage 2 epochs: {len(history['stage2'])}")

# Check success
if history['best_conservation_error'] < training_config['conservation_threshold']:
    print("✅ SUCCESS: Conserved quantity discovered!")
else:
    print("⚠️  WARNING: Conservation threshold not reached")
    print("   Consider: longer training, different hyperparameters, or data quality")
```

### Step 6: Evaluate Discovered Invariant

```python
from ml import evaluate_conservation, compute_conservation_violation

# Detailed evaluation
eval_metrics = evaluate_conservation(
    final_state, model, (val_states[:1000], val_derivatives[:1000]), inv_idx=0
)

print("\nValidation Metrics:")
print(f"  Trajectory loss: {eval_metrics['val_trajectory_loss']:.6f}")
print(f"  Conservation violation (mean): {eval_metrics['val_conservation_mean']:.2e}")
print(f"  Conservation violation (max): {eval_metrics['val_conservation_max']:.2e}")
print(f"  Conservation violation (median): {eval_metrics['val_conservation_median']:.2e}")
print(f"  Invariant variance: {eval_metrics['val_invariant_variance']:.6f}")
print(f"  Invariant mean: {eval_metrics['val_invariant_mean']:.6f}")
print(f"  Invariant std: {eval_metrics['val_invariant_std']:.6f}")

# Variance check: non-trivial invariant should have variance > 0.01
if eval_metrics['val_invariant_variance'] < 0.01:
    print("\n⚠️  WARNING: Invariant has very low variance - may be trivial (constant)")
```

### Step 7: Save Model

```python
from ml import save_checkpoint

# Save final model
save_checkpoint(
    final_state,
    filepath='checkpoints/conservation_hnn_inv0_best.pkl',
    metadata={
        'model_config': {
            'state_dim': 8,
            'num_invariants': 1,
            'encoder_dims': (256, 256),
            'hamiltonian_dims': (128, 64),
            'invariant_dims': (128, 64)
        },
        'training_config': training_config,
        'best_conservation_error': history['best_conservation_error'],
        'best_epoch': history['best_epoch'],
        'masses': masses.tolist(),
        'manifold_type': 's1'
    }
)

print("\n✅ Model saved to checkpoints/conservation_hnn_inv0_best.pkl")
```

---

## Understanding the Output

### Training Progress

During training, you'll see output like:

```
================================================================================
STAGE 1: HAMILTONIAN WARM-UP
================================================================================
Epoch   0/50: Train Loss: 0.123456, Val Loss: 0.134567, Grad Norm: 2.345678
Epoch  10/50: Train Loss: 0.023456, Val Loss: 0.025678, Grad Norm: 0.456789
...

Stage 1 complete in 45.2s
Final trajectory loss: 0.001234

================================================================================
STAGE 2: CONSERVATION DISCOVERY
================================================================================
Epoch   0/150: λ_cons=0.000, Total Loss: 0.001234, Conservation: 1.23e-02, I_var: 0.456789
Epoch  10/150: λ_cons=0.200, Total Loss: 0.002345, Conservation: 5.67e-03, I_var: 0.567890
Epoch  50/150: λ_cons=1.000, Total Loss: 0.003456, Conservation: 1.23e-04, I_var: 0.678901
...

🎯 Conservation threshold reached at epoch 87!
   {I, H} mean: 9.87e-05 < 1.00e-04
```

### Key Metrics

**Stage 1 (Hamiltonian Warm-up)**:
- **Train/Val Loss**: Should decrease to ~10⁻³ - 10⁻⁴
  - Measures how well H_θ predicts dynamics: ||dz/dt - J∇H||²
  - Lower = more accurate dynamics
- **Grad Norm**: Should stabilize (not explode or vanish)
  - Typical values: 0.1 - 2.0

**Stage 2 (Conservation Discovery)**:
- **λ_cons**: Conservation weight (0 → 1)
  - Gradually increases to prevent mode collapse
- **Total Loss**: Combined loss function
  - May initially increase as conservation constraint added
  - Should decrease overall as training progresses
- **Conservation**: Mean |{I_φ, H_θ}|²
  - **Target**: < 10⁻⁴ (success)
  - **Good**: < 10⁻³
  - **Needs work**: > 10⁻²
- **I_var**: Invariant variance
  - **Non-trivial**: > 0.01
  - **Suspicious**: < 0.001 (may be constant)

### Training History Structure

```python
history = {
    'stage1': [
        {
            'epoch': 0,
            'train': {'trajectory_loss': ..., 'grad_norm': ...},
            'val': {'val_trajectory_loss': ..., 'val_energy_error': ...}
        },
        ...
    ],
    'stage2': [
        {
            'epoch': 0,
            'lambda_conservation': 0.0,
            'train': {'total_loss': ..., 'trajectory_loss': ...,
                     'conservation_loss': ..., 'noether_loss': ..., ...},
            'val': {'val_conservation_mean': ..., 'val_invariant_variance': ...}
        },
        ...
    ],
    'best_conservation_error': 9.87e-05,
    'best_epoch': 87
}
```

---

## Hyperparameter Tuning

### Critical Hyperparameters

#### 1. Model Architecture

```python
model, params = create_conservation_hnn(
    state_dim=8,
    num_invariants=1,

    # CRITICAL: Network depth and width
    encoder_dims=(256, 256),        # Shared feature extraction
    hamiltonian_dims=(128, 64),     # H_θ head
    invariant_dims=(128, 64),       # I_φ head

    # Activation function
    activation='tanh',  # Smooth for physics (default)
    # activation='swish'  # Alternative: try if tanh doesn't work
)
```

**Guidelines**:
- **Deeper networks** (more layers): Better for complex systems
  - Try: `encoder_dims=(256, 256, 128)` or `(512, 512, 256)`
- **Wider networks** (more units): More representational power
  - Try: `encoder_dims=(512, 512)` or `(1024, 512)`
- **Shared encoder**: Should be largest (most capacity)
- **Head networks**: Can be smaller (specialized tasks)
- **Activation**: `tanh` is standard for physics; `swish`/`gelu` sometimes help

**How to tune**:
1. Start with default: `encoder=(256,256)`, heads=`(128,64)`
2. If conservation error plateaus high (> 10⁻³): **Increase capacity**
3. If overfitting (train << val loss): **Decrease capacity** or add regularization
4. Typical parameter count: 100K - 500K (use `count_parameters`)

#### 2. Training Schedule

```python
training_config = {
    # Stage durations
    'stage1_epochs': 50,      # DEFAULT: 30-50
    'stage2_epochs': 150,     # DEFAULT: 100-200

    # Learning rate
    'learning_rate': 1e-3,    # DEFAULT: 1e-3
    'warmup_steps': 1000,     # DEFAULT: 1000

    # Conservation constraint ramping
    'lambda_conservation_schedule': 'linear',  # 'linear', 'exponential', 'cosine'
    'lambda_warmup_epochs': 50,  # DEFAULT: 50 (stage2_epochs / 3)
}
```

**Guidelines**:
- **stage1_epochs**:
  - Too few (< 20): H_θ not accurate, Stage 2 fails
  - Too many (> 100): Diminishing returns, longer training
  - **Recommended**: 40-60
- **stage2_epochs**:
  - Too few (< 50): Conservation constraint not satisfied
  - Too many (> 300): Overfitting risk
  - **Recommended**: 100-200
- **learning_rate**:
  - Too high (> 3e-3): Training unstable, divergence
  - Too low (< 1e-4): Very slow convergence
  - **Recommended**: 1e-3 to 3e-4
  - **Tip**: If loss plateaus early, reduce to 3e-4 or 1e-4
- **lambda_warmup_epochs**:
  - Too fast (< 20): Mode collapse (trivial solutions)
  - Too slow (> stage2_epochs): Constraint never enforced
  - **Recommended**: stage2_epochs / 3 to stage2_epochs / 2

**How to tune**:
1. **First run**: Use defaults
2. **If Stage 1 loss > 10⁻³**: Increase `stage1_epochs` or `learning_rate`
3. **If Stage 2 conservation plateaus**: Increase `stage2_epochs` or model capacity
4. **If trivial solutions** (low variance): Slow down `lambda_warmup_epochs`

#### 3. Loss Weights

```python
# In conservation_training.py, ConservationTrainState:
state = state.replace(
    lambda_conservation=1.0,     # DEFAULT: 1.0
    lambda_noether=0.1,          # DEFAULT: 0.1
    lambda_regularization=0.01,  # DEFAULT: 0.01
    lambda_involution=0.1        # DEFAULT: 0.1 (if num_invariants > 1)
)
```

**Guidelines**:
- **lambda_conservation**: Main constraint {I, H} = 0
  - **Don't change** (always 1.0 after warmup)
- **lambda_noether**: Symmetry-based regularization
  - Increase (0.5-1.0): Stronger symmetry enforcement
  - Decrease (0.01-0.05): Weaker, more flexibility
  - **Recommended**: 0.1
- **lambda_regularization**: Prevent trivial solutions
  - Increase (0.1-0.5): Stronger penalty on constants/coordinates
  - Decrease (0.001-0.01): Less aggressive
  - **Recommended**: 0.01-0.05
- **lambda_involution**: Multiple invariants commute
  - Only relevant if `num_invariants > 1`
  - **Recommended**: 0.1

**How to tune**:
1. **Start with defaults**: λ_cons=1.0, λ_noeth=0.1, λ_reg=0.01
2. **If trivial solutions** (I ≈ constant): **Increase λ_reg** to 0.1
3. **If symmetries violated**: **Increase λ_noeth** to 0.5
4. **If conservation error stuck**: Check data quality, not weights

#### 4. Data Configuration

```python
training_config = {
    'batch_size': 256,    # DEFAULT: 256
}
```

**Guidelines**:
- **batch_size**:
  - Too small (< 64): Noisy gradients, slow convergence
  - Too large (> 1024): Less gradient updates, may underfit
  - **Memory limit**: Larger batches need more GPU memory
  - **Recommended**: 128-512

**How to tune**:
1. **Default**: 256
2. **If GPU memory error**: Reduce to 128 or 64
3. **If convergence very slow**: Increase to 512
4. **For large datasets** (> 100K samples): 512-1024

### Tuning Workflow

**Step 1**: Baseline run with all defaults
```python
final_state, history = two_stage_training(
    model, params,
    train_data=..., val_data=..., masses=...,
    # All defaults
    verbose=True
)
```

**Step 2**: Diagnose issues
- **High Stage 1 loss** (> 10⁻³):
  - Increase `stage1_epochs` (e.g., 50 → 100)
  - Increase model capacity
  - Check data quality
- **High Stage 2 conservation** (> 10⁻³):
  - Increase `stage2_epochs` (e.g., 150 → 300)
  - Increase model capacity
  - Slow down λ warmup
- **Trivial invariant** (variance < 0.01):
  - Increase `lambda_regularization` (0.01 → 0.1)
  - Slow down λ warmup
  - Check initialization
- **Symmetry violations**:
  - Increase `lambda_noether` (0.1 → 0.5)
  - Verify symmetry transforms are correct

**Step 3**: Iterate
- Change one hyperparameter at a time
- Keep best configuration
- Typical tuning: 5-10 runs

### Recommended Configurations

**Small systems** (harmonic oscillator, 2-body Kepler):
```python
encoder_dims=(128, 128)
hamiltonian_dims=(64, 32)
invariant_dims=(64, 32)
stage1_epochs=30
stage2_epochs=100
learning_rate=1e-3
batch_size=256
```

**Medium systems** (3-body, S¹ bundle):
```python
encoder_dims=(256, 256)
hamiltonian_dims=(128, 64)
invariant_dims=(128, 64)
stage1_epochs=50
stage2_epochs=150
learning_rate=1e-3
batch_size=256
```

**Complex systems** (4-body, KS regularization):
```python
encoder_dims=(512, 512, 256)
hamiltonian_dims=(256, 128)
invariant_dims=(256, 128)
stage1_epochs=100
stage2_epochs=300
learning_rate=5e-4
batch_size=128
```

---

## Interpreting Discovered Invariants

### Step 1: Extract Invariant Function

```python
from ml import load_checkpoint

# Load trained model
params, metadata = load_checkpoint('checkpoints/conservation_hnn_inv0_best.pkl')

# Extract invariant values on test set
test_states = ...  # (N_test, state_dim)

I_values = model.batch_invariant(params, test_states, inv_idx=0)
print(f"Invariant statistics:")
print(f"  Mean: {jnp.mean(I_values):.6f}")
print(f"  Std: {jnp.std(I_values):.6f}")
print(f"  Min: {jnp.min(I_values):.6f}")
print(f"  Max: {jnp.max(I_values):.6f}")
```

### Step 2: Verify Conservation Along Trajectories

```python
from ml import integrate_trajectory_learned

# Integrate test trajectory with learned Hamiltonian
z0 = test_states[0]
times, states_pred = integrate_trajectory_learned(
    model, params, z0, t_span=100.0, dt=0.01
)

# Compute invariant along trajectory
I_traj = model.batch_invariant(params, states_pred, inv_idx=0)

# Check drift
I_drift = jnp.max(jnp.abs(I_traj - I_traj[0])) / jnp.abs(I_traj[0])
print(f"Invariant relative drift: {I_drift:.2e}")

# Plot
import matplotlib.pyplot as plt
plt.figure(figsize=(10, 4))
plt.subplot(1, 2, 1)
plt.plot(times, I_traj)
plt.xlabel('Time')
plt.ylabel('I(z)')
plt.title('Conserved Quantity Along Trajectory')

plt.subplot(1, 2, 2)
plt.plot(times, (I_traj - I_traj[0]) / I_traj[0])
plt.xlabel('Time')
plt.ylabel('Relative Drift')
plt.title('Conservation Violation')
plt.tight_layout()
plt.savefig('invariant_conservation.png')
```

**Expected**: Relative drift < 10⁻³ for well-learned invariants

### Step 3: Compare with Known Invariants

If you know the true invariants (e.g., energy, angular momentum):

```python
# Example: 3-body problem energy
def compute_energy(state):
    """Compute total energy E = T + V"""
    # Extract positions and velocities from state
    q, p = split_state(state)  # Depends on manifold type
    # ... compute kinetic and potential energy
    return T + V

# Compute true energy
E_true = jax.vmap(compute_energy)(test_states)

# Compare with discovered invariant
from scipy.stats import pearsonr
correlation, p_value = pearsonr(I_values, E_true)

print(f"Correlation with energy: {correlation:.6f} (p={p_value:.2e})")

# Scatter plot
plt.figure(figsize=(6, 6))
plt.scatter(E_true, I_values, alpha=0.5, s=10)
plt.xlabel('True Energy')
plt.ylabel('Discovered Invariant')
plt.title(f'Correlation: {correlation:.4f}')
plt.savefig('invariant_vs_energy.png')
```

**Expected**: High correlation (> 0.95) with known invariants

### Step 4: Functional Form Analysis

Attempt to reverse-engineer the functional form:

```python
# Test different functional forms
import numpy as np

# Candidate forms for 2D harmonic oscillator
candidates = {
    'E = (q² + p²)/2': lambda z: (z[0]**2 + z[1]**2) / 2,
    'q² only': lambda z: z[0]**2,
    'p² only': lambda z: z[1]**2,
    'qp': lambda z: z[0] * z[1],
}

for name, func in candidates.items():
    candidate_values = jax.vmap(func)(test_states)
    corr, _ = pearsonr(I_values, candidate_values)
    print(f"{name}: correlation = {corr:.6f}")

# Best match
# E = (q² + p²)/2: correlation = 0.9998  ← Discovered energy!
```

### Step 5: Independence Testing

If discovering multiple invariants:

```python
from ml import MultiInvariantHNN, involution_loss

# Train model with num_invariants=2
model, params = create_conservation_hnn(state_dim=8, num_invariants=2)
final_state, history = two_stage_training(...)

# Extract both invariants
I0_values = model.batch_invariant(params, test_states, inv_idx=0)
I1_values = model.batch_invariant(params, test_states, inv_idx=1)

# Check functional independence
corr, _ = pearsonr(I0_values, I1_values)
print(f"Correlation between I0 and I1: {corr:.6f}")

if abs(corr) < 0.3:
    print("✅ Invariants are functionally independent")
else:
    print("⚠️  Invariants may be redundant")

# Check involution: {I0, I1} ≈ 0
test_batch = (test_states[:1000], None)
invol_loss = involution_loss(params, model, test_states[:1000], inv_idx_i=0, inv_idx_j=1)
print(f"Involution constraint {I0, I1}: {invol_loss:.2e}")
```

**Expected**:
- Correlation < 0.3 (independent)
- Involution loss < 10⁻⁴ (in involution)

### Step 6: Physical Interpretation

For 3-body problem, discovered invariants typically correspond to:

1. **Energy** (H): Always discovered first
   - Linear scaling with kinetic + potential terms
   - Negative for bound orbits
   - Correlation with Hamiltonian: ~1.0

2. **Angular momentum** (L_z): Planar systems
   - Component perpendicular to plane
   - Conserved if no external torques
   - Test: Check if I ∝ Σ(r × v)_z

3. **Higher-order integrals**: Non-integrable systems
   - May not have simple closed form
   - Emergent from system's symmetries
   - Valuable even if analytically unknown!

**Validation checklist**:
- [ ] Conserved along trajectories (drift < 10⁻³)
- [ ] Non-trivial (variance > 0.01)
- [ ] Satisfies {I, H} ≈ 0 (< 10⁻⁴)
- [ ] Respects symmetries: I(σ(z)) ≈ I(z)
- [ ] Independent from other invariants (if multiple)
- [ ] Physical interpretation (if possible)

---

## Common Pitfalls

### 1. Trivial Solutions

**Problem**: Invariant is constant (I ≈ c for all states)

**Symptoms**:
- Very low variance: `val_invariant_variance < 0.001`
- High correlation with constant: I_values ≈ mean(I_values)
- Conservation trivially satisfied

**Causes**:
- λ_conservation increased too quickly
- Insufficient regularization
- Poor initialization

**Solutions**:
```python
# Slow down conservation weight ramping
'lambda_warmup_epochs': 100,  # Instead of 50

# Increase regularization
state = state.replace(lambda_regularization=0.1)  # Instead of 0.01

# Try different initialization seed
model, params = create_conservation_hnn(..., seed=123)  # Instead of 42
```

### 2. Coordinate Solutions

**Problem**: Invariant is just a coordinate (I ≈ q₁ or I ≈ p₁)

**Symptoms**:
- High correlation with single coordinate
- Not physically meaningful

**Causes**:
- Weak regularization
- Insufficient data diversity

**Solutions**:
```python
# Increase regularization
state = state.replace(lambda_regularization=0.1)

# Verify data covers phase space
print(f"q range: {jnp.min(train_states[:, :n])} to {jnp.max(train_states[:, :n])}")
print(f"p range: {jnp.min(train_states[:, n:])} to {jnp.max(train_states[:, n:])}")

# Regenerate data with wider parameter ranges if needed
```

### 3. Poor Stage 1 Convergence

**Problem**: Hamiltonian never learns accurate dynamics

**Symptoms**:
- Stage 1 loss plateaus > 10⁻²
- Stage 2 immediately diverges

**Causes**:
- Model too small
- Learning rate too high/low
- Data quality issues

**Solutions**:
```python
# Increase model capacity
encoder_dims=(512, 512, 256)  # Instead of (256, 256)

# Adjust learning rate
'learning_rate': 3e-4  # Instead of 1e-3

# Check data quality
from ml import validate_dataset
report = validate_dataset('data/3body_s1_dataset.h5')
passed, issues = check_quality_thresholds(report)
if not passed:
    print("Data quality issues:", issues)
```

### 4. Mode Collapse in Stage 2

**Problem**: Conservation loss decreases but invariant becomes trivial

**Symptoms**:
- `conservation_loss` → 0 rapidly
- `invariant_variance` → 0 simultaneously

**Causes**:
- λ_conservation ramped up too fast
- Network finds trivial solution (I = const)

**Solutions**:
```python
# Much slower warmup
'lambda_warmup_epochs': stage2_epochs,  # Full stage duration

# Exponential schedule (slower start)
'lambda_conservation_schedule': 'exponential'

# Increase regularization
lambda_regularization=0.1
```

### 5. Symmetry Violations

**Problem**: Discovered invariant doesn't respect known symmetries

**Symptoms**:
- `noether_loss` remains high (> 10⁻²)
- I(σ(z)) ≠ I(z) for symmetry transform σ

**Causes**:
- λ_noether too small
- Incorrect symmetry transforms
- Insufficient training

**Solutions**:
```python
# Increase Noether weight
state = state.replace(lambda_noether=0.5)  # Instead of 0.1

# Verify symmetry transforms
from ml import test_symmetry_preservation
for sym in symmetry_transforms:
    errors = test_symmetry_preservation(params, model, test_states, sym, inv_idx=0)
    print(f"Symmetry error: {jnp.mean(errors):.2e}")

# Longer training
'stage2_epochs': 300  # Instead of 150
```

### 6. Overfitting

**Problem**: Train loss << Val loss

**Symptoms**:
- `train_conservation_loss` = 10⁻⁶
- `val_conservation_loss` = 10⁻²

**Causes**:
- Model too large
- Training too long
- Insufficient data

**Solutions**:
```python
# Reduce model size
encoder_dims=(128, 128)  # Instead of (512, 512)

# Early stopping (already implemented)
'early_stopping_patience': 10  # Instead of 20

# Generate more data
# ... increase num_samples in data generation
```

---

## Advanced Usage

### 1. Discovering Multiple Invariants

For integrable systems, discover k independent invariants:

```python
# Create model with multiple invariant heads
model, params = create_conservation_hnn(
    state_dim=8,
    num_invariants=3,  # Discover 3 invariants (energy, L_z, ...)
    encoder_dims=(512, 512),  # Larger encoder for more invariants
    invariant_dims=(256, 128)  # Each head has same architecture
)

# Train one invariant at a time
for inv_idx in range(3):
    print(f"\n{'='*80}")
    print(f"TRAINING INVARIANT {inv_idx}")
    print(f"{'='*80}")

    # Use previous best state if not first invariant
    if inv_idx > 0:
        # Load previous checkpoint
        params, _ = load_checkpoint(f'checkpoints/inv{inv_idx-1}_best.pkl')

    # Train with involution constraint
    state = create_conservation_train_state(model, params)
    if inv_idx > 0:
        state = state.replace(lambda_involution=0.5)  # Enforce {I_i, I_j} = 0

    final_state, history = two_stage_training(
        model, params,
        ...,
        inv_idx=inv_idx,
        verbose=True
    )

    # Save
    save_checkpoint(final_state, f'checkpoints/inv{inv_idx}_best.pkl')

    print(f"Invariant {inv_idx} conservation error: {history['best_conservation_error']:.2e}")

# Verify independence
I0 = model.batch_invariant(final_state.params, test_states, 0)
I1 = model.batch_invariant(final_state.params, test_states, 1)
I2 = model.batch_invariant(final_state.params, test_states, 2)

print("\nIndependence matrix (correlations):")
print(np.corrcoef([I0, I1, I2]))
# Should be close to identity (off-diagonal ≈ 0)
```

### 2. Custom Symmetry Transforms

Add problem-specific symmetries:

```python
from ml import compose_transforms

# Define custom symmetry (example: reflection)
def reflection_transform(z: jnp.ndarray) -> jnp.ndarray:
    """Reflect across x-axis: (x,y,vx,vy) → (x,-y,vx,-vy)"""
    n = len(z) // 2
    q, p = z[:n], z[n:]

    # Assuming state = [x1, y1, x2, y2, vx1, vy1, vx2, vy2]
    # Flip y-coordinates and vy-velocities
    q_reflected = q.at[1::2].set(-q[1::2])  # y → -y
    p_reflected = p.at[1::2].set(-p[1::2])  # vy → -vy

    return jnp.concatenate([q_reflected, p_reflected])

# Add to symmetry list
base_transforms = get_symmetry_transforms_3body(masses)
custom_transforms = base_transforms + [reflection_transform]

# Use in training
final_state, history = two_stage_training(
    ...,
    # Pass symmetries directly (bypassing get_symmetry_transforms_3body)
    include_symmetries=False  # Disable automatic
)

# Manually set symmetries in train_step_stage2
# (requires modifying training loop - see conservation_training.py)
```

### 3. Transfer Learning

Fine-tune on new system with similar physics:

```python
# Load model trained on equal-mass 3-body
params_pretrained, metadata = load_checkpoint('checkpoints/equal_mass_best.pkl')

# Fine-tune on hierarchical masses (Sun-Jupiter-asteroid)
masses_new = jnp.array([1.0, 0.001, 0.0001])  # Hierarchical

final_state, history = two_stage_training(
    model,
    params_pretrained,  # Start from pretrained weights
    train_data=...,  # New data with hierarchical masses
    val_data=...,
    masses=masses_new,
    stage1_epochs=20,  # Shorter (already has good dynamics)
    stage2_epochs=80,
    learning_rate=1e-4,  # Lower LR for fine-tuning
    verbose=True
)
```

### 4. Integration with WP 3.1 (Geometric)

Compare ML-discovered invariants with geometric (Killing) invariants:

```python
# WP 3.1: Geometric discovery via Killing PDEs
from killing_pde_solver import KillingPDESolver

# Solve for geometric invariants
solver = KillingPDESolver(bundle_type='s1')
geometric_invariants = solver.solve()  # Returns symbolic expressions

print(f"WP 3.1 found {len(geometric_invariants)} geometric invariants")

# WP 3.2: ML discovery
final_state, history = two_stage_training(...)

# Compare
ml_invariant = model.batch_invariant(final_state.params, test_states, inv_idx=0)

# Evaluate geometric invariant numerically
geom_invariant = evaluate_geometric_invariant(geometric_invariants[0], test_states)

# Correlation
corr, _ = pearsonr(ml_invariant, geom_invariant)
print(f"ML vs Geometric invariant correlation: {corr:.6f}")

# Expected: High correlation (> 0.95) if they found the same invariant
```

### 5. Batch Processing Multiple Systems

Train on ensemble of systems with different parameters:

```python
import os

# Parameter grid
mass_ratios = [0.1, 0.3, 0.5, 0.7, 0.9]
energy_ranges = [(-2.0, -1.0), (-1.0, -0.5), (-0.5, -0.1)]

for mu in mass_ratios:
    for E_range in energy_ranges:
        exp_name = f"mu{mu:.1f}_E{E_range[0]:.1f}to{E_range[1]:.1f}"
        print(f"\n{'='*80}")
        print(f"EXPERIMENT: {exp_name}")
        print(f"{'='*80}")

        # Generate data
        param_ranges = ParameterRanges(
            mass_ratio=(mu, mu),
            energy=E_range,
            ...
        )
        # ... data generation ...

        # Train
        final_state, history = two_stage_training(...)

        # Save
        os.makedirs(f'results/{exp_name}', exist_ok=True)
        save_checkpoint(final_state, f'results/{exp_name}/model.pkl')

        # Log results
        with open(f'results/{exp_name}/summary.txt', 'w') as f:
            f.write(f"Conservation error: {history['best_conservation_error']:.2e}\n")
            f.write(f"Best epoch: {history['best_epoch']}\n")
```

---

## Troubleshooting

### Q: Training is very slow (< 1 epoch/second)

**A**:
1. Reduce `batch_size` (256 → 128)
2. Reduce model size (`encoder_dims=(128,128)`)
3. Disable symmetries if not needed (`include_symmetries=False`)
4. Use GPU acceleration (JAX automatically uses GPU if available)

### Q: "NaN in loss" error

**A**:
1. **Reduce learning rate**: `learning_rate=1e-4` instead of `1e-3`
2. **Increase warmup**: `warmup_steps=2000`
3. **Check data**: Ensure no NaN/Inf in training data
4. **Gradient clipping**: Already enabled (1.0), try reducing to 0.5

### Q: Conservation error stuck at ~10⁻²

**A**:
1. **Increase training**: `stage2_epochs=300`
2. **Increase model capacity**: `encoder_dims=(512,512,256)`
3. **Slow down λ warmup**: `lambda_warmup_epochs=100`
4. **Check data quality**: Ensure energy drift < 10⁻¹⁰

### Q: Invariant has zero variance

**A**:
1. **Increase regularization**: `lambda_regularization=0.1`
2. **Slow down λ warmup**: `lambda_warmup_epochs=stage2_epochs`
3. **Try different initialization**: `seed=456`
4. **Check Stage 1 convergence**: Should reach < 10⁻³

### Q: How do I know if my invariant is correct?

**A**:
Run validation checklist:
```python
# 1. Conservation along trajectories
times, traj = integrate_trajectory_learned(model, params, z0, t_span=100.0)
I_traj = model.batch_invariant(params, traj, 0)
drift = jnp.max(jnp.abs(I_traj - I_traj[0])) / jnp.abs(I_traj[0])
print(f"1. Drift: {drift:.2e} {'✓' if drift < 1e-3 else '✗'}")

# 2. Non-trivial
variance = jnp.var(model.batch_invariant(params, test_states, 0))
print(f"2. Variance: {variance:.6f} {'✓' if variance > 0.01 else '✗'}")

# 3. Poisson bracket
pb_error = compute_conservation_violation(params, model, test_states, 0)['mean']
print(f"3. {{I,H}}: {pb_error:.2e} {'✓' if pb_error < 1e-4 else '✗'}")

# 4. Symmetries (if applicable)
from ml import test_symmetry_preservation
for sym in symmetry_transforms:
    sym_error = jnp.mean(test_symmetry_preservation(params, model, test_states, sym, 0))
    print(f"4. Symmetry: {sym_error:.2e} {'✓' if sym_error < 1e-3 else '✗'}")

# All ✓ → Correct invariant!
```

### Q: Can I discover non-polynomial invariants?

**A**: Yes! Neural networks are universal approximators. They can discover:
- Polynomial: E = q² + p²
- Rational: I = q/(1 + p²)
- Transcendental: I = sin(q) + cos(p) (rare in physics)
- Implicit: Any function satisfying {I, H} = 0

The method is agnostic to functional form.

---

## References

- **WP 3.2 Design**: See `Project-Design-Docs/WP3/WP3.2-ML-Discovery-Summary.md`
- **Implementation Plans**: `Task-3.2.{1,2,3,4}-Implementation-Plan.md`
- **Module Documentation**: See docstrings in source files
- **JAX Documentation**: https://jax.readthedocs.io/
- **Flax Documentation**: https://flax.readthedocs.io/

---

## Quick Reference

### Typical Workflow

```python
# 1. Data
from ml import generate_lhs_samples, integrate_batch_parallel, TrajectoryDataset

# 2. Model
from ml import create_conservation_hnn
model, params = create_conservation_hnn(state_dim=8, num_invariants=1)

# 3. Train
from ml import two_stage_training
final_state, history = two_stage_training(
    model, params, train_data=..., val_data=..., masses=...
)

# 4. Evaluate
from ml import evaluate_conservation
metrics = evaluate_conservation(final_state, model, test_data, inv_idx=0)

# 5. Interpret
I_values = model.batch_invariant(final_state.params, test_states, inv_idx=0)

# 6. Save
from ml import save_checkpoint
save_checkpoint(final_state, 'checkpoints/model.pkl')
```

### Default Configuration (Copy-Paste)

```python
# Recommended defaults for 3-body S¹ bundle
config = {
    # Model
    'state_dim': 8,
    'num_invariants': 1,
    'encoder_dims': (256, 256),
    'hamiltonian_dims': (128, 64),
    'invariant_dims': (128, 64),

    # Training
    'stage1_epochs': 50,
    'stage2_epochs': 150,
    'batch_size': 256,
    'learning_rate': 1e-3,
    'warmup_steps': 1000,

    # Conservation
    'lambda_conservation_schedule': 'linear',
    'lambda_warmup_epochs': 50,
    'lambda_noether': 0.1,
    'lambda_regularization': 0.01,

    # Early stopping
    'early_stopping_patience': 20,
    'conservation_threshold': 1e-4,

    # Symmetries
    'include_symmetries': True,
}
```

---

**End of Guide**

For questions or issues, consult:
- Source code: `src/python/ml/conservation_*.py`
- Tests: Run `python -m ml.conservation_training` for test example
- Implementation plan: `Project-Design-Docs/WP3/Task-3.2.3-Implementation-Plan.md`
