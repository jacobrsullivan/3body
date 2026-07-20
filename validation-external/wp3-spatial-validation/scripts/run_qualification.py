#!/usr/bin/env python
"""Execute one WP1Q-N3BP-SPATIAL-v1 qualification split."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys
from typing import Any

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
CAMPAIGN_ROOT = Path(__file__).resolve().parents[1]
for path in (REPO_ROOT, VALIDATION_ROOT, Path(__file__).resolve().parent):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from qualification_tools import (  # noqa: E402
    atomic_write_json,
    load_json,
    runtime_fingerprint,
    sha256_file,
    utc_now,
    verify_lock,
)
from spatial_reference import (  # noqa: E402
    case_scales,
    finite_time_lyapunov,
    integrate_taylor,
    parse_case,
    spatial_rank_ratio,
)
from src.python.n3bp_qualification import (  # noqa: E402
    DOP853Config,
    InertialState,
    SystemParameters,
    propagate_dop853,
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--selected-rows", required=True)
    parser.add_argument(
        "--split", choices=("development", "calibration", "holdout"), required=True
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--lock")
    return parser.parse_args()


def _selected_hashes(path: str | Path) -> set[str]:
    hashes: set[str] = set()
    with Path(path).open("r", encoding="ascii") as stream:
        for line in stream:
            stripped = line.rstrip("\n")
            if stripped and not stripped.startswith("#"):
                hashes.add(hashlib.sha256(stripped.encode("ascii")).hexdigest())
    return hashes


def _scaled_errors(
    first: np.ndarray,
    second: np.ndarray,
    length_scale: float,
    velocity_scale: float,
) -> tuple[float, float]:
    first_positions = first[..., :9].reshape(-1, 3, 3)
    second_positions = second[..., :9].reshape(-1, 3, 3)
    first_velocities = first[..., 9:].reshape(-1, 3, 3)
    second_velocities = second[..., 9:].reshape(-1, 3, 3)
    return (
        float(
            np.max(np.linalg.norm(first_positions - second_positions, axis=2))
            / length_scale
        ),
        float(
            np.max(np.linalg.norm(first_velocities - second_velocities, axis=2))
            / velocity_scale
        ),
    )


def _minimum_separation(states: np.ndarray, length_scale: float) -> float:
    positions = states[:, :9].reshape(-1, 3, 3)
    return min(
        float(np.min(np.linalg.norm(positions[:, first] - positions[:, second], axis=1)))
        / length_scale
        for first, second in ((0, 1), (0, 2), (1, 2))
    )


def _evaluate_case(
    case: dict[str, Any],
    spec: dict[str, Any],
    selected_hashes: set[str],
) -> dict[str, Any]:
    reference = parse_case(case)
    execution = spec["execution"]
    times = np.linspace(0.0, reference.duration, int(execution["checkpoint_count"]))
    low = integrate_taylor(
        case,
        times,
        precision_bits=int(execution["oracle_precision_bits_low"]),
        tolerance=str(execution["oracle_tolerance_low"]),
    )
    high = integrate_taylor(
        case,
        times,
        precision_bits=int(execution["oracle_precision_bits_high"]),
        tolerance=str(execution["oracle_tolerance_high"]),
    )
    parameters = SystemParameters(reference.masses, gravitational_constant=1.0)
    production = propagate_dop853(
        InertialState.from_components(reference.positions, reference.velocities),
        times,
        parameters,
        config=DOP853Config(
            rtol=float(execution["production_rtol"]),
            atol=float(execution["production_atol"]),
            max_step=float(execution["production_max_step"]),
        ),
    )
    length_scale, velocity_scale = case_scales(reference)
    low_high = _scaled_errors(
        low["states_float64"], high["states_float64"], length_scale, velocity_scale
    )
    high_brutus = _scaled_errors(
        high["states_float64"][-1:],
        reference.final_state.reshape(1, 18),
        length_scale,
        velocity_scale,
    )
    production_high_full = _scaled_errors(
        production.states,
        high["states_float64"],
        length_scale,
        velocity_scale,
    )
    production_checkpoint = int(execution["production_validation_checkpoint_index"])
    production_high_short = _scaled_errors(
        production.states[: production_checkpoint + 1],
        high["states_float64"][: production_checkpoint + 1],
        length_scale,
        velocity_scale,
    )
    ftle = finite_time_lyapunov(
        reference,
        total_duration=min(
            float(execution["variational_total_duration"]), reference.duration
        ),
        segment_duration=float(execution["variational_segment_duration"]),
        rtol=float(execution["variational_rtol"]),
        atol=float(execution["variational_atol"]),
    )
    metrics = {
        "source_precision_pass": int(
            float(case["brutus_tolerance_decimal"])
            <= float(spec["source_selection"]["source_tolerance_max"])
            and int(case["brutus_word_length_bits"])
            >= int(spec["source_selection"]["source_word_length_bits_min"])
        ),
        "source_payload_hash_pass": int(
            str(case["source_line_sha256"]) in selected_hashes
        ),
        "spatial_rank_ratio": spatial_rank_ratio(reference),
        "finite_time_lyapunov": ftle,
        "oracle_convergence_position_scaled": low_high[0],
        "oracle_convergence_velocity_scaled": low_high[1],
        "oracle_brutus_position_scaled": high_brutus[0],
        "oracle_brutus_velocity_scaled": high_brutus[1],
        "production_validation_horizon": float(times[production_checkpoint]),
        "production_oracle_short_position_scaled": production_high_short[0],
        "production_oracle_short_velocity_scaled": production_high_short[1],
        "production_oracle_full_position_scaled": production_high_full[0],
        "production_oracle_full_velocity_scaled": production_high_full[1],
        "oracle_relative_energy_drift": float(high["relative_energy_drift_decimal"]),
        "minimum_pair_separation_scaled": _minimum_separation(
            high["states_float64"], length_scale
        ),
    }
    return {
        "case_id": case["case_id"],
        "source_family": case["source_family"],
        "success": True,
        "metrics": metrics,
        "oracle": {
            "backend": "heyoka.real adaptive Taylor",
            "precision_bits": high["precision_bits"],
            "tolerance": high["tolerance"],
            "times_decimal": high["times_decimal"],
            "states_decimal": high["states_decimal"],
            "relative_energy_drift_decimal": high[
                "relative_energy_drift_decimal"
            ],
            "total_steps": high["total_steps"],
        },
    }


def main() -> None:
    args = _args()
    spec = load_json(args.spec)
    corpus = load_json(args.corpus)
    lock = None
    if args.split == "holdout":
        if not args.lock:
            raise RuntimeError("holdout execution requires a qualification lock")
        lock = verify_lock(args.lock, REPO_ROOT, expected_prefix=spec["campaign"])
    selected = _selected_hashes(args.selected_rows)
    cases = [case for case in corpus["cases"] if case["split"] == args.split]
    results = []
    for index, case in enumerate(cases, start=1):
        print(f"[{index}/{len(cases)}] {case['case_id']}", flush=True)
        try:
            results.append(_evaluate_case(case, spec, selected))
        except Exception as error:
            results.append(
                {
                    "case_id": case["case_id"],
                    "source_family": case["source_family"],
                    "success": False,
                    "error": f"{type(error).__name__}: {error}",
                    "metrics": {},
                }
            )
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "split": args.split,
        "generated_utc": utc_now(),
        "spec_sha256": sha256_file(args.spec),
        "corpus_sha256": sha256_file(args.corpus),
        "selected_rows_sha256": sha256_file(args.selected_rows),
        "runtime": runtime_fingerprint(),
        "cases": results,
    }
    if lock is not None:
        payload["qualification_id"] = lock["qualification_id"]
        payload["lock_sha256"] = lock["lock_sha256"]
    atomic_write_json(args.output, payload)
    failures = [item for item in results if not item["success"]]
    if failures:
        print(f"{len(failures)} cases failed", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
