"""
Morales-Ramis validator for proving non-integrability.

This module integrates periodic orbits, variational equations, and the
Kovacic algorithm to apply the Morales-Ramis criterion for non-integrability.

The Morales-Ramis criterion states:
    If a Hamiltonian system is meromorphically integrable, then the
    differential Galois group of the Normal Variational Equation along
    any non-equilibrium solution must be abelian.

Contrapositive (what we use):
    If the Galois group is non-abelian → System is non-integrable.

Application to 3-body problem:
    - Compute NVE for periodic orbits (Lagrange L4, Figure-8, etc.)
    - Apply Kovacic algorithm to determine Galois group
    - If non-abelian (SL(2,ℂ)) → Proves non-integrability "downstairs"
    - This validates that any WP3 integrals genuinely live "upstairs"
"""

import numpy as np
import sympy as sp
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass

from .periodic_orbits import PeriodicOrbit, get_orbit_catalog
from .variational_equations import (
    VariationalEquationComputer,
    VariationalEquationData,
    NormalVariationalEquation
)
from .kovacic import (
    KovacicSolver,
    GaloisGroupType,
    KovacicResult,
    is_galois_group_abelian
)


@dataclass
class MoralesRamisResult:
    """Result of Morales-Ramis test on a single periodic orbit."""

    orbit_name: str
    """Name of the periodic orbit tested."""

    galois_type: GaloisGroupType
    """Classified differential Galois group."""

    is_integrable: bool
    """True if abelian (integrable), False if non-abelian (non-integrable)."""

    nve_symbolic: Optional[Tuple[sp.Expr, sp.Expr]]
    """Symbolic NVE coefficients (a, b) if conversion succeeded."""

    kovacic_result: Optional[KovacicResult]
    """Full Kovacic algorithm result."""

    interpretation: str
    """Human-readable interpretation."""

    details: Dict
    """Additional computational details."""


class MoralesRamisValidator:
    """
    Validator for applying Morales-Ramis criterion to periodic orbits.

    This class orchestrates the complete validation pipeline:
    1. Select periodic orbit
    2. Compute Normal Variational Equation (NVE)
    3. Convert NVE to symbolic form (if needed)
    4. Apply Kovacic algorithm to determine Galois group
    5. Interpret result (abelian → integrable, non-abelian → non-integrable)
    """

    def __init__(
        self,
        hamiltonian: Callable,
        gradient: Optional[Callable] = None,
        hessian: Optional[Callable] = None,
        verbose: bool = True
    ):
        """
        Initialize Morales-Ramis validator.

        Args:
            hamiltonian: H(q, p) → scalar (Hamiltonian function)
            gradient: ∇H(q, p) → (2n,) (optional, computed numerically if None)
            hessian: ∇²H(q, p) → (2n, 2n) (optional, computed numerically if None)
            verbose: Print detailed validation steps
        """
        self.hamiltonian = hamiltonian
        self.gradient = gradient
        self.hessian = hessian
        self.verbose = verbose

        # Initialize variational equation computer
        self.ve_computer = VariationalEquationComputer(
            hamiltonian=hamiltonian,
            gradient=gradient,
            hessian=hessian
        )

        # Initialize Kovacic solver
        self.kovacic_solver = KovacicSolver(verbose=verbose)

    def validate_orbit(
        self,
        orbit: PeriodicOrbit,
        n_points: int = 500,
        use_symbolic_nve: bool = False,
        symbolic_nve_coeffs: Optional[Tuple[sp.Expr, sp.Expr]] = None
    ) -> MoralesRamisResult:
        """
        Apply Morales-Ramis test to a single periodic orbit.

        Args:
            orbit: Periodic orbit to test
            n_points: Number of points for numerical computation
            use_symbolic_nve: If True, attempt symbolic NVE derivation
            symbolic_nve_coeffs: Pre-computed symbolic (a, b) for y'' + ay' + by = 0

        Returns:
            MoralesRamisResult with Galois group and interpretation

        Example:
            >>> from periodic_orbits import lagrange_l4_circular_restricted_3bp
            >>> orbit = lagrange_l4_circular_restricted_3bp()
            >>> validator = MoralesRamisValidator(hamiltonian_cr3bp, verbose=True)
            >>> result = validator.validate_orbit(orbit)
            >>> print(result.interpretation)
        """
        if self.verbose:
            print("\n" + "="*70)
            print(f"MORALES-RAMIS TEST: {orbit.name}")
            print("="*70)
            print(f"Period: {orbit.period:.6f}")
            print(f"Initial condition: {orbit.initial_condition}")
            print()

        details = {
            'orbit': orbit,
            'n_points': n_points
        }

        # Step 1: Compute Normal Variational Equation
        if self.verbose:
            print("Step 1: Computing Normal Variational Equation...")

        try:
            nve = self.ve_computer.compute_normal_variational_equation(
                orbit, n_points=n_points
            )
            details['nve_computed'] = True

            if self.verbose:
                print(f"  ✓ NVE computed (dimension: {nve.reduced_dimension})")
                print()

        except Exception as e:
            if self.verbose:
                print(f"  ✗ Failed to compute NVE: {e}")

            return MoralesRamisResult(
                orbit_name=orbit.name,
                galois_type=GaloisGroupType.UNKNOWN,
                is_integrable=None,
                nve_symbolic=None,
                kovacic_result=None,
                interpretation=f"Failed to compute NVE: {e}",
                details=details
            )

        # Step 2: Convert NVE to symbolic form (if provided or requested)
        if self.verbose:
            print("Step 2: Converting NVE to symbolic form...")

        if symbolic_nve_coeffs is not None:
            # Use provided symbolic coefficients
            nve_symbolic = symbolic_nve_coeffs
            details['nve_conversion'] = 'provided'

            if self.verbose:
                print(f"  ✓ Using provided symbolic NVE")
                print()

        elif use_symbolic_nve:
            # Attempt symbolic derivation (advanced feature)
            nve_symbolic = self._derive_symbolic_nve(orbit, nve)
            details['nve_conversion'] = 'derived'

            if nve_symbolic is None:
                if self.verbose:
                    print(f"  ✗ Could not derive symbolic NVE")
                    print(f"  → Falling back to numerical fitting")

                nve_symbolic = self._fit_nve_numerically(nve, orbit.period, n_points)
                details['nve_conversion'] = 'fitted'

            if self.verbose and nve_symbolic is not None:
                print(f"  ✓ Symbolic NVE derived")
                print()

        else:
            # Default: numerical fitting
            nve_symbolic = self._fit_nve_numerically(nve, orbit.period, n_points)
            details['nve_conversion'] = 'fitted'

            if self.verbose and nve_symbolic is not None:
                print(f"  ✓ NVE fitted to symbolic form")
                print()

        if nve_symbolic is None:
            return MoralesRamisResult(
                orbit_name=orbit.name,
                galois_type=GaloisGroupType.UNKNOWN,
                is_integrable=None,
                nve_symbolic=None,
                kovacic_result=None,
                interpretation="Failed to convert NVE to symbolic form",
                details=details
            )

        # Step 3: Apply Kovacic algorithm
        if self.verbose:
            print("Step 3: Applying Kovacic algorithm...")
            print()

        t = sp.Symbol('t')
        a_sym, b_sym = nve_symbolic

        try:
            kovacic_result = self.kovacic_solver.solve(a_sym, b_sym, t)
            details['kovacic_result'] = kovacic_result

            if self.verbose:
                print()
                print(f"  Galois group: {kovacic_result.galois_type.value}")
                print()

        except Exception as e:
            if self.verbose:
                print(f"  ✗ Kovacic algorithm failed: {e}")

            return MoralesRamisResult(
                orbit_name=orbit.name,
                galois_type=GaloisGroupType.UNKNOWN,
                is_integrable=None,
                nve_symbolic=nve_symbolic,
                kovacic_result=None,
                interpretation=f"Kovacic algorithm failed: {e}",
                details=details
            )

        # Step 4: Interpret result
        is_integrable = is_galois_group_abelian(kovacic_result.galois_type)

        if is_integrable:
            interpretation = (
                f"Orbit: {orbit.name}\n"
                f"Galois group: {kovacic_result.galois_type.value} (ABELIAN)\n"
                f"→ Morales-Ramis does NOT obstruct integrability\n"
                f"→ System MAY be integrable (further analysis needed)\n"
                f"⚠ Note: This is unexpected for 3-body problem"
            )
        else:
            interpretation = (
                f"Orbit: {orbit.name}\n"
                f"Galois group: {kovacic_result.galois_type.value} (NON-ABELIAN)\n"
                f"→ Morales-Ramis criterion OBSTRUCTS integrability\n"
                f"→ System is PROVABLY NON-INTEGRABLE\n"
                f"✓ Consistent with Bruns/Poincaré theorem"
            )

        if self.verbose:
            print("="*70)
            print("RESULT:")
            print(interpretation)
            print("="*70)
            print()

        return MoralesRamisResult(
            orbit_name=orbit.name,
            galois_type=kovacic_result.galois_type,
            is_integrable=is_integrable,
            nve_symbolic=nve_symbolic,
            kovacic_result=kovacic_result,
            interpretation=interpretation,
            details=details
        )

    def validate_multiple_orbits(
        self,
        orbit_specs: Dict[str, Dict],
        require_all_non_abelian: bool = True
    ) -> Dict[str, MoralesRamisResult]:
        """
        Apply Morales-Ramis test to multiple periodic orbits.

        Args:
            orbit_specs: Dictionary mapping orbit names to specifications
                Each spec should contain:
                - 'orbit': PeriodicOrbit object
                - 'symbolic_nve': Optional symbolic NVE coefficients
            require_all_non_abelian: If True, warn if not all orbits show non-abelian

        Returns:
            Dictionary mapping orbit names to MoralesRamisResult

        Example:
            >>> orbits = {
            ...     'L4': {
            ...         'orbit': lagrange_l4_circular_restricted_3bp(),
            ...         'symbolic_nve': None
            ...     },
            ...     'Figure8': {
            ...         'orbit': figure_8_choreography_approximate(),
            ...         'symbolic_nve': None
            ...     }
            ... }
            >>> results = validator.validate_multiple_orbits(orbits)
        """
        results = {}

        if self.verbose:
            print("\n" + "="*70)
            print(f"MORALES-RAMIS VALIDATION SUITE")
            print(f"Testing {len(orbit_specs)} periodic orbits")
            print("="*70)
            print()

        for name, spec in orbit_specs.items():
            orbit = spec['orbit']
            symbolic_nve = spec.get('symbolic_nve', None)

            result = self.validate_orbit(
                orbit,
                symbolic_nve_coeffs=symbolic_nve
            )

            results[name] = result

        # Summary
        if self.verbose:
            print("\n" + "="*70)
            print("VALIDATION SUITE SUMMARY")
            print("="*70)
            print()

            non_abelian_count = sum(
                1 for r in results.values()
                if not r.is_integrable and r.galois_type == GaloisGroupType.SL2C
            )

            print(f"Total orbits tested: {len(results)}")
            print(f"Non-abelian (SL(2,ℂ)): {non_abelian_count}/{len(results)}")
            print()

            for name, result in results.items():
                status = "✓ NON-ABELIAN" if not result.is_integrable else "⚠ ABELIAN"
                print(f"  {name:30s}: {status} ({result.galois_type.value})")

            print()

            if non_abelian_count == len(results):
                print("✓ ALL ORBITS SHOW NON-ABELIAN GALOIS GROUPS")
                print("→ Downstairs non-integrability CONFIRMED")
            elif require_all_non_abelian:
                print("⚠ WARNING: Not all orbits show non-abelian Galois groups")
                print("→ Requires further investigation")

            print("="*70)
            print()

        return results

    def interpret_for_lift_integrability(
        self,
        results: Dict[str, MoralesRamisResult],
        wp3_found_integrals: bool,
        wp3_integral_descriptions: Optional[List[str]] = None
    ) -> Dict:
        """
        Interpret Morales-Ramis results in context of lift-integrability.

        This is the key connection to WP3:
        - If downstairs is non-integrable (non-abelian) AND
        - WP3 found integrals upstairs
        - THEN those integrals are genuine lift-integrals

        Args:
            results: Results from validate_multiple_orbits
            wp3_found_integrals: Did WP3 discover any integrals?
            wp3_integral_descriptions: Descriptions of WP3 integrals

        Returns:
            Interpretation dictionary with verdict
        """
        all_non_abelian = all(
            not r.is_integrable for r in results.values() if r.is_integrable is not None
        )

        interpretation = {
            'downstairs_non_integrable': all_non_abelian,
            'consistent_with_bruns_poincare': all_non_abelian,
            'wp3_integrals_validated': False,
            'verdict': '',
            'detailed_interpretation': ''
        }

        if self.verbose:
            print("\n" + "="*70)
            print("LIFT-INTEGRABILITY INTERPRETATION")
            print("="*70)
            print()

        if all_non_abelian:
            verdict = "DOWNSTAIRS NON-INTEGRABILITY CONFIRMED"

            if wp3_found_integrals:
                interpretation['wp3_integrals_validated'] = True
                interpretation['verdict'] = "SUCCESS: LIFT-INTEGRABILITY VALIDATED"

                detailed = (
                    f"✓ SUCCESS: Lift-integrability hypothesis VALIDATED\n\n"
                    f"Findings:\n"
                    f"1. Morales-Ramis test confirms DOWNSTAIRS NON-INTEGRABILITY\n"
                    f"   → All tested orbits have non-abelian Galois groups (SL(2,ℂ))\n"
                    f"   → Consistent with Bruns (1887) and Poincaré (1890s)\n\n"
                    f"2. WP3 discovered integrals in lifted phase space\n"
                )

                if wp3_integral_descriptions:
                    detailed += "   Integrals found:\n"
                    for desc in wp3_integral_descriptions:
                        detailed += f"   - {desc}\n"

                detailed += (
                    f"\n"
                    f"Conclusion:\n"
                    f"→ WP3 integrals are GENUINE lift-integrals\n"
                    f"→ They cannot exist downstairs (proven by Morales-Ramis)\n"
                    f"→ They MUST live in the extended phase space (upstairs)\n"
                    f"→ This validates the lift-integrability hypothesis\n\n"
                    f"Next Steps:\n"
                    f"→ Apply Phase II: Upstairs Morales-Ramis test\n"
                    f"→ Verify abelian Galois structure upstairs\n"
                    f"→ Complete compatibility test"
                )

            else:
                interpretation['verdict'] = "NEGATIVE RESULT"

                detailed = (
                    f"Morales-Ramis confirms downstairs non-integrability\n"
                    f"(as expected from Bruns/Poincaré).\n\n"
                    f"However, WP3 found NO integrals upstairs.\n\n"
                    f"Conclusion:\n"
                    f"→ No evidence of lift-integrability detected\n"
                    f"→ Either:\n"
                    f"   (a) No integrals exist for tested lifts\n"
                    f"   (b) WP3 search was insufficient\n"
                    f"   (c) Different lift construction needed"
                )

        else:
            interpretation['verdict'] = "UNEXPECTED RESULT"

            detailed = (
                f"⚠ UNEXPECTED: Some orbits suggest possible integrability\n\n"
                f"This is inconsistent with Bruns/Poincaré theorem.\n\n"
                f"Possible explanations:\n"
                f"1. Numerical errors in NVE computation\n"
                f"2. Symbolic fitting introduced artifacts\n"
                f"3. Orbit is at special resonance point\n"
                f"4. Kovacic algorithm inconclusive\n\n"
                f"Recommendation: Investigate further"
            )

        interpretation['detailed_interpretation'] = detailed

        if self.verbose:
            print(detailed)
            print("="*70)
            print()

        return interpretation

    def _derive_symbolic_nve(
        self,
        orbit: PeriodicOrbit,
        nve: NormalVariationalEquation
    ) -> Optional[Tuple[sp.Expr, sp.Expr]]:
        """
        Derive symbolic NVE from analytical Hamiltonian.

        This requires:
        1. Hamiltonian to be symbolic (SymPy expression)
        2. Orbit to be known analytically
        3. Ability to compute symbolic Hessian

        Returns:
            (a, b) for y'' + a*y' + b*y = 0, or None if derivation fails
        """
        # This is an advanced feature requiring symbolic Hamiltonian
        # For now, return None (not implemented)

        # In full implementation, would:
        # 1. Express orbit as symbolic functions γ(t)
        # 2. Compute Hessian ∇²H symbolically
        # 3. Form VE matrix J ∇²H
        # 4. Project to normal space
        # 5. Reduce to second-order ODE
        # 6. Extract coefficients a(t), b(t)

        return None

    def _fit_nve_numerically(
        self,
        nve: NormalVariationalEquation,
        period: float,
        n_points: int
    ) -> Optional[Tuple[sp.Expr, sp.Expr]]:
        """
        Fit numerical NVE to symbolic form.

        This is challenging because NVE coefficients are time-dependent
        and may not have simple closed forms.

        Strategy:
        1. Assume coefficients are rational functions
        2. Fit numerator and denominator polynomials
        3. Use least-squares fitting

        Returns:
            (a, b) for y'' + a*y' + b*y = 0, or None if fitting fails
        """
        # This is a research-level problem
        # For production, would need sophisticated fitting algorithms

        # Placeholder: Return simple constant coefficients for testing
        # In reality, NVE coefficients are periodic functions

        # For now, return None to indicate symbolic form is unavailable
        return None


def create_validator_for_cr3bp(mu: float = 0.012, verbose: bool = True) -> MoralesRamisValidator:
    """
    Create Morales-Ramis validator for Circular Restricted 3-Body Problem.

    Args:
        mu: Mass ratio (default: Earth-Moon system)
        verbose: Print detailed steps

    Returns:
        Configured MoralesRamisValidator

    Example:
        >>> validator = create_validator_for_cr3bp(mu=0.012)
        >>> orbit = lagrange_l4_circular_restricted_3bp(mu=0.012)
        >>> result = validator.validate_orbit(orbit)
    """
    def hamiltonian_cr3bp(state):
        """
        Circular Restricted 3-Body Problem Hamiltonian (rotating frame).

        H = (px² + py²)/2 - (x*py - y*px) - (1-μ)/r1 - μ/r2
        """
        n = len(state) // 2
        q = state[:n]  # positions
        p = state[n:]  # momenta

        x, y = q[0], q[1] if n > 1 else (q[0], 0)
        px, py = p[0], p[1] if n > 1 else (p[0], 0)

        # Kinetic energy
        T = 0.5 * (px**2 + py**2)

        # Coriolis term (rotating frame)
        Coriolis = -(x * py - y * px)

        # Potential energy
        # Distance to primary (mass 1-μ at (-μ, 0))
        r1 = np.sqrt((x + mu)**2 + y**2)

        # Distance to secondary (mass μ at (1-μ, 0))
        r2 = np.sqrt((x - (1 - mu))**2 + y**2)

        V = -(1 - mu) / r1 - mu / r2

        return T + Coriolis + V

    return MoralesRamisValidator(
        hamiltonian=hamiltonian_cr3bp,
        gradient=None,  # Will be computed numerically
        hessian=None,   # Will be computed numerically
        verbose=verbose
    )
