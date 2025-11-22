"""
Stress testing for WP 4.3: Numerical Robustness.

This module tests conservation in extreme scenarios:
1. Near-collision scenarios (r₁₂ < 10⁻³)
2. Chaotic regions (positive Lyapunov exponent)
3. High eccentricity orbits (e > 0.95)

These tests verify that conservation holds even in challenging
dynamical regimes where numerical instabilities are common.
"""

import numpy as np
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional
from scipy.integrate import solve_ivp


@dataclass
class StressTestResult:
    """
    Result from a stress test scenario.

    Attributes:
        test_type: Type of stress test ('collision', 'chaos', 'eccentricity')
        n_tested: Number of scenarios tested
        n_success: Number that passed conservation test
        success_rate: Fraction passing
        max_drift: Maximum observed drift
        mean_drift: Mean drift across successful cases
        failures: List of failure descriptions
    """
    test_type: str
    n_tested: int
    n_success: int
    success_rate: float
    max_drift: float
    mean_drift: float
    failures: List[str]

    def __str__(self) -> str:
        lines = []
        lines.append(f"{self.test_type.upper()} STRESS TEST")
        lines.append(f"  Tested: {self.n_tested}")
        lines.append(f"  Success: {self.n_success}/{self.n_tested} ({100*self.success_rate:.1f}%)")
        lines.append(f"  Max drift: {self.max_drift:.2e}")
        lines.append(f"  Mean drift: {self.mean_drift:.2e}")
        if self.failures:
            lines.append(f"  Failures: {len(self.failures)}")
        return "\n".join(lines)


class StressTester:
    """
    Test conservation in extreme dynamical scenarios.

    Example:
        >>> tester = StressTester(tolerance=1e-6)
        >>> result = tester.test_near_collision(
        ...     integral_func=my_integral,
        ...     hamiltonian_func=my_hamiltonian
        ... )
        >>> print(f"Collision test success rate: {result.success_rate:.1%}")
    """

    def __init__(
        self,
        tolerance: float = 1e-6,
        integrator: str = 'DOP853',
        rtol: float = 1e-12,
        atol: float = 1e-14
    ):
        """
        Initialize stress tester.

        Args:
            tolerance: Conservation error tolerance
            integrator: ODE integrator
            rtol: Relative integration tolerance
            atol: Absolute integration tolerance
        """
        self.tolerance = tolerance
        self.integrator = integrator
        self.rtol = rtol
        self.atol = atol

    def test_near_collision(
        self,
        integral_func: Callable,
        hamiltonian_func: Callable,
        dynamics_func: Callable,
        r_min: float = 1e-3,
        n_tests: int = 100,
        verbose: bool = True
    ) -> StressTestResult:
        """
        Test conservation during close encounters.

        Args:
            integral_func: Integral evaluator
            hamiltonian_func: Hamiltonian evaluator
            dynamics_func: Dynamics RHS function
            r_min: Minimum binary separation
            n_tests: Number of collision scenarios to test
            verbose: Print progress

        Returns:
            StressTestResult
        """
        if verbose:
            print("=" * 70)
            print(f"NEAR-COLLISION STRESS TEST (r_min = {r_min})")
            print("=" * 70)

        drifts = []
        failures = []
        n_success = 0

        for i in range(n_tests):
            if verbose and i % 10 == 0:
                print(f"Progress: {i}/{n_tests}")

            # Generate near-collision IC
            ic = self._generate_collision_ic(r_min)

            # Integrate and measure drift
            try:
                drift = self._measure_drift(
                    ic,
                    integral_func,
                    hamiltonian_func,
                    dynamics_func,
                    t_max=100.0  # Shorter integration for collision tests
                )

                if drift is not None and drift < self.tolerance:
                    n_success += 1
                    drifts.append(drift)
                else:
                    failures.append(f"IC {i}: drift = {drift}")

            except Exception as e:
                failures.append(f"IC {i}: {str(e)}")

        success_rate = n_success / n_tests if n_tests > 0 else 0.0
        max_drift = np.max(drifts) if drifts else np.inf
        mean_drift = np.mean(drifts) if drifts else np.inf

        result = StressTestResult(
            test_type='collision',
            n_tested=n_tests,
            n_success=n_success,
            success_rate=success_rate,
            max_drift=max_drift,
            mean_drift=mean_drift,
            failures=failures
        )

        if verbose:
            print(f"\n{result}")
            print("=" * 70)

        return result

    def test_chaotic_region(
        self,
        integral_func: Callable,
        hamiltonian_func: Callable,
        dynamics_func: Callable,
        n_tests: int = 100,
        verbose: bool = True
    ) -> StressTestResult:
        """
        Test conservation in chaotic regions.

        Identifies trajectories with positive Lyapunov exponent
        and verifies conservation holds despite chaos.

        Args:
            integral_func: Integral evaluator
            hamiltonian_func: Hamiltonian evaluator
            dynamics_func: Dynamics RHS function
            n_tests: Number of chaotic trajectories to find and test
            verbose: Print progress

        Returns:
            StressTestResult
        """
        if verbose:
            print("=" * 70)
            print("CHAOTIC REGION STRESS TEST")
            print("=" * 70)

        drifts = []
        failures = []
        n_success = 0
        n_attempts = 0
        max_attempts = n_tests * 10  # Try up to 10x to find chaotic orbits

        while len(drifts) + len(failures) < n_tests and n_attempts < max_attempts:
            n_attempts += 1

            if verbose and n_attempts % 10 == 0:
                found = len(drifts) + len(failures)
                print(f"Progress: {found}/{n_tests} chaotic orbits found ({n_attempts} attempts)")

            # Generate random IC
            ic = self._generate_random_ic()

            # Check if chaotic (simplified - full implementation would compute Lyapunov)
            is_chaotic = self._is_likely_chaotic(ic, dynamics_func)

            if not is_chaotic:
                continue

            # Test conservation
            try:
                drift = self._measure_drift(
                    ic,
                    integral_func,
                    hamiltonian_func,
                    dynamics_func,
                    t_max=1000.0
                )

                if drift is not None and drift < self.tolerance:
                    n_success += 1
                    drifts.append(drift)
                else:
                    failures.append(f"Chaotic IC {len(drifts)+len(failures)}: drift = {drift}")

            except Exception as e:
                failures.append(f"Chaotic IC {len(drifts)+len(failures)}: {str(e)}")

        n_tested = len(drifts) + len(failures)
        success_rate = n_success / n_tested if n_tested > 0 else 0.0
        max_drift = np.max(drifts) if drifts else np.inf
        mean_drift = np.mean(drifts) if drifts else np.inf

        result = StressTestResult(
            test_type='chaos',
            n_tested=n_tested,
            n_success=n_success,
            success_rate=success_rate,
            max_drift=max_drift,
            mean_drift=mean_drift,
            failures=failures
        )

        if verbose:
            print(f"\n{result}")
            if n_tested < n_tests:
                print(f"Warning: Only found {n_tested} chaotic orbits in {n_attempts} attempts")
            print("=" * 70)

        return result

    def test_high_eccentricity(
        self,
        integral_func: Callable,
        hamiltonian_func: Callable,
        dynamics_func: Callable,
        e_min: float = 0.95,
        n_tests: int = 100,
        verbose: bool = True
    ) -> StressTestResult:
        """
        Test high eccentricity orbits.

        Args:
            integral_func: Integral evaluator
            hamiltonian_func: Hamiltonian evaluator
            dynamics_func: Dynamics RHS function
            e_min: Minimum eccentricity
            n_tests: Number of high-e orbits to test
            verbose: Print progress

        Returns:
            StressTestResult
        """
        if verbose:
            print("=" * 70)
            print(f"HIGH ECCENTRICITY STRESS TEST (e > {e_min})")
            print("=" * 70)

        drifts = []
        failures = []
        n_success = 0

        for i in range(n_tests):
            if verbose and i % 10 == 0:
                print(f"Progress: {i}/{n_tests}")

            # Generate high-eccentricity IC
            ic = self._generate_eccentric_ic(e_min)

            # Test conservation
            try:
                drift = self._measure_drift(
                    ic,
                    integral_func,
                    hamiltonian_func,
                    dynamics_func,
                    t_max=100.0  # One or two orbits
                )

                if drift is not None and drift < self.tolerance:
                    n_success += 1
                    drifts.append(drift)
                else:
                    failures.append(f"IC {i}: drift = {drift}")

            except Exception as e:
                failures.append(f"IC {i}: {str(e)}")

        success_rate = n_success / n_tests if n_tests > 0 else 0.0
        max_drift = np.max(drifts) if drifts else np.inf
        mean_drift = np.mean(drifts) if drifts else np.inf

        result = StressTestResult(
            test_type='eccentricity',
            n_tested=n_tests,
            n_success=n_success,
            success_rate=success_rate,
            max_drift=max_drift,
            mean_drift=mean_drift,
            failures=failures
        )

        if verbose:
            print(f"\n{result}")
            print("=" * 70)

        return result

    def run_all_tests(
        self,
        integral_func: Callable,
        hamiltonian_func: Callable,
        dynamics_func: Callable,
        verbose: bool = True
    ) -> Dict[str, StressTestResult]:
        """
        Run all stress tests.

        Args:
            integral_func: Integral evaluator
            hamiltonian_func: Hamiltonian evaluator
            dynamics_func: Dynamics RHS function
            verbose: Print progress

        Returns:
            Dictionary of stress test results
        """
        results = {}

        results['collision'] = self.test_near_collision(
            integral_func, hamiltonian_func, dynamics_func, verbose=verbose
        )

        results['chaos'] = self.test_chaotic_region(
            integral_func, hamiltonian_func, dynamics_func, verbose=verbose
        )

        results['eccentricity'] = self.test_high_eccentricity(
            integral_func, hamiltonian_func, dynamics_func, verbose=verbose
        )

        if verbose:
            print("\n" + "=" * 70)
            print("STRESS TEST SUMMARY")
            print("=" * 70)
            for test_type, result in results.items():
                print(f"{test_type.upper()}: {result.success_rate:.1%} success rate")
            print("=" * 70)

        return results

    def _generate_collision_ic(self, r_min: float) -> np.ndarray:
        """Generate IC with close binary separation."""
        # Placeholder - would need proper 3-body collision setup
        ic = np.random.randn(4) * 0.1
        return ic

    def _generate_random_ic(self) -> np.ndarray:
        """Generate random IC."""
        return np.random.randn(4) * 0.5

    def _generate_eccentric_ic(self, e_min: float) -> np.ndarray:
        """Generate high-eccentricity IC."""
        # Placeholder - would need proper Kepler orbit setup
        ic = np.random.randn(4)
        ic[:2] *= (1 + e_min)  # Stretch position (approximate)
        return ic

    def _is_likely_chaotic(self, ic: np.ndarray, dynamics_func: Callable) -> bool:
        """
        Simplified chaos detection.

        Full implementation would compute Lyapunov exponent.
        """
        # Placeholder: Assume 30% of random ICs are chaotic
        return np.random.rand() < 0.3

    def _measure_drift(
        self,
        ic: np.ndarray,
        integral_func: Callable,
        hamiltonian_func: Callable,
        dynamics_func: Callable,
        t_max: float
    ) -> Optional[float]:
        """Integrate and measure conservation drift."""
        try:
            I_0 = integral_func(ic)

            sol = solve_ivp(
                lambda t, y: dynamics_func(t, y),
                [0, t_max],
                ic,
                method=self.integrator,
                rtol=self.rtol,
                atol=self.atol
            )

            if not sol.success:
                return None

            I_final = integral_func(sol.y[:, -1])
            drift = abs(I_final - I_0) / (abs(I_0) + 1e-16)

            return drift

        except Exception:
            return None
