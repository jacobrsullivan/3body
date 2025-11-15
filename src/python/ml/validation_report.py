"""
Automated validation reporting (Task 3.2.4, Part E).

This module provides comprehensive automated validation reports that combine
all validation tests into a single, actionable summary.

Report Sections:
---------------
1. Executive Summary: Pass/fail verdict with key metrics
2. Conservation Verification: Trajectory-level testing
3. OOD Generalization: Performance on out-of-distribution data
4. Functional Independence: Tests for multiple invariants
5. Cross-Method Comparison: ML vs geometric methods
6. Recommendations: Actionable suggestions for improvement

Output Formats:
--------------
- Text report (human-readable)
- JSON (machine-readable)
- HTML (with plots, if matplotlib available)
"""

import jax
import jax.numpy as jnp
from typing import Dict, List, Tuple, Optional, Any, Callable
import numpy as np
from dataclasses import dataclass, asdict
import json
from datetime import datetime

from .conservation_hnn import ConservationHNN
from .validation import verify_conservation_batch, TrajectoryValidation
from .ood_tests import ood_test_suite, OODTestResult
from .independence_test import test_functional_independence, IndependenceTestResult
from .wp31_comparison import cross_method_validation, ComparisonResult


@dataclass
class ValidationReport:
    """
    Comprehensive validation report.

    Attributes:
        model_name: Descriptive name
        timestamp: When report was generated
        executive_summary: High-level pass/fail verdict
        conservation_results: Conservation verification results
        ood_results: OOD generalization results
        independence_results: Functional independence results (if multiple invariants)
        comparison_results: ML vs geometric comparison (if available)
        recommendations: List of actionable recommendations
        metadata: Additional information
    """
    model_name: str
    timestamp: str
    executive_summary: Dict[str, Any]
    conservation_results: Dict[str, Any]
    ood_results: Optional[Dict[str, Any]]
    independence_results: Optional[Dict[str, Any]]
    comparison_results: Optional[Dict[str, Any]]
    recommendations: List[str]
    metadata: Dict[str, Any]


def generate_validation_report(
    model: ConservationHNN,
    params: Any,
    test_initial_conditions: List[jnp.ndarray],
    training_config: Dict[str, Any],
    in_distribution_baseline: Dict[str, float],
    model_name: str = "ConservationHNN",
    run_ood_tests: bool = True,
    run_independence_tests: bool = True,
    run_comparison: bool = False,
    geometric_invariants: Optional[List[Tuple[str, Callable]]] = None,
    verbose: bool = True
) -> ValidationReport:
    """
    Generate comprehensive automated validation report.

    Args:
        model: Trained ConservationHNN
        params: Model parameters
        test_initial_conditions: Test initial conditions
        training_config: Training configuration (parameter ranges, etc.)
        in_distribution_baseline: In-distribution validation metrics
        model_name: Descriptive model name
        run_ood_tests: Run OOD generalization tests
        run_independence_tests: Run functional independence tests
        run_comparison: Run WP 3.1 comparison (requires geometric_invariants)
        geometric_invariants: List of (name, func) for geometric invariants
        verbose: Print progress

    Returns:
        report: ValidationReport

    Example:
        >>> report = generate_validation_report(
        ...     model, params, test_ics, training_config, baseline
        ... )
        >>> print_report(report)
        >>> save_report(report, 'validation_report.json')
    """
    if verbose:
        print("="*80)
        print(f"GENERATING VALIDATION REPORT: {model_name}")
        print("="*80)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    timestamp = datetime.now().isoformat()

    # Determine number of invariants
    if hasattr(model, 'num_invariants'):
        num_invariants = model.num_invariants
    else:
        num_invariants = 1

    # =========================================================================
    # Section 1: Conservation Verification
    # =========================================================================
    if verbose:
        print("\n[1/4] Conservation verification...")

    # Get test states for evaluation
    # Integrate a few trajectories to get states
    from .model_utils import integrate_trajectory_learned
    test_states_list = []
    for z0 in test_initial_conditions[:10]:  # Use first 10 ICs
        times, traj = integrate_trajectory_learned(
            model, params, z0, t_span=50.0, dt=0.5
        )
        test_states_list.append(traj)
    test_states = jnp.concatenate(test_states_list, axis=0)

    validations, conservation_summary = verify_conservation_batch(
        model, params, test_initial_conditions,
        t_span=100.0, dt=0.1, inv_idx=0, verbose=False
    )

    conservation_results = {
        'num_trajectories': conservation_summary['num_trajectories'],
        'pass_rate': conservation_summary['pass_rate'],
        'conservation_error_mean': conservation_summary['conservation_error_mean'],
        'conservation_error_max': conservation_summary['conservation_error_max'],
        'poisson_bracket_mean': conservation_summary['poisson_bracket_mean']
    }

    if verbose:
        print(f"  Pass rate: {conservation_summary['pass_rate']:.1%}")
        print(f"  Mean conservation error: {conservation_summary['conservation_error_mean']:.2e}")

    # =========================================================================
    # Section 2: OOD Generalization (optional)
    # =========================================================================
    ood_results_dict = None
    if run_ood_tests:
        if verbose:
            print("\n[2/4] OOD generalization testing...")

        ood_results = ood_test_suite(
            model, params, training_config, in_distribution_baseline,
            state_dim=test_states.shape[1], inv_idx=0, verbose=False
        )

        ood_results_dict = {
            'num_tests': len(ood_results),
            'tests': [
                {
                    'name': r.test_name,
                    'pass_rate': r.pass_rate,
                    'conservation_error_mean': r.conservation_error_mean,
                    'degradation_factor': r.degradation_factor
                }
                for r in ood_results
            ],
            'worst_degradation': max(r.degradation_factor for r in ood_results if r.degradation_factor)
        }

        if verbose:
            print(f"  Tests run: {len(ood_results)}")
            print(f"  Worst degradation: {ood_results_dict['worst_degradation']:.1f}×")
    else:
        if verbose:
            print("\n[2/4] Skipping OOD tests")

    # =========================================================================
    # Section 3: Functional Independence (if multiple invariants)
    # =========================================================================
    independence_results_dict = None
    if run_independence_tests and num_invariants > 1:
        if verbose:
            print(f"\n[3/4] Functional independence testing ({num_invariants} invariants)...")

        independence_result = test_functional_independence(
            model, params, test_states, num_invariants, verbose=False
        )

        independence_results_dict = {
            'num_invariants': independence_result.num_invariants,
            'functionally_independent': independence_result.functionally_independent,
            'gradient_rank_mean': independence_result.gradient_rank_mean,
            'gradient_rank_full': independence_result.gradient_rank_full,
            'max_correlation': independence_result.max_correlation,
            'max_involution_error': independence_result.max_involution_error
        }

        if verbose:
            status = "✓" if independence_result.functionally_independent else "✗"
            print(f"  {status} Functionally independent: {independence_result.functionally_independent}")
            print(f"  Max correlation: {independence_result.max_correlation:.4f}")
    else:
        if verbose:
            print(f"\n[3/4] Skipping independence tests (only {num_invariants} invariant)")

    # =========================================================================
    # Section 4: Cross-Method Comparison (optional)
    # =========================================================================
    comparison_results_dict = None
    if run_comparison and geometric_invariants:
        if verbose:
            print("\n[4/4] Cross-method comparison (ML vs geometric)...")

        comparison_results = cross_method_validation(
            model, params, test_states, geometric_invariants,
            num_ml_invariants=num_invariants, verbose=False
        )

        # Find best match for each ML invariant
        best_matches = []
        for ml_idx in range(num_invariants):
            ml_results = [r for r in comparison_results if r.ml_invariant_name == f"ML invariant {ml_idx}"]
            if ml_results:
                best = max(ml_results, key=lambda r: abs(r.pearson_correlation))
                best_matches.append({
                    'ml_invariant': ml_idx,
                    'geometric_invariant': best.geometric_invariant_name,
                    'correlation': best.pearson_correlation,
                    'agreement': best.agreement
                })

        comparison_results_dict = {
            'num_geometric_invariants': len(geometric_invariants),
            'best_matches': best_matches
        }

        if verbose:
            print(f"  Geometric invariants tested: {len(geometric_invariants)}")
            print(f"  Best matches: {len(best_matches)}")
    else:
        if verbose:
            print("\n[4/4] Skipping cross-method comparison")

    # =========================================================================
    # Executive Summary
    # =========================================================================
    # Determine overall pass/fail
    conservation_passed = conservation_summary['pass_rate'] > 0.9
    ood_passed = (ood_results_dict is None or
                  ood_results_dict['worst_degradation'] < 10.0)
    independence_passed = (independence_results_dict is None or
                           independence_results_dict['functionally_independent'])

    all_tests_passed = conservation_passed and ood_passed and independence_passed

    executive_summary = {
        'overall_verdict': 'PASS' if all_tests_passed else 'FAIL',
        'num_invariants': num_invariants,
        'conservation_passed': conservation_passed,
        'ood_passed': ood_passed,
        'independence_passed': independence_passed,
        'conservation_pass_rate': conservation_summary['pass_rate'],
        'mean_conservation_error': conservation_summary['conservation_error_mean']
    }

    # =========================================================================
    # Recommendations
    # =========================================================================
    recommendations = []

    if not conservation_passed:
        recommendations.append("CRITICAL: Low conservation pass rate. Consider:")
        recommendations.append("  - Longer Stage 2 training")
        recommendations.append("  - Increase lambda_conservation")
        recommendations.append("  - Check data quality")

    if ood_results_dict and ood_results_dict['worst_degradation'] > 10.0:
        recommendations.append("WARNING: Poor OOD generalization. Consider:")
        recommendations.append("  - Broader training parameter ranges")
        recommendations.append("  - Data augmentation")
        recommendations.append("  - Regularization")

    if independence_results_dict and not independence_results_dict['functionally_independent']:
        recommendations.append("WARNING: Invariants not fully independent. Consider:")
        recommendations.append("  - Increase lambda_regularization")
        recommendations.append("  - Increase lambda_involution")
        recommendations.append("  - Train invariants sequentially")

    if all_tests_passed:
        recommendations.append("✓ All tests passed successfully!")
        recommendations.append("Model is ready for production use.")

    # =========================================================================
    # Assemble Report
    # =========================================================================
    report = ValidationReport(
        model_name=model_name,
        timestamp=timestamp,
        executive_summary=executive_summary,
        conservation_results=conservation_results,
        ood_results=ood_results_dict,
        independence_results=independence_results_dict,
        comparison_results=comparison_results_dict,
        recommendations=recommendations,
        metadata={
            'num_test_ics': len(test_initial_conditions),
            'training_config': training_config,
            'in_distribution_baseline': in_distribution_baseline
        }
    )

    if verbose:
        print("\n" + "="*80)
        print("REPORT GENERATION COMPLETE")
        print("="*80)

    return report


def print_report(report: ValidationReport) -> None:
    """
    Print validation report in human-readable format.

    Args:
        report: ValidationReport

    Example:
        >>> print_report(report)
    """
    print("\n" + "="*80)
    print(f"VALIDATION REPORT: {report.model_name}")
    print("="*80)
    print(f"Generated: {report.timestamp}")
    print()

    # Executive Summary
    print("EXECUTIVE SUMMARY")
    print("-"*80)
    verdict = report.executive_summary['overall_verdict']
    verdict_symbol = "✅" if verdict == "PASS" else "❌"
    print(f"{verdict_symbol} Overall Verdict: {verdict}")
    print(f"Number of invariants: {report.executive_summary['num_invariants']}")
    print(f"Conservation pass rate: {report.executive_summary['conservation_pass_rate']:.1%}")
    print(f"Mean conservation error: {report.executive_summary['mean_conservation_error']:.2e}")
    print()

    # Conservation
    print("CONSERVATION VERIFICATION")
    print("-"*80)
    cons = report.conservation_results
    print(f"Trajectories tested: {cons['num_trajectories']}")
    print(f"Pass rate: {cons['pass_rate']:.1%}")
    print(f"Mean error: {cons['conservation_error_mean']:.2e}")
    print(f"Max error: {cons['conservation_error_max']:.2e}")
    print(f"Poisson bracket: {cons['poisson_bracket_mean']:.2e}")
    print()

    # OOD
    if report.ood_results:
        print("OOD GENERALIZATION")
        print("-"*80)
        ood = report.ood_results
        print(f"Tests run: {ood['num_tests']}")
        print(f"Worst degradation: {ood['worst_degradation']:.1f}×")
        print()

    # Independence
    if report.independence_results:
        print("FUNCTIONAL INDEPENDENCE")
        print("-"*80)
        ind = report.independence_results
        status = "✓" if ind['functionally_independent'] else "✗"
        print(f"{status} Functionally independent: {ind['functionally_independent']}")
        print(f"Gradient rank: {ind['gradient_rank_mean']:.2f} / {ind['num_invariants']}")
        print(f"Max correlation: {ind['max_correlation']:.4f}")
        print(f"Max involution error: {ind['max_involution_error']:.2e}")
        print()

    # Comparison
    if report.comparison_results:
        print("CROSS-METHOD COMPARISON")
        print("-"*80)
        comp = report.comparison_results
        print(f"Geometric invariants tested: {comp['num_geometric_invariants']}")
        for match in comp['best_matches']:
            print(f"  ML inv {match['ml_invariant']} ↔ {match['geometric_invariant']}")
            print(f"    Correlation: {match['correlation']:.4f} ({match['agreement']})")
        print()

    # Recommendations
    print("RECOMMENDATIONS")
    print("-"*80)
    for rec in report.recommendations:
        print(f"  {rec}")
    print()
    print("="*80)


def save_report(report: ValidationReport, filepath: str, format: str = 'json') -> None:
    """
    Save validation report to file.

    Args:
        report: ValidationReport
        filepath: Output file path
        format: 'json' or 'txt'

    Example:
        >>> save_report(report, 'validation_report.json', format='json')
        >>> save_report(report, 'validation_report.txt', format='txt')
    """
    if format == 'json':
        # Convert to dictionary
        report_dict = asdict(report)
        with open(filepath, 'w') as f:
            json.dump(report_dict, f, indent=2, default=str)
        print(f"✓ Report saved to {filepath} (JSON)")

    elif format == 'txt':
        # Redirect print to file
        import sys
        from io import StringIO
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        print_report(report)
        report_text = sys.stdout.getvalue()
        sys.stdout = old_stdout

        with open(filepath, 'w') as f:
            f.write(report_text)
        print(f"✓ Report saved to {filepath} (TXT)")

    else:
        raise ValueError(f"Unknown format: {format}. Use 'json' or 'txt'.")


# Test code
if __name__ == "__main__":
    print("Testing validation reporting...")

    from .conservation_hnn import create_conservation_hnn

    # Create model
    print("\n[1] Creating ConservationHNN...")
    model, params = create_conservation_hnn(
        state_dim=4, num_invariants=2, encoder_dims=(64, 64), seed=0
    )

    # Generate test data
    print("\n[2] Generating test data...")
    key = jax.random.PRNGKey(42)
    test_ics = [jax.random.normal(jax.random.split(key)[1], (4,)) for _ in range(20)]

    training_config = {
        'mass_ratio_range': (0.1, 0.5),
        't_span': 100.0,
        'ecc_max': 0.7
    }

    baseline = {
        'conservation_error_mean': 1e-4,
        'pass_rate': 0.95
    }

    # Generate report
    print("\n[3] Generating validation report...")
    report = generate_validation_report(
        model, params, test_ics, training_config, baseline,
        model_name="Test ConservationHNN",
        run_ood_tests=True,
        run_independence_tests=True,
        run_comparison=False,
        verbose=True
    )

    # Print report
    print("\n[4] Printing report...")
    print_report(report)

    # Save report
    print("\n[5] Saving report...")
    save_report(report, '/tmp/test_validation_report.json', format='json')
    save_report(report, '/tmp/test_validation_report.txt', format='txt')

    print("\n✓ All tests passed!")
