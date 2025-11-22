"""
Complete Analytical Vetting Pipeline for WP 4.1.

This module orchestrates the complete three-stage Liouville integrability test:
1. Conservation: {I_k, H} = 0
2. Involution: {I_i, I_j} = 0
3. Functional Independence: rank(∇I_1, ..., ∇I_n) = n

This is the first stage of the WP4 validation gauntlet. Candidates must pass
ALL three tests to proceed to WP 4.2 (Morales-Ramis) and WP 4.3 (Numerical Robustness).
"""

import sympy as sp
from typing import Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum

from .conservation_validator import ConservationValidator, ConservationValidationResult
from .involution_tester import InvolutionTester, InvolutionTestResult
from .independence_tester import IndependenceTester, IndependenceTestResult


class VettingVerdict(Enum):
    """Overall verdict from analytical vetting."""
    PASS_ALL = "pass_all"  # Passed all three tests
    FAIL_CONSERVATION = "fail_conservation"  # Failed conservation test
    FAIL_INVOLUTION = "fail_involution"  # Failed involution test
    FAIL_INDEPENDENCE = "fail_independence"  # Failed independence test
    FAIL_MULTIPLE = "fail_multiple"  # Failed multiple tests
    ERROR = "error"  # Error during testing


@dataclass
class AnalyticalVettingReport:
    """
    Complete report from analytical vetting pipeline.

    Attributes:
        verdict: Overall verdict
        passed_candidates: List of candidate names that passed all tests
        conservation_results: Results from conservation tests
        involution_result: Result from involution test
        independence_result: Result from independence test
        n_candidates: Total number of candidates tested
        n_passed: Number that passed all tests
    """
    verdict: VettingVerdict
    passed_candidates: List[str]
    conservation_results: Dict[str, ConservationValidationResult]
    involution_result: Optional[InvolutionTestResult]
    independence_result: Optional[IndependenceTestResult]
    n_candidates: int
    n_passed: int

    def __str__(self) -> str:
        lines = []
        lines.append("=" * 70)
        lines.append("ANALYTICAL VETTING REPORT")
        lines.append("=" * 70)
        lines.append(f"Candidates tested: {self.n_candidates}")
        lines.append(f"Candidates passed: {self.n_passed}")
        lines.append(f"Success rate: {100*self.n_passed/max(self.n_candidates,1):.1f}%")
        lines.append(f"Verdict: {self.verdict.value.upper()}")
        lines.append("=" * 70)

        if self.passed_candidates:
            lines.append("\n✓ PASSED CANDIDATES:")
            for name in self.passed_candidates:
                lines.append(f"  - {name}")
        else:
            lines.append("\n✗ NO CANDIDATES PASSED ALL TESTS")

        return "\n".join(lines)

    def print_detailed_report(self):
        """Print comprehensive detailed report."""
        print(self)

        # Conservation details
        print("\n" + "=" * 70)
        print("STAGE 1: CONSERVATION TEST RESULTS")
        print("=" * 70)
        for name, result in self.conservation_results.items():
            print(f"\n{name}:")
            print(f"  {result}")

        # Involution details
        if self.involution_result:
            print("\n" + "=" * 70)
            print("STAGE 2: INVOLUTION TEST RESULTS")
            print("=" * 70)
            print(f"{self.involution_result}")
            if hasattr(self.involution_result, 'print_matrix'):
                self.involution_result.print_matrix(compact=True)

        # Independence details
        if self.independence_result:
            print("\n" + "=" * 70)
            print("STAGE 3: INDEPENDENCE TEST RESULTS")
            print("=" * 70)
            print(f"{self.independence_result}")
            if hasattr(self.independence_result, 'print_rank_distribution'):
                self.independence_result.print_rank_distribution()


class AnalyticalVetter:
    """
    Complete WP 4.1 analytical vetting pipeline.

    Runs the three-stage Liouville integrability test:
    1. Conservation: {I, H} = 0 for each candidate
    2. Involution: {I_i, I_j} = 0 for all pairs
    3. Independence: Full Jacobian rank

    Only candidates passing ALL stages are deemed valid.

    Example:
        >>> import sympy as sp
        >>> q1, q2, p1, p2 = sp.symbols('q1 q2 p1 p2', real=True)
        >>> H = (p1**2 + p2**2)/2 + (q1**2 + q2**2)/2  # Harmonic oscillator
        >>> candidates = {
        ...     'E': H,
        ...     'L': q1*p2 - q2*p1,
        ...     'bad': q1  # Not conserved
        ... }
        >>> known = {'H': H}
        >>> variables = [q1, q2, p1, p2]
        >>>
        >>> vetter = AnalyticalVetter(H, known, variables)
        >>> report = vetter.vet_candidates(candidates)
        >>> print(f"Passed: {report.passed_candidates}")
        >>> # Passed: ['E', 'L']
    """

    def __init__(
        self,
        hamiltonian: Union[sp.Expr, Callable],
        known_integrals: Dict[str, Union[sp.Expr, Callable]],
        variables: List[sp.Symbol],
        tolerance: float = 1e-12,
        conservation_samples: int = 10000,
        independence_samples: int = 10000,
        independence_threshold: float = 0.995
    ):
        """
        Initialize analytical vetter.

        Args:
            hamiltonian: Hamiltonian H of the system
            known_integrals: Dictionary of known conserved quantities (e.g., E, L)
            variables: Phase space variables [q0, ..., p0, ...]
            tolerance: Acceptance threshold for bracket/conservation tests
            conservation_samples: Samples for conservation testing
            independence_samples: Samples for independence testing
            independence_threshold: Minimum fraction for independence
        """
        self.hamiltonian = hamiltonian
        self.known_integrals = known_integrals
        self.variables = variables
        self.tolerance = tolerance

        # Initialize validators
        self.conservation_validator = ConservationValidator(
            hamiltonian=hamiltonian,
            known_integrals=known_integrals,
            tolerance=tolerance,
            bracket_samples=conservation_samples
        )

        self.involution_tester = InvolutionTester(
            tolerance=tolerance * 100,  # Slightly relaxed for involution
            n_samples=conservation_samples
        )

        self.independence_tester = IndependenceTester(
            n_samples=independence_samples,
            rank_threshold=independence_threshold,
            tolerance=tolerance
        )

    def vet_candidates(
        self,
        new_candidates: Dict[str, Union[sp.Expr, Callable]],
        verbose: bool = True
    ) -> AnalyticalVettingReport:
        """
        Run complete analytical vetting on new candidates.

        Executes three-stage pipeline:
        1. Conservation: Filter to conserved candidates only
        2. Involution: Test pairwise brackets (known + new)
        3. Independence: Test Jacobian rank (known + new)

        Args:
            new_candidates: Dictionary of new candidate integrals to test
            verbose: Print detailed progress

        Returns:
            AnalyticalVettingReport with complete results
        """
        if verbose:
            print("\n" + "=" * 70)
            print("WP 4.1: ANALYTICAL VETTING PIPELINE")
            print("=" * 70)
            print(f"New candidates: {len(new_candidates)}")
            print(f"Known integrals: {len(self.known_integrals)}")
            print(f"Tolerance: {self.tolerance:.2e}")

        n_candidates = len(new_candidates)

        # ========================================
        # STAGE 1: CONSERVATION TEST
        # ========================================
        if verbose:
            print("\n" + "=" * 70)
            print("STAGE 1: CONSERVATION TEST")
            print("=" * 70)
            print("Testing {I, H} = 0 for each candidate...")

        conservation_results = self.conservation_validator.validate_candidates(
            new_candidates,
            variables=self.variables,
            verbose=verbose
        )

        # Filter: Only keep conserved candidates
        conserved_candidates = {
            name: new_candidates[name]
            for name, result in conservation_results.items()
            if result.success
        }

        if verbose:
            print(f"\n→ {len(conserved_candidates)}/{n_candidates} candidates conserved")

        if not conserved_candidates:
            if verbose:
                print("\n✗ NO CANDIDATES PASSED CONSERVATION TEST")
                print("=" * 70)

            return AnalyticalVettingReport(
                verdict=VettingVerdict.FAIL_CONSERVATION,
                passed_candidates=[],
                conservation_results=conservation_results,
                involution_result=None,
                independence_result=None,
                n_candidates=n_candidates,
                n_passed=0
            )

        # ========================================
        # STAGE 2: INVOLUTION TEST
        # ========================================
        if verbose:
            print("\n" + "=" * 70)
            print("STAGE 2: INVOLUTION TEST")
            print("=" * 70)
            print("Testing {I_i, I_j} = 0 for all pairs...")

        # Combine known + new integrals
        all_integrals = {**self.known_integrals, **conserved_candidates}

        involution_result = self.involution_tester.test_involution(
            all_integrals,
            variables=self.variables,
            verbose=verbose
        )

        if not involution_result.all_in_involution:
            if verbose:
                print("\n✗ INVOLUTION TEST FAILED")
                print("=" * 70)

            return AnalyticalVettingReport(
                verdict=VettingVerdict.FAIL_INVOLUTION,
                passed_candidates=[],
                conservation_results=conservation_results,
                involution_result=involution_result,
                independence_result=None,
                n_candidates=n_candidates,
                n_passed=0
            )

        if verbose:
            print(f"\n→ All integrals in involution ✓")

        # ========================================
        # STAGE 3: FUNCTIONAL INDEPENDENCE TEST
        # ========================================
        if verbose:
            print("\n" + "=" * 70)
            print("STAGE 3: FUNCTIONAL INDEPENDENCE TEST")
            print("=" * 70)
            print("Testing rank(∇I_1, ..., ∇I_n) = n...")

        independence_result = self.independence_tester.test_independence(
            all_integrals,
            variables=self.variables,
            verbose=verbose
        )

        if not independence_result.is_independent:
            if verbose:
                print("\n✗ INDEPENDENCE TEST FAILED")
                print("=" * 70)

            return AnalyticalVettingReport(
                verdict=VettingVerdict.FAIL_INDEPENDENCE,
                passed_candidates=[],
                conservation_results=conservation_results,
                involution_result=involution_result,
                independence_result=independence_result,
                n_candidates=n_candidates,
                n_passed=0
            )

        if verbose:
            print(f"\n→ Integrals functionally independent ✓")

        # ========================================
        # FINAL VERDICT
        # ========================================
        passed_candidates = list(conserved_candidates.keys())

        if verbose:
            print("\n" + "=" * 70)
            print("✓ ALL TESTS PASSED!")
            print("=" * 70)
            print(f"Validated candidates: {passed_candidates}")

        return AnalyticalVettingReport(
            verdict=VettingVerdict.PASS_ALL,
            passed_candidates=passed_candidates,
            conservation_results=conservation_results,
            involution_result=involution_result,
            independence_result=independence_result,
            n_candidates=n_candidates,
            n_passed=len(passed_candidates)
        )


def quick_vetting(
    candidates: Dict[str, sp.Expr],
    hamiltonian: sp.Expr,
    known_integrals: Dict[str, sp.Expr],
    variables: List[sp.Symbol],
    verbose: bool = True
) -> List[str]:
    """
    Quick analytical vetting.

    Convenience function that returns list of passed candidates.

    Args:
        candidates: New candidates to test
        hamiltonian: Hamiltonian of the system
        known_integrals: Known conserved quantities
        variables: Phase space variables
        verbose: Print progress

    Returns:
        List of candidate names that passed all tests
    """
    vetter = AnalyticalVetter(hamiltonian, known_integrals, variables)
    report = vetter.vet_candidates(candidates, verbose)
    return report.passed_candidates


def comprehensive_vetting(
    candidates: Dict[str, sp.Expr],
    hamiltonian: sp.Expr,
    known_integrals: Dict[str, sp.Expr],
    variables: List[sp.Symbol],
    verbose: bool = True
) -> AnalyticalVettingReport:
    """
    Comprehensive analytical vetting with detailed report.

    Args:
        candidates: New candidates to test
        hamiltonian: Hamiltonian of the system
        known_integrals: Known conserved quantities
        variables: Phase space variables
        verbose: Print progress

    Returns:
        AnalyticalVettingReport with complete results
    """
    vetter = AnalyticalVetter(hamiltonian, known_integrals, variables)
    report = vetter.vet_candidates(candidates, verbose)

    if verbose:
        print("\n")
        report.print_detailed_report()

    return report
