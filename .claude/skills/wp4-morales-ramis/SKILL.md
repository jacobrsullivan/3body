---
name: wp4-morales-ramis
version: 2.0.0
description: >
  Differential Galois theory obstruction test for validating lift-integrability hypothesis.
  Two-phase structure: Phase I confirms classical non-integrability (downstairs non-abelian),
  Phase II validates lift-integrability (upstairs abelian). Use when computing Normal
  Variational Equations (NVE), applying Kovacic algorithm, testing Galois group structure,
  or validating the downstairs/upstairs abelianization pattern.
triggers:
  - morales-ramis
  - differential galois
  - variational equations
  - kovacic algorithm
  - galois group
  - abelian identity component
  - monodromy matrix
  - picard-vessiot
  - nve computation
  - upstairs downstairs
use_cases:
  - Computing Normal Variational Equations along periodic orbits
  - Applying Kovacic algorithm to determine Galois group
  - Testing abelianness of identity component
  - Phase I downstairs non-abelian verification
  - Phase II upstairs abelian validation
  - Lifting periodic orbits to S¹-bundle or KS space
  - Monodromy matrix computation
  - Floquet multiplier analysis
references:
  - references/differential-galois-theory.md
  - references/kovacic-algorithm.md
  - references/nve-computation.md
---

# WP4 Morales-Ramis Test

Differential Galois theory obstruction test for integrability validation.

## Overview

The Morales-Ramis test is the **central theoretical validation** in WP4. It determines whether the three-body problem admits new integrals in the lifted space by analyzing the algebraic structure of variational equations.

### Two-Phase Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    MORALES-RAMIS TEST                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PHASE I: DOWNSTAIRS (Reduced/Shape Space)                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ • Compute NVE along periodic orbit                  │   │
│  │ • Apply Kovacic algorithm                           │   │
│  │ • EXPECTED: Non-abelian Galois group               │   │
│  │ • PURPOSE: Confirm classical non-integrability      │   │
│  │ • OUTCOME: Validates consistency with Bruns-Poincaré│   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  PHASE II: UPSTAIRS (Lifted Space) ⭐ CRITICAL             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ • Lift periodic orbit to S¹-bundle or KS space     │   │
│  │ • Compute NVE in lifted coordinates                 │   │
│  │ • Apply Kovacic algorithm                           │   │
│  │ • EXPECTED (if lift-integrable): Abelian group     │   │
│  │ • PURPOSE: Validate lift-integrability hypothesis   │   │
│  │ • OUTCOME: Compatible/incompatible with WP3 results │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Compatibility Matrix

| Downstairs | Upstairs | WP3 Found Integrals | Verdict |
|------------|----------|---------------------|---------|
| Non-abelian | Abelian | Yes | **LIFT-INTEGRABILITY CONFIRMED** ✓ |
| Non-abelian | Non-abelian | Yes | WP3 integrals spurious |
| Non-abelian | Abelian | No | Integrals exist but missed |
| Non-abelian | Non-abelian | No | Negative result confirmed |
| Abelian | - | - | ERROR: Contradicts Bruns-Poincaré |

## Quick Start

```python
from src.python.validation.morales_ramis import MoralesRamisValidator
from src.python.validation.periodic_orbits import get_lagrange_l4_orbit

mu = 0.012150585609624  # Earth-Moon mass ratio

# Get periodic orbit
orbit = get_lagrange_l4_orbit(mu=mu)

# Create validator
mr_val = MoralesRamisValidator(mu=mu)

# Phase I: Downstairs test
print("=== Phase I: Downstairs ===")
downstairs = mr_val.test_downstairs(orbit)
print(f"Galois group: {downstairs.galois_group}")
print(f"Is abelian: {downstairs.is_abelian}")
# Expected: Non-abelian (confirms classical non-integrability)

# Phase II: Upstairs test
print("\n=== Phase II: Upstairs ===")
upstairs = mr_val.test_upstairs(orbit, lift_type='s1_bundle')
print(f"Galois group: {upstairs.galois_group}")
print(f"Is abelian: {upstairs.is_abelian}")
# If abelian: Lift-integrability compatible!

# Verdict
if not downstairs.is_abelian and upstairs.is_abelian:
    print("\n✓ LIFT-INTEGRABILITY COMPATIBLE!")
else:
    print("\n✗ Not compatible with lift-integrability")
```

## Theoretical Background

### Morales-Ramis Theorem

**Statement**: If a Hamiltonian system is meromorphically integrable in the Liouville sense, then the identity component G⁰ of the differential Galois group of its Normal Variational Equations along any particular solution must be abelian.

**Contrapositive**: Non-abelian G⁰ → System is NOT integrable.

### Normal Variational Equations (NVE)

For a trajectory x(t) satisfying ẋ = X_H(x), the NVE describe infinitesimal perturbations:

```
d/dt (δx) = ∇²H(x(t)) · δx
```

where ∇²H is the Hessian of the Hamiltonian.

### Differential Galois Group

The differential Galois group (DGG) is the group of differential automorphisms of the Picard-Vessiot extension containing all solutions to the NVE. For Hamiltonian systems, G ⊆ Sp(2n, ℂ).

### For Lift-Integrability

The three-body problem is known non-integrable in standard coordinates. We test:

1. **Downstairs**: Non-abelian confirms classical obstruction
2. **Upstairs**: If abelian, the obstruction is removed by the lift

## Phase I: Downstairs Test

### Computing NVE in Reduced Space

```python
from src.python.validation.variational_equations import compute_nve
from src.python.validation.periodic_orbits import PeriodicOrbit

def compute_downstairs_nve(orbit: PeriodicOrbit, mu: float):
    """
    Compute NVE in reduced (shape) space coordinates.

    Returns:
        NVESystem with coefficient matrices A(t)
    """
    # Get Hamiltonian Hessian
    def hessian(state, mu):
        """Compute ∇²H at state."""
        # ... numerical or symbolic Hessian
        pass

    # Compute A(t) along orbit
    times = np.linspace(0, orbit.period, 1000)
    A_matrices = []

    for t in times:
        state = orbit.state_at(t)
        H_hess = hessian(state, mu)

        # NVE: δẋ = J · ∇²H · δx where J is symplectic matrix
        J = np.array([[0, 0, 0, 1, 0, 0],
                      [0, 0, 0, 0, 1, 0],
                      [0, 0, 0, 0, 0, 1],
                      [-1, 0, 0, 0, 0, 0],
                      [0, -1, 0, 0, 0, 0],
                      [0, 0, -1, 0, 0, 0]])

        A = J @ H_hess
        A_matrices.append(A)

    return NVESystem(times=times, A_matrices=A_matrices, period=orbit.period)
```

### Applying Kovacic Algorithm

The Kovacic algorithm determines the Galois group of second-order linear ODEs:

```python
from src.python.validation.kovacic import kovacic_algorithm

# Reduce NVE to scalar form if possible
# y'' + a(t)y' + b(t)y = 0

result = kovacic_algorithm(a_coeff, b_coeff, domain='periodic')

print(f"Kovacic case: {result.case}")
print(f"Galois group: {result.galois_group}")
print(f"Is abelian: {result.is_abelian}")
```

### Using the Validator

```python
from src.python.validation.morales_ramis import MoralesRamisValidator

mr_val = MoralesRamisValidator(mu=mu)
result = mr_val.test_downstairs(orbit)

print(f"Galois group: {result.galois_group}")
print(f"Is abelian: {result.is_abelian}")
print(f"Eigenvalues: {result.monodromy_eigenvalues}")
print(f"Monodromy trace: {result.monodromy_trace:.4f}")
```

**Expected**: Non-abelian (SL(2,ℂ) or non-abelian subgroup)

## Phase II: Upstairs Test

### Lifting Periodic Orbits

```python
from src.python.lifts.s1_bundle import S1BundleLift
from src.python.lifts.ks_spinor import KSLift

def lift_orbit_to_s1(orbit: PeriodicOrbit, mu: float, L: float):
    """
    Lift periodic orbit to S¹-bundle over shape space.

    Parameters:
        orbit: Periodic orbit in reduced space
        L: Angular momentum value

    Returns:
        LiftedOrbit in extended phase space
    """
    lift = S1BundleLift(mu=mu, angular_momentum=L)

    # Lift initial condition
    state0 = orbit.state0
    lifted_state0 = lift.lift_state(state0)

    # Integrate in lifted space
    lifted_trajectory = lift.integrate(
        lifted_state0,
        t_span=(0, orbit.period),
        dense_output=True
    )

    return LiftedOrbit(
        trajectory=lifted_trajectory,
        period=orbit.period,
        base_orbit=orbit,
        lift_type='s1_bundle'
    )
```

### Computing Upstairs NVE

```python
def compute_upstairs_nve(
    lifted_orbit: LiftedOrbit,
    mu: float,
    lift_type: str = 's1_bundle'
):
    """
    Compute NVE in lifted (upstairs) coordinates.

    The lifted Hamiltonian H̃ includes fiber terms.
    """
    if lift_type == 's1_bundle':
        # Extended Hamiltonian: H̃ = H + p_θ · A(q, p)
        def lifted_hessian(lifted_state, mu):
            # ... compute ∇²H̃
            pass
    elif lift_type == 'ks_spinor':
        # KS-regularized Hamiltonian
        def lifted_hessian(lifted_state, mu):
            # ... compute in spinor coordinates
            pass

    # Compute A(t) matrices
    times = np.linspace(0, lifted_orbit.period, 1000)
    A_matrices = []

    for t in times:
        state = lifted_orbit.state_at(t)
        H_hess = lifted_hessian(state, mu)

        # Extended symplectic structure
        n_lifted = len(state) // 2
        J = np.block([
            [np.zeros((n_lifted, n_lifted)), np.eye(n_lifted)],
            [-np.eye(n_lifted), np.zeros((n_lifted, n_lifted))]
        ])

        A = J @ H_hess
        A_matrices.append(A)

    return NVESystem(times=times, A_matrices=A_matrices, period=lifted_orbit.period)
```

### Running Phase II Test

```python
# S¹ bundle lift
upstairs_s1 = mr_val.test_upstairs(orbit, lift_type='s1_bundle')
print(f"S¹ Galois group: {upstairs_s1.galois_group}")
print(f"S¹ Is abelian: {upstairs_s1.is_abelian}")

# KS-spinor lift
upstairs_ks = mr_val.test_upstairs(orbit, lift_type='ks_spinor')
print(f"KS Galois group: {upstairs_ks.galois_group}")
print(f"KS Is abelian: {upstairs_ks.is_abelian}")
```

**Expected (if lift-integrable)**: Abelian

## Periodic Orbit Library

### Available Orbits

```python
from src.python.validation.periodic_orbits import (
    get_lagrange_l4_orbit,
    get_lagrange_l5_orbit,
    get_lyapunov_orbit,
    get_halo_orbit,
    get_figure8_orbit
)

# Lagrange points (equilateral triangle)
l4_orbit = get_lagrange_l4_orbit(mu=mu)
l5_orbit = get_lagrange_l5_orbit(mu=mu)

# Lyapunov orbits around collinear points
lyapunov_l1 = get_lyapunov_orbit(mu=mu, L_point='L1', amplitude=0.01)
lyapunov_l2 = get_lyapunov_orbit(mu=mu, L_point='L2', amplitude=0.01)

# Halo orbits (3D)
halo_l2 = get_halo_orbit(mu=mu, L_point='L2', amplitude=0.1, family='northern')

# Figure-8 choreography
figure8 = get_figure8_orbit()
```

### Orbit Properties

```python
orbit = get_lagrange_l4_orbit(mu=mu)

print(f"Period: {orbit.period:.6f}")
print(f"Initial state: {orbit.state0}")
print(f"Jacobi constant: {orbit.jacobi_constant:.6f}")
print(f"Stability type: {orbit.stability}")
print(f"Floquet multipliers: {orbit.floquet_multipliers}")
```

## Complete Workflow

```python
def run_complete_morales_ramis(mu: float, orbit_type: str = 'lagrange_l4'):
    """
    Complete two-phase Morales-Ramis test.

    Returns:
        Dict with verdict and detailed results
    """
    from src.python.validation.morales_ramis import MoralesRamisValidator
    from src.python.validation import periodic_orbits

    # Get orbit
    orbit_func = getattr(periodic_orbits, f'get_{orbit_type}_orbit')
    orbit = orbit_func(mu=mu)

    print(f"{'='*60}")
    print(f"MORALES-RAMIS TEST: {orbit_type}")
    print(f"{'='*60}")
    print(f"Period: {orbit.period:.6f}")
    print(f"Jacobi constant: {orbit.jacobi_constant:.6f}")

    mr_val = MoralesRamisValidator(mu=mu)
    results = {}

    # Phase I: Downstairs
    print(f"\n{'─'*60}")
    print("PHASE I: DOWNSTAIRS (Reduced Space)")
    print(f"{'─'*60}")

    downstairs = mr_val.test_downstairs(orbit)
    results['downstairs'] = downstairs

    print(f"Galois group: {downstairs.galois_group}")
    print(f"Is abelian: {downstairs.is_abelian}")
    print(f"Monodromy trace: {downstairs.monodromy_trace:.4f}")

    if downstairs.is_abelian:
        print("\n⚠ WARNING: Downstairs is abelian!")
        print("  This contradicts Bruns-Poincaré theorem.")
        print("  Check orbit validity or numerical accuracy.")
        return {'valid': False, 'error': 'unexpected_abelian_downstairs'}

    print("✓ Non-abelian (classical obstruction confirmed)")

    # Phase II: Upstairs (S¹)
    print(f"\n{'─'*60}")
    print("PHASE II: UPSTAIRS (S¹ Bundle)")
    print(f"{'─'*60}")

    upstairs_s1 = mr_val.test_upstairs(orbit, lift_type='s1_bundle')
    results['upstairs_s1'] = upstairs_s1

    print(f"Galois group: {upstairs_s1.galois_group}")
    print(f"Is abelian: {upstairs_s1.is_abelian}")

    # Phase II: Upstairs (KS)
    print(f"\n{'─'*60}")
    print("PHASE II: UPSTAIRS (KS-Spinor)")
    print(f"{'─'*60}")

    upstairs_ks = mr_val.test_upstairs(orbit, lift_type='ks_spinor')
    results['upstairs_ks'] = upstairs_ks

    print(f"Galois group: {upstairs_ks.galois_group}")
    print(f"Is abelian: {upstairs_ks.is_abelian}")

    # Verdict
    print(f"\n{'='*60}")
    print("VERDICT")
    print(f"{'='*60}")

    s1_compatible = not downstairs.is_abelian and upstairs_s1.is_abelian
    ks_compatible = not downstairs.is_abelian and upstairs_ks.is_abelian

    if s1_compatible:
        print("✓ S¹ LIFT: Compatible with lift-integrability")
    else:
        print("✗ S¹ LIFT: NOT compatible")

    if ks_compatible:
        print("✓ KS LIFT: Compatible with lift-integrability")
    else:
        print("✗ KS LIFT: NOT compatible")

    return {
        'valid': True,
        'downstairs': downstairs,
        'upstairs_s1': upstairs_s1,
        'upstairs_ks': upstairs_ks,
        's1_compatible': s1_compatible,
        'ks_compatible': ks_compatible,
        'orbit_type': orbit_type
    }

# Usage
result = run_complete_morales_ramis(mu=0.012150585609624, orbit_type='lagrange_l4')
```

## Monodromy Analysis

### Computing Monodromy Matrix

```python
from src.python.validation.monodromy import compute_monodromy_matrix

def analyze_monodromy(orbit: PeriodicOrbit, mu: float):
    """
    Compute and analyze monodromy matrix.
    """
    # Compute fundamental matrix solution
    M = compute_monodromy_matrix(orbit, mu)

    # Eigenvalue analysis
    eigenvalues = np.linalg.eigvals(M)

    # Floquet multipliers (should come in reciprocal pairs for Hamiltonian)
    floquet = np.sort(np.abs(eigenvalues))[::-1]

    # Stability classification
    if np.all(np.abs(eigenvalues) < 1.01):
        stability = 'stable'
    elif np.any(np.abs(eigenvalues) > 1.01):
        stability = 'unstable'
    else:
        stability = 'marginally_stable'

    return {
        'monodromy_matrix': M,
        'eigenvalues': eigenvalues,
        'floquet_multipliers': floquet,
        'trace': np.trace(M),
        'determinant': np.linalg.det(M),
        'stability': stability
    }
```

## Common Issues

### Downstairs is Abelian?

This contradicts the Bruns-Poincaré theorem. Possible causes:
- Orbit is not valid (numerical error in period)
- Coordinate system mismatch
- Orbit is at a special point (measure zero)

**Resolution**:
```python
# Verify orbit validity
assert abs(orbit.final_state - orbit.state0).max() < 1e-10, "Orbit not closed"

# Check Jacobi constant conservation
C_initial = jacobi_constant(orbit.state0, mu)
C_final = jacobi_constant(orbit.final_state, mu)
assert abs(C_final - C_initial) < 1e-10, "Jacobi constant not conserved"

# Try different orbit
result = run_complete_morales_ramis(mu, orbit_type='lyapunov_l1')
```

### Kovacic Algorithm Fails?

NVE may have singularities or be in non-standard form.

**Resolution**:
```python
# Try different periodic orbit
# Use numerical monodromy analysis as fallback
monodromy = analyze_monodromy(orbit, mu)
# Check if monodromy group is abelian via trace
```

### Upstairs Still Non-Abelian?

The lift does not remove the obstruction for this orbit.

**Implications**:
- WP3 candidates on this lift type are likely spurious
- Try different lift type (S¹ vs KS)
- May indicate fundamental limitation

## Tests

```bash
pytest tests/validation/test_kovacic.py -v
pytest tests/validation/test_periodic_orbits.py -v
pytest tests/validation/test_morales_ramis.py -v
pytest tests/validation/test_monodromy.py -v
```

## References

- `references/differential-galois-theory.md` - DGG theory and Morales-Ramis theorem
- `references/kovacic-algorithm.md` - Kovacic algorithm implementation
- `references/nve-computation.md` - NVE computation methods
- Morales-Ruiz & Ramis (2001). "Galoisian obstructions to integrability"
- Kovacic (1986). "Algorithm for solving second order linear ODEs"
- Ziglin (1983). "Branching of solutions and nonexistence of first integrals"
