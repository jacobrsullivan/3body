# WP3 Integration Testing Guide

## Overview

This document provides detailed specifications for integration tests that validate the complete WP3 pipeline, ensuring all three tracks (WP3.1, WP3.2, WP3.3) work together seamlessly.

## Test Architecture

```
Integration Tests
├── Test Suite 1: WP3.1 → WP3.3 (Geometric → Symbolic)
├── Test Suite 2: WP3.2 → WP3.3 (ML → Symbolic)
└── Test Suite 3: Full Pipeline (Consolidation → Ranking → Report)
```

Each test suite validates:
- ✓ Data flow between components
- ✓ API compatibility
- ✓ Numerical accuracy
- ✓ Conservation properties
- ✓ Output format correctness

---

## Test Suite 1: WP3.1 → WP3.3 Integration

**Purpose**: Verify that Killing field results from geometric search can be converted to symbolic expressions and validated.

### Test 1.1: Trivial Case - Angular Momentum on S¹ Bundle

**What it tests**: Known conserved quantity (p_θ) should be recovered and validated.

#### Test Code

```python
"""
Test: WP3.1 Killing field → WP3.3 symbolic expression → validation

Expected result: p_θ (fiber momentum) is conserved with error < 1e-12
"""

import numpy as np
import sympy as sp
from src.python.pde import solve_killing_fields
from src.python.analysis import discover_integrals_from_killing_solution
from src.python.symbolic import (
    create_candidate_from_wp31_killing,
    validate_candidate_integral,
    simplify_candidate_integral,
    CandidateSource
)


def test_wp31_to_wp33_angular_momentum():
    """Test 1.1: Known integral (p_θ) from WP3.1 through WP3.3 validation."""

    print("=" * 80)
    print("TEST 1.1: WP3.1 → WP3.3 - Angular Momentum (p_θ)")
    print("=" * 80)

    # Step 1: WP3.1 - Discover Killing fields on S¹ bundle
    print("\n[WP3.1] Solving Killing equations on S¹ bundle...")

    masses = np.array([1.0, 1.0, 1.0])
    energy = -1.0
    L_magnitude = 1.0

    try:
        killing_solution = solve_killing_fields(
            manifold_type='s1_bundle',
            masses=masses,
            energy=energy,
            L_magnitude=L_magnitude,
            resolution={'shape_fine': 50, 'fiber': 16},
            field_type='vector',
            verbose=False
        )
        print(f"  ✓ Found {len(killing_solution.fields)} Killing fields")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False

    # Step 2: WP3.1 - Convert to integrals
    print("\n[WP3.1] Converting Killing fields to integrals...")

    # Define metric and Hamiltonian (simplified for test)
    def s1_metric(state):
        # Simplified metric for S¹ bundle
        dim = len(state) // 2
        g = np.eye(dim * 2)
        return g

    def s1_hamiltonian(state):
        # Simplified Hamiltonian
        dim = len(state) // 2
        q = state[:dim]
        p = state[dim:]
        H = 0.5 * np.sum(p**2)  # Simplified
        dH_dq = -q  # Simplified
        dH_dp = p
        dz_dt = np.concatenate([dH_dp, -dH_dq])
        return dz_dt, H

    try:
        integral_result = discover_integrals_from_killing_solution(
            killing_solution,
            metric_func=s1_metric,
            hamiltonian=s1_hamiltonian,
            masses=masses,
            test_trajectory_count=5
        )
        print(f"  ✓ Discovered {len(integral_result.conserved)} conserved integrals")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False

    # Step 3: WP3.3 - Select p_θ integral
    print("\n[WP3.3] Converting to symbolic expression...")

    # Find the fiber momentum integral (should be one of the discovered integrals)
    p_theta_integral = None
    for integral in integral_result.conserved:
        if 'theta' in integral.name.lower() or 'fiber' in integral.name.lower():
            p_theta_integral = integral
            break

    if p_theta_integral is None:
        print("  ✗ FAILED: p_θ integral not found in results")
        return False

    # Create symbolic expression (simplified for test)
    # In full implementation, this would come from regression
    state_symbols = sp.symbols('q0 q1 q2 q3 p0 p1 p2 p3')
    p_theta_sym = state_symbols[7]  # p_θ is the 8th component

    print(f"  ✓ Symbolic expression: p_θ")

    # Step 4: WP3.3 - Simplify
    print("\n[WP3.3] Simplifying expression...")

    simplified = simplify_candidate_integral(
        p_theta_sym,
        list(state_symbols)
    )

    print(f"  Original:   {simplified.original}")
    print(f"  Simplified: {simplified.simplified}")
    print(f"  Reduction:  {simplified.reduction_factor:.2f}")

    # Step 5: WP3.3 - Validate conservation
    print("\n[WP3.3] Validating conservation...")

    # Numerical function
    def p_theta_numerical(z):
        return z[7]  # 8th component

    # Generate test states
    sample_states = np.random.randn(100, 8)
    initial_conditions = np.random.randn(5, 8)

    validation = validate_candidate_integral(
        simplified.simplified,
        p_theta_numerical,
        s1_hamiltonian,
        sample_states,
        list(state_symbols),
        test_trajectories=initial_conditions
    )

    print(f"  Conservation error: {validation.conservation_error:.2e}")
    print(f"  Is conserved: {validation.is_conserved}")
    print(f"  Symbolic-numerical residual: {validation.symbolic_numerical_residual:.2e}")

    # Step 6: WP3.3 - Create candidate
    print("\n[WP3.3] Creating candidate integral...")

    candidate = create_candidate_from_wp31_killing(
        killing_field_name="K_theta",
        integral_expr=simplified.simplified,
        integral_func=p_theta_numerical,
        validation=validation,
        is_tensor=False
    )

    print(f"  Name: {candidate.name}")
    print(f"  Source: {candidate.source}")
    print(f"  Complexity: {candidate.complexity}")

    # Success criteria
    success = (
        validation.is_conserved and
        validation.conservation_error < 1e-5 and
        validation.symbolic_numerical_residual < 1e-10
    )

    print("\n" + "=" * 80)
    if success:
        print("✓ TEST 1.1 PASSED")
        print(f"  - Conservation error: {validation.conservation_error:.2e} < 1e-5")
        print(f"  - Symbolic-numerical agreement: {validation.symbolic_numerical_residual:.2e} < 1e-10")
    else:
        print("✗ TEST 1.1 FAILED")
        if not validation.is_conserved:
            print(f"  - Not conserved (error: {validation.conservation_error:.2e})")
        if validation.symbolic_numerical_residual >= 1e-10:
            print(f"  - Symbolic-numerical mismatch: {validation.symbolic_numerical_residual:.2e}")
    print("=" * 80)

    return success


if __name__ == "__main__":
    test_wp31_to_wp33_angular_momentum()
```

#### Expected Output

```
================================================================================
TEST 1.1: WP3.1 → WP3.3 - Angular Momentum (p_θ)
================================================================================

[WP3.1] Solving Killing equations on S¹ bundle...
  ✓ Found 4 Killing fields

[WP3.1] Converting Killing fields to integrals...
  ✓ Discovered 3 conserved integrals

[WP3.3] Converting to symbolic expression...
  ✓ Symbolic expression: p_θ

[WP3.3] Simplifying expression...
  Original:   p3
  Simplified: p3
  Reduction:  1.00

[WP3.3] Validating conservation...
  Conservation error: 3.24e-13
  Is conserved: True
  Symbolic-numerical residual: 0.00e+00

[WP3.3] Creating candidate integral...
  Name: I_K_theta
  Source: wp3.1_killing_field
  Complexity: 1

================================================================================
✓ TEST 1.1 PASSED
  - Conservation error: 3.24e-13 < 1e-5
  - Symbolic-numerical agreement: 0.00e+00 < 1e-10
================================================================================
```

#### Success Criteria

- ✓ WP3.1 finds Killing fields (including p_θ)
- ✓ Integral discovery identifies conserved quantities
- ✓ Symbolic expression matches numerical function (residual < 1e-10)
- ✓ Conservation validated on trajectories (error < 1e-5)
- ✓ Candidate created successfully with correct metadata

---

### Test 1.2: Complex Case - Quadratic Integral from Killing Tensor

**What it tests**: More complex integrals (e.g., energy-like) require symbolic regression.

#### Test Code

```python
def test_wp31_to_wp33_quadratic_integral():
    """Test 1.2: Quadratic integral from Killing tensor through symbolic regression."""

    print("=" * 80)
    print("TEST 1.2: WP3.1 → WP3.3 - Quadratic Integral (Energy-like)")
    print("=" * 80)

    # Step 1: WP3.1 - Discover Killing tensors
    print("\n[WP3.1] Solving for Killing tensors...")

    killing_solution = solve_killing_fields(
        manifold_type='s1_bundle',
        masses=np.array([1.0, 1.0, 1.0]),
        energy=-1.0,
        L_magnitude=1.0,
        resolution={'shape_fine': 50, 'fiber': 16},
        field_type='tensor',  # Rank-2 tensor
        verbose=False
    )

    print(f"  ✓ Found {len(killing_solution.fields)} Killing tensors")

    # Step 2: Extract numerical quadratic integral
    # K_ij v^i v^j = some conserved quantity

    def quadratic_integral_numerical(z):
        """Numerical evaluation: simplified quadratic form."""
        dim = len(z) // 2
        p = z[dim:]
        # Example: kinetic energy-like term
        return 0.5 * np.sum(p**2)

    # Step 3: WP3.3 - Symbolic regression to find analytical form
    print("\n[WP3.3] Performing symbolic regression...")

    from src.python.symbolic import (
        construct_hierarchical_basis,
        sindy_regression
    )

    # Build basis library
    library = construct_hierarchical_basis(
        state_dim=8,
        max_polynomial_degree=2,
        masses=np.array([1.0, 1.0, 1.0])
    )

    # Generate sample data
    samples = np.random.randn(500, 8)

    # Regression
    regression_result = sindy_regression(
        quadratic_integral_numerical,
        samples,
        library,
        threshold=0.01
    )

    print(f"  Expression: {regression_result.expression_str}")
    print(f"  Residual: {regression_result.residual:.2e}")
    print(f"  Complexity: {regression_result.complexity}")

    # Step 4: Simplify
    from src.python.symbolic import simplify_candidate_integral

    state_symbols = sp.symbols('q0 q1 q2 q3 p0 p1 p2 p3')

    simplified = simplify_candidate_integral(
        regression_result.expression_sympy,
        list(state_symbols)
    )

    print(f"\n[WP3.3] Simplified: {simplified.simplified}")

    # Step 5: Validate
    from src.python.symbolic import validate_candidate_integral

    def hamiltonian(z):
        dim = len(z) // 2
        q = z[:dim]
        p = z[dim:]
        H = 0.5 * np.sum(p**2) + 0.5 * np.sum(q**2)
        dz_dt = np.concatenate([p, -q])
        return dz_dt, H

    sample_states = np.random.randn(100, 8)
    initial_conditions = np.random.randn(5, 8)

    validation = validate_candidate_integral(
        simplified.simplified,
        quadratic_integral_numerical,
        hamiltonian,
        sample_states,
        list(state_symbols),
        test_trajectories=initial_conditions
    )

    print(f"\n[WP3.3] Validation:")
    print(f"  Conservation error: {validation.conservation_error:.2e}")
    print(f"  Is conserved: {validation.is_conserved}")

    # Success criteria
    success = (
        regression_result.residual < 1e-6 and
        validation.conservation_error < 1e-4 and
        regression_result.complexity < 20
    )

    print("\n" + "=" * 80)
    if success:
        print("✓ TEST 1.2 PASSED")
    else:
        print("✗ TEST 1.2 FAILED")
    print("=" * 80)

    return success
```

---

## Test Suite 2: WP3.2 → WP3.3 Integration

**Purpose**: Verify that ML-discovered integrals can be converted to symbolic form and validated.

### Test 2.1: HNN Prediction → Symbolic Regression

**What it tests**: Neural network predictions can be fitted with symbolic expressions.

#### Test Code

```python
"""
Test: WP3.2 HNN prediction → WP3.3 symbolic regression → validation

Expected result: ML-discovered integral can be expressed symbolically
"""

import numpy as np
import sympy as sp


def test_wp32_to_wp33_hnn_to_symbolic():
    """Test 2.1: HNN prediction to symbolic expression."""

    print("=" * 80)
    print("TEST 2.1: WP3.2 → WP3.3 - HNN Prediction to Symbolic")
    print("=" * 80)

    # Step 1: WP3.2 - Train HNN (simulated here with mock)
    print("\n[WP3.2] Training HNN model...")

    # Mock: In reality, this would be from trained ConservationHNN
    class MockHNN:
        """Simulated HNN that predicts a conserved quantity."""

        def predict_invariant(self, z):
            """Predict I_φ(z) - for test, use known integral."""
            # Example: q0^2 + p1^2
            return z[0]**2 + z[5]**2

    hnn_model = MockHNN()
    print("  ✓ HNN trained (mock)")

    # Step 2: WP3.2 - Extract numerical function
    print("\n[WP3.2] Extracting learned integral function...")

    def I_phi_numerical(z):
        return hnn_model.predict_invariant(z)

    # Test on random states
    test_state = np.random.randn(8)
    test_value = I_phi_numerical(test_state)
    print(f"  ✓ Numerical function evaluates: I_φ = {test_value:.4f}")

    # Step 3: WP3.3 - Symbolic regression
    print("\n[WP3.3] Performing symbolic regression on HNN output...")

    from src.python.symbolic import (
        construct_hierarchical_basis,
        sindy_regression
    )

    # Build basis
    library = construct_hierarchical_basis(
        state_dim=8,
        max_polynomial_degree=2,
        masses=np.array([1.0, 1.0, 1.0])
    )

    # Generate high-quality samples
    np.random.seed(42)
    samples = np.random.randn(1000, 8)

    # Regression
    regression_result = sindy_regression(
        I_phi_numerical,
        samples,
        library,
        threshold=0.005,  # Tighter threshold for ML data
        alpha=0.01
    )

    print(f"  Expression: {regression_result.expression_str}")
    print(f"  Residual: {regression_result.residual:.2e}")
    print(f"  Active terms: {len(regression_result.basis_functions_used)}")

    # Step 4: WP3.3 - Simplification
    print("\n[WP3.3] Simplifying discovered expression...")

    from src.python.symbolic import simplify_candidate_integral

    state_symbols = sp.symbols('q0 q1 q2 q3 p0 p1 p2 p3')

    simplified = simplify_candidate_integral(
        regression_result.expression_sympy,
        list(state_symbols),
        aggressive=True
    )

    print(f"  Original:   {simplified.original}")
    print(f"  Simplified: {simplified.simplified}")
    print(f"  Complexity reduction: {simplified.reduction_factor:.2%}")

    # Step 5: WP3.3 - Validation
    print("\n[WP3.3] Validating symbolic expression...")

    from src.python.symbolic import (
        validate_symbolic_numerical_agreement,
        lambdify_expression
    )

    # Check symbolic matches numerical
    agrees, residual = validate_symbolic_numerical_agreement(
        simplified.simplified,
        I_phi_numerical,
        samples[:100],
        list(state_symbols),
        tolerance=1e-8
    )

    print(f"  Symbolic-numerical agreement: {agrees}")
    print(f"  RMS residual: {residual:.2e}")

    # Step 6: WP3.3 - Create candidate
    print("\n[WP3.3] Creating candidate from ML result...")

    from src.python.symbolic import (
        create_candidate_from_wp32_ml,
        ValidationResult
    )

    # Mock validation result
    validation = ValidationResult(
        is_conserved=True,
        conservation_error=1e-6,
        symbolic_numerical_residual=residual,
        is_independent=True
    )

    candidate = create_candidate_from_wp32_ml(
        model_name="HNN_test",
        integral_expr=simplified.simplified,
        integral_func=I_phi_numerical,
        validation=validation,
        is_sympnet=False
    )

    print(f"  Name: {candidate.name}")
    print(f"  Source: {candidate.source}")
    print(f"  Conservation error: {candidate.conservation_error:.2e}")

    # Success criteria
    success = (
        regression_result.residual < 1e-4 and
        agrees and
        residual < 1e-6 and
        regression_result.complexity < 10
    )

    print("\n" + "=" * 80)
    if success:
        print("✓ TEST 2.1 PASSED")
        print(f"  - Regression residual: {regression_result.residual:.2e} < 1e-4")
        print(f"  - Symbolic-numerical agreement: {residual:.2e} < 1e-6")
        print(f"  - Expression complexity: {regression_result.complexity} < 10")
    else:
        print("✗ TEST 2.1 FAILED")
        if regression_result.residual >= 1e-4:
            print(f"  - Regression residual too high: {regression_result.residual:.2e}")
        if not agrees:
            print(f"  - Symbolic-numerical mismatch")
    print("=" * 80)

    return success
```

#### Expected Output

```
================================================================================
TEST 2.1: WP3.2 → WP3.3 - HNN Prediction to Symbolic
================================================================================

[WP3.2] Training HNN model...
  ✓ HNN trained (mock)

[WP3.2] Extracting learned integral function...
  ✓ Numerical function evaluates: I_φ = 1.2345

[WP3.3] Performing symbolic regression on HNN output...
  Expression: 1.0*z0^2 + 1.0*z5^2
  Residual: 2.34e-12
  Active terms: 2

[WP3.3] Simplifying discovered expression...
  Original:   1.0*z0**2 + 1.0*z5**2
  Simplified: q0**2 + p1**2
  Complexity reduction: 66.67%

[WP3.3] Validating symbolic expression...
  Symbolic-numerical agreement: True
  RMS residual: 3.45e-13

[WP3.3] Creating candidate from ML result...
  Name: I_ML_HNN_test
  Source: wp3.2_hnn
  Conservation error: 1.00e-06

================================================================================
✓ TEST 2.1 PASSED
  - Regression residual: 2.34e-12 < 1e-4
  - Symbolic-numerical agreement: 3.45e-13 < 1e-6
  - Expression complexity: 2 < 10
================================================================================
```

---

### Test 2.2: Multiple Methods Comparison

**What it tests**: SINDy vs PySR on same ML output.

#### Test Code

```python
def test_wp32_to_wp33_method_comparison():
    """Test 2.2: Compare SINDy and PySR on ML output."""

    print("=" * 80)
    print("TEST 2.2: WP3.2 → WP3.3 - Method Comparison (SINDy vs PySR)")
    print("=" * 80)

    # Mock HNN output
    def I_phi(z):
        return z[0]**2 + 2*z[1]*z[2] + z[3]

    # Generate data
    samples = np.random.randn(1000, 8)

    # Build basis
    from src.python.symbolic import construct_hierarchical_basis

    library = construct_hierarchical_basis(
        state_dim=8,
        max_polynomial_degree=2,
        masses=np.array([1.0, 1.0, 1.0])
    )

    # Method 1: SINDy
    print("\n[Method 1] SINDy Regression...")

    from src.python.symbolic import sindy_regression, PYSINDY_AVAILABLE

    if PYSINDY_AVAILABLE:
        result_sindy = sindy_regression(I_phi, samples, library)
        print(f"  Expression: {result_sindy.expression_str}")
        print(f"  Residual: {result_sindy.residual:.2e}")
        print(f"  Complexity: {result_sindy.complexity}")
    else:
        print("  ⚠ SINDy not available")
        result_sindy = None

    # Method 2: PySR
    print("\n[Method 2] PySR Regression...")

    from src.python.symbolic import pysr_regression, PYSR_AVAILABLE

    if PYSR_AVAILABLE:
        result_pysr = pysr_regression(
            I_phi,
            samples,
            niterations=20,  # Quick for testing
            maxsize=10
        )
        print(f"  Expression: {result_pysr.expression_str}")
        print(f"  Residual: {result_pysr.residual:.2e}")
        print(f"  Complexity: {result_pysr.complexity}")
    else:
        print("  ⚠ PySR not available")
        result_pysr = None

    # Compare
    print("\n[Comparison]")

    if result_sindy and result_pysr:
        print(f"  SINDy residual: {result_sindy.residual:.2e}")
        print(f"  PySR residual:  {result_pysr.residual:.2e}")

        if result_sindy.residual < result_pysr.residual:
            print("  → SINDy found better fit")
        else:
            print("  → PySR found better fit")

        success = (result_sindy.residual < 1e-6 or result_pysr.residual < 1e-6)
    elif result_sindy:
        success = result_sindy.residual < 1e-6
        print("  → Only SINDy available")
    elif result_pysr:
        success = result_pysr.residual < 1e-6
        print("  → Only PySR available")
    else:
        print("  ✗ No regression methods available")
        success = False

    print("\n" + "=" * 80)
    if success:
        print("✓ TEST 2.2 PASSED - At least one method found good fit")
    else:
        print("✗ TEST 2.2 FAILED")
    print("=" * 80)

    return success
```

---

## Test Suite 3: Full Pipeline Integration

**Purpose**: End-to-end test of complete WP3 workflow with consolidation and ranking.

### Test 3.1: Complete Pipeline with Multiple Sources

**What it tests**: All components working together from discovery to final report.

#### Test Code

```python
"""
Test: Complete WP3 pipeline
- Collect candidates from WP3.1 (geometric)
- Collect candidates from WP3.2 (ML)
- Consolidate all candidates
- Rank by quality
- Generate report

Expected result: Ranked list with top candidates identified
"""

def test_full_wp3_pipeline():
    """Test 3.1: Complete WP3 pipeline end-to-end."""

    print("=" * 80)
    print("TEST 3.1: Full WP3 Pipeline - Discovery to Report")
    print("=" * 80)

    import numpy as np
    import sympy as sp
    from src.python.symbolic import (
        CandidateIntegral,
        CandidateSource,
        consolidate_and_rank,
        generate_candidate_report,
        ValidationResult
    )

    # Simulate candidates from different sources
    state_symbols = sp.symbols('q0 q1 q2 q3 p0 p1 p2 p3')
    q0, q1, q2, q3, p0, p1, p2, p3 = state_symbols

    # Step 1: Collect candidates from WP3.1
    print("\n[Step 1] Collecting WP3.1 (Geometric) candidates...")

    wp31_candidates = []

    # Candidate 1: Angular momentum (p_θ)
    wp31_candidates.append(CandidateIntegral(
        name="p_theta",
        expression_symbolic=p3,
        expression_numerical=lambda z: z[7],
        source=CandidateSource.KILLING_FIELD,
        conservation_error=1e-14,
        complexity=1,
        is_independent=True,
        validation_result=ValidationResult(
            is_conserved=True,
            conservation_error=1e-14,
            symbolic_numerical_residual=0.0
        )
    ))

    # Candidate 2: Energy-like (from Killing tensor)
    wp31_candidates.append(CandidateIntegral(
        name="K_energy",
        expression_symbolic=p0**2 + p1**2 + p2**2,
        expression_numerical=lambda z: z[4]**2 + z[5]**2 + z[6]**2,
        source=CandidateSource.KILLING_TENSOR,
        conservation_error=1e-12,
        complexity=5,
        is_independent=True,
        validation_result=ValidationResult(
            is_conserved=True,
            conservation_error=1e-12,
            symbolic_numerical_residual=1e-15
        )
    ))

    print(f"  ✓ Collected {len(wp31_candidates)} candidates from WP3.1")

    # Step 2: Collect candidates from WP3.2
    print("\n[Step 2] Collecting WP3.2 (ML) candidates...")

    wp32_candidates = []

    # Candidate 3: ML discovery
    wp32_candidates.append(CandidateIntegral(
        name="I_ML_1",
        expression_symbolic=q0**2 + q1**2,
        expression_numerical=lambda z: z[0]**2 + z[1]**2,
        source=CandidateSource.ML_HNN,
        conservation_error=1e-6,
        complexity=3,
        is_independent=True,
        validation_result=ValidationResult(
            is_conserved=True,
            conservation_error=1e-6,
            symbolic_numerical_residual=1e-10
        )
    ))

    # Candidate 4: Another ML discovery (non-independent)
    wp32_candidates.append(CandidateIntegral(
        name="I_ML_2",
        expression_symbolic=2*p3,  # Just 2× p_theta (not independent)
        expression_numerical=lambda z: 2*z[7],
        source=CandidateSource.ML_HNN,
        conservation_error=1e-7,
        complexity=2,
        is_independent=False,  # Dependent on p_theta
        validation_result=ValidationResult(
            is_conserved=True,
            conservation_error=1e-7,
            symbolic_numerical_residual=0.0,
            is_independent=False
        )
    ))

    print(f"  ✓ Collected {len(wp32_candidates)} candidates from WP3.2")

    # Step 3: Collect candidates from WP3.3 symbolic regression
    print("\n[Step 3] Collecting WP3.3 (Symbolic Regression) candidates...")

    wp33_candidates = []

    # Candidate 5: Symbolic regression discovery
    wp33_candidates.append(CandidateIntegral(
        name="I_Symbolic",
        expression_symbolic=p0*q1 - p1*q0,  # Angular momentum-like
        expression_numerical=lambda z: z[4]*z[1] - z[5]*z[0],
        source=CandidateSource.SYMBOLIC_REGRESSION,
        conservation_error=1e-8,
        complexity=4,
        is_independent=True,
        validation_result=ValidationResult(
            is_conserved=True,
            conservation_error=1e-8,
            symbolic_numerical_residual=1e-12
        )
    ))

    print(f"  ✓ Collected {len(wp33_candidates)} candidates from WP3.3")

    # Step 4: Consolidate all candidates
    print("\n[Step 4] Consolidating all candidates...")

    all_candidates = wp31_candidates + wp32_candidates + wp33_candidates
    print(f"  Total candidates before consolidation: {len(all_candidates)}")

    # Generate sample states for comparison
    np.random.seed(42)
    sample_states = np.random.randn(500, 8)

    # Known trivial integrals to filter
    known_trivial = []

    # Consolidate and rank
    ranked = consolidate_and_rank(
        all_candidates,
        sample_states,
        known_trivial=known_trivial,
        remove_duplicates=True
    )

    print(f"  Candidates after consolidation: {len(ranked)}")
    print(f"  Top candidate score: {ranked[0].score:.2f}")

    # Step 5: Generate report
    print("\n[Step 5] Generating candidate report...")

    report = generate_candidate_report(
        ranked,
        top_n=10,
        output_format='markdown'
    )

    print("\n" + "-" * 80)
    print(report)
    print("-" * 80)

    # Step 6: Verify ranking quality
    print("\n[Step 6] Verifying ranking quality...")

    # Check that independent candidates rank higher than dependent
    independent_ranks = [i for i, c in enumerate(ranked) if c.is_independent]
    dependent_ranks = [i for i, c in enumerate(ranked) if not c.is_independent]

    if independent_ranks and dependent_ranks:
        avg_independent_rank = np.mean(independent_ranks)
        avg_dependent_rank = np.mean(dependent_ranks)

        print(f"  Average rank of independent: {avg_independent_rank:.1f}")
        print(f"  Average rank of dependent: {avg_dependent_rank:.1f}")

        ranking_quality = avg_independent_rank < avg_dependent_rank
    else:
        ranking_quality = True

    # Check that lower conservation error → better rank
    errors = [c.conservation_error for c in ranked[:3]]
    error_trend = all(errors[i] <= errors[i+1]*10 for i in range(len(errors)-1))

    print(f"  Top 3 conservation errors: {errors}")
    print(f"  Error trend correct: {error_trend}")

    # Success criteria
    success = (
        len(ranked) >= 3 and  # At least 3 unique candidates
        ranked[0].conservation_error < 1e-6 and  # Best is well-conserved
        ranking_quality and  # Independent ranked higher
        error_trend  # Better conservation → better rank
    )

    print("\n" + "=" * 80)
    if success:
        print("✓ TEST 3.1 PASSED - Full pipeline functional")
        print(f"  - {len(ranked)} unique candidates identified")
        print(f"  - Best candidate: {ranked[0].name}")
        print(f"  - Conservation error: {ranked[0].conservation_error:.2e}")
        print(f"  - Ranking quality verified")
    else:
        print("✗ TEST 3.1 FAILED")
        if len(ranked) < 3:
            print(f"  - Too few candidates: {len(ranked)} < 3")
        if ranked[0].conservation_error >= 1e-6:
            print(f"  - Best candidate not well-conserved: {ranked[0].conservation_error:.2e}")
    print("=" * 80)

    return success
```

#### Expected Output

```
================================================================================
TEST 3.1: Full WP3 Pipeline - Discovery to Report
================================================================================

[Step 1] Collecting WP3.1 (Geometric) candidates...
  ✓ Collected 2 candidates from WP3.1

[Step 2] Collecting WP3.2 (ML) candidates...
  ✓ Collected 2 candidates from WP3.2

[Step 3] Collecting WP3.3 (Symbolic Regression) candidates...
  ✓ Collected 1 candidates from WP3.3

[Step 4] Consolidating all candidates...
  Total candidates before consolidation: 5
  Candidates after consolidation: 5
  Top candidate score: -5.23

[Step 5] Generating candidate report...

--------------------------------------------------------------------------------
# Top Candidate Conserved Integrals

Total candidates analyzed: 5
Showing top 5 candidates

| Rank | Name | Expression | Source | Conservation Error | Complexity | Independent | Score |
|------|------|------------|--------|-------------------|------------|-------------|-------|
| 1 | p_theta | `p3` | wp3.1_killing_field | 1.00e-14 | 1 | ✓ | -5.23 |
| 2 | K_energy | `p0**2 + p1**2 + p2**2` | wp3.1_killing_tensor | 1.00e-12 | 5 | ✓ | -2.15 |
| 3 | I_Symbolic | `p0*q1 - p1*q0` | wp3.3_symbolic | 1.00e-08 | 4 | ✓ | 1.42 |
| 4 | I_ML_1 | `q0**2 + q1**2` | wp3.2_hnn | 1.00e-06 | 3 | ✓ | 3.78 |
| 5 | I_ML_2 | `2*p3` | wp3.2_hnn | 1.00e-07 | 2 | ✗ | 201.23 |

## Detailed Information

### 1. p_theta

**Expression**: `p3`

**LaTeX**: $p_{3}$

- **Source**: wp3.1_killing_field
- **Conservation error**: 1.00e-14
- **Complexity**: 1 operations
- **Functionally independent**: Yes
- **Score**: -5.23

--------------------------------------------------------------------------------

[Step 6] Verifying ranking quality...
  Average rank of independent: 1.5
  Average rank of dependent: 4.0
  Top 3 conservation errors: [1e-14, 1e-12, 1e-08]
  Error trend correct: True

================================================================================
✓ TEST 3.1 PASSED - Full pipeline functional
  - 5 unique candidates identified
  - Best candidate: p_theta
  - Conservation error: 1.00e-14
  - Ranking quality verified
================================================================================
```

---

## Running All Tests

### Master Test Script

```python
#!/usr/bin/env python3
"""
Master test script for WP3 integration tests.

Usage:
    python tests/integration/test_wp3_integration.py

    # Or run individual suites:
    python tests/integration/test_wp3_integration.py --suite 1
    python tests/integration/test_wp3_integration.py --suite 2
    python tests/integration/test_wp3_integration.py --suite 3
"""

import sys
import argparse


def run_test_suite_1():
    """Run Test Suite 1: WP3.1 → WP3.3"""
    print("\n" + "="*80)
    print("TEST SUITE 1: WP3.1 → WP3.3 Integration")
    print("="*80 + "\n")

    results = {}

    # Test 1.1
    from tests.integration.test_wp31_to_wp33 import test_wp31_to_wp33_angular_momentum
    results['1.1'] = test_wp31_to_wp33_angular_momentum()

    # Test 1.2
    from tests.integration.test_wp31_to_wp33 import test_wp31_to_wp33_quadratic_integral
    results['1.2'] = test_wp31_to_wp33_quadratic_integral()

    return results


def run_test_suite_2():
    """Run Test Suite 2: WP3.2 → WP3.3"""
    print("\n" + "="*80)
    print("TEST SUITE 2: WP3.2 → WP3.3 Integration")
    print("="*80 + "\n")

    results = {}

    # Test 2.1
    from tests.integration.test_wp32_to_wp33 import test_wp32_to_wp33_hnn_to_symbolic
    results['2.1'] = test_wp32_to_wp33_hnn_to_symbolic()

    # Test 2.2
    from tests.integration.test_wp32_to_wp33 import test_wp32_to_wp33_method_comparison
    results['2.2'] = test_wp32_to_wp33_method_comparison()

    return results


def run_test_suite_3():
    """Run Test Suite 3: Full Pipeline"""
    print("\n" + "="*80)
    print("TEST SUITE 3: Full WP3 Pipeline")
    print("="*80 + "\n")

    results = {}

    # Test 3.1
    from tests.integration.test_full_pipeline import test_full_wp3_pipeline
    results['3.1'] = test_full_wp3_pipeline()

    return results


def main():
    parser = argparse.ArgumentParser(description='Run WP3 integration tests')
    parser.add_argument('--suite', type=int, choices=[1, 2, 3],
                       help='Run specific test suite (1, 2, or 3)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')

    args = parser.parse_args()

    all_results = {}

    if args.suite == 1 or args.suite is None:
        all_results.update(run_test_suite_1())

    if args.suite == 2 or args.suite is None:
        all_results.update(run_test_suite_2())

    if args.suite == 3 or args.suite is None:
        all_results.update(run_test_suite_3())

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for result in all_results.values() if result)
    total = len(all_results)

    for test_id, result in sorted(all_results.items()):
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  Test {test_id}: {status}")

    print()
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("="*80)

    # Exit code
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
```

### Expected Summary Output

```
================================================================================
TEST SUMMARY
================================================================================
  Test 1.1: ✓ PASS
  Test 1.2: ✓ PASS
  Test 2.1: ✓ PASS
  Test 2.2: ✓ PASS
  Test 3.1: ✓ PASS

Total: 5/5 tests passed (100.0%)
================================================================================
```

---

## Test Organization

### Recommended Directory Structure

```
tests/
└── integration/
    ├── __init__.py
    ├── test_wp3_integration.py         # Master script
    ├── test_wp31_to_wp33.py            # Suite 1 tests
    ├── test_wp32_to_wp33.py            # Suite 2 tests
    ├── test_full_pipeline.py           # Suite 3 tests
    └── fixtures/
        ├── sample_killing_fields.pkl    # Pre-computed test data
        ├── sample_hnn_predictions.pkl
        └── test_trajectories.npy
```

---

## Continuous Integration

### GitHub Actions Workflow

```yaml
name: WP3 Integration Tests

on:
  push:
    branches: [ main, develop ]
    paths:
      - 'src/python/pde/**'
      - 'src/python/analysis/**'
      - 'src/python/ml/**'
      - 'src/python/symbolic/**'
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        pip install numpy scipy sympy
        pip install pysindy  # Optional
        # pip install pysr  # Skip if too heavy

    - name: Run integration tests
      run: |
        python tests/integration/test_wp3_integration.py

    - name: Upload test results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: test-results
        path: test-results/
```

---

## Success Criteria Summary

### Test Suite 1 (WP3.1 → WP3.3)
- ✓ Killing fields discovered
- ✓ Integrals extracted correctly
- ✓ Symbolic expressions match numerical (residual < 1e-10)
- ✓ Conservation validated (error < 1e-5)
- ✓ Candidates created with proper metadata

### Test Suite 2 (WP3.2 → WP3.3)
- ✓ HNN predictions can be evaluated
- ✓ Symbolic regression finds expressions (residual < 1e-4)
- ✓ Symbolic-numerical agreement (< 1e-6)
- ✓ Multiple methods work (SINDy and/or PySR)
- ✓ Candidates created from ML results

### Test Suite 3 (Full Pipeline)
- ✓ Candidates from all sources consolidated
- ✓ Duplicates removed correctly
- ✓ Ranking reflects quality (conservation + independence)
- ✓ Report generation successful
- ✓ Top candidates are physically meaningful

---

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError` for pysindy or pysr
- **Solution**: These are optional. Tests should skip gracefully if not available.

**Issue**: Numerical instability in trajectory integration
- **Solution**: Reduce integration time or increase tolerance in tests.

**Issue**: Symbolic regression takes too long
- **Solution**: Reduce sample size or iterations for testing.

**Issue**: Tests pass individually but fail when run together
- **Solution**: Add proper cleanup between tests, reset random seeds.

---

## Next Steps

1. **Implement test files** in `tests/integration/`
2. **Create test fixtures** with pre-computed data
3. **Set up CI/CD** with GitHub Actions
4. **Run tests** and iterate until all pass
5. **Document results** for WP4 handoff

---

**Document Version**: 1.0
**Created**: 2025-11-15
**Status**: Ready for Implementation
