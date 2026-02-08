# Task 3.2.4: Validation and Generalization Guardrails
## Implementation Plan

**Duration**: 3-4 days
**Priority**: Critical (Ensures results are genuine, not spurious)
**Dependencies**: Task 3.2.3 (trained ConservationHNN)

---

## Overview

**Goal**: Rigorously validate that discovered invariants are:
1. **Conserved**: dI/dt ≈ 0 along trajectories
2. **Independent**: Not linear combinations of known integrals
3. **Generalizable**: Work beyond training distribution
4. **Physical**: Not overfitting artifacts

**Philosophy**: Neural networks can easily overfit or learn spurious patterns. We must apply multiple validation tests to ensure discovered invariants are genuine.

---

## Part A: Conservation Verification (1 day)

### A.1: Trajectory Integration Tests

**File**: `src/python/ml/validation.py`

```python
import jax
import jax.numpy as jnp
from scipy.integrate import solve_ivp
from typing import Dict, Tuple, List
import numpy as np

@dataclass
class ConservationTestResult:
    """Results from conservation validation."""
    trajectory_id: int
    initial_value: float
    final_value: float
    max_absolute_drift: float
    relative_drift: float
    mean_absolute_deviation: float
    conserved: bool  # True if drift < threshold
    integration_time: float

def verify_conservation_single_trajectory(
    model,
    params,
    z0: jnp.ndarray,
    t_span: Tuple[float, float],
    dt: float = 0.1,
    inv_idx: int = 0,
    threshold: float = 1e-5
) -> ConservationTestResult:
    """
    Verify conservation of I_φ along a single trajectory.

    Procedure:
    1. Integrate Hamilton's equations using learned H_θ
    2. Evaluate I_φ at each timestep
    3. Compute drift: max|I(t) - I(0)| / |I(0)|
    4. Check if drift < threshold

    Args:
        model: Trained ConservationHNN
        params: Model parameters
        z0: Initial state
        t_span: (t_start, t_end)
        dt: Timestep for evaluation
        inv_idx: Which invariant to test
        threshold: Acceptable relative drift

    Returns:
        ConservationTestResult with metrics
    """
    # Define dynamics using learned Hamiltonian
    def learned_dynamics(t, z):
        return np.array(model.dynamics(jnp.array(z), params))

    # Integrate trajectory
    times = np.arange(t_span[0], t_span[1], dt)
    sol = solve_ivp(
        learned_dynamics,
        t_span,
        z0,
        t_eval=times,
        method='DOP853',
        rtol=1e-10,
        atol=1e-12
    )

    if not sol.success:
        raise ValueError("Integration failed")

    # Evaluate invariant at each timestep
    I_values = np.array([
        model.invariant(jnp.array(sol.y[:, i]), params, inv_idx)
        for i in range(len(sol.t))
    ])

    # Compute drift metrics
    I0 = I_values[0]
    I_final = I_values[-1]

    absolute_drift = np.abs(I_values - I0)
    max_abs_drift = np.max(absolute_drift)
    relative_drift = max_abs_drift / (np.abs(I0) + 1e-14)
    mean_abs_deviation = np.mean(absolute_drift)

    # Check conservation
    is_conserved = relative_drift < threshold

    return ConservationTestResult(
        trajectory_id=0,
        initial_value=float(I0),
        final_value=float(I_final),
        max_absolute_drift=float(max_abs_drift),
        relative_drift=float(relative_drift),
        mean_absolute_deviation=float(mean_abs_deviation),
        conserved=is_conserved,
        integration_time=sol.t[-1]
    )

def verify_conservation_ensemble(
    model,
    params,
    initial_states: List[jnp.ndarray],
    t_span: Tuple[float, float] = (0, 100),
    dt: float = 0.1,
    inv_idx: int = 0,
    threshold: float = 1e-5
) -> Dict:
    """
    Verify conservation across ensemble of trajectories.

    Args:
        model: Trained model
        params: Parameters
        initial_states: List of initial conditions
        t_span: Integration time
        dt: Timestep
        inv_idx: Invariant index
        threshold: Conservation threshold

    Returns:
        Dictionary with ensemble statistics:
        - conservation_rate: Fraction of trajectories conserved
        - mean_drift: Mean relative drift
        - max_drift: Worst-case drift
        - individual_results: List of ConservationTestResults
    """
    results = []

    for i, z0 in enumerate(initial_states):
        try:
            result = verify_conservation_single_trajectory(
                model, params, z0, t_span, dt, inv_idx, threshold
            )
            result.trajectory_id = i
            results.append(result)
        except Exception as e:
            print(f"Trajectory {i} failed: {e}")
            continue

    # Aggregate statistics
    conservation_rate = sum(r.conserved for r in results) / len(results)
    mean_drift = np.mean([r.relative_drift for r in results])
    max_drift = np.max([r.relative_drift for r in results])

    return {
        'conservation_rate': conservation_rate,
        'mean_drift': mean_drift,
        'max_drift': max_drift,
        'num_trajectories': len(results),
        'threshold': threshold,
        'individual_results': results
    }
```

**Deliverables**:
- [ ] `validation.py` (~400 lines)
- [ ] Tests on validation dataset (100+ trajectories)
- [ ] Conservation plots: I(t) vs t for sample trajectories

---

## Part B: Out-of-Distribution Testing (1 day)

### B.1: OOD Generalization Tests

**File**: `src/python/ml/ood_tests.py`

```python
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class OODTestConfig:
    """Configuration for out-of-distribution test."""
    test_name: str
    description: str
    train_range: Tuple[float, float]
    test_range: Tuple[float, float]
    parameter: str  # 'mass_ratio', 'energy', 'angular_momentum', etc.

def create_ood_test_suite() -> List[OODTestConfig]:
    """
    Define suite of OOD tests.

    Tests verify that learned invariants generalize beyond
    the training distribution.
    """
    tests = [
        OODTestConfig(
            test_name='mass_ratio_ood',
            description='Test on different mass ratios',
            train_range=(0.1, 0.3),
            test_range=(0.4, 0.5),
            parameter='mass_ratio'
        ),
        OODTestConfig(
            test_name='energy_ood',
            description='Test on different energies',
            train_range=(-1.5, -0.5),
            test_range=(-2.0, -1.5),
            parameter='energy'
        ),
        OODTestConfig(
            test_name='angular_momentum_ood',
            description='Test on different angular momenta',
            train_range=(1.0, 2.0),
            test_range=(2.5, 3.5),
            parameter='angular_momentum'
        ),
        OODTestConfig(
            test_name='long_time_ood',
            description='Test on longer integration times',
            train_range=(0, 50),  # Training trajectories: 50 time units
            test_range=(0, 200),  # Test: 200 time units
            parameter='integration_time'
        ),
        OODTestConfig(
            test_name='high_eccentricity_ood',
            description='Test on high eccentricity orbits',
            train_range=(0.0, 0.5),
            test_range=(0.6, 0.9),
            parameter='eccentricity'
        )
    ]
    return tests

def run_ood_test(
    model,
    params,
    test_config: OODTestConfig,
    num_samples: int = 50
) -> Dict:
    """
    Run single out-of-distribution test.

    Procedure:
    1. Generate test samples in OOD regime
    2. Integrate trajectories
    3. Verify conservation
    4. Compare to in-distribution performance

    Returns:
        Results dictionary with OOD performance metrics
    """
    # Generate OOD samples
    if test_config.parameter == 'mass_ratio':
        test_states = generate_samples_mass_ratio(
            test_config.test_range,
            num_samples
        )
    elif test_config.parameter == 'energy':
        test_states = generate_samples_energy(
            test_config.test_range,
            num_samples
        )
    # ... other cases ...

    # Verify conservation on OOD samples
    results = verify_conservation_ensemble(
        model,
        params,
        test_states,
        t_span=(0, 100),
        threshold=1e-5
    )

    return {
        'test_name': test_config.test_name,
        'description': test_config.description,
        'conservation_rate': results['conservation_rate'],
        'mean_drift': results['mean_drift'],
        'max_drift': results['max_drift'],
        'num_samples': num_samples
    }

def run_full_ood_suite(
    model,
    params,
    num_samples_per_test: int = 50
) -> Dict:
    """
    Run complete OOD validation suite.

    Returns:
        Comprehensive OOD validation report
    """
    test_suite = create_ood_test_suite()
    results = []

    print("=" * 60)
    print("OUT-OF-DISTRIBUTION VALIDATION SUITE")
    print("=" * 60)

    for test_config in test_suite:
        print(f"\nRunning: {test_config.test_name}")
        print(f"  {test_config.description}")

        result = run_ood_test(model, params, test_config, num_samples_per_test)
        results.append(result)

        print(f"  Conservation Rate: {result['conservation_rate']:.2%}")
        print(f"  Mean Drift: {result['mean_drift']:.2e}")

    # Overall OOD score
    overall_conservation_rate = np.mean([r['conservation_rate'] for r in results])

    return {
        'individual_tests': results,
        'overall_conservation_rate': overall_conservation_rate,
        'num_tests': len(results)
    }
```

**Deliverables**:
- [ ] `ood_tests.py` (~350 lines)
- [ ] OOD validation report
- [ ] Comparison plots: In-distribution vs OOD performance

---

## Part C: Functional Independence Testing (1 day)

### C.1: Jacobian Rank Analysis

**File**: `src/python/ml/independence_test.py`

```python
import jax
import jax.numpy as jnp
from typing import List, Callable

def test_functional_independence_ml(
    model,
    params,
    known_integrals: List[Callable],
    test_states: List[jnp.ndarray],
    inv_idx: int = 0,
    tolerance: float = 1e-6
) -> Dict:
    """
    Test if learned invariant I_φ is functionally independent
    of known integrals (E, L, p_θ, etc.).

    Method: Jacobian rank test
    1. Define function vector F = (E, L_x, L_y, L_z, p_θ, I_φ)
    2. Compute Jacobian J_ij = ∂F_i/∂z_j at multiple states
    3. Check rank(J) = rank(J_known) + 1

    Args:
        model: Trained model
        params: Parameters
        known_integrals: List of known conserved quantities
        test_states: Sample states for evaluation
        inv_idx: Which learned invariant to test
        tolerance: Numerical tolerance for rank determination

    Returns:
        Dictionary with independence test results
    """
    num_known = len(known_integrals)
    num_total = num_known + 1  # Known + learned invariant

    # Define combined function vector
    def function_vector(z):
        """F(z) = [I_1(z), I_2(z), ..., I_k(z), I_φ(z)]"""
        # Known integrals
        known_values = jnp.array([I(z) for I in known_integrals])

        # Learned invariant
        learned_value = model.invariant(z, params, inv_idx)

        return jnp.concatenate([known_values, jnp.array([learned_value])])

    # Compute Jacobian at each test state
    jacobians = []
    for z in test_states:
        J = jax.jacobian(function_vector)(z)
        jacobians.append(J)

    # Compute ranks
    ranks_known = []
    ranks_total = []

    for J in jacobians:
        # Rank of known integrals only
        J_known = J[:num_known, :]
        rank_known = np.linalg.matrix_rank(J_known, tol=tolerance)
        ranks_known.append(rank_known)

        # Rank including learned invariant
        rank_total = np.linalg.matrix_rank(J, tol=tolerance)
        ranks_total.append(rank_total)

    # Check if rank increases
    rank_increase = np.array(ranks_total) - np.array(ranks_known)
    independent = np.all(rank_increase == 1)

    # Condition number analysis
    condition_numbers = [np.linalg.cond(J) for J in jacobians]

    return {
        'independent': independent,
        'rank_known': np.mean(ranks_known),
        'rank_total': np.mean(ranks_total),
        'rank_increase': np.mean(rank_increase),
        'condition_number': np.mean(condition_numbers),
        'test_states': len(test_states),
        'details': {
            'ranks_known': ranks_known,
            'ranks_total': ranks_total,
            'rank_increase': rank_increase
        }
    }

def test_involution_ml(
    model,
    params,
    inv_idx1: int,
    inv_idx2: int,
    test_states: List[jnp.ndarray],
    tolerance: float = 1e-6
) -> Dict:
    """
    Test if two learned invariants are in involution: {I_i, I_j} ≈ 0.

    For Liouville integrability, conserved quantities must
    pairwise commute.

    Args:
        model: Model with multiple invariants
        params: Parameters
        inv_idx1, inv_idx2: Indices of invariants to test
        test_states: Sample states
        tolerance: Tolerance for Poisson bracket

    Returns:
        Involution test results
    """
    def poisson_bracket(z):
        n = len(z) // 2

        grad_I1 = jax.grad(lambda s: model.invariant(s, params, inv_idx1))(z)
        grad_I2 = jax.grad(lambda s: model.invariant(s, params, inv_idx2))(z)

        dI1_dq, dI1_dp = grad_I1[:n], grad_I1[n:]
        dI2_dq, dI2_dp = grad_I2[:n], grad_I2[n:]

        bracket = jnp.dot(dI1_dq, dI2_dp) - jnp.dot(dI1_dp, dI2_dq)
        return bracket

    # Compute Poisson bracket at all test states
    brackets = jnp.array([poisson_bracket(z) for z in test_states])

    # Check if {I_i, I_j} ≈ 0
    mean_bracket = jnp.mean(jnp.abs(brackets))
    max_bracket = jnp.max(jnp.abs(brackets))
    in_involution = max_bracket < tolerance

    return {
        'in_involution': in_involution,
        'mean_poisson_bracket': float(mean_bracket),
        'max_poisson_bracket': float(max_bracket),
        'tolerance': tolerance,
        'bracket_values': brackets
    }

def analyze_learned_integral(
    model,
    params,
    inv_idx: int,
    test_states: List[jnp.ndarray],
    known_integrals: List[Callable]
) -> Dict:
    """
    Comprehensive analysis of learned integral.

    Tests:
    1. Conservation verification
    2. Functional independence from known integrals
    3. Involution with known integrals (Poisson commutativity)
    4. Smoothness (gradient statistics)

    Returns:
        Complete analysis report
    """
    # 1. Conservation
    conservation_results = verify_conservation_ensemble(
        model, params, test_states, inv_idx=inv_idx
    )

    # 2. Independence
    independence_results = test_functional_independence_ml(
        model, params, known_integrals, test_states, inv_idx
    )

    # 3. Involution with known integrals
    # (Only test with energy, since other known integrals commute by assumption)
    involution_results = []
    # ... test {I_φ, E}, {I_φ, L}, etc. ...

    # 4. Smoothness: Check gradient norm statistics
    gradients = []
    for z in test_states:
        grad = jax.grad(lambda s: model.invariant(s, params, inv_idx))(z)
        gradients.append(jnp.linalg.norm(grad))

    gradient_stats = {
        'mean': float(jnp.mean(jnp.array(gradients))),
        'std': float(jnp.std(jnp.array(gradients))),
        'max': float(jnp.max(jnp.array(gradients)))
    }

    return {
        'conservation': conservation_results,
        'independence': independence_results,
        'involution': involution_results,
        'gradient_statistics': gradient_stats
    }
```

**Deliverables**:
- [ ] `independence_test.py` (~400 lines)
  - Note: Can reuse/extend `src/python/analysis/independence_test.py` from WP 3.1.4
- [ ] Independence validation report
- [ ] Jacobian rank plots

---

## Part D: Comparison with WP 3.1 Geometric Results (0.5 days)

### D.1: Cross-Validation

**File**: `src/python/ml/wp31_comparison.py`

```python
def compare_ml_vs_geometric(
    ml_model,
    ml_params,
    geometric_integrals: List,  # From WP 3.1
    test_states: List[jnp.ndarray]
) -> Dict:
    """
    Compare ML-discovered integrals with geometric (Killing field) integrals.

    Questions:
    1. Do they agree numerically?
    2. Are they the same up to linear combination?
    3. Did ML find something geometric search missed?

    Args:
        ml_model: Trained ConservationHNN
        ml_params: Parameters
        geometric_integrals: Integrals from WP 3.1 Killing PDE solver
        test_states: Sample states

    Returns:
        Comparison analysis
    """
    from src.python.analysis.integral_from_killing import ConservedIntegral

    # Evaluate ML integral
    I_ml_values = np.array([
        ml_model.invariant(z, ml_params)
        for z in test_states
    ])

    # Evaluate geometric integrals
    geometric_values = []
    for integral in geometric_integrals:
        values = np.array([
            integral.expression(z)
            for z in test_states
        ])
        geometric_values.append(values)

    # Test for linear dependence
    # If I_ml = a_0 + a_1 I_1 + ... + a_k I_k, then ML found nothing new
    from sklearn.linear_model import LinearRegression

    X = np.column_stack(geometric_values)  # (N, k)
    y = I_ml_values  # (N,)

    reg = LinearRegression().fit(X, y)
    y_pred = reg.predict(X)
    r2_score = reg.score(X, y)

    if r2_score > 0.99:
        conclusion = "ML integral is linear combination of geometric integrals"
        novel = False
    else:
        conclusion = "ML integral is independent of geometric integrals"
        novel = True

    return {
        'novel': novel,
        'r2_score': r2_score,
        'linear_coefficients': reg.coef_,
        'conclusion': conclusion
    }
```

**Deliverables**:
- [ ] `wp31_comparison.py` (~200 lines)
- [ ] Comparison report: ML vs Geometric discoveries

---

## Part E: Validation Report Generation (0.5 days)

### E.1: Comprehensive Report

**File**: `src/python/ml/validation_report.py`

```python
import matplotlib.pyplot as plt
from typing import Dict

def generate_validation_report(
    model,
    params,
    val_dataset,
    ood_results: Dict,
    independence_results: Dict,
    output_dir: str
):
    """
    Generate comprehensive validation report with plots and tables.

    Sections:
    1. Executive Summary
    2. Conservation Verification
       - Trajectory plots: I(t) vs t
       - Conservation rate table
       - Drift histograms
    3. OOD Generalization
       - Conservation rates by regime
       - Generalization gap analysis
    4. Functional Independence
       - Jacobian rank analysis
       - Involution tests
    5. Comparison with WP 3.1
    6. Conclusions and Recommendations

    Outputs:
    - validation_report.pdf
    - Figures saved to output_dir/figures/
    - Raw data saved to output_dir/data/
    """
    report_sections = []

    # Section 1: Executive Summary
    summary = f"""
    # WP 3.2 Validation Report

    ## Executive Summary

    - **Learned Invariant**: I_φ(q, p) [functional form TBD]
    - **Conservation Rate**: {ood_results['overall_conservation_rate']:.1%}
    - **Functionally Independent**: {independence_results['independent']}
    - **Generalization**: {'PASS' if ood_results['overall_conservation_rate'] > 0.9 else 'FAIL'}

    ## Key Findings

    [To be filled programmatically]
    """

    # Section 2: Conservation plots
    plot_conservation_trajectories(model, params, val_dataset, output_dir)

    # Section 3: OOD performance
    plot_ood_performance(ood_results, output_dir)

    # Section 4: Independence analysis
    plot_jacobian_analysis(independence_results, output_dir)

    # Generate PDF report (using reportlab or LaTeX)
    # ...
    pass

def plot_conservation_trajectories(
    model,
    params,
    dataset,
    output_dir: str,
    num_examples: int = 6
):
    """
    Plot I(t) vs t for sample trajectories.

    Shows conservation visually.
    """
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()

    for i in range(num_examples):
        # Get trajectory
        z0 = dataset.get_initial_state(i)

        # Integrate and evaluate I(t)
        result = verify_conservation_single_trajectory(
            model, params, z0, t_span=(0, 100), dt=0.1
        )

        # Plot (need to extract I(t) from result)
        # axes[i].plot(times, I_values)
        # axes[i].set_title(f"Trajectory {i}: Drift = {result.relative_drift:.2e}")

    plt.savefig(f"{output_dir}/conservation_trajectories.png")
    plt.close()

def plot_ood_performance(ood_results: Dict, output_dir: str):
    """
    Bar chart: Conservation rate for each OOD test.
    """
    test_names = [r['test_name'] for r in ood_results['individual_tests']]
    conservation_rates = [r['conservation_rate'] for r in ood_results['individual_tests']]

    plt.figure(figsize=(10, 6))
    plt.barh(test_names, conservation_rates)
    plt.xlabel('Conservation Rate')
    plt.title('Out-of-Distribution Generalization')
    plt.axvline(x=0.9, color='r', linestyle='--', label='Target (90%)')
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{output_dir}/ood_performance.png")
    plt.close()

def plot_jacobian_analysis(independence_results: Dict, output_dir: str):
    """
    Visualize Jacobian rank distribution.
    """
    ranks = independence_results['details']['ranks_total']

    plt.figure(figsize=(8, 6))
    plt.hist(ranks, bins=10, edgecolor='black')
    plt.xlabel('Jacobian Rank')
    plt.ylabel('Frequency')
    plt.title('Functional Independence: Jacobian Rank Distribution')
    plt.savefig(f"{output_dir}/jacobian_ranks.png")
    plt.close()
```

**Deliverables**:
- [ ] `validation_report.py` (~300 lines)
- [ ] Automated report generation script
- [ ] Example validation report (PDF)

---

## Part F: Acceptance Criteria (0.5 days)

### F.1: Formal Acceptance Tests

**File**: `tests/wp3/test_ml_validation.py`

```python
import pytest

def test_conservation_acceptance():
    """
    ACCEPTANCE TEST: Conservation rate > 90% on validation set.
    """
    # Load trained model
    model, params = load_trained_model()

    # Load validation dataset
    val_dataset = load_validation_dataset()

    # Run conservation tests
    results = verify_conservation_ensemble(
        model, params, val_dataset.initial_states, threshold=1e-5
    )

    # Assert acceptance criterion
    assert results['conservation_rate'] > 0.9, \
        f"Conservation rate {results['conservation_rate']:.1%} < 90%"

def test_ood_generalization_acceptance():
    """
    ACCEPTANCE TEST: OOD conservation rate > 80%.
    """
    model, params = load_trained_model()
    ood_results = run_full_ood_suite(model, params)

    assert ood_results['overall_conservation_rate'] > 0.8, \
        f"OOD conservation rate {ood_results['overall_conservation_rate']:.1%} < 80%"

def test_functional_independence_acceptance():
    """
    ACCEPTANCE TEST: Learned integral is independent of known integrals.
    """
    model, params = load_trained_model()
    known_integrals = load_known_integrals()
    test_states = generate_test_states(1000)

    results = test_functional_independence_ml(
        model, params, known_integrals, test_states
    )

    assert results['independent'], \
        "Learned integral is not functionally independent"

def test_non_trivial_acceptance():
    """
    ACCEPTANCE TEST: Learned integral is non-trivial.

    Checks:
    1. Not constant: std(I) / mean(I) > 0.1
    2. Not coordinate function: Nonlinear in z
    3. Different from known integrals
    """
    model, params = load_trained_model()
    test_states = generate_test_states(1000)

    I_values = np.array([
        model.invariant(z, params)
        for z in test_states
    ])

    # Non-constant
    coefficient_of_variation = np.std(I_values) / (np.abs(np.mean(I_values)) + 1e-10)
    assert coefficient_of_variation > 0.1, "Invariant appears to be constant"

    # TODO: Add nonlinearity test

def test_full_validation_suite():
    """
    META-TEST: Run all validation tests and generate report.

    This is the master test that runs the complete validation pipeline.
    """
    model, params = load_trained_model()

    # Run all tests
    conservation_ok = test_conservation_acceptance()
    ood_ok = test_ood_generalization_acceptance()
    independence_ok = test_functional_independence_acceptance()
    non_trivial_ok = test_non_trivial_acceptance()

    # Generate report
    generate_validation_report(model, params, ...)

    # Overall verdict
    all_passed = all([conservation_ok, ood_ok, independence_ok, non_trivial_ok])

    assert all_passed, "Not all validation tests passed"
```

**Deliverables**:
- [ ] `test_ml_validation.py` (~250 lines)
- [ ] Automated acceptance test suite

---

## Integration Points

### From Task 3.2.3 (Conservation Training)
- **Input**: Trained ConservationHNN with learned invariant
- **Checkpoint**: Model parameters, training history

### To WP 3.3 (Symbolic Regression - Future)
- **Output**: Validated numerical function I_φ(q, p)
- **Format**: Evaluations on dense grid for regression
- **Metadata**: Conservation error, independence status

### From WP 3.1 (Geometric Search)
- **Input**: Killing field integrals for comparison
- **Comparison**: Check if ML and geometric agree

---

## Implementation Schedule

### Day 1: Conservation Verification
- [ ] Implement trajectory integration tests
- [ ] Test on validation set (100 trajectories)
- [ ] Generate conservation plots

### Day 2: OOD Testing
- [ ] Implement OOD test suite
- [ ] Run all OOD tests
- [ ] Analyze generalization performance

### Day 3: Independence Testing
- [ ] Implement Jacobian rank tests
- [ ] Test functional independence
- [ ] Compare with WP 3.1 results

### Day 4: Reporting & Acceptance
- [ ] Generate validation report
- [ ] Implement acceptance tests
- [ ] Final verdict: PASS/FAIL

---

## Success Criteria

**Minimum (Research Contribution)**:
- [ ] Conservation verified on ≥ 80% of validation trajectories
- [ ] OOD generalization demonstrated on ≥ 2 regimes
- [ ] Non-trivial invariant (not constant, not known integral)

**Target (Strong Result)**:
- [ ] Conservation rate > 90% (drift < 10⁻⁵)
- [ ] OOD conservation rate > 80%
- [ ] Functionally independent of all known integrals
- [ ] Generalizes across full parameter space

**Stretch (Publication-Quality)**:
- [ ] Conservation rate > 95% (drift < 10⁻⁶)
- [ ] Perfect OOD generalization (>90% on all tests)
- [ ] Multiple independent invariants discovered
- [ ] Agreement with WP 3.1 geometric methods

---

## Deliverables Summary

### Code
- [ ] `src/python/ml/validation.py` (~400 lines)
- [ ] `src/python/ml/ood_tests.py` (~350 lines)
- [ ] `src/python/ml/independence_test.py` (~400 lines)
- [ ] `src/python/ml/wp31_comparison.py` (~200 lines)
- [ ] `src/python/ml/validation_report.py` (~300 lines)

### Tests
- [ ] `tests/wp3/test_ml_validation.py` (~250 lines)

### Documentation
- [ ] Validation report (PDF, 20-30 pages)
- [ ] Validation plots and figures
- [ ] Acceptance test results

**Total**: ~1,900 lines code + comprehensive report

---

## Negative Results Protocol

**What if validation fails?**

If the learned invariant does NOT pass validation:

1. **Diagnose**: Identify which test failed
   - Conservation? → Increase training time, tune λ_conservation
   - Independence? → May have rediscovered known integral (still useful validation)
   - OOD? → Training distribution too narrow, expand dataset
   - Trivial? → Increase regularization penalties

2. **Document**: Negative results are scientifically valuable
   - Report what was attempted
   - Explain why it failed
   - Provide recommendations for future work

3. **Iterate**: If time permits
   - Adjust hyperparameters
   - Modify architecture
   - Expand training data

4. **Alternative success**: Even if no novel integral found
   - HNN learning validates WP 3.1 results
   - Method demonstrated on 3-body problem
   - Framework established for future systems

---

**Document Version**: 1.0
**Status**: Ready for Implementation
**Completion**: This completes WP 3.2 implementation planning
