# AMENDED WP 4.2: Complete Morales-Ramis Test - Downstairs AND Upstairs
## Full Implementation Plan for Lift-Integrability Validation

**AMENDMENT DATE**: 2025-11-20
**AMENDMENT REASON**: Critical discrepancy identified between theoretical framework (Section VI) and original implementation plan

**Duration**: 10-14 days (expanded from 5-7 days)
**Prerequisites**: Knowledge of differential Galois theory, symbolic ODE solvers, WP2 lifts implemented
**Objective**: Prove BOTH that the three-body problem is non-integrable "downstairs" AND that the lifted system exhibits abelian Galois group structure "upstairs", thereby validating lift-integrability

---

## CRITICAL AMENDMENT SUMMARY

### Original Plan Deficiency

The original WP 4.2 plan **only** implemented the downstairs Morales-Ramis test:
- ✅ Compute NVE downstairs
- ✅ Verify Galois group is non-abelian
- ✅ Conclude: non-integrable downstairs

### Missing Component (Now Added)

**The core of the Compatibility Test** requires proving that the differential Galois group **upstairs** is abelian:
- ❌ **MISSING**: Compute NVE upstairs (in S¹ lift and KS-Spinor lift)
- ❌ **MISSING**: Verify Galois group is abelian upstairs
- ❌ **MISSING**: Validate that this abelian structure is compatible with discovered integrals

### Theoretical Justification

From "Abelianizing Variational Equations in the Three-Body Problem":

> "The aim is to find a transformation such that the NVE upstairs has an abelian Galois group, even though downstairs it was non-abelian. [...] If the extended system becomes integrable (in a broad sense), then along the lifted orbit the NVE's Galois group will have an abelian identity component by design – essentially we have manufactured a situation that satisfies Morales-Ramis."

**Morales-Ramis Theorem (Forward Direction):**
- IF a system is Liouville integrable → THEN its NVE Galois group is abelian

**Application to Lift-Integrability:**
- IF we find integrals upstairs (WP3) → THEN the upstairs NVE Galois group MUST be abelian
- IF upstairs Galois group is NOT abelian → THEN WP3 integrals are spurious

**This is the Compatibility Test.**

---

## Table of Contents

1. [Overview](#overview)
2. [Mathematical Framework](#mathematical-framework)
3. [Implementation Architecture](#implementation-architecture)
4. [PHASE I: Downstairs Analysis](#phase-i-downstairs-analysis)
   - [Task 4.2.1: Downstairs Variational Equations Setup](#task-421-downstairs-variational-equations-setup)
   - [Task 4.2.2: Downstairs Differential Galois Group](#task-422-downstairs-differential-galois-group)
   - [Task 4.2.3: Confirmation of Downstairs Non-Integrability](#task-423-confirmation-of-downstairs-non-integrability)
5. [PHASE II: Upstairs Analysis (NEW)](#phase-ii-upstairs-analysis-new)
   - [Task 4.2.4: Upstairs Variational Equations Setup](#task-424-upstairs-variational-equations-setup)
   - [Task 4.2.5: Upstairs Differential Galois Group](#task-425-upstairs-differential-galois-group)
   - [Task 4.2.6: Compatibility Test Validation](#task-426-compatibility-test-validation)
6. [Integration and Interpretation](#integration-and-interpretation)
7. [Deliverables](#deliverables)

---

## Overview

### Complete Two-Phase Morales-Ramis Test

```
┌─────────────────────────────────────────────────────────────┐
│                   COMPLETE MR TEST                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PHASE I: DOWNSTAIRS (Defensive Falsification)             │
│  ─────────────────────────────────────────────             │
│  • Compute NVE in original 3BP coordinates                 │
│  • Verify: Galois group is NON-ABELIAN (SL(2,ℂ))          │
│  • Conclusion: 3BP is provably non-integrable downstairs   │
│  • Validates: Any new integral must live upstairs          │
│                                                             │
│  PHASE II: UPSTAIRS (Compatibility Test) ⭐ NEW             │
│  ─────────────────────────────────────────                 │
│  • Compute NVE in LIFTED coordinates (S¹ / KS-Spinor)      │
│  • Verify: Galois group IS ABELIAN (or solvable)          │
│  • Conclusion: Lift-integrability is possible              │
│  • Validates: WP3 integrals are genuine                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Why Both Phases Are Essential

**PHASE I alone** (original plan):
- Proves non-integrability downstairs ✓
- Consistent with Bruns/Poincaré ✓
- **BUT**: Does NOT validate that upstairs integrals exist ✗

**PHASE I + PHASE II** (amended plan):
- Proves non-integrability downstairs ✓
- Proves abelian structure upstairs ✓
- **Validates lift-integrability hypothesis** ✓
- **Confirms WP3 integrals are not spurious** ✓

---

## Mathematical Framework

### The Complete Morales-Ramis Criterion for Lifts

**Theorem (Morales-Ramis, 1999):**

For an $n$-DOF Hamiltonian system $H$ to be meromorphically integrable, the identity component of the differential Galois group $G^0$ of the NVE along any non-equilibrium solution must be **abelian**.

**Contrapositive (Downstairs):**
$$
G^0_{\text{downstairs}} \text{ non-abelian} \Rightarrow H_{\text{downstairs}} \text{ non-integrable}
$$

**Forward Direction (Upstairs):**
$$
\widetilde{H}_{\text{upstairs}} \text{ integrable} \Rightarrow G^0_{\text{upstairs}} \text{ abelian}
$$

**Compatibility Test:**
$$
\text{If WP3 found } \widetilde{I} \Rightarrow G^0_{\text{upstairs}} \text{ MUST be abelian}
$$

### Variational Equations in Lifted Coordinates

**Downstairs** (original 3BP):
- Phase space: $(q, p) \in \mathbb{R}^{2n}$ (planar: $n=3$ after COM reduction)
- Hamiltonian: $H(q,p)$
- NVE: $\frac{d}{dt}\delta y = J \nabla^2 H|_{\gamma(t)} \delta y$

**Upstairs** (S¹ lift):
- Phase space: $(q, p, \theta, p_\theta) \in \mathbb{R}^{2n+2}$
- Extended Hamiltonian: $\widetilde{H}(q, p, \theta, p_\theta)$
- Extended symplectic form: $\widetilde{\omega} = \omega_{\text{can}} + d\theta \wedge (dp_\theta - A)$
- **Upstairs NVE**: $\frac{d}{dt}\delta \widetilde{y} = \widetilde{J} \nabla^2 \widetilde{H}|_{\widetilde{\gamma}(t)} \delta \widetilde{y}$

**Upstairs** (KS-Spinor lift):
- Phase space: Constrained $(Q, P) \in \mathbb{R}^{2m}$ with constraints
- Extended Hamiltonian: $\widetilde{H}_{KS}$
- **Upstairs NVE**: Linearization respecting constraints

### Expected Results

| System | Galois Group $G^0$ | Integrability |
|--------|-------------------|---------------|
| Downstairs 3BP | $\text{SL}(2,\mathbb{C})$ (non-abelian) | ✗ Non-integrable |
| Upstairs S¹ lift | $\mathbb{C}^*$ or $\mathbb{C}$ (abelian) | ✓ If integral exists |
| Upstairs KS lift | Abelian (expected) | ✓ If integral exists |

---

## PHASE I: Downstairs Analysis

### Task 4.2.1: Downstairs Variational Equations Setup

**Duration**: 2 days
**Objective**: Set up Normal Variational Equations for selected periodic orbits in **original** 3BP coordinates

*[Content identical to original plan - omitted for brevity]*

### Task 4.2.2: Downstairs Differential Galois Group

**Duration**: 2-3 days
**Objective**: Apply Kovacic algorithm to determine Galois group **downstairs**

*[Content identical to original plan - omitted for brevity]*

### Task 4.2.3: Confirmation of Downstairs Non-Integrability

**Duration**: 1 day
**Objective**: Interpret downstairs results and confirm non-integrability

**Expected Result**:
- Galois group is $\text{SL}(2,\mathbb{C})$ (non-abelian)
- Confirms: 3BP is non-integrable downstairs
- Validates: Any integral from WP3 must live upstairs

---

## PHASE II: Upstairs Analysis (NEW)

### Task 4.2.4: Upstairs Variational Equations Setup

**Duration**: 2-3 days
**Objective**: Set up Normal Variational Equations for periodic orbits in **LIFTED** coordinates

**NEW CONTENT**: This task was completely missing from the original plan.

#### Implementation

**File**: `src/python/validation/upstairs_variational_equations.py`

```python
"""
Compute Variational Equations in Lifted Phase Spaces.

This module extends the downstairs VE computation to the S¹ bundle
and KS-Spinor lifts constructed in WP2.
"""

import numpy as np
import sympy as sp
from typing import Tuple, Callable, Optional
from .variational_equations import VariationalEquationComputer


class UpstirsVariationalEquationComputer:
    """
    Compute variational equations in lifted phase spaces.

    Supports:
    - S¹ bundle lift (WP 2.2)
    - KS-Spinor lift (WP 2.3)
    """

    def __init__(
        self,
        lift_type: str,  # 's1_bundle' or 'ks_spinor'
        extended_hamiltonian: Callable,
        extended_symplectic_form: Callable,
        constraints: Optional[Callable] = None
    ):
        """
        Args:
            lift_type: Type of lift ('s1_bundle' or 'ks_spinor')
            extended_hamiltonian: H̃(q, p, θ, p_θ) or H̃_KS
            extended_symplectic_form: ω̃ including connection term
            constraints: For KS lift, the triangle closure constraint
        """
        self.lift_type = lift_type
        self.H_tilde = extended_hamiltonian
        self.omega_tilde = extended_symplectic_form
        self.constraints = constraints

    def compute_lifted_periodic_orbit(
        self,
        downstairs_orbit: np.ndarray,
        initial_fiber_coords: np.ndarray,
        period: float,
        n_periods: int = 1
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Lift a downstairs periodic orbit to the extended space.

        For S¹ bundle: Add (θ, p_θ) coordinates
        For KS-Spinor: Transform to spinor coordinates with constraints

        Returns:
            t: Time array
            lifted_orbit: Orbit in extended phase space
        """
        if self.lift_type == 's1_bundle':
            return self._lift_to_s1_bundle(downstairs_orbit, initial_fiber_coords, period, n_periods)
        elif self.lift_type == 'ks_spinor':
            return self._lift_to_ks_spinor(downstairs_orbit, initial_fiber_coords, period, n_periods)
        else:
            raise ValueError(f"Unknown lift type: {self.lift_type}")

    def _lift_to_s1_bundle(
        self,
        downstairs_orbit: np.ndarray,
        initial_fiber: np.ndarray,  # (θ₀, p_θ₀)
        period: float,
        n_periods: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Lift orbit to S¹ bundle.

        Extended coordinates: (q, p, θ, p_θ)
        Extended Hamiltonian: H̃ = H(q,p) + V_lift(θ, p_θ)
        """
        n_points = len(downstairs_orbit)
        n_downstairs = downstairs_orbit.shape[1]

        # Initialize lifted orbit
        lifted_orbit = np.zeros((n_points, n_downstairs + 2))
        lifted_orbit[:, :n_downstairs] = downstairs_orbit

        # Evolve fiber coordinates
        # θ evolves according to connection A
        # p_θ is conserved (Noether's theorem for S¹ symmetry)
        theta_0, p_theta_0 = initial_fiber

        for i in range(n_points):
            # Compute connection A at this point
            A_i = self._compute_connection(downstairs_orbit[i])

            # Integrate fiber evolution: dθ/dt = ∂H̃/∂p_θ = (depends on lift definition)
            # For minimal lift: dθ/dt = A·dq/dt (horizontal lift condition)
            theta_i = theta_0 + self._integrate_connection(downstairs_orbit[:i+1], A_i)

            lifted_orbit[i, -2] = theta_i
            lifted_orbit[i, -1] = p_theta_0  # Conserved

        t = np.linspace(0, period * n_periods, n_points)
        return t, lifted_orbit

    def _compute_connection(self, state: np.ndarray) -> float:
        """
        Compute connection one-form A at given state.

        From WP 2.1.2: A is the mechanical connection (magnetic term).
        """
        # Extract position and momentum
        n = len(state) // 2
        q = state[:n]
        p = state[n:]

        # Connection A = (angular momentum term) / (moment of inertia)
        # Specific formula depends on reduction (see WP 2.1.2)
        # Placeholder:
        A = self._connection_formula(q, p)
        return A

    def _connection_formula(self, q: np.ndarray, p: np.ndarray) -> float:
        """
        Compute A from WP 2.1.2 implementation.
        TODO: Import from WP2 modules
        """
        # This should be imported from the WP 2.1.2 implementation
        raise NotImplementedError("Import connection from WP 2.1.2")

    def compute_upstairs_variational_equation(
        self,
        lifted_orbit: np.ndarray,
        times: np.ndarray
    ) -> Tuple[Callable, int]:
        """
        Compute Variational Equation in the LIFTED space.

        This is the KEY new functionality.

        Returns:
            upstairs_ve: Variational equation d(δỹ)/dt = J̃ ∇²H̃ δỹ
            n_dof_upstairs: Dimension of upstairs phase space
        """
        from scipy.interpolate import interp1d
        orbit_interp = interp1d(times, lifted_orbit.T, kind='cubic')

        def upstairs_ve(t, delta_y_tilde):
            """
            Upstairs VE: d(δỹ)/dt = J̃ ∇²H̃(γ̃(t)) δỹ

            where J̃ is the extended symplectic matrix and
            ∇²H̃ is the Hessian of the extended Hamiltonian.
            """
            gamma_tilde_t = orbit_interp(t)

            # Compute extended Hessian
            hess_tilde = self._compute_extended_hessian(gamma_tilde_t)

            # Extended symplectic matrix
            n_upstairs = len(delta_y_tilde) // 2
            J_tilde = self._extended_symplectic_matrix(n_upstairs)

            return J_tilde @ hess_tilde @ delta_y_tilde

        n_dof_upstairs = len(lifted_orbit[0]) // 2
        return upstairs_ve, n_dof_upstairs

    def _compute_extended_hessian(self, state: np.ndarray) -> np.ndarray:
        """
        Compute Hessian ∇²H̃ of extended Hamiltonian.

        For S¹ bundle: includes cross-terms with θ, p_θ
        For KS-Spinor: includes constraint contributions
        """
        # Numerical differentiation or symbolic computation
        # TODO: Implement based on extended Hamiltonian from WP2
        raise NotImplementedError("Compute extended Hessian from WP2 Hamiltonian")

    def _extended_symplectic_matrix(self, n: int) -> np.ndarray:
        """
        Extended symplectic matrix J̃.

        For S¹ bundle: 2(n+1) × 2(n+1)
        For KS-Spinor: Depends on constraint structure
        """
        if self.lift_type == 's1_bundle':
            I = np.eye(n)
            return np.block([[np.zeros((n,n)), I], [-I, np.zeros((n,n))]])
        else:
            # KS-Spinor: Dirac bracket or reduced symplectic form
            raise NotImplementedError("Extended symplectic matrix for KS lift")

    def compute_upstairs_normal_variational_equation(
        self,
        lifted_orbit: np.ndarray,
        times: np.ndarray
    ) -> Tuple[Callable, int]:
        """
        Compute Normal Variational Equation in lifted space.

        Reduces to directions perpendicular to the lifted orbit.
        """
        # Similar to downstairs, but in higher-dimensional space
        upstairs_ve, n_upstairs = self.compute_upstairs_variational_equation(
            lifted_orbit, times
        )

        # Project out tangent direction (in upstairs space)
        # This is the NVE we will use for Galois group computation

        n_normal_upstairs = n_upstairs - 1  # Remove tangent

        # TODO: Implement symplectic orthogonalization in lifted space

        return upstairs_ve, n_normal_upstairs
```

#### Test Cases for Upstairs VE

```python
def test_s1_lagrange_equilateral_upstairs():
    """
    Test upstairs VE for Lagrange L4 point in S¹ bundle.

    Expected: Upstairs Galois group should be ABELIAN
              (if lift-integrability hypothesis is correct)
    """
    # Load downstairs L4 orbit
    downstairs_orbit = load_lagrange_l4_orbit()

    # Initial fiber coordinates (θ₀, p_θ₀)
    initial_fiber = np.array([0.0, compute_angular_momentum(downstairs_orbit[0])])

    # Create upstairs computer
    upstairs_computer = UpstirsVariationalEquationComputer(
        lift_type='s1_bundle',
        extended_hamiltonian=s1_extended_hamiltonian,
        extended_symplectic_form=s1_extended_symplectic_form
    )

    # Lift orbit
    t, lifted_orbit = upstairs_computer.compute_lifted_periodic_orbit(
        downstairs_orbit,
        initial_fiber,
        period=2*np.pi
    )

    # Compute upstairs NVE
    nve_upstairs, n_normal = upstairs_computer.compute_upstairs_normal_variational_equation(
        lifted_orbit, t
    )

    print(f"Upstairs DOF: {n_normal}")
    print(f"Upstairs NVE ready for Galois group computation")

    return nve_upstairs, lifted_orbit, t


def test_ks_spinor_upstairs():
    """
    Test upstairs VE for KS-Spinor lift.

    This is more complex due to constraints.
    """
    # TODO: Implement KS-Spinor upstairs VE test
    pass
```

---

### Task 4.2.5: Upstairs Differential Galois Group

**Duration**: 3-4 days
**Objective**: Apply Kovacic algorithm to determine Galois group **UPSTAIRS**

**NEW CONTENT**: This is the core of the Compatibility Test.

#### Implementation

**File**: `src/python/validation/upstairs_kovacic.py`

```python
"""
Kovacic Algorithm for Upstairs Variational Equations.

This module determines whether the upstairs NVE has an ABELIAN
Galois group, which is the key test for lift-integrability.
"""

from .kovacic_algorithm import KovacicSolver, GaloisGroupType
import sympy as sp
from typing import Tuple, Dict


class UpstirsGaloisAnalyzer:
    """
    Analyze differential Galois groups of upstairs NVEs.
    """

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.solver = KovacicSolver(verbose=verbose)

    def test_upstairs_abelian(
        self,
        upstairs_nve: Callable,
        orbit_period: float,
        lift_type: str
    ) -> Tuple[bool, GaloisGroupType, str]:
        """
        Test if upstairs NVE has abelian Galois group.

        This is the COMPATIBILITY TEST.

        Args:
            upstairs_nve: Upstairs normal variational equation
            orbit_period: Period of lifted orbit
            lift_type: 's1_bundle' or 'ks_spinor'

        Returns:
            is_abelian: True if Galois group is abelian
            galois_type: Type of Galois group
            interpretation: Human-readable interpretation
        """
        if self.verbose:
            print("\n" + "="*70)
            print(f"UPSTAIRS GALOIS GROUP COMPUTATION ({lift_type})")
            print("="*70)

        # Convert upstairs NVE to symbolic form
        # (This is the challenging part - may need numerical→symbolic conversion)
        nve_symbolic = self._numerically_fit_nve(upstairs_nve, orbit_period)

        # Extract coefficients for Kovacic algorithm
        t = sp.Symbol('t')
        a, b = self._extract_coefficients(nve_symbolic, t)

        if self.verbose:
            print(f"Upstairs NVE coefficients:")
            print(f"  a(t) = {a}")
            print(f"  b(t) = {b}")

        # Apply Kovacic algorithm
        galois_type, solution = self.solver.solve(a, b, t)

        # Check if abelian
        is_abelian = galois_type in [
            GaloisGroupType.FINITE,
            GaloisGroupType.REDUCIBLE
        ]

        # Interpret result
        if is_abelian:
            interpretation = (
                f"✓ UPSTAIRS ABELIAN: Galois group is {galois_type.value}\n"
                f"  → Lift-integrability is COMPATIBLE with Morales-Ramis\n"
                f"  → WP3 integrals are VALIDATED\n"
                f"  → This is evidence of genuine lift-integrability"
            )
        else:
            interpretation = (
                f"✗ UPSTAIRS NON-ABELIAN: Galois group is {galois_type.value}\n"
                f"  → Lift-integrability is INCOMPATIBLE with Morales-Ramis\n"
                f"  → WP3 integrals are SPURIOUS or INCOMPLETE\n"
                f"  → Lift construction may be incorrect"
            )

        if self.verbose:
            print("\n" + "="*70)
            print("RESULT:")
            print(interpretation)
            print("="*70)

        return is_abelian, galois_type, interpretation

    def _numerically_fit_nve(self, nve: Callable, period: float) -> sp.Expr:
        """
        Convert numerical NVE to symbolic expression.

        This is challenging - may need to:
        1. Evaluate NVE at many points
        2. Fit to known function families (polynomial, rational, elliptic)
        3. Use symbolic regression (SINDy, PySR)
        """
        # Placeholder - this is a research problem
        raise NotImplementedError(
            "Numerical → symbolic conversion for upstairs NVE\n"
            "Possible approaches:\n"
            "1. Assume rational function form and fit coefficients\n"
            "2. Use symbolic regression (PySR)\n"
            "3. Identify special functions (elliptic, hypergeometric)\n"
            "4. For specific lifts, derive symbolically from H̃"
        )

    def _extract_coefficients(
        self,
        nve_expr: sp.Expr,
        t: sp.Symbol
    ) -> Tuple[sp.Expr, sp.Expr]:
        """
        Extract a(t), b(t) from y'' + a(t)y' + b(t)y = 0
        """
        # Parse the symbolic NVE expression
        # TODO: Implement based on nve_expr structure
        raise NotImplementedError("Extract Kovacic coefficients from symbolic NVE")
```

#### Critical Implementation Notes

**Challenge**: Converting numerical upstairs NVE to symbolic form

**Possible Approaches**:

1. **Symbolic Derivation** (preferred):
   - Derive upstairs Hamiltonian $\widetilde{H}$ symbolically (from WP2)
   - Compute Hessian $\nabla^2 \widetilde{H}$ symbolically
   - NVE is then symbolic by construction
   - **Requires**: WP2 lifts to be implemented symbolically

2. **Numerical Fitting**:
   - Evaluate NVE coefficients at many points along orbit
   - Fit to rational function: $r(t) = P(t)/Q(t)$
   - Apply Kovacic to fitted rational function
   - **Risk**: Fitting errors may obscure true Galois group

3. **Symbolic Regression**:
   - Use PySR or similar to discover symbolic form
   - Validate discovered form against numerical NVE
   - **Risk**: May not converge for complex functions

**Recommended Path**:
- Derive upstairs Hamiltonians symbolically in WP2 (use SymPy)
- Compute variational equations symbolically
- Apply Kovacic algorithm symbolically
- Validate numerically

---

### Task 4.2.6: Compatibility Test Validation

**Duration**: 1-2 days
**Objective**: Interpret upstairs Galois group results and validate against WP3 discoveries

#### Implementation

**File**: `src/python/validation/compatibility_test.py`

```python
"""
Compatibility Test: Validate lift-integrability via Morales-Ramis.

This module performs the complete two-phase Morales-Ramis test:
1. Downstairs: Verify non-abelian → non-integrable
2. Upstairs: Verify abelian → integrable (compatible with WP3)
"""

from typing import Dict, List
from .morales_ramis_validator import MoralesRamisValidator, GaloisGroupType
from .upstairs_kovacic import UpstirsGaloisAnalyzer


class CompatibilityTestValidator:
    """
    Complete Morales-Ramis compatibility test for lift-integrability.
    """

    def __init__(self):
        self.downstairs_validator = MoralesRamisValidator()
        self.upstairs_analyzer = UpstirsGaloisAnalyzer()

    def run_complete_test(
        self,
        periodic_orbits: Dict[str, dict],
        lift_types: List[str],
        wp3_found_integrals: bool,
        wp3_integral_descriptions: List[str] = None
    ) -> Dict:
        """
        Run complete two-phase Morales-Ramis test.

        Args:
            periodic_orbits: Dict of orbit data (both downstairs and upstairs)
            lift_types: ['s1_bundle', 'ks_spinor'] - which lifts to test
            wp3_found_integrals: Did WP3 discover integrals?
            wp3_integral_descriptions: Descriptions of discovered integrals

        Returns:
            Complete test results with compatibility verdict
        """
        results = {
            'phase_1_downstairs': {},
            'phase_2_upstairs': {},
            'compatibility_verdict': None,
            'detailed_interpretation': None
        }

        print("\n" + "="*70)
        print("COMPLETE MORALES-RAMIS COMPATIBILITY TEST")
        print("="*70)

        # ============================================================
        # PHASE I: DOWNSTAIRS
        # ============================================================
        print("\n" + "─"*70)
        print("PHASE I: DOWNSTAIRS NON-INTEGRABILITY TEST")
        print("─"*70)

        downstairs_results = self.downstairs_validator.validate_multiple_orbits(
            {name: data['downstairs'] for name, data in periodic_orbits.items()},
            verbose=True
        )

        results['phase_1_downstairs'] = downstairs_results

        all_downstairs_non_abelian = all(
            g == GaloisGroupType.SL2C for g in downstairs_results.values()
        )

        if not all_downstairs_non_abelian:
            results['compatibility_verdict'] = 'UNEXPECTED_DOWNSTAIRS_ABELIAN'
            results['detailed_interpretation'] = (
                "⚠ UNEXPECTED: Some downstairs orbits have abelian Galois groups.\n"
                "This suggests possible integrability downstairs, which contradicts\n"
                "Bruns/Poincaré. Re-examine orbit selection and computation."
            )
            return results

        print("\n✓ PHASE I PASSED: All downstairs orbits have non-abelian Galois groups")
        print("  → 3BP is provably non-integrable downstairs")
        print("  → Any new integrals must live upstairs")

        # ============================================================
        # PHASE II: UPSTAIRS
        # ============================================================
        print("\n" + "─"*70)
        print("PHASE II: UPSTAIRS ABELIAN TEST (COMPATIBILITY)")
        print("─"*70)

        upstairs_results = {}

        for lift_type in lift_types:
            print(f"\n┌─ Testing {lift_type.upper()} lift")

            lift_results = {}

            for orbit_name, orbit_data in periodic_orbits.items():
                upstairs_data = orbit_data.get(f'upstairs_{lift_type}')

                if upstairs_data is None:
                    print(f"  ⚠ No upstairs data for {orbit_name} in {lift_type}")
                    continue

                print(f"  • {orbit_name}:")

                is_abelian, galois_type, interpretation = \
                    self.upstairs_analyzer.test_upstairs_abelian(
                        upstairs_data['nve'],
                        upstairs_data['period'],
                        lift_type
                    )

                lift_results[orbit_name] = {
                    'is_abelian': is_abelian,
                    'galois_type': galois_type,
                    'interpretation': interpretation
                }

                # Print summary
                if is_abelian:
                    print(f"    ✓ Abelian ({galois_type.value})")
                else:
                    print(f"    ✗ Non-abelian ({galois_type.value})")

            upstairs_results[lift_type] = lift_results

        results['phase_2_upstairs'] = upstairs_results

        # ============================================================
        # COMPATIBILITY VERDICT
        # ============================================================
        print("\n" + "="*70)
        print("COMPATIBILITY VERDICT")
        print("="*70)

        # Count abelian upstairs results
        total_upstairs_tests = sum(len(v) for v in upstairs_results.values())
        abelian_count = sum(
            1 for lift_results in upstairs_results.values()
            for result in lift_results.values()
            if result['is_abelian']
        )

        abelian_fraction = abelian_count / total_upstairs_tests if total_upstairs_tests > 0 else 0

        # Determine verdict
        if abelian_fraction >= 0.8:  # At least 80% abelian
            if wp3_found_integrals:
                verdict = 'LIFT_INTEGRABILITY_CONFIRMED'
                interpretation = (
                    f"✓✓✓ LIFT-INTEGRABILITY CONFIRMED ✓✓✓\n\n"
                    f"DOWNSTAIRS (PHASE I):\n"
                    f"  • All orbits: Non-abelian Galois group (SL(2,ℂ))\n"
                    f"  • Conclusion: 3BP is provably non-integrable downstairs\n"
                    f"  • Consistent with: Bruns (1887), Poincaré (1890s)\n\n"
                    f"UPSTAIRS (PHASE II):\n"
                    f"  • {abelian_count}/{total_upstairs_tests} orbits: Abelian Galois group\n"
                    f"  • Conclusion: Lifted system exhibits integrable structure\n"
                    f"  • Compatible with: Morales-Ramis criterion\n\n"
                    f"WP3 INTEGRALS:\n"
                )
                if wp3_integral_descriptions:
                    for i, desc in enumerate(wp3_integral_descriptions, 1):
                        interpretation += f"  {i}. {desc}\n"
                interpretation += (
                    f"\nVERDICT:\n"
                    f"  The discovered integrals from WP3 are GENUINE.\n"
                    f"  They represent lift-integrability: integrals that exist\n"
                    f"  in the extended phase space but not downstairs.\n"
                    f"  This is consistent with both:\n"
                    f"    • Classical no-go theorems (downstairs)\n"
                    f"    • Morales-Ramis integrability criterion (upstairs)\n\n"
                    f"SIGNIFICANCE:\n"
                    f"  This validates the lift-integrability hypothesis and\n"
                    f"  provides rigorous proof that the 3BP possesses hidden\n"
                    f"  symmetries accessible only through higher-dimensional\n"
                    f"  symplectic embedding.\n"
                )
            else:
                verdict = 'UPSTAIRS_ABELIAN_BUT_NO_INTEGRALS_FOUND'
                interpretation = (
                    f"⚠ UPSTAIRS ABELIAN BUT NO INTEGRALS FOUND\n\n"
                    f"  • Upstairs Galois groups are abelian ({abelian_fraction:.0%})\n"
                    f"  • BUT: WP3 did not discover any integrals\n"
                    f"  • Possible explanations:\n"
                    f"    1. Integrals exist but WP3 methods didn't find them\n"
                    f"    2. Abelian structure is local, not global\n"
                    f"    3. Additional symmetries needed for full integrability\n\n"
                    f"RECOMMENDATION:\n"
                    f"  • Re-run WP3 with expanded search space\n"
                    f"  • Focus on regions where Galois group is abelian\n"
                    f"  • Investigate partial integrability\n"
                )
        elif abelian_fraction <= 0.2:  # Mostly non-abelian
            if wp3_found_integrals:
                verdict = 'INTEGRALS_INCOMPATIBLE_WITH_MR'
                interpretation = (
                    f"✗✗✗ WP3 INTEGRALS INCOMPATIBLE WITH MORALES-RAMIS ✗✗✗\n\n"
                    f"  • WP3 claimed to find integrals\n"
                    f"  • BUT: Upstairs Galois groups are NON-abelian ({(1-abelian_fraction):.0%})\n"
                    f"  • Morales-Ramis says: Integrability → Abelian Galois group\n"
                    f"  • Contrapositive: Non-abelian → NOT integrable\n\n"
                    f"CONCLUSION:\n"
                    f"  The WP3 integrals are SPURIOUS. They are either:\n"
                    f"    1. Numerical artifacts (not exact conservation)\n"
                    f"    2. Functionally dependent on known integrals\n"
                    f"    3. Adiabatic/approximate invariants (not true integrals)\n\n"
                    f"ACTION REQUIRED:\n"
                    f"  • Re-examine WP3 integral discovery process\n"
                    f"  • Verify conservation to machine precision (WP 4.1)\n"
                    f"  • Check functional independence (WP 4.1)\n"
                    f"  • Consider alternative lift constructions (WP2)\n"
                )
            else:
                verdict = 'NEGATIVE_RESULT_CONFIRMED'
                interpretation = (
                    f"○ NEGATIVE RESULT CONFIRMED\n\n"
                    f"DOWNSTAIRS:\n"
                    f"  • Non-abelian Galois groups → Non-integrable\n\n"
                    f"UPSTAIRS:\n"
                    f"  • Non-abelian Galois groups → Still non-integrable\n\n"
                    f"CONCLUSION:\n"
                    f"  Neither the original 3BP nor the current lifts are integrable.\n"
                    f"  The lift construction (S¹ bundle, KS-Spinor) does not resolve\n"
                    f"  the integrability obstruction.\n\n"
                    f"INTERPRETATION:\n"
                    f"  This is a RIGOROUS NEGATIVE RESULT. It establishes bounds\n"
                    f"  on what lift constructions are insufficient for integrability.\n\n"
                    f"NEXT STEPS:\n"
                    f"  • Explore alternative lift constructions\n"
                    f"  • Investigate higher-order variational equations (Morales-Ramis-Simó)\n"
                    f"  • Consider partial/conditional integrability\n"
                    f"  • Document as contribution to integrability theory\n"
                )
        else:  # Mixed results
            verdict = 'MIXED_RESULTS'
            interpretation = (
                f"⚠ MIXED RESULTS (REQUIRES INVESTIGATION)\n\n"
                f"  • Abelian upstairs: {abelian_fraction:.0%}\n"
                f"  • Non-abelian upstairs: {(1-abelian_fraction):.0%}\n\n"
                f"This suggests:\n"
                f"  • Integrability may be orbit-specific or regime-specific\n"
                f"  • Some lifts work better than others\n"
                f"  • Partial integrability structure\n\n"
                f"RECOMMENDATION:\n"
                f"  • Categorize which orbits/lifts have abelian structure\n"
                f"  • Investigate common features\n"
                f"  • Consider conditional integrability\n"
            )

        results['compatibility_verdict'] = verdict
        results['detailed_interpretation'] = interpretation

        print(interpretation)
        print("="*70)

        return results
```

---

## Integration and Interpretation

### Complete Test Pipeline

```python
# Example: Complete Morales-Ramis Test

from validation.compatibility_test import CompatibilityTestValidator

# Prepare periodic orbits (downstairs + upstairs data)
periodic_orbits = {
    'Lagrange_L4': {
        'downstairs': {
            'nve': nve_L4_downstairs,
            'period': 2*np.pi,
            'description': 'Lagrange L4 equilibrium'
        },
        'upstairs_s1_bundle': {
            'nve': nve_L4_s1_upstairs,
            'period': 2*np.pi,
            'description': 'L4 in S¹ bundle'
        },
        'upstairs_ks_spinor': {
            'nve': nve_L4_ks_upstairs,
            'period': 2*np.pi,
            'description': 'L4 in KS-Spinor lift'
        }
    },
    # Add Figure-8, Euler collinear, etc.
}

# Run complete test
validator = CompatibilityTestValidator()

results = validator.run_complete_test(
    periodic_orbits=periodic_orbits,
    lift_types=['s1_bundle', 'ks_spinor'],
    wp3_found_integrals=True,
    wp3_integral_descriptions=[
        "Conserved quantity Ĩ in S¹ bundle (from HNN)",
        "Runge-Lenz-like tensor in KS-Spinor lift (from Killing tensor search)"
    ]
)

# Results
print(f"\nVerdict: {results['compatibility_verdict']}")
print(results['detailed_interpretation'])
```

---

## Deliverables

### Code Modules (7 files - expanded from 4)

- [x] `variational_equations.py` (~400 lines) - Downstairs VE
- [x] `kovacic_algorithm.py` (~600 lines) - Downstairs Kovacic
- [x] `morales_ramis_validator.py` (~300 lines) - Downstairs validation
- [ ] **`upstairs_variational_equations.py` (~500 lines) - NEW** - Upstairs VE
- [ ] **`upstairs_kovacic.py` (~400 lines) - NEW** - Upstairs Kovacic
- [ ] **`compatibility_test.py` (~600 lines) - NEW** - Complete test
- [ ] `symbolic_ode_utils.py` (~200 lines) - Shared utilities

**Total**: ~3,000 lines (doubled from original 1,500 lines)

### Documentation

- [ ] **Amended Technical Report**: "Complete Morales-Ramis Test for Lift-Integrability"
- [ ] Downstairs Galois group computations for 3+ periodic orbits
- [ ] **Upstairs Galois group computations for 3+ periodic orbits (NEW)**
- [ ] **Compatibility test results and interpretation (NEW)**
- [ ] Validation of lift-integrability hypothesis

### Validation

- [ ] Test on known integrable systems (expect abelian upstairs)
- [ ] Test on known non-integrable systems (expect non-abelian upstairs)
- [ ] Cross-validation with literature results
- [ ] **Verify consistency between downstairs and upstairs results (NEW)**

---

## Success Criteria

### Minimum Success
- [ ] Variational equations computed for 3+ periodic orbits (downstairs and upstairs)
- [ ] Kovacic algorithm implemented (may use SymPy) for both phases
- [ ] Galois groups determined for both downstairs and upstairs
- [ ] **Compatibility test executed for at least one lift type**

### Target Success
- [ ] All tested orbits show non-abelian Galois groups **downstairs**
- [ ] **At least 80% of tested orbits show abelian Galois groups upstairs**
- [ ] **Compatibility with WP3 integrals confirmed**
- [ ] Clear validation of lift-integrability hypothesis

### Stretch Success
- [ ] Symbolic proofs for all orbits (downstairs and upstairs)
- [ ] Both S¹ and KS-Spinor lifts show abelian structure
- [ ] Extension to 3D orbits
- [ ] **Publication-quality proof of lift-integrability**

---

## Timeline (Revised)

**Week 1** (Days 1-5):
- Days 1-2: Task 4.2.1 (Downstairs VE Setup)
- Days 3-5: Task 4.2.2 (Downstairs Kovacic)

**Week 2** (Days 6-10):
- Day 6: Task 4.2.3 (Downstairs Validation)
- Days 7-9: Task 4.2.4 (Upstairs VE Setup) **NEW**
- Day 10: Integration and testing

**Week 3** (Days 11-14):
- Days 11-13: Task 4.2.5 (Upstairs Kovacic) **NEW**
- Day 14: Task 4.2.6 (Compatibility Test) **NEW**

**Total Duration**: 10-14 days (vs. original 5-7 days)

---

## Critical Dependencies

### From WP2 (Required)

This amended plan **requires** that WP2 deliverables include:

- [ ] **Symbolic implementation** of extended Hamiltonians (S¹ and KS-Spinor)
- [ ] **Symbolic implementation** of extended symplectic forms
- [ ] **Connection one-form** $A$ (for S¹ bundle) - from WP 2.1.2
- [ ] **Constraint Hamiltonians** (for KS-Spinor) - from WP 2.3.3

**If WP2 is only numerical**: Upstairs Galois group computation will be significantly more difficult (requiring numerical→symbolic conversion).

**RECOMMENDATION**: Implement WP2 lifts using SymPy for symbolic manipulation.

---

## Amendments Summary

| Aspect | Original Plan | Amended Plan |
|--------|--------------|--------------|
| **Scope** | Downstairs only | Downstairs + Upstairs |
| **Tasks** | 3 tasks | 6 tasks |
| **Duration** | 5-7 days | 10-14 days |
| **Code Lines** | ~1,500 | ~3,000 |
| **Key Addition** | — | Upstairs Galois group computation (Tasks 4.2.4-4.2.6) |
| **Validation** | Confirms non-integrability | Confirms lift-integrability |
| **Deliverable** | Downstairs obstruction proof | **Complete compatibility test** |

---

**Document Version**: 2.0 (AMENDED)
**Created**: 2025-11-16 (original), 2025-11-20 (amended)
**Status**: Complete Implementation Plan (Amended)
**Estimated Implementation Time**: 10-14 days
**Amendment Author**: Based on critical analysis of theoretical framework vs. implementation gap
