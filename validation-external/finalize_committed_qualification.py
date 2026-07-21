#!/usr/bin/env python
"""Finalize qualification only from clean, committed, internally consistent evidence."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

from qualification_tools import (
    atomic_write_json,
    canonical_json,
    git_output,
    load_json,
    make_gate,
    require_clean_worktree,
    sha256_bytes,
)


def _require_committed(root: Path, path: Path) -> None:
    relative = path.resolve().relative_to(root).as_posix()
    tracked = git_output(root, "ls-files", "--error-unmatch", "--", relative)
    if tracked != relative:
        raise RuntimeError(f"qualification evidence is not committed: {relative}")


def _verify_evaluation(path: Path) -> None:
    evaluation = load_json(path)
    gates = evaluation.get("gates")
    if not isinstance(gates, list) or not gates:
        raise RuntimeError(f"evaluation has no gates: {path}")
    recomputed = [
        make_gate(
            str(gate["name"]),
            gate["observed"],
            str(gate["comparator"]),
            gate["threshold"],
        )
        for gate in gates
    ]
    if any(
        expected["passed"] != recorded.get("passed")
        for expected, recorded in zip(recomputed, gates, strict=True)
    ):
        raise RuntimeError(f"evaluation contains inconsistent gate decisions: {path}")
    status = "PASS" if all(gate["passed"] for gate in recomputed) else "FAIL"
    if evaluation.get("status") != status:
        raise RuntimeError(f"evaluation status is inconsistent with its gates: {path}")


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
    record_path = Path(args.record).resolve()
    report_path = Path(args.report).resolve()
    if record_path.exists() or report_path.exists():
        raise RuntimeError("refusing to overwrite final qualification outputs")
    require_clean_worktree(root)
    for value in (args.development, args.calibration, args.holdout):
        evaluation_path = Path(value).resolve()
        result_path = evaluation_path.parent / evaluation_path.name.replace(
            "_evaluation.json", ".json"
        )
        _require_committed(root, evaluation_path)
        _require_committed(root, result_path)
        _verify_evaluation(evaluation_path)

    generic = root / "validation-external/finalize_qualification.py"
    command = [
        sys.executable,
        str(generic),
        "--repo-root",
        str(root),
        "--prefix",
        args.prefix,
        "--spec",
        args.spec,
        "--corpus",
        args.corpus,
        "--source-manifest",
        args.source_manifest,
        "--lock",
        args.lock,
        "--development",
        args.development,
        "--calibration",
        args.calibration,
        "--holdout",
        args.holdout,
        "--record",
        args.record,
        "--report",
        args.report,
    ]
    subprocess.run(command, cwd=root, check=True)

    evidence_commit = git_output(root, "rev-parse", "HEAD")
    record = load_json(record_path)
    record.pop("record_payload_sha256", None)
    record["evidence_git_commit"] = evidence_commit
    record["record_payload_sha256"] = sha256_bytes(canonical_json(record))
    atomic_write_json(record_path, record)

    report = report_path.read_text(encoding="utf-8")
    marker = f"- Base commit: `{record['base_git_commit']}`"
    if marker not in report:
        raise RuntimeError("generic report lacks the expected integrity marker")
    report = report.replace(
        marker, marker + f"\n- Evidence commit: `{evidence_commit}`", 1
    )
    report_path.write_text(report, encoding="utf-8")
    print(f"Committed-evidence finalization: {evidence_commit}")


if __name__ == "__main__":
    main()
