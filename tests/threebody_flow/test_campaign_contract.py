"""Qualification contract checks for WP2-3BFLOWQ-v1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "validation-external/wp2-threebody-flow-validation"
SPATIAL = ROOT / "validation-external/wp3-spatial-validation-v2"
KS = ROOT / "validation-external/wp2-ks-validation"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_flow_prerequisites_pin_passing_records_by_content() -> None:
    specification = _json(CAMPAIGN / "qualification_spec.json")
    spatial_record_path = SPATIAL / "reports/wp3_spatial_v2_qualification_record.json"
    spatial_record = _json(spatial_record_path)
    expected_spatial = specification["prerequisites"]["wp1_spatial_n3bp"]
    assert spatial_record["status"] == "PASS"
    assert spatial_record["qualification_id"] == expected_spatial["qualification_id"]
    assert spatial_record["lock_sha256"] == expected_spatial["lock_sha256"]
    assert _sha(spatial_record_path) == expected_spatial["record_sha256"]

    ks_record_path = KS / "reports/wp2_ks_qualification_record.json"
    ks_record = _json(ks_record_path)
    expected_ks = specification["prerequisites"]["wp2_kepler_ks"]
    assert ks_record["status"] == "PASS"
    assert ks_record["qualification_id"] == expected_ks["qualification_id"]
    assert ks_record["lock_sha256"] == expected_ks["lock_sha256"]
    assert _sha(ks_record_path) == expected_ks["record_sha256"]


def test_flow_corpus_uses_whole_external_cases_and_reserved_split() -> None:
    corpus = _json(CAMPAIGN / "data/qualification_corpus.json")
    spatial = _json(SPATIAL / "data/qualification_corpus.json")
    source_splits = {case["case_id"]: case["split"] for case in spatial["cases"]}
    assert len(corpus["cases"]) == 34
    assert {
        split: sum(case["split"] == split for case in corpus["cases"])
        for split in ("development", "calibration", "holdout")
    } == {"development": 16, "calibration": 12, "holdout": 6}
    assert all(
        source_splits[case["source_case_id"]] == case["split"]
        for case in corpus["cases"]
    )
    assert all(case["checkpoint_indices"] == [0, 2, 4, 6, 8] for case in corpus["cases"])


def test_unsealed_flow_splits_pass_and_global_sundman_remains_excluded() -> None:
    for split in ("development", "calibration"):
        evaluation = _json(CAMPAIGN / f"results/{split}_evaluation.json")
        assert evaluation["status"] == "PASS"
        assert all(gate["passed"] for gate in evaluation["gates"])
    specification = _json(CAMPAIGN / "qualification_spec.json")
    assert specification["gates"]["structural_global_sundman_qualified"] == 0
    boundary = (ROOT / "src/python/threebody_flow/QUALIFICATION_BOUNDARY.md").read_text(
        encoding="utf-8"
    )
    assert "global regularized time transformation would be a separate model" in boundary
