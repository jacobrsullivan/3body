from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "validation-external/wp3-upstairs-candidate-v2"


def _json(relative: str):
    return json.loads((CAMPAIGN / relative).read_text(encoding="utf-8"))


def test_v2_search_declares_fail_closed_spatial_inputs() -> None:
    spec = _json("search_spec.json")
    assert spec["campaign"] == "WP3-UP-CAND-v2"
    assert "every consumed spatial" in spec["staged_policy"]["SEARCH_READY"]
    shell = (CAMPAIGN / "run_search.sh").read_text(encoding="utf-8")
    assert "--scope validation-external/wp3-spatial-validation-v2" in shell
    assert "--scope src/python/wp3_exploration_v2/__init__.py" in shell


def test_v2_runner_checks_spatial_results_against_record() -> None:
    runner = (CAMPAIGN / "scripts/run_search.py").read_text(encoding="utf-8")
    assert "_verify_spatial_inputs" in runner
    assert "results_sha256" in runner
    assert "spatial_inputs_hash_verified" in runner


def test_v2_final_record_binds_post_search_outputs() -> None:
    finalizer = (CAMPAIGN / "scripts/finalize_search.py").read_text(encoding="utf-8")
    assert "results_sha256" in finalizer
    assert "gate_sha256" in finalizer
    assert "record_payload_sha256" in finalizer
    assert "search results and staged gate are inconsistent" in finalizer


def test_v2_sealed_trigger_is_conditioned_on_search_readiness() -> None:
    runner = (CAMPAIGN / "scripts/run_search.py").read_text(encoding="utf-8")
    assert 'if search_ready != "PASS"' in runner
    assert 'sealed_qualification = "BLOCKED"' in runner
    assert '"SEALED_QUALIFICATION": sealed_qualification' in runner


def test_v2_corpus_has_only_development_and_calibration() -> None:
    corpus = _json("data/search_corpus.json")
    assert {case["split"] for case in corpus["cases"]} == {"development", "calibration"}


def test_v2_grammar_includes_energy_and_mass_parameters() -> None:
    spec = _json("search_spec.json")
    assert spec["library"]["parameter_variables"] == ["fixed_energy", "mass_s2", "mass_s3"]
    assert spec["library"]["monomial_count"] == 1120
    assert spec["library"]["total_feature_count"] == 1126
