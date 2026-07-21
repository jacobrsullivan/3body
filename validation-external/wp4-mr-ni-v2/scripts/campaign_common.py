"""Integrity helpers for the corrected WP4-MR-NI-v2 campaign."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
CAMPAIGN_ROOT = VALIDATION_ROOT / "wp4-mr-ni-v2"
SPECIFICATION_LOCK = CAMPAIGN_ROOT / "reports/wp4_mr_v2_specification_lock.json"
INVALIDATED_V1_ASSESSMENT = (
    VALIDATION_ROOT / "wp4-mr-ni-v1/reports/wp4_mr_v1_specification_assessment.json"
)

for path in (REPO_ROOT, VALIDATION_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from qualification_tools import (  # noqa: E402
    canonical_json,
    load_json,
    sha256_bytes,
    sha256_file,
)


def verify_specification_lock(spec_path: str | Path) -> dict[str, Any]:
    spec_path = Path(spec_path).resolve()
    spec = load_json(spec_path)
    lock = load_json(SPECIFICATION_LOCK)
    unsigned = dict(lock)
    recorded = unsigned.pop("specification_lock_sha256", None)
    if recorded != sha256_bytes(canonical_json(unsigned)):
        raise RuntimeError("WP4 MR v2 specification lock payload is invalid")
    if (
        lock.get("campaign") != spec.get("campaign")
        or lock.get("lock_type") != "claim_specification"
        or lock.get("spec_sha256") != sha256_file(spec_path)
        or (REPO_ROOT / lock["spec_path"]).resolve() != spec_path
    ):
        raise RuntimeError("WP4 MR v2 specification lock does not bind this spec")
    for relative, expected_hash in lock["prerequisite_file_hashes"].items():
        if sha256_file(REPO_ROOT / relative) != expected_hash:
            raise RuntimeError(f"specification prerequisite changed: {relative}")
    return lock


def verify_invalidated_v1() -> dict[str, Any]:
    assessment = load_json(INVALIDATED_V1_ASSESSMENT)
    if (
        assessment.get("campaign") != "WP4-MR-NI-v1"
        or assessment.get("status") != "INVALIDATED_PREIMPLEMENTATION"
        or assessment.get("implementation_started") is not False
        or assessment.get("scientific_outputs_produced") is not False
        or assessment.get("successor") != "WP4-MR-NI-v2"
    ):
        raise RuntimeError("invalidated WP4-MR-NI-v1 assessment changed")
    return assessment
