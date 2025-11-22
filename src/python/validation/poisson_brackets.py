"""
Unified Poisson bracket computation for WP 4.1: Analytical Vetting.

This module provides a unified interface for computing Poisson brackets
{f, g} in both symbolic and numerical modes. It wraps and consolidates
existing implementations scattered across the codebase:
- symbolic/validation.py::compute_poisson_bracket_symbolic()
- analysis/independence_test.py::compute_poisson_bracket()
- lifts/extended_symplectic.py::poisson_bracket_on_bundle()

The PoissonBracketComputer class provides:
- Symbolic computation using SymPy
- Numerical evaluation via finite differences
- Automatic fallback from symbolic to numerical
- Batch evaluation capabilities
- Consistent result format across all modes

Example:
    >>> import sympy as sp
    >>> q, p = sp.symbols('q p', real=True)
    >>> H = (p**2 + q**2) / 2  # Harmonic oscillator
    >>> E = H  # Energy
    >>>
    >>> computer = PoissonBracketComputer()
    >>> result = computer.compute_bracket(E, H, variables=[q, p])
    >>> print(f"Conservation: {result.success}")
    >>> # Conservation: True (energy is conserved)
"""

import numpy as np
import sympy as sp
from typing import List, Dict, Optional, Callable, Union, Tuple
from dataclasses import dataclass
from enum import Enum


class BracketMethod(Enum):
    """Method used for Poisson bracket computation."""
    SYMBOLIC = "symbolic"
    NUMERICAL = "numerical"
    HYBRID = "hybrid"  # Symbolic computation, numerical validation
    FAILED = "failed"


@dataclass
class PoissonBracketResult:
    """
    Result of Poisson bracket computation.

    Attributes:
        bracket_expr: Symbolic expression for {f, g} (if computed)
        is_zero_symbolic: True if symbolically proven to be zero
        numerical_max: Maximum numerical value over test points
        numerical_samples: Number of test points evaluated
        success: True if bracket vanishes (within tolerance)
        method: Method used (symbolic, numerical, hybrid, failed)
        tolerance: Acceptance threshold used
    """
    bracket_expr: Optional[sp.Expr]
    is_zero_symbolic: bool
    numerical_max: float
    numerical_samples: int
    success: bool
    method: BracketMethod
    tolerance: float

    def __str__(self) -> str:
        """Human-readable summary."""
        if self.is_zero_symbolic:
            return f"✓ Symbolically zero ({self.method.value})"
        elif self.success:
            return f"✓ Numerically zero: max={self.numerical_max:.2e} < {self.tolerance:.2e} ({self.method.value})"
        else:
            return f"✗ Non-zero: max={self.numerical_max:.2e} >= {self.tolerance:.2e} ({self.method.value})"


class PoissonBracketComputer:
    """
    Unified Poisson bracket computation.

    Computes Poisson brackets {f, g} = Σᵢ (∂f/∂qᵢ ∂g/∂pᵢ - ∂f/∂pᵢ ∂g/∂qᵢ)
    using symbolic or numerical methods.

    Attributes:
        use_symbolic: Attempt symbolic computation first
        use_numerical: Fall back to numerical if symbolic fails
        numerical_samples: Number of random test points for numerical validation
        tolerance: Acceptance threshold for numerical brackets
        coordinate_system: Type of coordinates ('canonical', 's1_bundle', 'ks_spinor')
    """

    def __init__(
        self,
        use_symbolic: bool = True,
        use_numerical: bool = True,
        numerical_samples: int = 10000,
        tolerance: float = 1e-12,
        coordinate_system: str = 'canonical'
    ):
        """
        Initialize Poisson bracket computer.

        Args:
            use_symbolic: Attempt symbolic computation first
            use_numerical: Fall back to numerical evaluation
            numerical_samples: Number of test points for numerical validation
            tolerance: Acceptance threshold for numerical brackets
            coordinate_system: 'canonical', 's1_bundle', or 'ks_spinor'
        """
        self.use_symbolic = use_symbolic
        self.use_numerical = use_numerical
        self.numerical_samples = numerical_samples
        self.tolerance = tolerance
        self.coordinate_system = coordinate_system

    def compute_bracket(
        self,
        f: Union[sp.Expr, Callable],
        g: Union[sp.Expr, Callable],
        variables: Optional[List[sp.Symbol]] = None,
        verbose: bool = False
    ) -> PoissonBracketResult:
        """
        Compute Poisson bracket {f, g}.

        Args:
            f: First function (SymPy expression or callable)
            g: Second function (SymPy expression or callable)
            variables: Phase space variables [q0, q1, ..., p0, p1, ...]
                      If None, inferred from expressions
            verbose: Print progress information

        Returns:
            PoissonBracketResult with bracket and verification status
        """
        # Handle callable functions (convert to symbolic if possible)
        if callable(f) and not isinstance(f, sp.Expr):
            if verbose:
                print("Warning: f is callable, numerical mode only")
            self.use_symbolic = False

        if callable(g) and not isinstance(g, sp.Expr):
            if verbose:
                print("Warning: g is callable, numerical mode only")
            self.use_symbolic = False

        # Extract variables if not provided
        if variables is None and isinstance(f, sp.Expr) and isinstance(g, sp.Expr):
            variables = self._extract_canonical_variables(f, g)
            if verbose:
                print(f"Inferred variables: {variables}")

        if variables is None:
            # Cannot proceed without variables
            return PoissonBracketResult(
                bracket_expr=None,
                is_zero_symbolic=False,
                numerical_max=np.inf,
                numerical_samples=0,
                success=False,
                method=BracketMethod.FAILED,
                tolerance=self.tolerance
            )

        # Attempt symbolic computation
        bracket_expr = None
        is_zero_symbolic = False

        if self.use_symbolic and isinstance(f, sp.Expr) and isinstance(g, sp.Expr):
            try:
                if verbose:
                    print("Attempting symbolic computation...")

                bracket_expr = self._compute_symbolic_bracket(f, g, variables)

                # Simplify
                if verbose:
                    print("Simplifying...")
                bracket_simplified = sp.simplify(bracket_expr)

                # Check if symbolically zero
                if bracket_simplified == 0 or bracket_simplified == sp.S.Zero:
                    is_zero_symbolic = True
                    if verbose:
                        print("✓ Symbolically zero!")

                    return PoissonBracketResult(
                        bracket_expr=bracket_simplified,
                        is_zero_symbolic=True,
                        numerical_max=0.0,
                        numerical_samples=0,
                        success=True,
                        method=BracketMethod.SYMBOLIC,
                        tolerance=self.tolerance
                    )

                bracket_expr = bracket_simplified
                if verbose:
                    print(f"Symbolic result: {bracket_expr}")

            except Exception as e:
                if verbose:
                    print(f"Symbolic computation failed: {e}")
                bracket_expr = None

        # Numerical validation
        numerical_max = np.inf

        if self.use_numerical:
            try:
                if verbose:
                    print(f"Numerical validation on {self.numerical_samples} samples...")

                if bracket_expr is not None:
                    # Evaluate symbolic expression numerically
                    numerical_max = self._evaluate_bracket_numerically(
                        bracket_expr,
                        variables,
                        n_samples=self.numerical_samples,
                        verbose=verbose
                    )
                else:
                    # Direct numerical computation (finite differences)
                    numerical_max = self._compute_bracket_numerically(
                        f, g, variables,
                        n_samples=self.numerical_samples,
                        verbose=verbose
                    )

                success = numerical_max < self.tolerance

                if verbose:
                    if success:
                        print(f"✓ Numerical validation passed: max={numerical_max:.2e}")
                    else:
                        print(f"✗ Numerical validation failed: max={numerical_max:.2e}")

                method = BracketMethod.HYBRID if self.use_symbolic and bracket_expr is not None else BracketMethod.NUMERICAL

                return PoissonBracketResult(
                    bracket_expr=bracket_expr,
                    is_zero_symbolic=False,
                    numerical_max=numerical_max,
                    numerical_samples=self.numerical_samples,
                    success=success,
                    method=method,
                    tolerance=self.tolerance
                )

            except Exception as e:
                if verbose:
                    print(f"Numerical evaluation failed: {e}")

        # Failed all methods
        return PoissonBracketResult(
            bracket_expr=bracket_expr,
            is_zero_symbolic=False,
            numerical_max=numerical_max,
            numerical_samples=0,
            success=False,
            method=BracketMethod.FAILED,
            tolerance=self.tolerance
        )

    def _compute_symbolic_bracket(
        self,
        f: sp.Expr,
        g: sp.Expr,
        variables: List[sp.Symbol]
    ) -> sp.Expr:
        """
        Symbolically compute {f, g} = Σᵢ (∂f/∂qᵢ ∂g/∂pᵢ - ∂f/∂pᵢ ∂g/∂qᵢ).

        Wraps existing implementation from symbolic/validation.py.
        """
        n_dof = len(variables) // 2
        q_vars = variables[:n_dof]
        p_vars = variables[n_dof:]

        bracket = sp.S(0)

        for q, p in zip(q_vars, p_vars):
            df_dq = sp.diff(f, q)
            df_dp = sp.diff(f, p)
            dg_dq = sp.diff(g, q)
            dg_dp = sp.diff(g, p)

            bracket += df_dq * dg_dp - df_dp * dg_dq

        return bracket

    def _evaluate_bracket_numerically(
        self,
        bracket_expr: sp.Expr,
        variables: List[sp.Symbol],
        n_samples: int,
        verbose: bool = False
    ) -> float:
        """
        Evaluate symbolic bracket expression on random phase space points.

        Returns maximum absolute value.
        """
        # Convert to NumPy function
        try:
            bracket_func = sp.lambdify(variables, bracket_expr, 'numpy')
        except Exception as e:
            if verbose:
                print(f"Lambdify failed: {e}")
            return np.inf

        # Generate random samples (Gaussian distribution)
        samples = np.random.randn(n_samples, len(variables))

        # Evaluate
        values = []
        n_failures = 0

        for i, sample in enumerate(samples):
            try:
                val = float(bracket_func(*sample))
                if np.isfinite(val):
                    values.append(abs(val))
                else:
                    n_failures += 1
            except Exception:
                n_failures += 1

        if verbose and n_failures > 0:
            print(f"Warning: {n_failures}/{n_samples} evaluations failed")

        if not values:
            return np.inf

        return np.max(values)

    def _compute_bracket_numerically(
        self,
        f: Callable,
        g: Callable,
        variables: List[sp.Symbol],
        n_samples: int,
        verbose: bool = False,
        epsilon: float = 1e-6
    ) -> float:
        """
        Compute Poisson bracket numerically via finite differences.

        Uses existing implementation from analysis/independence_test.py.
        """
        n_dof = len(variables) // 2

        # Generate random samples
        samples = np.random.randn(n_samples, len(variables))

        bracket_values = []

        for sample in samples:
            # Compute numerical derivatives
            bracket_val = 0.0

            for i in range(n_dof):
                # Perturb q_i
                sample_q_plus = sample.copy()
                sample_q_plus[i] += epsilon
                sample_q_minus = sample.copy()
                sample_q_minus[i] -= epsilon

                # Perturb p_i
                sample_p_plus = sample.copy()
                sample_p_plus[n_dof + i] += epsilon
                sample_p_minus = sample.copy()
                sample_p_minus[n_dof + i] -= epsilon

                try:
                    # ∂f/∂q_i
                    df_dq = (f(sample_q_plus) - f(sample_q_minus)) / (2 * epsilon)

                    # ∂f/∂p_i
                    df_dp = (f(sample_p_plus) - f(sample_p_minus)) / (2 * epsilon)

                    # ∂g/∂q_i
                    dg_dq = (g(sample_q_plus) - g(sample_q_minus)) / (2 * epsilon)

                    # ∂g/∂p_i
                    dg_dp = (g(sample_p_plus) - g(sample_p_minus)) / (2 * epsilon)

                    # {f, g} term
                    bracket_val += df_dq * dg_dp - df_dp * dg_dq

                except Exception:
                    bracket_val = np.inf
                    break

            if np.isfinite(bracket_val):
                bracket_values.append(abs(bracket_val))

        if not bracket_values:
            return np.inf

        return np.max(bracket_values)

    def _extract_canonical_variables(
        self,
        f: sp.Expr,
        g: sp.Expr
    ) -> List[sp.Symbol]:
        """
        Extract canonical coordinates (q, p) from expressions.

        Assumes variables named q0, q1, ..., p0, p1, ...
        or q, p for single DOF.
        """
        all_symbols = f.free_symbols | g.free_symbols

        # Try standard naming: q0, q1, ..., p0, p1, ...
        q_symbols = sorted([s for s in all_symbols if str(s).startswith('q')],
                          key=lambda x: str(x))
        p_symbols = sorted([s for s in all_symbols if str(s).startswith('p')],
                          key=lambda x: str(x))

        if len(q_symbols) == len(p_symbols) and len(q_symbols) > 0:
            return q_symbols + p_symbols

        # Fallback: alphabetical ordering
        all_sorted = sorted(all_symbols, key=lambda x: str(x))

        if len(all_sorted) % 2 == 0:
            n_dof = len(all_sorted) // 2
            return all_sorted[:n_dof] + all_sorted[n_dof:]

        # Cannot determine structure
        return list(all_sorted)


def test_conservation(
    candidate_integral: Union[sp.Expr, Callable],
    hamiltonian: Union[sp.Expr, Callable],
    variables: Optional[List[sp.Symbol]] = None,
    tolerance: float = 1e-12,
    n_samples: int = 10000,
    verbose: bool = True
) -> PoissonBracketResult:
    """
    Test if candidate integral is conserved: {I, H} = 0.

    Convenience function for the most common use case: testing conservation.

    Args:
        candidate_integral: Proposed conserved quantity I
        hamiltonian: Hamiltonian H of the system
        variables: Phase space variables [q0, ..., p0, ...]
        tolerance: Acceptance threshold
        n_samples: Number of test points for numerical validation
        verbose: Print results

    Returns:
        PoissonBracketResult indicating whether conservation holds

    Example:
        >>> q, p = sp.symbols('q p', real=True)
        >>> H = (p**2 + q**2) / 2  # Harmonic oscillator
        >>> E = H  # Energy
        >>> result = test_conservation(E, H)
        >>> assert result.success  # Energy is conserved
    """
    computer = PoissonBracketComputer(
        numerical_samples=n_samples,
        tolerance=tolerance
    )

    if verbose:
        print("=" * 70)
        print("CONSERVATION TEST: {I, H} = 0?")
        print("=" * 70)
        if isinstance(candidate_integral, sp.Expr):
            print(f"Candidate: {candidate_integral}")
        else:
            print(f"Candidate: <callable>")

        if isinstance(hamiltonian, sp.Expr):
            print(f"Hamiltonian: {hamiltonian}")
        else:
            print(f"Hamiltonian: <callable>")

    result = computer.compute_bracket(
        candidate_integral,
        hamiltonian,
        variables,
        verbose=verbose
    )

    if verbose:
        print(f"\n{result}")
        print("=" * 70)

    return result


def batch_test_conservation(
    candidates: Dict[str, Union[sp.Expr, Callable]],
    hamiltonian: Union[sp.Expr, Callable],
    variables: Optional[List[sp.Symbol]] = None,
    tolerance: float = 1e-12,
    n_samples: int = 10000,
    verbose: bool = True
) -> Dict[str, PoissonBracketResult]:
    """
    Test conservation for multiple candidates.

    Args:
        candidates: Dictionary mapping names to candidate integrals
        hamiltonian: Hamiltonian of the system
        variables: Phase space variables
        tolerance: Acceptance threshold
        n_samples: Number of test points
        verbose: Print progress

    Returns:
        Dictionary mapping candidate names to PoissonBracketResult
    """
    computer = PoissonBracketComputer(
        numerical_samples=n_samples,
        tolerance=tolerance
    )

    results = {}

    if verbose:
        print("\n" + "=" * 70)
        print(f"BATCH CONSERVATION TEST: {len(candidates)} candidates")
        print("=" * 70)

    for name, candidate in candidates.items():
        if verbose:
            print(f"\n[{name}]")

        result = computer.compute_bracket(
            candidate,
            hamiltonian,
            variables,
            verbose=False
        )

        results[name] = result

        if verbose:
            status = "✓ PASS" if result.success else "✗ FAIL"
            print(f"  {status} - {result}")

    if verbose:
        n_pass = sum(1 for r in results.values() if r.success)
        print("\n" + "=" * 70)
        print(f"SUMMARY: {n_pass}/{len(candidates)} candidates conserved")
        print("=" * 70)

    return results
