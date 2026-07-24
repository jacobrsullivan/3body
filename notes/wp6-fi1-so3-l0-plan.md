# WP6-FI1 / WP2-SO3-LEAF / WP6-L0 execution plan

Status: specifications locked before implementation

Baseline: `e04390652793b602bdb91df2f5fb239492b74a3c`

This successor work preserves the completed WP5 publication chain unchanged.
It addresses three distinct gaps and does not merge their claims.

## 1. WP6-FI1-v1

Qualify the published Morales-Ruiz--Simon obstruction to one additional
meromorphic first integral for the positive-mass Newtonian three-body problem.
The project-owned layer will:

1. reproduce the exact mass invariant and both Lagrange witness branches;
2. audit the exceptional mass branches left by the earlier Tsygvintsev NVE;
3. independently check Hessian spectra at exact mass specializations;
4. distinguish an unreduced theorem, independent of the classical integrals,
   from a theorem on a specified fixed-momentum reduced leaf.

The authorized result will not concern non-meromorphic integrals or assert that
every individual Lagrange neighborhood is obstructed by the same witness.

## 2. WP2-SO3-LEAF-v1

Extend the qualified nine-dimensional regular SO(3) Poisson quotient to an
explicit leaf model.  On the non-collinear chart

`rho=(r,0,0), lambda=(x,y,0), r>0, y>0`,

the new coordinates are

`(r,x,y,pr,px,py,ell_x,ell_y,ell_z)`.

The project-owned layer will:

1. implement the exact momentum-coordinate cotangent map and inverse;
2. implement the canonical plus body Lie-Poisson tensor;
3. implement the Newtonian Hamiltonian, analytic gradient, and reduced flow;
4. qualify nonzero leaves `|ell|=mu` and the zero leaf `ell=0`;
5. compare against the existing independently qualified quotient flow and a
   source-disjoint finite-difference/symbolic reference.

Collinear configurations, collisions, and a global atlas remain outside this
chart.  The zero leaf is qualified as a regular non-collinear stratum; it does
not contain the collinear witness used by WP6-L0-v1.

## 3. WP6-L0-v1

Qualify the planar zero-angular-momentum, nonzero-energy restricted
nonintegrability result.  The project-owned layer will:

1. reproduce the Pacella/Combot spectral implication
   `lambda>2 => -lambda/2<-1`;
2. prove exact exclusion from the degree-minus-one Morales-Ramis allowed set;
3. reproduce an exact equal-mass Euler configuration benchmark;
4. bind the result to the 2025 common-level theorem and its definition of
   restricted rational integrability.

The doubly-zero level `(H,C)=(0,0)`, spatial zero momentum, absence of one
additional integral, and collision regularization are prohibited conclusions.

## Completion gate

Each track must have:

- a preimplementation specification lock;
- pinned primary-source hashes and machine-checked source text contracts;
- a source-disjoint reference implementation;
- deterministic positive and adversarial controls;
- an immutable qualification lock, result, record, and report;
- focused tests and a full non-slow regression pass;
- a final boundary assessment that states exactly what is and is not proved.
