"""Contract checks that remain valid before and after WP2-UP holdout."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "validation-external/wp2-up-validation"


def _json(relative: str):
    with (CAMPAIGN / relative).open(encoding="utf-8") as stream:
        return json.load(stream)


def test_claim_excludes_simultaneous_regularization_and_integrability() -> None:
    spec = _json("qualification_spec.json")
    boundary = spec["evidence_boundary"].lower()
    assert "simultaneous" in boundary
    assert "integrability" in boundary
    assert spec["gates"]["structural_simultaneous_regularization_qualified"] == 0


def test_corpus_has_external_development_calibration_and_holdout() -> None:
    corpus = _json("data/qualification_corpus.json")
    counts = {
        split: sum(case["split"] == split for case in corpus["cases"])
        for split in ("development", "calibration", "holdout")
    }
    assert counts == {"development": 48, "calibration": 24, "holdout": 12}
    for split in counts:
        families = {
            case["source_family"]
            for case in corpus["cases"]
            if case["split"] == split
        }
        assert families == {"equal_mass_plummer", "mass_4_2_1_plummer"}


def test_unsealed_splits_pass_every_frozen_gate() -> None:
    for split in ("development", "calibration"):
        evaluation = _json(f"results/{split}_evaluation.json")
        assert evaluation["status"] == "PASS"
        assert all(gate["passed"] for gate in evaluation["gates"])


def test_holdout_requires_lock_in_runner_contract() -> None:
    script = (CAMPAIGN / "scripts/run_qualification.py").read_text(encoding="utf-8")
    assert "holdout execution requires the WP2-UP lock" in script
    assert "verify_lock" in script
