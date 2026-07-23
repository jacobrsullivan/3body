from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import random

import pytest

from src.python.wp1_residual_map_v1 import (
    ASYMPTOTIC_MANIFOLD,
    HIGHER_VARIATIONAL_EXCEPTION,
    LOCAL_STABLE_NORMAL_FORM,
    build_residual_map,
)


ROOT = Path(__file__).resolve().parents[2]
CATALOGUE = (
    ROOT
    / "validation-external/wp1-catalogue-n3bp-validation/data/native_catalogue.json"
)


def _catalogue() -> dict[str, object]:
    return json.loads(CATALOGUE.read_text(encoding="utf-8"))


def _scientific_projection(payload: dict[str, object]) -> dict[str, object]:
    return payload


def test_locked_catalogue_maps_one_to_one_with_expected_counts() -> None:
    result = build_residual_map(_catalogue())
    assert result["candidate_count"] == 169
    assert result["counts"] == {
        "local_stable_normal_form": 118,
        "asymptotic_manifold": 51,
        "higher_variational_exception_overlay": 1,
        "domain_restricted_or_nonmeromorphic_overlay": 169,
    }
    rows = result["candidates"]
    assert len({row["candidate_id"] for row in rows}) == 169
    assert result["no_invariant_interpretation"] is True
    assert all(str(row["publication_gate"]).startswith("NO_INTERPRETATION:") for row in rows)


def test_track_ranking_is_invariant_under_input_row_permutation() -> None:
    catalogue = _catalogue()
    expected = build_residual_map(catalogue)
    shuffled = deepcopy(catalogue)
    random.Random(20260723).shuffle(shuffled["candidates"])
    observed = build_residual_map(shuffled)
    assert _scientific_projection(observed) == _scientific_projection(expected)


def test_primary_track_follows_only_qualified_planar_label() -> None:
    result = build_residual_map(_catalogue())
    for row in result["candidates"]:
        expected = (
            LOCAL_STABLE_NORMAL_FORM
            if row["qualified_planar_label"] == "S"
            else ASYMPTOTIC_MANIFOLD
        )
        assert row["primary_track"] == expected


def test_exact_exception_overlay_is_equal_mass_only_in_locked_grid() -> None:
    result = build_residual_map(_catalogue())
    selected = [
        row
        for row in result["candidates"]
        if HIGHER_VARIATIONAL_EXCEPTION in row["overlays"]
    ]
    assert len(selected) == 1
    assert selected[0]["sigma"] == "1/3"
    assert selected[0]["masses_exact"] == ["1", "1", "1"]


def test_duplicate_unknown_label_and_changed_mass_are_rejected() -> None:
    catalogue = _catalogue()
    duplicate = deepcopy(catalogue)
    duplicate["candidates"].append(deepcopy(duplicate["candidates"][0]))
    with pytest.raises(ValueError, match="duplicate"):
        build_residual_map(duplicate)

    unknown = deepcopy(catalogue)
    unknown["candidates"][0]["stability"]["label"] = "?"
    with pytest.raises(ValueError, match="unknown"):
        build_residual_map(unknown)

    nonpositive = deepcopy(catalogue)
    nonpositive["candidates"][0]["parameters"]["m1"] = "0"
    with pytest.raises(ValueError, match="positive"):
        build_residual_map(nonpositive)

