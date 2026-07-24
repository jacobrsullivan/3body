# WP6-COMMON-v1 result

Date: 2026-07-24

## Decision

`WP6-COMMON-v1-502728e5b811` is qualified with status `PASS`.

The campaign adds the following authorized claim:

> For arbitrary finite positive masses and every finite real planar
> three-body common level `(H,C)=(h,c)` with `(h,c)!=(0,0)`, the pinned
> Maciejewski-Przybylska-Combot theorem, with the project-owned exact
> audit, proves failure of rational integrability in the theorem's
> restricted-integrability sense.

The proof is direct on each common level and uses Euler-Moulton collinear
homographic witnesses. It is not inferred from the unreduced
`WP6-FI1-v1` one-integral result.

## External authority and project contribution

The theorem is externally established work, now published in the
*Journal of the European Mathematical Society* as
[DOI 10.4171/JEMS/1717](https://doi.org/10.4171/JEMS/1717). The campaign
is reproducibly pinned to
[arXiv 2502.01426v2](https://arxiv.org/abs/2502.01426), SHA-256
`54aa7075cbfcdaf3cd8b559ccdfc1067e1ce87e9839c8d089ba3757df57debeb`.

The project does not claim to have discovered or independently reproved
the universal differential-Galois theorem. Its contribution is a
fail-closed qualification that:

- pins the source and predecessor evidence by content;
- audits the exhaustive common-level proof branches;
- derives the Kepler relation independently;
- reproduces the exact equal-mass Euler-Moulton spectrum;
- audits the generic and circular block discriminants;
- matches representative scalar NVE coefficients against a
  source-disjoint SymPy implementation;
- rejects every declared claim extension.

## Proof branches

| Common level | Witness | Authority |
| --- | --- | --- |
| `c=0,h!=0` | Euler-Moulton homothetic | Qualified `WP6-L0-v1` predecessor |
| `c!=0,2*h*c^2!=-mu^2` | Euler-Moulton noncircular homographic | Source Lemma 5.1 |
| `c!=0,2*h*c^2=-mu^2` | Complex Euler-Moulton homographic | Source Lemma 5.3 |
| `(h,c)=(0,0)` | None qualified | Explicitly excluded |

The circular branch must not use the real circular orbit: its variational
equation has constant coefficients and yields no obstruction. The
published proof uses a complex homographic solution on the complexified
level.

## Exact audit

For equal masses at positions `(-1,0,1)`, the campaign independently
reproduces:

- central multiplier `mu=5/4`;
- Euler matrix spectrum `{0,1,12/5}`;
- physical parameter `delta=7/5`;
- generic benchmark `Delta=1186/25` at `e=1`;
- circular benchmark `Delta^2=816/25`.

Production uses exact Python `Fraction` arithmetic. The independent
reference derives the conic relation and Euler spectrum in SymPy without
production imports.

Qualification results:

- source payloads: `2/2` verified;
- predecessor qualifications: `3/3` verified;
- deterministic benchmarks: `6/6` pass;
- theorem obligations: `10/10` pass;
- adversarial controls: `13/13` pass;
- production/reference agreement: exact PASS;
- frozen files: `23/23` verified.

## Significance for domains outside Lagrange

This closes the strongest feasible generic planar "outside Lagrange"
track. The witness is Euler-Moulton, so the conclusion no longer depends
only on a Lagrange neighborhood. It also extends the earlier
zero-angular-momentum result to every non-double-zero
energy-angular-momentum common level.

The quantifier is nevertheless a common-level integrability quantifier.
A variational obstruction along one Euler-Moulton phase curve rules out a
complete rational commuting family on that common level. It does not show
that every point or every open subset outside the Lagrange neighborhood is
individually nonintegrable, chaotic, or free of all first integrals.

Accordingly, this result does not invalidate local, individual,
non-rational, or approximate invariant candidates produced by WP3. Those
candidates remain subject to their own publication gates.

## Remaining boundaries

The campaign does not prove:

- rational nonintegrability on `(H,C)=(0,0)`;
- absence of one additional first integral on every fixed common level;
- a spatial common-level theorem;
- absence of meromorphic, analytic, smooth, or other non-rational
  integrability structures;
- pointwise nonintegrability on every open non-Lagrange domain;
- collision-regularized continuation;
- a regular SO(3) chart through the collinear witness.

The completed WP5 publication chain remains unchanged. WP6-COMMON-v1 is
separate successor evidence and must not be retroactively inserted into a
frozen manuscript or qualification record.

## Next research priorities

The generic planar non-Lagrange question should no longer be pursued as an
open-ended orbit search. Remaining work should name a narrower unresolved
claim:

1. the doubly-zero planar common level, which still lacks a qualified
   explicit witness;
2. absence of one additional integral defined only on a fixed common
   level;
3. a spatial fixed-common-level nonintegrability theorem;
4. local domain-specific results near figure-eight, hierarchical, or other
   non-Lagrange dynamics.

These are mathematically distinct projects and require separate locked
specifications.

## Integrity and regression

- Qualification lock:
  `835cbe6631d20345a5274be8546c8125ec5ee4c58ed5fa30b7d6816dfcf6fb5c`
- Evidence commit:
  `9b689fa22b8dc7a284547d2d9734053d2af13394`
- Result SHA-256:
  `f9ba90dc61716fa5c40cc99b426c332a8e41a54565a00b8d4d3f58868acd18ff`
- Record payload SHA-256:
  `35d26fe23c008e214efd3dad74db471ba45b52782342a05181f83ae72579a630`
- Focused tests: `35 passed`
- Pinned Python 3.11 fast lane: `1237 passed`, `2 skipped`,
  `134 deselected`, `19 warnings`
- Slow simulations remain isolated in the existing slow lane.
