#!/usr/bin/env python
"""Execute one WP2KSQ-v1 split without exposing other split outputs."""

from __future__ import annotations

import argparse
import importlib.metadata
from pathlib import Path
import sys
from typing import Any

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
CAMPAIGN_ROOT = Path(__file__).resolve().parents[1]
for path in (
    REPO_ROOT,
    VALIDATION_ROOT,
    CAMPAIGN_ROOT / "scripts",
    CAMPAIGN_ROOT / "evaluation",
):
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
from kepler_benchmarks import KeplerBenchmark  # noqa: E402
from kepler_reference import EllipticElements  # noqa: E402
from ks_benchmark_evaluator import evaluate_ks_benchmark  # noqa: E402
from src.python.ks import (  # noqa: E402
    KSPhaseState,
    KeplerPhaseState,
    NegativeEnergyKSSystem,
    canonical_poisson_matrix,
    ks_position,
    lift_cotangent,
    project_cotangent,
    projected_poisson_matrix,
    s1_action,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument(
        "--split", choices=("development", "calibration", "holdout"), required=True
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--lock")
    return parser.parse_args()


def structural_metrics(seed: int, count: int) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    radius_error = 0.0
    s1_error = 0.0
    roundtrip_error = 0.0
    poisson_error = 0.0
    canonical = canonical_poisson_matrix(3)
    for _ in range(count):
        q = rng.normal(size=4)
        q *= rng.uniform(0.2, 3.0) / np.linalg.norm(q)
        radius_error = max(
            radius_error,
            abs(np.linalg.norm(ks_position(q)) - float(np.dot(q, q))),
        )

        direction = rng.normal(size=3)
        direction /= np.linalg.norm(direction)
        x = direction * rng.uniform(0.2, 4.0)
        p = rng.normal(scale=1.5, size=3)
        physical = KeplerPhaseState(x, p)
        lifted = lift_cotangent(physical, angle=rng.uniform(-np.pi, np.pi))
        transformed = s1_action(lifted, rng.uniform(-4.0 * np.pi, 4.0 * np.pi))
        reduced = project_cotangent(transformed).as_vector()
        s1_error = max(s1_error, float(np.max(np.abs(reduced - physical.as_vector()))))
        roundtrip_error = max(
            roundtrip_error,
            float(
                np.max(
                    np.abs(project_cotangent(lifted).as_vector() - physical.as_vector())
                )
            ),
        )
        poisson_error = max(
            poisson_error,
            float(np.max(np.abs(projected_poisson_matrix(lifted) - canonical))),
        )
    return {
        "radius_error_max": radius_error,
        "s1_invariance_error_max": s1_error,
        "cotangent_roundtrip_error_max": roundtrip_error,
        "poisson_error_max": poisson_error,
    }


def elliptic_case(case: dict[str, Any]) -> dict[str, Any]:
    benchmark = KeplerBenchmark(
        case_id=str(case["case_id"]),
        description=str(case["description"]),
        elements=EllipticElements(**case["elements"]),
        period_fractions=tuple(float(item) for item in case["period_fractions"]),
        reduced_mass=float(case["reduced_mass"]),
    )
    evaluation = evaluate_ks_benchmark(benchmark)
    return {
        "case_id": benchmark.case_id,
        "case_type": "elliptic",
        "success": True,
        "metrics": evaluation.metrics,
        "rebound_version": evaluation.rebound_version,
    }


def radial_case(case: dict[str, Any]) -> dict[str, Any]:
    reduced_mass = float(case["reduced_mass"])
    kappa = float(case["kappa"])
    apocenter = float(case["apocenter"])
    energy = -kappa / apocenter
    system = NegativeEnergyKSSystem(
        kappa=kappa,
        energy=energy,
        reduced_mass=reduced_mass,
    )
    initial = lift_cotangent(
        KeplerPhaseState(np.array([0.0, 0.0, apocenter]), np.zeros(3))
    )
    collision_s = np.pi / (2.0 * system.angular_frequency)
    offset = float(case["sample_offset_s"])
    q_values, Q_values = system.flow(
        initial, collision_s + np.array([-offset, 0.0, offset])
    )
    hamiltonian = np.array(
        [
            system.regularized_hamiltonian(KSPhaseState(q, Q))
            for q, Q in zip(q_values, Q_values, strict=True)
        ]
    )
    metrics = {
        "collision_q_norm": float(np.linalg.norm(q_values[1])),
        "collision_Q_norm": float(np.linalg.norm(Q_values[1])),
        "symmetry_error": float(
            np.max(np.abs(ks_position(q_values[0]) - ks_position(q_values[2])))
        ),
        "regularized_hamiltonian_abs_max": float(np.max(np.abs(hamiltonian))),
        "finite_regular_state": float(
            np.all(np.isfinite(q_values)) and np.all(np.isfinite(Q_values))
        ),
    }
    return {
        "case_id": str(case["case_id"]),
        "case_type": "radial_collision",
        "success": bool(metrics["finite_regular_state"] and metrics["collision_Q_norm"] > 0),
        "metrics": metrics,
    }


def main() -> None:
    args = parse_args()
    output = Path(args.output).resolve()
    lock_payload = None
    if args.split == "holdout":
        if not args.lock:
            raise RuntimeError("holdout execution requires a qualification lock")
        if output.exists():
            raise RuntimeError("refusing to execute the WP2 holdout more than once")
        lock_payload = verify_lock(args.lock, REPO_ROOT, expected_prefix="WP2KSQ-v1")

    spec = load_json(args.spec)
    corpus = load_json(args.corpus)
    if lock_payload is not None:
        if lock_payload["spec_sha256"] != sha256_file(args.spec):
            raise RuntimeError("holdout specification does not match the lock")
        if lock_payload["corpus_sha256"] != sha256_file(args.corpus):
            raise RuntimeError("holdout corpus does not match the lock")

    cases = [case for case in corpus["cases"] if case["split"] == args.split]
    if not cases:
        raise RuntimeError(f"no {args.split} cases in the qualification corpus")
    results: list[dict[str, Any]] = []
    for case in cases:
        try:
            if case["case_type"] == "elliptic":
                results.append(elliptic_case(case))
            elif case["case_type"] == "radial_collision":
                results.append(radial_case(case))
            else:
                raise ValueError(f"unsupported case type: {case['case_type']}")
        except Exception as error:
            results.append(
                {
                    "case_id": str(case["case_id"]),
                    "case_type": str(case["case_type"]),
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
        "runtime": runtime_fingerprint(),
        "rebound_distribution_version": importlib.metadata.version("rebound"),
        "structural_metrics": structural_metrics(
            int(spec["execution"]["structural_seed_by_split"][args.split]),
            int(spec["execution"]["structural_random_cases_per_split"]),
        ),
        "cases": results,
    }
    if lock_payload is not None:
        payload["qualification_id"] = lock_payload["qualification_id"]
        payload["lock_sha256"] = lock_payload["lock_sha256"]
    atomic_write_json(output, payload)
    print(f"WP2KSQ-v1 {args.split}: {sum(item['success'] for item in results)}/{len(results)} cases")


if __name__ == "__main__":
    main()
