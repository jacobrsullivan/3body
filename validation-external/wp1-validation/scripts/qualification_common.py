"""Shared deterministic utilities for the WP1 qualification campaign."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import pyarrow.parquet as pq


STATE_KEYS = ("x", "y", "z", "vx", "vy", "vz")


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
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


def resolve_manifest_path(manifest_path: str | Path, value: str | Path) -> Path:
    """Resolve a portable path stored relative to its manifest."""
    path = Path(value)
    if path.is_absolute():
        return path.resolve()
    return (Path(manifest_path).resolve().parent / path).resolve()


def repository_root(path: str | Path) -> Path:
    """Locate the enclosing Git worktree without invoking Git."""
    candidate = Path(path).resolve()
    if candidate.is_file():
        candidate = candidate.parent
    for directory in (candidate, *candidate.parents):
        if (directory / ".git").exists():
            return directory
    raise RuntimeError(f"No Git repository contains {path}")


def verify_qualification_lock(
    lock_path: str | Path, repo_root: str | Path
) -> dict[str, Any]:
    """Verify lock integrity and every repository-relative frozen file hash."""
    lock = load_json(lock_path)
    expected_lock_hash = str(lock.get("lock_sha256", ""))
    unsigned = dict(lock)
    unsigned.pop("lock_sha256", None)
    actual_lock_hash = sha256_bytes(canonical_json(unsigned))
    if not expected_lock_hash or actual_lock_hash != expected_lock_hash:
        raise RuntimeError(
            "Qualification lock integrity failure: "
            f"calculated {actual_lock_hash}, recorded {expected_lock_hash or '<missing>'}"
        )

    root = Path(repo_root).resolve()
    for filename, expected in lock.get("file_hashes", {}).items():
        relative = Path(filename)
        if relative.is_absolute():
            raise RuntimeError(
                f"Qualification lock contains an absolute path: {filename}"
            )
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise RuntimeError(
                f"Qualification lock path escapes the repository: {filename}"
            ) from exc
        actual = sha256_file(candidate)
        if actual != expected:
            raise RuntimeError(
                f"Qualification lock violation: {filename} is {actual}, expected {expected}"
            )
    return lock


def load_spec(path: str | Path) -> dict[str, Any]:
    spec = load_json(path)
    if spec.get("schema_version") != "1.0":
        raise ValueError(
            f"Unsupported qualification spec: {spec.get('schema_version')}"
        )
    return spec


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


def write_csv(path: str | Path, rows: Sequence[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError("Refusing to write an empty qualification CSV")
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open("r", newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def finite_float(value: Any) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return result if np.isfinite(result) else float("nan")


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "pass"}


def state_from_row(row: dict[str, Any]) -> np.ndarray:
    return np.array([finite_float(row.get(key)) for key in STATE_KEYS], dtype=float)


def load_corpus(path: str | Path, split: str | None = None) -> list[dict[str, Any]]:
    rows = pq.read_table(path).to_pylist()
    if split is not None:
        rows = [row for row in rows if row["split"] == split]
    return rows


def stable_rank(token: str, salt: str) -> str:
    return sha256_bytes(f"{salt}:{token}".encode("utf-8"))


def deterministic_subset(
    rows: Sequence[dict[str, Any]],
    maximum: int,
    *,
    salt: str,
    group_keys: Sequence[str] = ("system", "family", "stability_regime"),
) -> list[dict[str, Any]]:
    """Select a reproducible, group-covering subset without random state."""
    if maximum <= 0:
        return []
    ordered = sorted(rows, key=lambda row: stable_rank(str(row["catalog_id"]), salt))
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in ordered:
        groups[tuple(row.get(key) for key in group_keys)].append(row)

    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    group_order = sorted(
        groups,
        key=lambda key: stable_rank(
            "|".join(str(part) for part in key), f"{salt}:groups"
        ),
    )
    if len(group_order) > maximum:
        # Round-robin over the first grouping dimension (normally system) so a
        # fine-grained cap cannot exhaust alphabetically before later systems.
        buckets: dict[str, list[tuple[Any, ...]]] = defaultdict(list)
        for key in group_order:
            buckets[str(key[0])].append(key)
        group_order = []
        bucket_names = sorted(buckets)
        while len(group_order) < maximum and any(buckets.values()):
            for name in bucket_names:
                if buckets[name] and len(group_order) < maximum:
                    group_order.append(buckets[name].pop(0))
    for key in group_order[:maximum]:
        row = groups[key][0]
        selected.append(row)
        selected_ids.add(str(row["catalog_id"]))
    for row in ordered:
        if len(selected) >= maximum:
            break
        if str(row["catalog_id"]) not in selected_ids:
            selected.append(row)
            selected_ids.add(str(row["catalog_id"]))
    return selected


def percentile(values: Iterable[Any], quantile: float) -> float:
    finite = np.array(
        [finite_float(value) for value in values if np.isfinite(finite_float(value))]
    )
    return float(np.percentile(finite, quantile)) if len(finite) else float("nan")


def maximum(values: Iterable[Any]) -> float:
    finite = np.array(
        [finite_float(value) for value in values if np.isfinite(finite_float(value))]
    )
    return float(np.max(finite)) if len(finite) else float("nan")


def rate(values: Iterable[Any]) -> float:
    materialized = list(values)
    return (
        float(sum(as_bool(value) for value in materialized) / len(materialized))
        if materialized
        else 0.0
    )
