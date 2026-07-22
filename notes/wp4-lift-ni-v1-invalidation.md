# WP4-LIFT-NI-v1 Invalidation

Date: 2026-07-22

`WP4-LIFT-NI-v1` is invalidated before implementation freeze or scientific
execution. It authorizes no claim.

The locked admissibility definition required the nine upstairs covectors to
have generic rank in the ambient 18-dimensional chart. The T6 argument used
that rank at points of the physical shell `J=0, K=0`, but the specification did
not require the ambient full-rank locus to meet that shell.

The gap is real. In adapted canonical coordinates, set

```text
g=1, H=p1, K=p1+p_t,
(F1,F2,F3,F4,F5)=(p2,p3,p4,p5,I1*p6).
```

Together with `(K,p_t,I1,I2)`, these are nine commuting first integrals and
have rank nine where `I1 != 0`. On `I1=I2=K=0`, however, `F5` restricts to zero,
so the descended physical family has rank five. Gauge and clock commutation do
not prevent this off-shell-only rank.

`WP4-LIFT-NI-v2` must require ambient rank nine on a relative dense-open subset
of the physical shell. It must also reject the counterexample above and make
the planar fixed-angular-momentum quotient explicit before qualifying the
spatial variational subquotient.
