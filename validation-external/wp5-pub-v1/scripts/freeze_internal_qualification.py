#!/usr/bin/env python
"""Freeze a passing WP5-PUB-v1 core replay into immutable internal records."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
CAMPAIGN_ROOT = REPO_ROOT / "validation-external/wp5-pub-v1"
SPEC_PATH = CAMPAIGN_ROOT / "qualification_spec.json"
SPEC_LOCK_PATH = (
    CAMPAIGN_ROOT / "reports/wp5_pub_v1_specification_lock.json"
)
MANIFEST_PATH = REPO_ROOT / "publication/wp5-pub-v1/artifact_manifest.json"
PDF_PATH = REPO_ROOT / "publication/wp5-pub-v1/manuscript/main.pdf"
VISUAL_QA_PATH = (
    CAMPAIGN_ROOT / "reports/wp5_pub_v1_pdf_visual_inspection.json"
)
RESULTS_PATH = (
    CAMPAIGN_ROOT / "results/wp5_pub_v1_internal_qualification_results.json"
)
RECORD_PATH = (
    CAMPAIGN_ROOT / "reports/wp5_pub_v1_internal_qualification_record.json"
)


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def git_output(*arguments: str) -> str:
    return subprocess.check_output(
        ["git", *arguments], cwd=REPO_ROOT, text=True
    ).strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if git_output("status", "--short"):
        raise RuntimeError("internal qualification freeze requires a clean worktree")
    if RESULTS_PATH.exists() or RECORD_PATH.exists():
        raise RuntimeError("refusing to overwrite immutable internal qualification")
    report_path = args.report
    if not report_path.is_absolute():
        report_path = REPO_ROOT / report_path
    report = load_json(report_path)
    unsigned_report = dict(report)
    recorded_report_hash = unsigned_report.pop("report_payload_sha256")
    if sha256_bytes(canonical_json(unsigned_report)) != recorded_report_hash:
        raise RuntimeError("core report payload hash mismatch")
    if not (
        report.get("campaign") == "WP5-PUB-v1"
        and report.get("mode") == "core"
        and report.get("internal_gates_pass") is True
        and report.get("status") == "READY_FOR_EXTERNAL_REVIEW"
    ):
        raise RuntimeError("only a passing core report can be frozen")

    manifest_sha256 = sha256_file(MANIFEST_PATH)
    pdf_sha256 = sha256_file(PDF_PATH)
    gates = report["gate_results"]
    if gates["artifact_manifest"]["manifest_file_sha256"] != manifest_sha256:
        raise RuntimeError("core report targets a different artifact manifest")
    if gates["pdf"]["sha256"] != pdf_sha256:
        raise RuntimeError("core report targets a different manuscript PDF")
    visual_qa = load_json(VISUAL_QA_PATH)
    if not (
        visual_qa["status"] == "PASS"
        and visual_qa["artifact"]["sha256"] == pdf_sha256
        and visual_qa["independent_external_review"] is False
    ):
        raise RuntimeError("internal PDF visual inspection is absent or stale")

    evidence_commit = git_output("rev-parse", "HEAD")
    frozen_results = dict(report)
    frozen_results["evidence_git_commit"] = evidence_commit
    frozen_results["source_report_path"] = str(
        report_path.relative_to(REPO_ROOT)
        if REPO_ROOT in report_path.parents
        else report_path
    )
    frozen_results["frozen_utc"] = datetime.now(timezone.utc).isoformat()
    write_json(RESULTS_PATH, frozen_results)

    identity_payload = {
        "campaign": "WP5-PUB-v1",
        "evidence_git_commit": evidence_commit,
        "specification_lock_sha256": gates["specification_lock"][
            "specification_lock_sha256"
        ],
        "artifact_manifest_sha256": manifest_sha256,
        "manuscript_pdf_sha256": pdf_sha256,
        "normalized_generic_payload_sha256": gates["generic_replay"][
            "normalized_payload_sha256"
        ],
        "core_report_payload_sha256": recorded_report_hash,
    }
    qualification_id = (
        "WP5-PUB-v1-" + sha256_bytes(canonical_json(identity_payload))[:12]
    )
    spec = load_json(SPEC_PATH)
    record = {
        "schema_version": "1.0",
        "campaign": "WP5-PUB-v1",
        "qualification_id": qualification_id,
        "status": "READY_FOR_EXTERNAL_REVIEW",
        "internal_status": "PASS",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_git_commit": evidence_commit,
        "authorized_claim": spec["primary_result"],
        "claim_boundary": (
            "The result is local, complete, and meromorphic near the declared "
            "fixed-nonzero-angular-momentum phase curve. It does not exclude "
            "one additional integral and is not a global, zero-angular-"
            "momentum, non-meromorphic, nonzero-Xi, or triple-collision claim."
        ),
        "spec_sha256": sha256_file(SPEC_PATH),
        "specification_lock_sha256": gates["specification_lock"][
            "specification_lock_sha256"
        ],
        "artifact_manifest_sha256": manifest_sha256,
        "artifact_manifest_payload_sha256": gates["artifact_manifest"][
            "manifest_payload_sha256"
        ],
        "manuscript_pdf_sha256": pdf_sha256,
        "manuscript_pdf_pages": gates["pdf"]["pages"],
        "visual_inspection_sha256": sha256_file(VISUAL_QA_PATH),
        "core_report_payload_sha256": recorded_report_hash,
        "results_sha256": sha256_file(RESULTS_PATH),
        "generic_replay": gates["generic_replay"],
        "publication_tests": {
            "passed": gates["publication_tests"]["passed"],
            "command": gates["publication_tests"]["command"],
        },
        "adversarial_controls": gates["adversarial_controls"],
        "prerequisite_records": gates["prerequisite_records"],
        "external_gates": report["external_gates"],
        "external_evidence_count": (
            report["external_gates"]["review_count"]
            + report["external_gates"]["receipt_count"]
        ),
        "submission_authorized": False,
        "publication_authorized": False,
        "next_gate": (
            "Two independent consenting human mathematical reviews, at least "
            "one external clean-room core replay, resolved findings, confirmed "
            "author metadata and licenses, then explicit release authorization."
        ),
    }
    record["record_payload_sha256"] = sha256_bytes(canonical_json(record))
    write_json(RECORD_PATH, record)
    print(
        json.dumps(
            {
                "qualification_id": qualification_id,
                "status": record["status"],
                "record": str(RECORD_PATH.relative_to(REPO_ROOT)),
                "results": str(RESULTS_PATH.relative_to(REPO_ROOT)),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
