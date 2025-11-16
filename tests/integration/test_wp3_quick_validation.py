#!/usr/bin/env python3
"""
Quick validation test for WP3 integration.

This is a simplified test that validates the basic functionality of the
WP3.1 → WP3.3 and WP3.2 → WP3.3 pipelines without requiring extensive
computation or external data.

Usage:
    python tests/integration/test_wp3_quick_validation.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import numpy as np
import sympy as sp


def test_basic_imports():
    """Test 0: Verify all WP3 modules can be imported."""
    print("=" * 80)
    print("TEST 0: Module Import Validation")
    print("=" * 80)

    try:
        # WP3.1 modules
        from src.python.geometry import lifted_jm_metric
        from src.python.pde import killing_solver
        from src.python.analysis import integral_from_killing
        print("  ✓ WP3.1 modules imported")

        # WP3.2 modules
        from src.python.ml import hnn_architecture
        from src.python.ml import conservation_training
        print("  ✓ WP3.2 modules imported")

        # WP3.3 modules
        from src.python.symbolic import (
            construct_hierarchical_basis,
            sindy_regression,
            simplify_candidate_integral,
            validate_candidate_integral,
            consolidate_and_rank,
            generate_candidate_report,
            CandidateIntegral,
            CandidateSource,
            PYSINDY_AVAILABLE,
            PYSR_AVAILABLE
        )
        print("  ✓ WP3.3 modules imported")

        print(f"\n  Optional dependencies:")
        print(f"    - PySINDy: {'✓ Available' if PYSINDY_AVAILABLE else '✗ Not installed'}")
        print(f"    - PySR:    {'✓ Available' if PYSR_AVAILABLE else '✗ Not installed'}")

        print("\n✓ TEST 0 PASSED - All modules import successfully\n")
        return True

    except ImportError as e:
        print(f"\n✗ TEST 0 FAILED - Import error: {e}\n")
        return False


def test_basis_construction():
    """Test 1: Verify basis function construction works."""
    print("=" * 80)
    print("TEST 1: Basis Function Construction")
    print("=" * 80)

    try:
        from src.python.symbolic import construct_hierarchical_basis

        # Build basis library
        library = construct_hierarchical_basis(
            state_dim=4,
            max_polynomial_degree=2,
            masses=np.array([1.0, 1.0, 1.0]),
            include_transcendental=False,
            include_conservation=True
        )

        print(f"  ✓ Basis library created")
        print(f"    - Total functions: {len(library.functions)}")
        print(f"    - State dimension: 4")
        print(f"    - Max degree: 2")

        # Test evaluation
        test_state = np.random.randn(4)
        features = library.evaluate_library(test_state)

        print(f"  ✓ Evaluation successful")
        print(f"    - Features shape: {features.shape}")
        print(f"    - Sample values: {features[:5]}")

        success = len(library.functions) > 0 and features.shape[0] == len(library.functions)

        if success:
            print("\n✓ TEST 1 PASSED\n")
        else:
            print("\n✗ TEST 1 FAILED - Unexpected output\n")

        return success

    except Exception as e:
        print(f"\n✗ TEST 1 FAILED - Error: {e}\n")
        return False


def test_symbolic_regression_basic():
    """Test 2: Verify symbolic regression works on known function."""
    print("=" * 80)
    print("TEST 2: Basic Symbolic Regression")
    print("=" * 80)

    try:
        from src.python.symbolic import (
            construct_hierarchical_basis,
            sindy_regression,
            PYSINDY_AVAILABLE
        )

        if not PYSINDY_AVAILABLE:
            print("  ⚠ PySINDy not available - skipping test\n")
            return True  # Not a failure, just skipped

        # Define known integral: I = z0^2 + z1^2
        def known_integral(z):
            return z[0]**2 + z[1]**2

        # Generate sample data
        np.random.seed(42)
        samples = np.random.randn(500, 4)

        # Build basis
        library = construct_hierarchical_basis(
            state_dim=4,
            max_polynomial_degree=2,
            masses=np.array([1.0, 1.0, 1.0])
        )

        print(f"  ✓ Generated {len(samples)} samples")
        print(f"  ✓ Basis library: {len(library.functions)} functions")

        # Regression
        result = sindy_regression(
            known_integral,
            samples,
            library,
            threshold=0.01
        )

        print(f"\n  Regression results:")
        print(f"    - Expression: {result.expression_str}")
        print(f"    - Residual: {result.residual:.2e}")
        print(f"    - Complexity: {result.complexity}")
        print(f"    - Active terms: {len(result.basis_functions_used)}")

        # Success if residual is very small
        success = result.residual < 1e-6

        if success:
            print("\n✓ TEST 2 PASSED - Regression found accurate expression\n")
        else:
            print(f"\n✗ TEST 2 FAILED - Residual too high: {result.residual:.2e}\n")

        return success

    except Exception as e:
        print(f"\n✗ TEST 2 FAILED - Error: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_simplification():
    """Test 3: Verify expression simplification works."""
    print("=" * 80)
    print("TEST 3: Expression Simplification")
    print("=" * 80)

    try:
        from src.python.symbolic import simplify_candidate_integral

        # Create test expression
        q0, q1, p0, p1 = sp.symbols('q0 q1 p0 p1')
        expr = q0**2 + 2*q0*q1 + q1**2  # Should factor to (q0 + q1)^2

        print(f"  Original expression: {expr}")

        # Simplify
        result = simplify_candidate_integral(
            expr,
            [q0, q1, p0, p1],
            aggressive=True
        )

        print(f"  Simplified: {result.simplified}")
        print(f"  Reduction factor: {result.reduction_factor:.2f}")
        print(f"  Steps: {len(result.simplification_steps)}")

        # Check if simplified (should be (q0 + q1)^2 or equivalent)
        from src.python.symbolic import count_operations

        original_ops = count_operations(result.original)
        simplified_ops = count_operations(result.simplified)

        print(f"\n  Operations: {original_ops} → {simplified_ops}")

        success = simplified_ops <= original_ops

        if success:
            print("\n✓ TEST 3 PASSED - Simplification successful\n")
        else:
            print("\n✗ TEST 3 FAILED - Simplification increased complexity\n")

        return success

    except Exception as e:
        print(f"\n✗ TEST 3 FAILED - Error: {e}\n")
        return False


def test_validation():
    """Test 4: Verify conservation validation works."""
    print("=" * 80)
    print("TEST 4: Conservation Validation")
    print("=" * 80)

    try:
        from src.python.symbolic import (
            validate_symbolic_numerical_agreement,
            lambdify_expression
        )

        # Define symbolic and numerical versions of same function
        q, p = sp.symbols('q p')
        expr_sym = q**2 + p**2

        def expr_num(z):
            return z[0]**2 + z[1]**2

        # Generate test states
        samples = np.random.randn(100, 2)

        print(f"  Testing agreement on {len(samples)} samples...")

        # Validate
        agrees, residual = validate_symbolic_numerical_agreement(
            expr_sym,
            expr_num,
            samples,
            [q, p],
            tolerance=1e-10
        )

        print(f"\n  Results:")
        print(f"    - Agreement: {agrees}")
        print(f"    - RMS residual: {residual:.2e}")

        success = agrees and residual < 1e-10

        if success:
            print("\n✓ TEST 4 PASSED - Validation successful\n")
        else:
            print(f"\n✗ TEST 4 FAILED - Validation failed\n")

        return success

    except Exception as e:
        print(f"\n✗ TEST 4 FAILED - Error: {e}\n")
        return False


def test_candidate_ranking():
    """Test 5: Verify candidate ranking and consolidation."""
    print("=" * 80)
    print("TEST 5: Candidate Ranking and Consolidation")
    print("=" * 80)

    try:
        from src.python.symbolic import (
            CandidateIntegral,
            CandidateSource,
            consolidate_and_rank,
            generate_candidate_report,
            ValidationResult
        )

        # Create mock candidates
        q0, q1, p0, p1 = sp.symbols('q0 q1 p0 p1')

        candidates = [
            # Good candidate
            CandidateIntegral(
                name="Good_1",
                expression_symbolic=p0**2 + p1**2,
                expression_numerical=lambda z: z[2]**2 + z[3]**2,
                source=CandidateSource.KILLING_FIELD,
                conservation_error=1e-12,
                complexity=3,
                is_independent=True,
                validation_result=ValidationResult(
                    is_conserved=True,
                    conservation_error=1e-12,
                    symbolic_numerical_residual=0.0
                )
            ),
            # Medium candidate
            CandidateIntegral(
                name="Medium_1",
                expression_symbolic=q0*p1 - q1*p0,
                expression_numerical=lambda z: z[0]*z[3] - z[1]*z[2],
                source=CandidateSource.ML_HNN,
                conservation_error=1e-6,
                complexity=4,
                is_independent=True,
                validation_result=ValidationResult(
                    is_conserved=True,
                    conservation_error=1e-6,
                    symbolic_numerical_residual=1e-10
                )
            ),
            # Poor candidate (not independent)
            CandidateIntegral(
                name="Poor_1",
                expression_symbolic=2*p0,
                expression_numerical=lambda z: 2*z[2],
                source=CandidateSource.SYMBOLIC_REGRESSION,
                conservation_error=1e-8,
                complexity=2,
                is_independent=False,
                validation_result=ValidationResult(
                    is_conserved=True,
                    conservation_error=1e-8,
                    symbolic_numerical_residual=0.0,
                    is_independent=False
                )
            ),
        ]

        print(f"  Created {len(candidates)} mock candidates")

        # Consolidate and rank
        samples = np.random.randn(100, 4)

        ranked = consolidate_and_rank(
            candidates,
            samples,
            remove_duplicates=False
        )

        print(f"\n  Ranking results:")
        for i, cand in enumerate(ranked):
            print(f"    {i+1}. {cand.name}: score={cand.score:.2f}, "
                  f"error={cand.conservation_error:.2e}, "
                  f"indep={cand.is_independent}")

        # Generate report
        report = generate_candidate_report(ranked, top_n=3, output_format='plain')
        print(f"\n  Report generated ({len(report)} characters)")

        # Check ranking quality
        # Best candidate should have lowest conservation error among independent ones
        independent = [c for c in ranked if c.is_independent]

        if len(independent) > 0:
            best_independent = independent[0]
            success = best_independent.conservation_error < 1e-6
        else:
            success = False

        if success:
            print("\n✓ TEST 5 PASSED - Ranking successful\n")
        else:
            print("\n✗ TEST 5 FAILED - Ranking quality issues\n")

        return success

    except Exception as e:
        print(f"\n✗ TEST 5 FAILED - Error: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all quick validation tests."""
    print("\n" + "="*80)
    print("WP3 INTEGRATION - QUICK VALIDATION TESTS")
    print("="*80 + "\n")

    results = {
        'Test 0': test_basic_imports(),
        'Test 1': test_basis_construction(),
        'Test 2': test_symbolic_regression_basic(),
        'Test 3': test_simplification(),
        'Test 4': test_validation(),
        'Test 5': test_candidate_ranking(),
    }

    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {test_name}: {status}")

    print()
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("=" * 80)

    # Exit code
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
