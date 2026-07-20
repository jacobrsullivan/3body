#!/usr/bin/env python
"""Execute the fail-closed WP3-UP-CAND-v2 development/calibration search."""

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
    atomic_write_json, load_json, make_gate, runtime_fingerprint,
    sha256_file, utc_now, verify_lock,
)
from src.python.n3bp_qualification import InertialState, SystemParameters  # noqa: E402
from src.python.upstairs_ks import lift_jacobi_state, upstairs_vector_field  # noqa: E402
from src.python.wp3_exploration_v2 import nondimensionalize, search_near_null_modes  # noqa: E402
from src.python.wp3_upstairs_v2 import (  # noqa: E402
    evaluate_upstairs_v2_features, feature_names, known_control_coefficients,
)


SPATIAL_ROOT = VALIDATION_ROOT / "wp3-spatial-validation-v2"
SPATIAL_LOCK = SPATIAL_ROOT / "reports/wp3_spatial_v2_qualification_lock.json"
SPATIAL_RECORD = SPATIAL_ROOT / "reports/wp3_spatial_v2_qualification_record.json"
UP_ROOT = VALIDATION_ROOT / "wp2-up-validation-v2"
UP_LOCK = UP_ROOT / "reports/wp2_up_v2_qualification_lock.json"
UP_RECORD = UP_ROOT / "reports/wp2_up_v2_qualification_record.json"


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--source-corpus", required=True)
    parser.add_argument("--spatial-corpus", required=True)
    parser.add_argument("--spatial-development", required=True)
    parser.add_argument("--spatial-calibration", required=True)
    parser.add_argument("--commitments", required=True)
    parser.add_argument("--lock", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--gate-output", required=True)
    return parser.parse_args()


def _verify_prerequisite(expected: dict[str, str], lock_path: Path, record_path: Path, prefix: str) -> dict[str, str]:
    lock = verify_lock(lock_path, REPO_ROOT, expected_prefix=prefix)
    record = load_json(record_path)
    valid = bool(
        record.get("status") == "PASS"
        and record.get("qualification_id") == expected["qualification_id"] == lock["qualification_id"]
        and record.get("lock_sha256") == expected["lock_sha256"] == lock["lock_sha256"]
        and sha256_file(record_path) == expected["record_sha256"]
    )
    if not valid:
        raise RuntimeError(f"invalid prerequisite: {prefix}")
    return {
        "status": "PASS", "qualification_id": record["qualification_id"],
        "lock_sha256": lock["lock_sha256"], "record_sha256": sha256_file(record_path),
    }


def _verify_reserve(path: str, expected_hash: str) -> dict[str, Any]:
    payload = load_json(path)
    commitments = payload.get("commitments", [])
    forbidden = {
        "source_case_id", "source_index", "initial_positions_decimal",
        "initial_velocities_decimal", "brutus_final_positions_decimal",
        "brutus_final_velocities_decimal",
    }
    valid = bool(
        sha256_file(path) == expected_hash
        and payload.get("status") == "SEALED_UNEXECUTED"
        and payload.get("case_count") == 24
        and len(commitments) == 24
        and all(item.get("status") == "SEALED_UNEXECUTED" for item in commitments)
        and all(not (forbidden & set(item)) for item in commitments)
    )
    if not valid:
        raise RuntimeError("WP3 publication reserve is not intact and sealed")
    return {"status": "SEALED_UNEXECUTED", "case_count": 24, "sha256": sha256_file(path), "source_rows_present": False}


def _verify_spatial_inputs(
    spatial_corpus_path: str,
    development_path: str,
    calibration_path: str,
) -> dict[str, str]:
    record = load_json(SPATIAL_RECORD)
    corpus_evidence = record["evidence_files"]["corpus"]
    if sha256_file(spatial_corpus_path) != corpus_evidence["sha256"]:
        raise RuntimeError("spatial corpus is not the qualified input")
    output = {"corpus_sha256": sha256_file(spatial_corpus_path)}
    for split, result_path in (
        ("development", development_path),
        ("calibration", calibration_path),
    ):
        evidence = record["evidence_files"][f"{split}_evaluation"]
        evaluation_path = REPO_ROOT / evidence["path"]
        if sha256_file(evaluation_path) != evidence["sha256"]:
            raise RuntimeError(f"qualified spatial {split} evaluation changed")
        evaluation = load_json(evaluation_path)
        if evaluation["status"] != "PASS" or evaluation["results_sha256"] != sha256_file(result_path):
            raise RuntimeError(f"spatial {split} result is not qualification-bound")
        output[f"{split}_results_sha256"] = sha256_file(result_path)
        output[f"{split}_evaluation_sha256"] = sha256_file(evaluation_path)
    return output


def _matrix_sha256(matrix: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(matrix, dtype="<f8")
    digest = hashlib.sha256(str(contiguous.shape).encode("ascii"))
    digest.update(contiguous.tobytes())
    return digest.hexdigest()


def _evaluate_state(
    state: InertialState,
    parameters: SystemParameters,
    *,
    length_scale: float,
    gauge_angles: list[float],
    group_id: str,
    family_id: str,
    source_kind: str,
    point_label: str,
) -> tuple[list[np.ndarray], list[np.ndarray], list[dict[str, str]]]:
    system = nondimensionalize(state, parameters, length_scale=length_scale)
    values, derivatives, metadata = [], [], []
    for gauge_index, angle in enumerate(gauge_angles):
        shell = lift_jacobi_state(system.state, system.parameters, angle=float(angle))
        flow = upstairs_vector_field(shell.state, system.parameters, shell.energy)
        evaluation = evaluate_upstairs_v2_features(
            shell.state,
            flow.derivative,
            system.parameters,
            fixed_energy=shell.energy,
        )
        if evaluation.names != feature_names():
            raise RuntimeError("upstairs feature ordering changed")
        values.append(evaluation.values)
        derivatives.append(evaluation.lie_derivatives)
        metadata.append(
            {
                "point_id": f"{point_label}:gauge-{gauge_index}",
                "group_id": group_id,
                "family_id": family_id,
                "source_kind": source_kind,
            }
        )
    return values, derivatives, metadata


def _split_matrices(
    split: str,
    corpus: dict[str, Any],
    source_definitions: dict[str, dict[str, Any]],
    source_results: dict[str, dict[str, Any]],
) -> tuple[np.ndarray, np.ndarray, list[dict[str, str]]]:
    values: list[np.ndarray] = []
    derivatives: list[np.ndarray] = []
    metadata: list[dict[str, str]] = []
    angles = [float(value) for value in corpus["gauge_angles"]]
    for case in (item for item in corpus["cases"] if item["split"] == split):
        if case["source_kind"] == "qualified_external_trajectory":
            definition = source_definitions[case["source_case_id"]]
            result = source_results[case["source_case_id"]]
            parameters = SystemParameters(
                [float(value) for value in definition["masses_decimal"]],
                gravitational_constant=1.0,
            )
            for checkpoint in case["checkpoint_indices"]:
                state = InertialState(np.asarray(result["oracle"]["states_decimal"][checkpoint], dtype=float))
                chunk = _evaluate_state(
                    state, parameters, length_scale=float(case["length_scale"]),
                    gauge_angles=angles, group_id=case["case_id"],
                    family_id=case["source_family"], source_kind=case["source_kind"],
                    point_label=f"{case['case_id']}:checkpoint-{checkpoint}",
                )
                values.extend(chunk[0]); derivatives.extend(chunk[1]); metadata.extend(chunk[2])
        elif case["source_kind"] == "deterministic_spatial_collocation":
            state = InertialState.from_components(case["positions"], case["velocities"])
            parameters = SystemParameters(case["masses"], gravitational_constant=1.0)
            chunk = _evaluate_state(
                state, parameters, length_scale=float(case["length_scale"]),
                gauge_angles=angles, group_id=case["case_id"],
                family_id=case["source_family"], source_kind=case["source_kind"],
                point_label=case["case_id"],
            )
            values.extend(chunk[0]); derivatives.extend(chunk[1]); metadata.extend(chunk[2])
        else:
            raise ValueError(f"unsupported source kind: {case['source_kind']}")
    return np.stack(values), np.stack(derivatives), metadata


def main() -> None:
    args = _args()
    spec, corpus, source_corpus = load_json(args.spec), load_json(args.corpus), load_json(args.source_corpus)
    spatial_corpus = load_json(args.spatial_corpus)
    if corpus["spec_sha256"] != sha256_file(args.spec) or corpus["source_corpus_sha256"] != sha256_file(args.source_corpus):
        raise RuntimeError("WP3-UP corpus input mismatch")
    if corpus["sealed_commitments_sha256"] != sha256_file(args.commitments):
        raise RuntimeError("WP3-UP corpus reserve mismatch")
    lock = verify_lock(args.lock, REPO_ROOT, expected_prefix=spec["campaign"])
    if lock["spec_sha256"] != sha256_file(args.spec) or lock["corpus_sha256"] != sha256_file(args.corpus):
        raise RuntimeError("WP3-UP search lock input mismatch")
    prerequisites = {
        "wp2_upstairs": _verify_prerequisite(spec["prerequisites"]["wp2_upstairs"], UP_LOCK, UP_RECORD, "WP2-UPQ-v2"),
        "wp1_spatial_n3bp": _verify_prerequisite(spec["prerequisites"]["wp1_spatial_n3bp"], SPATIAL_LOCK, SPATIAL_RECORD, "WP1Q-N3BP-SPATIAL-v2"),
    }
    spatial_inputs = _verify_spatial_inputs(
        args.spatial_corpus,
        args.spatial_development,
        args.spatial_calibration,
    )
    reserve = _verify_reserve(args.commitments, spec["prerequisites"]["sealed_publication_reserve_sha256"])
    definitions = {case["case_id"]: case for case in spatial_corpus["cases"]}
    development_sources = {case["case_id"]: case for case in load_json(args.spatial_development)["cases"]}
    calibration_sources = {case["case_id"]: case for case in load_json(args.spatial_calibration)["cases"]}
    train_values, train_derivatives, train_metadata = _split_matrices("development", corpus, definitions, development_sources)
    calibration_values, calibration_derivatives, calibration_metadata = _split_matrices("calibration", corpus, definitions, calibration_sources)
    search_spec = spec["search"]
    search = search_near_null_modes(
        train_values, train_derivatives, calibration_values, calibration_derivatives,
        feature_names=feature_names(), known_controls=known_control_coefficients(),
        training_group_ids=[item["group_id"] for item in train_metadata],
        training_family_ids=[item["family_id"] for item in train_metadata],
        calibration_group_ids=[item["group_id"] for item in calibration_metadata],
        calibration_family_ids=[item["family_id"] for item in calibration_metadata],
        mode_count=int(search_spec["mode_count"]),
        value_rank_relative_tolerance=float(search_spec["value_rank_relative_tolerance"]),
        candidate_lie_rms_max=float(search_spec["candidate_lie_rms_max"]),
        calibration_to_training_max=float(search_spec["calibration_to_training_max"]),
        family_fold_cosine_min=float(search_spec["family_fold_coefficient_cosine_min"]),
        trajectory_drift_max=float(search_spec["calibration_trajectory_drift_max"]),
    )
    known_max = max(metric["weighted_lie_rms"] for metric in search["known_control_metrics"].values())
    search_ready_gates = [
        make_gate("prerequisite_pass_rate", 1.0, ">=", 1.0),
        make_gate("search_lock_verified", 1, "==", 1),
        make_gate("sealed_reserve_intact", 1, "==", 1),
        make_gate("spatial_inputs_hash_verified", 1, "==", 1),
        make_gate("feature_count", int(search["feature_count"]), "==", int(spec["library"]["total_feature_count"])),
        make_gate("known_control_weighted_lie_rms_max", known_max, "<=", float(search_spec["known_control_weighted_lie_rms_max"])),
    ]
    search_ready = "PASS" if all(gate["passed"] for gate in search_ready_gates) else "FAIL"
    candidate_count = int(search["candidate_count"])
    if search_ready != "PASS":
        candidate_ready = "BLOCKED"
        sealed_qualification = "BLOCKED"
        status = "INVALID_SEARCH_NOT_READY"
    elif candidate_count:
        candidate_ready = "PASS"
        sealed_qualification = "REQUIRED"
        status = "CANDIDATE_REQUIRES_SEPARATE_QUALIFICATION"
    else:
        candidate_ready = "NOT_TRIGGERED"
        sealed_qualification = "NOT_TRIGGERED"
        status = "COMPLETE_BOUNDED_NULL_RESULT"
    payload = {
        "schema_version": "1.0", "campaign": spec["campaign"], "status": status,
        "interpretation_status": "PROHIBITED", "generated_utc": utc_now(),
        "qualification_id": lock["qualification_id"], "lock_sha256": lock["lock_sha256"],
        "spec_sha256": sha256_file(args.spec), "corpus_sha256": sha256_file(args.corpus),
        "source_corpus_sha256": sha256_file(args.source_corpus),
        "prerequisites": prerequisites, "sealed_publication_reserve": reserve,
        "qualified_spatial_inputs": spatial_inputs,
        "runtime": runtime_fingerprint(),
        "matrix_hashes": {
            "training_values": _matrix_sha256(train_values),
            "training_lie_derivatives": _matrix_sha256(train_derivatives),
            "calibration_values": _matrix_sha256(calibration_values),
            "calibration_lie_derivatives": _matrix_sha256(calibration_derivatives),
        },
        "source_summary": {
            "training_points": len(train_metadata), "calibration_points": len(calibration_metadata),
            "training_groups": len({item["group_id"] for item in train_metadata}),
            "calibration_groups": len({item["group_id"] for item in calibration_metadata}),
            "gauge_count": len(corpus["gauge_angles"]),
        },
        "search": search,
    }
    gate = {
        "schema_version": "1.0", "campaign": spec["campaign"],
        "qualification_id": lock["qualification_id"], "lock_sha256": lock["lock_sha256"],
        "SEARCH_READY": search_ready, "CANDIDATE_READY": candidate_ready,
        "SEALED_QUALIFICATION": sealed_qualification,
        "WP4_READY": "BLOCKED", "publication_reserve_status": "SEALED_UNEXECUTED",
        "candidate_count": candidate_count, "search_ready_gates": search_ready_gates,
    }
    atomic_write_json(args.output, payload)
    atomic_write_json(args.gate_output, gate)
    print(f"{spec['campaign']}: {status}; SEARCH_READY={search_ready}; candidates={candidate_count}")


if __name__ == "__main__":
    main()
