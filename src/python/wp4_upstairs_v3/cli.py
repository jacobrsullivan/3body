"""Freeze, execute, and verify WP4-UP-READY-v3."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from src.python.wp4_upstairs_v2.harness import evaluate_readiness

from .integrity import (
    atomic_write_json,
    build_readiness_lock_v3,
    canonical_json,
    load_json,
    make_gate,
    runtime_fingerprint,
    sha256_bytes,
    sha256_file,
    verify_signed_lock,
    verify_wp2_prerequisite,
    verify_wp3_v3_null_result,
    utc_now,
)


ROOT = Path(__file__).resolve().parents[3]
CAMPAIGN = ROOT / "validation-external/wp4-upstairs-readiness-v3"
SPEC_PATH = CAMPAIGN / "qualification_spec.json"
LOCK_PATH = CAMPAIGN / "reports/wp4_upstairs_v3_readiness_lock.json"
RESULTS_PATH = CAMPAIGN / "results/readiness_results.json"
RECORD_PATH = CAMPAIGN / "reports/wp4_upstairs_v3_readiness_record.json"
REPORT_PATH = CAMPAIGN / "reports/wp4_upstairs_v3_readiness_report.md"

FROZEN_SCOPES = (
    "src/python/ks",
    "src/python/n3bp_qualification",
    "src/python/pairwise_ks",
    "src/python/threebody_flow",
    "src/python/threebody_reduction",
    "src/python/upstairs_ks",
    "src/python/wp4_upstairs_v2",
    "src/python/wp4_upstairs_v3",
    "tests/wp4_upstairs_v3",
    "validation-external/wp4-upstairs-readiness-v3/README.md",
    "validation-external/wp4-upstairs-readiness-v3/qualification_spec.json",
    "validation-external/wp4-upstairs-readiness-v3/run_qualification.sh",
    "validation-external/wp4-upstairs-readiness-v3/scripts",
    "notes/wp4-upstairs-v3-readiness-plan.md",
)
OUTPUT_PATHS = (
    "validation-external/wp4-upstairs-readiness-v3/reports/wp4_upstairs_v3_readiness_lock.json",
    "validation-external/wp4-upstairs-readiness-v3/results/readiness_results.json",
    "validation-external/wp4-upstairs-readiness-v3/reports/wp4_upstairs_v3_readiness_record.json",
    "validation-external/wp4-upstairs-readiness-v3/reports/wp4_upstairs_v3_readiness_report.md",
)


def _spec() -> dict[str, Any]:
    overlay = load_json(SPEC_PATH)
    base_path = ROOT / overlay["base_control_spec"]["path"]
    if sha256_file(base_path) != overlay["base_control_spec"]["sha256"]:
        raise RuntimeError("WP4-v3 base control specification changed")
    effective = load_json(base_path)
    for name in (
        "campaign",
        "specification_status",
        "claim",
        "evidence_boundary",
        "prerequisites",
        "staged_policy",
    ):
        effective[name] = overlay[name]
    effective["base_control_spec"] = overlay["base_control_spec"]
    return effective


def _external_paths(spec: dict[str, Any]) -> tuple[str, ...]:
    wp2 = spec["prerequisites"]["wp2_upstairs"]
    wp3 = spec["prerequisites"]["wp3_upstairs_search"]
    return (
        spec["base_control_spec"]["path"],
        wp2["record_path"],
        wp2["lock_path"],
        wp3["search_lock_path"],
        wp3["search_record_path"],
        wp3["search_results_path"],
        wp3["staged_gate_path"],
        wp3["candidate_decision_path"],
        wp3["candidate_protocol_path"],
        wp3["publication_reserve_path"],
    )


def freeze() -> dict[str, Any]:
    spec = _spec()
    wp2 = verify_wp2_prerequisite(ROOT, spec["prerequisites"]["wp2_upstairs"])
    wp3 = verify_wp3_v3_null_result(ROOT, spec["prerequisites"]["wp3_upstairs_search"])
    lock = build_readiness_lock_v3(
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


def _apply_gates(
    raw: dict[str, Any],
    spec: dict[str, Any],
    wp3: dict[str, Any],
) -> list[dict[str, Any]]:
    metrics = dict(raw["metrics"])
    metrics.update(
        {
            "wp2_prerequisite_verified": 1,
            "wp3_candidate_count": int(wp3["candidate_count"]),
            "wp3_candidate_not_triggered": int(
                wp3["candidate_status"] == "NOT_TRIGGERED"
            ),
            "publication_reserve_sealed": int(
                wp3["publication_reserve_status"] == "SEALED_UNEXECUTED"
            ),
        }
    )
    return [
        make_gate(
            definition["name"],
            metrics[definition["metric"]],
            definition["comparator"],
            definition["threshold"],
        )
        for definition in spec["gates"]
    ]


def _render_report(record: dict[str, Any]) -> str:
    metrics = record["metrics"]
    passed = sum(gate["passed"] for gate in record["gates"])
    return "\n".join(
        [
            "# WP4 Upstairs Readiness Qualification v3",
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
            "The gauntlet accepted `K_h`, `Xi`, `Lx`, `Ly`, and `Lz`; rejected `q0` as nonconserved and gauge variant; and rejected `2 K_h - 3 Xi` as functionally dependent.",
            "",
            "## Key Metrics",
            "",
            f"- Deterministic states: `{metrics['deterministic_state_count']}`",
            f"- Maximum positive-control scaled Lie derivative: `{metrics['positive_control_lie_scaled_max']:.16e}`",
            f"- Minimum false-coordinate scaled Lie derivative: `{metrics['negative_coordinate_lie_scaled_min']:.16e}`",
            f"- Maximum angular-momentum Poisson residual: `{metrics['angular_momentum_so3_abs_max']:.16e}`",
            f"- Minimum known functional rank: `{metrics['known_functional_rank_min']}`",
            f"- Maximum positive-control trajectory drift: `{metrics['positive_trajectory_drift_scaled_max']:.16e}`",
            "",
            "## Claim Boundary",
            "",
            record["evidence_boundary"],
            "",
            "No candidate expression was supplied or evaluated. No reserve data was read, and no Morales-Ramis computation was run.",
            "",
        ]
    )


def run() -> dict[str, Any]:
    spec = _spec()
    lock = verify_signed_lock(LOCK_PATH, ROOT)
    if lock["spec_sha256"] != sha256_file(SPEC_PATH):
        raise RuntimeError("WP4-v3 readiness lock/spec mismatch")
    runtime = runtime_fingerprint()
    if runtime != lock["runtime"]:
        raise RuntimeError("WP4-v3 decision runtime differs from frozen runtime")
    wp2 = verify_wp2_prerequisite(ROOT, spec["prerequisites"]["wp2_upstairs"])
    wp3 = verify_wp3_v3_null_result(ROOT, spec["prerequisites"]["wp3_upstairs_search"])
    if wp2 != lock["wp2_upstairs_prerequisite"] or wp3 != lock["wp3_upstairs_state"]:
        raise RuntimeError("WP4-v3 prerequisite changed after freeze")

    raw = evaluate_readiness(spec)
    raw.update(
        {
            "generated_utc": utc_now(),
            "qualification_id": lock["qualification_id"],
            "lock_sha256": lock["lock_sha256"],
            "spec_sha256": sha256_file(SPEC_PATH),
            "runtime": runtime,
            "wp2_upstairs_prerequisite": wp2,
            "wp3_upstairs_state": wp3,
        }
    )
    atomic_write_json(RESULTS_PATH, raw)
    gates = _apply_gates(raw, spec, wp3)
    harness_status = (
        "HARNESS_READY" if all(gate["passed"] for gate in gates) else "HARNESS_NOT_READY"
    )
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
        "runtime": runtime,
    }
    record["record_payload_sha256"] = sha256_bytes(canonical_json(record))
    atomic_write_json(RECORD_PATH, record)
    REPORT_PATH.write_text(_render_report(record), encoding="utf-8")
    if harness_status != "HARNESS_READY":
        raise RuntimeError("WP4-v3 readiness gates did not all pass")
    return record


def verify() -> dict[str, Any]:
    lock = verify_signed_lock(LOCK_PATH, ROOT)
    record = load_json(RECORD_PATH)
    recorded_payload = record.pop("record_payload_sha256")
    if sha256_bytes(canonical_json(record)) != recorded_payload:
        raise RuntimeError("WP4-v3 readiness record payload integrity failure")
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
        and record["runtime"] == lock["runtime"]
        and all(gate["passed"] for gate in record["gates"])
        and record["results_sha256"] == sha256_file(RESULTS_PATH)
    ):
        raise RuntimeError("WP4-v3 readiness record contract failure")
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
