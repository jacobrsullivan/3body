"""Small, dependency-light integrity helpers for qualification campaigns."""

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


def git_output(repo_root: str | Path, *arguments: str) -> str:
    return subprocess.check_output(
        ["git", *arguments], cwd=repo_root, text=True
    ).strip()


def require_clean_worktree(repo_root: str | Path) -> None:
    status = git_output(repo_root, "status", "--short")
    if status:
        raise RuntimeError(
            "qualification freeze requires a clean committed worktree:\n" + status
        )


def tracked_files(
    repo_root: str | Path,
    scopes: Iterable[str],
) -> list[Path]:
    root = Path(repo_root).resolve()
    command = ["git", "ls-files", "--", *scopes]
    result = subprocess.check_output(command, cwd=root, text=True).splitlines()
    files = sorted({(root / item).resolve() for item in result})
    missing = [str(path) for path in files if not path.is_file()]
    if missing:
        raise RuntimeError(f"tracked qualification inputs are missing: {missing}")
    if not files:
        raise RuntimeError("qualification freeze scope selected no tracked files")
    return files


def runtime_fingerprint() -> dict[str, Any]:
    packages: dict[str, str] = {}
    for name in ("numpy", "scipy", "rebound", "pytest"):
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


def build_lock(
    *,
    repo_root: str | Path,
    qualification_prefix: str,
    spec_path: str | Path,
    corpus_path: str | Path,
    source_manifest_path: str | Path,
    development_evaluation_path: str | Path,
    calibration_evaluation_path: str | Path,
    scopes: Iterable[str],
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    spec = Path(spec_path).resolve()
    corpus = Path(corpus_path).resolve()
    source_manifest = Path(source_manifest_path).resolve()
    evaluations = {
        "development": Path(development_evaluation_path).resolve(),
        "calibration": Path(calibration_evaluation_path).resolve(),
    }

    require_clean_worktree(root)
    for split, path in evaluations.items():
        payload = load_json(path)
        if payload.get("split") != split or payload.get("status") != "PASS":
            raise RuntimeError(f"cannot freeze non-passing {split} evidence")
        if payload.get("spec_sha256") != sha256_file(spec):
            raise RuntimeError(f"{split} evidence uses a different specification")
        if payload.get("corpus_sha256") != sha256_file(corpus):
            raise RuntimeError(f"{split} evidence uses a different corpus")

    corpus_payload = load_json(corpus)
    holdout_ids = sorted(
        str(case["case_id"])
        for case in corpus_payload["cases"]
        if case["split"] == "holdout"
    )
    if not holdout_ids:
        raise RuntimeError("qualification corpus has no reserved holdout cases")

    files = tracked_files(root, scopes)
    required = {spec, corpus, source_manifest, *evaluations.values()}
    if not required.issubset(set(files)):
        omitted = sorted(str(path) for path in required.difference(files))
        raise RuntimeError(f"freeze scopes omit required evidence: {omitted}")
    file_hashes = {
        path.relative_to(root).as_posix(): sha256_file(path) for path in files
    }
    snapshot_sha256 = sha256_bytes(canonical_json(file_hashes))
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "qualification_id": f"{qualification_prefix}-{snapshot_sha256[:12]}",
        "frozen_utc": utc_now(),
        "base_git_commit": git_output(root, "rev-parse", "HEAD"),
        "worktree_clean_at_freeze": True,
        "holdout_outputs_absent_at_freeze": True,
        "spec_sha256": sha256_file(spec),
        "corpus_sha256": sha256_file(corpus),
        "source_manifest_sha256": sha256_file(source_manifest),
        "holdout_ids": holdout_ids,
        "holdout_ids_sha256": sha256_bytes(canonical_json(holdout_ids)),
        "code_snapshot_sha256": snapshot_sha256,
        "runtime": runtime_fingerprint(),
        "file_hashes": file_hashes,
    }
    payload["lock_sha256"] = sha256_bytes(canonical_json(payload))
    return payload


def verify_lock(
    lock_path: str | Path,
    repo_root: str | Path,
    *,
    expected_prefix: str | None = None,
) -> dict[str, Any]:
    lock = load_json(lock_path)
    recorded = str(lock.get("lock_sha256", ""))
    unsigned = dict(lock)
    unsigned.pop("lock_sha256", None)
    actual = sha256_bytes(canonical_json(unsigned))
    if not recorded or actual != recorded:
        raise RuntimeError(
            f"qualification lock integrity failure: expected {recorded}, got {actual}"
        )
    qualification_id = str(lock.get("qualification_id", ""))
    if expected_prefix and not qualification_id.startswith(expected_prefix + "-"):
        raise RuntimeError(f"unexpected qualification ID: {qualification_id}")

    root = Path(repo_root).resolve()
    for relative_name, expected_hash in lock.get("file_hashes", {}).items():
        relative = Path(relative_name)
        if relative.is_absolute() or ".." in relative.parts:
            raise RuntimeError(f"unsafe path in qualification lock: {relative_name}")
        candidate = (root / relative).resolve()
        if sha256_file(candidate) != expected_hash:
            raise RuntimeError(f"frozen qualification input changed: {relative_name}")
    return lock


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
        raise ValueError(f"unsupported gate comparator: {comparator}")
    return {
        "name": name,
        "observed": observed,
        "comparator": comparator,
        "threshold": threshold,
        "passed": bool(passed),
    }
