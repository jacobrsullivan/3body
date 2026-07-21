#!/usr/bin/env python
"""Execute the frozen WP3-MULTI-CAND-v2 rank-one resolution protocol."""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
from pathlib import Path
import sys
from typing import Any, Sequence

import mpmath
import numpy as np
from numpy.typing import NDArray
from scipy import linalg


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
CAMPAIGN_ROOT = VALIDATION_ROOT / "wp3-multi-candidate-v2-resolution"
SOURCE_ROOT = VALIDATION_ROOT / "wp3-multi-candidate-v2"
V1_ROOT = VALIDATION_ROOT / "wp3-multi-candidate-v1"
SPATIAL_ROOT = VALIDATION_ROOT / "wp3-spatial-validation-v2"
WP1_ROOT = VALIDATION_ROOT / "wp1-catalogue-n3bp-validation"
for path in (REPO_ROOT, VALIDATION_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from qualification_tools import (  # noqa: E402
    atomic_write_json,
    load_json,
    make_gate,
    runtime_fingerprint,
    sha256_file,
    utc_now,
    verify_lock,
)
from validation_external_import import campaign_module  # noqa: E402
from src.python.n3bp_qualification import (  # noqa: E402
    InertialState,
    SystemParameters,
    newtonian_rhs,
    total_energy,
)
from src.python.wp3_exploration_v3.search import balanced_row_weights  # noqa: E402
from src.python.wp3_multi_v2 import (  # noqa: E402
    angular_momentum_squared_coefficients,
    evaluate_multi_features,
    feature_names,
    structural_zero_feature_indices,
)


FloatArray = NDArray[np.float64]


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--challenge-corpus", required=True)
    parser.add_argument("--lock", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def _load_common():
    return campaign_module(
        CAMPAIGN_ROOT / "scripts/campaign_common.py",
        "_wp3_multi_v2_resolution_common_run",
    )


def _load_source_runner():
    return campaign_module(
        SOURCE_ROOT / "scripts/run_search.py",
        "_wp3_multi_v2_resolution_source_runner",
    )


def _load_reference():
    return campaign_module(
        CAMPAIGN_ROOT / "reference/mpmath_features.py",
        "_wp3_multi_v2_resolution_mpmath_reference",
    )


def _matrix_sha256(matrix: FloatArray) -> str:
    contiguous = np.ascontiguousarray(matrix, dtype="<f8")
    digest = hashlib.sha256(str(contiguous.shape).encode("ascii"))
    digest.update(contiguous.tobytes())
    return digest.hexdigest()


def _svd(
    matrix: FloatArray,
    *,
    driver: str,
    full_matrices: bool,
) -> tuple[FloatArray, FloatArray, FloatArray]:
    if driver == "numpy":
        return np.linalg.svd(matrix, full_matrices=full_matrices)
    return linalg.svd(
        matrix,
        full_matrices=full_matrices,
        lapack_driver=driver,
        check_finite=True,
    )


def _rank(singular: FloatArray, relative_tolerance: float) -> int:
    if not singular.size or singular[0] == 0.0:
        return 0
    return int(np.count_nonzero(singular > singular[0] * relative_tolerance))


def generalized_direction(
    values: FloatArray,
    derivatives: FloatArray,
    group_ids: Sequence[str],
    family_ids: Sequence[str],
    known_coefficients: FloatArray,
    *,
    driver: str,
    value_rank_relative_tolerance: float,
) -> dict[str, Any]:
    """Independently reconstruct the smallest generalized direction."""

    weights = balanced_row_weights(group_ids, family_ids)
    scales = np.sqrt(np.sum(weights[:, None] * np.square(values), axis=0))
    if np.any(scales <= 1e-14):
        raise RuntimeError("active resolution matrix has an unobservable column")
    known_normalized = scales * known_coefficients
    known_basis = known_normalized / np.linalg.norm(known_normalized)
    complement = linalg.null_space(known_basis[None, :], rcond=1e-12)
    normalized_values = values / scales
    normalized_derivatives = derivatives / scales
    mean = np.sum(weights[:, None] * normalized_values, axis=0)
    value_operator = np.sqrt(weights)[:, None] * (
        (normalized_values - mean) @ complement
    )
    derivative_operator = np.sqrt(weights)[:, None] * (
        normalized_derivatives @ complement
    )
    _, value_singular, value_right = _svd(
        value_operator, driver=driver, full_matrices=True
    )
    value_rank = _rank(value_singular, value_rank_relative_tolerance)
    if value_rank == 0:
        raise RuntimeError("resolution value operator has zero rank")
    active = value_right[:value_rank].T
    nuisance = value_right[value_rank:].T
    active_derivative = derivative_operator @ active
    nuisance_derivative = derivative_operator @ nuisance
    nuisance_rank = 0
    nuisance_left = np.empty((values.shape[0], 0))
    nuisance_singular = np.empty(0)
    nuisance_right = np.empty((0, 0))
    residual_derivative = active_derivative
    if nuisance_derivative.shape[1]:
        nuisance_left, nuisance_singular, nuisance_right = _svd(
            nuisance_derivative, driver=driver, full_matrices=False
        )
        nuisance_rank = _rank(nuisance_singular, 1e-12)
        basis = nuisance_left[:, :nuisance_rank]
        residual_derivative = active_derivative - basis @ (basis.T @ active_derivative)
    generalized_operator = residual_derivative / value_singular[:value_rank]
    _, generalized_singular, generalized_right = _svd(
        generalized_operator, driver=driver, full_matrices=False
    )
    selected = int(np.argmin(generalized_singular))
    observable_coordinates = generalized_right[selected] / value_singular[:value_rank]
    nuisance_coordinates = np.zeros(nuisance.shape[1], dtype=np.float64)
    if nuisance_rank:
        target = active_derivative @ observable_coordinates
        nuisance_coordinates = -nuisance_right[:nuisance_rank].T @ (
            (nuisance_left[:, :nuisance_rank].T @ target)
            / nuisance_singular[:nuisance_rank]
        )
    quotient_coordinates = (
        active @ observable_coordinates + nuisance @ nuisance_coordinates
    )
    normalized = complement @ quotient_coordinates
    raw = normalized / scales
    projected = values @ raw
    value_mean = float(np.sum(weights * projected))
    value_std = float(np.sqrt(np.sum(weights * np.square(projected - value_mean))))
    raw /= value_std
    normalized = scales * raw
    dominant = int(np.argmax(np.abs(normalized)))
    if normalized[dominant] < 0.0:
        raw = -raw
        normalized = -normalized
    return {
        "driver": driver,
        "generalized_singular_value": float(generalized_singular[selected]),
        "value_rank": value_rank,
        "value_nuisance_nullity": int(nuisance.shape[1]),
        "value_nuisance_derivative_rank": nuisance_rank,
        "raw_coefficients": raw,
        "normalized_coefficients": normalized,
    }


def _subspace_projection(first: FloatArray, second: FloatArray) -> float:
    return abs(float(np.dot(first, second))) / (
        float(np.linalg.norm(first)) * float(np.linalg.norm(second))
    )


def _rebuild_source_rows(spec: dict[str, Any]) -> tuple[Any, Any]:
    runner = _load_source_runner()
    source_spec = load_json(SOURCE_ROOT / "search_spec.json")
    corpus = load_json(V1_ROOT / "data/search_corpus.json")
    spatial_corpus = load_json(SPATIAL_ROOT / "data/qualification_corpus.json")
    definitions = {case["case_id"]: case for case in spatial_corpus["cases"]}
    development_results = {
        case["case_id"]: case
        for case in load_json(SPATIAL_ROOT / "results/development.json")["cases"]
    }
    calibration_results = {
        case["case_id"]: case
        for case in load_json(SPATIAL_ROOT / "results/calibration.json")["cases"]
    }
    catalogue = load_json(WP1_ROOT / "data/native_catalogue.json")
    wp1_candidates = {
        candidate["candidate_id"]: candidate for candidate in catalogue["candidates"]
    }
    if (
        sha256_file(V1_ROOT / "data/search_corpus.json")
        != spec["prerequisites"]["v1_search_corpus_sha256"]
    ):
        raise RuntimeError("candidate resolution source corpus changed")
    return (
        runner._build_rows(
            "development",
            source_spec,
            corpus,
            spatial_definitions=definitions,
            spatial_results=development_results,
            wp1_candidates=wp1_candidates,
        ),
        runner._build_rows(
            "calibration",
            source_spec,
            corpus,
            spatial_definitions=definitions,
            spatial_results=calibration_results,
            wp1_candidates=wp1_candidates,
        ),
    )


def _fraction(value: str) -> float:
    return float(Fraction(value))


def _challenge_production(case: dict[str, Any]) -> tuple[FloatArray, FloatArray]:
    positions = np.asarray(
        [[_fraction(value) for value in row] for row in case["positions"]],
        dtype=np.float64,
    )
    velocities = np.asarray(
        [[_fraction(value) for value in row] for row in case["velocities"]],
        dtype=np.float64,
    )
    masses = [_fraction(value) for value in case["masses"]]
    state = InertialState.from_components(positions, velocities)
    parameters = SystemParameters(masses)
    clock = float(
        np.prod(
            [
                np.linalg.norm(positions[first] - positions[second])
                for first, second in ((0, 1), (1, 2), (2, 0))
            ]
        )
    )
    tangent = clock * newtonian_rhs(0.0, state, parameters)
    evaluation = evaluate_multi_features(
        state,
        tangent,
        parameters,
        fixed_energy=total_energy(state, parameters),
    )
    return evaluation.values, evaluation.derivatives


def _direction_metrics(
    values: FloatArray,
    derivatives: FloatArray,
    coefficients: FloatArray,
    splits: Sequence[str],
) -> dict[str, Any]:
    projected_values = values @ coefficients
    projected_derivatives = derivatives @ coefficients
    output: dict[str, Any] = {}
    for split in ("development_challenge", "calibration_challenge"):
        mask = np.asarray([value == split for value in splits], dtype=bool)
        centered = projected_values[mask] - np.mean(projected_values[mask])
        output[split] = {
            "value_std": float(np.sqrt(np.mean(np.square(centered)))),
            "lie_rms": float(np.sqrt(np.mean(np.square(projected_derivatives[mask])))),
            "lie_abs_max": float(np.max(np.abs(projected_derivatives[mask]))),
        }
    return output


def _rational_reconstruction(
    coefficients: FloatArray,
    names: Sequence[str],
    *,
    max_denominator: int,
) -> dict[str, Any]:
    dominant = float(np.max(np.abs(coefficients)))
    normalized = coefficients / dominant
    reconstructed = np.zeros_like(normalized)
    terms = []
    for index, value in enumerate(normalized):
        if abs(float(value)) <= 1e-10:
            rational = Fraction(0)
        else:
            rational = Fraction(float(value)).limit_denominator(max_denominator)
        reconstructed[index] = float(rational)
        if rational:
            terms.append(
                {
                    "feature": str(names[index]),
                    "coefficient": str(rational),
                }
            )
    return {
        "dominant_coefficient_scale": dominant,
        "normalized_coefficient_residual_max": float(
            np.max(np.abs(normalized - reconstructed))
        ),
        "nonzero_term_count": len(terms),
        "maximum_denominator": max(
            (Fraction(term["coefficient"]).denominator for term in terms),
            default=1,
        ),
        "terms": terms,
        "reconstructed_normalized_coefficients": reconstructed,
    }


def decide_resolution(
    *,
    numeric_gates_pass: bool,
    known_direction: bool,
    formula_resolved: bool,
) -> str:
    if not numeric_gates_pass:
        return "REJECTED_NUMERICAL_OR_GENERALIZATION_ARTIFACT"
    if known_direction:
        return "EXACT_KNOWN_DIRECTION"
    if formula_resolved:
        return "SURVIVES_RESOLUTION"
    return "SURVIVES_NUMERICALLY_FORMULA_UNRESOLVED"


def main() -> None:
    args = _args()
    destination = Path(args.output)
    if destination.exists():
        raise RuntimeError("refusing to overwrite one-shot resolution output")
    common = _load_common()
    reference = _load_reference()
    spec = load_json(args.spec)
    challenge = load_json(args.challenge_corpus)
    specification_lock = common.verify_specification_lock(args.spec)
    candidate_metadata = common.verify_candidate_metadata(spec)
    reserve_before = common.verify_publication_reserve(
        spec["prerequisites"]["sealed_publication_reserve_sha256"]
    )
    lock = verify_lock(args.lock, REPO_ROOT, expected_prefix=spec["campaign"])
    if (
        lock.get("spec_sha256") != sha256_file(args.spec)
        or lock.get("challenge_corpus_sha256") != sha256_file(args.challenge_corpus)
        or lock.get("specification_lock_sha256")
        != specification_lock["specification_lock_sha256"]
        or lock.get("candidate_expression_interpreted_before_implementation_lock")
        is not False
    ):
        raise RuntimeError("resolution lock does not bind the frozen implementation")
    expected_challenge_count = int(
        spec["challenge_corpus"]["development_challenge_count"]
    ) + int(spec["challenge_corpus"]["calibration_challenge_count"])
    if (
        challenge.get("campaign") != spec["campaign"]
        or challenge.get("spec_sha256") != sha256_file(args.spec)
        or challenge.get("specification_lock_sha256")
        != specification_lock["specification_lock_sha256"]
        or len(challenge.get("cases", [])) != expected_challenge_count
        or challenge.get("publication_reserve_used") is not False
    ):
        raise RuntimeError("challenge corpus does not match the resolution contract")

    source_results = load_json(SOURCE_ROOT / "results/search_results.json")
    source_search = source_results["search"]
    candidate_rank = int(candidate_metadata["mode_rank"])
    mode = next(
        item for item in source_search["modes"] if int(item["rank"]) == candidate_rank
    )
    committed_full = np.asarray(mode["coefficients"], dtype=np.float64)
    if committed_full.shape != (285,):
        raise RuntimeError("committed candidate coefficient vector has wrong length")
    zero_indices = np.asarray(structural_zero_feature_indices(), dtype=np.int64)
    active_mask = np.ones(285, dtype=bool)
    active_mask[zero_indices] = False
    active_indices = np.flatnonzero(active_mask)
    if np.any(committed_full[zero_indices] != 0.0):
        raise RuntimeError("committed candidate uses exact-zero Reynolds columns")

    training, calibration = _rebuild_source_rows(spec)
    expected_hashes = source_results["matrix_hashes"]
    rebuilt_hashes = {
        "training_values_full": _matrix_sha256(training.values),
        "training_derivatives_full": _matrix_sha256(training.derivatives),
        "calibration_values_full": _matrix_sha256(calibration.values),
        "calibration_derivatives_full": _matrix_sha256(calibration.derivatives),
    }
    matrix_identity = rebuilt_hashes == expected_hashes
    if not matrix_identity:
        raise RuntimeError(
            "resolution could not byte-rebuild the frozen source matrices"
        )
    active_values = training.values[:, active_indices]
    active_derivatives = training.derivatives[:, active_indices]
    known_active = angular_momentum_squared_coefficients()[active_indices]
    source_search_spec = load_json(SOURCE_ROOT / "search_spec.json")["search"]
    replications = [
        generalized_direction(
            active_values,
            active_derivatives,
            training.group_ids,
            training.family_ids,
            known_active,
            driver=driver,
            value_rank_relative_tolerance=float(
                source_search_spec["value_rank_relative_tolerance"]
            ),
        )
        for driver in ("numpy", "gesdd", "gesvd")
    ]
    training_weights = balanced_row_weights(training.group_ids, training.family_ids)
    feature_scales = np.sqrt(
        np.sum(training_weights[:, None] * np.square(active_values), axis=0)
    )
    committed_active_normalized = feature_scales * committed_full[active_indices]
    backend_summaries = []
    full_directions = {"committed": committed_full}
    for replication in replications:
        full = np.zeros(285, dtype=np.float64)
        full[active_indices] = replication["raw_coefficients"]
        full_directions[str(replication["driver"])] = full
        backend_summaries.append(
            {
                "driver": replication["driver"],
                "generalized_singular_value": replication["generalized_singular_value"],
                "value_rank": replication["value_rank"],
                "value_nuisance_nullity": replication["value_nuisance_nullity"],
                "value_nuisance_derivative_rank": replication[
                    "value_nuisance_derivative_rank"
                ],
                "committed_subspace_projection": _subspace_projection(
                    committed_active_normalized,
                    replication["normalized_coefficients"],
                ),
            }
        )
    backend_projection_min = min(
        item["committed_subspace_projection"] for item in backend_summaries
    )
    backend_singular = [
        float(item["generalized_singular_value"]) for item in backend_summaries
    ]
    backend_singular_relative_spread = (
        max(backend_singular) - min(backend_singular)
    ) / max(max(backend_singular), np.finfo(float).tiny)

    production_values = []
    production_derivatives = []
    reference_values = []
    reference_derivatives = []
    splits = []
    for case in challenge["cases"]:
        values, derivatives = _challenge_production(case)
        high_values, high_derivatives = reference.evaluate(case, dps=80)
        production_values.append(values)
        production_derivatives.append(derivatives)
        reference_values.append(high_values)
        reference_derivatives.append(high_derivatives)
        splits.append(case["split"])
    challenge_values = np.stack(production_values)
    challenge_derivatives = np.stack(production_derivatives)
    direction_metrics = {
        name: _direction_metrics(
            challenge_values, challenge_derivatives, coefficients, splits
        )
        for name, coefficients in full_directions.items()
    }
    committed_production_values = challenge_values @ committed_full
    committed_production_derivatives = challenge_derivatives @ committed_full
    precision_value_difference = 0.0
    precision_lie_difference = 0.0
    with mpmath.workdps(80):
        coefficient_mp = [mpmath.mpf(float(value)) for value in committed_full]
        for index in range(len(challenge["cases"])):
            high_value = mpmath.fsum(
                coefficient * value
                for coefficient, value in zip(
                    coefficient_mp, reference_values[index], strict=True
                )
            )
            high_lie = mpmath.fsum(
                coefficient * value
                for coefficient, value in zip(
                    coefficient_mp, reference_derivatives[index], strict=True
                )
            )
            precision_value_difference = max(
                precision_value_difference,
                abs(float(high_value) - committed_production_values[index])
                / max(1.0, abs(float(high_value))),
            )
            precision_lie_difference = max(
                precision_lie_difference,
                abs(float(high_lie) - committed_production_derivatives[index])
                / max(1.0, abs(float(high_lie))),
            )

    thresholds = spec["thresholds"]
    challenge_value_std_min = min(
        metrics[split]["value_std"]
        for metrics in direction_metrics.values()
        for split in ("development_challenge", "calibration_challenge")
    )
    challenge_lie_rms_max = max(
        metrics[split]["lie_rms"]
        for metrics in direction_metrics.values()
        for split in ("development_challenge", "calibration_challenge")
    )
    challenge_lie_abs_max = max(
        metrics[split]["lie_abs_max"]
        for metrics in direction_metrics.values()
        for split in ("development_challenge", "calibration_challenge")
    )
    formula = _rational_reconstruction(
        committed_full,
        feature_names(),
        max_denominator=int(thresholds["rational_reconstruction_max_denominator"]),
    )
    known = angular_momentum_squared_coefficients()
    known_scale = float(np.dot(committed_full, known) / np.dot(known, known))
    known_residual = float(
        np.linalg.norm(committed_full - known_scale * known)
        / np.linalg.norm(committed_full)
    )
    gates = [
        make_gate("specification_lock_verified", 1, "==", 1),
        make_gate("implementation_lock_verified", 1, "==", 1),
        make_gate("candidate_metadata_verified", 1, "==", 1),
        make_gate("source_matrix_byte_identity", int(matrix_identity), "==", 1),
        make_gate(
            "publication_reserve_intact_before",
            int(reserve_before["status"] == "SEALED_UNEXECUTED"),
            "==",
            1,
        ),
        make_gate(
            "existing_basis_direction_passes_all_diagnostics",
            int(bool(mode["basis_direction_passes_all_diagnostic_gates"])),
            "==",
            1,
        ),
        make_gate(
            "backend_rank_one_subspace_projection_min",
            backend_projection_min,
            ">=",
            float(thresholds["backend_rank_one_subspace_projection_min"]),
        ),
        make_gate(
            "backend_generalized_singular_relative_spread",
            backend_singular_relative_spread,
            "<=",
            float(thresholds["backend_generalized_singular_relative_spread_max"]),
        ),
        make_gate(
            "challenge_weighted_value_std_min",
            challenge_value_std_min,
            ">=",
            float(thresholds["challenge_weighted_value_std_min"]),
        ),
        make_gate(
            "challenge_lie_rms_max",
            challenge_lie_rms_max,
            "<=",
            float(thresholds["challenge_lie_rms_max"]),
        ),
        make_gate(
            "challenge_lie_abs_max",
            challenge_lie_abs_max,
            "<=",
            float(thresholds["challenge_lie_abs_max"]),
        ),
        make_gate(
            "production_mpmath_value_relative_difference_max",
            precision_value_difference,
            "<=",
            float(thresholds["production_mpmath_value_relative_difference_max"]),
        ),
        make_gate(
            "production_mpmath_lie_relative_difference_max",
            precision_lie_difference,
            "<=",
            float(thresholds["production_mpmath_lie_relative_difference_max"]),
        ),
    ]
    numeric_gates_pass = all(gate["passed"] for gate in gates)
    formula_resolved = bool(
        formula["normalized_coefficient_residual_max"]
        <= float(
            thresholds["rational_reconstruction_normalized_coefficient_residual_max"]
        )
        and challenge_lie_rms_max <= float(thresholds["challenge_lie_rms_max"])
    )
    known_direction = known_residual <= float(
        thresholds["known_direction_projection_residual_max"]
    )
    decision = decide_resolution(
        numeric_gates_pass=numeric_gates_pass,
        known_direction=known_direction,
        formula_resolved=formula_resolved,
    )
    reserve_after = common.verify_publication_reserve(
        spec["prerequisites"]["sealed_publication_reserve_sha256"]
    )
    payload = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "status": decision,
        "generated_utc": utc_now(),
        "qualification_id": lock["qualification_id"],
        "lock_sha256": lock["lock_sha256"],
        "spec_sha256": sha256_file(args.spec),
        "specification_lock_sha256": specification_lock["specification_lock_sha256"],
        "challenge_corpus_sha256": sha256_file(args.challenge_corpus),
        "runtime": runtime_fingerprint(),
        "candidate_metadata": candidate_metadata,
        "candidate_expression_access": {
            "accessed_after_specification_lock": True,
            "interpreted_after_implementation_lock": True,
            "mode_rank": candidate_rank,
            "committed_top_terms": mode.get("top_terms", []),
        },
        "source_matrix_hashes": rebuilt_hashes,
        "backend_replication": {
            "summaries": backend_summaries,
            "subspace_projection_min": backend_projection_min,
            "generalized_singular_relative_spread": backend_singular_relative_spread,
        },
        "challenge_summary": {
            "case_count": len(challenge["cases"]),
            "development_count": challenge["development_challenge_count"],
            "calibration_count": challenge["calibration_challenge_count"],
            "spatial_count": challenge["spatial_case_count"],
            "planar_count": challenge["planar_case_count"],
            "direction_metrics": direction_metrics,
            "value_std_min": challenge_value_std_min,
            "lie_rms_max": challenge_lie_rms_max,
            "lie_abs_max": challenge_lie_abs_max,
        },
        "independent_precision": {
            "implementation": "source-disjoint mpmath feature evaluator",
            "decimal_digits": 80,
            "reference_sha256": sha256_file(
                CAMPAIGN_ROOT / "reference/mpmath_features.py"
            ),
            "production_import_absent": "src.python.wp3_multi_v2"
            not in (CAMPAIGN_ROOT / "reference/mpmath_features.py").read_text(),
            "value_relative_difference_max": precision_value_difference,
            "lie_relative_difference_max": precision_lie_difference,
        },
        "formula_resolution": {
            key: value
            for key, value in formula.items()
            if key != "reconstructed_normalized_coefficients"
        },
        "known_direction_test": {
            "angular_momentum_squared_projection_scale": known_scale,
            "coefficient_projection_residual": known_residual,
            "identified_as_known": known_direction,
        },
        "gates": gates,
        "numeric_gates_pass": numeric_gates_pass,
        "formula_resolved": formula_resolved,
        "decision": decision,
        "claim_boundary": spec["evidence_boundary"],
        "publication_reserve_before": reserve_before,
        "publication_reserve_after": reserve_after,
        "publication_reserve_accessed": False,
        "next_action": {
            "REJECTED_NUMERICAL_OR_GENERALIZATION_ARTIFACT": "Do not promote the direction; preserve the original search as spectrally unresolved and the reserve as sealed.",
            "EXACT_KNOWN_DIRECTION": "Freeze a successor search with the enlarged exact known module.",
            "SURVIVES_RESOLUTION": "Freeze a candidate-specific qualification specification before reserve access.",
            "SURVIVES_NUMERICALLY_FORMULA_UNRESOLVED": "Continue unsealed formula resolution under another lock.",
        }[decision],
    }
    atomic_write_json(destination, payload)
    print(
        f"{spec['campaign']}: {decision}; "
        f"backend_projection_min={backend_projection_min:.6f}; "
        f"challenge_lie_rms_max={challenge_lie_rms_max:.6e}; "
        "reserve=SEALED_UNEXECUTED"
    )


if __name__ == "__main__":
    main()
