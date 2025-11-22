"""
Involution tester for WP 4.1: Analytical Vetting.

This module tests whether a set of integrals are in mutual involution,
i.e., {I_i, I_j} = 0 for all pairs (i, j).

This is one of the three Liouville integrability criteria:
1. Conservation: {I_k, H} = 0  ✓ (conservation_validator.py)
2. Involution: {I_i, I_j} = 0   ✓ (this module)
3. Independence: rank(∇I_1, ..., ∇I_n) = n  (independence_tester.py)
"""

import numpy as np
import sympy as sp
from typing import Dict, List, Optional, Union, Callable, Tuple
from dataclasses import dataclass
from itertools import combinations

from .poisson_brackets import (
    PoissonBracketComputer,
    PoissonBracketResult
)


@dataclass
class InvolutionTestResult:
    """
    Result of involution test for all pairs.

    Attributes:
        all_in_involution: True if all pairwise brackets vanish
        bracket_matrix: Dictionary of pairwise bracket results
                       Key: (name_i, name_j), Value: PoissonBracketResult
        n_pairs_tested: Number of pairs tested
        n_pairs_success: Number of pairs in involution
        success_rate: Fraction of pairs in involution
    """
    all_in_involution: bool
    bracket_matrix: Dict[Tuple[str, str], PoissonBracketResult]
    n_pairs_tested: int
    n_pairs_success: int
    success_rate: float

    def __str__(self) -> str:
        if self.all_in_involution:
            return f"✓ All {self.n_pairs_tested} pairs in involution"
        else:
            return f"✗ Only {self.n_pairs_success}/{self.n_pairs_tested} pairs in involution ({100*self.success_rate:.1f}%)"

    def get_failed_pairs(self) -> List[Tuple[str, str]]:
        """Return list of pairs that failed involution test."""
        return [
            pair for pair, result in self.bracket_matrix.items()
            if not result.success
        ]

    def print_matrix(self, compact: bool = False):
        """
        Print involution matrix.

        Args:
            compact: If True, print compact version (✓/✗ only)
        """
        integral_names = list(set(
            name for pair in self.bracket_matrix.keys()
            for name in pair
        ))

        integral_names_sorted = sorted(integral_names)

        print("\nInvolution Matrix:")
        print("-" * 70)

        # Header
        print(f"{'':15}", end="")
        for name_j in integral_names_sorted:
            print(f"{name_j:>15}", end="")
        print()

        # Rows
        for name_i in integral_names_sorted:
            print(f"{name_i:15}", end="")
            for name_j in integral_names_sorted:
                if name_i == name_j:
                    print(f"{'—':>15}", end="")  # Diagonal (trivial)
                else:
                    # Find result (either (i,j) or (j,i))
                    pair = (name_i, name_j)
                    pair_rev = (name_j, name_i)

                    if pair in self.bracket_matrix:
                        result = self.bracket_matrix[pair]
                    elif pair_rev in self.bracket_matrix:
                        result = self.bracket_matrix[pair_rev]
                    else:
                        print(f"{'?':>15}", end="")
                        continue

                    if compact:
                        symbol = "✓" if result.success else "✗"
                        print(f"{symbol:>15}", end="")
                    else:
                        if result.is_zero_symbolic:
                            print(f"{'0 (sym)':>15}", end="")
                        elif result.success:
                            print(f"{result.numerical_max:>15.2e}", end="")
                        else:
                            print(f"{result.numerical_max:>15.2e}*", end="")

            print()

        if not compact:
            print("\n* = Failed (exceeds tolerance)")


class InvolutionTester:
    """
    Test mutual involution of integrals: {I_i, I_j} = 0 for all pairs.

    Example:
        >>> import sympy as sp
        >>> q1, q2, p1, p2 = sp.symbols('q1 q2 p1 p2', real=True)
        >>> integrals = {
        ...     'E': (p1**2 + p2**2)/2 + (q1**2 + q2**2)/2,
        ...     'L': q1*p2 - q2*p1
        ... }
        >>> tester = InvolutionTester()
        >>> result = tester.test_involution(integrals)
        >>> print(result.all_in_involution)
        >>> # True (energy and angular momentum are in involution)
    """

    def __init__(
        self,
        tolerance: float = 1e-10,
        n_samples: int = 10000,
        test_self_brackets: bool = False
    ):
        """
        Initialize involution tester.

        Args:
            tolerance: Acceptance threshold for bracket magnitude
            n_samples: Number of samples for numerical evaluation
            test_self_brackets: If True, test {I_i, I_i} = 0 (always true)
        """
        self.tolerance = tolerance
        self.n_samples = n_samples
        self.test_self_brackets = test_self_brackets

        self.bracket_computer = PoissonBracketComputer(
            numerical_samples=n_samples,
            tolerance=tolerance
        )

    def test_involution(
        self,
        integrals: Dict[str, Union[sp.Expr, Callable]],
        variables: Optional[List[sp.Symbol]] = None,
        verbose: bool = True
    ) -> InvolutionTestResult:
        """
        Test pairwise involution for all integrals.

        Args:
            integrals: Dictionary mapping names to integral expressions
            variables: Phase space variables (inferred if not provided)
            verbose: Print progress

        Returns:
            InvolutionTestResult with detailed pairwise results
        """
        integral_names = list(integrals.keys())
        n_integrals = len(integral_names)

        if verbose:
            print("\n" + "=" * 70)
            print(f"INVOLUTION TEST: {n_integrals} integrals")
            print("=" * 70)

        # Determine number of pairs to test
        if self.test_self_brackets:
            n_pairs = n_integrals * (n_integrals + 1) // 2
        else:
            n_pairs = n_integrals * (n_integrals - 1) // 2

        if verbose:
            print(f"Testing {n_pairs} pairs...")
            print(f"Tolerance: {self.tolerance:.2e}")

        bracket_matrix = {}
        n_success = 0

        # Test all pairs
        for i, name_i in enumerate(integral_names):
            for j, name_j in enumerate(integral_names):
                # Skip if already tested (matrix is symmetric)
                if i > j:
                    continue

                # Skip self-brackets unless requested
                if i == j and not self.test_self_brackets:
                    continue

                I_i = integrals[name_i]
                I_j = integrals[name_j]

                if verbose:
                    print(f"\n  {{{name_i}, {name_j}}}", end=" ")

                result = self.bracket_computer.compute_bracket(
                    I_i, I_j, variables, verbose=False
                )

                bracket_matrix[(name_i, name_j)] = result

                if result.success:
                    n_success += 1
                    if verbose:
                        if result.is_zero_symbolic:
                            print("✓ (symbolic)")
                        else:
                            print(f"✓ (numerical: {result.numerical_max:.2e})")
                else:
                    if verbose:
                        print(f"✗ (max: {result.numerical_max:.2e})")

        # Summary
        n_tested = len(bracket_matrix)
        all_in_involution = (n_success == n_tested)
        success_rate = n_success / n_tested if n_tested > 0 else 0.0

        if verbose:
            print("\n" + "=" * 70)
            print(f"INVOLUTION SUMMARY: {n_success}/{n_tested} pairs in involution")
            if all_in_involution:
                print("✓ ALL PAIRS IN INVOLUTION")
            else:
                print(f"✗ {n_tested - n_success} pairs FAILED")
            print("=" * 70)

        result = InvolutionTestResult(
            all_in_involution=all_in_involution,
            bracket_matrix=bracket_matrix,
            n_pairs_tested=n_tested,
            n_pairs_success=n_success,
            success_rate=success_rate
        )

        if verbose and not all_in_involution:
            print("\nFailed pairs:")
            for pair in result.get_failed_pairs():
                bracket_res = bracket_matrix[pair]
                print(f"  {{{pair[0]}, {pair[1]}}}: max = {bracket_res.numerical_max:.2e}")

        return result

    def test_new_integral_involution(
        self,
        new_integral: Union[sp.Expr, Callable],
        new_integral_name: str,
        known_integrals: Dict[str, Union[sp.Expr, Callable]],
        variables: Optional[List[sp.Symbol]] = None,
        verbose: bool = True
    ) -> Tuple[bool, Dict[str, PoissonBracketResult]]:
        """
        Test if a new integral is in involution with all known integrals.

        Useful for incremental testing when discovering new integrals.

        Args:
            new_integral: New candidate integral
            new_integral_name: Name for the new integral
            known_integrals: Dictionary of already-validated integrals
            variables: Phase space variables
            verbose: Print progress

        Returns:
            Tuple of (in_involution, bracket_results)
                in_involution: True if new integral commutes with all known ones
                bracket_results: Dict mapping known integral names to bracket results
        """
        if verbose:
            print("\n" + "=" * 70)
            print(f"INCREMENTAL INVOLUTION TEST: {new_integral_name}")
            print("=" * 70)
            print(f"Testing against {len(known_integrals)} known integrals...")

        bracket_results = {}
        all_in_involution = True

        for known_name, known_integral in known_integrals.items():
            if verbose:
                print(f"\n  {{{new_integral_name}, {known_name}}}", end=" ")

            result = self.bracket_computer.compute_bracket(
                new_integral, known_integral, variables, verbose=False
            )

            bracket_results[known_name] = result

            if result.success:
                if verbose:
                    if result.is_zero_symbolic:
                        print("✓ (symbolic)")
                    else:
                        print(f"✓ (numerical: {result.numerical_max:.2e})")
            else:
                all_in_involution = False
                if verbose:
                    print(f"✗ (max: {result.numerical_max:.2e})")

        if verbose:
            print("\n" + "=" * 70)
            if all_in_involution:
                print(f"✓ {new_integral_name} is in involution with all known integrals")
            else:
                n_failed = sum(1 for r in bracket_results.values() if not r.success)
                print(f"✗ {new_integral_name} fails involution with {n_failed} integrals")
            print("=" * 70)

        return all_in_involution, bracket_results


def quick_involution_check(
    integrals: Dict[str, sp.Expr],
    variables: Optional[List[sp.Symbol]] = None,
    tolerance: float = 1e-10,
    verbose: bool = True
) -> bool:
    """
    Quick check: are all integrals in mutual involution?

    Convenience function for simple yes/no answer.

    Args:
        integrals: Dictionary of integrals to test
        variables: Phase space variables
        tolerance: Acceptance threshold
        verbose: Print results

    Returns:
        True if all pairs are in involution
    """
    tester = InvolutionTester(tolerance=tolerance)
    result = tester.test_involution(integrals, variables, verbose)
    return result.all_in_involution


def check_liouville_involution(
    integrals: Dict[str, sp.Expr],
    variables: Optional[List[sp.Symbol]] = None,
    verbose: bool = True
) -> InvolutionTestResult:
    """
    Check Liouville involution criterion for integrability.

    This is the second of three Liouville criteria.

    Args:
        integrals: Dictionary of candidate integrals
        variables: Phase space variables
        verbose: Print detailed results

    Returns:
        InvolutionTestResult
    """
    tester = InvolutionTester(tolerance=1e-10)
    return tester.test_involution(integrals, variables, verbose)
