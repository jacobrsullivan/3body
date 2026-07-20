from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from src.python.wp1_catalogue_v1.qualification import (
    build_corpus,
    canonical_json,
    sha256_bytes,
    sha256_file,
    verify_lock,
)


def _row(index: int, lpoint: str, x: float) -> dict[str, object]:
    return {
        "x": x,
        "y": 0.0,
        "z": 0.0,
        "vx": 0.0,
        "vy": 0.1 + index * 1e-4,
        "vz": 0.0,
        "period": 3.0,
        "jacobi": 3.1,
        "family": "lyapunov",
        "lpoint": lpoint,
        "branch": "",
        "stability": 100.0,
    }


def test_corpus_partitions_are_balanced_disjoint_and_deterministic(tmp_path: Path):
    repo = tmp_path / "repo"
    campaign = repo / "validation-external/wp1-catalogue-validation"
    source = repo / "validation-external/wp1-validation/data/jpl/normalized.parquet"
    source.parent.mkdir(parents=True)
    campaign.mkdir(parents=True)
    rows = []
    for index in range(8):
        rows.append(_row(index, "L1", 0.82 - index * 0.001))
        rows.append(_row(index + 20, "L2", 1.14 - index * 0.001))
    pq.write_table(pa.Table.from_pylist(rows), source)
    spec = {
        "external_source": {"required_rows": len(rows)},
        "model": {"mu": 0.012150585609624},
        "sampling": {
            "salt": "test",
            "per_lpoint": {"development": 2, "calibration": 1, "holdout": 1},
        },
        "generation": {
            "branches": {
                "L1": {"amplitude_min": 0.001, "amplitude_max": 0.1},
                "L2": {"amplitude_min": 0.001, "amplitude_max": 0.1},
            }
        },
    }
    spec_path = campaign / "qualification_spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    corpus = campaign / "data/corpus.parquet"
    manifest_path = campaign / "data/corpus_manifest.json"
    holdout_path = campaign / "data/holdout_ids.json"
    first = build_corpus(spec_path, source, corpus, manifest_path, holdout_path)
    selected = pq.read_table(corpus).to_pylist()
    assert first["split_counts"] == {"calibration": 2, "development": 4, "holdout": 2}
    identifiers = [row["catalog_id"] for row in selected]
    assert len(identifiers) == len(set(identifiers))
    assert first["partition_disjoint"] is True

    first_ids = [(row["catalog_id"], row["split"]) for row in selected]
    corpus.unlink()
    manifest_path.unlink()
    holdout_path.unlink()
    build_corpus(spec_path, source, corpus, manifest_path, holdout_path)
    second_ids = [(row["catalog_id"], row["split"]) for row in pq.read_table(corpus).to_pylist()]
    assert second_ids == first_ids


def test_lock_detects_frozen_file_tampering(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    frozen = repo / "frozen.txt"
    frozen.write_text("frozen", encoding="utf-8")
    unsigned = {
        "schema_version": "1.0",
        "file_hashes": {"frozen.txt": sha256_file(frozen)},
    }
    lock = {**unsigned, "lock_sha256": sha256_bytes(canonical_json(unsigned))}
    lock_path = repo / "lock.json"
    lock_path.write_text(json.dumps(lock), encoding="utf-8")
    verify_lock(lock_path, repo)
    frozen.write_text("changed", encoding="utf-8")
    with pytest.raises(RuntimeError, match="lock violation"):
        verify_lock(lock_path, repo)


def test_lock_detects_its_own_tampering(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    unsigned = {"schema_version": "1.0", "file_hashes": {}}
    lock = {**unsigned, "lock_sha256": sha256_bytes(canonical_json(unsigned))}
    lock_path = repo / "lock.json"
    lock_path.write_text(json.dumps(lock), encoding="utf-8")
    lock["schema_version"] = "2.0"
    lock_path.write_text(json.dumps(lock), encoding="utf-8")
    with pytest.raises(RuntimeError, match="integrity failure"):
        verify_lock(lock_path, repo)
