"""Provenance isolation and publication-gate tests for WP3."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from src.python.wp3_exploration import (
    PublicationGateError,
    ReservedSplitError,
    evaluate_publication_gate,
    require_publishable,
    sample_exploration_split,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = REPO_ROOT / "validation-external" / "wp3-exploration"
UPSTREAM_CORPUS = (
    REPO_ROOT
    / "validation-external"
    / "wp1-n3bp-validation"
    / "data"
    / "qualification_corpus.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_actual_publication_gate_is_blocked_and_fail_closed() -> None:
    gate = evaluate_publication_gate(
        CAMPAIGN / "publication_gate_spec.json",
        CAMPAIGN / "publication_evidence_manifest.json",
        repo_root=REPO_ROOT,
    )
    assert gate["status"] == "BLOCKED"
    assert gate["passed_gate_count"] == 3
    assert gate["required_gate_count"] == 11
    with pytest.raises(PublicationGateError, match="not authorized"):
        require_publishable(gate)
    with pytest.raises(PublicationGateError, match="not authorized"):
        require_publishable(
            {"status": "PASS", "interpretation_authorized": True}
        )


def test_publication_gate_marks_tampered_evidence_invalid() -> None:
    manifest = _load(CAMPAIGN / "publication_evidence_manifest.json")
    manifest["evidence"]["wp1_n3bp_qualification"]["lock_path"] = (
        "validation-external/wp2-ks-validation/reports/"
        "wp2_ks_qualification_lock.json"
    )
    gate = evaluate_publication_gate(
        CAMPAIGN / "publication_gate_spec.json",
        manifest,
        repo_root=REPO_ROOT,
    )
    wp1_gate = next(
        row for row in gate["gates"] if row["id"] == "wp1_n3bp_qualification"
    )
    assert not wp1_gate["passed"]
    assert wp1_gate["observed_status"] == "INVALID"


def test_complete_integrity_checked_artifact_can_open_a_minimal_gate(
    tmp_path: Path,
) -> None:
    evidence_id = "independent_replication"
    artifact = {
        "schema_version": "1.0",
        "evidence_id": evidence_id,
        "status": "PASS",
        "scope": "unit-test fixture",
    }
    canonical = json.dumps(
        artifact, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    artifact["record_payload_sha256"] = hashlib.sha256(canonical).hexdigest()
    artifact_path = tmp_path / "artifact.json"
    artifact_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest = {
        "campaign": "TEST-GATE-v1",
        "evidence": {
            evidence_id: {
                "status": "PASS",
                "artifact_path": "artifact.json",
                "sha256": hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
            }
        }
    }
    spec = {
        "campaign": "TEST-GATE-v1",
        "policy": "test only",
        "required_evidence": [
            {
                "id": evidence_id,
                "kind": "artifact",
                "description": "independent test evidence",
            }
        ],
    }
    gate = evaluate_publication_gate(spec, manifest, repo_root=tmp_path)
    assert gate["status"] == "PASS"
    require_publishable(gate)


def test_non_executable_split_is_refused() -> None:
    corpus = _load(CAMPAIGN / "data" / "exploration_corpus.json")
    upstream = _load(UPSTREAM_CORPUS)
    with pytest.raises(ReservedSplitError, match="not executable"):
        sample_exploration_split(corpus, upstream, "publication_holdout")


def test_collocation_sampling_is_deterministic_and_spatial() -> None:
    corpus = _load(CAMPAIGN / "data" / "exploration_corpus.json")
    upstream = _load(UPSTREAM_CORPUS)
    mini_corpus = {
        "executable_splits": ["training"],
        "execution": corpus["execution"],
        "trajectory_sources": [],
        "collocation_sources": [
            {**corpus["collocation_sources"][0], "count": 4}
        ],
    }
    first = sample_exploration_split(mini_corpus, upstream, "training")
    second = sample_exploration_split(mini_corpus, upstream, "training")
    assert len(first) == 4
    for left, right in zip(first, second, strict=True):
        np.testing.assert_array_equal(left.state.values, right.state.values)
        np.testing.assert_array_equal(left.parameters.masses, right.parameters.masses)

    spatial_measure = []
    for point in first:
        rho = point.state.positions[1] - point.state.positions[0]
        lambda_vector = point.state.positions[2] - point.state.positions[0]
        normal = np.cross(rho, lambda_vector)
        relative_velocity = point.state.velocities[1] - point.state.velocities[0]
        spatial_measure.append(abs(float(np.dot(normal, relative_velocity))))
    assert max(spatial_measure) > 1.0e-6
