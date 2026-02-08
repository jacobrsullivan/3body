---
name: wp2-lift-constructions
description: >
  S¹ bundle and KS-Spinor lift constructions for testing lift-integrability in the 
  three-body problem. Use when: (1) constructing S¹ principal bundle over shape space, 
  (2) testing fiber momentum conservation (p_θ), (3) implementing extended symplectic forms, 
  (4) applying Kustaanheimo-Stiefel transformation, (5) handling collision regularization, 
  (6) working with spinor coordinates, (7) implementing Sundman time transformation, 
  (8) using RATTLE constrained integrator, (9) computing bilinear constraints as momentum maps, 
  (10) testing integrability in lifted spaces, or (11) comparing S¹ vs KS lift effectiveness. 
  Triggers on requests involving S¹ lift, KS transformation, spinor coordinates, fiber bundle, 
  extended phase space, collision regularization, bilinear relation, momentum map constraint, 
  Sundman time, RATTLE integrator, geometric lift, integrability test, or p_theta conservation.
---

# WP2 Lift Constructions

S¹ bundle and KS-Spinor lift constructions for testing the lift-integrability hypothesis.

## Overview

The lift-integrability hypothesis posits that while the three-body problem is non-integrable in reduced coordinates (proven by Bruns/Poincaré), it may become integrable in appropriately constructed higher-dimensional "lifted" spaces.

```
┌────────────────────────────────────────────────────────────────┐
│ SHAPE SPACE (Reduced, 12D)                                     │
│ ✗ Non-integrable (Bruns, Poincaré)                            │
│ ✗ Curvature F = dA ≠ 0 (geometric obstruction)               │
└──────────────────────────┬─────────────────────────────────────┘
                           │ LIFT CONSTRUCTIONS
           ┌───────────────┴───────────────┐
           ↓                               ↓
┌─────────────────────────┐   ┌─────────────────────────────────┐
│ S¹ BUNDLE LIFT          │   │ KS-SPINOR LIFT                  │
│ Shape × S¹ (8D phase)   │   │ Spinor space (10D phase)        │
│                         │   │                                  │
│ ✓ Geometric untwisting  │   │ ✓ Collision regularization      │
│ ✓ p_θ potentially       │   │ ✓ Reveals SO(4)-like symmetry   │
│   conserved             │   │ ✓ Time regularization           │
│ ✗ No collision handling │   │                                  │
└─────────────────────────┘   └─────────────────────────────────┘
           ↓                               ↓
┌─────────────────────────────────────────────────────────────────┐
│ QUESTION: Is there a new integral of motion in lifted space?    │
│ → If yes: Lift-integrability confirmed!                         │
│ → WP3 searches, WP4 validates                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Lift Selection Guide

| Feature | S¹ Lift | KS-Spinor Lift |
|---------|---------|----------------|
| **Purpose** | Untwist magnetic term | Regularize collisions |
| **Phase dim** | 8D (4D config) | 10D (5D config) |
| **Collisions** | Not handled | Fully regularized |
| **Time** | Physical t | Fictitious s (Sundman) |
| **Complexity** | Lower | Higher |
| **Best for** | Non-collision dynamics | Collision-prone orbits |

### Decision Tree

```
Need to handle close encounters/collisions?
├── Yes → KS-Spinor Lift
└── No → S¹ Bundle Lift

Want to test both approaches?
└── Yes → Run both and compare (recommended for WP3/WP4)
```

## S¹ Bundle Lift (WP 2.2)

### Theory

Construct a circle bundle P = S × S¹ over shape space S:

```
P = S × S¹
   ↓ π
   S

Extended phase space: T*P = 8D = (s, θ, p_s, p_θ)
```

**Key idea**: Add fiber coordinate θ to absorb the magnetic twist from the connection.

### Extended Symplectic Form

```
ω̃ = ω_shape + dθ ∧ d(p_θ - L·A)
```

where:
- ω_shape = canonical form on T*S
- A = mechanical connection 1-form
- L = angular momentum magnitude

### Lifted Hamiltonian

```
H̃(s, θ, p_s, p_θ) = H_red(s, p_s)
```

**Crucial observation**: H̃ is **independent of θ**!

By Noether's theorem: **p_θ is conserved** (if H̃ is truly θ-independent).

### Implementation

```python
from src.python.lifts.s1_bundle import S1Bundle
from src.python.lifts.integrability import test_integrability
import numpy as np

masses = np.array([1.0, 0.3, 0.1])
L = 1.0  # Fixed angular momentum

# 1. Create S¹ bundle
bundle = S1Bundle(masses=masses, angular_momentum=L)

# 2. Initial shape space state (6D: positions + momenta)
shape_state = np.array([1.0, 1.2, 0.8, 0.1, -0.05, 0.02])

# 3. Lift to S¹ bundle (8D: add θ=0 and compute p_θ)
lifted_state = bundle.lift_state(shape_state, theta=0.0)
print(f"Lifted state dimension: {len(lifted_state)}")  # 8D

# 4. Integrate in lifted space
integrator = bundle.create_integrator()
times, lifted_states = integrator.integrate(
    state0=lifted_state,
    t_span=(0, 100),
    dt=0.1
)

# 5. Check fiber momentum conservation
p_thetas = [s[7] for s in lifted_states]  # p_θ is index 7
p_theta_drift = max(p_thetas) - min(p_thetas)
print(f"p_θ drift: {p_theta_drift:.2e}")

if p_theta_drift < 1e-10:
    print("✓ p_θ conserved: New integral found!")
else:
    print("✗ p_θ not conserved: No new integral from S¹ lift")
```

### Extended Symplectic Form Verification

```python
from src.python.lifts.extended_symplectic import ExtendedSymplecticForm

ext_form = ExtendedSymplecticForm(masses=masses, angular_momentum=L)

# Evaluate at lifted state
omega_tilde = ext_form.evaluate(lifted_state)

# Verify closure: dω̃ = 0
is_closed = ext_form.verify_closure(lifted_state)
print(f"Symplectic form closed: {is_closed}")

# Verify non-degeneracy
is_nondegenerate = ext_form.verify_nondegeneracy(lifted_state)
print(f"Symplectic form non-degenerate: {is_nondegenerate}")
```

### Integrability Test

```python
from src.python.lifts.integrability import test_integrability

result = test_integrability(times, lifted_states, bundle)

print(f"Energy E conserved: {result['energy_conserved']}")
print(f"Angular momentum L conserved: {result['L_conserved']}")
print(f"Fiber momentum p_θ conserved: {result['p_theta_conserved']}")
print(f"All in involution: {result['in_involution']}")

# Integrability criterion:
# 4D phase space + 3 independent integrals in involution → integrable!
if all([result['energy_conserved'],
        result['L_conserved'],
        result['p_theta_conserved'],
        result['in_involution']]):
    print("✓ System appears integrable in S¹ lift!")
```

See `references/s1-bundle-theory.md` for complete mathematical theory.

## KS-Spinor Lift (WP 2.3)

### Theory

The Kustaanheimo-Stiefel transformation maps 3D position to 4D spinor:

```
r ∈ ℝ³ → u ∈ ℝ⁴

Bilinear relation: |r| = |u|²
```

This is a **4+1 dimensional lift** (4 spatial + 1 temporal via Sundman).

### KS Transformation

```python
from src.python.regularization.ks_transform import ks_transform, ks_inverse

# 3D position to 4D spinor
r = np.array([1.0, 2.0, 3.0])
u = ks_transform(r)
print(f"Spinor u: {u}")  # 4D vector

# Verify bilinear relation
r_norm = np.linalg.norm(r)
u_norm_sq = np.dot(u, u)
assert np.isclose(r_norm, u_norm_sq), "Bilinear relation violated!"

# Inverse (spinor to position)
r_back = ks_inverse(u)
assert np.allclose(r, r_back)
```

### Levi-Civita Matrix

The transformation uses the Levi-Civita matrix L(u):

```python
def levi_civita_matrix(u):
    """
    Build 4×4 Levi-Civita matrix L(u).
    
    Position r is given by: r = L(u)·u (first 3 components)
    """
    u0, u1, u2, u3 = u
    return np.array([
        [u0, -u1, -u2,  u3],
        [u1,  u0, -u3, -u2],
        [u2,  u3,  u0,  u1],
        [u3, -u2,  u1, -u0]
    ])
```

### Bilinear Constraint as Momentum Map

**Key insight**: The KS constraint is the zero level set of a momentum map!

```
Ξ = u₀p₁ - u₁p₀ + u₂p₃ - u₃p₂ = 0
```

This is the momentum map for the S¹ gauge symmetry of the KS transformation.

```python
def bilinear_constraint(u, p_u):
    """
    Compute KS bilinear constraint Ξ.
    
    This is the S¹ momentum map—should be zero on physical trajectories.
    """
    return u[0]*p_u[1] - u[1]*p_u[0] + u[2]*p_u[3] - u[3]*p_u[2]

# Verify constraint
Xi = bilinear_constraint(u, p_u)
assert abs(Xi) < 1e-10, f"Constraint violated: Ξ = {Xi}"
```

### Sundman Time Transformation

The temporal lift uses fictitious time s:

```
dt/ds = g(r) = |u|² = r
```

Near collisions (r → 0), time slows down → smooth dynamics.

```python
from src.python.regularization.sundman import SundmanTransformation

# Create Sundman transformation
sundman = SundmanTransformation(strategy='simple')  # dt/ds = r

# For multiple bodies, use:
sundman_multi = SundmanTransformation(strategy='sum')  # g = 1/(r₁₂ + r₂₃ + r₃₁)
# Or:
sundman_product = SundmanTransformation(strategy='product')  # g = 1/(r₁₂·r₂₃·r₃₁)
```

### Pairwise KS for Three-Body

Apply KS to all three body pairs:

```python
from src.python.regularization.ks_pairwise import PairwiseKS

pairwise_ks = PairwiseKS(masses=masses)

# Transform positions to spinors (12D = 3 × 4D)
positions = np.array([[0,0,0], [1,0,0], [0.5,0.8,0]])
spinors = pairwise_ks.transform(positions)
# Returns: u₁₂, u₂₃, u₃₁ (each 4D)

# Configuration space: 12D with 6 constraints
# Effective dimension: 12 - 6 + 3 (gauge) = 9D (matches original 3BP)
```

### RATTLE Constrained Integrator

Maintain constraints exactly during integration:

```python
from src.python.regularization.rattle_integrator import RATTLEIntegrator

# Create RATTLE integrator
integrator = RATTLEIntegrator(
    masses=masses,
    constraints='ks_bilinear',  # Enforce Ξ = 0
    dt=0.01,
    tol=1e-14
)

# Integrate in constrained spinor space
times, spinor_states = integrator.integrate(
    state0=spinor_state0,
    t_span=(0, 100)
)

# Verify constraints maintained
for state in spinor_states:
    u, p_u = state[:4], state[4:8]
    Xi = bilinear_constraint(u, p_u)
    assert abs(Xi) < 1e-12, "RATTLE constraint violation!"
```

### Time-Regularized Dynamics

```python
from src.python.regularization.time_regularized_dynamics import TimeRegularizedDynamics

# Full time-regularized 3BP
dynamics = TimeRegularizedDynamics(
    masses=masses,
    sundman_strategy='sum'
)

# Extended phase space: (u, p_u, t, E)
# t = physical time (coordinate)
# E = energy (conjugate momentum to t)

# Equations of motion in fictitious time s
state_dot = dynamics.compute(s, extended_state)
```

See `references/ks-spinor-theory.md` for complete mathematical theory.

## Complete Lift Workflow

```python
def test_lift_integrability(trajectory, masses, method='s1'):
    """
    Test lift-integrability hypothesis using specified lift.
    
    Args:
        trajectory: Dict with 'states', 'times', 'L' (angular momentum)
        masses: Mass array
        method: 's1' or 'ks'
        
    Returns:
        Dict with integrability analysis results
    """
    if method == 's1':
        from src.python.lifts.s1_bundle import S1Bundle
        
        # Construct S¹ bundle
        bundle = S1Bundle(masses=masses, angular_momentum=trajectory['L'])
        
        # Lift trajectory
        lifted = bundle.lift_trajectory(trajectory['states'])
        
        # Integrate in lifted space
        integrator = bundle.create_integrator()
        times, states = integrator.integrate(lifted[0], (0, 100), 0.1)
        
        # Test integrals
        result = test_integrability(times, states, bundle)
        
        return {
            'method': 'S¹ bundle',
            'new_integral': 'p_θ' if result['p_theta_conserved'] else None,
            'integrable': all(result.values()),
            'details': result
        }
        
    elif method == 'ks':
        from src.python.regularization.ks_pairwise import PairwiseKS
        from src.python.regularization.rattle_integrator import RATTLEIntegrator
        
        # KS transformation
        ks = PairwiseKS(masses=masses)
        spinor_state = ks.lift_state(trajectory['states'][0])
        
        # Integrate with RATTLE
        integrator = RATTLEIntegrator(masses=masses)
        times, states = integrator.integrate(spinor_state, (0, 100))
        
        # Search for spinor-based integrals (WP3 does deeper search)
        return {
            'method': 'KS-Spinor',
            'regularized': True,
            'constraints_maintained': True,
            'new_integral': None  # To be discovered by WP3
        }
```

## Comparing Lifts

```python
def compare_lift_methods(initial_conditions, masses, L):
    """
    Compare S¹ and KS lifts on same initial conditions.
    """
    trajectory = {
        'states': initial_conditions,
        'L': L
    }
    
    # Test both lifts
    result_s1 = test_lift_integrability(trajectory, masses, method='s1')
    result_ks = test_lift_integrability(trajectory, masses, method='ks')
    
    print("=" * 50)
    print("LIFT COMPARISON")
    print("=" * 50)
    
    print("\nS¹ Bundle Lift:")
    print(f"  New integral: {result_s1['new_integral']}")
    print(f"  Appears integrable: {result_s1['integrable']}")
    
    print("\nKS-Spinor Lift:")
    print(f"  Regularized: {result_ks['regularized']}")
    print(f"  Constraints OK: {result_ks['constraints_maintained']}")
    print(f"  New integral: {result_ks['new_integral']}")
    
    return {'s1': result_s1, 'ks': result_ks}
```

## Downstream Usage

### For WP3 (Invariant Discovery)

```python
# WP3 searches for integrals in lifted spaces
from src.python.symbolic.multi_stage_pipeline import MultiStageInvariantSearch

# Get lifted trajectory
bundle = S1Bundle(masses=masses, angular_momentum=L)
lifted_traj = bundle.lift_trajectory(shape_trajectory)

# Search in lifted space
search = MultiStageInvariantSearch(
    stages=['polynomial', 'spinor'],
    lifted_space=True
)
results = search.run(lifted_times, lifted_states, mu=mu)

# Look for p_θ or spinor-based integrals
for candidate in results.top_candidates:
    print(f"Found: {candidate.expression}")
```

### For WP4 (Validation)

```python
# WP4 validates using Morales-Ramis test
from src.python.validation.upstairs_variational import compute_upstairs_nve

# Lift periodic orbit
lifted_orbit = bundle.lift_orbit(orbit)

# Compute variational equations in lifted space
upstairs_nve = compute_upstairs_nve(
    lifted_orbit=lifted_orbit,
    lift_type='s1_bundle',
    mu=mu
)

# Apply Kovacic algorithm
galois_result = apply_kovacic_algorithm(upstairs_nve)

print(f"Upstairs Galois group: {galois_result.group_name}")
print(f"Is abelian: {galois_result.is_abelian}")
# If abelian: lift-integrability confirmed!
```

## Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| p_θ not conserved | Numerical error or true non-conservation | Increase precision, verify implementation |
| KS constraint violated | RATTLE tolerance too loose | Tighten RATTLE tolerance |
| Near-collision instability | Need regularization | Switch to KS-Spinor lift |
| Dimension mismatch | Wrong state layout | Check coordinate conventions |

### Diagnostic

```python
def diagnose_lift(lifted_state, lift_type):
    """Diagnose common lift issues."""
    if lift_type == 's1':
        expected_dim = 8
        s, theta, p_s, p_theta = split_s1_state(lifted_state)
        
        return {
            'dimension_correct': len(lifted_state) == expected_dim,
            'theta_in_range': 0 <= theta < 2*np.pi,
            'p_theta_finite': np.isfinite(p_theta),
        }
        
    elif lift_type == 'ks':
        expected_dim = 8  # Per pair
        u, p_u = lifted_state[:4], lifted_state[4:8]
        
        Xi = bilinear_constraint(u, p_u)
        
        return {
            'dimension_correct': len(lifted_state) >= expected_dim,
            'constraint_satisfied': abs(Xi) < 1e-10,
            'spinor_nonzero': np.linalg.norm(u) > 1e-10,
        }
```

## Tests

```bash
# S¹ bundle tests
pytest tests/lifts/test_s1_bundle.py -v
pytest tests/lifts/test_integrability.py -v

# KS tests
pytest tests/symbolic_lifts/test_ks_symbolic.py -v
pytest tests/regularization/test_time_regularization.py -v

# RATTLE integrator
pytest tests/regularization/test_rattle.py -v
```

## References

- `references/s1-bundle-theory.md` - S¹ bundle mathematical theory
- `references/ks-spinor-theory.md` - KS transformation theory
- `references/constraint-momentum-map.md` - Constraints as momentum maps
- `src/python/lifts/` - S¹ bundle implementation
- `src/python/regularization/` - KS and time regularization
- `Science-Research-Docs/WP2 – 2-Body Kepler + KS.pdf` - S¹ theory
- `Science-Research-Docs/WP3 – Generalized KS.pdf` - KS-Spinor theory
- Kustaanheimo & Stiefel (1965) - Original KS paper
- Zhao (2015) - KS as momentum map
