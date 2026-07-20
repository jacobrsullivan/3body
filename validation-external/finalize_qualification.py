#!/usr/bin/env python
"""Create final machine and human qualification records from frozen evidence."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from qualification_tools import (
    atomic_write_json,
    canonical_json,
    load_json,
    sha256_bytes,
    sha256_file,
    utc_now,
    verify_lock,
)


def _relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _format(value: Any) -> str:
    return f"{value:.6e}" if isinstance(value, float) else str(value)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--source-manifest", required=True)
    parser.add_argument("--lock", required=True)
    parser.add_argument("--development", required=True)
    parser.add_argument("--calibration", required=True)
    parser.add_argument("--holdout", required=True)
    parser.add_argument("--record", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    spec_path = Path(args.spec).resolve()
    corpus_path = Path(args.corpus).resolve()
    source_path = Path(args.source_manifest).resolve()
    lock_path = Path(args.lock).resolve()
    lock = verify_lock(lock_path, root, expected_prefix=args.prefix)
    if lock["spec_sha256"] != sha256_file(spec_path):
        raise RuntimeError("qualification specification differs from the lock")
    if lock["corpus_sha256"] != sha256_file(corpus_path):
        raise RuntimeError("qualification corpus differs from the lock")
    if lock["source_manifest_sha256"] != sha256_file(source_path):
        raise RuntimeError("source manifest differs from the lock")

    evaluations: dict[str, dict[str, Any]] = {}
    evaluation_paths: dict[str, Path] = {}
    for split, value in (
        ("development", args.development),
        ("calibration", args.calibration),
        ("holdout", args.holdout),
    ):
        path = Path(value).resolve()
        evaluation = load_json(path)
        if evaluation.get("split") != split:
            raise RuntimeError(f"mislabeled {split} evaluation")
        if evaluation.get("spec_sha256") != lock["spec_sha256"]:
            raise RuntimeError(f"{split} evaluation uses a different spec")
        if evaluation.get("corpus_sha256") != lock["corpus_sha256"]:
            raise RuntimeError(f"{split} evaluation uses a different corpus")
        result_path = path.parent / f"{split}.json"
        if evaluation.get("results_sha256") != sha256_file(result_path):
            raise RuntimeError(f"{split} results changed after evaluation")
        if split == "holdout":
            if evaluation.get("qualification_id") != lock["qualification_id"]:
                raise RuntimeError("holdout was not executed under this lock")
            if evaluation.get("lock_sha256") != lock["lock_sha256"]:
                raise RuntimeError("holdout lock hash does not match")
        evaluations[split] = evaluation
        evaluation_paths[split] = path

    status = (
        "PASS"
        if all(item.get("status") == "PASS" for item in evaluations.values())
        else "FAIL"
    )
    spec = load_json(spec_path)
    corpus = load_json(corpus_path)
    evidence_paths = {
        "spec": spec_path,
        "corpus": corpus_path,
        "source_manifest": source_path,
        "lock": lock_path,
        **{f"{split}_evaluation": path for split, path in evaluation_paths.items()},
    }
    evidence_files = {
        name: {"path": _relative(path, root), "sha256": sha256_file(path)}
        for name, path in evidence_paths.items()
    }
    record: dict[str, Any] = {
        "schema_version": "1.0",
        "generated_utc": utc_now(),
        "qualification_id": lock["qualification_id"],
        "status": status,
        "claim": spec["claim"],
        "evidence_boundary": spec["evidence_boundary"],
        "base_git_commit": lock["base_git_commit"],
        "lock_sha256": lock["lock_sha256"],
        "code_snapshot_sha256": lock["code_snapshot_sha256"],
        "spec_sha256": lock["spec_sha256"],
        "corpus_sha256": lock["corpus_sha256"],
        "source_manifest_sha256": lock["source_manifest_sha256"],
        "holdout_ids_sha256": lock["holdout_ids_sha256"],
        "runtime_at_freeze": lock["runtime"],
        "corpus_case_counts": {
            split: sum(case["split"] == split for case in corpus["cases"])
            for split in ("development", "calibration", "holdout")
        },
        "evaluation_status": {
            split: evaluation["status"]
            for split, evaluation in evaluations.items()
        },
        "evaluations": evaluations,
        "evidence_files": evidence_files,
        "downstream_policy": spec["downstream_policy"],
    }
    record["record_payload_sha256"] = sha256_bytes(canonical_json(record))
    atomic_write_json(args.record, record)

    lines = [
        f"# {spec['campaign']} Qualification Report",
        "",
        f"**Decision:** {status}",
        "",
        f"**Qualification ID:** `{lock['qualification_id']}`",
        "",
        "## Qualified Claim",
        "",
        spec["claim"],
        "",
        "## Evidence Boundary",
        "",
        spec["evidence_boundary"],
        "",
        "## Decisions",
        "",
    ]
    for split, evaluation in evaluations.items():
        lines.extend(
            [
                f"### {split.title()}",
                "",
                f"**{evaluation['status']}** across {evaluation['case_count']} cases.",
                "",
                "| Gate | Observed | Requirement | Result |",
                "|---|---:|---:|:---:|",
            ]
        )
        for gate in evaluation["gates"]:
            lines.append(
                f"| `{gate['name']}` | {_format(gate['observed'])} | "
                f"{gate['comparator']} {_format(gate['threshold'])} | "
                f"{'PASS' if gate['passed'] else 'FAIL'} |"
            )
        lines.append("")
    lines.extend(
        [
            "## Integrity",
            "",
            f"- Base commit: `{lock['base_git_commit']}`",
            f"- Code snapshot: `{lock['code_snapshot_sha256']}`",
            f"- Lock: `{lock['lock_sha256']}`",
            f"- Corpus: `{lock['corpus_sha256']}`",
            f"- Holdout IDs: `{lock['holdout_ids_sha256']}`",
            "",
            "The holdout runner verified every frozen input before selecting the reserved "
            "cases. The final status is fail-closed: any failed mandatory gate produces FAIL.",
            "",
            "## Downstream Policy",
            "",
            spec["downstream_policy"],
            "",
        ]
    )
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Qualification decision: {status}")
    print(f"Record: {Path(args.record).resolve()}")
    print(f"Report: {report_path.resolve()}")
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
