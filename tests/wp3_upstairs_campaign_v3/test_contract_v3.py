from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from src.python.wp3_upstairs_v3 import known_module_coefficients


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "validation-external/wp3-upstairs-candidate-v3"


def _json(relative: str):
    return json.loads((CAMPAIGN / relative).read_text(encoding="utf-8"))


def test_v3_spec_declares_exact_module_and_remediation_boundary() -> None:
    spec = _json("search_spec.json")
    assert spec["campaign"] == "WP3-UP-CAND-v3"
    assert spec["library"]["search_feature_count"] == 1120
    assert spec["library"]["exact_constraint_ideal_count"] == 18
    assert spec["library"]["exact_angular_module_count"] == 12
    assert spec["library"]["exact_known_module_rank"] == 30
    assert "previously examined" in spec["evidence_boundary"]


def test_v3_known_module_is_coefficient_independent() -> None:
    module = known_module_coefficients()
    matrix = np.column_stack(tuple(module.values()))
    assert matrix.shape == (1120, 30)
    assert np.linalg.matrix_rank(matrix, tol=1e-12) == 30
    assert sum(name.startswith("known:") and "*" in name for name in module) == 9


def test_v3_runner_uses_physical_and_s1_derivatives() -> None:
    runner = (CAMPAIGN / "scripts/run_search.py").read_text(encoding="utf-8")
    assert "search_quotient_modes" in runner
    assert "s1_generator" in runner
    assert "known_module_coefficients" in runner
    assert "known_module_projection_residual" in runner
    assert "physical_point_id" in runner


def test_v3_final_record_uses_generalized_quotient_metrics() -> None:
    finalizer = (CAMPAIGN / "scripts/finalize_search.py").read_text(encoding="utf-8")
    assert "observable_value_rank" in finalizer
    assert "value_nuisance_derivative_rank" in finalizer
    assert "exact_known_module_rank" in finalizer
    assert "smallest_generalized_lie_value_singular_value" in finalizer


def test_v3_corpus_excludes_publication_reserve() -> None:
    corpus = _json("data/search_corpus.json")
    assert corpus["corpus_id"] == "wp3-upstairs-v3-exact-module-frozen-corpus"
    assert {case["split"] for case in corpus["cases"]} == {"development", "calibration"}
