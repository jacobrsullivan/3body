"""Integrity helpers for WP4-LIFT-NI-v2."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
CAMPAIGN_ROOT = VALIDATION_ROOT / "wp4-lift-ni-v2"
SPECIFICATION_LOCK = CAMPAIGN_ROOT / "reports/wp4_lift_ni_v2_specification_lock.json"
INVALIDATED_PREDECESSOR = (
    VALIDATION_ROOT
    / "wp4-lift-ni-v1/reports/wp4_lift_ni_v1_specification_assessment.json"
)

for path in (REPO_ROOT, VALIDATION_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from qualification_tools import (  # noqa: E402
    canonical_json,
    load_json,
    sha256_bytes,
    sha256_file,
    verify_lock,
)


def verify_specification_lock(spec_path: str | Path) -> dict[str, Any]:
    spec_path = Path(spec_path).resolve()
    spec = load_json(spec_path)
    lock = load_json(SPECIFICATION_LOCK)
    unsigned = dict(lock)
    recorded = unsigned.pop("specification_lock_sha256", None)
    if recorded != sha256_bytes(canonical_json(unsigned)):
        raise RuntimeError("WP4 lift specification lock payload is invalid")
    if (
        lock.get("campaign") != spec.get("campaign")
        or lock.get("lock_type") != "corrective_claim_specification"
        or lock.get("implementation_existed_before_lock") is not False
        or lock.get("qualification_outputs_existed_before_lock") is not False
        or lock.get("predecessor_invalidated_before_lock") is not True
        or lock.get("spec_sha256") != sha256_file(spec_path)
        or (REPO_ROOT / lock["spec_path"]).resolve() != spec_path
    ):
        raise RuntimeError("WP4 lift specification lock does not bind this claim")
    for relative, expected_hash in lock["prerequisite_file_hashes"].items():
        if sha256_file(REPO_ROOT / relative) != expected_hash:
            raise RuntimeError(f"specification prerequisite changed: {relative}")
    return lock


def verify_invalidated_predecessor(spec: dict[str, Any]) -> dict[str, Any]:
    contract = spec["prerequisites"]["invalidated_predecessor"]
    assessment = load_json(INVALIDATED_PREDECESSOR)
    if (
        (REPO_ROOT / contract["assessment_file"]).resolve()
        != INVALIDATED_PREDECESSOR.resolve()
        or sha256_file(INVALIDATED_PREDECESSOR) != contract["assessment_file_sha256"]
        or assessment.get("campaign") != contract["campaign"]
        or assessment.get("status") != contract["required_status"]
        or assessment.get("successor") != spec["campaign"]
        or assessment.get("qualification_lock_created") is not False
        or assessment.get("frozen_execution_started") is not False
        or assessment.get("scientific_outputs_produced") is not False
        or assessment.get("claim_authorization") != "NONE"
    ):
        raise RuntimeError("invalidated WP4 lift predecessor contract changed")
    return assessment


def verify_prerequisites(spec: dict[str, Any]) -> dict[str, Any]:
    verify_invalidated_predecessor(spec)
    records: dict[str, Any] = {}
    for name in ("wp2_multi", "wp4_mr"):
        contract = spec["prerequisites"][name]
        lock_path = REPO_ROOT / contract["lock_file"]
        record_path = REPO_ROOT / contract["record_file"]
        if sha256_file(lock_path) != contract["lock_file_sha256"]:
            raise RuntimeError(f"{name} prerequisite lock hash changed")
        if sha256_file(record_path) != contract["record_file_sha256"]:
            raise RuntimeError(f"{name} prerequisite record hash changed")
        lock = verify_lock(
            lock_path,
            REPO_ROOT,
            expected_prefix=contract["qualification_id"].rsplit("-", 1)[0],
        )
        record = load_json(record_path)
        if (
            record.get("status") != "PASS"
            or record.get("qualification_id") != contract["qualification_id"]
            or record.get("lock_sha256") != lock["lock_sha256"]
        ):
            raise RuntimeError(f"{name} prerequisite is not a matching PASS")
        records[name] = {"lock": lock, "record": record}
    return records
