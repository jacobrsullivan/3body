# WP3-MULTI-CAND-v2 Qualification Boundary

This module implements only the 285-column physical-quotient library frozen in
`validation-external/wp3-multi-candidate-v2/search_spec.json`. Each feature is
the six-body-permutation Reynolds average of a declared Gram numerator divided
by one of the three declared global denominators. Inputs must lie on the
zero-total-momentum translation quotient and away from collisions.

The Reynolds projection creates 36 exact zero columns. Twenty-four are the
degree-one `X1.W2` and `X2.W1` numerators, with zero or one symmetric parameter
factor, under each denominator. Twelve more are the quadratic orbits
`X1.X1*X1.W2`, `X1.W2*W2.W2`, `X2.X2*X2.W1`, and `X2.W1*W1.W1` under each
denominator. They remain part of the frozen 285-column declaration and are
removed as exact coefficient-space identities before numerical SVD. This
leaves 249 nonzero input columns; further value dependencies are handled by the
qualified generalized Lie/value quotient.

The represented known module contains only total angular momentum squared.
Energy is checked independently and is not claimed to be represented exactly
by this grammar. Passing a search cannot establish general non-integrability,
exclude integrals outside the frozen rational library, or authorize candidate
interpretation before the campaign publication gate.
