"""Freeze, execute, and verify the WP4 upstairs readiness qualification."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from .harness import evaluate_readiness
from .integrity import (
    atomic_write_json,
    build_readiness_lock,
    canonical_json,
    load_json,
    make_gate,
    runtime_fingerprint,
    sha256_bytes,
    sha256_file,
    utc_now,
    verify_signed_lock,
    verify_wp2_prerequisite,
    verify_wp3_null_result,
)


ROOT = Path(__file__).resolve().parents[3]
CAMPAIGN = ROOT / "validation-external/wp4-upstairs-readiness-v2"
SPEC_PATH = CAMPAIGN / "qualification_spec.json"
LOCK_PATH = CAMPAIGN / "reports/wp4_upstairs_v2_readiness_lock.json"
RESULTS_PATH = CAMPAIGN / "results/readiness_results.json"
RECORD_PATH = CAMPAIGN / "reports/wp4_upstairs_v2_readiness_record.json"
REPORT_PATH = CAMPAIGN / "reports/wp4_upstairs_v2_readiness_report.md"

FROZEN_SCOPES = (
    "src/python/wp4_upstairs_v2",
    "tests/wp4_upstairs_v2",
    "validation-external/wp4-upstairs-readiness-v2/README.md",
    "validation-external/wp4-upstairs-readiness-v2/qualification_spec.json",
    "validation-external/wp4-upstairs-readiness-v2/run_qualification.sh",
    "validation-external/wp4-upstairs-readiness-v2/scripts",
    "notes/wp4-upstairs-v2-readiness-plan.md",
)
OUTPUT_PATHS = (
    "validation-external/wp4-upstairs-readiness-v2/reports/wp4_upstairs_v2_readiness_lock.json",
    "validation-external/wp4-upstairs-readiness-v2/results/readiness_results.json",
    "validation-external/wp4-upstairs-readiness-v2/reports/wp4_upstairs_v2_readiness_record.json",
    "validation-external/wp4-upstairs-readiness-v2/reports/wp4_upstairs_v2_readiness_report.md",
)


def _spec() -> dict[str, Any]:
    return load_json(SPEC_PATH)


def _external_paths(spec: dict[str, Any]) -> tuple[str, ...]:
    wp2 = spec["prerequisites"]["wp2_upstairs"]
    wp3 = spec["prerequisites"]["wp3_upstairs_search"]
    return (
        wp2["record_path"],
        wp2["lock_path"],
        "src/python/upstairs_ks/QUALIFICATION_BOUNDARY.md",
        "src/python/upstairs_ks/__init__.py",
        "src/python/upstairs_ks/model.py",
        wp3["search_lock_path"],
        wp3["search_record_path"],
        wp3["search_results_path"],
        wp3["staged_gate_path"],
        wp3["candidate_decision_path"],
        wp3["publication_reserve_path"],
    )


def freeze() -> dict[str, Any]:
    spec = _spec()
    wp2 = verify_wp2_prerequisite(ROOT, spec["prerequisites"]["wp2_upstairs"])
    wp3 = verify_wp3_null_result(ROOT, spec["prerequisites"]["wp3_upstairs_search"])
    lock = build_readiness_lock(
        root=ROOT,
        spec_path=SPEC_PATH,
        scopes=FROZEN_SCOPES,
        external_paths=_external_paths(spec),
        output_paths=OUTPUT_PATHS,
        prerequisite=wp2,
        wp3_state=wp3,
    )
    atomic_write_json(LOCK_PATH, lock)
    return lock


def _apply_gates(raw: dict[str, Any], spec: dict[str, Any], wp3: dict[str, Any]) -> list[dict[str, Any]]:
    metrics = dict(raw["metrics"])
    metrics.update({
        "wp2_prerequisite_verified": 1,
        "wp3_candidate_count": int(wp3["candidate_count"]),
        "wp3_candidate_not_triggered": int(wp3["candidate_status"] == "NOT_TRIGGERED"),
        "publication_reserve_sealed": int(
            wp3["publication_reserve_status"] == "SEALED_UNEXECUTED"
        ),
    })
    gates = []
    for definition in spec["gates"]:
        gates.append(make_gate(
            definition["name"],
            metrics[definition["metric"]],
            definition["comparator"],
            definition["threshold"],
        ))
    return gates


def _render_report(record: dict[str, Any]) -> str:
    metrics = record["metrics"]
    passed = sum(gate["passed"] for gate in record["gates"])
    lines = [
        "# WP4 Upstairs Readiness Qualification v2",
        "",
        "## Decision",
        "",
        f"- Harness status: **{record['harness_status']}**",
        f"- Candidate validation: **{record['candidate_validation_status']}**",
        f"- Candidate-specific sealed qualification: **{record['sealed_qualification_status']}**",
        f"- Morales-Ramis: **{record['morales_ramis_status']}**",
        f"- Publication reserve: **{record['publication_reserve_status']}**",
        f"- Gates: **{passed}/{len(record['gates'])} passed**",
        "",
        "## Control Result",
        "",
        "The gauntlet accepted the known upstairs controls `K_h`, `Xi`, `Lx`, `Ly`, and `Lz`.",
        "It rejected `q0` as nonconserved and gauge variant, and rejected `2 K_h - 3 Xi`",
        "because adding it did not increase functional rank.",
        "",
        "## Key Metrics",
        "",
        f"- Deterministic states: `{metrics['deterministic_state_count']}`",
        f"- Maximum positive-control scaled Lie derivative: `{metrics['positive_control_lie_scaled_max']:.16e}`",
        f"- Minimum false-coordinate scaled Lie derivative: `{metrics['negative_coordinate_lie_scaled_min']:.16e}`",
        f"- Maximum Hamiltonian-vector-field residual: `{metrics['hamiltonian_vector_field_scaled_max']:.16e}`",
        f"- Maximum angular-momentum Poisson-algebra residual: `{metrics['angular_momentum_so3_abs_max']:.16e}`",
        f"- Minimum known functional rank: `{metrics['known_functional_rank_min']}`",
        f"- Dependent-control rank increment: `{metrics['dependent_rank_increment_max']}`",
        f"- Maximum positive-control trajectory drift: `{metrics['positive_trajectory_drift_scaled_max']:.16e}`",
        f"- Minimum false-coordinate trajectory drift: `{metrics['negative_coordinate_trajectory_drift_scaled_min']:.16e}`",
        "",
        "## Claim Boundary",
        "",
        record["evidence_boundary"],
        "",
        "No candidate expression was supplied or evaluated. No reserve data was read, and no",
        "Morales-Ramis computation was run.",
        "",
    ]
    return "\n".join(lines)


def run() -> dict[str, Any]:
    spec = _spec()
    lock = verify_signed_lock(LOCK_PATH, ROOT)
    if lock["spec_sha256"] != sha256_file(SPEC_PATH):
        raise RuntimeError("WP4 readiness lock/spec mismatch")
    wp2 = verify_wp2_prerequisite(ROOT, spec["prerequisites"]["wp2_upstairs"])
    wp3 = verify_wp3_null_result(ROOT, spec["prerequisites"]["wp3_upstairs_search"])
    if wp2 != lock["wp2_upstairs_prerequisite"] or wp3 != lock["wp3_upstairs_state"]:
        raise RuntimeError("WP4 readiness prerequisite changed after freeze")

    raw = evaluate_readiness(spec)
    raw.update({
        "generated_utc": utc_now(),
        "qualification_id": lock["qualification_id"],
        "lock_sha256": lock["lock_sha256"],
        "spec_sha256": sha256_file(SPEC_PATH),
        "runtime": runtime_fingerprint(),
        "wp2_upstairs_prerequisite": wp2,
        "wp3_upstairs_state": wp3,
    })
    atomic_write_json(RESULTS_PATH, raw)
    gates = _apply_gates(raw, spec, wp3)
    harness_status = "HARNESS_READY" if all(gate["passed"] for gate in gates) else "HARNESS_NOT_READY"
    record: dict[str, Any] = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "qualification_id": lock["qualification_id"],
        "generated_utc": utc_now(),
        "harness_status": harness_status,
        "candidate_validation_status": "CANDIDATE_NOT_TRIGGERED",
        "sealed_qualification_status": "NOT_TRIGGERED",
        "morales_ramis_status": "NOT_TRIGGERED",
        "publication_reserve_status": wp3["publication_reserve_status"],
        "publication_reserve_open_attempts": 0,
        "candidate_count": 0,
        "claim": spec["claim"],
        "evidence_boundary": spec["evidence_boundary"],
        "wp2_upstairs_prerequisite": wp2,
        "wp3_upstairs_state": wp3,
        "lock_sha256": lock["lock_sha256"],
        "lock_file_sha256": sha256_file(LOCK_PATH),
        "spec_sha256": sha256_file(SPEC_PATH),
        "results_sha256": sha256_file(RESULTS_PATH),
        "metrics": raw["metrics"],
        "control_decisions": raw["controls"],
        "gates": gates,
        "runtime": runtime_fingerprint(),
    }
    record["record_payload_sha256"] = sha256_bytes(canonical_json(record))
    atomic_write_json(RECORD_PATH, record)
    REPORT_PATH.write_text(_render_report(record), encoding="utf-8")
    if harness_status != "HARNESS_READY":
        raise RuntimeError("WP4 upstairs readiness gates did not all pass")
    return record


def verify() -> dict[str, Any]:
    lock = verify_signed_lock(LOCK_PATH, ROOT)
    record = load_json(RECORD_PATH)
    recorded_payload = record.pop("record_payload_sha256")
    if sha256_bytes(canonical_json(record)) != recorded_payload:
        raise RuntimeError("WP4 readiness record payload integrity failure")
    record["record_payload_sha256"] = recorded_payload
    if not (
        record["qualification_id"] == lock["qualification_id"]
        and record["lock_sha256"] == lock["lock_sha256"]
        and record["harness_status"] == "HARNESS_READY"
        and record["candidate_validation_status"] == "CANDIDATE_NOT_TRIGGERED"
        and record["sealed_qualification_status"] == "NOT_TRIGGERED"
        and record["morales_ramis_status"] == "NOT_TRIGGERED"
        and record["publication_reserve_status"] == "SEALED_UNEXECUTED"
        and record["publication_reserve_open_attempts"] == 0
        and record["candidate_count"] == 0
        and all(gate["passed"] for gate in record["gates"])
        and record["results_sha256"] == sha256_file(RESULTS_PATH)
    ):
        raise RuntimeError("WP4 readiness record contract failure")
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze", "run", "verify"))
    args = parser.parse_args()
    if args.command == "freeze":
        payload = freeze()
        print(f"froze {payload['qualification_id']}")
    elif args.command == "run":
        payload = run()
        print(
            f"{payload['qualification_id']}: {payload['harness_status']} "
            f"({sum(g['passed'] for g in payload['gates'])}/{len(payload['gates'])} gates)"
        )
    else:
        payload = verify()
        print(f"verified {payload['qualification_id']}: {payload['harness_status']}")


if __name__ == "__main__":
    main()
