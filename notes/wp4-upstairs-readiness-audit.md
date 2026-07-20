# WP4 Upstairs Readiness Audit

## Existing code inspected

- `src/python/validation/poisson_brackets.py`
- `src/python/validation/independence_tester.py`
- `src/python/validation/conservation_validator.py`
- `src/python/validation/morales_ramis_validator.py`
- `src/python/upstairs_ks/model.py`
- the `WP2-UPQ-v2` qualification record and lock
- the `WP3-UP-CAND-v1` staged gate and bounded-null report

The older WP4 utilities mix symbolic and random numerical paths and are not
bound to the qualified 14-dimensional upstairs model. The readiness campaign
therefore owns a small deterministic implementation: five-point gradients,
the canonical 14-dimensional Poisson tensor, SVD rank tests, explicit S1
generator checks, and bounded DOP853 integrations.

## Frozen controls

Positive controls are `K_h`, `Xi`, and the three physical angular momentum
components. The nonconserved control is upstairs coordinate `q0`. The
dependent control is `2 K_h - 3 Xi`, which is conserved but cannot increase
the rank of the known set.

Six collision-free physical states are lifted to `K_h = Xi = 0`, covering
equal masses and two unequal-mass triples with multiple gauges. This is a
deterministic readiness corpus, not an external scientific holdout.

## Trigger boundary

`WP3-UP-CAND-v1` has zero candidates. The harness must not fabricate one,
must not inspect the reserve, and must record candidate qualification and
Morales-Ramis as not triggered regardless of the control result.
