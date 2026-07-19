"""Load and enforce the frozen WP1 qualification record."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DEFAULT_RECORD = (
    Path(__file__).resolve().parents[3]
    / "validation-external"
    / "wp1-validation"
    / "reports"
    / "wp1_qualification_record.json"
)


class QualificationError(RuntimeError):
    """Raised when a downstream artifact lacks a passing qualification."""


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def load_qualification_record(
    path: str | Path | None = None, *, require_pass: bool = True
) -> dict[str, Any]:
    """Load a qualification record and optionally require a PASS decision."""
    record_path = Path(path) if path is not None else DEFAULT_RECORD
    if not record_path.is_file():
        raise QualificationError(f"WP1 qualification record not found: {record_path}")
    with record_path.open("r", encoding="utf-8") as stream:
        record = json.load(stream)
    required = {
        "schema_version",
        "qualification_id",
        "status",
        "claim",
        "lock_sha256",
        "record_payload_sha256",
    }
    missing = sorted(required.difference(record))
    if missing:
        raise QualificationError(f"Qualification record missing fields: {missing}")
    expected_integrity = str(record["record_payload_sha256"])
    unsigned = dict(record)
    unsigned.pop("record_payload_sha256")
    actual_integrity = hashlib.sha256(_canonical_json(unsigned)).hexdigest()
    if actual_integrity != expected_integrity:
        raise QualificationError(
            "Qualification record integrity failure: "
            f"calculated {actual_integrity}, recorded {expected_integrity}"
        )
    if require_pass and record["status"] != "PASS":
        raise QualificationError(
            f"WP1 qualification {record['qualification_id']} is {record['status']}"
        )
    record["record_path"] = str(record_path.resolve())
    record["record_sha256"] = sha256_file(record_path)
    return record


def qualification_metadata(
    path: str | Path | None = None, *, require_pass: bool = True
) -> dict[str, str]:
    """Return the immutable fields that downstream artifacts must embed."""
    record = load_qualification_record(path, require_pass=require_pass)
    return {
        "wp1_qualification_id": str(record["qualification_id"]),
        "wp1_qualification_status": str(record["status"]),
        "wp1_qualification_lock_sha256": str(record["lock_sha256"]),
        "wp1_qualification_record_sha256": str(record["record_sha256"]),
    }


def stamp_hdf5(handle: Any, metadata: dict[str, str]) -> None:
    """Stamp an open h5py file/group with qualification metadata."""
    for key, value in metadata.items():
        handle.attrs[key] = value


def assert_metadata_matches(actual: dict[str, Any], expected: dict[str, str]) -> None:
    """Reject missing or mismatched qualification metadata."""
    mismatches = {
        key: {"expected": value, "actual": actual.get(key)}
        for key, value in expected.items()
        if str(actual.get(key, "")) != value
    }
    if mismatches:
        raise QualificationError(f"Qualification metadata mismatch: {mismatches}")
