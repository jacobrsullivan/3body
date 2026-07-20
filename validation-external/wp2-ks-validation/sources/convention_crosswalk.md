# WP2KSQ-v1 Convention Crosswalk

The campaign fixes the van der Meer/Hopf sign convention encoded in
`qualification_spec.json`. The second Cartesian component is
`2*(u1*u4-u2*u3)`, the common-phase generator is
`(-u2,u1,-u4,u3)`, and the momentum map is its canonical pairing with
`p_u`. The canonical cotangent inverse has denominator `4*|u|^2`.

The validation analytic solver uses Cartesian velocity and gravitational
parameter `mu=kappa/reduced_mass`. Before lifting, velocity is converted to
canonical momentum `p=reduced_mass*v`. REBOUND independently propagates the
same Cartesian acceleration `x''=-mu*x/|x|^3`; projected KS momentum is divided
by the reduced mass before checkpoint comparison.

The Sundman convention is `dt/ds=|u|^2`. On fixed physical energy `E<0`, the
regular Hamiltonian is

```text
K_E=|p_u|^2/(8*reduced_mass)-kappa-E*|u|^2.
```

Only `K_E=0` and `Xi=0` are qualified. A norm identity is not treated as a
constraint, and a nonzero Xi level is outside this campaign.
