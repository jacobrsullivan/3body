# WP 3.3: Symbolic Regression and Consolidation
## Complete Implementation Summary

**Duration**: 10-12 days
**Approach**: Data-driven symbolic discovery
**Goal**: Convert numerical candidates into analytical expressions

---

## Overview

WP 3.3 serves as the **consolidation phase** for WP3, taking numerical candidate integrals discovered by geometric methods (WP 3.1) and machine learning (WP 3.2) and converting them into concise analytical expressions suitable for rigorous symbolic validation in WP4.

### Strategic Role

**Bridge Between Discovery and Validation**:
- **Input**: Numerical functions (from WP 3.1 and 3.2)
- **Process**: Symbolic regression with physics-informed basis
- **Output**: Analytical expressions ready for Poisson bracket tests (WP 4.1)

**Why This Matters**: WP4 validation requires symbolic expressions for:
- Computing $\{I, H\}$ analytically
- Verifying involution $\{I_1, I_2\}$
- Checking functional independence (Jacobian rank)

---

## Three-Task Pipeline

```
Task 3.3.1: Symbolic Regression Pipeline (4-5 days)
    ↓ SINDy/PySR implementation
Task 3.3.2: Basis Function Optimization (3-4 days)
    ↓ Physics-informed search space
Task 3.3.3: Candidate Ranking & Consolidation (3 days)
    ↓ Final list of analytical I~ candidates
```

---

## Task Summaries

### Task 3.3.1: Symbolic Regression Pipeline

**Objective**: Implement and integrate symbolic regression tools.

**Tool Options**:

#### 1. SINDy (Sparse Identification of Nonlinear Dynamics)

**Approach**: Sparse regression to find simplest expression.

**Core Algorithm**:
1. Evaluate candidate integral on grid: $I_{\text{num}}(q_i, p_i)$ for $i=1,\ldots,N$
2. Construct library of basis functions: $\Theta = [\phi_1, \phi_2, \ldots, \phi_M]$
3. Solve sparse regression:
   $$
   \min_{\xi} \|I_{\text{num}} - \Theta \xi\|_2^2 + \lambda \|\xi\|_1
   $$
4. Output: $I_{\text{sym}} = \sum_{j} \xi_j \phi_j(q, p)$

**Advantages**:
- Promotes sparsity (few terms)
- Fast and interpretable
- Good for polynomial expressions

**Limitations**:
- Requires manual basis function library
- May miss non-polynomial forms

---

#### 2. PySR (Python Symbolic Regression)

**Approach**: Evolutionary algorithm search over expression trees.

**Core Algorithm**:
1. Start with random expression trees
2. Mutate and recombine (genetic programming)
3. Fitness function: $\text{MSE} + \lambda \cdot \text{complexity}$
4. Evolve for many generations
5. Return Pareto front (accuracy vs. complexity)

**Advantages**:
- Discovers complex functional forms (transcendental, nested, etc.)
- No predefined basis needed
- Finds multiple candidate expressions

**Limitations**:
- Computationally expensive (hours to days)
- May converge to local optima
- Requires careful complexity penalty tuning

---

#### 3. AI-Feynman

**Approach**: Physics-inspired hierarchical symbolic regression.

**Key Ideas**:
- Exploit symmetries (dimensional analysis, translational invariance)
- Decompose complex expressions into simpler sub-expressions
- Use neural networks to guide search

**Advantages**:
- Best for physics problems
- Incorporates domain knowledge

**Limitations**:
- Requires significant setup
- Less mature than SINDy/PySR

---

**Recommended Strategy**: Use **SINDy** first (fast), then **PySR** for refinement.

**Implementation**:

```python
# src/python/symbolic/regression_pipeline.py

import pysindy as ps
from pysr import PySRRegressor

def symbolic_regression_sindy(
    I_numerical: Callable,
    sample_points: np.ndarray,
    basis_functions: List[Callable],
    sparsity_param: float = 0.01
) -> Tuple[str, Dict]:
    """
    Symbolic regression using SINDy.

    Args:
        I_numerical: Numerical function to fit
        sample_points: Evaluation points (N, 2n) in phase space
        basis_functions: Library of basis functions
        sparsity_param: L1 regularization strength

    Returns:
        expression: Symbolic expression string
        coefficients: Dictionary of fitted coefficients
    """
    # Evaluate numerical function
    I_values = np.array([I_numerical(z) for z in sample_points])

    # Construct feature library
    library = ps.FeatureLibrary(
        functions=basis_functions,
        function_names=[f.__name__ for f in basis_functions]
    )

    # Fit sparse model
    model = ps.SINDy(
        feature_library=library,
        optimizer=ps.STLSQ(threshold=sparsity_param)
    )
    model.fit(sample_points, I_values)

    # Extract symbolic expression
    expression = model.equations_[0]
    coefficients = model.coefficients_[0]

    return expression, coefficients


def symbolic_regression_pysr(
    I_numerical: Callable,
    sample_points: np.ndarray,
    niterations: int = 100,
    populations: int = 20
) -> pd.DataFrame:
    """
    Symbolic regression using PySR (genetic programming).

    Returns:
        pareto_front: DataFrame with expressions and their complexity/error
    """
    I_values = np.array([I_numerical(z) for z in sample_points])

    model = PySRRegressor(
        niterations=niterations,
        populations=populations,
        binary_operators=["+", "-", "*", "/", "^"],
        unary_operators=["sin", "cos", "exp", "log", "sqrt"],
        constraints={
            "^": (-1, 3),  # Limit power to cubic
            "/": (-1, 1),  # Avoid division by small numbers
        },
        loss="L2DistLoss()",
        maxsize=20,  # Maximum expression complexity
    )

    model.fit(sample_points, I_values)

    # Return Pareto front (multiple candidate expressions)
    return model.equations_
```

**Deliverables**:
- [ ] `regression_pipeline.py` - SINDy and PySR interfaces
- [ ] `expression_simplification.py` - SymPy post-processing
- [ ] `numerical_validation.py` - Check symbolic vs. numerical residual
- [ ] Tutorial notebook: "Symbolic Regression for Integrals"

---

### Task 3.3.2: Basis Function Optimization

**Objective**: Construct physics-informed basis function library for SINDy.

**Basis Function Design Principles**:

1. **Geometric Quantities** (coordinate-independent):
   - Distances: $r_{12}, r_{23}, r_{31}$
   - Dot products: $\mathbf{r}_{12} \cdot \mathbf{v}_{12}$ (radial velocities)
   - Cross products: $\mathbf{r}_{12} \times \mathbf{v}_{12}$ (angular momentum components)

2. **Conserved Quantity Polynomials**:
   - Energy polynomials: $E, E^2$ (powers of Hamiltonian)
   - Angular momentum polynomials: $L, L^2, \mathbf{L} \cdot \mathbf{r}$
   - Combinations: $EL, E^2L$, etc.

3. **Shape Space Coordinates**:
   - For S¹ bundle: $(s_1, s_2, s_3, \theta)$ and conjugate momenta
   - Low-degree polynomials: $s_1^2, s_1 s_2, p_{s_1} p_{s_2}$, etc.

4. **KS Spinor Coordinates** (if using KS lift):
   - Spinor components: $u_{12}^{(i)}, u_{23}^{(i)}, u_{31}^{(i)}$ for $i=0,1,2,3$
   - Bilinear combinations: $\mathbf{u}_{12} \cdot \mathbf{u}_{23}$

5. **Transcendental Functions** (for PySR):
   - Allow: $\sin, \cos$ (periodic motion), $\exp, \log$ (scale transformations)
   - Restrict: Avoid $\tan$ (singularities), high powers (overfitting)

**Hierarchical Basis Strategy**:

```
Level 1 (Linear): {1, q_i, p_i}  (10-20 functions)
    ↓ If no fit found
Level 2 (Quadratic): {q_i q_j, q_i p_j, p_i p_j}  (50-100 functions)
    ↓ If no fit found
Level 3 (Cubic): {q_i q_j q_k, ...}  (200-500 functions)
    ↓ If no fit found
Level 4 (Transcendental): {sin(q_i), sqrt(q_i^2 + q_j^2), ...}
```

**Implementation**:

```python
# src/python/symbolic/basis_functions.py

def construct_basis_library(
    coordinate_system: str,  # 's1', 'ks', or 'cartesian'
    max_degree: int = 3,
    include_transcendental: bool = False
) -> List[Tuple[Callable, str]]:
    """
    Construct physics-informed basis function library.

    Returns:
        basis: List of (function, name) tuples
    """
    basis = []

    # Level 1: Linear
    dim = get_phase_space_dim(coordinate_system)
    for i in range(dim):
        basis.append((lambda z, i=i: z[i], f"z{i}"))

    # Level 2: Quadratic
    if max_degree >= 2:
        for i in range(dim):
            for j in range(i, dim):
                basis.append((lambda z, i=i, j=j: z[i]*z[j], f"z{i}*z{j}"))

    # Level 3: Cubic
    if max_degree >= 3:
        # Only include physically motivated cubics (avoid explosion)
        # E.g., r^3, r·v^2, etc.
        pass

    # Transcendental
    if include_transcendental:
        for i in range(dim):
            basis.append((lambda z, i=i: np.sin(z[i]), f"sin(z{i})"))
            basis.append((lambda z, i=i: np.cos(z[i]), f"cos(z{i})"))

    return basis


def geometric_basis_functions(masses: np.ndarray) -> List[Tuple[Callable, str]]:
    """
    Basis functions using geometric invariants (distances, angles, etc.).

    Examples:
        - r12, r23, r31 (distances)
        - r12·v12 (radial velocity)
        - |r12 × v12| (angular momentum magnitude per pair)
    """
    basis = []

    # Distances
    basis.append((lambda z: compute_r12(z, masses), "r12"))
    basis.append((lambda z: compute_r23(z, masses), "r23"))
    basis.append((lambda z: compute_r31(z, masses), "r31"))

    # Dot products (radial velocities)
    basis.append((lambda z: radial_velocity(z, masses, pair=(1,2)), "r12_dot_v12"))

    # Angular momentum components
    basis.append((lambda z: angular_momentum_magnitude(z, masses), "L_mag"))

    return basis
```

**Deliverables**:
- [ ] `basis_functions.py` - Hierarchical basis construction
- [ ] `geometric_invariants.py` - Coordinate-independent quantities
- [ ] Basis validation: Test on known integrals (E, L)

---

### Task 3.3.3: Candidate Ranking and Consolidation

**Objective**: Combine results from WP 3.1 and 3.2, rank by promise, output top candidates.

**Consolidation Strategy**:

1. **Collect All Candidates**:
   - From WP 3.1: Killing fields → Integrals $I_K$
   - From WP 3.2: ML predictions → Numerical functions $I_\phi$
   - From WP 3.3.1-3.3.2: Symbolic regression → Analytical expressions $I_{\text{sym}}$

2. **Unify Representation**:
   - Convert all to symbolic SymPy expressions
   - Simplify using `sympy.simplify()`, `sympy.factor()`
   - Standardize notation (consistent variable names)

3. **Rank by Criteria**:

   **Primary Criteria**:
   - **Conservation Accuracy**: $|\{I, H\}| < \epsilon$ (numerically)
   - **Simplicity**: Number of terms, maximum degree
   - **Functional Independence**: Jacobian rank test

   **Scoring Function**:
   $$
   \text{Score}(I) = \alpha \cdot \log(\epsilon_{\text{conservation}}) + \beta \cdot \text{complexity} + \gamma \cdot (1 - \text{independence})
   $$

   (Lower score is better)

4. **Filter Duplicates**:
   - Check if candidates are equivalent up to constants
   - Remove trivial combinations (e.g., $I_1 + I_2$ if both $I_1, I_2$ already found)

5. **Output Top 10 Candidates**:
   - Ranked table with expressions, scores, metadata
   - Visualizations (conservation plots, phase space level sets)

**Implementation**:

```python
# src/python/symbolic/candidate_ranking.py

@dataclass
class CandidateIntegral:
    """Candidate conserved quantity."""
    expression: sp.Expr  # SymPy expression
    source: str  # 'killing_field', 'ml', 'symbolic_regression'
    conservation_error: float  # Numerical test result
    complexity: int  # Number of operations
    independent: bool  # Functionally independent of E, L, p_θ
    metadata: Dict  # Additional info


def consolidate_and_rank(
    candidates: List[CandidateIntegral],
    weights: Dict[str, float] = {'conservation': 10.0, 'complexity': 1.0, 'independence': 100.0}
) -> List[CandidateIntegral]:
    """
    Rank and filter candidate integrals.

    Args:
        candidates: List of all discovered candidates
        weights: Scoring function weights

    Returns:
        ranked_candidates: Top candidates sorted by score
    """
    # Remove duplicates
    unique_candidates = remove_duplicates(candidates)

    # Compute scores
    for cand in unique_candidates:
        cand.score = compute_score(cand, weights)

    # Sort by score (lower is better)
    ranked = sorted(unique_candidates, key=lambda c: c.score)

    return ranked
```

**Deliverable**:

**Final Output: Candidate Integral Report**

| Rank | Expression | Source | Conservation Error | Complexity | Independent | Score |
|------|-----------|--------|-------------------|------------|-------------|-------|
| 1 | $p_\theta$ | Killing (S¹) | $3.2 \times 10^{-14}$ | 1 | Yes | 0.12 |
| 2 | $r_{12}^2 + r_{23}^2 + L^2$ | ML + SymReg | $1.5 \times 10^{-7}$ | 5 | Yes (TBC) | 1.83 |
| 3 | $E L \cos(\theta)$ | Symbolic Reg | $8.4 \times 10^{-6}$ | 4 | No | 4.21 |
| ... | ... | ... | ... | ... | ... | ... |

**Deliverables**:
- [ ] `candidate_ranking.py` - Scoring and filtering
- [ ] `deduplication.py` - Remove equivalent expressions
- [ ] `visualization.py` - Level set plots for top candidates
- [ ] **Final Report**: "Top 10 Candidate Conserved Quantities" (PDF)

---

## Validation and Quality Control

### V1. Symbolic-Numerical Agreement

**Test**: Does symbolic expression match numerical function?

```python
def validate_symbolic_fit(
    I_symbolic: sp.Expr,
    I_numerical: Callable,
    test_points: np.ndarray,
    tolerance: float = 1e-10
) -> bool:
    """
    Verify symbolic expression reproduces numerical function.
    """
    I_sym_lambdified = sp.lambdify(symbols, I_symbolic, 'numpy')
    residuals = [abs(I_sym_lambdified(*z) - I_numerical(z)) for z in test_points]
    max_residual = max(residuals)
    return max_residual < tolerance
```

**Acceptance**: Residual $< 10^{-10}$ on 10^4 random test points.

---

### V2. Conservation Verification

**Test**: Integrate dynamics and monitor $\Delta I / I$.

```python
def verify_conservation_long_time(
    I_symbolic: sp.Expr,
    initial_state: np.ndarray,
    t_span: float = 100.0,
    masses: np.ndarray
) -> float:
    """
    Integrate trajectory and measure conservation of I.

    Returns:
        drift: max|ΔI/I| over trajectory
    """
    trajectory = integrate_hamiltonian(initial_state, t_span, masses)
    I_values = [evaluate_symbolic(I_symbolic, z) for z in trajectory]
    drift = (max(I_values) - min(I_values)) / abs(I_values[0])
    return drift
```

**Acceptance**: Drift $< 10^{-5}$ over 100 orbital periods.

---

### V3. Simplicity and Interpretability

**Manual Review**:
- Is the expression physically interpretable?
- Does it reduce to known forms in limits (e.g., Kepler, equal masses)?
- Can it be connected to geometric structures (Killing fields)?

---

## Expected Outcomes

### Best Case: Clean Analytical Expressions
- Top candidates are simple (low-degree polynomials or rationals)
- Conservation verified numerically to $< 10^{-10}$
- Clear physical interpretation
- → Ready for WP4 symbolic validation

### Moderate Case: Complex but Valid Expressions
- Expressions involve transcendentals or many terms
- Conservation holds but expressions are not "elegant"
- → Proceed to WP4 with numerical assistance

### Negative Case: No Simple Symbolic Form
- Regression does not converge
- Best fits still have residuals $> 10^{-6}$
- → Proceed to WP4 with numerical candidates only
- → Poisson brackets computed numerically

---

## Computational Requirements

**Hardware**:
- CPU-based (symbolic regression is not GPU-accelerated)
- 16+ cores recommended (PySR parallelization)
- 32-64 GB RAM

**Time**:
- SINDy: Minutes to hours
- PySR: Hours to days (depending on search space)
- Simplification: Minutes

**Storage**:
- Expression databases: ~100 MB
- Evaluation data: ~1 GB

---

## Integration Summary

### Inputs
- **From WP 3.1**: Numerical Killing fields $K(q)$
- **From WP 3.2**: Trained neural network $I_\phi(q, p)$
- **Evaluation Data**: High-precision trajectories

### Outputs
- **To WP 4.1**: Symbolic expressions $I_{\text{sym}}$ for Poisson bracket tests
- **To WP 4.3**: Numerical evaluation functions for Monte Carlo validation

---

## Deliverables Summary

### Code (3 main modules)
- [ ] `regression_pipeline.py` - SINDy/PySR integration
- [ ] `basis_functions.py` - Physics-informed basis
- [ ] `candidate_ranking.py` - Consolidation and scoring

### Documentation
- [ ] Technical report: "Symbolic Regression Results" (15 pages)
- [ ] Top 10 candidate table (with expressions, scores)
- [ ] Tutorial: "From Numerical to Symbolic Integrals"

### Scientific Outputs
- [ ] Ranked list of analytical candidate integrals
- [ ] Validation plots (symbolic vs. numerical)
- [ ] Negative result documentation (if no simple forms exist)

---

## Success Criteria

**Minimum Success**:
- [ ] Regression pipeline functional
- [ ] At least one candidate converted to symbolic form
- [ ] Symbolic-numerical residual documented

**Target Success**:
- [ ] Top 3-5 candidates with residual $< 10^{-10}$
- [ ] Conservation verified on test trajectories
- [ ] Expressions simple enough for analytical Poisson brackets

**Stretch Success**:
- [ ] Analytical expression for primary integral (if exists)
- [ ] Physical interpretation clear (geometric or dynamical)
- [ ] Publication-ready figures and tables

---

## Timeline

**Days 1-2**: Task 3.3.1 (SINDy setup, initial fits)
**Days 3-5**: Task 3.3.1 (PySR runs, long searches)
**Days 6-8**: Task 3.3.2 (Basis optimization, refinement)
**Days 9-10**: Task 3.3.3 (Consolidation, ranking, report)

**Total**: 10 days (can extend to 12 if PySR requires more iterations)

---

## References

1. **SINDy**:
   - Brunton et al., "Discovering governing equations from data" (2016)
   - Champion et al., "Data-driven discovery of coordinates" (2019)

2. **PySR**:
   - Cranmer, "Interpretable Machine Learning for Science with PySR" (2023)
   - https://github.com/MilesCranmer/PySR

3. **AI-Feynman**:
   - Udrescu & Tegmark, "AI Feynman: A physics-inspired method" (2020)

4. **Symbolic Regression Review**:
   - Schmidt & Lipson, "Distilling free-form natural laws" (2009)
   - La Cava et al., "Contemporary symbolic regression methods" (2021)

---

**Document Version**: 1.0
**Last Updated**: 2025-11-14
**Status**: Complete Planning - Ready for Implementation
