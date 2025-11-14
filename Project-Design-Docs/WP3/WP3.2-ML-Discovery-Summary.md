# WP 3.2: Structure-Preserving Machine Learning Discovery
## Complete Implementation Summary

**Duration**: 18-22 days
**Approach**: Geometric deep learning with physics constraints
**Goal**: Discover conserved quantities using Hamiltonian Neural Networks

---

## Overview

WP 3.2 employs machine learning methods that respect the symplectic geometry of the three-body problem to discover conserved quantities implicitly encoded in trajectory data. Unlike traditional neural networks, these architectures preserve the Hamiltonian structure, enabling discovery of conservation laws.

### Architecture Philosophy

**Key Insight**: If a conserved quantity $\widetilde{I}$ exists, it satisfies:
$$
\frac{d\widetilde{I}}{dt} = \{\widetilde{I}, \widetilde{H}\}_{\widetilde{\omega}} = 0
$$

We can train a neural network to learn $\widetilde{I}$ by enforcing this condition as a soft constraint.

---

## Four-Task Pipeline

```
Task 3.2.1: High-Precision Data Generation (4-5 days)
    ↓ Trajectory datasets on lifted spaces
Task 3.2.2: HNN/SympNet Architecture (5-6 days)
    ↓ Network learns lifted Hamiltonian
Task 3.2.3: Conservation-Constrained Training (6-7 days)
    ↓ Auxiliary head learns integral I
Task 3.2.4: Validation & Generalization (3-4 days)
    ↓ Out-of-distribution testing
```

---

## Task Summaries

### Task 3.2.1: Data Generation on the Lift

**Objective**: Create high-quality training datasets from WP2 lifted dynamics.

**Data Requirements**:
- **Volume**: 10^5 - 10^6 trajectory segments
- **Precision**: Energy conservation $|\Delta E| / E < 10^{-12}$
- **Coverage**: Diverse mass ratios, energies, angular momenta
- **Format**: (state, time derivative) pairs

**Data Generation Strategy**:

1. **Parameter Space Sampling**:
   - Mass ratios: $\mu \in [0.01, 0.5]$ (mass ratio $m_2/m_1$)
   - Energies: $E \in [-2, -0.1]$ (bound orbits)
   - Angular momenta: $L \in [0.5, 3.0]$
   - Initial conditions: Latin hypercube sampling

2. **Integration**:
   - Use WP1 high-precision integrators (IAS15)
   - Integrate for 10-100 orbital periods
   - Store state every $\Delta t = 0.01$ time units
   - Quality control: Reject trajectories with energy drift $> 10^{-10}$

3. **Augmentation**:
   - Symmetry transformations (permutations for equal masses)
   - Time reversal (Hamiltonian systems are time-reversible)
   - Scaling transformations (virial theorem)

**Implementation**:

```python
# src/python/ml/data_generation.py

def generate_lifted_trajectories(
    lift_type: str,  # 's1' or 'ks'
    num_samples: int,
    param_ranges: Dict[str, Tuple[float, float]],
    t_span: float,
    dt: float
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate training data on lifted manifolds.

    Returns:
        states: (N, dim) - Phase space states
        derivatives: (N, dim) - Time derivatives dz/dt
    """
    pass
```

**Deliverables**:
- [ ] `data_generation.py` - Trajectory generation
- [ ] `data_augmentation.py` - Symmetry augmentation
- [ ] `dataset_validation.py` - Quality control
- [ ] HDF5 datasets: `s1_bundle_train.h5`, `ks_spinor_train.h5`

**Dataset Size**: ~10-50 GB

---

### Task 3.2.2: HNN/SympNet Architecture

**Objective**: Implement neural network architectures that preserve symplectic structure.

**Architecture Options**:

#### Option 1: Hamiltonian Neural Network (HNN)

**Core Idea**: Learn the Hamiltonian $\widetilde{H}_\theta(q, p)$ such that:
$$
\dot{q} = \frac{\partial \widetilde{H}_\theta}{\partial p}, \quad \dot{p} = -\frac{\partial \widetilde{H}_\theta}{\partial q}
$$

**Network Structure**:
```
Input: (q, p) ∈ R^{2n}
    ↓
Hidden Layers (MLP): [256, 256, 128]
    ↓
Output: H_θ(q, p) ∈ R
    ↓
Automatic Differentiation: (∂H/∂p, -∂H/∂q)
    ↓
Predicted: (dq/dt, dp/dt)
```

**Advantages**:
- Exactly preserves symplectic structure by construction
- Energy conservation if $H_\theta$ is time-independent
- Interpretable output (learned Hamiltonian)

---

#### Option 2: Symplectic Neural Network (SympNet)

**Core Idea**: Learn a symplectic flow map $\phi_\theta: (q_0, p_0) \to (q_t, p_t)$.

**Network Structure**: Composition of learned symplectic transformations.

**Advantages**:
- Better for long-time integration
- Can learn non-Hamiltonian perturbations

---

**Implementation** (JAX for automatic differentiation):

```python
# src/python/ml/hnn_architecture.py

import jax
import jax.numpy as jnp
from flax import linen as nn

class HamiltonianNN(nn.Module):
    """Hamiltonian Neural Network."""

    hidden_dims: Sequence[int] = (256, 256, 128)

    @nn.compact
    def __call__(self, z):
        """
        Args:
            z: Phase space state (2n,) = (q, p)

        Returns:
            H: Scalar Hamiltonian value
        """
        x = z
        for dim in self.hidden_dims:
            x = nn.Dense(dim)(x)
            x = nn.tanh(x)  # Smooth activation
        H = nn.Dense(1)(x)
        return jnp.squeeze(H)

    def dynamics(self, z):
        """
        Compute dz/dt = J ∇H where J is symplectic matrix.
        """
        n = len(z) // 2

        # Compute gradient of H
        grad_H = jax.grad(self.__call__)(z)

        # Symplectic matrix multiplication: J ∇H = (∂H/∂p, -∂H/∂q)
        dq_dt = grad_H[n:]   # ∂H/∂p
        dp_dt = -grad_H[:n]  # -∂H/∂q

        return jnp.concatenate([dq_dt, dp_dt])
```

**Deliverables**:
- [ ] `hnn_architecture.py` - HNN implementation (JAX/Flax)
- [ ] `sympnet_architecture.py` - SympNet alternative
- [ ] `model_utils.py` - Training utilities
- [ ] Unit tests on toy Hamiltonians (harmonic oscillator, Kepler)

---

### Task 3.2.3: Constrained Training for Invariant Discovery

**Objective**: Extend HNN to learn conserved quantities via auxiliary prediction head.

**Extended Architecture**:

```
Input: (q, p)
    ↓
Shared Encoder: [256, 256]
    ↓
    ├─→ Hamiltonian Head: H_θ(q,p)
    │       ↓
    │   Dynamics: dz/dt = J ∇H
    │
    └─→ Invariant Head: I_φ(q,p)
            ↓
        Conservation Loss: E[|dI_φ/dt|²]
```

**Training Objective**:

$$
\mathcal{L} = \mathcal{L}_{\text{trajectory}} + \lambda_1 \mathcal{L}_{\text{conservation}} + \lambda_2 \mathcal{L}_{\text{Noether}}
$$

where:

1. **Trajectory Loss**: Predict dynamics accurately
   $$
   \mathcal{L}_{\text{trajectory}} = \mathbb{E}\left[ \left\| \frac{dz}{dt}_{\text{true}} - J\nabla H_\theta(z) \right\|^2 \right]
   $$

2. **Conservation Loss**: Enforce $dI_\phi/dt = 0$
   $$
   \mathcal{L}_{\text{conservation}} = \mathbb{E}\left[ \left| \{I_\phi, H_\theta\} \right|^2 \right]
   $$

   where $\{I_\phi, H_\theta\} = \nabla I_\phi \cdot J \nabla H_\theta$ (Poisson bracket).

3. **Noether Regularizer**: Encourage symmetry-based integrals
   $$
   \mathcal{L}_{\text{Noether}} = \mathbb{E}\left[ \|I_\phi(\sigma(z)) - I_\phi(z)\|^2 \right]
   $$

   for symmetry transformations $\sigma$ (e.g., permutations, rotations).

**Implementation**:

```python
# src/python/ml/conservation_loss.py

def conservation_loss(model, params, batch):
    """
    Compute conservation constraint loss.

    Args:
        model: HNN with invariant head
        params: Network parameters
        batch: (states, derivatives)

    Returns:
        loss: Scalar conservation violation
    """
    states, _ = batch

    # Forward pass
    H = model.apply(params, states, method='hamiltonian')
    I = model.apply(params, states, method='invariant')

    # Compute Poisson bracket {I, H}
    def poisson_bracket(z):
        grad_I = jax.grad(lambda x: model.apply(params, x, method='invariant'))(z)
        grad_H = jax.grad(lambda x: model.apply(params, x, method='hamiltonian'))(z)

        n = len(z) // 2
        # {I, H} = ∂I/∂q · ∂H/∂p - ∂I/∂p · ∂H/∂q
        poisson = jnp.dot(grad_I[:n], grad_H[n:]) - jnp.dot(grad_I[n:], grad_H[:n])
        return poisson

    # Vectorize over batch
    poisson_values = jax.vmap(poisson_bracket)(states)

    # Loss: squared Poisson bracket (should be zero)
    loss = jnp.mean(poisson_values**2)

    return loss
```

**Deliverables**:
- [ ] `conservation_loss.py` - Physics-informed loss functions
- [ ] `noether_regularizers.py` - Symmetry-based priors
- [ ] `training.py` - Training loop with multiple loss terms
- [ ] Hyperparameter tuning: $\lambda_1, \lambda_2$ via grid search

---

### Task 3.2.4: Validation and Generalization Guardrails

**Objective**: Ensure discovered integrals are genuine and not spurious overfitting.

**Validation Strategy**:

1. **Train/Val/Test Split** (Rigorous):
   - **Train**: 70% of trajectories
   - **Validation**: 15% (same parameter ranges, different ICs)
   - **Test**: 15% (held-out parameter regimes)

2. **Out-of-Distribution (OOD) Tests**:
   - **Mass Ratio OOD**: Train on $\mu \in [0.1, 0.3]$, test on $\mu \in [0.4, 0.5]$
   - **Energy OOD**: Train on $E \in [-1.5, -0.5]$, test on $E \in [-2, -1.5]$
   - **Long-Time OOD**: Train on 10-period trajectories, test on 100-period

3. **Conservation Verification**:
   - Integrate trajectories with learned $H_\theta$
   - Monitor $\Delta I_\phi / I_\phi$ over time
   - **Acceptance**: Drift $< 10^{-5}$ over 100 periods

4. **Functional Independence**:
   - Compute Jacobian: $\frac{\partial (E, L, I_\phi)}{\partial (q, p)}$
   - Check rank numerically on 10^4 random states
   - **Acceptance**: Rank increases by 1 (new independent integral)

**Implementation**:

```python
# src/python/ml/validation.py

def validate_conservation_ood(
    model,
    params,
    test_dataset,
    t_span: float = 100.0
) -> Dict[str, float]:
    """
    Out-of-distribution conservation validation.

    Returns:
        metrics: {
            'conservation_error': float,
            'generalization_gap': float,
            'functional_independence': bool
        }
    """
    pass
```

**Deliverables**:
- [ ] `validation.py` - Comprehensive validation suite
- [ ] `ood_tests.py` - Out-of-distribution testing
- [ ] `independence_test.py` - Jacobian rank verification
- [ ] Validation report: Plots, tables, acceptance criteria

---

## Expected Outcomes

### Best Case: Conserved Integral Discovered
- Trained model predicts $I_\phi(q, p)$ with conservation error $< 10^{-6}$
- Functionally independent of E, L, $p_\theta$
- Generalizes across parameter space
- → Extract numerical form, pass to WP 3.3 for symbolic regression

### Moderate Case: Approximate Integral
- Conservation error $\sim 10^{-4}$ to $10^{-6}$
- May be regime-specific (e.g., works only for low energy)
- → Document as "near-integral" or "adiabatic invariant"

### Negative Case: No Conservation Learned
- Network fails to find conserved quantities beyond known ones
- → Indicates no simple functional form exists
- → Document negative result, proceed with WP 3.1 results only

---

## Computational Resources

**Hardware Requirements**:
- **GPU**: NVIDIA A100 or V100 (16-40 GB VRAM)
- **CPU**: 16+ cores for data generation
- **RAM**: 64-128 GB (for large datasets)
- **Storage**: 100 GB (datasets + model checkpoints)

**Training Time**:
- Data generation: 1-2 days
- Model training: 2-4 days (1000+ epochs)
- Validation: 1 day

**Optimization**:
- Mixed precision training (float16/bfloat16)
- Distributed training (multi-GPU with JAX pmap)
- Checkpointing and early stopping

---

## Integration with Other WP3 Tasks

### From WP 3.1 (Geometric Search)
- **Input**: Discovered Killing fields → Use as architectural priors
- **Comparison**: Do ML and geometric methods agree?

### To WP 3.3 (Symbolic Regression)
- **Output**: Numerical function $I_\phi(q, p)$ → Fit symbolic expression
- **Evaluation data**: High-precision samples for regression

---

## Key Innovations

1. **First Application to Celestial Mechanics**: HNNs haven't been applied to discover hidden integrals in N-body problems
2. **Conservation-Constrained Training**: Novel loss function enforcing Poisson bracket = 0
3. **Lifted Coordinate Discovery**: Learning integrals in higher-dimensional spaces
4. **Rigorous Generalization Testing**: OOD validation prevents spurious results

---

## Deliverables Summary

### Code (4 main modules)
- [ ] `data_generation.py` - Trajectory datasets
- [ ] `hnn_architecture.py` - Neural network models
- [ ] `conservation_loss.py` - Physics-informed training
- [ ] `validation.py` - Generalization testing

### Models
- [ ] Trained HNN for S¹ bundle
- [ ] Trained HNN for KS manifold (optional)
- [ ] Model checkpoints and hyperparameters

### Documentation
- [ ] Technical report: "ML Discovery of Hidden Integrals" (20+ pages)
- [ ] Training curves and ablation studies
- [ ] Validation plots (conservation vs. time, OOD performance)

---

## Success Criteria

**Minimum Success**:
- [ ] HNN accurately learns lifted Hamiltonian (trajectory error < 1%)
- [ ] Training pipeline functional and documented
- [ ] Validation framework in place

**Target Success**:
- [ ] Invariant head discovers conserved $I_\phi$ with error $< 10^{-5}$
- [ ] Generalization verified on OOD tests
- [ ] Functional independence confirmed

**Stretch Success**:
- [ ] Multiple independent integrals discovered
- [ ] Analytical form extractable via symbolic regression
- [ ] Universal across full parameter space

---

## References

1. **Hamiltonian Neural Networks**:
   - Greydanus et al., "Hamiltonian Neural Networks" (2019)
   - Toth et al., "Hamiltonian Generative Networks" (2020)

2. **Symplectic Neural Networks**:
   - Chen et al., "Symplectic Recurrent Neural Networks" (2020)
   - Jin et al., "SympNets: Intrinsic structure-preserving symplectic networks" (2020)

3. **Physics-Informed ML**:
   - Raissi et al., "Physics-informed neural networks" (2019)
   - Cranmer et al., "Lagrangian Neural Networks" (2020)

4. **Conservation Law Discovery**:
   - Sanchez-Gonzalez et al., "Learning to Simulate Complex Physics" (2020)
   - Zhong et al., "Unsupervised Learning of Lagrangian Dynamics" (2020)

---

**Document Version**: 1.0
**Last Updated**: 2025-11-14
**Status**: Complete Planning - Ready for Implementation
