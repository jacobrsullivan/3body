"""Dependency-light integrity helpers owned by the WP4 readiness campaign."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


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


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as stream:
        return json.load(stream)


def atomic_write_json(path: str | Path, value: Any) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{destination.name}.", dir=destination.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
        os.replace(temporary, destination)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def runtime_fingerprint() -> dict[str, Any]:
    packages: dict[str, str] = {}
    for name in ("numpy", "scipy", "pytest"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = "not-installed"
    return {
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "python_executable": str(Path(sys.executable).resolve()),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "packages": packages,
    }


def _input_files(root: Path, scopes: Iterable[str]) -> list[Path]:
    files: set[Path] = set()
    for scope in scopes:
        candidate = (root / scope).resolve()
        if candidate.is_file():
            files.add(candidate)
            continue
        if not candidate.is_dir():
            raise RuntimeError(f"frozen input scope does not exist: {scope}")
        for path in candidate.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                files.add(path.resolve())
    if not files:
        raise RuntimeError("WP4 readiness freeze selected no files")
    return sorted(files)


def verify_signed_lock(lock_path: str | Path, root: str | Path) -> dict[str, Any]:
    lock = load_json(lock_path)
    recorded = str(lock.get("lock_sha256", ""))
    unsigned = dict(lock)
    unsigned.pop("lock_sha256", None)
    actual = sha256_bytes(canonical_json(unsigned))
    if not recorded or actual != recorded:
        raise RuntimeError("WP4 readiness lock payload integrity failure")
    repo = Path(root).resolve()
    for relative, expected in lock["file_hashes"].items():
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            raise RuntimeError(f"unsafe frozen path: {relative}")
        if sha256_file(repo / path) != expected:
            raise RuntimeError(f"frozen WP4 readiness input changed: {relative}")
    for relative, expected in lock["external_file_hashes"].items():
        if sha256_file(repo / relative) != expected:
            raise RuntimeError(f"qualified prerequisite input changed: {relative}")
    return lock


def verify_wp2_prerequisite(root: str | Path, expected: dict[str, Any]) -> dict[str, Any]:
    repo = Path(root).resolve()
    record_path = repo / expected["record_path"]
    lock_path = repo / expected["lock_path"]
    if sha256_file(record_path) != expected["record_sha256"]:
        raise RuntimeError("WP2-UP-v2 record hash mismatch")
    if sha256_file(lock_path) != expected["lock_file_sha256"]:
        raise RuntimeError("WP2-UP-v2 lock file hash mismatch")
    record = load_json(record_path)
    lock = load_json(lock_path)
    unsigned = dict(lock)
    recorded_lock_hash = str(unsigned.pop("lock_sha256", ""))
    if sha256_bytes(canonical_json(unsigned)) != recorded_lock_hash:
        raise RuntimeError("WP2-UP-v2 lock payload integrity failure")
    if not (
        record.get("status") == "PASS"
        and record.get("qualification_id") == expected["qualification_id"]
        and lock.get("qualification_id") == expected["qualification_id"]
        and record.get("lock_sha256") == expected["lock_sha256"]
        and lock.get("lock_sha256") == expected["lock_sha256"]
    ):
        raise RuntimeError("WP2-UP-v2 prerequisite is not the expected PASS")
    for relative, digest in lock["file_hashes"].items():
        if sha256_file(repo / relative) != digest:
            raise RuntimeError(f"WP2-UP-v2 frozen input changed: {relative}")
    return {
        "status": "PASS",
        "qualification_id": record["qualification_id"],
        "lock_sha256": record["lock_sha256"],
        "record_sha256": expected["record_sha256"],
    }


def verify_wp3_null_result(root: str | Path, expected: dict[str, Any]) -> dict[str, Any]:
    repo = Path(root).resolve()
    gate_path = repo / expected["staged_gate_path"]
    if sha256_file(gate_path) != expected["staged_gate_sha256"]:
        raise RuntimeError("WP3 upstairs staged-gate hash mismatch")
    gate = load_json(gate_path)
    required = {
        "SEARCH_READY": "PASS",
        "CANDIDATE_READY": "NOT_TRIGGERED",
        "SEALED_QUALIFICATION": "NOT_TRIGGERED",
        "WP4_READY": "BLOCKED",
        "publication_reserve_status": "SEALED_UNEXECUTED",
        "candidate_count": 0,
        "qualification_id": expected["qualification_id"],
        "lock_sha256": expected["lock_sha256"],
    }
    for key, value in required.items():
        if gate.get(key) != value:
            raise RuntimeError(f"WP3 upstairs null-result contract failed at {key}")
    return {
        "search_status": gate["SEARCH_READY"],
        "candidate_count": 0,
        "candidate_status": gate["CANDIDATE_READY"],
        "sealed_qualification_status": gate["SEALED_QUALIFICATION"],
        "wp4_candidate_status": gate["WP4_READY"],
        "publication_reserve_status": gate["publication_reserve_status"],
        "qualification_id": gate["qualification_id"],
        "lock_sha256": gate["lock_sha256"],
        "staged_gate_sha256": expected["staged_gate_sha256"],
    }


def build_readiness_lock(
    *,
    root: str | Path,
    spec_path: str | Path,
    scopes: Iterable[str],
    external_paths: Iterable[str],
    output_paths: Iterable[str],
    prerequisite: dict[str, Any],
    wp3_state: dict[str, Any],
) -> dict[str, Any]:
    repo = Path(root).resolve()
    present_outputs = [path for path in output_paths if (repo / path).exists()]
    if present_outputs:
        raise RuntimeError(
            "readiness outputs must be absent at freeze: " + ", ".join(present_outputs)
        )
    files = _input_files(repo, scopes)
    file_hashes = {
        path.relative_to(repo).as_posix(): sha256_file(path) for path in files
    }
    external_hashes = {path: sha256_file(repo / path) for path in external_paths}
    snapshot = sha256_bytes(canonical_json({
        "file_hashes": file_hashes,
        "external_file_hashes": external_hashes,
    }))
    base_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True
    ).strip()
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "qualification_id": f"WP4-UP-READY-v1-{snapshot[:12]}",
        "frozen_utc": utc_now(),
        "base_git_commit": base_commit,
        "readiness_outputs_absent_at_freeze": True,
        "candidate_input_present_at_freeze": False,
        "publication_reserve_opened_at_freeze": False,
        "spec_sha256": sha256_file(spec_path),
        "code_snapshot_sha256": snapshot,
        "file_hashes": file_hashes,
        "external_file_hashes": external_hashes,
        "wp2_upstairs_prerequisite": prerequisite,
        "wp3_upstairs_state": wp3_state,
        "runtime": runtime_fingerprint(),
    }
    payload["lock_sha256"] = sha256_bytes(canonical_json(payload))
    return payload


def make_gate(
    name: str,
    observed: float | int,
    comparator: str,
    threshold: float | int,
) -> dict[str, Any]:
    if comparator == "<=":
        passed = observed <= threshold
    elif comparator == ">=":
        passed = observed >= threshold
    elif comparator == "==":
        passed = observed == threshold
    else:
        raise ValueError(f"unsupported comparator: {comparator}")
    return {
        "name": name,
        "observed": observed,
        "comparator": comparator,
        "threshold": threshold,
        "passed": bool(passed),
    }
