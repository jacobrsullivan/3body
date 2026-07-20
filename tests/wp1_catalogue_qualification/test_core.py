from __future__ import annotations

from copy import deepcopy
import inspect
from pathlib import Path

import numpy as np

from src.python.wp1_catalogue_v1.core import (
    deduplicate_catalogue,
    generate_native_catalogue,
    match_external_rows,
    planar_linear_seed,
)
from src.python.wp1_catalogue_v1.qualification import load_json


ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "validation-external/wp1-catalogue-validation/qualification_spec.json"


def test_native_generator_has_no_external_corpus_parameter():
    parameters = inspect.signature(generate_native_catalogue).parameters
    assert set(parameters) == {"spec", "with_stability"}


def test_linear_seed_uses_inner_positive_vy_canonical_section():
    for lpoint in ("L1", "L2"):
        state, period = planar_linear_seed(0.012150585609624, lpoint, 0.001)
        assert state.shape == (6,)
        assert state[4] > 0.0
        assert np.count_nonzero(state[[1, 2, 3, 5]]) == 0
        assert period > 2.0


def test_small_native_continuation_closes_without_external_seed():
    spec = deepcopy(load_json(SPEC_PATH))
    for lpoint in ("L1", "L2"):
        spec["generation"]["branches"][lpoint].update(
            amplitude_min=0.001,
            amplitude_max=0.002,
            amplitude_step=0.001,
        )
    run = generate_native_catalogue(spec, with_stability=False)
    assert len(run.rows) == 4
    assert not run.rejected_duplicates
    assert max(row["closure_error"] for row in run.rows) < 1e-8
    assert all(row["seed_source"] == "analytic-collinear-center-mode" for row in run.rows)
    assert run.provenance["external_data_used_by_generation"] is False


def test_phase_invariant_deduplication_rejects_same_c_period():
    base = {"catalogue_id": "a", "lpoint": "L1", "amplitude": 0.01, "jacobi": 3.1, "period": 3.0}
    duplicate = {**base, "catalogue_id": "b", "amplitude": 0.02, "jacobi": 3.1 + 1e-13}
    distinct = {**base, "catalogue_id": "c", "amplitude": 0.03, "jacobi": 3.0}
    accepted, rejected = deduplicate_catalogue([duplicate, distinct, base])
    assert [row["catalogue_id"] for row in accepted] == ["a", "c"]
    assert rejected[0]["duplicate_of"] == "a"


def test_external_match_is_selected_by_lpoint_and_x_not_stability():
    spec = load_json(SPEC_PATH)
    candidates = [
        {
            "catalogue_id": "near-x-wrong-index",
            "lpoint": "L1",
            "x": 0.8,
            "y": 0.0,
            "z": 0.0,
            "vx": 0.0,
            "vy": 0.2,
            "vz": 0.0,
            "period": 3.0,
            "jacobi": 3.1,
            "stability_index": 101.0,
            "stability_label": "strongly_unstable",
        },
        {
            "catalogue_id": "far-x-perfect-index",
            "lpoint": "L1",
            "x": 0.7,
            "y": 0.0,
            "z": 0.0,
            "vx": 0.0,
            "vy": 0.2,
            "vz": 0.0,
            "period": 3.0,
            "jacobi": 3.1,
            "stability_index": 100.0,
            "stability_label": "strongly_unstable",
        },
    ]
    external = [
        {
            "catalog_id": "jpl-1",
            "split": "development",
            "family": "lyapunov",
            "lpoint": "L1",
            "x": 0.8001,
            "y": 0.0,
            "z": 0.0,
            "vx": 0.0,
            "vy": 0.2,
            "vz": 0.0,
            "period": 3.0,
            "jacobi": 3.1,
            "stability": 100.0,
        }
    ]
    match = match_external_rows(external, candidates, spec)[0]
    assert match["native_catalogue_id"] == "near-x-wrong-index"
    assert match["match_key"].startswith("nearest same-lpoint x")
