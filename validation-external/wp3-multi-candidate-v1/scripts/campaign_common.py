"""Shared integrity and runtime helpers for WP3-MULTI-CAND-v1."""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
import platform
import struct
import sys
from typing import Any

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation-external"
CAMPAIGN_ROOT = REPO_ROOT / "validation-external/wp3-multi-candidate-v1"
SPECIFICATION_LOCK = (
    CAMPAIGN_ROOT / "reports/wp3_multi_v1_specification_lock.json"
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


def _verify_record_payload(record: dict[str, Any]) -> None:
    unsigned = dict(record)
    recorded = unsigned.pop("record_payload_sha256", None)
    if recorded != sha256_bytes(canonical_json(unsigned)):
        raise RuntimeError("prerequisite record payload hash is invalid")


def verify_specification_lock(spec_path: str | Path) -> dict[str, Any]:
    spec_path = Path(spec_path).resolve()
    spec = load_json(spec_path)
    lock = load_json(SPECIFICATION_LOCK)
    unsigned = dict(lock)
    recorded = unsigned.pop("specification_lock_sha256", None)
    if recorded != sha256_bytes(canonical_json(unsigned)):
        raise RuntimeError("WP3 multi specification lock payload is invalid")
    if (
        lock.get("campaign") != spec.get("campaign")
        or lock.get("lock_type") != "claim_specification"
        or lock.get("spec_sha256") != sha256_file(spec_path)
        or (REPO_ROOT / lock["spec_path"]).resolve() != spec_path
    ):
        raise RuntimeError("WP3 multi specification lock does not bind this spec")
    for relative, expected_hash in lock["prerequisite_file_hashes"].items():
        if sha256_file(REPO_ROOT / relative) != expected_hash:
            raise RuntimeError(f"specification prerequisite changed: {relative}")
    return lock


def verify_prerequisite(
    expected: dict[str, str],
    *,
    lock_path: str | Path,
    record_path: str | Path,
    prefix: str,
) -> dict[str, str]:
    lock_path = Path(lock_path)
    record_path = Path(record_path)
    lock = verify_lock(lock_path, REPO_ROOT, expected_prefix=prefix)
    record = load_json(record_path)
    _verify_record_payload(record)
    if (
        sha256_file(lock_path) != expected["lock_file_sha256"]
        or sha256_file(record_path) != expected["record_file_sha256"]
        or lock.get("qualification_id") != expected["qualification_id"]
        or lock.get("lock_sha256") != expected["lock_sha256"]
        or record.get("qualification_id") != expected["qualification_id"]
        or record.get("lock_sha256") != expected["lock_sha256"]
        or record.get("record_payload_sha256")
        != expected["record_payload_sha256"]
        or record.get("status") != "PASS"
    ):
        raise RuntimeError(f"invalid prerequisite qualification: {prefix}")
    return {
        "status": "PASS",
        "qualification_id": expected["qualification_id"],
        "lock_sha256": expected["lock_sha256"],
        "lock_file_sha256": expected["lock_file_sha256"],
        "record_file_sha256": expected["record_file_sha256"],
        "record_payload_sha256": expected["record_payload_sha256"],
    }


def verify_publication_reserve(path: str | Path, expected_hash: str) -> dict[str, Any]:
    path = Path(path)
    payload = load_json(path)
    commitments = payload.get("commitments", [])
    forbidden = {
        "source_case_id",
        "source_index",
        "initial_positions_decimal",
        "initial_velocities_decimal",
        "brutus_final_positions_decimal",
        "brutus_final_velocities_decimal",
    }
    if (
        sha256_file(path) != expected_hash
        or payload.get("status") != "SEALED_UNEXECUTED"
        or payload.get("case_count") != 24
        or len(commitments) != 24
        or any(item.get("status") != "SEALED_UNEXECUTED" for item in commitments)
        or any(forbidden & set(item) for item in commitments)
    ):
        raise RuntimeError("publication reserve is not intact and sealed")
    return {
        "status": "SEALED_UNEXECUTED",
        "case_count": 24,
        "sha256": sha256_file(path),
        "source_rows_present": False,
    }


def numpy_backend_fingerprint() -> dict[str, Any]:
    config = np.show_config(mode="dicts")
    if not isinstance(config, dict):
        raise RuntimeError("NumPy did not expose structured build configuration")

    def dependency(name: str) -> dict[str, Any]:
        source = config["Build Dependencies"][name]
        fields = (
            "name",
            "found",
            "version",
            "detection method",
            "openblas configuration",
        )
        return {field: source.get(field) for field in fields}

    def machine(name: str) -> dict[str, Any]:
        source = config["Machine Information"][name]
        return {
            field: source.get(field)
            for field in ("system", "family", "cpu", "endian")
        }

    configuration = {
        "blas": dependency("blas"),
        "lapack": dependency("lapack"),
        "machine": {"build": machine("build"), "host": machine("host")},
        "simd_extensions": {
            key: sorted(config["SIMD Extensions"][key])
            for key in ("baseline", "found", "not found")
        },
    }
    return {
        "configuration": configuration,
        "sha256": sha256_bytes(
            json.dumps(
                configuration,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            ).encode("ascii")
        ),
    }


def decision_runtime() -> dict[str, Any]:
    return {
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "platform": platform.platform(),
            "mac_version": platform.mac_ver()[0],
            "machine": platform.machine(),
            "processor": platform.processor(),
            "architecture": list(platform.architecture()),
            "pointer_bits": struct.calcsize("P") * 8,
            "byteorder": sys.byteorder,
        },
        "packages": {
            name: importlib.metadata.version(name) for name in ("numpy", "scipy")
        },
        "numpy_backend_sha256": numpy_backend_fingerprint()["sha256"],
    }


def verify_decision_runtime(expected: dict[str, Any]) -> dict[str, Any]:
    observed = decision_runtime()
    if observed != expected:
        raise RuntimeError(
            f"decision runtime mismatch: expected {expected}, observed {observed}"
        )
    return observed
