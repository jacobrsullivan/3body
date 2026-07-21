# WP3-MULTI-CAND-v2 Corrected Candidate Resolution

**Status:** KNOWN_L2_FUNCTION_EQUIVALENCE

**Qualification ID:** `WP3-MULTI-CAND-v2-RES-v2-1277d77b2a25`

## Decision

Freeze and execute a successor search that removes the full observable L^2 equivalence class before making any bounded-null claim.

- Training relative value RMS max: `9.429769811073e-13`
- Calibration relative value RMS max: `6.273148570610e-13`
- Challenge relative value RMS max: `6.830542672500e-13`
- Split scale relative spread max: `3.342786710600e-13`
- Observable backend projection min: `1.000000000000e+00`
- 80-digit candidate/L^2 relative RMS: `2.180976795578e-13`

## Frozen Gates

| Gate | Observed | Requirement | Result |
|---|---:|---:|:---:|
| `specification_lock_verified` | 1 | == 1 | PASS |
| `implementation_lock_verified` | 1 | == 1 | PASS |
| `superseded_v1_assessment_verified` | 1 | == 1 | PASS |
| `source_matrix_byte_identity` | 1 | == 1 | PASS |
| `publication_reserve_intact_before` | 1 | == 1 | PASS |
| `training_candidate_l2_relative_value_rms_max` | 9.42976981107296e-13 | <= 1e-10 | PASS |
| `calibration_candidate_l2_relative_value_rms_max` | 6.273148570610375e-13 | <= 1e-10 | PASS |
| `challenge_candidate_l2_relative_value_rms_max` | 6.830542672500359e-13 | <= 1e-10 | PASS |
| `split_scale_relative_spread_max` | 3.342786710599983e-13 | <= 1e-10 | PASS |
| `held_scale_lie_rms_max` | 7.147049727768985e-10 | <= 1e-09 | PASS |
| `held_scale_lie_abs_max` | 7.2562265479419374e-09 | <= 1e-07 | PASS |
| `backend_centered_response_projection_min` | 0.9999999999999998 | >= 0.999999999 | PASS |
| `backend_l2_relative_value_rms_max` | 9.42976981107296e-13 | <= 1e-09 | PASS |
| `production_physical_l2_relative_difference_max` | 1.0547118733938987e-14 | <= 1e-12 | PASS |
| `mpmath_feature_physical_l2_relative_difference_max` | 8.433758354584419e-80 | <= 1e-10 | PASS |
| `mpmath_candidate_l2_relative_value_rms_max` | 2.180976795577622e-13 | <= 1e-10 | PASS |

## Claim Boundary

A KNOWN_L2_FUNCTION_EQUIVALENCE result establishes only that the frozen numerical candidate and replicated rank-one directions evaluate as scalar multiples of the already known L^2 observable over the declared source and challenge domains. It does not prove a global symbolic coefficient identity, discover a new invariant, authorize publication-reserve access, or convert the original search into a bounded-null result. It requires a separately locked successor search that removes the observable L^2 equivalence class. An UNRESOLVED result preserves the original search as spectrally unresolved.

## Integrity

- Evidence commit: `3c082ba10c9ca49c9641b61fdac099cd19ffa0cc`
- Resolution lock: `1dfea7f42701b78e4ac5dfb871edef844b2b11bf105f7db941cfcf9a90448e8a`
- Results SHA-256: `aa2468f4947a8f2f40e14564bfd1f80673503b6bc0f219e219f063ce718ce62c`
- Record payload SHA-256: `71134308e2bafdaa0f74302d6029d8c0c3e6d625202793a34f759e374bd0d23e`
- Publication reserve: **SEALED_UNEXECUTED**
