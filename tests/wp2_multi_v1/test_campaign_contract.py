from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "validation-external/wp2-multi-validation"


def test_locked_specification_is_bounded_and_fail_closed() -> None:
    spec = json.loads((CAMPAIGN / "qualification_spec.json").read_text())
    boundary = spec["evidence_boundary"].lower()
    assert spec["specification_status"] == "LOCKED_BY_SEPARATE_RECORD"
    assert "triple collision" in boundary
    assert "integrability" in boundary
    assert spec["model"]["time_law"] == "dt/ds=g=R1*R2*R3 in every chart."
    assert spec["model"]["gauge_group"].startswith("T2=S1xS1")
    assert spec["gates"]["structural_triple_collision_qualified"] == 0


def test_corpus_allocation_matches_the_locked_claim() -> None:
    path = CAMPAIGN / "data/qualification_corpus.json"
    if not path.exists():
        return
    corpus = json.loads(path.read_text())
    assert corpus["category_counts"] == {
        "exact_passage": 9,
        "generic": 18,
        "near_binary": 18,
    }
    assert corpus["split_counts"] == {
        "calibration": 12,
        "development": 21,
        "holdout": 12,
    }
    assert len({case["case_id"] for case in corpus["cases"]}) == 45
