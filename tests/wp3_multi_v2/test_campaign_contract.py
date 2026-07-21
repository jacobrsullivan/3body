from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pytest

from src.python.wp1_catalogue_n3bp_v1 import canonical_section_state
from src.python.wp3_multi_v2 import structural_zero_feature_indices


ROOT = Path(__file__).resolve().parents[2]
VALIDATION = ROOT / "validation-external"
CAMPAIGN = VALIDATION / "wp3-multi-candidate-v2"
sys.path.insert(0, str(VALIDATION))
from validation_external_import import campaign_module  # noqa: E402


def _module(relative: str, name: str):
    return campaign_module(CAMPAIGN / relative, name)


def test_specification_lock_predecessor_and_reserve_are_intact() -> None:
    common = _module("scripts/campaign_common.py", "_wp3_multi_v2_test_common")
    spec_path = CAMPAIGN / "search_spec.json"
    spec = json.loads(spec_path.read_text())
    lock = common.verify_specification_lock(spec_path)
    assert lock["campaign"] == "WP3-MULTI-CAND-v2"
    predecessor = common.verify_wp3_v1_prerequisite(
        spec["prerequisites"]["wp3_multi_v1"],
        lock_path=VALIDATION
        / "wp3-multi-candidate-v1/reports/wp3_multi_v1_search_lock.json",
        record_path=VALIDATION
        / "wp3-multi-candidate-v1/reports/wp3_multi_v1_search_record.json",
        gate_path=VALIDATION / "wp3-multi-candidate-v1/results/publication_gate.json",
    )
    assert predecessor["status"] == "COMPLETE_BOUNDED_NULL_RESULT"
    reserve = common.verify_publication_reserve(
        VALIDATION / "wp3-v2-exploration/sealed/publication_holdout_commitments.json",
        spec["prerequisites"]["sealed_publication_reserve_sha256"],
    )
    assert reserve["status"] == "SEALED_UNEXECUTED"
    assert reserve["source_rows_present"] is False


def test_single_physical_point_produces_one_structurally_invariant_row() -> None:
    runner = _module("scripts/run_search.py", "_wp3_multi_v2_test_runner")
    spec = json.loads((CAMPAIGN / "search_spec.json").read_text())
    state = canonical_section_state(
        1.0,
        1.0,
        -0.37200864,
        1.21800411,
        0.45310805,
        7.53971451,
    )
    corpus = {
        "cases": [
            {
                "case_id": "tiny",
                "split": "development",
                "source_kind": "deterministic_spatial_collocation",
                "source_family": "tiny_family",
                "positions": state[:9].reshape(3, 3).tolist(),
                "velocities": state[9:].reshape(3, 3).tolist(),
                "masses": [1.0, 1.0, 1.0],
                "length_scale": 1.0,
            }
        ]
    }
    rows = runner._build_rows(
        "development",
        spec,
        corpus,
        spatial_definitions={},
        spatial_results={},
        wp1_candidates={},
    )
    assert rows.values.shape == (1, 285)
    assert rows.derivatives.shape == (1, 285)
    zeros = np.asarray(structural_zero_feature_indices())
    assert np.array_equal(rows.values[:, zeros], np.zeros((1, 36)))
    assert np.array_equal(rows.derivatives[:, zeros], np.zeros((1, 36)))
    assert rows.group_count == 1
    assert rows.physical_point_count == 1
    assert rows.minimum_pair_separation_scaled_min > 0.1
    assert rows.minimum_denominator_abs > 0.1
    assert rows.gauge_orbit_spread_max < 1e-11
    assert rows.chart_overlap_spread_max < 1e-11
    assert rows.body_permutation_spread_max < 1e-13
    assert rows.rotation_spread_max < 1e-13


def test_publication_gate_is_fail_closed_before_candidate_interpretation() -> None:
    gate = _module(
        "scripts/evaluate_publication_gate.py",
        "_wp3_multi_v2_test_publication_gate",
    )
    bounded_null = gate.decide_publication_gate(
        search_status="COMPLETE_BOUNDED_NULL_RESULT",
        candidate_count=0,
        null_certified=True,
    )
    assert bounded_null["PUBLICATION_GATE"] == "PASS_BOUNDED_NULL_ONLY"
    assert bounded_null["INTERPRETATION_AUTHORIZATION"] == "BOUNDED_NULL_ONLY"

    unresolved = gate.decide_publication_gate(
        search_status="CANDIDATE_SUBSPACE_REQUIRES_RESOLUTION",
        candidate_count=2,
        null_certified=False,
    )
    assert unresolved["PUBLICATION_GATE"] == "BLOCKED_PENDING_CANDIDATE_RESOLUTION"
    assert unresolved["INTERPRETATION_AUTHORIZATION"] == "PROHIBITED"

    with pytest.raises(RuntimeError):
        gate.decide_publication_gate(
            search_status="COMPLETE_BOUNDED_NULL_RESULT",
            candidate_count=1,
            null_certified=True,
        )
