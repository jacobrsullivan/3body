from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = REPO_ROOT / "validation-external/wp2-threebody-validation"


def _load(relative: str) -> dict:
    return json.loads((CAMPAIGN / relative).read_text(encoding="utf-8"))


def test_spec_is_bounded_and_requires_both_frozen_pass_records() -> None:
    spec = _load("qualification_spec.json")
    assert spec["campaign"] == "WP2-3BRQ-v1"
    assert spec["prerequisites"]["wp2_ks"]["qualification_id"].startswith("WP2KSQ-v1-")
    assert spec["prerequisites"]["wp1_n3bp"]["qualification_id"].startswith(
        "WP1Q-N3BP-v1-"
    )
    boundary = spec["evidence_boundary"].lower()
    assert "does not qualify reduced hamilton equations" in boundary
    assert "simultaneous three-body sundman" in boundary
    assert "production periodic-orbit catalogue" in boundary


def test_corpus_has_disjoint_nonempty_splits_and_reserved_holdout() -> None:
    corpus = _load("data/qualification_corpus.json")
    identifiers = [case["case_id"] for case in corpus["cases"]]
    assert len(identifiers) == len(set(identifiers))
    for split in ("development", "calibration", "holdout"):
        assert any(case["split"] == split for case in corpus["cases"])
    assert all(
        case["case_id"].startswith("hold_")
        for case in corpus["cases"]
        if case["split"] == "holdout"
    )


def test_source_manifest_names_compositional_not_independent_evidence() -> None:
    manifest = _load("sources/manifest.json")
    assert len(manifest["composition_inputs"]) == 3
    assert "does not present" in manifest["independence_note"]
