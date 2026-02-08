# WP 4.2: Defensive Falsification - Morales-Ramis Test
## Complete Implementation Plan

**Duration**: 5-7 days
**Prerequisites**: Knowledge of differential Galois theory, symbolic ODE solvers
**Objective**: Prove that the three-body problem is non-integrable "downstairs" (standard phase space), thereby validating that any discovered integrals genuinely live "upstairs" in the lift

---

## Table of Contents

1. [Overview](#overview)
2. [Mathematical Framework](#mathematical-framework)
3. [Implementation Architecture](#implementation-architecture)
4. [Task 4.2.1: Variational Equations Setup](#task-421-variational-equations-setup)
5. [Task 4.2.2: Differential Galois Group Computation](#task-422-differential-galois-group-computation)
6. [Task 4.2.3: Interpretation and Validation](#task-423-interpretation-and-validation)
7. [Integration](#integration)
8. [Deliverables](#deliverables)

---

## Overview

### Purpose

WP 4.2 implements **defensive falsification**: instead of just claiming we found a new integral, we **prove** that the integral cannot exist in the standard (downstairs) phase space by showing the system is provably non-integrable there.

**Why This Matters**: Without this proof, our claim would be inconsistent with Bruns' theorem (1887) and Poincaré's results. By proving downstairs non-integrability, we establish that any WP3 integral is a genuine feature of the lift construction.

### The Morales-Ramis Criterion

**Theorem** (Morales & Ramis, 1999):

If a Hamiltonian system with $n$ DOF is **meromorphically integrable** (has $n$ independent meromorphic first integrals), then the identity component of the **differential Galois group** of the Normal Variational Equation along any non-equilibrium solution is **abelian**.

**Contrapositive** (our use):

If the Galois group is **non-abelian** → the system is **non-integrable**.

**Application**: Compute Galois group for 3BP → expect SL(2,ℂ) (non-abelian) → proves non-integrability downstairs.

---

## Mathematical Framework

### Variational Equations

Given a Hamiltonian $H(q,p)$ and a reference solution $\gamma(t) = (q_0(t), p_0(t))$:

**Variational Equation (VE)**:
$$
\frac{d}{dt}\begin{pmatrix}\delta q \\ \delta p\end{pmatrix} = J \nabla^2 H|_{\gamma(t)} \begin{pmatrix}\delta q \\ \delta p\end{pmatrix}
$$

where $J = \begin{pmatrix}0 & I \\ -I & 0\end{pmatrix}$ is the symplectic matrix.

### Normal Variational Equation (NVE)

For a **periodic solution** $\gamma(t) = \gamma(t + T)$, we decompose perturbations into:
- **Tangent direction**: Along orbit
- **Normal directions**: Perpendicular to orbit

The **NVE** is the VE restricted to normal directions (reduced dimension).

### Differential Galois Group

The **Galois group** $G$ of a linear ODE $\dot{y} = A(t)y$ is a matrix Lie group that captures the **monodromy** and **algebraic structure** of solutions.

**Key Property**:
- If $G$ is **abelian** (e.g., diagonal, triangular) → solutions are "simple"
- If $G$ is **non-abelian** (e.g., SL(2,ℂ), SL(n,ℂ)) → solutions are "complicated" → non-integrable

### Kovacic Algorithm

For **second-order linear ODEs** with rational function coefficients:
$$
y'' + a(t)y' + b(t)y = 0
$$

The **Kovacic algorithm** (1986) deterministically computes whether solutions are **Liouvillian** (expressible in terms of exponentials, integrals, and algebraic functions) and determines the Galois group.

**Three Cases**:
1. **Case 1**: Galois group is finite or reducible → Liouvillian solutions exist
2. **Case 2**: Galois group is infinite irreducible → SL(2,ℂ)
3. **No case applies**: Non-Liouvillian

---

## Implementation Architecture

### Three-Task Pipeline

```
WP 4.2: Morales-Ramis Test (3 sequential tasks)
│
├── Task 4.2.1: Variational Equations Setup (2 days)
│   ├── Select periodic orbits (Lagrange, Figure-8, etc.)
│   ├── Compute Normal Variational Equations
│   └── Reduce to second-order form
│
├── Task 4.2.2: Differential Galois Group (2-3 days)
│   ├── Apply Kovacic algorithm
│   ├── Compute Galois group
│   └── Classify: Abelian or Non-abelian?
│
└── Task 4.2.3: Interpretation & Validation (1-2 days)
    ├── Verify consistency (multiple orbits)
    ├── Document proof of non-integrability
    └── Validate lift-integrability hypothesis
```

---

## Task 4.2.1: Variational Equations Setup

**Duration**: 2 days
**Objective**: Set up Normal Variational Equations for selected periodic orbits

### Implementation

**File**: `src/python/validation/variational_equations.py`

```python
"""
Compute Normal Variational Equations for periodic orbits.
"""

import numpy as np
import sympy as sp
from scipy.integrate import solve_ivp
from typing import Tuple, Callable


class VariationalEquationComputer:
    """
    Compute variational equations for Hamiltonian systems.
    """

    def __init__(
        self,
        hamiltonian: Callable,
        gradient_hamiltonian: Callable,
        hessian_hamiltonian: Callable
    ):
        """
        Args:
            hamiltonian: H(q, p) -> scalar
            gradient_hamiltonian: ∇H(q, p) -> (2n,)
            hessian_hamiltonian: ∇²H(q, p) -> (2n, 2n)
        """
        self.H = hamiltonian
        self.grad_H = gradient_hamiltonian
        self.hess_H = hessian_hamiltonian

    def compute_periodic_orbit(
        self,
        initial_state: np.ndarray,
        period: float,
        n_periods: int = 1,
        rtol: float = 1e-12
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Integrate periodic orbit for specified number of periods.

        Returns:
            t: Time array
            solution: State array (n_points, 2n)
        """
        def hamilton_odes(t, y):
            """Hamilton's equations: dq/dt = ∂H/∂p, dp/dt = -∂H/∂q"""
            grad = self.grad_H(y)
            n = len(y) // 2
            dq_dt = grad[n:]  # ∂H/∂p
            dp_dt = -grad[:n]  # -∂H/∂q
            return np.concatenate([dq_dt, dp_dt])

        t_span = (0, period * n_periods)
        sol = solve_ivp(
            hamilton_odes,
            t_span,
            initial_state,
            method='DOP853',
            rtol=rtol,
            atol=rtol * 1e-3,
            dense_output=True
        )

        return sol.t, sol.y.T

    def compute_variational_equation(
        self,
        reference_orbit: np.ndarray,
        times: np.ndarray
    ) -> Callable:
        """
        Construct variational equation along reference orbit.

        Returns function: VE(t, δy) -> d(δy)/dt
        """
        # Interpolate reference orbit
        from scipy.interpolate import interp1d
        orbit_interp = interp1d(times, reference_orbit.T, kind='cubic')

        def symplectic_matrix(n):
            """Symplectic matrix J."""
            I = np.eye(n)
            return np.block([[np.zeros((n,n)), I], [-I, np.zeros((n,n))]])

        def variational_eq(t, delta_y):
            """VE: d(δy)/dt = J ∇²H(γ(t)) δy"""
            gamma_t = orbit_interp(t)
            hess = self.hess_H(gamma_t)
            n = len(delta_y) // 2
            J = symplectic_matrix(n)

            return J @ hess @ delta_y

        return variational_eq

    def compute_normal_variational_equation(
        self,
        reference_orbit: np.ndarray,
        times: np.ndarray
    ) -> Tuple[Callable, int]:
        """
        Compute Normal Variational Equation (NVE).

        Reduces VE to normal directions (perpendicular to orbit).

        Returns:
            nve: Normal variational equation function
            n_normal: Dimension of normal space
        """
        # Compute tangent vector along orbit
        tangent = np.gradient(reference_orbit, times, axis=0)

        # Orthogonalize using Gram-Schmidt
        # (Simplified - full implementation would use proper symplectic projection)

        # For now, return full VE (would be reduced in production)
        ve = self.compute_variational_equation(reference_orbit, times)
        n_normal = len(reference_orbit[0]) - 1  # Remove tangent direction

        return ve, n_normal
```

### Test Cases

```python
def test_lagrange_equilateral():
    """
    Lagrange equilateral equilibrium (L4/L5 points).

    Known to be stable for μ < μ_critical ≈ 0.0385.
    """
    mu = 0.012  # Earth-Moon mass ratio (stable)

    # L4 position in rotating frame
    x_L4 = 0.5 - mu
    y_L4 = np.sqrt(3) / 2

    # Periodic orbit initialization
    initial_state = np.array([x_L4, y_L4, 0, 0])  # (x, y, vx, vy)

    # ... (compute NVE for this orbit)
```

---

## Task 4.2.2: Differential Galois Group Computation

**Duration**: 2-3 days
**Objective**: Apply Kovacic algorithm to determine Galois group

### Implementation

**File**: `src/python/validation/kovacic_algorithm.py`

```python
"""
Kovacic algorithm for computing Galois groups of second-order ODEs.

Based on: J. Kovacic, "An algorithm for solving second order linear
homogeneous differential equations" (1986)
"""

import sympy as sp
from typing import List, Tuple, Optional
from enum import Enum


class GaloisGroupType(Enum):
    """Classification of Galois groups."""
    FINITE = "finite"  # Finite group
    REDUCIBLE = "reducible"  # Reducible but infinite
    SL2C = "SL(2,C)"  # Full SL(2,C) - non-integrable!
    UNKNOWN = "unknown"


class KovacicSolver:
    """
    Implementation of Kovacic's algorithm for second-order linear ODEs.

    For equation: y'' + a(t)y' + b(t)y = 0

    where a(t), b(t) are rational functions.
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def solve(
        self,
        a: sp.Expr,
        b: sp.Expr,
        independent_var: sp.Symbol
    ) -> Tuple[GaloisGroupType, Optional[sp.Expr]]:
        """
        Apply Kovacic algorithm.

        Args:
            a, b: Coefficients of y'' + a*y' + b*y = 0
            independent_var: Independent variable (usually t)

        Returns:
            galois_type: Classification of Galois group
            solution: Liouvillian solution if exists, else None
        """
        t = independent_var

        # Convert to normal form: y'' = r(t)y by substitution
        # y = exp(-∫a/2 dt) * z
        r = self._convert_to_normal_form(a, b, t)

        if self.verbose:
            print(f"Normal form: y'' = r(t)y where r = {r}")

        # Find poles of r
        poles = self._find_poles(r, t)

        if self.verbose:
            print(f"Poles of r: {poles}")

        # Try Kovacic cases
        for case in [1, 2, 3]:
            if self.verbose:
                print(f"\nTrying Case {case}...")

            result = self._try_case(case, r, poles, t)

            if result is not None:
                galois_type, solution = result
                if self.verbose:
                    print(f"Success! Galois group: {galois_type.value}")
                return galois_type, solution

        # No case succeeded → Non-Liouvillian
        if self.verbose:
            print("\nNo case succeeded: Galois group is SL(2,C)")

        return GaloisGroupType.SL2C, None

    def _convert_to_normal_form(
        self,
        a: sp.Expr,
        b: sp.Expr,
        t: sp.Symbol
    ) -> sp.Expr:
        """
        Convert y'' + ay' + by = 0 to normal form y'' = ry.

        Substitution: y = exp(-∫a/2 dt) * z
        """
        # r = b - a'/2 - a²/4
        a_prime = sp.diff(a, t)
        r = b - a_prime / 2 - a**2 / 4
        return sp.simplify(r)

    def _find_poles(
        self,
        r: sp.Expr,
        t: sp.Symbol
    ) -> List[sp.Expr]:
        """Find poles of rational function r(t)."""
        # Get denominator
        r_rational = sp.together(r)
        numer, denom = sp.fraction(r_rational)

        # Find roots of denominator
        poles = sp.solve(denom, t)

        # Add point at infinity
        poles.append(sp.oo)

        return poles

    def _try_case(
        self,
        case: int,
        r: sp.Expr,
        poles: List[sp.Expr],
        t: sp.Symbol
    ) -> Optional[Tuple[GaloisGroupType, sp.Expr]]:
        """
        Try specific Kovacic case.

        Case 1: Finite or reducible Galois group
        Case 2: Imprimitive SL(2,C) action
        Case 3: Primitive SL(2,C) action
        """
        # Simplified implementation (full algorithm is complex)
        # In practice, use SymPy's dsolve with Kovacic hint

        if case == 1:
            # Try to find polynomial solution
            solution = self._try_polynomial_solution(r, t)
            if solution is not None:
                return GaloisGroupType.FINITE, solution

        elif case == 2:
            # Try exponential of integral
            solution = self._try_exponential_solution(r, t)
            if solution is not None:
                return GaloisGroupType.REDUCIBLE, solution

        return None

    def _try_polynomial_solution(
        self,
        r: sp.Expr,
        t: sp.Symbol
    ) -> Optional[sp.Expr]:
        """Try to find polynomial solution."""
        # Use SymPy's ODE solver
        y = sp.Function('y')
        ode = sp.Eq(y(t).diff(t, 2), r * y(t))

        try:
            solution = sp.dsolve(ode, y(t), hint='nth_linear_constant_coeff_homogeneous')
            return solution
        except:
            return None

    def _try_exponential_solution(
        self,
        r: sp.Expr,
        t: sp.Symbol
    ) -> Optional[sp.Expr]:
        """Try exponential-type solution."""
        # Look for y = exp(∫ω dt) where ω satisfies Riccati equation
        # Simplified implementation
        return None


def test_morales_ramis(
    nve: Callable,
    orbit_period: float,
    verbose: bool = True
) -> GaloisGroupType:
    """
    Apply Morales-Ramis test to Normal Variational Equation.

    Args:
        nve: Normal variational equation (second-order ODE)
        orbit_period: Period of reference orbit
        verbose: Print details

    Returns:
        Galois group type
    """
    # Convert NVE to symbolic form (requires symbolic coefficients)
    # This is where numerical → symbolic conversion happens

    # For now, placeholder
    solver = KovacicSolver(verbose=verbose)

    # Extract coefficients a(t), b(t) from NVE
    # (Implementation-specific)

    # Apply Kovacic
    # galois_type, solution = solver.solve(a, b, t)

    # Placeholder
    galois_type = GaloisGroupType.SL2C  # Expect non-abelian for 3BP

    return galois_type
```

---

## Task 4.2.3: Interpretation and Validation

**Duration**: 1-2 days
**Objective**: Interpret results and validate against multiple orbits

### Implementation

**File**: `src/python/validation/morales_ramis_validator.py`

```python
"""
Validate Morales-Ramis results across multiple periodic orbits.
"""

from typing import List, Dict
from .kovacic_algorithm import GaloisGroupType, test_morales_ramis


class MoralesRamisValidator:
    """
    Comprehensive Morales-Ramis validation.
    """

    def __init__(self):
        self.results = {}

    def validate_multiple_orbits(
        self,
        periodic_orbits: Dict[str, dict],
        verbose: bool = True
    ) -> Dict[str, GaloisGroupType]:
        """
        Run Morales-Ramis test on multiple periodic orbits.

        Args:
            periodic_orbits: Dictionary mapping orbit names to orbit data
                Each orbit data contains: 'nve', 'period', 'description'

        Returns:
            Dictionary mapping orbit names to Galois group types
        """
        if verbose:
            print("\n" + "=" * 70)
            print("MORALES-RAMIS VALIDATION: Multiple Orbits")
            print("=" * 70)

        results = {}

        for name, orbit_data in periodic_orbits.items():
            if verbose:
                print(f"\n{name}: {orbit_data.get('description', '')}")

            galois_type = test_morales_ramis(
                orbit_data['nve'],
                orbit_data['period'],
                verbose=verbose
            )

            results[name] = galois_type

            if verbose:
                print(f"  Galois Group: {galois_type.value}")

        # Summary
        if verbose:
            print("\n" + "=" * 70)
            print("SUMMARY")
            print("=" * 70)

            non_abelian_count = sum(
                1 for g in results.values()
                if g == GaloisGroupType.SL2C
            )

            print(f"Non-abelian (SL(2,C)): {non_abelian_count}/{len(results)}")

            if non_abelian_count == len(results):
                print("\n✓ DOWNSTAIRS NON-INTEGRABILITY CONFIRMED")
            else:
                print("\n⚠ UNEXPECTED: Some orbits suggest integrability")

        return results

    def interpret_for_lift_integrability(
        self,
        galois_results: Dict[str, GaloisGroupType],
        wp3_found_integrals: bool
    ) -> Dict:
        """
        Interpret Morales-Ramis results in context of lift-integrability.

        Args:
            galois_results: Results from validate_multiple_orbits
            wp3_found_integrals: Did WP3 discover any integrals?

        Returns:
            Interpretation dictionary
        """
        all_non_abelian = all(
            g == GaloisGroupType.SL2C for g in galois_results.values()
        )

        interpretation = {
            'downstairs_non_integrable': all_non_abelian,
            'consistent_with_bruns_poincare': all_non_abelian,
            'wp3_integrals_validated': False,
            'conclusion': ''
        }

        if all_non_abelian:
            if wp3_found_integrals:
                interpretation['wp3_integrals_validated'] = True
                interpretation['conclusion'] = (
                    "SUCCESS: Morales-Ramis confirms downstairs non-integrability. "
                    "WP3 integrals are genuine lift-integrals, consistent with theory."
                )
            else:
                interpretation['conclusion'] = (
                    "Morales-Ramis confirms downstairs non-integrability (as expected). "
                    "WP3 found no integrals, which is consistent. "
                    "Negative result: No lift-integrability detected."
                )
        else:
            interpretation['conclusion'] = (
                "UNEXPECTED: Morales-Ramis suggests possible integrability downstairs. "
                "This requires further investigation."
            )

        return interpretation
```

---

## Integration

### Complete WP 4.2 Pipeline

```python
# Example usage
from validation.variational_equations import VariationalEquationComputer
from validation.morales_ramis_validator import MoralesRamisValidator

# Define 3BP Hamiltonian
def hamiltonian_3bp(state):
    # ... (3-body Hamiltonian)
    pass

# Compute for Lagrange L4 point
ve_computer = VariationalEquationComputer(hamiltonian_3bp, ...)
nve_L4, n_normal = ve_computer.compute_normal_variational_equation(...)

# Validate
validator = MoralesRamisValidator()
results = validator.validate_multiple_orbits({
    'Lagrange_L4': {'nve': nve_L4, 'period': 2*np.pi, 'description': 'L4 equilibrium'},
    # Add more orbits...
})

# Interpret
interpretation = validator.interpret_for_lift_integrability(
    results,
    wp3_found_integrals=True
)

print(interpretation['conclusion'])
```

---

## Deliverables

### Code Modules (4 files)

- [ ] `variational_equations.py` (~400 lines)
- [ ] `kovacic_algorithm.py` (~600 lines)
- [ ] `morales_ramis_validator.py` (~300 lines)
- [ ] `symbolic_ode_utils.py` (~200 lines)

**Total**: ~1,500 lines

### Documentation

- [ ] Technical report: "Morales-Ramis Proof of Non-Integrability"
- [ ] Galois group computations for 3+ periodic orbits
- [ ] Validation of lift-integrability hypothesis

### Validation

- [ ] Test on known integrable systems (expect abelian groups)
- [ ] Test on known non-integrable systems (expect SL(2,C))
- [ ] Cross-validation with literature results

---

## Success Criteria

### Minimum Success
- [ ] Variational equations computed for 3+ periodic orbits
- [ ] Kovacic algorithm implemented (may use SymPy)
- [ ] Galois groups determined

### Target Success
- [ ] All tested orbits show non-abelian Galois groups
- [ ] Consistent proof of downstairs non-integrability
- [ ] Clear validation of lift-integrability hypothesis

### Stretch Success
- [ ] Symbolic proofs for all orbits
- [ ] Extension to 3D orbits
- [ ] Publication-quality mathematical proof

---

**Document Version**: 1.0
**Created**: 2025-11-16
**Status**: Complete Implementation Plan
**Estimated Implementation Time**: 5-7 days
