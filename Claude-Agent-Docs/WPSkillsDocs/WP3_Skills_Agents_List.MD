# WP3: Discovery of Candidate Invariants
## Skills and Subagents List

**Work Package**: WP3 - Discovery of Candidate Invariants ($\widetilde{I}$)
**Purpose**: Search for hidden integrals "upstairs" in lifted spaces
**Duration**: 35-45 days
**Key Activities**: Geometric search, ML discovery, symbolic regression, consolidation

---

## Overview

WP3 employs a **three-pronged discovery strategy** to find conserved quantities that may exist in the lifted phase spaces but are invisible in standard coordinates. This document catalogs the Skills and Subagents for each discovery track.

---

## 1. Agent Skills

### 1.1 Killing Equation Formulation

**Name**: `wp3-killing-equations`

**Description**: Use when setting up Killing field/tensor PDEs on lifted manifolds. Provides formulation, discretization, and solution strategies for finding geometric symmetries.

**When to Invoke**:
- User requests "Killing fields", "symmetry search", "PDE for integrals"
- Implementing WP 3.1
- Geometric approach to invariant discovery

**Workflow**:
```markdown
# Killing Field/Tensor Equations

## Killing Vector Fields (Linear Integrals)

**Equation**: ∇_(i K_j) = 0 (symmetrized covariant derivative)

**Implementation**:
```python
def killing_vector_equation(K, g_JM, mesh):
    """
    Killing equation: ∇_(i K_j) = 0

    Discretized on mesh → sparse linear system
    """
    # Christoffel symbols from JM metric
    Gamma = christoffel_symbols(g_JM)

    # Covariant derivative: ∇_i K_j = ∂_i K_j - Γ^k_ij K_k
    nabla_K = compute_covariant_derivative(K, Gamma, mesh)

    # Symmetrize: (∇_i K_j + ∇_j K_i) / 2 = 0
    killing_condition = symmetrize(nabla_K)

    return killing_condition  # Should be zero
```

**Discretization**: Finite element method on mesh
**Solution**: Least-squares + regularization

## Killing Tensors (Quadratic Integrals)

**Equation**: ∇_(k K_ij) = 0

**Physical Meaning**: Generators of hidden symmetries (e.g., Runge-Lenz vector)

## References
- Benenti (2002): "Intrinsic characterization of variable separation"
- WP 3.1.2: PDE Formulation
```

**Supporting Assets**:
- `src/python/pde/killing_equations.py`
- `src/python/pde/mesh_discretization.py`

---

### 1.2 Hamiltonian Neural Network Training

**Name**: `wp3-hnn-training`

**Description**: Use when training structure-preserving neural networks (HNNs, SympNets) to discover conserved quantities from trajectory data. Includes conservation-constrained loss functions.

**When to Invoke**:
- User requests "train HNN", "neural network discovery", "ML for integrals"
- Implementing WP 3.2
- Data-driven approach

**Workflow**:
```markdown
# HNN Training Workflow

## Architecture

**Hamiltonian Neural Network**:
```python
class HNN(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.Tanh(),
            nn.Linear(128, 128),
            nn.Tanh(),
            nn.Linear(128, 1)  # Outputs scalar H
        )

    def forward(self, q, p):
        z = torch.cat([q, p], dim=-1)
        H = self.net(z)
        return H

    def hamiltonian_dynamics(self, q, p):
        # dq/dt = ∂H/∂p, dp/dt = -∂H/∂q
        H = self.forward(q, p)
        dq_dt = torch.autograd.grad(H, p, grad_outputs=torch.ones_like(H), create_graph=True)[0]
        dp_dt = -torch.autograd.grad(H, q, grad_outputs=torch.ones_like(H), create_graph=True)[0]
        return dq_dt, dp_dt
```

## Conservation-Constrained Loss

**Objective**: Learn integral I such that dI/dt = 0

```python
def conservation_loss(model, trajectories):
    # Standard trajectory prediction loss
    loss_traj = trajectory_loss(model, trajectories)

    # Conservation constraint: {I, H} = 0
    I = model.integral_head(q, p)
    H = model.hamiltonian(q, p)
    poisson_bracket = compute_poisson_bracket(I, H, q, p)

    loss_conservation = torch.mean(poisson_bracket**2)

    # Combined loss
    return loss_traj + lambda_conservation * loss_conservation
```

## Noether Regularization

**Idea**: Encourage discovery of symmetry-based integrals

## References
- Greydanus et al. (2019): "Hamiltonian Neural Networks"
- WP 3.2.3: Conservation-Constrained Training
```

**Supporting Assets**:
- `src/python/ml/hnn_architecture.py`
- `src/python/ml/conservation_loss.py`

---

### 1.3 Symbolic Regression Pipeline

**Name**: `wp3-symbolic-regression`

**Description**: Use when converting numerical candidate integrals into analytical expressions. Integrates SINDy, PySR, and AI-Feynman for physics-informed symbolic discovery.

**When to Invoke**:
- User requests "symbolic form", "analytical expression", "SINDy"
- Implementing WP 3.3
- Converting numerical → symbolic

**Workflow**:
```markdown
# Symbolic Regression Workflow

## Step 1: Generate Training Data

**From Numerical Candidate**:
```python
def generate_symbolic_training_data(I_numerical, n_samples=10000):
    # Sample phase space
    states = sample_phase_space(n_samples)

    # Evaluate numerical integral
    I_vals = [I_numerical(state) for state in states]

    # Also compute geometric quantities (basis functions)
    basis_features = []
    for state in states:
        features = {
            'r12': distance(state, 1, 2),
            'r23': distance(state, 2, 3),
            'r31': distance(state, 3, 1),
            'E': energy(state),
            'L': angular_momentum(state),
            'p_theta': fiber_momentum(state),
            # Higher-order terms
            'r12_squared': distance(state, 1, 2)**2,
            # ...
        }
        basis_features.append(features)

    return basis_features, I_vals
```

## Step 2: SINDy (Sparse Identification)

```python
from pysindy import SINDy

# Define library of candidate functions
library = PolynomialLibrary(degree=3) + FourierLibrary()

model = SINDy(feature_library=library, optimizer=STLSQ(threshold=0.01))
model.fit(X, y)  # X = basis features, y = I_vals

# Extract symbolic form
symbolic_I = model.print()
```

## Step 3: PySR (Evolutionary Search)

```python
from pysr import PySRRegressor

model = PySRRegressor(
    binary_operators=["+", "*", "/", "-"],
    unary_operators=["sin", "cos", "sqrt", "square"],
    constraints={'sqrt': (1, 1), '/': (5, 1)},  # Complexity penalties
    loss="L2DistLoss()",
)

model.fit(X, y)
print(model)  # Best expression found
```

## Step 4: Validation

**Test symbolic form**:
```python
def validate_symbolic_integral(I_symbolic, I_numerical):
    states_test = sample_phase_space(1000)

    for state in states_test:
        val_symbolic = I_symbolic(state)
        val_numerical = I_numerical(state)

        error = abs(val_symbolic - val_numerical)
        assert error < 1e-10, f"Residual: {error}"
```

## References
- Brunton et al. (2016): "Discovering governing equations from data by sparse identification"
- Cranmer (2023): "Interpretable Machine Learning for Science with PySR"
```

**Supporting Assets**:
- `src/python/symbolic/regression_pipeline.py`
- `src/python/symbolic/basis_functions.py`

---

### 1.4 Conservation Verification Protocol

**Name**: `wp3-conservation-check`

**Description**: Use when verifying that a candidate integral is truly conserved along trajectories. Provides numerical integration tests and drift analysis.

**When to Invoke**:
- User asks "is this conserved?", "verify integral", "check conservation"
- Testing candidates from any track (3.1, 3.2, 3.3)
- Quality control

**Workflow**:
```markdown
# Conservation Verification

## Test Protocol

**Step 1: Time Series**
```python
def test_conservation(I_candidate, state0, t_max=1000):
    # Integrate trajectory
    trajectory = integrate(state0, t_max)

    # Evaluate integral along trajectory
    I_vals = [I_candidate(state) for state in trajectory]

    # Compute drift
    Delta_I = [I - I_vals[0] for I in I_vals]
    drift = max(abs(dI) for dI in Delta_I)

    # Relative error
    epsilon_I = drift / abs(I_vals[0])

    return epsilon_I
```

**Acceptance**: ε_I < 10^-6 (minimum), < 10^-8 (target)

**Step 2: Statistical Validation**
- Test on 1000 random initial conditions
- Success rate: >95% should pass

**Step 3: Poisson Bracket**
```python
def verify_via_poisson_bracket(I, H):
    # Symbolic or numerical PB
    pb = poisson_bracket(I, H)

    # Should be zero
    assert max(abs(pb)) < 1e-10
```

## References
- WP 3.3.3: Candidate Validation
```

**Supporting Assets**:
- `src/python/analysis/conservation_test.py`

---

### 1.5 Functional Independence Test

**Name**: `wp3-independence-test`

**Description**: Use when checking if a candidate integral is functionally independent of known integrals (E, L, p_θ). Uses Jacobian rank test.

**When to Invoke**:
- User asks "is this independent?", "Jacobian rank", "new integral?"
- Verifying non-triviality of candidates

**Workflow**:
```markdown
# Functional Independence Test

## Jacobian Rank Method

**Test**: rank(∇I₁, ∇I₂, ..., ∇I_n) = n?

```python
def test_functional_independence(integrals, n_samples=10000):
    # Known integrals
    known = [energy, angular_momentum_x, angular_momentum_y, angular_momentum_z, fiber_momentum]

    # Add candidate
    all_integrals = known + [new_candidate]

    # Sample phase space
    states = sample_phase_space(n_samples)

    ranks = []
    for state in states:
        # Compute gradients
        gradients = [numerical_gradient(I, state) for I in all_integrals]

        # Stack into matrix
        J = np.vstack(gradients)

        # Rank
        rank = np.linalg.matrix_rank(J, tol=1e-10)
        ranks.append(rank)

    # Statistics
    expected_rank = len(all_integrals)
    success_rate = sum(r == expected_rank for r in ranks) / len(ranks)

    return success_rate > 0.99  # 99% of samples should have full rank
```

## Interpretation
- rank = n: Independent ✓
- rank < n: Dependent (candidate is function of known integrals) ✗

## References
- WP 4.1.3: Functional Independence Validation
```

**Supporting Assets**:
- `src/python/analysis/independence_test.py`

---

### 1.6 Involution Verification

**Name**: `wp3-involution-check`

**Description**: Use when verifying that integrals Poisson-commute (involution condition for integrability). Essential Liouville criterion.

**When to Invoke**:
- User asks "do they commute?", "involution?", "Poisson brackets"
- Checking integrability conditions

**Workflow**:
```markdown
# Involution Verification

## Test All Pairs

**Condition**: {I_i, I_j} = 0 for all i, j

```python
def verify_involution(integrals):
    from itertools import combinations

    for I, J in combinations(integrals, 2):
        # Compute Poisson bracket
        pb = poisson_bracket(I, J)

        # Numerical evaluation on sample
        states = sample_phase_space(1000)
        pb_vals = [pb(state) for state in states]

        # Check
        max_pb = max(abs(val) for val in pb_vals)

        if max_pb > 1e-10:
            print(f"FAIL: {{{I.name}, {J.name}}} = {max_pb}")
            return False

    print("PASS: All integrals in involution")
    return True
```

## References
- Arnold (1989): "Mathematical Methods of Classical Mechanics"
- WP 4.1.2: Involution Testing
```

**Supporting Assets**:
- `src/python/analysis/involution_test.py`

---

## 2. Subagents

### 2.1 Killing Field PDE Solver

**Name**: `wp3-killing-solver`

**Description**: Use PROACTIVELY when solving Killing field/tensor PDEs on lifted manifolds. Handles mesh generation, sparse linear systems, and solution filtering. MUST BE USED for WP 3.1.

**Isolated Context Benefits**:
- Solves large sparse PDEs (10^4 mesh points)
- Tests multiple regularization schemes
- Returns only non-trivial solutions

**System Prompt**:
```markdown
You are a PDE specialist for geometric symmetry discovery.

Your task: Solve Killing field equations on lifted JM metric.

## Workflow

### Step 1: Lifted JM Metric
- Compute: g_JM on S¹ bundle or KS spinor space
- Verify: positive definite, smooth

### Step 2: Mesh Generation
- Domain: Lifted configuration manifold
- Method: Delaunay triangulation or structured grid
- Size: 10^4 points (adjust for computational budget)

### Step 3: Killing PDE Discretization
- Finite element method
- Result: Sparse linear system A·K = 0
- Size: ~10^5 equations

### Step 4: Solution
- Method: SVD of A, find null space
- Regularization: Tikhonov if needed
- Output: Killing field candidates

### Step 5: Filtering
- Remove trivial: E, L, p_θ, fiber coordinates
- Check: Non-zero on interior
- Validate: Really satisfies Killing equation (residual < 10^-8)

## Output Format
```
Killing Field Search Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mesh: 12,483 points on S¹ bundle
PDE System: 87,341 equations
Solution Time: 14m 32s

Killing Fields Found: 4
  1. K₁ = ∂/∂θ (trivial - fiber coordinate) ✗
  2. K₂ = ... (corresponds to angular momentum) ✗
  3. K₃ = ... (non-trivial!) ✓
  4. K₄ = ... (linear combination of K₂, K₃) ✗

Non-Trivial Candidates: 1
Associated Integral: I = K₃ · ∂H/∂p

Validation:
  - Killing equation residual: 2.1×10^-9 ✓
  - Conservation: tested on 100 trajectories ✓

[Candidate exported: output/killing_field_K3.json]
```
```

**Invocation Criteria**:
- WP 3.1 implementation
- User requests "solve Killing equations", "find symmetries"

---

### 2.2 ML Integral Discovery Trainer

**Name**: `wp3-ml-trainer`

**Description**: Use PROACTIVELY when training HNNs or SympNets to discover integrals from trajectory data. Handles data generation, architecture search, and out-of-distribution validation. MUST BE USED for WP 3.2.

**Isolated Context Benefits**:
- Trains for 1000+ epochs without polluting context
- Handles hyperparameter tuning
- Returns only converged models

**System Prompt**:
```markdown
You are an ML specialist for physics-informed neural networks.

Your task: Train HNN to discover conserved quantities.

## Phase 1: Data Generation (WP 3.2.1)

### High-Precision Trajectories
- Source: WP1 catalogue + new integrations on lifts
- Size: 10^5 trajectories
- Format: (t, q, p) sequences

### Train/Val/Test Split
- Train: 70% (random initial conditions)
- Val: 15% (held-out ICs)
- Test: 15% (held-out mass ratios, energies)

## Phase 2: Architecture (WP 3.2.2)

### Primary: HNN
```python
class HNNWithIntegral(nn.Module):
    def __init__(self):
        super().__init__()
        self.hamiltonian_net = MLP([dim_state, 256, 256, 1])
        self.integral_net = MLP([dim_state, 128, 128, 1])

    def forward(self, state):
        H = self.hamiltonian_net(state)
        I = self.integral_net(state)
        return H, I

    def loss(self, trajectory):
        # Trajectory prediction
        loss_traj = ...

        # Conservation: dI/dt = {I, H} = 0
        loss_conservation = ...

        return loss_traj + lambda_c * loss_conservation
```

## Phase 3: Training (WP 3.2.3)

### Hyperparameters
- Optimizer: Adam, lr=1e-3
- Epochs: 1000 (early stopping)
- Batch size: 256
- λ_conservation: 10.0 (tune)

### Monitoring
- Conservation error: |dI/dt|
- Trajectory accuracy: RMSE
- Out-of-distribution: test set performance

## Phase 4: Validation (WP 3.2.4)

### Tests
1. Conservation: ε_I < 10^-6 on test set
2. Generalization: <5% accuracy drop on held-out parameters
3. Independence: Jacobian rank test

## Output Format
```
ML Integral Discovery Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Training Data: 105,000 trajectories
Architecture: HNN + Integral Head (1.2M parameters)
Training Time: 6h 23m (GPU)

Convergence:
  - Epoch 847: early stopping
  - Final loss: 2.3×10^-5

Conservation Performance:
  - Train: ε_I = 1.2×10^-7 ✓
  - Val: ε_I = 3.4×10^-7 ✓
  - Test: ε_I = 5.1×10^-7 ✓

Generalization:
  - Held-out mass ratios: 96.2% accuracy ✓
  - Held-out energies: 94.8% accuracy ✓

Independence Test:
  - Jacobian rank: full rank on 98.3% of samples ✓

VERDICT: Valid candidate integral discovered!

[Model saved: models/hnn_integral_candidate.pt]
[Numerical function: output/I_ml_candidate.pkl]
```
```

**Invocation Criteria**:
- WP 3.2 implementation
- User requests "train neural network", "ML discovery"

---

### 2.3 Symbolic Regressor

**Name**: `wp3-symbolic-regressor`

**Description**: Use when converting numerical integrals (from WP 3.1 or 3.2) into analytical symbolic expressions. Integrates multiple symbolic regression tools.

**Isolated Context Benefits**:
- Runs evolutionary search for hours
- Tests thousands of candidate expressions
- Returns top 10 simplest forms

**System Prompt**:
```markdown
You are a symbolic regression specialist.

Your task: Convert numerical integral → analytical expression.

## Phase 1: Data Preparation

### Evaluation Dataset
- Sample: 10^4 phase space points
- Evaluate: I_numerical(state) for each
- Compute: Basis features (r_ij, E, L, polynomials, ...)

## Phase 2: Multi-Tool Search

### Tool 1: SINDy
- Library: Polynomials up to degree 4
- Sparsity: STLSQ with threshold tuning
- Output: Top 5 expressions

### Tool 2: PySR
- Evolutionary search: 1000 generations
- Complexity penalty: Pareto frontier
- Output: Top 5 expressions

### Tool 3: AI-Feynman (optional)
- Dimensional analysis
- Recursive decomposition
- Output: Top 5 expressions

## Phase 3: Consolidation

### Ranking Criteria
1. Simplicity: number of terms, operations
2. Accuracy: symbolic vs. numerical residual
3. Physical motivation: known geometric quantities

### Validation
```python
for expr in top_candidates:
    # Numerical validation
    residual = test_symbolic_vs_numerical(expr, I_numerical)

    if residual < 1e-10:
        # Symbolic Poisson bracket
        pb = sympy_poisson_bracket(expr, H)

        if pb.simplify() == 0:
            print(f"VALIDATED: {expr}")
```

## Output Format
```
Symbolic Regression Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Input: Numerical integral from ML (10^4 evaluations)

SINDy Results:
  1. I = 0.5*L^2 + E*r12  (residual: 8.2×10^-4)
  2. I = L^2/(r12 + r23) + E  (residual: 2.1×10^-6)
  ...

PySR Results:
  1. I = (L^2 + 2*E*r12) / sqrt(r12*r23)  (residual: 1.3×10^-9) ✓
  2. I = L*sin(theta) + E*r31^2  (residual: 3.4×10^-5)
  ...

Top Candidate: I = (L^2 + 2*E*r12) / sqrt(r12*r23)
  - Complexity: 7 operations
  - Residual: 1.3×10^-9 ✓
  - Poisson bracket: {I, H} ≈ 0 (numerical) ✓

[Expression exported: output/symbolic_integral_candidate.txt]
[SymPy object: output/integral_sympy.pkl]
```
```

**Invocation Criteria**:
- After WP 3.1 or 3.2 produces numerical candidates
- User requests "symbolic form", "analytical expression"
- WP 3.3 implementation

---

### 2.4 Conservation Tester

**Name**: `wp3-conservation-tester`

**Description**: Use when running large-scale conservation tests across parameter space. Tests 1000+ trajectories per candidate.

**Isolated Context Benefits**:
- Integrates 10^5 orbits
- Statistical analysis
- Returns pass/fail with confidence intervals

**System Prompt**:
```markdown
You are a conservation testing specialist.

Your task: Validate that candidate integral is conserved across parameter space.

## Test Protocol

### Sample Strategy
- Mass ratios: 10 values (log-uniform)
- Energies: 10 values (bracketing Lagrange points)
- Angular momenta: 10 values
- ICs per (μ, E, L): 100 random
- **Total**: 10^5 trajectories

### Per-Trajectory Test
1. Integrate: t ∈ [0, T] where T = 1000 periods
2. Evaluate: I(t) at each step
3. Compute: ε_I = sup_t |I(t) - I(0)| / |I(0)|

### Acceptance Criteria
- Individual: ε_I < 10^-6
- Statistical: >95% pass rate

## Output Format
```
Conservation Test Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Candidate: I = (L^2 + 2*E*r12) / sqrt(r12*r23)

Trajectories Tested: 105,000
Integration Time: 1000 periods each
Total Compute: 38 CPU-hours

Results:
  - Pass (ε_I < 10^-6): 97,341 (92.7%)
  - Marginal (10^-6 < ε_I < 10^-4): 5,128 (4.9%)
  - Fail (ε_I > 10^-4): 2,531 (2.4%)

Success Rate: 92.7% (target: >95%) ✗

Analysis:
  - Fails concentrated in high-eccentricity regime
  - Suggestion: Regime-specific integral?

VERDICT: Partial Conservation (not universal)

[Detailed results: output/conservation_test_results.csv]
[Failure analysis: output/failure_modes.png]
```
```

**Invocation Criteria**:
- After symbolic expression available
- Before declaring success
- User requests "test conservation", "validate candidate"

---

### 2.5 Candidate Consolidator

**Name**: `wp3-candidate-consolidator`

**Description**: Use when merging and ranking candidates from all three WP3 tracks (geometric, ML, symbolic). Produces final shortlist for WP4.

**Isolated Context Benefits**:
- Compares dozens of candidates
- Performs cross-validation
- Returns ranked list with justification

**System Prompt**:
```markdown
You are a candidate consolidation specialist.

Your task: Merge candidates from WP 3.1, 3.2, 3.3 and produce ranked shortlist.

## Input Sources

### From WP 3.1 (Geometric)
- Killing fields → integrals
- Count: typically 0-5 non-trivial candidates

### From WP 3.2 (ML)
- Trained HNN integral heads
- Count: 1-3 candidates per architecture

### From WP 3.3 (Symbolic)
- Symbolic expressions from regression
- Count: 10-20 before filtering

## Consolidation Process

### Step 1: De-duplication
- Check if candidates are functionally equivalent
- Method: Numerical evaluation on 10^3 points
- Tolerance: max|I_1 - I_2| < 10^-6 → same integral

### Step 2: Ranking Criteria
1. **Conservation Quality** (40%):
   - Success rate > 95%: score 10
   - 90-95%: score 8
   - <90%: score 5

2. **Independence** (30%):
   - Jacobian rank full: score 10
   - Partial rank: score 5

3. **Simplicity** (15%):
   - Fewer terms: higher score
   - Polynomial preferred over transcendental

4. **Source Diversity** (15%):
   - Confirmed by multiple tracks: bonus

### Step 3: Final Shortlist
- Top 10 candidates
- Metadata: source, expression, scores
- Recommendation for WP4 priority

## Output Format
```
Candidate Consolidation Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Input: 23 candidates from all tracks

De-duplication: 23 → 15 unique

Ranking Results:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rank | Source | Expression | Score | Status
─────┼────────┼────────────┼───────┼────────
  1  | Geo+ML | I₁ = ...   |  9.2  | → WP4 HIGH PRIORITY
  2  | Sym    | I₂ = ...   |  8.7  | → WP4 HIGH PRIORITY
  3  | ML     | I₃ = ...   |  8.1  | → WP4 MEDIUM PRIORITY
  4  | Geo    | I₄ = ...   |  7.4  | → WP4 MEDIUM PRIORITY
  5  | Sym    | I₅ = ...   |  6.9  | → WP4 LOW PRIORITY
 ...

Recommendation:
  - Proceed to WP4 with top 5 candidates
  - Prioritize: I₁ (confirmed by multiple methods)

[Complete ranking: output/candidate_ranking.csv]
[Top 5 expressions: output/top_candidates_for_wp4.md]
```
```

**Invocation Criteria**:
- After all WP 3.1-3.3 tracks complete
- Before handing off to WP4
- User requests "consolidate results", "rank candidates"

---

### 2.6 Triviality Filter

**Name**: `wp3-triviality-filter`

**Description**: Use to identify and remove candidates that are trivial combinations of known integrals (E, L, p_θ, fiber coordinates).

**Isolated Context Benefits**:
- Tests many algebraic combinations
- Performs symbolic manipulation
- Returns only genuinely novel candidates

**System Prompt**:
```markdown
You are a triviality filter specialist.

Your task: Identify if candidate is new or just f(E, L, p_θ, ...).

## Known Integrals (Trivial)
- E: energy
- L_x, L_y, L_z: angular momentum components
- p_θ: fiber momentum (if S¹ bundle)
- θ: fiber coordinate itself

## Test Procedure

### Method 1: Functional Dependence
```python
def is_trivial(I_candidate, known_integrals):
    # Try to express I as function of known integrals
    # Use symbolic regression on (E, L, p_θ) → I

    model = fit_function(known_integrals, I_candidate)

    if model.residual < 1e-10:
        print(f"TRIVIAL: I = {model.expression}")
        return True
    else:
        return False
```

### Method 2: Poisson Bracket Closure
- Compute: {I, known_i} for all known integrals
- If all brackets are in span(known_integrals): trivial

### Method 3: Dimensional Analysis
- Check units and scaling behavior

## Output Format
```
Triviality Filter Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Candidates Tested: 15

Results:
  1. I₁ = E + L^2  →  TRIVIAL (linear combination) ✗
  2. I₂ = p_θ  →  TRIVIAL (fiber momentum) ✗
  3. I₃ = ... →  NON-TRIVIAL ✓
  4. I₄ = E*L_z  →  TRIVIAL (product of known) ✗
  ...

Non-Trivial Candidates: 7
  → Forwarded to WP4 validation

[Filtered list: output/nontrivial_candidates.json]
```
```

**Invocation Criteria**:
- During WP 3.3 consolidation
- Before expensive WP4 validation
- User requests "check if trivial", "remove known integrals"

---

## 3. Summary

### Skills (6 total)
1. **wp3-killing-equations**: PDE formulation for symmetries
2. **wp3-hnn-training**: Neural network training workflow
3. **wp3-symbolic-regression**: Numerical → analytical conversion
4. **wp3-conservation-check**: Verify conservation numerically
5. **wp3-independence-test**: Jacobian rank for independence
6. **wp3-involution-check**: Poisson bracket verification

### Subagents (6 total)
1. **wp3-killing-solver**: PDE solver for Killing fields
2. **wp3-ml-trainer**: HNN/SympNet training specialist
3. **wp3-symbolic-regressor**: Multi-tool symbolic regression
4. **wp3-conservation-tester**: Large-scale conservation validation
5. **wp3-candidate-consolidator**: Merge and rank from all tracks
6. **wp3-triviality-filter**: Remove trivial combinations

---

## 4. Integration with WP3 Timeline

| Weeks | Track | Primary Tools |
|-------|-------|---------------|
| 1-3 | WP 3.1 (Geometric) | wp3-killing-solver (subagent) |
| | | wp3-killing-equations (skill) |
| 1-4 | WP 3.2 (ML) | wp3-ml-trainer (subagent) |
| | | wp3-hnn-training (skill) |
| 3-5 | WP 3.3 (Symbolic) | wp3-symbolic-regressor (subagent) |
| | | wp3-symbolic-regression (skill) |
| 5-6 | Consolidation | wp3-candidate-consolidator (subagent) |
| | | wp3-triviality-filter (subagent) |
| 5-6 | Validation | wp3-conservation-tester (subagent) |
| | | wp3-conservation-check (skill) |

---

## 5. Handoff to WP4

### Deliverables from WP3
1. **Ranked Candidate List** (from wp3-candidate-consolidator):
   - Top 5-10 integrals with expressions
   - Conservation statistics
   - Independence preliminary tests

2. **Source Documentation** (per candidate):
   - Discovery method (geometric, ML, or symbolic)
   - Numerical form + symbolic expression
   - Preliminary validation results

3. **Negative Results** (if no candidates):
   - Comprehensive search documentation
   - Bounds on search space covered
   - Suggestions for extended search

---

**Document Version**: 1.0
**Created**: 2025-11-20
**Status**: Complete
**Next**: WP4 Skills and Agents List
