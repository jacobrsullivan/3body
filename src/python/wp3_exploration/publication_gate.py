"""Fail-closed publication gate for interpreting WP3 screening results."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


class PublicationGateError(RuntimeError):
    """Raised when publication-level interpretation is not authorized."""


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_json(value: str | Path | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    with Path(value).open("r", encoding="utf-8") as stream:
        loaded = json.load(stream)
    if not isinstance(loaded, dict):
        raise PublicationGateError("publication gate JSON must contain an object")
    return loaded


def _resolve_repo_path(repo_root: Path, relative_name: str) -> Path:
    relative = Path(relative_name)
    if relative.is_absolute() or ".." in relative.parts:
        raise PublicationGateError(f"unsafe evidence path: {relative_name}")
    resolved = (repo_root / relative).resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as error:
        raise PublicationGateError(
            f"evidence path escapes repository: {relative_name}"
        ) from error
    return resolved


def _verify_record(record_path: Path, expected_id: str) -> dict[str, Any]:
    if not record_path.is_file():
        raise PublicationGateError(f"qualification record is missing: {record_path}")
    record = _load_json(record_path)
    recorded_hash = str(record.get("record_payload_sha256", ""))
    unsigned = dict(record)
    unsigned.pop("record_payload_sha256", None)
    actual_hash = _sha256_bytes(_canonical_json(unsigned))
    if not recorded_hash or recorded_hash != actual_hash:
        raise PublicationGateError(
            f"qualification record integrity failure: {record_path}"
        )
    if record.get("qualification_id") != expected_id:
        raise PublicationGateError(
            f"unexpected qualification ID in {record_path}: "
            f"{record.get('qualification_id')}"
        )
    if record.get("status") != "PASS":
        raise PublicationGateError(
            f"qualification {expected_id} is {record.get('status')}"
        )
    return record


def _verify_lock(lock_path: Path, repo_root: Path, expected_id: str) -> dict[str, Any]:
    if not lock_path.is_file():
        raise PublicationGateError(f"qualification lock is missing: {lock_path}")
    lock = _load_json(lock_path)
    recorded_hash = str(lock.get("lock_sha256", ""))
    unsigned = dict(lock)
    unsigned.pop("lock_sha256", None)
    actual_hash = _sha256_bytes(_canonical_json(unsigned))
    if not recorded_hash or recorded_hash != actual_hash:
        raise PublicationGateError(f"qualification lock integrity failure: {lock_path}")
    if lock.get("qualification_id") != expected_id:
        raise PublicationGateError(
            f"unexpected qualification ID in {lock_path}: "
            f"{lock.get('qualification_id')}"
        )
    file_hashes = lock.get("file_hashes")
    if not isinstance(file_hashes, Mapping) or not file_hashes:
        raise PublicationGateError(
            f"qualification lock has no frozen file hashes: {lock_path}"
        )
    for relative_name, expected_hash in file_hashes.items():
        candidate = _resolve_repo_path(repo_root, str(relative_name))
        if not candidate.is_file() or _sha256_file(candidate) != expected_hash:
            raise PublicationGateError(
                f"frozen qualification input changed: {relative_name}"
            )
    return lock


def _evaluate_qualification(
    requirement: Mapping[str, Any],
    evidence: Mapping[str, Any],
    repo_root: Path,
) -> dict[str, Any]:
    expected_id = str(requirement["qualification_id"])
    record_path = _resolve_repo_path(repo_root, str(evidence["record_path"]))
    lock_path = _resolve_repo_path(repo_root, str(evidence["lock_path"]))
    record = _verify_record(record_path, expected_id)
    lock = _verify_lock(lock_path, repo_root, expected_id)
    if record.get("lock_sha256") != lock.get("lock_sha256"):
        raise PublicationGateError(
            f"record and lock disagree for qualification {expected_id}"
        )
    for field in (
        "base_git_commit",
        "code_snapshot_sha256",
        "corpus_sha256",
        "holdout_ids_sha256",
        "source_manifest_sha256",
        "spec_sha256",
    ):
        if record.get(field) != lock.get(field):
            raise PublicationGateError(
                f"record and lock disagree on {field} for {expected_id}"
            )
    evidence_files = record.get("evidence_files")
    if not isinstance(evidence_files, Mapping) or not evidence_files:
        raise PublicationGateError(
            f"qualification record has no evidence files: {expected_id}"
        )
    for evidence_name, evidence_file in evidence_files.items():
        if not isinstance(evidence_file, Mapping):
            raise PublicationGateError(
                f"invalid evidence file entry {evidence_name}: {expected_id}"
            )
        candidate = _resolve_repo_path(repo_root, str(evidence_file.get("path", "")))
        if not candidate.is_file() or _sha256_file(candidate) != evidence_file.get(
            "sha256"
        ):
            raise PublicationGateError(
                f"qualification evidence changed: {evidence_name} ({expected_id})"
            )
    return {
        "passed": True,
        "observed_status": "PASS",
        "qualification_id": expected_id,
        "record_sha256": _sha256_file(record_path),
        "lock_sha256": lock["lock_sha256"],
    }


def _evaluate_artifact(
    requirement: Mapping[str, Any],
    evidence: Mapping[str, Any],
    repo_root: Path,
) -> dict[str, Any]:
    status = str(evidence.get("status", "MISSING"))
    result: dict[str, Any] = {
        "passed": status == "PASS",
        "observed_status": status,
    }
    if "reason" in evidence:
        result["reason"] = str(evidence["reason"])
    if status != "PASS":
        return result

    artifact_name = evidence.get("artifact_path")
    expected_hash = evidence.get("sha256")
    if not artifact_name or not expected_hash:
        return {
            "passed": False,
            "observed_status": "INVALID",
            "reason": "PASS evidence must declare artifact_path and sha256",
        }
    artifact_path = _resolve_repo_path(repo_root, str(artifact_name))
    if not artifact_path.is_file():
        return {
            "passed": False,
            "observed_status": "INVALID",
            "reason": f"artifact is missing: {artifact_name}",
        }
    actual_hash = _sha256_file(artifact_path)
    if actual_hash != expected_hash:
        return {
            "passed": False,
            "observed_status": "INVALID",
            "reason": "artifact hash does not match evidence manifest",
        }
    try:
        artifact = _load_json(artifact_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return {
            "passed": False,
            "observed_status": "INVALID",
            "reason": f"artifact is not a valid JSON evidence record: {error}",
        }
    recorded_payload_hash = str(artifact.get("record_payload_sha256", ""))
    unsigned = dict(artifact)
    unsigned.pop("record_payload_sha256", None)
    actual_payload_hash = _sha256_bytes(_canonical_json(unsigned))
    if not recorded_payload_hash or recorded_payload_hash != actual_payload_hash:
        return {
            "passed": False,
            "observed_status": "INVALID",
            "reason": "artifact evidence-record integrity check failed",
        }
    if artifact.get("evidence_id") != requirement.get("id"):
        return {
            "passed": False,
            "observed_status": "INVALID",
            "reason": "artifact evidence_id does not match gate requirement",
        }
    if artifact.get("status") != "PASS":
        return {
            "passed": False,
            "observed_status": "INVALID",
            "reason": "artifact evidence record is not PASS",
        }
    if not artifact.get("schema_version"):
        return {
            "passed": False,
            "observed_status": "INVALID",
            "reason": "artifact evidence record has no schema_version",
        }
    result["artifact_path"] = str(artifact_name)
    result["sha256"] = actual_hash
    result["evidence_class"] = str(requirement.get("evidence_class", "unspecified"))
    return result


def evaluate_publication_gate(
    specification: str | Path | Mapping[str, Any],
    evidence_manifest: str | Path | Mapping[str, Any],
    *,
    repo_root: str | Path,
) -> dict[str, Any]:
    """Evaluate every required item and return PASS only when all pass."""

    spec = _load_json(specification)
    manifest = _load_json(evidence_manifest)
    root = Path(repo_root).resolve()
    requirements = spec.get("required_evidence")
    items = manifest.get("evidence")
    if not isinstance(requirements, list) or not requirements:
        raise PublicationGateError("publication gate has no required evidence")
    if not isinstance(items, Mapping):
        raise PublicationGateError("evidence manifest has no evidence map")
    if manifest.get("campaign") != spec.get("campaign"):
        raise PublicationGateError(
            "publication gate specification and evidence manifest campaigns differ"
        )
    requirement_ids = [str(requirement.get("id", "")) for requirement in requirements]
    if "" in requirement_ids or len(requirement_ids) != len(set(requirement_ids)):
        raise PublicationGateError(
            "publication gate requirement IDs must be non-empty and unique"
        )

    gates: list[dict[str, Any]] = []
    for requirement in requirements:
        requirement_id = str(requirement["id"])
        kind = str(requirement["kind"])
        evidence = items.get(requirement_id)
        gate: dict[str, Any] = {
            "id": requirement_id,
            "kind": kind,
            "description": str(requirement["description"]),
        }
        if not isinstance(evidence, Mapping):
            gate.update(
                {
                    "passed": False,
                    "observed_status": "MISSING",
                    "reason": "evidence item is absent from the manifest",
                }
            )
        else:
            try:
                if kind == "qualification":
                    gate.update(
                        _evaluate_qualification(requirement, evidence, root)
                    )
                elif kind == "artifact":
                    gate.update(_evaluate_artifact(requirement, evidence, root))
                else:
                    raise PublicationGateError(
                        f"unsupported publication evidence kind: {kind}"
                    )
            except (KeyError, OSError, ValueError, PublicationGateError) as error:
                gate.update(
                    {
                        "passed": False,
                        "observed_status": "INVALID",
                        "reason": f"{type(error).__name__}: {error}",
                    }
                )
        gates.append(gate)

    status = "PASS" if all(gate["passed"] for gate in gates) else "BLOCKED"
    return {
        "schema_version": "1.0",
        "campaign": str(spec["campaign"]),
        "status": status,
        "interpretation_authorized": status == "PASS",
        "policy": str(spec["policy"]),
        "passed_gate_count": sum(bool(gate["passed"]) for gate in gates),
        "required_gate_count": len(gates),
        "gates": gates,
    }


def require_publishable(gate_result: Mapping[str, Any]) -> None:
    """Raise unless a complete gate result authorizes interpretation."""

    gates = gate_result.get("gates")
    required_count = gate_result.get("required_gate_count")
    passed_count = gate_result.get("passed_gate_count")
    complete = (
        isinstance(gates, list)
        and bool(gates)
        and isinstance(required_count, int)
        and isinstance(passed_count, int)
        and required_count == len(gates)
        and passed_count == required_count
        and all(gate.get("passed") is True for gate in gates)
    )
    authorized = (
        gate_result.get("status") == "PASS"
        and gate_result.get("interpretation_authorized") is True
        and complete
    )
    if not authorized:
        blocked = [
            str(gate.get("id"))
            for gate in gates or []
            if not gate.get("passed", False)
        ]
        suffix = f": {', '.join(blocked)}" if blocked else ""
        raise PublicationGateError(
            "WP3 publication interpretation is not authorized" + suffix
        )
