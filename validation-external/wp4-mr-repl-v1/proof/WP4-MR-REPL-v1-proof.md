# WP4-MR-REPL-v1 Exact Reproduction

## Scope

The proof concerns the complexification of the planar positive-mass Newtonian
three-body Hamiltonian after translation reduction, rotation reduction at
fixed nonzero angular momentum, and the normalizations `G=1`, `k=1`,
`m3=1`. Positive common scaling represents every finite positive mass triple.
The starting reduced Hamiltonian is the one declared in the locked
specification.

The source-disjoint reference program constructs every derivative below from
that Hamiltonian. It does not import a published NVE matrix or the production
certificate.

## R1: Reduced Hamiltonian

Set

```text
M1 = 1 + 1/m1
M2 = 1 + 1/m2
P  = p3*q2 - p2*q3 - 1
```

and

```text
H = M1/2*(p1^2 + P^2/q1^2)
  + M2/2*(p2^2 + p3^2)
  + p1*p2 - p3*P/q1
  - m1/q1
  - m2/sqrt(q2^2+q3^2)
  - m1*m2/sqrt((q1-q2)^2+q3^2).
```

The nine exact terms and signs are checked against the hash-pinned original
source convention. The completed WP2 qualification supplies the separately
frozen KS/physical model boundary; it is not used to manufacture this NVE.

## R2: Parabolic Lagrange Phase Curve

Let `S1=m1+m2+1`, `S2=m1*m2+m1+m2`, and `S3=m2+2`. The equilateral curve is

```text
q1=q, q2=q/2, q3=sqrt(3)*q/2,
p1=p, p2=A*p+B/q, p3=C*p+D/q,
```

with

```text
A=m2*(1-m1)/(m1*S3)
B=-sqrt(3)*S1*m2/(S2*S3)
C=sqrt(3)*m2*(m1+1)/(m1*S3)
D=-m2*(S2+m1*m2-1)/(S2*S3).
```

At zero energy, put `w=p*q`. Direct substitution gives

```text
q(w)=-(a*w^2+b*w+d)/c, p(w)=w/q(w),
a=2*S1*S2/(m1^2*S3^2),
b=-2*sqrt(3)*m2*S1/(m1*S3^2),
c=-S2,
d=2*S1*(m2^2+m2+1)/(S3^2*S2).
```

The reference calculation first simplifies on positive radial `q`, then
substitutes `q(w)`. It verifies `H=0` and proves that all six components of
`J grad(H)` equal `dz/dw` times the same exact `dw/dt`. Thus the displayed
curve is an integral phase curve, rather than merely an energy-shell
parametrization.

## R3: Whittaker Energy-Shell Reduction

Before reducing, the reference constructs the complete planar variational
equation

```text
d(delta z)/dt = J6*H_zz(Gamma)*delta z
```

as a `6x6` exact matrix, substitutes the phase curve, and verifies its
Hamiltonian-matrix identity. This is the planar variational equation from
which the normal system is reduced.

Solve `H=0` locally for `p1` and write `K=-p1`. For
`y=(q2,q3,p2,p3)`, implicit differentiation gives

```text
K_ij = H_ij/H_p
     - H_ip*H_j/H_p^2
     - H_i*H_pj/H_p^2
     + H_i*H_pp*H_j/H_p^3,
```

where `p=p1`. The reference program differentiates `H` to construct this
Hessian, checks its symmetry, substitutes the phase curve, changes independent
variable from `q1` to `w`, and forms

```text
A_NVE = J4 * (dq/dw) * Hess_y(K).
```

It also verifies the Hamiltonian-matrix identity for this four-dimensional
normal system. The implicit energy-shell step removes the energy/flow pair and
therefore realizes the declared `6 -> 4` normal reduction.

## R4: Fuchs System

Define

```text
L = 2*S2*w - sqrt(3)*m1*m2
Z = S2^2*w^2 - sqrt(3)*m1*m2*S2*w
  + m1^2*(m2^2+m2+1)
C = diag(L*Z,L*Z,1,1).
```

With `eta=C*x`, the system matrix is

```text
A_F = C^-1*A_NVE*C - C^-1*dC/dw.
```

Exact denominator-degree accounting and local valuations prove every entry is
proper at infinity, all denominator zeros are supported on `L*Z`, and every
net finite pole is at most simple. The three distinct finite singularities are

```text
t0=sqrt(3)*m1*m2/(2*S2),
t1=m1*(sqrt(3)*m2+i*S3)/(2*S2),
t2=conjugate(t1).
```

## R5: Finite Residue Spectra

Residues are computed from the generated matrix, not entered as data. Their
characteristic polynomials are

```text
t0: lambda^2*(lambda+1)^2
t1: lambda*(lambda-1)*(lambda+1)*(lambda+2)
t2: lambda*(lambda-1)*(lambda+1)*(lambda+2).
```

## R6: Infinity Residue

The residue at infinity is minus their sum. Its characteristic polynomial is

```text
lambda^4 - 6*lambda^3 + 7*lambda^2 + 6*lambda + (27*sigma-8),
sigma=S2/S1^2.
```

One exact generic replay proves these identities over
`Q(sqrt(3),i)(m1,m2)`. Exact rational specializations are separate regression
and convention checks.

## R7: Complete Positive-Mass Domain

Before setting `m3=1`,

```text
sigma=(m1*m2+m2*m3+m3*m1)/(m1+m2+m3)^2.
```

Positivity gives `sigma>0`, and

```text
1/3-sigma =
((m1-m2)^2+(m2-m3)^2+(m3-m1)^2)
/ (6*(m1+m2+m3)^2) >= 0.
```

Equality holds exactly at equal masses. Hence every finite positive triple
has `0<sigma<=1/3`.

## R8: Non-Abelian Identity Component

The three finite residue spectra are integral. Therefore every finite local
monodromy has all eigenvalues one and is unipotent.

For this Fuchsian system over `C(w)`, the analytic monodromy matrices lie in
the differential-Galois group (indeed their Zariski closure gives the
regular-singular Galois group). Thus the following identity-component
argument takes place inside the same algebraic group used by Morales-Ramis.

Every unipotent element of a complex linear algebraic group belongs to its
identity component: the Zariski closure of its integer powers lies in the
connected one-parameter unipotent subgroup generated by its logarithm.

Assume the differential-Galois identity component `G0` were Abelian. The
three finite local monodromies would then commute. A product of commuting
unipotent matrices is unipotent. The fundamental-group relation says that the
inverse infinity monodromy is that finite product, so infinity monodromy would
also be unipotent.

The infinity residue exponents satisfy

```text
((2*lambda-3)^2-13)^2=144*(1-3*sigma).
```

If all infinity monodromy eigenvalues were one, all four exponents would be
integers. For two nested-radical roots, set
`x=2*lambda1-3` and `y=2*lambda2-3`. Then `x,y` are odd integers and
`x^2+y^2=26`. The only odd-square decomposition is `1+25`. It forces the
inner square root to be `12`, hence `sigma=0`, contradicting positive masses.
Infinity monodromy is therefore not unipotent. The contradiction proves that
`G0` is non-Abelian for every finite positive mass triple.

The first-NVE polynomial-invariant values `1/3`, `8/27`, and `2/9` do not
alter this proof. The exceptional set for the complete-integrability
obstruction is empty.

## R9: Morales-Ramis Application

The hash-pinned Morales-Ruiz-Ramis theorem gives a necessary condition for
complete meromorphic Liouville integrability: the identity component of the
variational differential Galois group must be Abelian. The normal variational
identity component just proved non-Abelian violates that condition. The
conclusion is local to the complex neighborhood of this phase curve and to the
declared reduced model.

## R10: Source Equivalence and Nonclaims

The original NVE source and this reproduction use the same reduced
Hamiltonian, Lagrange parametrization, `w=p*q`, `L`, `Z`, gauge, singular
points, finite residue spectra, mass invariant, and infinity exponent
polynomial. The independently published Boucher-Weil application agrees at
the theorem-conclusion level. PDF hashes and source-text contracts prevent
silent source substitution.

This proof does not exclude one additional integral, non-meromorphic
integrability, zero angular momentum, spatial integrability without the
separate transfer theorem, or integrability on a domain not containing the
phase-curve neighborhood. It does not rederive every canonical reduction map
from the unreduced 18-dimensional state.
