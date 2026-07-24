# WP6-DZ-FEAS-v1 Witness Audit

## Purpose

This campaign asks one bounded question: does the locked search expose an
explicit, non-equilibrium algebraic phase curve of the full planar Newtonian
three-body problem on `(H,C)=(0,0)` that is suitable for a tangent
Morales-Ramis or Ziglin analysis?

The campaign does not attempt to prove nonintegrability. Its null outcome is a
search result, not a nonexistence theorem.

## Pre-Discovery Lock

The specification, `W1`-`W12`, twelve queries, eight mandatory candidate
classes, source and candidate caps, stop rules, adversarial controls, and MR
promotion rule were signed before discovery. The lock records that no
candidate ledger, discovery implementation, discovery source manifest, or
qualification output existed.

## Source Frontier

The campaign inspected sixteen primary payloads:

- four prelocked theorem seeds;
- twelve eligible citation-expansion sources, reaching the locked expansion
  cap;
- all twelve query windows; and
- every plausible exact-orbit or explicit double-zero result in those windows.

The payload hashes and source roles are in
`sources/discovery_manifest.json`. Search-result screening and exclusions are
in `search_receipt.json`.

## Exact Controls

### Legacy Euler fixture

For equal masses at `x=(-1,0,1)`, the positive Newtonian potential is

`U = 1 + 1 + 1/2 = 5/2`.

The legacy outer speed satisfies `v^2=3/2`, so

`T = v^2 = 3/2`, and therefore `H=T-U=-1`.

The fixture's zero-energy annotation is false.

### Corrected parabolic Euler curve

Set `kappa^2=5/2` and use the algebraic parameter `s`:

`q=(-s^2,0,s^2)`, `qdot=(kappa/s,0,-kappa/s)`,

with differential field `C(s,kappa)`, `kappa^2=5/2`, and

`d/dt = -kappa/(2s^2) d/ds`.

The outer acceleration from the curve is
`kappa^2/(2s^4)=5/(4s^4)`. Newtonian attraction gives
`1/s^4+1/(4s^4)=5/(4s^4)`. Also,

`T=5/(2s^2)=U`, so `H=0`, while radial collinear motion gives `C=0`.

This is exact and algebraic, but it is the known homothetic curve. It fails
`W3`, and the pinned literature says its double-zero variational equations are
integrable at all orders, so it fails `W9`.

### Positive scaling

For length scale `a>0`, Newtonian similarity sends `H` to `H/a`. It preserves
the sign of every nonzero energy and cannot move a periodic or free-fall orbit
onto `H=0`.

### Periodic families

With `I=sum m_i |q_i|^2` and positive attraction `U`, the
Lagrange-Jacobi identity is

`I'' = 4H + 2U`.

For a collision-free periodic orbit, averaging one period gives

`0 = 4H + 2<U>`, hence `H=-<U>/2<0`.

This excludes every collision-free Newtonian choreography or periodic
catalogue from the target level, independent of numerical accuracy or mass
choice.

### Free fall

A finite collision-free configuration released from rest has `T=0` and
`H=-U<0`. This excludes free-fall initial conditions before any numerical
integration.

### Recent explicit triple-collision formula

The inspected publisher presentation uses equal masses and a finite initial
configuration at rest, so its Newtonian energy is strictly negative. Its
displayed `r(u)` and `delta(u)` share the same `cos^2` factor, with constant
`(delta/r)^2=3/4`; the shape is fixed. The treatment is also described as
formal. It therefore fails mass scope, nonhomothety, exact target energy, and
physical meromorphic-regularization requirements.

## Candidate Results

| ID | Family | First decisive failure |
|---|---|---|
| C01 | Parabolic central configurations | `W3`, `W9`: known homothetic, obstruction-free |
| C02 | Full rectilinear collision-manifold flow | `W1`, `W5`: no identified algebraic orbit |
| C03 | Weak-KAM/free-time minimizers | `W5`: existence without algebraic phase curve |
| C04 | Isosceles zero-energy geodesics | `W2`, `W5`: symmetry-restricted and nonexplicit |
| C05 | Parabolic restricted collinear problem | `W1`, `W2`: massless restricted model |
| C06 | Triple-collision blow-up strata | `W1`, `W5`, `W10`: no orbit and generic essential singularity |
| C07 | Recent explicit triple collision | `W2`, `W3`, `W4`: equal-mass, homothetic, negative energy |
| C08 | Figure-eight/choreographies | `W4`: periodic Newtonian energy is negative |
| C09 | Regularized numerical examples | `W4`, `W5`: h=-1 examples and numerical trajectories |
| C10 | Free-fall/brake orbits | `W4`: exact negative energy |
| C11 | Saari homographic classifications | `W1`, `W3`: no new orbit; C=0 branch is homothetic |
| C12 | Published MR/Ziglin parabolic analyses | `W3`, `W9`: same homothetic fixed-level failure |

`C03` is the nearest miss. It proves that the double-zero level contains many
nonhomothetic physical solutions for arbitrary positive masses. What it does
not provide is the object MR/Ziglin needs here: one explicit algebraic phase
curve and its candidate-specific tangent NVE.

## W1-W12 Outcome

Every candidate has an explicit decision for all twelve requirements. No
candidate passes all requirements. No candidate reaches a qualifying
candidate-specific NVE, so the conditional independent NVE reproduction is
not triggered. A source-disjoint implementation nevertheless reproduces all
exact negative controls.

## Bounded Result

The campaign outcome is `COMPLETE_BOUNDED_NULL_RESULT`.

Authorized claim:

> Under the locked WP6-DZ-FEAS-v1 primary-source and exact-audit protocol, no
> explicit non-equilibrium algebraic phase curve satisfying every W1-W12
> requirement was found.

This does not claim that no suitable witness exists. It does not prove
nonintegrability on `(H,C)=(0,0)`. It does not prove a differential-Galois or
Ziglin obstruction.

## MR Promotion

The locked promotion condition is false. `WP6-DZ-MR-v1` must not be created
from this result.

Any renewed search requires a separately locked `WP6-DZ-FEAS-v2`. The most
focused route is constructive: impose an algebraically invariant slice or
boundary condition within the weak-KAM/zero-energy collision-manifold
families and prove that one nonhomothetic orbit closes to an algebraic phase
curve. Raising source caps or re-running numerical orbit searches would not
address the observed failure.
