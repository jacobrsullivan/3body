#!/usr/bin/env python
"""Execute the fail-closed WP3-UP-CAND-v3 exact-module search."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
from pathlib import Path
import platform
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
from src.python.wp3_exploration_v2.normalization import nondimensionalize  # noqa: E402
from src.python.wp3_exploration_v3 import search_quotient_modes  # noqa: E402
from src.python.wp3_upstairs_v3 import (  # noqa: E402
    evaluate_upstairs_v3_features, feature_names, known_module_coefficients,
    s1_generator,
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


def _verify_runtime(expected: dict[str, Any]) -> dict[str, Any]:
    observed = {
        "python": platform.python_version(),
        "packages": {
            name: importlib.metadata.version(name)
            for name in expected["packages"]
        },
    }
    if observed != expected:
        raise RuntimeError(f"decision runtime mismatch: expected {expected}, observed {observed}")
    return observed


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
    fixed_energy: float | None = None,
) -> tuple[list[np.ndarray], list[np.ndarray], list[np.ndarray], list[dict[str, Any]]]:
    system = nondimensionalize(state, parameters, length_scale=length_scale)
    values, derivatives, gauge_derivatives, metadata = [], [], [], []
    for gauge_index, angle in enumerate(gauge_angles):
        shell = lift_jacobi_state(system.state, system.parameters, angle=float(angle))
        energy = shell.energy if fixed_energy is None else float(fixed_energy)
        flow = upstairs_vector_field(shell.state, system.parameters, energy)
        evaluation = evaluate_upstairs_v3_features(
            shell.state,
            flow.derivative,
            system.parameters,
            fixed_energy=energy,
        )
        gauge_evaluation = evaluate_upstairs_v3_features(
            shell.state,
            s1_generator(shell.state),
            system.parameters,
            fixed_energy=energy,
        )
        if evaluation.names != feature_names():
            raise RuntimeError("upstairs feature ordering changed")
        values.append(evaluation.values)
        derivatives.append(evaluation.lie_derivatives)
        gauge_derivatives.append(gauge_evaluation.lie_derivatives)
        metadata.append(
            {
                "point_id": f"{point_label}:gauge-{gauge_index}",
                "physical_point_id": point_label,
                "group_id": group_id,
                "family_id": family_id,
                "source_kind": source_kind,
                "checkpoint_energy_difference": float(shell.energy - energy),
            }
        )
    return values, derivatives, gauge_derivatives, metadata


def _split_matrices(
    split: str,
    corpus: dict[str, Any],
    source_definitions: dict[str, dict[str, Any]],
    source_results: dict[str, dict[str, Any]],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[dict[str, Any]]]:
    values: list[np.ndarray] = []
    derivatives: list[np.ndarray] = []
    gauge_derivatives: list[np.ndarray] = []
    metadata: list[dict[str, Any]] = []
    angles = [float(value) for value in corpus["gauge_angles"]]
    for case in (item for item in corpus["cases"] if item["split"] == split):
        if case["source_kind"] == "qualified_external_trajectory":
            definition = source_definitions[case["source_case_id"]]
            result = source_results[case["source_case_id"]]
            parameters = SystemParameters(
                [float(value) for value in definition["masses_decimal"]],
                gravitational_constant=1.0,
            )
            reference_index = int(case["checkpoint_indices"][0])
            reference_state = InertialState(
                np.asarray(result["oracle"]["states_decimal"][reference_index], dtype=float)
            )
            reference_system = nondimensionalize(
                reference_state, parameters, length_scale=float(case["length_scale"])
            )
            fixed_energy = lift_jacobi_state(
                reference_system.state, reference_system.parameters, angle=0.0
            ).energy
            for checkpoint in case["checkpoint_indices"]:
                state = InertialState(np.asarray(result["oracle"]["states_decimal"][checkpoint], dtype=float))
                chunk = _evaluate_state(
                    state, parameters, length_scale=float(case["length_scale"]),
                    gauge_angles=angles, group_id=case["case_id"],
                    family_id=case["source_family"], source_kind=case["source_kind"],
                    point_label=f"{case['case_id']}:checkpoint-{checkpoint}",
                    fixed_energy=fixed_energy,
                )
                values.extend(chunk[0]); derivatives.extend(chunk[1]); gauge_derivatives.extend(chunk[2]); metadata.extend(chunk[3])
        elif case["source_kind"] == "deterministic_spatial_collocation":
            state = InertialState.from_components(case["positions"], case["velocities"])
            parameters = SystemParameters(case["masses"], gravitational_constant=1.0)
            chunk = _evaluate_state(
                state, parameters, length_scale=float(case["length_scale"]),
                gauge_angles=angles, group_id=case["case_id"],
                family_id=case["source_family"], source_kind=case["source_kind"],
                point_label=case["case_id"],
            )
            values.extend(chunk[0]); derivatives.extend(chunk[1]); gauge_derivatives.extend(chunk[2]); metadata.extend(chunk[3])
        else:
            raise ValueError(f"unsupported source kind: {case['source_kind']}")
    return np.stack(values), np.stack(derivatives), np.stack(gauge_derivatives), metadata


def main() -> None:
    args = _args()
    spec, corpus, source_corpus = load_json(args.spec), load_json(args.corpus), load_json(args.source_corpus)
    decision_runtime = _verify_runtime(spec["decision_runtime"])
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
    train_values, train_derivatives, train_gauge_derivatives, train_metadata = _split_matrices("development", corpus, definitions, development_sources)
    calibration_values, calibration_derivatives, calibration_gauge_derivatives, calibration_metadata = _split_matrices("calibration", corpus, definitions, calibration_sources)
    search_spec = spec["search"]
    search = search_quotient_modes(
        train_values, train_derivatives, train_gauge_derivatives,
        calibration_values, calibration_derivatives, calibration_gauge_derivatives,
        feature_names=feature_names(), known_module=known_module_coefficients(),
        training_group_ids=[item["group_id"] for item in train_metadata],
        training_family_ids=[item["family_id"] for item in train_metadata],
        training_point_ids=[item["physical_point_id"] for item in train_metadata],
        calibration_group_ids=[item["group_id"] for item in calibration_metadata],
        calibration_family_ids=[item["family_id"] for item in calibration_metadata],
        calibration_point_ids=[item["physical_point_id"] for item in calibration_metadata],
        mode_count=int(search_spec["mode_count"]),
        fold_mode_count=int(search_spec["fold_mode_count"]),
        value_rank_relative_tolerance=float(search_spec["value_rank_relative_tolerance"]),
        candidate_lie_rms_max=float(search_spec["candidate_lie_rms_max"]),
        candidate_gauge_lie_rms_max=float(search_spec["candidate_gauge_lie_rms_max"]),
        calibration_ratio_floor=float(search_spec["calibration_ratio_floor"]),
        calibration_to_training_max=float(search_spec["calibration_to_training_max"]),
        family_fold_subspace_projection_min=float(search_spec["family_fold_subspace_projection_min"]),
        calibration_trajectory_drift_max=float(search_spec["calibration_trajectory_drift_max"]),
        gauge_orbit_spread_max=float(search_spec["gauge_orbit_spread_max"]),
    )
    known_metrics = search["known_module_metrics"]
    known_lie_max = max(
        max(metric["training_lie_rms_per_coefficient_scale"], metric["calibration_lie_rms_per_coefficient_scale"])
        for metric in known_metrics.values()
    )
    known_gauge_max = max(
        max(metric["training_gauge_lie_rms_per_coefficient_scale"], metric["calibration_gauge_lie_rms_per_coefficient_scale"])
        for metric in known_metrics.values()
    )
    constraint_value_max = max(
        max(metric["training_value_abs_max"], metric["calibration_value_abs_max"])
        for name, metric in known_metrics.items() if name.startswith("constraint:")
    )
    parameter_weighted_angular_count = sum(
        name.startswith("known:") and "*" in name for name in known_metrics
    )
    fixed_energy_checkpoint_abs_max = max(
        abs(float(item["checkpoint_energy_difference"]))
        for item in (*train_metadata, *calibration_metadata)
    )
    search_ready_gates = [
        make_gate("prerequisite_pass_rate", 1.0, ">=", 1.0),
        make_gate("search_lock_verified", 1, "==", 1),
        make_gate("sealed_reserve_intact", 1, "==", 1),
        make_gate("spatial_inputs_hash_verified", 1, "==", 1),
        make_gate("feature_count", int(search["feature_count"]), "==", int(spec["library"]["search_feature_count"])),
        make_gate("exact_known_module_rank", int(search["exact_known_module_rank"]), "==", int(spec["library"]["exact_known_module_rank"])),
        make_gate("parameter_weighted_angular_control_count", parameter_weighted_angular_count, "==", 9),
        make_gate("known_module_lie_rms_max", known_lie_max, "<=", float(search_spec["known_module_lie_rms_max"])),
        make_gate("known_module_gauge_lie_rms_max", known_gauge_max, "<=", float(search_spec["known_module_gauge_lie_rms_max"])),
        make_gate("constraint_value_abs_max", constraint_value_max, "<=", float(search_spec["constraint_value_abs_max"])),
        make_gate("known_module_projection_residual", float(search["exact_known_module_projection_residual"]), "<=", float(search_spec["known_module_projection_residual_max"])),
        make_gate("all_generalized_modes_evaluated", int(search["evaluated_mode_count"]), "==", int(search["observable_value_rank"])),
        make_gate("decision_runtime_exact", 1, "==", 1),
        make_gate("fixed_energy_checkpoint_abs_max", fixed_energy_checkpoint_abs_max, "<=", float(search_spec["fixed_energy_checkpoint_abs_max"])),
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
        "runtime": runtime_fingerprint(), "decision_runtime": decision_runtime,
        "matrix_hashes": {
            "training_values": _matrix_sha256(train_values),
            "training_lie_derivatives": _matrix_sha256(train_derivatives),
            "training_gauge_lie_derivatives": _matrix_sha256(train_gauge_derivatives),
            "calibration_values": _matrix_sha256(calibration_values),
            "calibration_lie_derivatives": _matrix_sha256(calibration_derivatives),
            "calibration_gauge_lie_derivatives": _matrix_sha256(calibration_gauge_derivatives),
        },
        "source_summary": {
            "training_points": len(train_metadata), "calibration_points": len(calibration_metadata),
            "training_groups": len({item["group_id"] for item in train_metadata}),
            "calibration_groups": len({item["group_id"] for item in calibration_metadata}),
            "gauge_count": len(corpus["gauge_angles"]),
            "fixed_energy_checkpoint_abs_max": fixed_energy_checkpoint_abs_max,
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
