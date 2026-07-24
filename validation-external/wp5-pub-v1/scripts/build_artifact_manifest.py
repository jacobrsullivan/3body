#!/usr/bin/env python
"""Build the deterministic WP5-PUB-v1 artifact manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT = REPO_ROOT / "publication/wp5-pub-v1/artifact_manifest.json"

ARTIFACT_PATHS = [
    "notes/wp5-pub-v1-plan.md",
    "output/pdf/wp5-pub-v1-manuscript.pdf",
    "publication/wp5-pub-v1/README.md",
    "publication/wp5-pub-v1/REPRODUCING.md",
    "publication/wp5-pub-v1/claims/claim_ledger.json",
    "publication/wp5-pub-v1/manuscript/main.pdf",
    "publication/wp5-pub-v1/manuscript/main.tex",
    "publication/wp5-pub-v1/manuscript/references.bib",
    "publication/wp5-pub-v1/proof_dependency_map.json",
    "publication/wp5-pub-v1/proof_dependency_map.md",
    "publication/wp5-pub-v1/release/SUBMISSION_CHECKLIST.md",
    "publication/wp5-pub-v1/release/metadata.json",
    "publication/wp5-pub-v1/requirements-publication.txt",
    "publication/wp5-pub-v1/review/EXTERNAL_REVIEW_GATE.md",
    "publication/wp5-pub-v1/review/REVIEWER_PACKET.md",
    "publication/wp5-pub-v1/review/REVIEW_FORM.md",
    "scripts/reproduce_wp5_pub_v1.sh",
    "tests/wp5_pub_v1/test_wp5_pub_v1.py",
    "validation-external/wp5-pub-v1/README.md",
    "validation-external/wp5-pub-v1/qualification_spec.json",
    "validation-external/wp5-pub-v1/reports/wp5_pub_v1_pdf_visual_inspection.json",
    "validation-external/wp5-pub-v1/reports/wp5_pub_v1_specification_lock.json",
    "validation-external/wp5-pub-v1/review/clean_room_receipt_schema.json",
    "validation-external/wp5-pub-v1/review/external_review_schema.json",
    "validation-external/wp5-pub-v1/scripts/build_artifact_manifest.py",
    "validation-external/wp5-pub-v1/scripts/lock_specification.py",
    "validation-external/wp5-pub-v1/scripts/verify_package.py",
    "validation-external/wp5-pub-v1/sources/manifest.json",
]


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    if ARTIFACT_PATHS != sorted(set(ARTIFACT_PATHS)):
        raise RuntimeError("artifact paths must be unique and sorted")
    artifacts = []
    for relative_name in ARTIFACT_PATHS:
        path = REPO_ROOT / relative_name
        if not path.is_file():
            raise FileNotFoundError(f"required publication artifact is missing: {path}")
        artifacts.append(
            {
                "path": relative_name,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    payload = {
        "schema_version": "1.0",
        "campaign": "WP5-PUB-v1",
        "manifest_policy": (
            "The manifest excludes itself and generated replay reports. "
            "External records pin the manifest file hash and git commit."
        ),
        "source_date_epoch": 1784851200,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    payload["manifest_payload_sha256"] = hashlib.sha256(
        canonical_json(payload)
    ).hexdigest()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {OUTPUT.relative_to(REPO_ROOT)} ({len(artifacts)} artifacts)")


if __name__ == "__main__":
    main()
