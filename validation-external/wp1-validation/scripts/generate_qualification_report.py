#!/usr/bin/env python
"""Generate the final human- and machine-readable WP1 qualification decision."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from qualification_common import (
    atomic_write_json,
    canonical_json,
    load_json,
    load_spec,
    repository_root,
    sha256_bytes,
    sha256_file,
    verify_qualification_lock,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--lock", required=True)
    parser.add_argument("--corpus-manifest", required=True)
    parser.add_argument("--development", required=True)
    parser.add_argument("--calibration", required=True)
    parser.add_argument("--holdout", required=True)
    parser.add_argument("--linux-parity", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--record", required=True)
    return parser.parse_args()


def fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6e}"
    return str(value)


def gate_table(evaluation: dict[str, Any]) -> list[str]:
    lines = [
        "| Gate | Observed | Requirement | Result |",
        "|---|---:|---:|:---:|",
    ]
    for gate in evaluation["gates"]:
        lines.append(
            f"| `{gate['name']}` | {fmt(gate['observed'])} | "
            f"{gate['comparator']} {fmt(gate['threshold'])} | "
            f"{'PASS' if gate['passed'] else 'FAIL'} |"
        )
    return lines


def validate_evaluation(
    split: str,
    evaluation_path: Path,
    evaluation: dict[str, Any],
    spec_hash: str,
    corpus_manifest_hash: str,
    lock: dict[str, Any],
) -> None:
    if evaluation.get("split") != split:
        raise RuntimeError(f"Mislabeled qualification evaluation: {split}")
    if evaluation.get("spec_sha256") != spec_hash:
        raise RuntimeError(f"{split} evaluation does not use the frozen specification")
    if evaluation.get("corpus_manifest_sha256") != corpus_manifest_hash:
        raise RuntimeError(f"{split} evaluation does not use the frozen corpus")
    for name, expected in evaluation.get("input_hashes", {}).items():
        result_path = evaluation_path.parent / f"{split}_{name}.csv"
        if sha256_file(result_path) != expected:
            raise RuntimeError(f"{split} {name} results changed after evaluation")
    if split == "holdout":
        if evaluation.get("qualification_id") != lock["qualification_id"]:
            raise RuntimeError("Holdout evaluation has the wrong qualification ID")
        if evaluation.get("lock_sha256") != lock["lock_sha256"]:
            raise RuntimeError(
                "Holdout evaluation has the wrong qualification lock hash"
            )


def main() -> None:
    args = parse_args()
    spec_path = Path(args.spec).resolve()
    repo_root = repository_root(spec_path)
    spec = load_spec(spec_path)
    lock = verify_qualification_lock(args.lock, repo_root)
    corpus = load_json(args.corpus_manifest)
    linux_parity = load_json(args.linux_parity)
    if linux_parity.get("status") != "PASS":
        raise RuntimeError("Linux parity evidence is not passing")
    evaluation_paths = {
        "development": Path(args.development).resolve(),
        "calibration": Path(args.calibration).resolve(),
        "holdout": Path(args.holdout).resolve(),
    }
    evaluations = {split: load_json(path) for split, path in evaluation_paths.items()}
    spec_hash = sha256_file(spec_path)
    corpus_manifest_hash = sha256_file(args.corpus_manifest)
    if lock["spec_sha256"] != spec_hash:
        raise RuntimeError("Qualification lock does not match the specification")
    if lock["corpus_manifest_sha256"] != corpus_manifest_hash:
        raise RuntimeError("Qualification lock does not match the corpus manifest")
    if lock["corpus_sha256"] != corpus["corpus_sha256"]:
        raise RuntimeError("Qualification lock does not match the corpus content")
    for split, evaluation in evaluations.items():
        validate_evaluation(
            split,
            evaluation_paths[split],
            evaluation,
            spec_hash,
            corpus_manifest_hash,
            lock,
        )
    status = (
        "PASS"
        if all(evaluation["status"] == "PASS" for evaluation in evaluations.values())
        else "FAIL"
    )
    generated = datetime.now(timezone.utc).isoformat()
    evidence_paths = {
        "spec": Path(args.spec).resolve(),
        "lock": Path(args.lock).resolve(),
        "corpus_manifest": Path(args.corpus_manifest).resolve(),
        "development_evaluation": Path(args.development).resolve(),
        "calibration_evaluation": Path(args.calibration).resolve(),
        "holdout_evaluation": Path(args.holdout).resolve(),
        "linux_parity": Path(args.linux_parity).resolve(),
    }
    evidence_files = {
        name: {
            "path": path.relative_to(repo_root).as_posix(),
            "sha256": sha256_file(path),
        }
        for name, path in evidence_paths.items()
    }
    evidence_hashes = {name: item["sha256"] for name, item in evidence_files.items()}

    record = {
        "schema_version": "1.0",
        "generated_utc": generated,
        "qualification_id": lock["qualification_id"],
        "status": status,
        "claim": spec["claim"],
        "evidence_boundary": spec["evidence_boundary"],
        "lock_sha256": lock["lock_sha256"],
        "code_snapshot_sha256": lock["code_snapshot_sha256"],
        "base_git_commit": lock["base_git_commit"],
        "spec_sha256": lock["spec_sha256"],
        "corpus_sha256": lock["corpus_sha256"],
        "external_source": spec["external_source"],
        "corpus_counts": corpus["counts"],
        "runtime": lock["runtime"],
        "cross_platform_parity": linux_parity,
        "evaluation_status": {
            split: evaluation["status"] for split, evaluation in evaluations.items()
        },
        "evaluations": {
            split: {
                key: evaluation[key]
                for key in (
                    "status",
                    "case_counts",
                    "group_coverage",
                    "result_group_coverage",
                    "gates",
                    "input_hashes",
                )
            }
            for split, evaluation in evaluations.items()
        },
        "evidence_files": evidence_files,
        "evidence_hashes": evidence_hashes,
        "downstream_policy": (
            "Artifacts generated by the qualified WP1 production path must embed "
            "this qualification ID, lock hash, and qualification-record hash."
        ),
    }
    record["record_payload_sha256"] = sha256_bytes(canonical_json(record))
    atomic_write_json(args.record, record)

    lines = [
        "# WP1 Qualification Report",
        "",
        f"**Decision:** {status}",
        "",
        f"**Qualification ID:** `{lock['qualification_id']}`",
        "",
        f"**Frozen code snapshot:** `{lock['code_snapshot_sha256']}`",
        "",
        "## Qualified Claim",
        "",
        spec["claim"],
        "",
        "## Evidence Boundary",
        "",
        spec["evidence_boundary"],
        "",
        "## External Corpus",
        "",
        f"The frozen corpus contains {corpus['sampled_record_count']} stratified records "
        f"from {corpus['source_record_count']} NASA/JPL records. The API payload version "
        f"is pinned to `{spec['external_source']['required_api_version']}` and every raw "
        "source file, source record, corpus row, split assignment, and holdout ID is "
        "content-addressed.",
        "",
        f"- Systems: {', '.join(spec['external_source']['systems'])}",
        "- Families: Lyapunov L1/L2; Halo L1/L2 northern/southern",
        "- Stability strata: marginal, weakly unstable, moderately unstable, strongly unstable",
        f"- Split counts: {corpus['counts']['split']}",
        "",
        "The development and calibration splits were executed before the code/spec/corpus "
        "lock was created. The holdout evaluator verifies every frozen input hash before "
        "reading holdout results.",
        "",
    ]
    for split, evaluation in evaluations.items():
        lines.extend(
            [
                f"## {split.title()} Decision",
                "",
                f"**{evaluation['status']}** with case counts "
                f"`{evaluation['case_counts']}`.",
                "",
                *gate_table(evaluation),
                "",
            ]
        )
    lines.extend(
        [
            "## Interpretation",
            "",
            "A PASS substantiates the exact qualified claim above. It shows that the same "
            "rounded external states propagated by WP1 and by a separately encoded, "
            "224-bit adaptive Taylor oracle agree at declared checkpoints; that invariant, "
            "frame, and reversibility gates pass; that analytic state-transition propagation "
            "reproduces JPL Floquet stability; and that strict WP1 differential correction "
            "recovers nearby periodic Lyapunov/Halo members from perturbed external seeds.",
            "",
            "One-period closure is retained as a diagnostic, not treated as a pure integrator "
            "error: published decimal initial conditions can amplify rounding along unstable "
            "orbits. The oracle checkpoint discrepancy is the integrator-accuracy test.",
            "",
            "## Downstream Use",
            "",
            "The production writer rejects a missing or failed qualification record and stamps "
            "the qualification ID and hashes into HDF5 and Parquet artifacts. Numeric state "
            "columns are float64; Tier 2 output also preserves decimal high-precision states.",
            "",
            "## Cross-Platform Parity",
            "",
            f"Bounded Linux/amd64 parity: **{linux_parity['status']}**, with "
            f"{linux_parity['passed']}/{linux_parity['collected']} evidence-bearing tests "
            f"passing on `{linux_parity['host']}` using Python {linux_parity['python']} "
            f"in `{linux_parity['container_image']}`.",
            "",
            "This is a bounded architecture check of the analytic STM/Floquet path, strict "
            "differential correctors, evidence integrity, and high-precision artifact "
            "contract. It is not represented as a full Linux replay of the campaign.",
            "",
            "## References",
            "",
            "- NASA/JPL Three-Body Periodic Orbits API: "
            "https://ssd-api.jpl.nasa.gov/doc/periodic_orbits.html",
            "- NASA Astrodynamics Convention and Modeling Reference, TP-20220014814: "
            "https://ntrs.nasa.gov/citations/20220014814",
            "- Poincare trajectory-design tool stability convention: "
            "https://indico.esa.int/event/224/papers/3852/files/225-Poincare_Vaquero.pdf",
            "",
            "## Reproducibility",
            "",
            f"- Base commit: `{lock['base_git_commit']}`",
            f"- Lock SHA-256: `{lock['lock_sha256']}`",
            f"- Corpus SHA-256: `{lock['corpus_sha256']}`",
            f"- Qualification record: `{Path(args.record).resolve().relative_to(repo_root)}`",
            "",
        ]
    )
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Qualification decision: {status}")
    print(f"Report: {report_path.resolve()}")
    print(f"Record: {Path(args.record).resolve()}")
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
