#!/usr/bin/env python
"""Run deterministic WP3 near-null screening on non-reserved data."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys
from typing import Any, Iterable

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
    runtime_fingerprint,
    sha256_bytes,
    sha256_file,
    utc_now,
)
from src.python.wp3_exploration import (  # noqa: E402
    evaluate_invariant_features,
    evaluate_publication_gate,
    feature_dimensions,
    feature_names,
    format_dimension_signature,
    jacobi_vector_field,
    known_control_coefficients,
    sample_exploration_split,
    search_near_null_modes,
)
from src.python.wp3_exploration.source_cases import SamplePoint  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--gate-result", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def _matrix_sha256(matrix: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(matrix, dtype="<f8")
    digest = hashlib.sha256()
    digest.update(str(contiguous.shape).encode("ascii"))
    digest.update(contiguous.tobytes())
    return digest.hexdigest()


def _declared_repo_path(relative_name: str) -> Path:
    relative = Path(relative_name)
    if relative.is_absolute() or ".." in relative.parts:
        raise RuntimeError(f"unsafe declared repository path: {relative_name}")
    result = (REPO_ROOT / relative).resolve()
    try:
        result.relative_to(REPO_ROOT)
    except ValueError as error:
        raise RuntimeError(
            f"declared path escapes repository: {relative_name}"
        ) from error
    return result


def _validate_gate_result(spec: dict[str, Any], gate: dict[str, Any]) -> None:
    gate_spec_path = _declared_repo_path(spec["publication_gate_spec"])
    gate_manifest_path = _declared_repo_path(
        spec["publication_evidence_manifest"]
    )
    if gate.get("spec_sha256") != sha256_file(gate_spec_path):
        raise RuntimeError("publication gate result uses a different specification")
    if gate.get("evidence_manifest_sha256") != sha256_file(gate_manifest_path):
        raise RuntimeError("publication gate result uses a different evidence manifest")
    fresh = evaluate_publication_gate(
        gate_spec_path,
        gate_manifest_path,
        repo_root=REPO_ROOT,
    )
    compared_fields = (
        "campaign",
        "status",
        "interpretation_authorized",
        "passed_gate_count",
        "required_gate_count",
        "gates",
    )
    if any(gate.get(field) != fresh.get(field) for field in compared_fields):
        raise RuntimeError("publication gate result does not match fresh evaluation")


def _implementation_snapshot(spec: dict[str, Any]) -> dict[str, Any]:
    relative_names = [str(value) for value in spec["implementation_files"]]
    if not relative_names or len(relative_names) != len(set(relative_names)):
        raise RuntimeError("implementation_files must be non-empty and unique")
    file_hashes = {
        relative_name: sha256_file(_declared_repo_path(relative_name))
        for relative_name in sorted(relative_names)
    }
    return {
        "snapshot_sha256": sha256_bytes(canonical_json(file_hashes)),
        "file_hashes": file_hashes,
    }


def _evaluate_points(
    points: tuple[SamplePoint, ...],
) -> tuple[np.ndarray, np.ndarray]:
    values: list[np.ndarray] = []
    derivatives: list[np.ndarray] = []
    expected_names = feature_names()
    for point in points:
        vector_field = jacobi_vector_field(point.state, point.parameters)
        evaluation = evaluate_invariant_features(
            vector_field.state,
            vector_field.derivative,
            point.parameters,
        )
        if evaluation.names != expected_names:
            raise RuntimeError("feature ordering changed during exploration")
        values.append(evaluation.values)
        derivatives.append(evaluation.lie_derivatives)
    return np.stack(values), np.stack(derivatives)


def _source_summary(points: Iterable[SamplePoint]) -> dict[str, Any]:
    point_list = list(points)
    kinds = sorted({point.source_kind for point in point_list})
    cases = sorted({point.case_id for point in point_list})
    return {
        "sample_count": len(point_list),
        "case_count": len(cases),
        "case_ids": cases,
        "source_kind_counts": {
            kind: sum(point.source_kind == kind for point in point_list)
            for kind in kinds
        },
    }


def _trajectory_drift(
    points: tuple[SamplePoint, ...],
    feature_values: np.ndarray,
    coefficients: np.ndarray,
) -> list[dict[str, float | str]]:
    projected = np.einsum(
        "ij,j->i", feature_values, coefficients, optimize=False
    )
    trajectory_cases = sorted(
        {
            point.case_id
            for point in points
            if point.source_kind == "qualified_trajectory"
        }
    )
    result: list[dict[str, float | str]] = []
    global_scale = max(float(np.std(projected)), np.finfo(float).tiny)
    for case_id in trajectory_cases:
        indices = [
            index
            for index, point in enumerate(points)
            if point.case_id == case_id
            and point.source_kind == "qualified_trajectory"
        ]
        values = projected[indices]
        peak_to_peak = float(np.ptp(values))
        relative_scale = max(float(np.max(np.abs(values))), global_scale)
        result.append(
            {
                "case_id": case_id,
                "absolute_peak_to_peak": peak_to_peak,
                "scaled_peak_to_peak": peak_to_peak / relative_scale,
            }
        )
    return result


def _max_scaled_drift(rows: list[dict[str, float | str]]) -> float:
    return max((float(row["scaled_peak_to_peak"]) for row in rows), default=0.0)


def _search_dimension_sectors(
    spec: dict[str, Any],
    training_points: tuple[SamplePoint, ...],
    calibration_points: tuple[SamplePoint, ...],
    training_values: np.ndarray,
    training_derivatives: np.ndarray,
    calibration_values: np.ndarray,
    calibration_derivatives: np.ndarray,
    controls: dict[str, np.ndarray],
) -> dict[str, Any]:
    names = feature_names()
    dimensions = feature_dimensions()
    sector_indices: dict[tuple[int, int, int], list[int]] = {}
    for index, signature in enumerate(dimensions):
        sector_indices.setdefault(signature, []).append(index)

    control_sectors: dict[tuple[int, int, int], dict[str, np.ndarray]] = {}
    for name, coefficients in controls.items():
        support = np.flatnonzero(coefficients)
        signatures = {dimensions[int(index)] for index in support}
        if len(signatures) != 1:
            raise RuntimeError(
                f"known control {name} crosses physical-dimension sectors"
            )
        signature = signatures.pop()
        indices = np.asarray(sector_indices[signature], dtype=np.int64)
        control_sectors.setdefault(signature, {})[name] = coefficients[indices]

    sectors: list[dict[str, Any]] = []
    known_control_metrics: dict[str, dict[str, float]] = {}
    total_nullity = 0
    for signature in sorted(sector_indices):
        indices = np.asarray(sector_indices[signature], dtype=np.int64)
        sector_names = tuple(names[int(index)] for index in indices)
        search = search_near_null_modes(
            training_values[:, indices],
            training_derivatives[:, indices],
            calibration_values[:, indices],
            calibration_derivatives[:, indices],
            feature_names=sector_names,
            control_coefficients=control_sectors.get(signature, {}),
            mode_count=int(
                spec["search"]["mode_count_per_dimension_sector"]
            ),
            nullity_relative_tolerance=float(
                spec["search"]["nullity_relative_tolerance"]
            ),
        )
        sector_payload = search.as_dict(
            top_term_count=int(spec["search"]["top_term_count"])
        )
        sector_payload.update(
            {
                "sector_id": format_dimension_signature(signature),
                "dimension_signature": {
                    "mass_exponent": signature[0],
                    "length_exponent": signature[1],
                    "time_exponent": signature[2],
                },
                "global_feature_indices": indices.tolist(),
            }
        )
        known_control_metrics.update(sector_payload["known_control_metrics"])
        total_nullity += int(
            sector_payload["numerical_nullity_after_known_controls"]
        )

        for mode_payload, mode in zip(
            sector_payload["near_null_modes"], search.modes, strict=True
        ):
            full_coefficients = np.zeros(len(names), dtype=np.float64)
            full_coefficients[indices] = mode.coefficients
            training_drift = _trajectory_drift(
                training_points, training_values, full_coefficients
            )
            calibration_drift = _trajectory_drift(
                calibration_points, calibration_values, full_coefficients
            )
            mode_payload["trajectory_drift"] = {
                "training": training_drift,
                "calibration": calibration_drift,
                "training_max_scaled_peak_to_peak": _max_scaled_drift(
                    training_drift
                ),
                "calibration_max_scaled_peak_to_peak": _max_scaled_drift(
                    calibration_drift
                ),
            }
        sectors.append(sector_payload)

    return {
        "interpretation_status": "EXPLORATORY_ONLY",
        "dimensional_policy": spec["dimensional_policy"],
        "feature_count": len(names),
        "dimension_sector_count": len(sectors),
        "nullity_relative_tolerance": float(
            spec["search"]["nullity_relative_tolerance"]
        ),
        "numerical_nullity_after_known_controls": total_nullity,
        "known_control_metrics": known_control_metrics,
        "sectors": sectors,
    }


def main() -> None:
    args = parse_args()
    spec = load_json(args.spec)
    corpus = load_json(args.corpus)
    gate = load_json(args.gate_result)
    if spec.get("interpretation_status") != "EXPLORATORY_ONLY":
        raise RuntimeError("WP3 exploration specification lost its status boundary")
    _validate_gate_result(spec, gate)

    upstream_path = _declared_repo_path(corpus["upstream_corpus"])
    actual_upstream_hash = sha256_file(upstream_path)
    if actual_upstream_hash != corpus["upstream_corpus_sha256"]:
        raise RuntimeError(
            "upstream N3BP corpus hash does not match exploration corpus"
        )
    upstream_corpus = load_json(upstream_path)
    training_points = sample_exploration_split(
        corpus, upstream_corpus, "training"
    )
    calibration_points = sample_exploration_split(
        corpus, upstream_corpus, "calibration"
    )
    training_values, training_derivatives = _evaluate_points(training_points)
    calibration_values, calibration_derivatives = _evaluate_points(
        calibration_points
    )

    controls = known_control_coefficients()
    search_payload = _search_dimension_sectors(
        spec,
        training_points,
        calibration_points,
        training_values,
        training_derivatives,
        calibration_values,
        calibration_derivatives,
        controls,
    )

    control_drift: dict[str, Any] = {}
    for name, coefficients in controls.items():
        training_drift = _trajectory_drift(
            training_points, training_values, coefficients
        )
        calibration_drift = _trajectory_drift(
            calibration_points, calibration_values, coefficients
        )
        control_drift[name] = {
            "coefficients": coefficients.tolist(),
            "training_trajectories": training_drift,
            "calibration_trajectories": calibration_drift,
            "training_max_scaled_peak_to_peak": _max_scaled_drift(training_drift),
            "calibration_max_scaled_peak_to_peak": _max_scaled_drift(
                calibration_drift
            ),
        }

    payload = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "generated_utc": utc_now(),
        "interpretation_status": "EXPLORATORY_ONLY",
        "publication_gate": {
            "campaign": gate["campaign"],
            "status": gate["status"],
            "interpretation_authorized": gate["interpretation_authorized"],
            "result_sha256": sha256_file(args.gate_result),
        },
        "claim_boundary": (
            "Outputs rank numerical screening directions only. No conservation, "
            "independence, involution, or integrability claim is made."
        ),
        "input_hashes": {
            "exploration_spec_sha256": sha256_file(args.spec),
            "exploration_corpus_sha256": sha256_file(args.corpus),
            "upstream_n3bp_corpus_sha256": actual_upstream_hash,
        },
        "implementation_snapshot": _implementation_snapshot(spec),
        "runtime": runtime_fingerprint(),
        "provenance": {
            "training": _source_summary(training_points),
            "calibration": _source_summary(calibration_points),
            "quarantined_upstream_holdout_ids": corpus[
                "quarantined_upstream_holdout_ids"
            ],
            "holdout_policy": corpus["holdout_policy"],
        },
        "matrix_hashes": {
            "training_features": _matrix_sha256(training_values),
            "training_lie_derivatives": _matrix_sha256(training_derivatives),
            "calibration_features": _matrix_sha256(calibration_values),
            "calibration_lie_derivatives": _matrix_sha256(
                calibration_derivatives
            ),
        },
        "search": search_payload,
        "known_control_trajectory_drift": control_drift,
    }
    atomic_write_json(args.output, payload)
    print(
        f"{spec['campaign']}: {len(training_points)} training and "
        f"{len(calibration_points)} calibration points; "
        f"status={payload['interpretation_status']}"
    )


if __name__ == "__main__":
    main()
