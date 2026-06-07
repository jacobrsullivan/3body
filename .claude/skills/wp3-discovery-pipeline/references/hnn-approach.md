# Hamiltonian Neural Networks for Invariant Discovery

Machine learning approach using structure-preserving neural networks.

## Table of Contents

1. [Overview](#overview)
2. [HNN Architecture](#hnn-architecture)
3. [Conservation-Constrained Training](#conservation-constrained-training)
4. [Integral Discovery Head](#integral-discovery-head)
5. [Implementation](#implementation)
6. [Integration with Pipeline](#integration-with-pipeline)

---

## Overview

### Motivation

Traditional symbolic regression (SINDy, PySR) searches within a predefined basis. What if the conserved quantity has a form not in our basis?

**Hamiltonian Neural Networks (HNNs)** can:
1. Learn dynamics without explicit basis
2. Discover conserved quantities implicitly
3. Respect symplectic structure by construction

### Key Insight

If a neural network learns H̃(q, p) such that trajectories are well-predicted, and an auxiliary head learns Ĩ(q, p) that is constant along those trajectories, then Ĩ is a candidate conserved quantity.

### HNN vs Standard NN

| Aspect | Standard NN | HNN |
|--------|-------------|-----|
| Learns | (q̇, ṗ) directly | H(q, p) scalar |
| Derivatives | Predicted | Computed via ∂H/∂q, ∂H/∂p |
| Energy conservation | Not guaranteed | Exact (by construction) |
| Symplectic structure | Not preserved | Preserved |

---

## HNN Architecture

### Basic Structure

```
Input: (q, p) ∈ ℝ^(2n)
           │
           ▼
    ┌──────────────┐
    │ Hidden Layer │ (e.g., 128 neurons, softplus)
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Hidden Layer │ (e.g., 128 neurons, softplus)
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Output Layer │ → H̃(q, p) ∈ ℝ
    └──────┬───────┘
           │
           ├─────────────────────────────────┐
           │                                 │
           ▼                                 ▼
    ∂H̃/∂p = q̇                        -∂H̃/∂q = ṗ
    (via autograd)                   (via autograd)
```

### PyTorch Implementation

```python
import torch
import torch.nn as nn

class HamiltonianNN(nn.Module):
    """
    Hamiltonian Neural Network that learns H(q, p).

    Dynamics derived via Hamilton's equations:
        q̇ = ∂H/∂p
        ṗ = -∂H/∂q
    """

    def __init__(self, input_dim, hidden_dims=[128, 128], activation='softplus'):
        super().__init__()

        self.input_dim = input_dim
        self.n_dof = input_dim // 2  # Degrees of freedom

        # Build network
        layers = []
        prev_dim = input_dim

        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            if activation == 'softplus':
                layers.append(nn.Softplus())
            elif activation == 'tanh':
                layers.append(nn.Tanh())
            elif activation == 'relu':
                layers.append(nn.ReLU())
            prev_dim = hidden_dim

        layers.append(nn.Linear(prev_dim, 1))  # Scalar output H

        self.network = nn.Sequential(*layers)

    def forward(self, x):
        """
        Compute Hamiltonian H(q, p).

        Args:
            x: State (batch_size, 2n) with [q, p]

        Returns:
            H: Hamiltonian values (batch_size, 1)
        """
        return self.network(x)

    def time_derivative(self, x):
        """
        Compute (q̇, ṗ) via Hamilton's equations.

        Args:
            x: State (batch_size, 2n)

        Returns:
            dx_dt: Time derivatives (batch_size, 2n)
        """
        x = x.requires_grad_(True)
        H = self.forward(x)

        # Compute gradients
        grad_H = torch.autograd.grad(
            H.sum(), x, create_graph=True
        )[0]

        # Split into q and p components
        grad_q = grad_H[:, :self.n_dof]  # ∂H/∂q
        grad_p = grad_H[:, self.n_dof:]  # ∂H/∂p

        # Hamilton's equations
        q_dot = grad_p       # q̇ = ∂H/∂p
        p_dot = -grad_q      # ṗ = -∂H/∂q

        return torch.cat([q_dot, p_dot], dim=1)
```

---

## Conservation-Constrained Training

### Loss Function

Standard HNN loss trains on trajectory prediction:
```
L_dynamics = ||x(t + dt) - x(t) - dt·f_HNN(x(t))||²
```

For invariant discovery, add conservation constraint:
```
L_conservation = ||Ĩ(x(t + dt)) - Ĩ(x(t))||²
```

**Total loss**:
```
L = L_dynamics + λ · L_conservation
```

### Noether Regularizer

Enforce Poisson bracket constraint:
```
L_noether = ||{Ĩ, H̃}||²

where {Ĩ, H̃} = Σᵢ (∂Ĩ/∂qᵢ · ∂H̃/∂pᵢ - ∂Ĩ/∂pᵢ · ∂H̃/∂qᵢ)
```

### Implementation

```python
class HNNTrainer:
    """
    Trainer for Hamiltonian Neural Network with conservation constraint.
    """

    def __init__(self, model, learning_rate=1e-3, conservation_weight=1.0,
                 noether_weight=0.1):
        self.model = model
        self.optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        self.conservation_weight = conservation_weight
        self.noether_weight = noether_weight

    def dynamics_loss(self, x, x_next, dt):
        """Loss for trajectory prediction."""
        x_pred = x + dt * self.model.time_derivative(x)
        return torch.mean((x_pred - x_next)**2)

    def conservation_loss(self, x, x_next, integral_head):
        """Loss for integral conservation."""
        I_current = integral_head(x)
        I_next = integral_head(x_next)
        return torch.mean((I_next - I_current)**2)

    def noether_loss(self, x, integral_head):
        """
        Loss enforcing {I, H} = 0 (Poisson bracket).
        """
        x = x.requires_grad_(True)

        H = self.model(x)
        I = integral_head(x)

        # Compute gradients
        grad_H = torch.autograd.grad(H.sum(), x, create_graph=True)[0]
        grad_I = torch.autograd.grad(I.sum(), x, create_graph=True)[0]

        n = self.model.n_dof

        # Poisson bracket
        dI_dq = grad_I[:, :n]
        dI_dp = grad_I[:, n:]
        dH_dq = grad_H[:, :n]
        dH_dp = grad_H[:, n:]

        poisson_bracket = torch.sum(dI_dq * dH_dp - dI_dp * dH_dq, dim=1)

        return torch.mean(poisson_bracket**2)

    def train_step(self, x, x_next, dt, integral_head=None):
        """Single training step."""
        self.optimizer.zero_grad()

        # Dynamics loss
        loss = self.dynamics_loss(x, x_next, dt)

        # Conservation loss (if integral head provided)
        if integral_head is not None:
            loss += self.conservation_weight * self.conservation_loss(
                x, x_next, integral_head
            )
            loss += self.noether_weight * self.noether_loss(x, integral_head)

        loss.backward()
        self.optimizer.step()

        return loss.item()

    def fit(self, times, states, epochs=1000, integral_head=None):
        """
        Train HNN on trajectory data.

        Args:
            times: Time array (N,)
            states: State array (N, 2n)
            epochs: Number of training epochs
            integral_head: Optional network for integral discovery

        Returns:
            Training history
        """
        # Convert to tensors
        x = torch.tensor(states[:-1], dtype=torch.float32)
        x_next = torch.tensor(states[1:], dtype=torch.float32)
        dt = times[1] - times[0]

        history = {'loss': []}

        for epoch in range(epochs):
            loss = self.train_step(x, x_next, dt, integral_head)
            history['loss'].append(loss)

            if epoch % 100 == 0:
                print(f"Epoch {epoch}: loss = {loss:.6f}")

        return history
```

---

## Integral Discovery Head

### Architecture

Add auxiliary network to predict candidate integral:

```
HNN Output: H̃(q, p)
                │
                ├──────────────────┐
                │                  │
                ▼                  ▼
        Dynamics (q̇, ṗ)    Integral Head
                                   │
                                   ▼
                              Ĩ(q, p) ∈ ℝ
```

### Implementation

```python
class IntegralHead(nn.Module):
    """
    Auxiliary network to discover conserved quantities.
    """

    def __init__(self, input_dim, hidden_dims=[64, 64]):
        super().__init__()

        layers = []
        prev_dim = input_dim

        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.Softplus())
            prev_dim = hidden_dim

        layers.append(nn.Linear(prev_dim, 1))

        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)


class HNNWithIntegral(nn.Module):
    """
    Combined HNN with integral discovery head.
    """

    def __init__(self, input_dim, hnn_hidden=[128, 128], integral_hidden=[64, 64]):
        super().__init__()

        self.hnn = HamiltonianNN(input_dim, hnn_hidden)
        self.integral_head = IntegralHead(input_dim, integral_hidden)

    def forward(self, x):
        """Return both H and I."""
        return self.hnn(x), self.integral_head(x)

    def evaluate_hamiltonian(self, x):
        return self.hnn(x)

    def evaluate_integral(self, x):
        return self.integral_head(x)

    def time_derivative(self, x):
        return self.hnn.time_derivative(x)
```

---

## Implementation

### Complete Training Pipeline

```python
def train_hnn_for_discovery(times, states, epochs=1000,
                            conservation_weight=1.0):
    """
    Train HNN with integral discovery.

    Args:
        times: Time array
        states: State array (N, 2n)
        epochs: Training epochs
        conservation_weight: Weight on conservation loss

    Returns:
        model: Trained HNN with integral head
        history: Training history
    """
    input_dim = states.shape[1]

    # Create model
    model = HNNWithIntegral(
        input_dim=input_dim,
        hnn_hidden=[128, 128, 64],
        integral_hidden=[64, 64]
    )

    # Create trainer
    trainer = HNNTrainer(
        model.hnn,
        learning_rate=1e-3,
        conservation_weight=conservation_weight
    )

    # Train
    history = trainer.fit(
        times, states,
        epochs=epochs,
        integral_head=model.integral_head
    )

    return model, history


def extract_learned_integral(model, states):
    """
    Extract learned integral values from trained model.

    Args:
        model: Trained HNNWithIntegral
        states: State array (N, 2n)

    Returns:
        integral_values: Array of I(x) values
    """
    model.eval()
    with torch.no_grad():
        x = torch.tensor(states, dtype=torch.float32)
        I = model.evaluate_integral(x)
    return I.numpy().flatten()
```

### Symbolic Extraction

After training, extract symbolic form via symbolic regression:

```python
def symbolify_learned_integral(model, states, method='pysr'):
    """
    Convert learned integral to symbolic expression.

    Strategy: Use PySR to fit symbolic expression to learned values.
    """
    # Get learned values
    I_learned = extract_learned_integral(model, states)

    if method == 'pysr':
        from pysr import PySRRegressor

        pysr = PySRRegressor(
            niterations=50,
            binary_operators=['+', '-', '*', '/'],
            unary_operators=['sin', 'cos', 'sqrt'],
            maxsize=15,
        )

        pysr.fit(states, I_learned)

        return pysr.sympy()

    elif method == 'sindy':
        from src.python.symbolic.regression_pipeline import SINDyRegressor

        sindy = SINDyRegressor(
            basis_type='polynomial',
            max_degree=4,
            threshold=0.1
        )

        # Create fake "times" for SINDy (it expects time series)
        fake_times = np.arange(len(states))
        result = sindy.fit(fake_times, states, target=I_learned)

        return result.expression
```

---

## Integration with Pipeline

### As Pipeline Stage

```python
class HNNSearchStage:
    """
    HNN-based search stage for multi-stage pipeline.
    """

    def __init__(self, epochs=500, conservation_weight=1.0):
        self.epochs = epochs
        self.conservation_weight = conservation_weight

    def search(self, times, states, **kwargs):
        """
        Search for integrals using HNN.

        Returns:
            List of candidate objects
        """
        # Train HNN
        model, history = train_hnn_for_discovery(
            times, states,
            epochs=self.epochs,
            conservation_weight=self.conservation_weight
        )

        # Extract learned integral
        I_values = extract_learned_integral(model, states)

        # Check if it's conserved
        conservation_error = np.std(I_values) / (np.abs(np.mean(I_values)) + 1e-15)

        if conservation_error < 1e-3:  # Promising
            # Try to symbolify
            try:
                expression = symbolify_learned_integral(model, states)
            except:
                expression = "HNN_learned_integral"

            candidate = Candidate(
                expression=str(expression),
                values=I_values,
                conservation_error=conservation_error,
                method='hnn',
                model=model
            )

            return [candidate]

        return []
```

### Usage in MultiStageSearch

```python
from src.python.symbolic.multi_stage_pipeline import MultiStageInvariantSearch

# Add HNN as a search stage
search = MultiStageInvariantSearch(
    stages=['hnn', 'spinor', 'elliptic', 'polynomial'],
    hnn_epochs=500,
    max_candidates_per_stage=5
)

results = search.run(times, states, mu=mu)

# HNN candidates in results
hnn_candidates = results.by_stage.get('hnn', [])
for cand in hnn_candidates:
    print(f"HNN found: {cand.expression}")
    print(f"Conservation: {cand.conservation_error:.2e}")
```

---

## Advanced Topics

### SympNets (Symplectic Networks)

Alternative architecture that enforces symplecticity at the layer level:

```python
class SympNetLayer(nn.Module):
    """
    Single symplectic layer (gradient map).
    """
    def __init__(self, n_dof, activation='softplus'):
        super().__init__()
        self.n_dof = n_dof
        self.W = nn.Linear(n_dof, n_dof, bias=True)
        self.act = nn.Softplus() if activation == 'softplus' else nn.Tanh()

    def forward(self, q, p):
        # Type 1: q' = q, p' = p + ∇V(q)
        V = self.act(self.W(q)).sum(dim=1, keepdim=True)
        grad_V = torch.autograd.grad(V.sum(), q, create_graph=True)[0]
        return q, p + grad_V
```

### Out-of-Distribution Validation

Test learned integral on different mass ratios:

```python
def validate_ood(model, mu_values=[0.001, 0.01, 0.1]):
    """
    Test if learned integral generalizes to different parameters.
    """
    results = {}

    for mu in mu_values:
        # Generate trajectory at new mu
        times, states = generate_trajectory(mu=mu)

        # Evaluate learned integral
        I_values = extract_learned_integral(model, states)

        # Measure conservation
        error = np.std(I_values) / (np.abs(np.mean(I_values)) + 1e-15)
        results[mu] = error

    return results
```

---

## References

- Greydanus, S. et al. (2019). "Hamiltonian Neural Networks", *NeurIPS*
- Chen, Z. et al. (2020). "Symplectic Recurrent Neural Networks", *ICLR*
- Cranmer, M. et al. (2020). "Discovering Symbolic Models from Deep Learning with Inductive Biases", *NeurIPS*
- Jin, P. et al. (2020). "SympNets: Intrinsic structure-preserving symplectic networks", *Neural Networks*
