#!/usr/bin/env python
"""Execute one frozen WP1-CAT-N3BP-v1 qualification split."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import importlib.metadata
from pathlib import Path
import sys
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
VALIDATION = ROOT / "validation-external"
for path in (ROOT, VALIDATION, Path(__file__).resolve().parent):
    sys.path.insert(0, str(path))

from campaign_common import (  # noqa: E402
    from_hex,
    require_full_lock_runtime,
    verify_candidate_lock,
    verify_prerequisite,
    verify_specification_lock,
)
from qualification_tools import (  # noqa: E402
    atomic_write_json,
    load_json,
    runtime_fingerprint,
    sha256_file,
    utc_now,
    verify_lock,
)
from src.python.n3bp_qualification import (  # noqa: E402
    DOP853Config,
    IAS15Config,
    InertialState,
    SystemParameters,
    measure_invariant_drift,
    propagate_dop853,
    propagate_rebound_ias15,
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--catalogue", required=True)
    parser.add_argument("--candidate-lock", required=True)
    parser.add_argument(
        "--split", choices=("development", "calibration", "holdout"), required=True
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--lock")
    return parser.parse_args()


def _candidate_parameters(candidate: dict[str, Any]) -> dict[str, float]:
    return {
        name: from_hex(candidate["parameters"][name])
        for name in ("m1", "m2", "m3", "x1", "v1", "v2", "period")
    }


def _scales(state: InertialState, parameters: SystemParameters) -> tuple[float, float]:
    positions = state.positions
    length = max(
        float(np.linalg.norm(positions[first] - positions[second]))
        for first, second in ((0, 1), (0, 2), (1, 2))
    )
    velocity = float(
        np.sqrt(parameters.gravitational_constant * parameters.total_mass / length)
    )
    return length, velocity


def _trajectory_metrics(
    candidate: dict[str, Any], spec: dict[str, Any], *, rebound: bool
) -> dict[str, float]:
    values = _candidate_parameters(candidate)
    parameters = SystemParameters(
        np.array([values["m1"], values["m2"], values["m3"]]), 1.0
    )
    initial = InertialState(np.array([from_hex(value) for value in candidate["state18"]]))
    period = values["period"]
    times = np.linspace(0.0, period, int(spec["execution"]["checkpoint_count"]))
    trajectory = propagate_dop853(
        initial,
        times,
        parameters,
        config=DOP853Config(
            rtol=float(spec["generation"]["correction_rtol"]),
            atol=float(spec["generation"]["correction_atol"]),
            max_step=period * float(spec["generation"]["correction_max_step_fraction"]),
        ),
    )
    length_scale, velocity_scale = _scales(initial, parameters)
    positions = trajectory.states[:, :9].reshape(-1, 3, 3)
    velocities = trajectory.states[:, 9:].reshape(-1, 3, 3)
    separations = np.concatenate(
        [
            np.linalg.norm(positions[:, first] - positions[:, second], axis=1)
            for first, second in ((0, 1), (0, 2), (1, 2))
        ]
    )
    drift = measure_invariant_drift(trajectory.states, parameters)
    metrics = {
        "closure_position_scaled": float(
            np.max(np.linalg.norm(positions[-1] - initial.positions, axis=1))
            / length_scale
        ),
        "closure_velocity_scaled": float(
            np.max(np.linalg.norm(velocities[-1] - initial.velocities, axis=1))
            / velocity_scale
        ),
        "relative_energy_drift": drift.max_relative_energy,
        "linear_momentum_drift_scaled": drift.max_linear_momentum
        / (parameters.total_mass * velocity_scale),
        "angular_momentum_drift_scaled": drift.max_angular_momentum
        / (parameters.total_mass * length_scale * velocity_scale),
        "minimum_pair_separation_scaled": float(np.min(separations) / length_scale),
    }
    if rebound:
        reference = propagate_rebound_ias15(
            initial,
            times,
            parameters,
            config=IAS15Config(
                epsilon=float(spec["execution"]["rebound_epsilon"]),
                adaptive_mode="prs23",
            ),
        )
        reference_positions = reference.states[:, :9].reshape(-1, 3, 3)
        reference_velocities = reference.states[:, 9:].reshape(-1, 3, 3)
        metrics["dop853_rebound_position_error_scaled"] = float(
            np.max(np.linalg.norm(positions - reference_positions, axis=2))
            / length_scale
        )
        metrics["dop853_rebound_velocity_error_scaled"] = float(
            np.max(np.linalg.norm(velocities - reference_velocities, axis=2))
            / velocity_scale
        )
    return metrics


def _evaluate_case(
    work: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]
) -> dict[str, Any]:
    case, candidate, spec = work
    native = _candidate_parameters(candidate)
    external = np.array([case[name] for name in ("x1", "v1", "v2")], dtype=np.float64)
    native_vector = np.array([native[name] for name in ("x1", "v1", "v2")])
    parameter_error = float(
        np.max(np.abs(native_vector - external))
        / max(1.0, float(np.max(np.abs(external))))
    )
    stability = candidate.get("stability")
    if stability is None:
        raise RuntimeError("candidate lacks a stability payload")
    label = str(stability["label"])
    metrics = _trajectory_metrics(
        candidate, spec, rebound=bool(case["rebound_selected"])
    )
    metrics.update(
        {
            "exact_mass_match": float(
                abs(native["m1"] - float(case["m1"])) <= 5.0e-13
                and abs(native["m2"] - float(case["m2"])) <= 5.0e-13
                and abs(native["m3"] - float(case["m3"])) <= 5.0e-13
            ),
            "external_parameter_error": parameter_error,
            "external_period_relative_error": abs(native["period"] - case["period"])
            / abs(float(case["period"])),
            "planar_stability_classified": float(label in {"S", "U"}),
            "planar_stability_label_agreement": float(
                label in {"S", "U"} and label == case["source_stability"]
            ),
        }
    )
    return {
        "case_id": case["case_id"],
        "candidate_id": candidate["candidate_id"],
        "source_line": case["source_line"],
        "source_stability": case["source_stability"],
        "native_stability": label,
        "rebound_selected": bool(case["rebound_selected"]),
        "success": bool(all(np.isfinite(value) for value in metrics.values())),
        "metrics": metrics,
    }


def _evaluate_case_safe(
    work: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]
) -> dict[str, Any]:
    case, candidate, _ = work
    try:
        return _evaluate_case(work)
    except Exception as error:
        return {
            "case_id": case["case_id"],
            "candidate_id": candidate["candidate_id"],
            "source_line": case["source_line"],
            "source_stability": case["source_stability"],
            "rebound_selected": bool(case["rebound_selected"]),
            "success": False,
            "error": f"{type(error).__name__}: {error}",
            "metrics": {},
        }


def _catalogue_metrics(
    catalogue: dict[str, Any], corpus: dict[str, Any]
) -> tuple[dict[str, float | int], dict[tuple[float, float], dict[str, Any]]]:
    candidates = catalogue["candidates"]
    by_mass: dict[tuple[float, float], dict[str, Any]] = {}
    candidate_ids = []
    successful = 0
    closure_position = []
    closure_velocity = []
    symplectic = []
    reciprocal = []
    for candidate in candidates:
        parameters = _candidate_parameters(candidate)
        key = (round(parameters["m1"], 12), round(parameters["m2"], 12))
        by_mass[key] = candidate
        candidate_ids.append(candidate["candidate_id"])
        stability = candidate.get("stability")
        correction = candidate["correction"]
        state = InertialState(np.array([from_hex(value) for value in candidate["state18"]]))
        system = SystemParameters(np.array([parameters["m1"], parameters["m2"], 1.0]))
        length, velocity = _scales(state, system)
        closure_position.append(from_hex(correction["position_closure_linf"]) / length)
        closure_velocity.append(from_hex(correction["velocity_closure_linf"]) / velocity)
        if correction["success"] and stability is not None:
            successful += 1
        if stability is not None:
            symplectic.append(from_hex(stability["symplectic_defect"]))
            reciprocal.append(from_hex(stability["reciprocal_pair_error"]))

    case_ids_by_split = {
        split: {case["case_id"] for case in corpus["cases"] if case["split"] == split}
        for split in ("development", "calibration", "holdout")
    }
    union = set().union(*case_ids_by_split.values())
    disjoint = sum(len(values) for values in case_ids_by_split.values()) == len(union)
    matched = sum(
        (round(float(case["m1"]), 12), round(float(case["m2"]), 12)) in by_mass
        for case in corpus["cases"]
    )
    duplicates = max(
        len(candidates) - len(set(candidate_ids)), len(candidates) - len(by_mass)
    )
    provenance = catalogue["provenance"]
    metrics: dict[str, float | int] = {
        "candidate_count": len(candidates),
        "candidate_success_rate": successful / len(candidates),
        "external_seed_count": int(provenance["external_seed_count"]),
        "evaluation_row_used_as_seed_count": int(
            provenance["evaluation_rows_used_as_seeds"]
        ),
        "stored_closure_position_scaled_max": max(closure_position),
        "stored_closure_velocity_scaled_max": max(closure_velocity),
        "monodromy_symplectic_defect_max": max(symplectic),
        "monodromy_reciprocal_pair_error_max": max(reciprocal),
        "partition_disjoint_rate": float(disjoint and len(union) == len(corpus["cases"])),
        "one_to_one_match_rate": matched / len(corpus["cases"]),
        "duplicate_count": duplicates,
    }
    return metrics, by_mass


def main() -> None:
    args = _args()
    if args.workers <= 0:
        raise ValueError("workers must be positive")
    output = Path(args.output).resolve()
    spec = load_json(args.spec)
    corpus = load_json(args.corpus)
    catalogue = load_json(args.catalogue)
    execution_runtime = runtime_fingerprint()
    specification_lock = verify_specification_lock(args.spec)
    candidate_lock = verify_candidate_lock(
        args.candidate_lock, args.catalogue, args.spec
    )
    if corpus["spec_sha256"] != sha256_file(args.spec):
        raise RuntimeError("external corpus uses another specification")
    if corpus["candidate_lock_sha256"] != candidate_lock["candidate_lock_sha256"]:
        raise RuntimeError("external corpus uses another candidate lock")
    if corpus["native_catalogue_file_sha256"] != sha256_file(args.catalogue):
        raise RuntimeError("external corpus uses another native catalogue")
    if corpus.get("campaign") != spec["campaign"]:
        raise RuntimeError("external corpus campaign mismatch")
    corpus_ids = [str(case.get("case_id", "")) for case in corpus.get("cases", [])]
    if (
        len(corpus_ids) != int(spec["execution"]["expected_external_case_count"])
        or any(not case_id for case_id in corpus_ids)
        or len(set(corpus_ids)) != len(corpus_ids)
    ):
        raise RuntimeError("external corpus case IDs are incomplete or non-unique")

    full_lock = None
    if args.split == "holdout":
        if not args.lock:
            raise RuntimeError("holdout execution requires the full qualification lock")
        if output.exists():
            raise RuntimeError("refusing to execute the WP1-CAT-N3BP holdout twice")
        full_lock = verify_lock(args.lock, ROOT, expected_prefix=spec["campaign"])
        require_full_lock_runtime(full_lock, execution_runtime)
        if full_lock["spec_sha256"] != sha256_file(args.spec):
            raise RuntimeError("holdout specification differs from full lock")
        if full_lock["corpus_sha256"] != sha256_file(args.corpus):
            raise RuntimeError("holdout corpus differs from full lock")
        expected_holdout_ids = sorted(
            case["case_id"]
            for case in corpus["cases"]
            if case.get("split") == "holdout"
        )
        if expected_holdout_ids != full_lock.get("holdout_ids"):
            raise RuntimeError("holdout case IDs differ from the full lock")

    prerequisite = verify_prerequisite(spec)
    catalogue_metrics, by_mass = _catalogue_metrics(catalogue, corpus)
    selected_cases = [case for case in corpus["cases"] if case["split"] == args.split]
    work = []
    for case in selected_cases:
        key = (round(float(case["m1"]), 12), round(float(case["m2"]), 12))
        if key not in by_mass:
            raise RuntimeError(f"no exact native candidate for {case['case_id']}")
        work.append((case, by_mass[key], spec))
    if args.workers == 1:
        evaluated = map(_evaluate_case_safe, work)
        cases = list(evaluated)
    else:
        try:
            executor = ProcessPoolExecutor(max_workers=args.workers)
        except PermissionError:
            executor = ThreadPoolExecutor(max_workers=args.workers)
        with executor:
            cases = list(executor.map(_evaluate_case_safe, work))

    root_metrics = None
    if args.split == "development":
        root = by_mass[(1.0, 1.0)]
        root_metrics = _trajectory_metrics(root, spec, rebound=False)
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "split": args.split,
        "generated_utc": utc_now(),
        "spec_sha256": sha256_file(args.spec),
        "specification_lock_sha256": specification_lock[
            "specification_lock_sha256"
        ],
        "corpus_sha256": sha256_file(args.corpus),
        "catalogue_sha256": sha256_file(args.catalogue),
        "candidate_lock_sha256": candidate_lock["candidate_lock_sha256"],
        "prerequisite": prerequisite,
        "runtime": execution_runtime,
        "rebound_distribution_version": importlib.metadata.version("rebound"),
        "catalogue_metrics": catalogue_metrics,
        "root_native_metrics": root_metrics,
        "structural": {
            "structural_blind_holdout": 0,
            "structural_independent_root_discovery": 0,
            "structural_general_n3bp_catalogue": 0,
        },
        "cases": cases,
    }
    if full_lock is not None:
        payload["qualification_id"] = full_lock["qualification_id"]
        payload["lock_sha256"] = full_lock["lock_sha256"]
    atomic_write_json(output, payload)
    print(
        f"WP1-CAT-N3BP-v1 {args.split}: "
        f"{sum(case['success'] for case in cases)}/{len(cases)} cases"
    )


if __name__ == "__main__":
    main()
