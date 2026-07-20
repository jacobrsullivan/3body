"""Contract tests for the fresh spatial v2 qualification campaign."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
V1 = ROOT / "validation-external/wp3-spatial-validation"
V2 = ROOT / "validation-external/wp3-spatial-validation-v2"
COMMITMENTS = (
    ROOT
    / "validation-external/wp3-v2-exploration/sealed/publication_holdout_commitments.json"
)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v2_corpus_is_fresh_balanced_and_exclusion_verified() -> None:
    first = _json(V1 / "data/qualification_corpus.json")
    second = _json(V2 / "data/qualification_corpus.json")
    first_hashes = {case["source_line_sha256"] for case in first["cases"]}
    second_hashes = {case["source_line_sha256"] for case in second["cases"]}
    assert not (first_hashes & second_hashes)
    assert second["publication_reserve_exclusion_verified"] is True
    assert second["excluded_previous_case_count"] == 84
    assert second["excluded_publication_reserve_count"] == 24
    assert second["sealed_commitments_sha256"] == hashlib.sha256(
        COMMITMENTS.read_bytes()
    ).hexdigest()
    assert len(second["cases"]) == 84
    assert {
        split: sum(case["split"] == split for case in second["cases"])
        for split in ("development", "calibration", "holdout")
    } == {"development": 48, "calibration": 24, "holdout": 12}


def test_v2_remediation_is_fixed_before_holdout_and_v1_is_immutable_failure() -> None:
    specification = _json(V2 / "qualification_spec.json")
    predecessor = _json(V1 / "reports/wp3_spatial_qualification_record.json")
    assert predecessor["qualification_id"] == specification["predecessor"]["qualification_id"]
    assert predecessor["status"] == specification["predecessor"]["status"] == "FAIL"
    assert specification["execution"]["production_validation_duration"] == 0.5
    assert specification["gates"]["production_validation_horizon_max"] == 0.5


def test_v2_selected_payload_contains_only_v2_qualification_rows() -> None:
    corpus = _json(V2 / "data/qualification_corpus.json")
    selected_hashes = {
        hashlib.sha256(line.encode("ascii")).hexdigest()
        for line in (V2 / "sources/brutus_selected_rows.txt")
        .read_text(encoding="ascii")
        .splitlines()
        if line and not line.startswith("#") and len(line.split()) == 46
    }
    assert selected_hashes == {
        case["source_line_sha256"] for case in corpus["cases"]
    }
