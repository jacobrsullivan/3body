# Task 3.2.2: HNN/SympNet Architecture
## Implementation Plan

**Duration**: 5-6 days
**Priority**: Critical
**Dependencies**: Task 3.2.1 (datasets), JAX/Flax installation

---

## Overview

Implement structure-preserving neural network architectures that respect the symplectic geometry of Hamiltonian systems. Two main approaches:

1. **Hamiltonian Neural Networks (HNN)**: Learn scalar Hamiltonian function H_θ(q,p)
2. **Symplectic Neural Networks (SympNet)**: Learn symplectic flow maps φ_θ

**Key Principle**: Standard neural networks violate energy conservation and symplectic structure. Physics-informed architectures enforce these constraints by design.

---

## Part A: JAX/Flax Setup and Utilities (1 day)

### A.1: Environment Setup

**New Dependencies**:
```bash
pip install jax jaxlib flax optax
```

- **JAX**: Automatic differentiation, JIT compilation
- **Flax**: Neural network library (Linen API)
- **Optax**: Optimization algorithms

### A.2: Utility Functions

**File**: `src/python/ml/jax_utils.py`

```python
import jax
import jax.numpy as jnp
from typing import Callable, Tuple

def symplectic_matrix(n: int) -> jnp.ndarray:
    """
    Construct standard symplectic matrix J ∈ R^{2n×2n}.

    J = [ 0   I_n ]
        [-I_n  0  ]

    Property: J^T = -J, J^2 = -I
    """
    I = jnp.eye(n)
    Z = jnp.zeros((n, n))
    J = jnp.block([[Z, I], [-I, Z]])
    return J

def poisson_bracket(
    f: Callable,
    g: Callable,
    params_f,
    params_g
) -> Callable:
    """
    Compute Poisson bracket {f, g} = ∇f · J · ∇g.

    Args:
        f, g: Scalar functions f(z), g(z) where z = (q, p)
        params_f, params_g: Network parameters

    Returns:
        Function computing {f, g}(z)
    """
    def bracket_fn(z):
        n = len(z) // 2
        J = symplectic_matrix(n)

        grad_f = jax.grad(lambda x: f(params_f, x))(z)
        grad_g = jax.grad(lambda x: g(params_g, x))(z)

        return jnp.dot(grad_f, jnp.dot(J, grad_g))

    return bracket_fn

def hamiltonian_vector_field(
    H: Callable,
    params
) -> Callable:
    """
    Construct Hamiltonian vector field X_H = J ∇H.

    For H(q, p), the equations of motion are:
        dz/dt = X_H(z) = J ∇H(z)

    where z = (q, p).
    """
    def vector_field(z):
        n = len(z) // 2
        grad_H = jax.grad(lambda x: H(params, x))(z)

        # J ∇H = (∂H/∂p, -∂H/∂q)
        dq_dt = grad_H[n:]   # ∂H/∂p
        dp_dt = -grad_H[:n]  # -∂H/∂q

        return jnp.concatenate([dq_dt, dp_dt])

    return vector_field

def split_state(z: jnp.ndarray) -> Tuple[jnp.ndarray, jnp.ndarray]:
    """Split phase space state into (q, p)."""
    n = len(z) // 2
    return z[:n], z[n:]

def join_state(q: jnp.ndarray, p: jnp.ndarray) -> jnp.ndarray:
    """Join (q, p) into phase space state."""
    return jnp.concatenate([q, p])
```

**Deliverables**:
- [ ] `jax_utils.py` (~150 lines)
- [ ] Unit tests for symplectic operations

---

## Part B: Hamiltonian Neural Network (3 days)

### B.1: Base HNN Architecture

**File**: `src/python/ml/hnn_architecture.py`

```python
import jax
import jax.numpy as jnp
from flax import linen as nn
from typing import Sequence, Callable
from dataclasses import field

class HamiltonianNN(nn.Module):
    """
    Hamiltonian Neural Network.

    Learns scalar Hamiltonian H_θ(z) where z = (q, p).
    Dynamics are then dz/dt = J ∇H_θ(z), automatically preserving
    symplectic structure.

    Architecture:
        Input: z ∈ R^{2n}
        Hidden: MLP with smooth activations
        Output: H ∈ R (scalar energy)
    """

    hidden_dims: Sequence[int] = (256, 256, 128, 64)
    activation: str = 'tanh'  # Smooth activation crucial for gradients
    use_layer_norm: bool = False

    @nn.compact
    def __call__(self, z: jnp.ndarray) -> jnp.ndarray:
        """
        Forward pass: compute H(z).

        Args:
            z: Phase space state (2n,)

        Returns:
            H: Scalar Hamiltonian value
        """
        x = z

        # Hidden layers
        for i, dim in enumerate(self.hidden_dims):
            x = nn.Dense(
                dim,
                kernel_init=nn.initializers.glorot_normal(),
                bias_init=nn.initializers.zeros
            )(x)

            if self.use_layer_norm:
                x = nn.LayerNorm()(x)

            # Activation
            if self.activation == 'tanh':
                x = nn.tanh(x)
            elif self.activation == 'softplus':
                x = nn.softplus(x)
            elif self.activation == 'gelu':
                x = nn.gelu(x)

        # Output layer: single scalar
        H = nn.Dense(
            1,
            kernel_init=nn.initializers.glorot_normal(),
            bias_init=nn.initializers.zeros
        )(x)

        return jnp.squeeze(H)  # Return scalar

    def dynamics(self, z: jnp.ndarray, params) -> jnp.ndarray:
        """
        Compute time derivative dz/dt = J ∇H.

        This is the key method: it computes Hamiltonian dynamics
        via automatic differentiation.

        Args:
            z: Phase space state (2n,)
            params: Network parameters

        Returns:
            dz_dt: Time derivative (2n,)
        """
        n = len(z) // 2

        # Compute gradient of H with respect to z
        grad_H = jax.grad(lambda state: self.apply(params, state))(z)

        # Apply symplectic matrix: J ∇H = (∂H/∂p, -∂H/∂q)
        dq_dt = grad_H[n:]   # ∂H/∂p
        dp_dt = -grad_H[:n]  # -∂H/∂q

        return jnp.concatenate([dq_dt, dp_dt])

    def energy(self, z: jnp.ndarray, params) -> float:
        """Compute energy (just the Hamiltonian value)."""
        return self.apply(params, z)


class SeparableHNN(nn.Module):
    """
    Separable Hamiltonian Neural Network.

    Assumes H(q, p) = T(p) + V(q) where T is kinetic, V is potential.
    This is a stronger inductive bias than general HNN.

    Often more sample-efficient for mechanical systems.
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
        """
        x = p
        for dim in self.hidden_dims:
            x = nn.Dense(dim)(x)
            x = nn.tanh(x)
        T = nn.Dense(1)(x)
        return jnp.squeeze(T)

    def _potential_network(self, q: jnp.ndarray) -> jnp.ndarray:
        """Learn potential energy V(q)."""
        x = q
        for dim in self.hidden_dims:
            x = nn.Dense(dim)(x)
            x = nn.tanh(x)
        V = nn.Dense(1)(x)
        return jnp.squeeze(V)

    def dynamics(self, z: jnp.ndarray, params) -> jnp.ndarray:
        """Same as HNN: dz/dt = J ∇H."""
        n = len(z) // 2
        grad_H = jax.grad(lambda state: self.apply(params, state))(z)
        dq_dt = grad_H[n:]
        dp_dt = -grad_H[:n]
        return jnp.concatenate([dq_dt, dp_dt])


def create_hnn_model(
    state_dim: int,
    hidden_dims: Sequence[int] = (256, 256, 128),
    separable: bool = False,
    seed: int = 42
):
    """
    Factory function to create and initialize HNN.

    Args:
        state_dim: Dimension of phase space (must be even)
        hidden_dims: Hidden layer sizes
        separable: Use separable H = T + V form
        seed: Random seed for initialization

    Returns:
        model: Flax model
        params: Initialized parameters
    """
    assert state_dim % 2 == 0, "Phase space dimension must be even"

    if separable:
        model = SeparableHNN(hidden_dims=hidden_dims)
    else:
        model = HamiltonianNN(hidden_dims=hidden_dims)

    # Initialize parameters
    rng = jax.random.PRNGKey(seed)
    dummy_input = jnp.ones(state_dim)
    params = model.init(rng, dummy_input)

    return model, params
```

**Deliverables**:
- [ ] `hnn_architecture.py` (~400 lines)
- [ ] Unit tests on toy Hamiltonians (harmonic oscillator, Kepler)

---

### B.2: Training Loop for HNN

**File**: `src/python/ml/hnn_training.py`

```python
import jax
import jax.numpy as jnp
import optax
from flax.training import train_state
from typing import Tuple, Dict, Callable
from tqdm import tqdm

class TrainState(train_state.TrainState):
    """Extended train state with metrics."""
    batch_stats: dict = None

def create_train_state(
    model,
    params,
    learning_rate: float = 1e-3,
    weight_decay: float = 1e-5
) -> TrainState:
    """Create optimizer and training state."""
    # Optimizer: AdamW with learning rate schedule
    schedule = optax.exponential_decay(
        init_value=learning_rate,
        transition_steps=1000,
        decay_rate=0.99
    )

    optimizer = optax.chain(
        optax.clip_by_global_norm(1.0),  # Gradient clipping
        optax.adamw(learning_rate=schedule, weight_decay=weight_decay)
    )

    return TrainState.create(
        apply_fn=model.apply,
        params=params,
        tx=optimizer
    )

@jax.jit
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
    def predict_dynamics(z):
        return model.dynamics(z, params)

    predicted_derivatives = jax.vmap(predict_dynamics)(states)

    # Mean squared error
    loss = jnp.mean((predicted_derivatives - derivatives) ** 2)

    # Additional metrics
    metrics = {
        'mse': loss,
        'max_error': jnp.max(jnp.abs(predicted_derivatives - derivatives)),
        'mean_abs_error': jnp.mean(jnp.abs(predicted_derivatives - derivatives))
    }

    return loss, metrics

@jax.jit
def train_step(
    state: TrainState,
    batch: Tuple[jnp.ndarray, jnp.ndarray],
    model
) -> Tuple[TrainState, Dict]:
    """Single training step."""
    states, derivatives = batch

    # Compute loss and gradients
    (loss, metrics), grads = jax.value_and_grad(
        trajectory_loss_fn,
        has_aux=True
    )(state.params, model, states, derivatives)

    # Update parameters
    state = state.apply_gradients(grads=grads)

    return state, metrics

def train_hnn(
    model,
    params,
    train_dataset,
    val_dataset,
    num_epochs: int = 100,
    batch_size: int = 256,
    learning_rate: float = 1e-3
) -> Tuple[TrainState, Dict]:
    """
    Train HNN on trajectory data.

    Args:
        model: HNN model
        params: Initial parameters
        train_dataset: Training data (states, derivatives)
        val_dataset: Validation data
        num_epochs: Number of training epochs
        batch_size: Batch size
        learning_rate: Initial learning rate

    Returns:
        final_state: Trained model state
        history: Training history (losses, metrics)
    """
    state = create_train_state(model, params, learning_rate)

    history = {
        'train_loss': [],
        'val_loss': [],
        'train_metrics': [],
        'val_metrics': []
    }

    # Training loop
    for epoch in tqdm(range(num_epochs), desc="Training HNN"):
        # Training
        epoch_metrics = []
        for batch in train_dataset.batch_iterator(batch_size):
            state, metrics = train_step(state, batch, model)
            epoch_metrics.append(metrics)

        # Aggregate metrics
        train_loss = jnp.mean(jnp.array([m['mse'] for m in epoch_metrics]))
        history['train_loss'].append(float(train_loss))

        # Validation
        val_metrics = []
        for batch in val_dataset.batch_iterator(batch_size):
            _, metrics = trajectory_loss_fn(
                state.params, model, batch[0], batch[1]
            )
            val_metrics.append(metrics)

        val_loss = jnp.mean(jnp.array([m['mse'] for m in val_metrics]))
        history['val_loss'].append(float(val_loss))

        # Logging
        if epoch % 10 == 0:
            print(f"Epoch {epoch}: Train Loss = {train_loss:.6f}, "
                  f"Val Loss = {val_loss:.6f}")

    return state, history
```

**Deliverables**:
- [ ] `hnn_training.py` (~350 lines)
- [ ] Training utilities: checkpointing, early stopping
- [ ] Visualization: training curves, prediction examples

---

## Part C: Symplectic Neural Network (2 days, Optional)

### C.1: SympNet Architecture

**File**: `src/python/ml/sympnet_architecture.py`

```python
class SymplecticLayer(nn.Module):
    """
    Single symplectic transformation layer.

    Based on: Jin et al., "SympNets" (2020)

    A symplectic transformation can be decomposed into:
    1. Gradients of generating functions
    2. Linear symplectic maps
    3. Activation functions applied componentwise

    This layer implements a gradient layer:
        (q', p') = (q, p + ∇_q S(q))
    or
        (q', p') = (q - ∇_p S(p), p)

    where S is a learned generating function.
    """

    hidden_dim: int = 64
    layer_type: str = 'q'  # 'q' or 'p'

    @nn.compact
    def __call__(self, z: jnp.ndarray) -> jnp.ndarray:
        """Apply symplectic transformation."""
        q, p = split_state(z)
        n = len(q)

        if self.layer_type == 'q':
            # Update p using gradient of S(q)
            S = self._generating_function(q)
            grad_S = jax.grad(lambda x: jnp.sum(S(x)))(q)
            p_new = p + grad_S
            return join_state(q, p_new)

        else:  # layer_type == 'p'
            # Update q using gradient of S(p)
            S = self._generating_function(p)
            grad_S = jax.grad(lambda x: jnp.sum(S(x)))(p)
            q_new = q - grad_S
            return join_state(q_new, p)

    def _generating_function(self, x: jnp.ndarray) -> Callable:
        """Learn generating function S(x)."""
        h = nn.Dense(self.hidden_dim)(x)
        h = nn.tanh(h)
        S = nn.Dense(len(x))(h)
        return S


class SympNet(nn.Module):
    """
    Symplectic Neural Network: composition of symplectic layers.

    Maps initial state to state at later time via learned flow.
        φ_θ: (q_0, p_0) → (q_t, p_t)

    Guaranteed to preserve symplectic structure exactly.
    """

    num_layers: int = 10
    hidden_dim: int = 64

    @nn.compact
    def __call__(self, z: jnp.ndarray, dt: float) -> jnp.ndarray:
        """
        Apply symplectic flow for time step dt.

        Args:
            z: Initial state (2n,)
            dt: Time step

        Returns:
            z_next: State at t + dt
        """
        x = z

        # Alternate between q-type and p-type layers
        for i in range(self.num_layers):
            layer_type = 'q' if i % 2 == 0 else 'p'
            x = SymplecticLayer(
                hidden_dim=self.hidden_dim,
                layer_type=layer_type
            )(x)

        # Scale by time step (for learned integrator)
        # (This is simplified; real SympNets are more sophisticated)
        return x
```

**Note**: SympNet is more complex than HNN and may not be necessary for initial implementation. Recommended to focus on HNN first.

**Deliverables** (Optional):
- [ ] `sympnet_architecture.py` (~300 lines)
- [ ] Comparison benchmarks: HNN vs SympNet on test cases

---

## Part D: Model Utilities and Testing (1 day)

### D.1: Model Utilities

**File**: `src/python/ml/model_utils.py`

```python
def count_parameters(params) -> int:
    """Count total trainable parameters."""
    return sum(x.size for x in jax.tree_util.tree_leaves(params))

def save_checkpoint(state: TrainState, filepath: str):
    """Save model checkpoint."""
    import pickle
    with open(filepath, 'wb') as f:
        pickle.dump({
            'params': state.params,
            'step': state.step,
            'opt_state': state.opt_state
        }, f)

def load_checkpoint(filepath: str, model) -> TrainState:
    """Load model checkpoint."""
    import pickle
    with open(filepath, 'rb') as f:
        data = pickle.load(f)
    # Reconstruct TrainState
    # ...
    return state

def integrate_trajectory(
    model,
    params,
    z0: jnp.ndarray,
    t_span: Tuple[float, float],
    dt: float
) -> Tuple[jnp.ndarray, jnp.ndarray]:
    """
    Integrate trajectory using learned HNN.

    Uses simple Euler or RK4 with learned dynamics.

    Args:
        model: Trained HNN
        params: Model parameters
        z0: Initial state
        t_span: (t_start, t_end)
        dt: Time step

    Returns:
        times: (N,)
        states: (N, 2n)
    """
    times = jnp.arange(t_span[0], t_span[1], dt)
    states = [z0]

    for i in range(len(times) - 1):
        z = states[-1]
        dz_dt = model.dynamics(z, params)

        # Euler step (can upgrade to RK4)
        z_next = z + dt * dz_dt

        states.append(z_next)

    return times, jnp.array(states)
```

**Deliverables**:
- [ ] `model_utils.py` (~200 lines)

---

### D.2: Testing on Known Systems

**File**: `tests/wp3/test_hnn_architecture.py`

```python
import pytest
import jax.numpy as jnp
from src.python.ml.hnn_architecture import HamiltonianNN, create_hnn_model
from src.python.ml.hnn_training import train_hnn

def harmonic_oscillator_hamiltonian(z):
    """H = (p^2 + q^2) / 2"""
    q, p = z[0], z[1]
    return 0.5 * (q**2 + p**2)

def harmonic_oscillator_dynamics(z):
    """dq/dt = p, dp/dt = -q"""
    q, p = z[0], z[1]
    return jnp.array([p, -q])

def generate_harmonic_data(num_samples=1000, t_span=10.0, dt=0.01):
    """Generate training data for harmonic oscillator."""
    from scipy.integrate import solve_ivp

    data_states = []
    data_derivatives = []

    for _ in range(num_samples):
        # Random initial condition
        z0 = np.random.randn(2)

        # Integrate
        sol = solve_ivp(
            lambda t, z: harmonic_oscillator_dynamics(z),
            (0, t_span),
            z0,
            t_eval=np.arange(0, t_span, dt)
        )

        data_states.extend(sol.y.T)
        derivatives = np.array([
            harmonic_oscillator_dynamics(sol.y[:, i])
            for i in range(sol.y.shape[1])
        ])
        data_derivatives.extend(derivatives)

    return jnp.array(data_states), jnp.array(data_derivatives)

def test_hnn_learns_harmonic_oscillator():
    """Test that HNN can learn harmonic oscillator."""
    # Generate data
    states, derivatives = generate_harmonic_data(num_samples=100)

    # Create model
    model, params = create_hnn_model(state_dim=2, hidden_dims=(32, 32))

    # Train (simplified)
    # ... training loop ...

    # Test: Check energy conservation
    z_test = jnp.array([1.0, 0.0])
    E_true = harmonic_oscillator_hamiltonian(z_test)
    E_learned = model.apply(params, z_test)

    # Should learn correct Hamiltonian
    assert abs(E_learned - E_true) < 0.1

def test_hnn_preserves_symplectic_structure():
    """Verify HNN dynamics preserve symplectic structure."""
    # TODO: Check that ω(dz/dt, dz/dt) = 0
    pass

def test_hnn_energy_conservation():
    """Verify learned Hamiltonian is conserved along trajectories."""
    # Integrate trajectory with learned dynamics
    # Check dH/dt ≈ 0
    pass
```

**Deliverables**:
- [ ] `test_hnn_architecture.py` (~300 lines)
- [ ] Tests for: harmonic oscillator, Kepler problem, pendulum
- [ ] Benchmark: Compare learned dynamics to ground truth

---

## Integration Points

### From Task 3.2.1 (Data Generation)
- **Input**: HDF5 datasets (`s1_bundle_train.h5`)
- **Interface**: Load states and derivatives as JAX arrays
- **Data loader**: Implement `batch_iterator` for HDF5

### To Task 3.2.3 (Conservation Training)
- **Output**: Base HNN architecture to extend with invariant head
- **Interface**: `HamiltonianNN` class with `dynamics()` method
- **Trained parameters**: Checkpoint to resume training with conservation loss

---

## Implementation Schedule

### Day 1: JAX Setup & Utilities
- [ ] Install JAX, Flax, Optax
- [ ] Implement `jax_utils.py`
- [ ] Test symplectic operations

### Day 2-3: HNN Architecture
- [ ] Implement `HamiltonianNN` and `SeparableHNN`
- [ ] Test on toy Hamiltonians (harmonic, Kepler)
- [ ] Verify gradient computation and dynamics

### Day 4: Training Loop
- [ ] Implement `hnn_training.py`
- [ ] Train on small dataset (harmonic oscillator)
- [ ] Validate energy conservation

### Day 5: Full Training
- [ ] Load Task 3.2.1 datasets
- [ ] Train HNN on S¹ bundle data
- [ ] Monitor training curves, save checkpoints

### Day 6: Validation & Testing
- [ ] Test on validation set
- [ ] Benchmark: trajectory prediction error
- [ ] Compare to baseline (standard MLP)

---

## Success Criteria

**Minimum**:
- [ ] HNN architecture implemented and tested
- [ ] Trains on toy systems (harmonic oscillator)
- [ ] Trajectory prediction error < 10%

**Target**:
- [ ] HNN learns S¹ bundle Hamiltonian with <1% error
- [ ] Energy conservation verified on held-out trajectories
- [ ] Symplectic structure preserved numerically

**Stretch**:
- [ ] SympNet implemented and benchmarked
- [ ] HNN generalizes to out-of-distribution parameters
- [ ] Real-time trajectory integration with learned dynamics

---

## Deliverables Summary

### Code
- [ ] `src/python/ml/jax_utils.py` (~150 lines)
- [ ] `src/python/ml/hnn_architecture.py` (~400 lines)
- [ ] `src/python/ml/hnn_training.py` (~350 lines)
- [ ] `src/python/ml/sympnet_architecture.py` (~300 lines, optional)
- [ ] `src/python/ml/model_utils.py` (~200 lines)

### Models
- [ ] Trained HNN checkpoint for S¹ bundle
- [ ] Hyperparameters file

### Tests
- [ ] `tests/wp3/test_hnn_architecture.py` (~300 lines)
- [ ] Validation report: energy conservation, trajectory error

**Total**: ~1,400-1,700 lines

---

**Document Version**: 1.0
**Status**: Ready for Implementation
**Next Task**: Task 3.2.3 (Conservation-Constrained Training)
