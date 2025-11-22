# AMENDED WP 3.3: Symbolic Regression for Complex Integrals
## Enhanced Search Basis and Non-Standard Function Discovery

**Duration**: 12-15 days (extended for complex function search)
**Approach**: Physics-informed symbolic discovery with enriched basis
**Goal**: Discover potentially non-standard analytical expressions for conserved quantities

**Amendment Date**: 2025-11-20
**Amendment Rationale**: The hidden integrals, if they exist, are likely complex and non-polynomial. This amendment expands the search basis to include physically motivated non-standard functions.

---

## Overview

WP 3.3 serves as the **consolidation phase** for WP3, taking numerical candidate integrals discovered by geometric methods (WP 3.1) and machine learning (WP 3.2) and converting them into analytical expressions. **This amended version recognizes that the three-body problem's hidden integrals may involve non-standard functions.**

### Key Insight: Complex Integrals in Hamiltonian Systems

**Historical Precedent**:
- **Kepler Problem**: Conserved Runge-Lenz vector involves $\mathbf{A} = \mathbf{p} \times \mathbf{L} - \frac{\mathbf{r}}{r}$ (cross products + reciprocal distances)
- **Rigid Body Motion**: Poinsot ellipsoid involves elliptic integrals
- **Kowalevskaya Top**: Integrals involve theta functions and elliptic functions
- **KAM Theory**: Integrable systems often have action-angle coordinates expressible via elliptic/hyperelliptic integrals

**Implication for Three-Body Problem**: If a fourth integral exists beyond E, L, p_θ, it may involve:
1. **Spinor/Quaternion components** (from KS regularization's intrinsic structure)
2. **Elliptic functions** (Weierstrass ℘, Jacobi sn/cn/dn)
3. **Modular forms** or theta functions
4. **Non-algebraic combinations** of distances and velocities

---

## Enhanced Three-Task Pipeline

```
Task 3.3.1: Adaptive Symbolic Regression Pipeline (5-6 days)
    ↓ SINDy → PySR → Custom genetic operators
Task 3.3.2: Enriched Basis Function Library (4-5 days)
    ↓ Spinor components, elliptic functions, modular forms
Task 3.3.3: Multi-Stage Candidate Ranking (3-4 days)
    ↓ Validate against trajectory data, check conservation
```

---

## Task 3.3.1: Adaptive Symbolic Regression (AMENDED)

### Extended Regression Methods

#### 1. SINDy (Baseline)
- **Use**: Polynomial and simple rational functions
- **Basis**: Expanded to include $r^{-1}, r^{-2}$ (gravitational potentials)
- **Expected Success Rate**: 30-40% (if integral is polynomial)

#### 2. PySR with Custom Operators (Primary)
- **Expanded Operator Set**:
  ```python
  binary_operators = ["+", "-", "*", "/", "^", "atan2"]
  unary_operators = [
      "sin", "cos", "tan",           # Trig
      "sinh", "cosh", "tanh",        # Hyperbolic
      "exp", "log", "sqrt",          # Elementary
      "reciprocal",                  # 1/x for gravitational terms
      "square", "cube",              # Powers
  ]
  ```

- **Constraints**:
  - Limit nesting depth to avoid combinatorial explosion
  - Prioritize physically motivated combinations
  - Use parsimony heavily (complexity penalty = 0.1)

#### 3. Elliptic Function Search (Novel)

**Rationale**: Many integrable Hamiltonian systems have integrals expressible via elliptic functions.

**Implementation Strategy**:
```python
# Stage 1: Identify periodicity structure
# - Compute autocorrelation of I(t) along trajectories
# - If periodic with two incommensurable periods → potential elliptic function

# Stage 2: Fit to elliptic function templates
elliptic_templates = [
    lambda z, k: elliptic_sn(f(z), k),  # Jacobi sn
    lambda z, k: elliptic_cn(f(z), k),  # Jacobi cn
    lambda z, k: elliptic_dn(f(z), k),  # Jacobi dn
    lambda z, omega: weierstrass_p(f(z), omega),  # Weierstrass ℘
]

# Stage 3: Use numerical optimization to find:
# - Argument function f(q, p)
# - Modular parameter k or lattice ω
```

**Deliverable**: `elliptic_regression.py` module

**Validation**: Test on Kowalevskaya top (known elliptic integral)

---

#### 4. Spinor Component Analysis (KS-Specific)

**Motivation**: The KS transformation introduces spinor coordinates $\mathbf{u} = (u_0, u_1, u_2, u_3)$ for each pair. These are not just change-of-variables but carry geometric meaning.

**Hypothesis**: Hidden integrals may be polynomial in spinor components even if non-polynomial in Cartesian coordinates.

**Implementation**:
```python
def construct_ks_spinor_basis(max_degree=3):
    """
    Basis functions using KS spinor coordinates.

    For three pairs (12, 23, 31), we have spinors:
        u_12 = (u12_0, u12_1, u12_2, u12_3)
        u_23 = (u23_0, u23_1, u23_2, u23_3)
        u_31 = (u31_0, u31_1, u31_2, u31_3)

    Basis includes:
        - Individual components: u12_0, u12_1, ...
        - Bilinear products: u12 · u23, u12 · u31, u23 · u31
        - Spinor norms: |u12|^2, |u23|^2, |u31|^2
        - Mixed products: (u12 · u23)(u23 · u31)
    """
    basis = []

    # Level 1: Individual spinor components (12 functions)
    for pair in ['12', '23', '31']:
        for i in range(4):
            basis.append((
                lambda z, pair=pair, i=i: get_spinor_component(z, pair, i),
                f"u{pair}_{i}"
            ))

    # Level 2: Bilinear forms (6 functions)
    basis.extend([
        (lambda z: np.dot(get_spinor(z, '12'), get_spinor(z, '23')), "u12_dot_u23"),
        (lambda z: np.dot(get_spinor(z, '12'), get_spinor(z, '31')), "u12_dot_u31"),
        (lambda z: np.dot(get_spinor(z, '23'), get_spinor(z, '31')), "u23_dot_u31"),
    ])

    # Level 3: Spinor norms squared (3 functions)
    for pair in ['12', '23', '31']:
        basis.append((
            lambda z, p=pair: np.linalg.norm(get_spinor(z, p))**2,
            f"|u{p}|^2"
        ))

    # Level 4: Higher-order combinations (selective)
    if max_degree >= 3:
        # Spinor triple product: (u12 · u23)(u23 · u31)(u31 · u12)
        basis.append((
            lambda z: (
                np.dot(get_spinor(z, '12'), get_spinor(z, '23')) *
                np.dot(get_spinor(z, '23'), get_spinor(z, '31')) *
                np.dot(get_spinor(z, '31'), get_spinor(z, '12'))
            ),
            "spinor_triple_product"
        ))

    return basis
```

**Expected Outcome**: If integral is "natural" in KS coordinates, regression should succeed with lower complexity.

---

### Enhanced Validation Framework

#### V1. Multi-Scale Conservation Test

**Issue**: Complex integrals may conserve exactly but numerical evaluation introduces errors.

**Solution**: Test conservation at multiple time scales
```python
def multi_scale_conservation_test(I_symbolic, trajectory, dt_values):
    """
    Test if I is conserved at multiple time scales.

    Args:
        I_symbolic: Candidate integral
        trajectory: Long trajectory (10^4 to 10^6 points)
        dt_values: [0.01, 0.1, 1.0, 10.0] (short to long)

    Returns:
        conservation_errors: Dict mapping dt -> max|ΔI/I|
    """
    errors = {}
    for dt in dt_values:
        subsampled = trajectory[::int(dt/trajectory.dt)]
        I_values = [I_symbolic(state) for state in subsampled]
        drift = (max(I_values) - min(I_values)) / abs(I_values[0])
        errors[dt] = drift

    return errors
```

#### V2. Functional Form Identification

**After** finding symbolic expression, identify its mathematical class:

```python
def identify_function_type(expr):
    """
    Classify symbolic expression by function type.

    Returns:
        type: 'polynomial', 'rational', 'algebraic',
              'trigonometric', 'elliptic', 'unknown'
    """
    # Check for algebraic expressions (roots of polynomials)
    if contains_sqrt_or_roots(expr):
        return 'algebraic'

    # Check for trigonometric
    if contains_trig_functions(expr):
        return 'trigonometric'

    # Check for elliptic patterns
    if matches_elliptic_template(expr):
        return 'elliptic'

    # Check for rational
    numer, denom = expr.as_numer_denom()
    if denom != 1 and numer.is_polynomial() and denom.is_polynomial():
        return 'rational'

    return 'unknown'
```

---

## Task 3.3.2: Enriched Basis Functions (AMENDED)

### Extended Basis Categories

#### Category 1: Geometric Invariants (Baseline)
- Distances: $r_{12}, r_{23}, r_{31}$
- Powers: $r_{12}^2, r_{12}^3, r_{12}^{-1}, r_{12}^{-2}$
- Products: $r_{12} r_{23}, r_{12} r_{23} r_{31}$

#### Category 2: Spinor Components (KS Regularization)

**Motivation**: KS coordinates $(u_0, u_1, u_2, u_3)$ are quaternion/spinor representations of position.

**Basis Functions**:
```python
spinor_basis = {
    # Individual components (12 total: 3 pairs × 4 components)
    'u12_0', 'u12_1', 'u12_2', 'u12_3',  # Body pair 1-2
    'u23_0', 'u23_1', 'u23_2', 'u23_3',  # Body pair 2-3
    'u31_0', 'u31_1', 'u31_2', 'u31_3',  # Body pair 3-1

    # Bilinear forms (inner products)
    'u12 · u23',  # ⟨u12, u23⟩ = u12_0*u23_0 + ... + u12_3*u23_3
    'u12 · u31',
    'u23 · u31',

    # Quaternion products (non-commutative)
    'u12 ⊗ u23',  # Quaternion multiplication
    'u23 ⊗ u31',
    'u31 ⊗ u12',

    # Norms
    '|u12|^2', '|u23|^2', '|u31|^2',
}
```

**Physical Interpretation**:
- KS spinors encode **both position and angular variables**
- A polynomial in spinors may correspond to a complex algebraic function of Cartesian coordinates
- Example: $|u|^2 = r$ (spinor norm = distance)

#### Category 3: Elliptic Functions

**Jacobi Elliptic Functions**:
```python
elliptic_basis = {
    # Jacobi amplitude
    'sn(am(I_arg), k)',  # sn(u, k) where u = f(q,p)
    'cn(am(I_arg), k)',  # cn(u, k)
    'dn(am(I_arg), k)',  # dn(u, k)

    # Argument templates
    'I_arg': [
        'E',                    # Energy
        'sqrt(E) * θ',          # Energy + angle
        'L / sqrt(E)',          # Angular momentum / sqrt(energy)
        'r12 * sqrt(E + 1/r12)', # Mixed geometric-energy
    ],

    # Modular parameter k candidates
    'k': [0.5, 0.7, 0.9, 'symbolic']  # Test fixed values or fit
}
```

**Weierstrass ℘ Function**:
```python
weierstrass_basis = {
    # Weierstrass ℘(z; ω1, ω2)
    'wp(I_arg, omega)',

    # Argument templates
    'I_arg': [
        'E * t',               # Time-parameterized
        'θ',                   # Fiber angle
        'r12 - r23',           # Distance difference
    ],

    # Lattice parameters ω1, ω2 (to be fitted)
}
```

**Implementation Note**: Use `mpmath` or `scipy.special` for numerical evaluation during fitting.

#### Category 4: Modular Forms / Theta Functions

**Jacobi Theta Functions**:
```python
theta_basis = {
    # θ1, θ2, θ3, θ4 (four Jacobi theta functions)
    'theta1(I_arg, q)',  # q = exp(iπτ) where τ = i·K'/K
    'theta2(I_arg, q)',
    'theta3(I_arg, q)',
    'theta4(I_arg, q)',

    # Argument templates
    'I_arg': [
        'θ',                   # Fiber angle (S¹ bundle)
        'arctan(p_y / p_x)',   # Angular momentum angle
        'E / L',               # Energy-momentum ratio
    ]
}
```

**Use Case**: If the integral has **quasi-periodic structure** with two incommensurable frequencies.

#### Category 5: Special Functions from Classical Mechanics

**Delaunay/Poincaré Variables**:
```python
action_angle_basis = {
    # Action variables (related to integrals)
    'I_radial': 'sqrt(2m(E - V(r)))',       # Radial action
    'I_angular': 'L',                        # Angular action

    # Angle variables
    'w_radial': 'arctan(p_r / sqrt(...))',  # Radial angle
    'w_angular': 'θ',                        # Angular angle
}
```

---

### Hierarchical Search Strategy (AMENDED)

```
Level 0: Known Integrals {E, L_x, L_y, L_z, p_θ}
    ↓ Baseline (already found)

Level 1: Polynomial (degree ≤ 3)
    ↓ ~100 functions | SINDy | 1 minute

Level 2: Rational Functions (numerator, denominator degree ≤ 3)
    ↓ ~500 functions | PySR | 10 minutes

Level 3: Algebraic (sqrt, cube root of polynomials)
    ↓ ~200 functions | PySR with sqrt, pow(x, 1/3) | 30 minutes

Level 4: Spinor Bilinears (KS-specific)
    ↓ ~50 functions | SINDy on KS coordinates | 5 minutes

Level 5: Trigonometric (sin, cos, tan of polynomial arguments)
    ↓ ~300 functions | PySR with trig | 1 hour

Level 6: Elliptic Functions (Jacobi sn/cn/dn)
    ↓ ~20 templates × parameter search | Custom optimizer | 2-4 hours

Level 7: Theta Functions (if Level 6 fails)
    ↓ ~16 templates (4 theta × 4 arguments) | Custom | 4-8 hours
```

**Termination Criteria**:
- Stop if conservation error < 10^{-10}
- Stop if all levels exhausted
- Stop if computation time > 24 hours

---

## Task 3.3.3: Candidate Ranking (AMENDED)

### Enhanced Scoring Function

```python
def compute_enhanced_score(candidate, weights):
    """
    Score = w1 * conservation_penalty +
            w2 * complexity_penalty +
            w3 * independence_penalty +
            w4 * interpretability_bonus +
            w5 * function_type_bonus
    """

    # Standard penalties
    conservation_penalty = -log10(conservation_error)  # Lower error → lower penalty
    complexity_penalty = operation_count + nesting_depth
    independence_penalty = 0 if independent else 1e6

    # NEW: Interpretability bonus
    interpretability_bonus = 0
    if has_physical_interpretation(candidate.expression):
        interpretability_bonus = -50  # Negative = better score

    # NEW: Function type bonus
    function_type_bonus = {
        'polynomial': 0,          # Baseline
        'rational': 10,           # Slightly more complex
        'algebraic': 20,          # sqrt acceptable
        'spinor_bilinear': -30,   # Prefer spinor forms (KS-natural)
        'trigonometric': 30,      # Periodic okay if physical
        'elliptic': 50,           # Complex but historically precedented
        'theta': 100,             # Very complex, last resort
    }[candidate.function_type]

    score = (
        weights['conservation'] * conservation_penalty +
        weights['complexity'] * complexity_penalty +
        weights['independence'] * independence_penalty +
        weights['interpretability'] * interpretability_bonus +
        weights['function_type'] * function_type_bonus
    )

    return score
```

### Physical Interpretation Heuristics

```python
def has_physical_interpretation(expr):
    """
    Check if expression has obvious physical meaning.

    Examples:
        - Energy: p^2/2m + V(r) ✓
        - Angular momentum: r × p ✓
        - Runge-Lenz: p × L - r/|r| ✓ (Kepler symmetry)
        - Spinor norm: |u|^2 = r ✓ (KS geometry)
        - Random polynomial: x^3 - 2xy + z ✗
    """
    # Check for conservation law structure
    if matches_pattern(expr, "kinetic + potential"):
        return True

    # Check for geometric invariant
    if is_coordinate_independent(expr):
        return True

    # Check for known symmetry generator
    if matches_symmetry_pattern(expr):
        return True

    return False
```

---

## Computational Requirements (UPDATED)

### Hardware
- **CPU**: 32+ cores (for parallel PySR populations)
- **RAM**: 64 GB (elliptic function libraries)
- **GPU**: Optional (for neural network-assisted search)

### Time Budget
- **SINDy** (Levels 1-2): 10 minutes
- **PySR** (Levels 3-5): 2-4 hours
- **Elliptic/Theta** (Levels 6-7): 4-8 hours
- **Total**: 6-12 hours per candidate

### Software Dependencies
```python
# Standard
pip install numpy scipy sympy pysindy pysr

# Special functions
pip install mpmath  # Arbitrary precision elliptic functions

# Quaternion/Spinor algebra
pip install quaternion

# Optional: Symbolic elliptic functions
pip install sage  # or use mpmath
```

---

## Expected Outcomes (REVISED)

### Best Case: Closed-Form Elliptic Integral
- Top candidate involves Jacobi elliptic function with fitted modulus $k$
- Conservation error < 10^{-12}
- Physical interpretation: Related to KS spinor dynamics
- Example form: $I = \text{cn}(\sqrt{E} \cdot \theta, k) \cdot |u_{12}|^2 + \text{const}$

### Moderate Case: Spinor Polynomial
- Expression is low-degree polynomial in KS spinor components
- Converts to complex algebraic function in Cartesian coordinates
- Conservation error < 10^{-8}
- Ready for WP4 analytical validation

### Realistic Case: High-Degree Polynomial or Rational
- Degree 4-6 polynomial or rational function
- No obvious simplification
- Conservation error < 10^{-6}
- Proceed to WP4 with numerical Poisson brackets

### Negative Case: No Closed Form
- Best fit has residual > 10^{-4}
- May indicate:
  - Integral does not exist (system non-integrable)
  - Integral exists but requires even more exotic functions (hyperelliptic, modular)
  - Numerical candidates from WP 3.1/3.2 were spurious

**Contingency**: Proceed to WP4 with numerical representations

---

## Scientific Risks and Mitigation

### Risk 1: Overfitting to Noise
**Mitigation**:
- Use independent train/test trajectories
- Require conservation on multiple initial conditions
- Cross-validate against WP1 trajectory catalog

### Risk 2: Non-Uniqueness
**Problem**: Multiple symbolic forms may fit equally well
**Mitigation**:
- Prefer simpler expressions (Occam's razor)
- Check if candidates are equivalent under coordinate transformations
- Prioritize expressions with physical interpretation

### Risk 3: Computational Cost
**Problem**: Elliptic function search is expensive
**Mitigation**:
- Use hierarchical search (fast methods first)
- Parallelize across multiple machines
- Implement early stopping if convergence stalls

---

## Integration with WP4 Validation

### Handoff Format

```python
# WP 3.3 → WP 4.1
candidate_integral = {
    'expression_sympy': sp.Expr,           # Symbolic expression
    'expression_latex': str,               # For publication
    'function_type': str,                  # 'elliptic', 'polynomial', etc.
    'basis_functions_used': List[str],     # Which basis functions appear
    'conservation_error': float,           # Numerical test result
    'poisson_bracket_H': sp.Expr,          # {I, H} (if computable)
    'dependencies': List[str],             # Required libraries (mpmath, etc.)
    'numerical_evaluator': Callable,       # Fast numpy function for validation
}
```

### WP4 Validation Requirements

1. **Symbolic Poisson Bracket**: Compute $\{I, H\}$ symbolically
   - If involves elliptic functions: Use computer algebra system (Sage, Mathematica)

2. **Numerical Verification**: Integrate trajectories and monitor $\Delta I$
   - Test on 10^4 trajectories from WP1 catalog
   - Require $|\Delta I / I| < 10^{-6}$ over 100 orbital periods

3. **Independence Check**: Compute Jacobian rank
   - If $I$ involves elliptic functions, compute derivatives numerically

---

## Deliverables (UPDATED)

### Code Modules
- [x] `regression_pipeline.py` - Multi-stage regression
- [x] `basis_functions.py` - Extended basis library
- [ ] **`spinor_basis.py`** - KS spinor functions (NEW)
- [ ] **`elliptic_regression.py`** - Elliptic function fitting (NEW)
- [ ] **`theta_functions.py`** - Theta function templates (NEW)
- [x] `candidate_ranking.py` - Enhanced scoring

### Documentation
- [ ] **"Search Basis Catalog"** - Complete list of basis functions with mathematical definitions
- [ ] **"Elliptic Function Primer"** - Tutorial on elliptic functions in mechanics
- [ ] **"Negative Results Report"** - If no complex integrals found, document search exhaustiveness

### Scientific Outputs
- [ ] Ranked list of candidates (with function types)
- [ ] Conservation plots at multiple time scales
- [ ] **Comparison table**: Polynomial vs. Elliptic vs. Theta function fits

---

## Success Criteria (REVISED)

### Minimum Success
- [ ] Hierarchical search pipeline functional (Levels 1-5)
- [ ] At least one candidate with error < 10^{-6}
- [ ] Function type classification implemented

### Target Success
- [ ] Elliptic function search operational (Level 6)
- [ ] Top 3 candidates have error < 10^{-8}
- [ ] At least one spinor-based candidate identified

### Stretch Success
- [ ] Closed-form elliptic integral with error < 10^{-12}
- [ ] Physical interpretation clear
- [ ] Publication-ready: "Discovery of Fourth Integral via Symbolic Regression"

---

## Timeline (REVISED)

**Days 1-3**: Task 3.3.1
- Implement SINDy, PySR, spinor basis
- Test on known integrals (E, L)

**Days 4-7**: Task 3.3.2
- Construct elliptic and theta function basis
- Implement custom regression for special functions
- Validate on Kowalevskaya top

**Days 8-10**: Long regression runs
- PySR on full search space (2-4 hours per candidate)
- Elliptic function parameter optimization

**Days 11-13**: Task 3.3.3
- Candidate consolidation and ranking
- Multi-scale conservation tests
- Physical interpretation analysis

**Days 14-15**: Documentation and reporting
- Generate candidate report
- Create visualization gallery
- Prepare WP4 handoff materials

**Total**: 15 days (with buffer for long searches)

---

## References (EXTENDED)

### Symbolic Regression
1. Brunton et al., "Discovering governing equations from data" (2016)
2. Cranmer, "Interpretable ML for Science with PySR" (2023)
3. Schmidt & Lipson, "Distilling free-form natural laws" (2009)

### Special Functions in Mechanics
4. **Whittaker & Watson**, *A Course of Modern Analysis* (1927) - Elliptic functions
5. **Lawden**, *Elliptic Functions and Applications* (1989)
6. **Mumford**, *Tata Lectures on Theta* (1983-1991) - Theta functions

### Integrable Systems
7. **Arnold**, *Mathematical Methods of Classical Mechanics* (1989) - Action-angle variables
8. **Olver**, *Applications of Lie Groups to Differential Equations* (1993)
9. **Kowalevski**, *Sur le problème de la rotation d'un corps solide* (1889) - Elliptic integrals in rigid body

### Three-Body Problem
10. **Meyer & Hall**, *Introduction to Hamiltonian Dynamical Systems* (1992)
11. **Stiefel & Scheifele**, *Linear and Regular Celestial Mechanics* (1971) - KS regularization

---

**Document Version**: 2.0 (AMENDED)
**Last Updated**: 2025-11-20
**Status**: Extended Planning - Ready for Implementation with Enriched Basis
**Key Changes**:
- Added spinor component basis (KS-specific)
- Added elliptic function search (Jacobi, Weierstrass)
- Added theta function templates
- Extended timeline from 10-12 days to 12-15 days
- Enhanced scoring function with interpretability and function-type bonuses
