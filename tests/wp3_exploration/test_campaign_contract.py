"""Static contract checks for WP3 exploration artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


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


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_exploration_corpus_pins_upstream_and_excludes_holdout() -> None:
    corpus = _load(CAMPAIGN / "data" / "exploration_corpus.json")
    upstream = _load(UPSTREAM_CORPUS)
    assert corpus["executable_splits"] == ["training", "calibration"]
    assert corpus["upstream_corpus_sha256"] == _sha256(UPSTREAM_CORPUS)
    assert all(
        source["required_upstream_split"] != "holdout"
        for source in corpus["trajectory_sources"]
    )
    upstream_holdouts = {
        case["case_id"] for case in upstream["cases"] if case["split"] == "holdout"
    }
    assert set(corpus["quarantined_upstream_holdout_ids"]) == upstream_holdouts


def test_exploration_and_gate_specs_lock_the_claim_boundary() -> None:
    exploration = _load(CAMPAIGN / "exploration_spec.json")
    gate = _load(CAMPAIGN / "publication_gate_spec.json")
    assert exploration["campaign"] == "WP3-EXP-v1"
    assert exploration["interpretation_status"] == "EXPLORATORY_ONLY"
    assert gate["campaign"] == "WP3-PUB-GATE-v1"
    requirement_ids = {item["id"] for item in gate["required_evidence"]}
    assert "sealed_wp3_publication_holdout" in requirement_ids
    assert "candidate_independent_replication" in requirement_ids
    assert "qualified_reduced_or_lifted_vector_field" in requirement_ids


def test_boundary_rejects_legacy_wp3_as_claim_evidence() -> None:
    boundary = (
        REPO_ROOT / "src" / "python" / "wp3_exploration" / "EXPLORATION_BOUNDARY.md"
    ).read_text(encoding="utf-8")
    assert "Every output is `EXPLORATORY_ONLY`" in boundary
    assert "legacy WP3 lifted metrics" in boundary
    assert "hidden" in boundary and "integrability" in boundary


def test_checked_exploration_result_remains_non_claim_bearing() -> None:
    results = _load(CAMPAIGN / "results" / "exploration_results.json")
    gate = _load(CAMPAIGN / "results" / "publication_gate.json")
    report = (CAMPAIGN / "reports" / "wp3_exploration_report.md").read_text(
        encoding="utf-8"
    )
    assert results["interpretation_status"] == "EXPLORATORY_ONLY"
    assert results["publication_gate"]["status"] == "BLOCKED"
    assert gate["status"] == "BLOCKED"
    assert not gate["interpretation_authorized"]
    assert results["search"]["numerical_nullity_after_known_controls"] == 0
    assert results["search"]["dimension_sector_count"] == 9
    implementation_hashes = results["implementation_snapshot"]["file_hashes"]
    assert implementation_hashes
    assert all(
        digest == _sha256(REPO_ROOT / relative_name)
        for relative_name, digest in implementation_hashes.items()
    )
    assert all(
        sector["dimension_signature"]
        and sector["near_null_modes"]
        for sector in results["search"]["sectors"]
    )
    assert "makes no conservation" in report
    assert "does not advance an additional direction" in report
