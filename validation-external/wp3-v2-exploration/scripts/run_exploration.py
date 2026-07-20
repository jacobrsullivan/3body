#!/usr/bin/env python
"""Run the qualification-gated WP3 v2 development/calibration search."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys
from typing import Any

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
for path in (REPO_ROOT, VALIDATION_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from qualification_tools import (  # noqa: E402
    atomic_write_json,
    canonical_json,
    load_json,
    make_gate,
    runtime_fingerprint,
    sha256_bytes,
    sha256_file,
    utc_now,
    verify_lock,
)
from src.python.n3bp_qualification import InertialState, SystemParameters  # noqa: E402
from src.python.wp3_exploration_v2 import (  # noqa: E402
    evaluate_feature_library,
    feature_names,
    known_algebra_coefficients,
    nondimensionalize,
    search_near_null_modes,
)


SPATIAL_ROOT = VALIDATION_ROOT / "wp3-spatial-validation-v2"
FLOW_ROOT = VALIDATION_ROOT / "wp2-threebody-flow-validation"
SPATIAL_LOCK = SPATIAL_ROOT / "reports/wp3_spatial_v2_qualification_lock.json"
SPATIAL_RECORD = SPATIAL_ROOT / "reports/wp3_spatial_v2_qualification_record.json"
FLOW_LOCK = FLOW_ROOT / "reports/wp2_threebody_flow_qualification_lock.json"
FLOW_RECORD = FLOW_ROOT / "reports/wp2_threebody_flow_qualification_record.json"


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--spatial-corpus", required=True)
    parser.add_argument("--spatial-development", required=True)
    parser.add_argument("--spatial-calibration", required=True)
    parser.add_argument("--commitments", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--gate-output", required=True)
    return parser.parse_args()


def _verify_prerequisite(
    expected: dict[str, str],
    lock_path: Path,
    record_path: Path,
    prefix: str,
) -> dict[str, str]:
    lock = verify_lock(lock_path, REPO_ROOT, expected_prefix=prefix)
    record = load_json(record_path)
    valid = bool(
        record.get("status") == "PASS"
        and record.get("qualification_id") == lock["qualification_id"]
        and record.get("qualification_id") == expected["qualification_id"]
        and record.get("lock_sha256") == lock["lock_sha256"]
        and record.get("lock_sha256") == expected["lock_sha256"]
        and sha256_file(record_path) == expected["record_sha256"]
    )
    if not valid:
        raise RuntimeError(f"invalid prerequisite record: {prefix}")
    return {
        "status": "PASS",
        "qualification_id": record["qualification_id"],
        "lock_sha256": lock["lock_sha256"],
        "record_sha256": sha256_file(record_path),
    }


def _verify_commitments(path: str, spec: dict[str, Any]) -> dict[str, Any]:
    payload = load_json(path)
    expected_hash = spec["prerequisites"]["sealed_publication_reserve_sha256"]
    actual_hash = sha256_file(path)
    forbidden = {
        "source_case_id",
        "source_index",
        "initial_positions_decimal",
        "initial_velocities_decimal",
        "brutus_final_positions_decimal",
        "brutus_final_velocities_decimal",
    }
    commitments = payload.get("commitments", [])
    families = [item.get("source_family") for item in commitments]
    valid = bool(
        actual_hash == expected_hash
        and payload.get("status") == "SEALED_UNEXECUTED"
        and payload.get("case_count") == 24
        and len(commitments) == 24
        and all(item.get("status") == "SEALED_UNEXECUTED" for item in commitments)
        and all(not (forbidden & set(item)) for item in commitments)
        and families.count("equal_mass_plummer") == 12
        and families.count("mass_4_2_1_plummer") == 12
    )
    if not valid:
        raise RuntimeError("publication reserve commitment is not intact and sealed")
    return {
        "status": "SEALED_UNEXECUTED",
        "sha256": actual_hash,
        "case_count": len(commitments),
        "source_rows_present": False,
    }


def _implementation_snapshot(spec: dict[str, Any]) -> dict[str, Any]:
    hashes = {}
    for relative_name in spec["implementation_files"]:
        path = (REPO_ROOT / relative_name).resolve()
        path.relative_to(REPO_ROOT)
        hashes[relative_name] = sha256_file(path)
    return {
        "file_hashes": hashes,
        "snapshot_sha256": sha256_bytes(canonical_json(hashes)),
    }


def _matrix_sha256(matrix: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(matrix, dtype="<f8")
    digest = hashlib.sha256(str(contiguous.shape).encode("ascii"))
    digest.update(contiguous.tobytes())
    return digest.hexdigest()


def _external_points(
    cases: list[dict[str, Any]],
    source_definitions: dict[str, dict[str, Any]],
    source_results: dict[str, dict[str, Any]],
) -> tuple[list[np.ndarray], list[np.ndarray], list[dict[str, str]]]:
    values = []
    derivatives = []
    metadata = []
    expected_names = feature_names()
    for case in cases:
        source_id = case["source_case_id"]
        definition = source_definitions[source_id]
        result = source_results[source_id]
        parameters = SystemParameters(
            [float(value) for value in definition["masses_decimal"]],
            gravitational_constant=1.0,
        )
        for checkpoint in case["checkpoint_indices"]:
            state = InertialState(
                np.asarray(result["oracle"]["states_decimal"][checkpoint], dtype=float)
            )
            system = nondimensionalize(
                state, parameters, length_scale=float(case["length_scale"])
            )
            evaluation = evaluate_feature_library(
                system.state, system.derivative, system.parameters
            )
            if evaluation.names != expected_names:
                raise RuntimeError("feature ordering changed during execution")
            values.append(evaluation.values)
            derivatives.append(evaluation.lie_derivatives)
            metadata.append(
                {
                    "point_id": f"{case['case_id']}:checkpoint-{checkpoint}",
                    "group_id": case["case_id"],
                    "family_id": case["source_family"],
                    "source_kind": case["source_kind"],
                }
            )
    return values, derivatives, metadata


def _synthetic_points(
    cases: list[dict[str, Any]],
) -> tuple[list[np.ndarray], list[np.ndarray], list[dict[str, str]]]:
    values = []
    derivatives = []
    metadata = []
    for case in cases:
        state = InertialState.from_components(case["positions"], case["velocities"])
        parameters = SystemParameters(case["masses"], gravitational_constant=1.0)
        system = nondimensionalize(
            state, parameters, length_scale=float(case["length_scale"])
        )
        evaluation = evaluate_feature_library(
            system.state, system.derivative, system.parameters
        )
        values.append(evaluation.values)
        derivatives.append(evaluation.lie_derivatives)
        metadata.append(
            {
                "point_id": case["case_id"],
                "group_id": case["case_id"],
                "family_id": case["source_family"],
                "source_kind": case["source_kind"],
            }
        )
    return values, derivatives, metadata


def _split_matrices(
    split: str,
    corpus: dict[str, Any],
    source_definitions: dict[str, dict[str, Any]],
    source_results: dict[str, dict[str, Any]],
) -> tuple[np.ndarray, np.ndarray, list[dict[str, str]]]:
    selected = [case for case in corpus["cases"] if case["split"] == split]
    external = [
        case for case in selected if case["source_kind"] == "qualified_external_trajectory"
    ]
    synthetic = [
        case
        for case in selected
        if case["source_kind"] == "deterministic_spatial_collocation"
    ]
    external_values, external_derivatives, external_metadata = _external_points(
        external, source_definitions, source_results
    )
    synthetic_values, synthetic_derivatives, synthetic_metadata = _synthetic_points(
        synthetic
    )
    return (
        np.stack(external_values + synthetic_values),
        np.stack(external_derivatives + synthetic_derivatives),
        external_metadata + synthetic_metadata,
    )


def main() -> None:
    args = _args()
    spec = load_json(args.spec)
    corpus = load_json(args.corpus)
    spatial_corpus = load_json(args.spatial_corpus)
    if corpus["spec_sha256"] != sha256_file(args.spec):
        raise RuntimeError("exploration corpus uses a different specification")
    if corpus["spatial_corpus_sha256"] != sha256_file(args.spatial_corpus):
        raise RuntimeError("exploration corpus uses a different spatial corpus")
    if corpus["sealed_commitments_sha256"] != sha256_file(args.commitments):
        raise RuntimeError("exploration corpus uses a different sealed reserve")
    prerequisites = {
        "wp1_spatial_n3bp": _verify_prerequisite(
            spec["prerequisites"]["wp1_spatial_n3bp"],
            SPATIAL_LOCK,
            SPATIAL_RECORD,
            "WP1Q-N3BP-SPATIAL-v2",
        ),
        "wp2_threebody_flow": _verify_prerequisite(
            spec["prerequisites"]["wp2_threebody_flow"],
            FLOW_LOCK,
            FLOW_RECORD,
            "WP2-3BFLOWQ-v1",
        ),
    }
    reserve = _verify_commitments(args.commitments, spec)
    definitions = {case["case_id"]: case for case in spatial_corpus["cases"]}
    development_results = load_json(args.spatial_development)
    calibration_results = load_json(args.spatial_calibration)
    development_sources = {
        case["case_id"]: case for case in development_results["cases"]
    }
    calibration_sources = {
        case["case_id"]: case for case in calibration_results["cases"]
    }
    train_values, train_derivatives, train_metadata = _split_matrices(
        "development", corpus, definitions, development_sources
    )
    calibration_values, calibration_derivatives, calibration_metadata = (
        _split_matrices(
            "calibration", corpus, definitions, calibration_sources
        )
    )
    search_spec = spec["search"]
    search = search_near_null_modes(
        train_values,
        train_derivatives,
        calibration_values,
        calibration_derivatives,
        feature_names=feature_names(),
        known_controls=known_algebra_coefficients(),
        training_group_ids=[item["group_id"] for item in train_metadata],
        training_family_ids=[item["family_id"] for item in train_metadata],
        calibration_group_ids=[item["group_id"] for item in calibration_metadata],
        calibration_family_ids=[item["family_id"] for item in calibration_metadata],
        mode_count=int(search_spec["mode_count"]),
        value_rank_relative_tolerance=float(
            search_spec["value_rank_relative_tolerance"]
        ),
        candidate_lie_rms_max=float(search_spec["candidate_lie_rms_max"]),
        calibration_to_training_max=float(
            search_spec["calibration_to_training_max"]
        ),
        family_fold_cosine_min=float(
            search_spec["family_fold_coefficient_cosine_min"]
        ),
        trajectory_drift_max=float(
            search_spec["calibration_trajectory_drift_max"]
        ),
    )
    known_control_max = max(
        metric["lie_max_abs"]
        for metric in search["known_control_metrics"].values()
    )
    search_ready_gates = [
        make_gate("prerequisite_pass_rate", 1.0, ">=", 1.0),
        make_gate("sealed_reserve_intact", 1, "==", 1),
        make_gate(
            "known_control_lie_max",
            known_control_max,
            "<=",
            float(search_spec["known_control_lie_max"]),
        ),
    ]
    search_ready = "PASS" if all(gate["passed"] for gate in search_ready_gates) else "FAIL"
    candidate_count = int(search["candidate_count"])
    candidate_status = "PASS" if candidate_count else "NOT_TRIGGERED"
    overall_status = (
        "CANDIDATE_REQUIRES_SEPARATE_QUALIFICATION"
        if candidate_count
        else "COMPLETE_BOUNDED_NULL_RESULT"
    )
    snapshot = _implementation_snapshot(spec)
    payload = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "status": overall_status,
        "interpretation_status": "PROHIBITED",
        "generated_utc": utc_now(),
        "spec_sha256": sha256_file(args.spec),
        "corpus_sha256": sha256_file(args.corpus),
        "spatial_corpus_sha256": sha256_file(args.spatial_corpus),
        "spatial_development_sha256": sha256_file(args.spatial_development),
        "spatial_calibration_sha256": sha256_file(args.spatial_calibration),
        "prerequisites": prerequisites,
        "sealed_publication_reserve": reserve,
        "implementation_snapshot": snapshot,
        "runtime": runtime_fingerprint(),
        "matrix_hashes": {
            "training_values": _matrix_sha256(train_values),
            "training_lie_derivatives": _matrix_sha256(train_derivatives),
            "calibration_values": _matrix_sha256(calibration_values),
            "calibration_lie_derivatives": _matrix_sha256(
                calibration_derivatives
            ),
        },
        "source_summary": {
            "training_points": len(train_metadata),
            "calibration_points": len(calibration_metadata),
            "training_groups": len({item["group_id"] for item in train_metadata}),
            "calibration_groups": len(
                {item["group_id"] for item in calibration_metadata}
            ),
            "training_source_kind_counts": {
                kind: sum(item["source_kind"] == kind for item in train_metadata)
                for kind in sorted({item["source_kind"] for item in train_metadata})
            },
            "calibration_source_kind_counts": {
                kind: sum(
                    item["source_kind"] == kind for item in calibration_metadata
                )
                for kind in sorted(
                    {item["source_kind"] for item in calibration_metadata}
                )
            },
        },
        "search": search,
    }
    gate_payload = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "generated_utc": utc_now(),
        "result_sha256": None,
        "SEARCH_READY": {
            "status": search_ready,
            "gates": search_ready_gates,
        },
        "CANDIDATE_READY": {
            "status": candidate_status,
            "candidate_count": candidate_count,
            "interpretation_authorized": False,
        },
        "PUBLICATION_READY": {
            "status": "BLOCKED",
            "reason": "candidate-specific qualification has not been frozen and passed",
            "sealed_reserve_status": reserve["status"],
            "interpretation_authorized": False,
        },
    }
    atomic_write_json(args.output, payload)
    gate_payload["result_sha256"] = sha256_file(args.output)
    atomic_write_json(args.gate_output, gate_payload)
    print(
        f"{spec['campaign']}: {overall_status}; "
        f"SEARCH_READY={search_ready}, candidates={candidate_count}"
    )
    if search_ready != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
