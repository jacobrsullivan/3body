"""
Functional independence tester for WP 4.1: Analytical Vetting.

This module tests whether a set of integrals are functionally independent
via Jacobian rank analysis.

This is the third of the three Liouville integrability criteria:
1. Conservation: {I_k, H} = 0  (conservation_validator.py)
2. Involution: {I_i, I_j} = 0  (involution_tester.py)
3. Independence: rank(∇I_1, ..., ∇I_n) = n  ✓ (this module)

Integrates with and enhances existing code from:
- analysis/independence_test.py
"""

import numpy as np
import sympy as sp
from typing import Dict, List, Optional, Union, Callable, Tuple
from dataclasses import dataclass
from scipy import linalg


@dataclass
class IndependenceTestResult:
    """
    Result of functional independence test.

    Attributes:
        is_independent: True if integrals are functionally independent
        rank_distribution: Dictionary mapping rank values to counts
        fraction_full_rank: Fraction of samples with full rank
        mean_rank: Mean rank across all samples
        std_rank: Standard deviation of rank
        n_integrals: Number of integrals tested
        n_samples: Number of random samples tested
        success_threshold: Threshold for fraction_full_rank
    """
    is_independent: bool
    rank_distribution: Dict[int, int]
    fraction_full_rank: float
    mean_rank: float
    std_rank: float
    n_integrals: int
    n_samples: int
    success_threshold: float

    def __str__(self) -> str:
        if self.is_independent:
            return f"✓ Independent: {100*self.fraction_full_rank:.1f}% full rank (>= {100*self.success_threshold:.1f}%)"
        else:
            return f"✗ Dependent: only {100*self.fraction_full_rank:.1f}% full rank (< {100*self.success_threshold:.1f}%)"

    def print_rank_distribution(self):
        """Print detailed rank distribution."""
        print("\nRank Distribution:")
        print("-" * 50)
        for rank in sorted(self.rank_distribution.keys()):
            count = self.rank_distribution[rank]
            pct = 100 * count / self.n_samples
            bar = "█" * int(pct / 2)  # Visual bar (max 50 chars)
            print(f"  Rank {rank}: {count:6d} ({pct:5.1f}%) {bar}")
        print("-" * 50)
        print(f"  Mean: {self.mean_rank:.2f} ± {self.std_rank:.2f}")


class IndependenceTester:
    """
    Test functional independence of integrals via Jacobian rank.

    Uses numerical rank computation on random samples to determine if
    gradients ∇I_1, ..., ∇I_n are linearly independent.

    Example:
        >>> import sympy as sp
        >>> q, p = sp.symbols('q p', real=True)
        >>> integrals = {
        ...     'E': (p**2 + q**2) / 2,
        ...     'not_independent': p**2 + q**2  # = 2*E (dependent!)
        ... }
        >>> tester = IndependenceTester()
        >>> result = tester.test_independence(integrals, variables=[q, p])
        >>> print(result.is_independent)
        >>> # False (integrals are linearly dependent)
    """

    def __init__(
        self,
        n_samples: int = 10000,
        rank_threshold: float = 0.995,
        tolerance: float = 1e-10,
        sampling_strategy: str = 'gaussian'
    ):
        """
        Initialize independence tester.

        Args:
            n_samples: Number of random samples for rank testing
            rank_threshold: Minimum fraction of samples with full rank
            tolerance: Tolerance for rank computation (singular value threshold)
            sampling_strategy: 'gaussian', 'uniform', or 'stratified'
        """
        self.n_samples = n_samples
        self.rank_threshold = rank_threshold
        self.tolerance = tolerance
        self.sampling_strategy = sampling_strategy

    def test_independence(
        self,
        integrals: Dict[str, Union[sp.Expr, Callable]],
        variables: List[sp.Symbol],
        verbose: bool = True
    ) -> IndependenceTestResult:
        """
        Test if integrals are functionally independent.

        Method: Compute Jacobian matrix at random points and check rank.

        Args:
            integrals: Dictionary of integral expressions
            variables: Phase space variables [q0, ..., p0, ...]
            verbose: Print progress

        Returns:
            IndependenceTestResult
        """
        n_integrals = len(integrals)
        n_vars = len(variables)

        if verbose:
            print("\n" + "=" * 70)
            print("FUNCTIONAL INDEPENDENCE TEST")
            print("=" * 70)
            print(f"  Integrals: {n_integrals}")
            print(f"  Variables: {n_vars}")
            print(f"  Samples: {self.n_samples}")
            print(f"  Threshold: {100*self.rank_threshold:.1f}% full rank")

        # Compute gradients symbolically
        if verbose:
            print("\nComputing gradients...")

        gradients = {}
        gradient_funcs = {}

        for name, integral in integrals.items():
            if isinstance(integral, sp.Expr):
                # Symbolic gradient
                grad = [sp.diff(integral, var) for var in variables]
                gradients[name] = grad

                # Convert to NumPy function
                try:
                    gradient_funcs[name] = sp.lambdify(variables, grad, 'numpy')
                except Exception as e:
                    if verbose:
                        print(f"Warning: Failed to lambdify gradient of {name}: {e}")
                    return self._failed_result(n_integrals)
            else:
                # Callable - would need numerical differentiation
                if verbose:
                    print(f"Warning: {name} is callable, using numerical differentiation")
                gradient_funcs[name] = lambda *args: self._numerical_gradient(
                    integral, list(args)
                )

        # Generate samples
        if verbose:
            print(f"\nSampling {self.n_samples} points ({self.sampling_strategy})...")

        samples = self._generate_samples(n_vars)

        # Compute ranks
        if verbose:
            print("Computing Jacobian ranks...")

        ranks = []
        n_failures = 0

        for i, sample in enumerate(samples):
            if verbose and i % 1000 == 0 and i > 0:
                print(f"  Progress: {i}/{self.n_samples}")

            # Build Jacobian matrix at this point
            jacobian = np.zeros((n_integrals, n_vars))

            try:
                for j, name in enumerate(integrals.keys()):
                    grad_val = gradient_funcs[name](*sample)

                    # Handle both array and scalar returns
                    if np.isscalar(grad_val):
                        grad_val = [grad_val]

                    grad_array = np.array(grad_val)

                    if grad_array.shape[0] != n_vars:
                        if verbose and i == 0:
                            print(f"Warning: gradient shape mismatch for {name}")
                        n_failures += 1
                        break

                    jacobian[j, :] = grad_array

                # Compute rank
                rank = np.linalg.matrix_rank(jacobian, tol=self.tolerance)
                ranks.append(rank)

            except Exception as e:
                # Evaluation failed (e.g., singular point)
                if verbose and i < 10:  # Only print first few failures
                    print(f"Warning: Evaluation failed at sample {i}: {e}")
                n_failures += 1
                ranks.append(0)

        if verbose and n_failures > 0:
            print(f"Warning: {n_failures}/{self.n_samples} evaluations failed")

        # Statistics
        ranks = np.array(ranks)
        unique_ranks, counts = np.unique(ranks, return_counts=True)
        rank_distribution = dict(zip([int(r) for r in unique_ranks], [int(c) for c in counts]))

        fraction_full_rank = np.sum(ranks == n_integrals) / len(ranks)
        is_independent = fraction_full_rank >= self.rank_threshold

        if verbose:
            print(f"\n{'='*70}")
            print("INDEPENDENCE SUMMARY")
            print(f"{'='*70}")
            print(f"  Full rank ({n_integrals}): {100*fraction_full_rank:.1f}%")

            if is_independent:
                print(f"  ✓ INDEPENDENT (>= {100*self.rank_threshold:.1f}% threshold)")
            else:
                print(f"  ✗ DEPENDENT (< {100*self.rank_threshold:.1f}% threshold)")

        result = IndependenceTestResult(
            is_independent=is_independent,
            rank_distribution=rank_distribution,
            fraction_full_rank=fraction_full_rank,
            mean_rank=float(np.mean(ranks)),
            std_rank=float(np.std(ranks)),
            n_integrals=n_integrals,
            n_samples=len(ranks),
            success_threshold=self.rank_threshold
        )

        if verbose:
            result.print_rank_distribution()
            print(f"{'='*70}\n")

        return result

    def _generate_samples(self, n_vars: int) -> np.ndarray:
        """Generate random samples in phase space."""
        if self.sampling_strategy == 'gaussian':
            return np.random.randn(self.n_samples, n_vars)
        elif self.sampling_strategy == 'uniform':
            return np.random.uniform(-2, 2, (self.n_samples, n_vars))
        elif self.sampling_strategy == 'stratified':
            # Mix of different scales
            samples = []
            n_per_scale = self.n_samples // 3
            samples.append(np.random.randn(n_per_scale, n_vars) * 0.1)  # Small
            samples.append(np.random.randn(n_per_scale, n_vars))  # Medium
            samples.append(np.random.randn(self.n_samples - 2*n_per_scale, n_vars) * 10)  # Large
            return np.vstack(samples)
        else:
            return np.random.randn(self.n_samples, n_vars)

    def _numerical_gradient(
        self,
        func: Callable,
        point: List[float],
        epsilon: float = 1e-6
    ) -> np.ndarray:
        """Compute numerical gradient via finite differences."""
        n = len(point)
        grad = np.zeros(n)

        for i in range(n):
            point_plus = point.copy()
            point_plus[i] += epsilon
            point_minus = point.copy()
            point_minus[i] -= epsilon

            try:
                grad[i] = (func(*point_plus) - func(*point_minus)) / (2 * epsilon)
            except Exception:
                grad[i] = 0.0

        return grad

    def _failed_result(self, n_integrals: int) -> IndependenceTestResult:
        """Return a failed result."""
        return IndependenceTestResult(
            is_independent=False,
            rank_distribution={0: self.n_samples},
            fraction_full_rank=0.0,
            mean_rank=0.0,
            std_rank=0.0,
            n_integrals=n_integrals,
            n_samples=self.n_samples,
            success_threshold=self.rank_threshold
        )


def quick_independence_check(
    integrals: Dict[str, sp.Expr],
    variables: List[sp.Symbol],
    threshold: float = 0.995,
    verbose: bool = True
) -> bool:
    """
    Quick check: are integrals functionally independent?

    Convenience function for simple yes/no answer.

    Args:
        integrals: Dictionary of integrals to test
        variables: Phase space variables
        threshold: Minimum fraction of samples with full rank
        verbose: Print results

    Returns:
        True if integrals are independent
    """
    tester = IndependenceTester(rank_threshold=threshold)
    result = tester.test_independence(integrals, variables, verbose)
    return result.is_independent


def check_liouville_independence(
    integrals: Dict[str, sp.Expr],
    variables: List[sp.Symbol],
    verbose: bool = True
) -> IndependenceTestResult:
    """
    Check Liouville independence criterion for integrability.

    This is the third of three Liouville criteria.

    Args:
        integrals: Dictionary of candidate integrals
        variables: Phase space variables
        verbose: Print detailed results

    Returns:
        IndependenceTestResult
    """
    tester = IndependenceTester(rank_threshold=0.995)
    return tester.test_independence(integrals, variables, verbose)


def analyze_integral_structure(
    integrals: Dict[str, sp.Expr],
    variables: List[sp.Symbol],
    verbose: bool = True
) -> Dict:
    """
    Complete analysis of integral structure.

    Performs multiple tests to characterize the integrals:
    - Functional independence
    - Approximate dependencies
    - Rank deficiency patterns

    Args:
        integrals: Dictionary of integrals
        variables: Phase space variables
        verbose: Print detailed analysis

    Returns:
        Dictionary with analysis results
    """
    tester = IndependenceTester(n_samples=10000)
    result = tester.test_independence(integrals, variables, verbose)

    analysis = {
        'independence_result': result,
        'is_independent': result.is_independent,
        'mean_rank': result.mean_rank,
        'rank_stability': 1.0 - result.std_rank / max(result.mean_rank, 1.0)
    }

    if verbose and not result.is_independent:
        print("\nDETAILED ANALYSIS:")
        print("-" * 70)
        print(f"Mean rank: {result.mean_rank:.2f} (expected {result.n_integrals})")
        print(f"Rank deficiency: {result.n_integrals - result.mean_rank:.2f}")
        print("\nPossible causes:")
        print("  - One or more integrals are linear combinations of others")
        print("  - Integrals are only independent in a restricted region")
        print("  - Numerical issues (try increasing tolerance)")

    return analysis
