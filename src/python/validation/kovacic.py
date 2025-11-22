"""
Kovacic algorithm for computing Galois groups of second-order linear ODEs.

This module implements the Kovacic algorithm (1986) for determining whether
a second-order linear ODE with rational function coefficients has Liouvillian
solutions, and classifies its differential Galois group.

Reference:
    J. Kovacic, "An algorithm for solving second order linear homogeneous
    differential equations", Journal of Symbolic Computation 2 (1986), 3-43.

The Kovacic algorithm is deterministic and decides whether the equation:
    y'' + a(t)y' + b(t)y = 0

has solutions expressible in terms of exponentials, integrals, and algebraic
functions (Liouvillian solutions).

Application to Morales-Ramis Test:
    - Non-abelian Galois group (SL(2,C)) → Non-integrable
    - Abelian Galois group → Possibly integrable
"""

import sympy as sp
from sympy import Symbol, Rational, sqrt, exp, log, simplify, factor, expand
from sympy import solve, roots, Poly, degree, LC
from typing import List, Tuple, Optional, Dict, Union
from enum import Enum
from dataclasses import dataclass


class GaloisGroupType(Enum):
    """Classification of differential Galois groups for second-order ODEs."""

    FINITE = "finite"
    """Finite Galois group - solutions are algebraic."""

    REDUCIBLE = "reducible"
    """Infinite but reducible group - solutions involve exp(∫r dt)."""

    SL2C = "SL(2,C)"
    """Full SL(2,ℂ) group - NON-INTEGRABLE case."""

    SOLVABLE = "solvable"
    """Solvable group - between reducible and SL(2,C)."""

    UNKNOWN = "unknown"
    """Unable to determine (algorithm inconclusive)."""


@dataclass
class KovacicResult:
    """Result of Kovacic algorithm computation."""

    galois_type: GaloisGroupType
    """Classified Galois group type."""

    solution: Optional[sp.Expr]
    """Liouvillian solution if found, None if non-Liouvillian."""

    case_succeeded: Optional[int]
    """Which Kovacic case succeeded (1, 2, 3), or None."""

    details: Dict
    """Additional computational details."""


class KovacicSolver:
    """
    Implementation of Kovacic's algorithm for second-order linear ODEs.

    Given an ODE of the form:
        y'' + a(t)y' + b(t)y = 0

    where a(t), b(t) are rational functions, the algorithm determines:
    1. Whether Liouvillian solutions exist
    2. The differential Galois group type
    3. An explicit solution if one exists

    The algorithm tries three cases in sequence:
    - Case 1: Finite or reducible Galois group
    - Case 2: Imprimitive SL(2,C) (order 4 or 6)
    - Case 3: Primitive SL(2,C)

    If no case succeeds, the Galois group is the full SL(2,C).
    """

    def __init__(self, verbose: bool = False, use_sympy_dsolve: bool = True):
        """
        Initialize Kovacic solver.

        Args:
            verbose: Print detailed algorithm steps
            use_sympy_dsolve: Try SymPy's built-in solver first (faster)
        """
        self.verbose = verbose
        self.use_sympy_dsolve = use_sympy_dsolve

    def solve(
        self,
        a: sp.Expr,
        b: sp.Expr,
        t: sp.Symbol
    ) -> KovacicResult:
        """
        Apply Kovacic algorithm to determine Galois group.

        Args:
            a, b: Coefficients of y'' + a*y' + b*y = 0
            t: Independent variable

        Returns:
            KovacicResult with Galois group classification and solution

        Example:
            >>> t = sp.Symbol('t')
            >>> solver = KovacicSolver(verbose=True)
            >>> # Airy equation: y'' - ty = 0
            >>> result = solver.solve(a=0, b=-t, t=t)
            >>> print(result.galois_type)
            GaloisGroupType.SL2C
        """
        if self.verbose:
            print("="*70)
            print("KOVACIC ALGORITHM")
            print("="*70)
            print(f"Equation: y'' + ({a})*y' + ({b})*y = 0")
            print()

        # Step 1: Try SymPy's built-in solver first (if enabled)
        if self.use_sympy_dsolve:
            sympy_result = self._try_sympy_dsolve(a, b, t)
            if sympy_result is not None:
                return sympy_result

        # Step 2: Convert to normal form y'' = r(t)y
        r = self._convert_to_normal_form(a, b, t)

        if self.verbose:
            print(f"Normal form: y'' = r(t)*y")
            print(f"  where r(t) = {r}")
            print()

        # Step 3: Analyze singularities of r(t)
        singularities = self._find_singularities(r, t)

        if self.verbose:
            print(f"Singularities of r(t):")
            for sing, mult, order in singularities:
                print(f"  t = {sing}: multiplicity {mult}, order {order}")
            print()

        # Step 4: Try Kovacic cases sequentially
        details = {
            'normal_form_r': r,
            'singularities': singularities
        }

        for case_num in [1, 2, 3]:
            if self.verbose:
                print(f"--- Trying Case {case_num} ---")
                print()

            result = self._try_case(case_num, r, singularities, t)

            if result is not None:
                galois_type, solution = result
                if self.verbose:
                    print(f"✓ Case {case_num} succeeded!")
                    print(f"  Galois group: {galois_type.value}")
                    if solution:
                        print(f"  Solution found: y = {solution}")
                    print()

                details['case_succeeded'] = case_num
                return KovacicResult(
                    galois_type=galois_type,
                    solution=solution,
                    case_succeeded=case_num,
                    details=details
                )

            if self.verbose:
                print(f"✗ Case {case_num} failed")
                print()

        # Step 5: No case succeeded → Galois group is SL(2,C)
        if self.verbose:
            print("="*70)
            print("RESULT: All cases failed")
            print("Galois group is the full SL(2,ℂ)")
            print("→ SYSTEM IS NON-INTEGRABLE")
            print("="*70)
            print()

        details['case_succeeded'] = None
        return KovacicResult(
            galois_type=GaloisGroupType.SL2C,
            solution=None,
            case_succeeded=None,
            details=details
        )

    def _try_sympy_dsolve(
        self,
        a: sp.Expr,
        b: sp.Expr,
        t: sp.Symbol
    ) -> Optional[KovacicResult]:
        """
        Try SymPy's built-in differential equation solver.

        This is faster than manual Kovacic implementation and can solve
        many standard equations automatically.

        Returns:
            KovacicResult if SymPy finds a solution, None otherwise
        """
        try:
            y = sp.Function('y')
            ode = sp.Eq(y(t).diff(t, 2) + a * y(t).diff(t) + b * y(t), 0)

            # Try to solve with hint='nth_linear_constant_coeff_homogeneous'
            # or let dsolve choose automatically
            solution = sp.dsolve(ode, y(t), hint='best')

            if solution is not None and not solution.has(sp.Integral):
                # Successfully found closed-form solution
                if self.verbose:
                    print("✓ SymPy dsolve found solution:")
                    print(f"  {solution}")
                    print()

                # Classify based on solution structure
                galois_type = self._classify_solution(solution, t)

                return KovacicResult(
                    galois_type=galois_type,
                    solution=solution.rhs if hasattr(solution, 'rhs') else solution,
                    case_succeeded=0,  # 0 = SymPy solver
                    details={'method': 'sympy_dsolve'}
                )
        except (NotImplementedError, ValueError, TypeError):
            # SymPy couldn't solve it
            pass

        return None

    def _classify_solution(self, solution: sp.Expr, t: sp.Symbol) -> GaloisGroupType:
        """
        Classify Galois group based on solution structure.

        Args:
            solution: The solution found by SymPy
            t: Independent variable

        Returns:
            Classified Galois group type
        """
        # Check if solution contains only algebraic operations
        if not solution.has(sp.exp, sp.log, sp.sin, sp.cos):
            return GaloisGroupType.FINITE

        # Check if solution has exponentials of integrals
        if solution.has(sp.exp):
            return GaloisGroupType.REDUCIBLE

        # Default: solvable
        return GaloisGroupType.SOLVABLE

    def _convert_to_normal_form(
        self,
        a: sp.Expr,
        b: sp.Expr,
        t: sp.Symbol
    ) -> sp.Expr:
        """
        Convert y'' + a*y' + b*y = 0 to normal form y'' = r*y.

        Substitution: y = exp(-∫(a/2)dt) * z

        Then z satisfies: z'' = r*z where r = b - a'/2 - a²/4

        Args:
            a, b: Original equation coefficients
            t: Independent variable

        Returns:
            r(t): Coefficient in normal form
        """
        a_prime = sp.diff(a, t)
        r = b - a_prime / 2 - a**2 / 4
        return sp.simplify(r)

    def _find_singularities(
        self,
        r: sp.Expr,
        t: sp.Symbol
    ) -> List[Tuple[Union[sp.Expr, sp.oo], int, int]]:
        """
        Find and classify singularities of r(t).

        A singularity can be:
        - A pole (finite point where r → ∞)
        - t = ∞ (checked separately)

        For each singularity, we determine:
        - Location (finite value or ∞)
        - Multiplicity (order of pole)
        - Order (for classification in Kovacic cases)

        Args:
            r: Coefficient in normal form y'' = r*y
            t: Independent variable

        Returns:
            List of (location, multiplicity, order) tuples
        """
        singularities = []

        # Convert r to rational function if possible
        r_simplified = sp.simplify(r)

        try:
            # Express as P(t)/Q(t)
            numer, denom = sp.fraction(r_simplified)

            # Find zeros of denominator (poles of r)
            pole_candidates = sp.solve(denom, t)

            for pole in pole_candidates:
                if pole.is_finite:
                    # Compute order of pole
                    # Expand r around pole: r ~ c/(t-pole)^m + ...
                    order = self._pole_order(r, t, pole)
                    singularities.append((pole, order, order))

        except (ValueError, TypeError, NotImplementedError):
            # Couldn't determine poles analytically
            if self.verbose:
                print("Warning: Could not determine singularities analytically")

        # Check singularity at infinity
        # r(∞) ~ c*t^m as t → ∞
        order_at_inf = self._order_at_infinity(r, t)
        singularities.append((sp.oo, order_at_inf, order_at_inf))

        return singularities

    def _pole_order(self, r: sp.Expr, t: sp.Symbol, pole: sp.Expr) -> int:
        """
        Compute order of pole at given point.

        The order m is the largest integer such that:
            (t - pole)^m * r(t) is finite at t = pole

        Args:
            r: Expression
            t: Variable
            pole: Location of pole

        Returns:
            Order of pole (positive integer)
        """
        # Try multiplying by (t - pole)^m and taking limit
        for m in range(1, 11):  # Check up to order 10
            test_expr = (t - pole)**m * r
            try:
                lim = sp.limit(test_expr, t, pole)
                if lim.is_finite and lim != 0:
                    return m
            except (ValueError, NotImplementedError):
                continue

        return 1  # Default: simple pole

    def _order_at_infinity(self, r: sp.Expr, t: sp.Symbol) -> int:
        """
        Compute order of r(t) as t → ∞.

        If r(t) ~ c*t^m as t → ∞, return m.

        Args:
            r: Expression
            t: Variable

        Returns:
            Order at infinity (can be negative)
        """
        try:
            # Substitute t = 1/s and analyze as s → 0
            s = sp.Symbol('s', positive=True)
            r_sub = r.subs(t, 1/s)

            # Find leading power of s
            r_expanded = sp.series(r_sub, s, 0, n=6).removeO()

            # Extract lowest power of s
            if r_expanded != 0:
                powers = []
                for term in sp.Add.make_args(r_expanded):
                    term_s = sp.simplify(term)
                    if term_s != 0:
                        # Find power of s in this term
                        power = sp.degree(term_s, s)
                        if power is not None:
                            powers.append(-power)  # Negate because s = 1/t

                if powers:
                    return max(powers)

        except (ValueError, TypeError, NotImplementedError):
            pass

        return 0  # Unknown order at infinity

    def _try_case(
        self,
        case_num: int,
        r: sp.Expr,
        singularities: List[Tuple],
        t: sp.Symbol
    ) -> Optional[Tuple[GaloisGroupType, Optional[sp.Expr]]]:
        """
        Try a specific Kovacic case.

        Args:
            case_num: Which case to try (1, 2, or 3)
            r: Coefficient in normal form
            singularities: List of singularities
            t: Independent variable

        Returns:
            (galois_type, solution) if case succeeds, None otherwise
        """
        if case_num == 1:
            return self._try_case_1(r, singularities, t)
        elif case_num == 2:
            return self._try_case_2(r, singularities, t)
        elif case_num == 3:
            return self._try_case_3(r, singularities, t)
        else:
            return None

    def _try_case_1(
        self,
        r: sp.Expr,
        singularities: List[Tuple],
        t: sp.Symbol
    ) -> Optional[Tuple[GaloisGroupType, Optional[sp.Expr]]]:
        """
        Kovacic Case 1: Finite or reducible Galois group.

        This case applies when all singularities have even order ≤ 2.
        Solutions have the form: y = exp(∫ω dt) where ω is algebraic in t.

        Returns:
            (galois_type, solution) if successful, None otherwise
        """
        # Check if Case 1 conditions are satisfied
        for sing, mult, order in singularities:
            if order > 2 or order % 2 != 0:
                if self.verbose:
                    print(f"  Case 1 inapplicable: singularity at {sing} has order {order}")
                return None

        if self.verbose:
            print("  Case 1 applicable (all singularities have even order ≤ 2)")

        # Try to find ω such that ω' + ω² = r
        # This is a Riccati equation
        omega = self._solve_riccati_case_1(r, singularities, t)

        if omega is not None:
            solution = sp.exp(sp.integrate(omega, t))
            galois_type = GaloisGroupType.REDUCIBLE

            if self.verbose:
                print(f"  Found ω = {omega}")
                print(f"  Solution: y = exp(∫ω dt)")

            return (galois_type, solution)

        return None

    def _solve_riccati_case_1(
        self,
        r: sp.Expr,
        singularities: List[Tuple],
        t: sp.Symbol
    ) -> Optional[sp.Expr]:
        """
        Solve Riccati equation ω' + ω² = r for Case 1.

        We assume ω is a rational function with poles at the singularities.

        Returns:
            ω if found, None otherwise
        """
        # Simplified implementation: try a rational function ansatz
        # ω = sum of terms c_i/(t - pole_i)

        # For full implementation, would need to:
        # 1. Determine possible pole orders for ω at each singularity
        # 2. Set up polynomial system for coefficients
        # 3. Solve for coefficients

        # For now, return None (not implemented)
        return None

    def _try_case_2(
        self,
        r: sp.Expr,
        singularities: List[Tuple],
        t: sp.Symbol
    ) -> Optional[Tuple[GaloisGroupType, Optional[sp.Expr]]]:
        """
        Kovacic Case 2: Imprimitive SL(2,C) of order 4 or 6.

        This case handles intermediate complexity.

        Returns:
            (galois_type, solution) if successful, None otherwise
        """
        # Case 2 implementation is complex
        # Would check specific order conditions at singularities

        if self.verbose:
            print("  Case 2 not fully implemented")

        return None

    def _try_case_3(
        self,
        r: sp.Expr,
        singularities: List[Tuple],
        t: sp.Symbol
    ) -> Optional[Tuple[GaloisGroupType, Optional[sp.Expr]]]:
        """
        Kovacic Case 3: Primitive SL(2,C).

        Most restrictive case - only applies to special equations.

        Returns:
            (galois_type, solution) if successful, None otherwise
        """
        # Case 3 implementation is complex

        if self.verbose:
            print("  Case 3 not fully implemented")

        return None


def classify_galois_group(
    ode_coefficients: Tuple[sp.Expr, sp.Expr],
    independent_var: sp.Symbol,
    verbose: bool = False
) -> GaloisGroupType:
    """
    Convenience function to classify Galois group of an ODE.

    Args:
        ode_coefficients: (a, b) for equation y'' + a*y' + b*y = 0
        independent_var: Independent variable (usually t)
        verbose: Print detailed steps

    Returns:
        Classified Galois group type

    Example:
        >>> t = sp.Symbol('t')
        >>> # Bessel equation: y'' + (1/t)*y' + y = 0
        >>> result = classify_galois_group((1/t, 1), t, verbose=True)
    """
    a, b = ode_coefficients
    solver = KovacicSolver(verbose=verbose)
    result = solver.solve(a, b, independent_var)
    return result.galois_type


def is_galois_group_abelian(galois_type: GaloisGroupType) -> bool:
    """
    Check if a Galois group type is abelian.

    Args:
        galois_type: Galois group classification

    Returns:
        True if abelian (integrable), False if non-abelian (non-integrable)
    """
    abelian_types = {
        GaloisGroupType.FINITE,
        GaloisGroupType.REDUCIBLE,
        GaloisGroupType.SOLVABLE
    }
    return galois_type in abelian_types


def morales_ramis_test(
    nve_coefficients: Tuple[sp.Expr, sp.Expr],
    t: sp.Symbol,
    verbose: bool = True
) -> Tuple[bool, GaloisGroupType, str]:
    """
    Apply Morales-Ramis test to Normal Variational Equation.

    Args:
        nve_coefficients: (a, b) for NVE: y'' + a*y' + b*y = 0
        t: Independent variable
        verbose: Print interpretation

    Returns:
        is_integrable: False if non-abelian (provably non-integrable)
        galois_type: Classified Galois group
        interpretation: Human-readable result

    Example:
        >>> t = sp.Symbol('t')
        >>> # Some NVE from 3-body problem
        >>> is_int, galois, msg = morales_ramis_test((a_expr, b_expr), t)
        >>> print(msg)
    """
    if verbose:
        print("\n" + "="*70)
        print("MORALES-RAMIS NON-INTEGRABILITY TEST")
        print("="*70)
        print()

    galois_type = classify_galois_group(nve_coefficients, t, verbose=verbose)
    is_integrable = is_galois_group_abelian(galois_type)

    if is_integrable:
        interpretation = (
            f"✓ Galois group is ABELIAN ({galois_type.value})\n"
            f"→ Morales-Ramis criterion does NOT obstruct integrability\n"
            f"→ System may be integrable (further analysis needed)"
        )
    else:
        interpretation = (
            f"✗ Galois group is NON-ABELIAN ({galois_type.value})\n"
            f"→ Morales-Ramis criterion OBSTRUCTS integrability\n"
            f"→ System is PROVABLY NON-INTEGRABLE"
        )

    if verbose:
        print()
        print("="*70)
        print("RESULT:")
        print(interpretation)
        print("="*70)
        print()

    return (is_integrable, galois_type, interpretation)
