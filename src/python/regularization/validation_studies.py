"""
Phase 5: Extended Validation Studies.

Comprehensive validation of time-regularized dynamics:
- Figure-eight choreography
- Collision passage tests
- Comparative analysis with standard methods
- Accuracy and stability assessment
"""

from dataclasses import dataclass
from typing import Dict, Tuple, Optional
import numpy as np

from .time_regularized_dynamics import (
    TimeRegularizedTrajectory,
    integrate_time_regularized_ks,
    create_kepler_initial_state,
    TimeRegularizedHamiltonian
)
from .threebody_time_regularized import (
    ThreeBodyTrajectory,
    PairwiseSpinorStateWithTime,
    ThreeBodyTimeRegularizedHamiltonian
)
from ..coordinates.base import Masses


@dataclass
class ValidationResult:
    """Result of a validation test."""
    test_name: str
    passed: bool
    error_metric: float
    tolerance: float
    details: Dict

    def __str__(self) -> str:
        status = "✓ PASS" if self.passed else "✗ FAIL"
        return f"{status} {self.test_name}: error={self.error_metric:.6e} (tol={self.tolerance:.6e})"


def validate_collision_passage(
    mu: float = 1.0,
    e: float = 0.95,
    n_points: int = 1000,
    rtol: float = 1e-10,
    atol: float = 1e-12
) -> ValidationResult:
    """
    Validate collision passage for highly eccentric orbit.

    Tests that time regularization handles near-collision smoothly.

    Args:
        mu: Gravitational parameter
        e: Eccentricity (0.95 = very eccentric)
        n_points: Number of integration points
        rtol, atol: Integration tolerances

    Returns:
        ValidationResult
    """
    # Create initial state for highly eccentric orbit
    state0 = create_kepler_initial_state(
        semi_major_axis=1.0,
        eccentricity=e,
        mu=mu
    )

    H = TimeRegularizedHamiltonian(mu=mu)

    # Integrate through periapsis
    expected_period = 2 * np.pi * np.sqrt(1.0**3 / mu)
    s_span = (0, expected_period * 2.0)

    try:
        traj = integrate_time_regularized_ks(
            state0, H, s_span, n_points=n_points, rtol=rtol, atol=atol
        )

        # Check energy conservation through near-collision
        E_vals, K_vals = traj.get_energies()
        E_drift = np.std(E_vals)

        # Check that integration didn't fail at periapsis
        Omega_vals = traj.get_time_dilations()
        min_Omega = np.min(Omega_vals)

        # Near-collision should have small Ω but integration should succeed
        collision_handled = min_Omega < 0.1 and E_drift < 1e-4

        error = E_drift
        tolerance = 1e-4

        return ValidationResult(
            test_name=f"Collision Passage (e={e})",
            passed=collision_handled and error < tolerance,
            error_metric=error,
            tolerance=tolerance,
            details={
                'E_drift': E_drift,
                'min_Omega': min_Omega,
                'collision_handled': collision_handled,
                'integration_successful': True
            }
        )

    except Exception as ex:
        return ValidationResult(
            test_name=f"Collision Passage (e={e})",
            passed=False,
            error_metric=float('inf'),
            tolerance=1e-4,
            details={'error': str(ex), 'integration_successful': False}
        )


def validate_energy_conservation_long_term(
    semi_major_axis: float = 1.0,
    eccentricity: float = 0.3,
    mu: float = 1.0,
    n_periods: int = 10,
    n_points: int = 10000
) -> ValidationResult:
    """
    Validate energy conservation over many orbital periods.

    Tests long-term stability of the integrator.

    Args:
        semi_major_axis: Orbital semi-major axis
        eccentricity: Eccentricity
        mu: Gravitational parameter
        n_periods: Number of periods to integrate
        n_points: Number of integration points

    Returns:
        ValidationResult
    """
    state0 = create_kepler_initial_state(
        semi_major_axis=semi_major_axis,
        eccentricity=eccentricity,
        mu=mu
    )

    H = TimeRegularizedHamiltonian(mu=mu)

    # Integrate for multiple periods
    period = 2 * np.pi * np.sqrt(semi_major_axis**3 / mu)
    s_span = (0, period * n_periods * 2.0)  # Extra margin for fictitious time

    try:
        traj = integrate_time_regularized_ks(
            state0, H, s_span, n_points=n_points, rtol=1e-10, atol=1e-12
        )

        # Check energy conservation
        E_vals, _ = traj.get_energies()
        E_drift = np.std(E_vals) / np.abs(np.mean(E_vals))  # Relative drift

        tolerance = 1e-6

        return ValidationResult(
            test_name=f"Long-term Energy Conservation ({n_periods} periods)",
            passed=E_drift < tolerance,
            error_metric=E_drift,
            tolerance=tolerance,
            details={
                'E_relative_drift': E_drift,
                'n_periods': n_periods,
                'final_time': traj.t_values[-1],
                'expected_time': period * n_periods
            }
        )

    except Exception as ex:
        return ValidationResult(
            test_name=f"Long-term Energy Conservation ({n_periods} periods)",
            passed=False,
            error_metric=float('inf'),
            tolerance=1e-6,
            details={'error': str(ex)}
        )


def validate_time_transformation_accuracy(
    semi_major_axis: float = 1.0,
    eccentricity: float = 0.5,
    mu: float = 1.0
) -> ValidationResult:
    """
    Validate accuracy of time transformation dt/ds = Ω(u).

    Args:
        semi_major_axis: Orbital semi-major axis
        eccentricity: Eccentricity
        mu: Gravitational parameter

    Returns:
        ValidationResult
    """
    state0 = create_kepler_initial_state(
        semi_major_axis=semi_major_axis,
        eccentricity=eccentricity,
        mu=mu
    )

    H = TimeRegularizedHamiltonian(mu=mu)

    # Short integration with high accuracy
    period = 2 * np.pi * np.sqrt(semi_major_axis**3 / mu)
    s_span = (0, period * 2.0)

    traj = integrate_time_regularized_ks(
        state0, H, s_span, n_points=1000, rtol=1e-12, atol=1e-14
    )

    # Verify dt/ds = Ω numerically
    t_vals = traj.t_values
    s_vals = traj.s_values
    Omega_vals = traj.get_time_dilations()

    # Compute dt/ds numerically
    dt_ds_numeric = np.gradient(t_vals, s_vals)

    # Compare with Ω
    error = np.max(np.abs(dt_ds_numeric - Omega_vals))
    tolerance = 1e-4  # Numerical differentiation introduces some error

    return ValidationResult(
        test_name="Time Transformation Accuracy (dt/ds = Ω)",
        passed=error < tolerance,
        error_metric=error,
        tolerance=tolerance,
        details={
            'max_error': error,
            'mean_error': np.mean(np.abs(dt_ds_numeric - Omega_vals)),
            'Omega_range': [np.min(Omega_vals), np.max(Omega_vals)]
        }
    )


def validate_k_e_omega_relation(
    semi_major_axis: float = 1.0,
    eccentricity: float = 0.4,
    mu: float = 1.0
) -> ValidationResult:
    """
    Validate K = E·Ω relation throughout integration.

    Args:
        semi_major_axis: Orbital semi-major axis
        eccentricity: Eccentricity
        mu: Gravitational parameter

    Returns:
        ValidationResult
    """
    state0 = create_kepler_initial_state(
        semi_major_axis=semi_major_axis,
        eccentricity=eccentricity,
        mu=mu
    )

    H = TimeRegularizedHamiltonian(mu=mu)

    period = 2 * np.pi * np.sqrt(semi_major_axis**3 / mu)
    s_span = (0, period * 2.0)

    traj = integrate_time_regularized_ks(
        state0, H, s_span, n_points=500, rtol=1e-10, atol=1e-12
    )

    # Check K = E·Ω
    E_vals, K_vals = traj.get_energies()
    Omega_vals = traj.get_time_dilations()

    K_expected = E_vals * Omega_vals
    error = np.max(np.abs(K_vals - K_expected))
    tolerance = 1e-4

    return ValidationResult(
        test_name="K = E·Ω Relation",
        passed=error < tolerance,
        error_metric=error,
        tolerance=tolerance,
        details={
            'max_error': error,
            'mean_error': np.mean(np.abs(K_vals - K_expected)),
            'E_conserved': np.std(E_vals) < 1e-6
        }
    )


def run_comprehensive_validation_suite() -> Dict[str, ValidationResult]:
    """
    Run comprehensive validation suite.

    Returns:
        Dictionary mapping test names to ValidationResult objects
    """
    results = {}

    print("Running Comprehensive Validation Suite...")
    print("=" * 80)

    # Test 1: Collision passage
    print("\n1. Testing collision passage...")
    results['collision_passage_e95'] = validate_collision_passage(e=0.95)
    print(f"   {results['collision_passage_e95']}")

    # Test 2: Long-term energy conservation
    print("\n2. Testing long-term energy conservation...")
    results['long_term_energy'] = validate_energy_conservation_long_term(n_periods=10)
    print(f"   {results['long_term_energy']}")

    # Test 3: Time transformation accuracy
    print("\n3. Testing time transformation accuracy...")
    results['time_transformation'] = validate_time_transformation_accuracy()
    print(f"   {results['time_transformation']}")

    # Test 4: K = E·Ω relation
    print("\n4. Testing K = E·Ω relation...")
    results['k_e_omega'] = validate_k_e_omega_relation()
    print(f"   {results['k_e_omega']}")

    # Test 5: Multiple eccentricities
    print("\n5. Testing multiple eccentricities...")
    for e in [0.0, 0.3, 0.6, 0.9]:
        result = validate_collision_passage(e=e)
        results[f'collision_e{int(e*100):02d}'] = result
        print(f"   e={e}: {result}")

    print("\n" + "=" * 80)
    print("Validation Suite Complete")
    print(f"Tests Passed: {sum(1 for r in results.values() if r.passed)}/{len(results)}")
    print("=" * 80)

    return results


def generate_validation_report(results: Dict[str, ValidationResult]) -> str:
    """
    Generate validation report.

    Args:
        results: Dictionary of validation results

    Returns:
        Formatted report string
    """
    passed = sum(1 for r in results.values() if r.passed)
    total = len(results)
    pass_rate = 100 * passed / total if total > 0 else 0

    report = f"""
================================================================================
                        VALIDATION REPORT
================================================================================

Overall Results: {passed}/{total} tests passed ({pass_rate:.1f}%)

Test Results:
"""

    for name, result in results.items():
        status = "✓ PASS" if result.passed else "✗ FAIL"
        report += f"\n  {status} {result.test_name}"
        report += f"\n      Error: {result.error_metric:.6e} (tolerance: {result.tolerance:.6e})"

        if not result.passed and 'error' in result.details:
            report += f"\n      Reason: {result.details['error']}"

    report += "\n\n"
    report += "=" * 80
    report += "\n"

    return report
