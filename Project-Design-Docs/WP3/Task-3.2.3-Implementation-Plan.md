# Task 3.2.3: Conservation-Constrained Training
## Implementation Plan

**Duration**: 6-7 days
**Priority**: Critical (Core innovation of WP 3.2)
**Dependencies**: Task 3.2.2 (HNN architecture)

---

## Overview

**Core Innovation**: Extend HNN with auxiliary "invariant head" that learns conserved quantities I_φ(q,p) by enforcing the conservation constraint {I_φ, H_θ} = 0.

**Training Objective**:
```
L = L_trajectory + λ₁ L_conservation + λ₂ L_Noether + λ₃ L_regularization
```

This is the key task for discovering new integrals via machine learning.

---

## Part A: Extended HNN Architecture (2 days)

### A.1: Dual-Head Architecture

**File**: `src/python/ml/conservation_hnn.py`

```python
import jax
import jax.numpy as jnp
from flax import linen as nn
from typing import Sequence, Tuple, Dict

class ConservationHNN(nn.Module):
    """
    HNN with auxiliary invariant prediction head.

    Architecture:
        Input: z = (q, p)
            ↓
        Shared Encoder: [256, 256]
            ↓
            ├─→ Hamiltonian Head: H_θ(z) → dz/dt = J ∇H
            │
            └─→ Invariant Head: I_φ(z) → conserved quantity

    Training enforces {I_φ, H_θ} = 0 (Poisson bracket).
    """

    # Shared encoder
    encoder_dims: Sequence[int] = (256, 256)

    # Hamiltonian head
    hamiltonian_dims: Sequence[int] = (128, 64)

    # Invariant head(s) - can learn multiple integrals
    num_invariants: int = 1
    invariant_dims: Sequence[int] = (128, 64)

    activation: str = 'tanh'

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
        for dim in self.encoder_dims:
            x = nn.Dense(dim)(x)
            x = nn.tanh(x)
        return x

    def _hamiltonian_head(self, features: jnp.ndarray) -> jnp.ndarray:
        """Hamiltonian prediction head."""
        x = features
        for dim in self.hamiltonian_dims:
            x = nn.Dense(dim)(x)
            x = nn.tanh(x)
        H = nn.Dense(1)(x)
        return jnp.squeeze(H)

    def _invariant_head(self, features: jnp.ndarray) -> jnp.ndarray:
        """Invariant prediction head(s)."""
        invariants = []

        for i in range(self.num_invariants):
            x = features
            for dim in self.invariant_dims:
                x = nn.Dense(dim, name=f'inv_{i}_dense_{dim}')(x)
                x = nn.tanh(x)

            # Output: single scalar invariant
            I_i = nn.Dense(1, name=f'inv_{i}_out')(x)
            invariants.append(jnp.squeeze(I_i))

        # Stack into array
        return jnp.array(invariants)

    def hamiltonian(self, z: jnp.ndarray, params) -> jnp.ndarray:
        """Compute just the Hamiltonian (for dynamics)."""
        H, _ = self.apply(params, z)
        return H

    def invariant(self, z: jnp.ndarray, params, idx: int = 0) -> jnp.ndarray:
        """Compute specific invariant."""
        _, I = self.apply(params, z)
        return I[idx]

    def dynamics(self, z: jnp.ndarray, params) -> jnp.ndarray:
        """Hamiltonian dynamics dz/dt = J ∇H."""
        n = len(z) // 2
        grad_H = jax.grad(lambda state: self.hamiltonian(state, params))(z)
        dq_dt = grad_H[n:]
        dp_dt = -grad_H[:n]
        return jnp.concatenate([dq_dt, dp_dt])


class MultiInvariantHNN(nn.Module):
    """
    Extension: Learn K independent invariants simultaneously.

    Useful for systems with multiple conserved quantities.
    Includes loss term enforcing mutual Poisson commutation:
        {I_i, I_j} = 0 for i ≠ j
    """

    encoder_dims: Sequence[int] = (256, 256)
    hamiltonian_dims: Sequence[int] = (128, 64)
    num_invariants: int = 3  # E, L, and one unknown
    invariant_dims: Sequence[int] = (128, 64)

    # Similar structure to ConservationHNN but with involution constraint
    # TODO: Implement if time permits
```

**Deliverables**:
- [ ] `conservation_hnn.py` (~400 lines)
- [ ] Unit tests: Forward pass, gradient computation
- [ ] Architectural diagram

---

## Part B: Physics-Informed Loss Functions (2 days)

### B.1: Conservation Loss

**File**: `src/python/ml/conservation_loss.py`

```python
import jax
import jax.numpy as jnp
from typing import Callable, Tuple, Dict

@jax.jit
def trajectory_loss(
    params,
    model,
    states: jnp.ndarray,
    derivatives: jnp.ndarray
) -> jnp.ndarray:
    """
    L_trajectory: Predict dynamics accurately.

    Loss: ||dz/dt_true - J ∇H_θ||²

    This ensures the Hamiltonian head learns the correct dynamics.
    """
    # Predict dynamics
    def predict_dynamics(z):
        return model.dynamics(z, params)

    predicted = jax.vmap(predict_dynamics)(states)

    # MSE with true derivatives
    loss = jnp.mean((predicted - derivatives) ** 2)

    return loss

@jax.jit
def conservation_loss(
    params,
    model,
    states: jnp.ndarray,
    inv_idx: int = 0
) -> jnp.ndarray:
    """
    L_conservation: Enforce {I_φ, H_θ} = 0.

    This is the key physics constraint: the Poisson bracket
    of the invariant with the Hamiltonian must vanish.

    For each state z, compute:
        {I, H}(z) = ∂I/∂q · ∂H/∂p - ∂I/∂p · ∂H/∂q

    Loss: E[|{I, H}|²]
    """
    def poisson_bracket_at_state(z):
        n = len(z) // 2

        # Gradients
        grad_I = jax.grad(lambda s: model.invariant(s, params, inv_idx))(z)
        grad_H = jax.grad(lambda s: model.hamiltonian(s, params))(z)

        # Extract q and p components
        dI_dq, dI_dp = grad_I[:n], grad_I[n:]
        dH_dq, dH_dp = grad_H[:n], grad_H[n:]

        # Poisson bracket: {I, H} = ∂I/∂q · ∂H/∂p - ∂I/∂p · ∂H/∂q
        bracket = jnp.dot(dI_dq, dH_dp) - jnp.dot(dI_dp, dH_dq)

        return bracket

    # Compute over batch
    brackets = jax.vmap(poisson_bracket_at_state)(states)

    # Loss: squared Poisson bracket (should be zero)
    loss = jnp.mean(brackets ** 2)

    return loss

@jax.jit
def noether_regularizer(
    params,
    model,
    states: jnp.ndarray,
    symmetry_transforms: list,
    inv_idx: int = 0
) -> jnp.ndarray:
    """
    L_Noether: Encourage invariants to respect symmetries.

    For known symmetries σ (e.g., permutations, rotations):
        I(σ(z)) should equal I(z)

    Loss: E[||I(σ(z)) - I(z)||²]

    This biases the network toward physically meaningful integrals
    arising from Noether's theorem.
    """
    total_loss = 0.0

    for transform_fn in symmetry_transforms:
        # Transform states
        transformed_states = jax.vmap(transform_fn)(states)

        # Compute invariants on original and transformed
        I_original = jax.vmap(
            lambda z: model.invariant(z, params, inv_idx)
        )(states)

        I_transformed = jax.vmap(
            lambda z: model.invariant(z, params, inv_idx)
        )(transformed_states)

        # Invariance loss
        loss = jnp.mean((I_original - I_transformed) ** 2)
        total_loss += loss

    return total_loss / len(symmetry_transforms)

@jax.jit
def involution_loss(
    params,
    model,
    states: jnp.ndarray
) -> jnp.ndarray:
    """
    L_involution: For multiple invariants, enforce {I_i, I_j} = 0.

    For Liouville integrability, conserved quantities must
    pairwise commute (be in involution).

    Only applicable if model.num_invariants > 1.
    """
    num_inv = model.num_invariants

    if num_inv <= 1:
        return 0.0

    total_loss = 0.0
    count = 0

    # For all pairs (i, j) with i < j
    for i in range(num_inv):
        for j in range(i + 1, num_inv):
            def pairwise_bracket(z):
                n = len(z) // 2
                grad_I = jax.grad(lambda s: model.invariant(s, params, i))(z)
                grad_J = jax.grad(lambda s: model.invariant(s, params, j))(z)

                dI_dq, dI_dp = grad_I[:n], grad_I[n:]
                dJ_dq, dJ_dp = grad_J[:n], grad_J[n:]

                bracket = jnp.dot(dI_dq, dJ_dp) - jnp.dot(dI_dp, dJ_dq)
                return bracket

            brackets = jax.vmap(pairwise_bracket)(states)
            total_loss += jnp.mean(brackets ** 2)
            count += 1

    return total_loss / count if count > 0 else 0.0

@jax.jit
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
    3. Known integral: I(z) = E or L

    Regularizers:
    1. Variance penalty: encourage non-constant
    2. Linear independence from known integrals
    """
    # Compute invariant values over batch
    I_values = jax.vmap(
        lambda z: model.invariant(z, params, inv_idx)
    )(states)

    # 1. Non-constant regularizer: maximize variance
    variance = jnp.var(I_values)
    constant_penalty = jnp.exp(-10 * variance)  # Penalize low variance

    # 2. Non-linear regularizer: encourage complexity
    # (Penalize if I is linear in z)
    # TODO: Implement gradient-based linearity check

    loss = constant_penalty

    return loss

def combined_loss(
    params,
    model,
    batch: Tuple[jnp.ndarray, jnp.ndarray],
    lambda_conservation: float = 1.0,
    lambda_noether: float = 0.1,
    lambda_regularization: float = 0.01,
    symmetry_transforms: list = None,
    inv_idx: int = 0
) -> Tuple[jnp.ndarray, Dict]:
    """
    Combined loss for conservation-constrained training.

    L = L_trajectory
        + λ₁ L_conservation
        + λ₂ L_Noether
        + λ₃ L_regularization

    Args:
        params: Model parameters
        model: ConservationHNN
        batch: (states, derivatives)
        lambda_*: Loss weights
        symmetry_transforms: List of symmetry functions
        inv_idx: Which invariant to train (if multiple)

    Returns:
        total_loss: Scalar loss
        metrics: Dictionary with individual loss components
    """
    states, derivatives = batch

    # Component losses
    L_traj = trajectory_loss(params, model, states, derivatives)
    L_cons = conservation_loss(params, model, states, inv_idx)
    L_reg = regularization_loss(params, model, states, inv_idx)

    # Noether loss (if symmetries provided)
    if symmetry_transforms:
        L_noeth = noether_regularizer(
            params, model, states, symmetry_transforms, inv_idx
        )
    else:
        L_noeth = 0.0

    # Combined loss
    total_loss = (
        L_traj
        + lambda_conservation * L_cons
        + lambda_noether * L_noeth
        + lambda_regularization * L_reg
    )

    # Metrics for logging
    metrics = {
        'total_loss': total_loss,
        'trajectory_loss': L_traj,
        'conservation_loss': L_cons,
        'noether_loss': L_noeth,
        'regularization_loss': L_reg
    }

    return total_loss, metrics
```

**Deliverables**:
- [ ] `conservation_loss.py` (~450 lines)
- [ ] Unit tests: Verify Poisson bracket computation
- [ ] Ablation study: Effect of each loss term

---

### B.2: Symmetry Transformations

**File**: `src/python/ml/symmetry_transforms.py`

```python
import jax.numpy as jnp

def permutation_transform_3body(
    z: jnp.ndarray,
    permutation: Tuple[int, int, int]
) -> jnp.ndarray:
    """
    Permutation symmetry for 3-body problem.

    For equal masses: permuting particle labels is a symmetry.

    Args:
        z: State in some coordinate system
        permutation: e.g., (0, 2, 1) swaps particles 2 and 3

    Returns:
        z_perm: Permuted state
    """
    # TODO: Implement based on coordinate system (S¹, KS, etc.)
    # This is highly dependent on the lifted coordinate structure
    pass

def rotation_transform(
    z: jnp.ndarray,
    axis: jnp.ndarray,
    angle: float
) -> jnp.ndarray:
    """
    SO(3) rotation symmetry.

    For systems with rotational symmetry, I should be invariant
    under rotations.

    Args:
        z: State (positions and momenta)
        axis: Rotation axis (3D unit vector)
        angle: Rotation angle (radians)

    Returns:
        z_rot: Rotated state
    """
    # Construct rotation matrix
    # Apply to position and momentum components
    # TODO: Implement
    pass

def time_reversal_transform(z: jnp.ndarray) -> jnp.ndarray:
    """
    Time reversal: (q, p) → (q, -p).

    For time-independent Hamiltonians, H(q, p) = H(q, -p).
    Conserved quantities may or may not be time-reversal invariant.

    Energy: Even under time reversal
    Angular momentum: Odd under time reversal
    """
    n = len(z) // 2
    q, p = z[:n], z[n:]
    return jnp.concatenate([q, -p])

def get_symmetry_transforms_s1_bundle(
    masses: jnp.ndarray
) -> list:
    """
    Get applicable symmetry transforms for S¹ bundle.

    Returns:
        List of symmetry transform functions
    """
    transforms = []

    # Time reversal (always applicable)
    transforms.append(time_reversal_transform)

    # Permutations (only if masses equal)
    if jnp.allclose(masses, masses[0]):
        # All 6 permutations of 3 particles
        for perm in [(0, 2, 1), (1, 0, 2), (1, 2, 0), (2, 0, 1), (2, 1, 0)]:
            transforms.append(
                lambda z, p=perm: permutation_transform_3body(z, p)
            )

    # Rotations (always applicable for 3-body)
    # Sample random rotations
    for _ in range(5):
        axis = jnp.array([...])  # Random axis
        angle = ...  # Random angle
        transforms.append(
            lambda z, ax=axis, ang=angle: rotation_transform(z, ax, ang)
        )

    return transforms
```

**Deliverables**:
- [ ] `symmetry_transforms.py` (~200 lines)
- [ ] Tests: Verify symmetries preserve known integrals (E, L)

---

## Part C: Two-Stage Training Strategy (2 days)

### C.1: Training Pipeline

**File**: `src/python/ml/conservation_training.py`

```python
from flax.training import train_state
import optax
from tqdm import tqdm

class ConservationTrainState(train_state.TrainState):
    """Extended state for conservation training."""
    lambda_conservation: float = 1.0
    lambda_noether: float = 0.1
    lambda_regularization: float = 0.01

def two_stage_training(
    model,
    params,
    train_dataset,
    val_dataset,
    symmetry_transforms: list = None,
    stage1_epochs: int = 50,
    stage2_epochs: int = 100,
    learning_rate: float = 1e-3
):
    """
    Two-stage training strategy.

    Stage 1 (Warm-up): Train only Hamiltonian head
        - Focus: L_trajectory only
        - Goal: Learn accurate dynamics
        - Duration: 50 epochs

    Stage 2 (Conservation): Train both heads jointly
        - Focus: L_trajectory + L_conservation + L_Noether
        - Goal: Discover conserved quantity
        - Duration: 100 epochs
        - Gradually increase λ_conservation from 0 → 1

    This staged approach prevents the invariant head from
    interfering with Hamiltonian learning early on.
    """
    # Stage 1: Hamiltonian only
    print("=" * 60)
    print("STAGE 1: Training Hamiltonian Head")
    print("=" * 60)

    state = create_train_state(model, params, learning_rate)

    for epoch in tqdm(range(stage1_epochs), desc="Stage 1"):
        for batch in train_dataset.batch_iterator(256):
            state, metrics = train_step_stage1(state, batch, model)

        # Validation
        if epoch % 10 == 0:
            val_loss = evaluate(state, model, val_dataset)
            print(f"Epoch {epoch}: Val Loss = {val_loss:.6f}")

    print(f"Stage 1 complete. Final trajectory loss: {metrics['trajectory_loss']:.6f}")

    # Stage 2: Joint training with conservation
    print("\n" + "=" * 60)
    print("STAGE 2: Conservation-Constrained Training")
    print("=" * 60)

    for epoch in tqdm(range(stage2_epochs), desc="Stage 2"):
        # Gradually increase conservation weight
        lambda_cons = min(1.0, epoch / 20.0)  # Ramp up over 20 epochs

        for batch in train_dataset.batch_iterator(256):
            state, metrics = train_step_stage2(
                state,
                batch,
                model,
                lambda_conservation=lambda_cons,
                symmetry_transforms=symmetry_transforms
            )

        # Validation and logging
        if epoch % 10 == 0:
            print(f"Epoch {epoch}:")
            print(f"  Trajectory Loss: {metrics['trajectory_loss']:.6f}")
            print(f"  Conservation Loss: {metrics['conservation_loss']:.6f}")
            print(f"  Noether Loss: {metrics['noether_loss']:.6f}")
            print(f"  λ_cons: {lambda_cons:.3f}")

            # Check if invariant is conserved on validation trajectories
            conservation_error = check_conservation_on_trajectories(
                state, model, val_dataset
            )
            print(f"  Conservation Error (val): {conservation_error:.6e}")

    return state, metrics

@jax.jit
def train_step_stage1(
    state: ConservationTrainState,
    batch,
    model
):
    """Stage 1: Train only Hamiltonian head."""
    states, derivatives = batch

    def loss_fn(params):
        return trajectory_loss(params, model, states, derivatives)

    loss, grads = jax.value_and_grad(loss_fn)(state.params)
    state = state.apply_gradients(grads=grads)

    return state, {'trajectory_loss': loss}

@jax.jit
def train_step_stage2(
    state: ConservationTrainState,
    batch,
    model,
    lambda_conservation: float,
    symmetry_transforms: list
):
    """Stage 2: Train with conservation constraints."""
    states, derivatives = batch

    def loss_fn(params):
        return combined_loss(
            params,
            model,
            batch,
            lambda_conservation=lambda_conservation,
            lambda_noether=state.lambda_noether,
            lambda_regularization=state.lambda_regularization,
            symmetry_transforms=symmetry_transforms
        )

    (loss, metrics), grads = jax.value_and_grad(
        loss_fn,
        has_aux=True
    )(state.params)

    state = state.apply_gradients(grads=grads)

    return state, metrics

def check_conservation_on_trajectories(
    state: ConservationTrainState,
    model,
    dataset,
    num_trajectories: int = 10
) -> float:
    """
    Verify conservation by integrating trajectories.

    For each trajectory:
    1. Integrate with learned Hamiltonian
    2. Evaluate I_φ at each timestep
    3. Compute max drift: |I(t) - I(0)| / |I(0)|

    Returns:
        Mean conservation error across trajectories
    """
    errors = []

    for traj_idx in range(num_trajectories):
        # Get trajectory from dataset
        z0 = dataset.get_initial_state(traj_idx)

        # Integrate
        times, states = integrate_trajectory(
            model,
            state.params,
            z0,
            t_span=(0, 100),
            dt=0.1
        )

        # Evaluate invariant along trajectory
        I_values = jnp.array([
            model.invariant(states[i], state.params)
            for i in range(len(states))
        ])

        # Conservation error
        drift = jnp.max(jnp.abs(I_values - I_values[0])) / (jnp.abs(I_values[0]) + 1e-10)
        errors.append(drift)

    return jnp.mean(jnp.array(errors))
```

**Deliverables**:
- [ ] `conservation_training.py` (~500 lines)
- [ ] Training script with checkpointing
- [ ] Logging: TensorBoard or Weights & Biases integration

---

## Part D: Hyperparameter Tuning (1 day)

### D.1: Grid Search

**File**: `src/python/ml/hyperparameter_tuning.py`

```python
def hyperparameter_grid_search(
    model,
    train_dataset,
    val_dataset,
    param_grid: Dict[str, list]
) -> Dict:
    """
    Grid search over hyperparameters.

    Tunable parameters:
    - lambda_conservation ∈ [0.1, 1.0, 10.0]
    - lambda_noether ∈ [0.01, 0.1, 1.0]
    - lambda_regularization ∈ [0.001, 0.01, 0.1]
    - learning_rate ∈ [1e-4, 1e-3, 1e-2]
    - num_invariants ∈ [1, 2, 3]

    Returns:
        Best hyperparameters based on validation conservation error
    """
    results = []

    for lambda_cons in param_grid['lambda_conservation']:
        for lambda_noeth in param_grid['lambda_noether']:
            for lr in param_grid['learning_rate']:
                print(f"\nTrying: λ_cons={lambda_cons}, λ_noeth={lambda_noeth}, lr={lr}")

                # Train
                state, _ = two_stage_training(
                    model,
                    params,
                    train_dataset,
                    val_dataset,
                    learning_rate=lr,
                    # ... pass lambda values ...
                )

                # Evaluate conservation on validation
                conservation_error = check_conservation_on_trajectories(
                    state, model, val_dataset
                )

                results.append({
                    'lambda_conservation': lambda_cons,
                    'lambda_noether': lambda_noeth,
                    'learning_rate': lr,
                    'conservation_error': conservation_error
                })

    # Find best
    best = min(results, key=lambda x: x['conservation_error'])
    return best
```

**Deliverables**:
- [ ] `hyperparameter_tuning.py` (~200 lines)
- [ ] Results: Hyperparameter sweep plots

---

## Part E: Curriculum Learning (Optional, 1 day)

### E.1: Progressive Training

**Strategy**: Start with simple parameter regimes, gradually increase difficulty.

1. **Easy**: Low eccentricity, moderate energy
2. **Medium**: Higher eccentricity, wider energy range
3. **Hard**: Full parameter space, near-collision events

This can improve convergence and generalization.

**File**: `src/python/ml/curriculum_learning.py`

```python
def curriculum_training(
    model,
    params,
    full_dataset,
    curriculum_schedule: list
):
    """
    Train with curriculum: easy → medium → hard examples.

    curriculum_schedule = [
        {'epochs': 20, 'difficulty': 'easy'},
        {'epochs': 30, 'difficulty': 'medium'},
        {'epochs': 50, 'difficulty': 'hard'}
    ]
    """
    for stage in curriculum_schedule:
        # Filter dataset by difficulty
        dataset = full_dataset.filter_by_difficulty(stage['difficulty'])

        # Train for specified epochs
        # ...
        pass
```

---

## Integration Points

### From Task 3.2.2 (HNN Architecture)
- **Input**: Base `HamiltonianNN` class
- **Extension**: Add invariant head to create `ConservationHNN`

### To Task 3.2.4 (Validation)
- **Output**: Trained model with learned invariant I_φ
- **Checkpoint**: Model parameters, training history
- **Metrics**: Conservation error, Poisson bracket values

---

## Implementation Schedule

### Day 1-2: Dual-Head Architecture
- [ ] Implement `ConservationHNN`
- [ ] Test forward/backward pass
- [ ] Verify gradient computation

### Day 3-4: Loss Functions
- [ ] Implement all loss components
- [ ] Test Poisson bracket computation
- [ ] Implement symmetry transforms

### Day 5-6: Training Pipeline
- [ ] Implement two-stage training
- [ ] Train on small dataset (validation)
- [ ] Monitor conservation metrics

### Day 7: Hyperparameter Tuning
- [ ] Grid search on validation set
- [ ] Select best configuration
- [ ] Full training run on complete dataset

---

## Success Criteria

**Minimum**:
- [ ] Conservation loss decreases during training
- [ ] Poisson bracket {I, H} < 0.1 on validation
- [ ] Learned invariant is non-trivial (not constant)

**Target**:
- [ ] Conservation error < 10⁻⁵ on validation trajectories
- [ ] {I, H} < 10⁻⁶
- [ ] Invariant functionally independent of E, L

**Stretch**:
- [ ] Discover novel invariant not found by WP 3.1
- [ ] Generalizes to out-of-distribution parameters
- [ ] Multiple independent invariants learned

---

## Deliverables Summary

### Code
- [ ] `src/python/ml/conservation_hnn.py` (~400 lines)
- [ ] `src/python/ml/conservation_loss.py` (~450 lines)
- [ ] `src/python/ml/symmetry_transforms.py` (~200 lines)
- [ ] `src/python/ml/conservation_training.py` (~500 lines)
- [ ] `src/python/ml/hyperparameter_tuning.py` (~200 lines)

### Models
- [ ] Trained ConservationHNN checkpoint
- [ ] Best hyperparameters

### Documentation
- [ ] Training report: Loss curves, conservation metrics
- [ ] Invariant analysis: Functional form, independence

**Total**: ~1,750 lines

---

**Document Version**: 1.0
**Status**: Ready for Implementation
**Next Task**: Task 3.2.4 (Validation and Generalization)
