# WP1/WP2 Model and Qualification Boundary

Date: 2026-07-20

Status: `PRE-HOLDOUT IMPLEMENTATION`

Qualification decision: `PENDING`

New scientific claims defined here: `UNQUALIFIED`

## Purpose

This document prevents evidence from one dynamical model from being used as
evidence for another. It defines the boundary among:

1. the already qualified WP1 normalized rotating-frame CR3BP path;
2. the proposed WP1 full Newtonian three-body path, `WP1Q-N3BP-v1`; and
3. the proposed WP2 canonical Kepler/KS prototype, `WP2KSQ-v1`.

The existing WP1 CR3BP decision remains immutable. Neither proposed campaign
inherits its `PASS`, and neither proposed claim may be represented as qualified
until its own first-execution holdout passes under an integrity-valid lock.

## Governing Records

| Track | Specification | Required final record | Current status |
|---|---|---|---|
| WP1 CR3BP | `validation-external/wp1-validation/qualification_spec.json` | `validation-external/wp1-validation/reports/wp1_qualification_record.json` | `PASS` as `WP1Q-v1-937694ba58a8` |
| WP2 Kepler/KS | `validation-external/wp2-ks-validation/qualification_spec.json` | `validation-external/wp2-ks-validation/reports/wp2_ks_qualification_record.json` | Development/calibration `PASS`; holdout not yet executed |
| WP1 full N3BP | `validation-external/wp1-n3bp-validation/qualification_spec.json` | `validation-external/wp1-n3bp-validation/reports/wp1_n3bp_qualification_record.json` | Development/calibration `PASS`; holdout not yet executed |

The two proposed qualification identifiers are not assigned until freeze. Names
such as `WP2KSQ-v1-PENDING` and `WP1Q-N3BP-v1-PENDING` are campaign labels, not
qualification IDs.

## Model Contracts

### Qualified WP1 CR3BP contract

The locked WP1 claim concerns one massless test particle in the normalized
circular restricted three-body problem.

- State: `(x, y, z, vx, vy, vz)`.
- Frame: uniformly rotating, barycentric CR3BP frame.
- Primaries: prescribed circular motion; they are not integrated state
  variables.
- Parameters: mass parameter `mu`; normalized primary separation, total primary
  mass, angular speed, and gravitational constant are one under the JPL CR3BP
  convention.
- Time: dimensionless physical CR3BP time, with rotating angular speed one.
- Evidence: the systems, orbit families, stability strata, precision tiers, and
  limits in the locked `WP1Q-v1-937694ba58a8` record only.

The six-column field labelled `inertial` in a WP1 CR3BP artifact is still the
state of the massless particle after a frame transformation. It is not an 18D
state for three dynamically evolving masses.

### WP1Q-N3BP-v1 contract

The proposed WP1 full-three-body track concerns the collisionless Newtonian
three-body equations

```text
dr_i/dt = v_i
dv_i/dt = G * sum(j != i) m_j * (r_j - r_i) / ||r_j - r_i||^3
```

with three strictly positive finite masses.

- Stored state is always 18D, including for planar cases:
  `(r1x,r1y,r1z,r2x,r2y,r2z,r3x,r3y,r3z,`
  `v1x,v1y,v1z,v2x,v2y,v2z,v3x,v3y,v3z)`.
- Frame: non-rotating barycentric inertial Cartesian frame.
- Barycentric constraints at the declared epoch:
  `sum(m_i*r_i) = 0` and `sum(m_i*v_i) = 0`.
- Planar v1 convention: the orbital plane is the `xy` plane and every stored
  `z` and `vz` component is exactly zero in the canonical corpus.
- Parameters: ordered `(m1,m2,m3)` and `G` are mandatory data, not global
  assumptions.
- Units: source-native nondimensional values with `G=1` for v1. Any source
  normalization must be an explicit, reversible, versioned provenance transform;
  no implicit rescaling is permitted.
- Time: monotonically increasing physical/source nondimensional Newtonian time
  `t`, with epoch `t=0` at the published or provenance-recorded initial state.
- Momentum, when needed by WP2, is derived as `p_i=m_i*v_i` and must not be
  confused with velocity.

Until a final record exists, this claim remains `UNQUALIFIED`. The executable
specification limits it to bounded collision-free full-state propagation, not
native periodic-orbit discovery. Numerical evidence comprises analytic planar
and spatially rotated Lagrange motion, a published rounded figure-eight,
pinned unequal-mass SJTU source states, and independent REBOUND IAS15
checkpoint propagation.

### WP2KSQ-v1 contract

The proposed WP2 prototype concerns the isolated relative two-body Kepler
Hamiltonian

```text
H_K(x,p) = ||p||^2 / (2*m_red) - kappa / ||x||
```

on `T*(R^3 minus {0})`, with `m_red > 0`, `kappa > 0`, and fixed bound energy
`E < 0`. Here `p=m_red*dx/dt` is canonical momentum.

The canonical KS convention is fixed as follows. For
`u=(u1,u2,u3,u4)` define the Hopf/KS map:

```text
x1 = 2*(u1*u3 + u2*u4)
x2 = 2*(u1*u4 - u2*u3)
x3 = u1^2 + u2^2 - u3^2 - u4^2
r  = ||x|| = ||u||^2
```

Let `J*u=(-u2,u1,-u4,u3)`. The `S^1` action and its cotangent lift are

```text
(u,p_u) -> (R(theta)u, R(theta)p_u),  R(theta)=exp(theta*J),
```

and the momentum map is

```text
Xi(u,p_u) = p_u dot (J*u)
           = u1*p2 - u2*p1 + u3*p4 - u4*p3.
```

The qualified reduction candidate is the zero level
`Xi^-1(0)/S^1`. If `D K(u)` denotes the `3x4` Jacobian of the KS map, the
cotangent relation is

```text
p_u = D K(u)^T p,
p   = D K(u) p_u / (4*r)  on Xi=0 and u != 0.
```

It must preserve the canonical one-form on horizontal variations and induce
the canonical symplectic form on the quotient. Norm identities alone are not
constraints and may not be substituted for `Xi=0`.

With the fixed-energy Sundman convention `dt/ds=r`, the zero-level
pre-regularized Hamiltonian is

```text
K_E(u,p_u) = r*(H_K-E)
           = ||p_u||^2/(8*m_red) - E*||u||^2 - kappa = 0.
```

For `E<0`, its Hamilton equations are the regular four-dimensional isotropic
oscillator

```text
du/ds   = p_u/(4*m_red)
dp_u/ds = 2*E*u
```

with physical time reconstructed by integrating `dt/ds=||u||^2`. A different
sign, matrix, momentum, or Sundman convention is a different specification and
requires a new qualification version or an explicit proved equivalence before
freeze.

Until a final record exists, this claim remains `UNQUALIFIED`. Its executable
scope is isolated negative-energy Kepler motion at `Xi=0`, with independently
encoded analytic conics, REBOUND IAS15 checkpoints, deterministic structural
tests, nonunit reduced-mass cases, and a regular-variable radial-collision
continuation. It does not cover a pair perturbed by a third body.

## Evidence Non-Inheritance Rules

| Evidence source | CR3BP propagation | Kepler/KS reduction | Full N3BP propagation | Three-body reduction/pairwise KS |
|---|---:|---:|---:|---:|
| `WP1Q-v1-937694ba58a8` | Qualified within its lock | No | No | No |
| Proposed `WP2KSQ-v1` | No | Only after its own `PASS` | No | Necessary but insufficient |
| Proposed `WP1Q-N3BP-v1` | No | No | Only after its own `PASS` | Necessary but insufficient |

In particular:

- A CR3BP state cannot be qualification-preservingly promoted to N3BP. Adding
  prescribed primary states and a zero-mass third body changes neither the
  restricted model nor its evidence and violates the strictly positive N3BP
  mass contract.
- A generic N3BP pair is not an isolated Kepler problem because the third body
  perturbs both members. KS prototype evidence transfers only to the exact
  isolated two-body contract and to later formulas whose equivalence is proved.
- Agreement after projecting a lifted trajectory is necessary but does not by
  itself validate a quotient, symplectic structure, momentum map, or
  regularization.
- Passing unit tests, symbolic simplification, or development data is not a
  qualification decision.

## Corpus and Provenance Boundary

Each campaign independently preserves:

1. immutable source payloads and source metadata;
2. an explicit normalization/canonicalization transform;
3. stable case IDs and deterministic development, calibration, and holdout assignments;
4. a canonical corpus and a hash of the reserved holdout IDs;
5. original decimal source values and explicit barycentric transforms;
6. separately encoded analytic and external-implementation outputs; and
7. hashes for every decision-bearing result.

The N3BP campaign performs no source-seed correction and does not train or fit
a case-dependent model. It therefore splits the authors' continuation table by
source row while disclosing that relationship; neighboring rows cannot tune the
fixed Newtonian equations, DOP853 tolerances, or frozen gates. This v1 decision
does not qualify family discovery, continuation, correction, stability labels,
or catalogue completeness. Rotated Lagrange cases are analytic covariance
strata, not independent discovered families.

## Lock and Decision Semantics

Before holdout execution, each campaign must freeze a repository-relative lock
covering its specification, production numerical source, qualification scripts,
tests, environment locks, source snapshots, normalized corpus, corpus manifest,
holdout IDs, and passing development/calibration results.

- Freeze requires a clean worktree and no holdout result files.
- Holdout execution requires successful lock verification.
- The holdout is executed exactly once for a qualification version.
- Thresholds, code, data, case eligibility, and exclusion rules cannot change
  after freeze.
- A failed holdout remains `FAIL`. Remediation requires a new version, a new
  split salt, and a newly reserved holdout; the failed evidence is retained.
- `PASS` requires every mandatory gate, artifact audit, and bounded platform
  parity check to pass, followed by an immutable machine-readable record.
- `UNQUALIFIED` and `PENDING` must be fail-closed for artifact writers and
  downstream consumers.

## Downstream Gate

Reimplementation, acceptance, or scientific use of full three-body reduction
and pairwise KS is prohibited until both of these conditions are true:

```text
WP2KSQ record.status == "PASS" AND lock verification succeeds
WP1Q-N3BP record.status == "PASS" AND lock verification succeeds
```

Design notes and test-fixture planning may continue, but existing three-body
reduction and pairwise-KS code remains an unqualified legacy prototype. It may
not generate claim-bearing evidence or be presented as a validated downstream
input. After both prerequisite records pass, the downstream work still requires
its own specification and qualification; prerequisite evidence does not confer
an automatic `PASS`.

## Change Control

Changes to a model equation, state ordering, frame, unit or time convention,
KS matrix/sign convention, momentum-map level, source eligibility rule, split
algorithm, gate, or lock policy require an explicit specification version
change. Editorial clarifications that do not change executable meaning may be
recorded before freeze. After freeze, any change invalidates that campaign
version.
