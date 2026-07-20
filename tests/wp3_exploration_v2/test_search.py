"""Tests for weighted WP3 v2 search mechanics."""

from __future__ import annotations

import numpy as np

from src.python.wp3_exploration_v2 import (
    balanced_row_weights,
    search_near_null_modes,
)


def test_balanced_weights_equalize_families_and_groups() -> None:
    groups = ["a", "a", "b", "c", "c", "c"]
    families = ["x", "x", "x", "y", "y", "y"]
    weights = balanced_row_weights(groups, families)
    assert np.isclose(np.sum(weights), 1.0)
    assert np.isclose(np.sum(weights[np.array(families) == "x"]), 0.5)
    assert np.isclose(np.sum(weights[np.array(families) == "y"]), 0.5)
    assert np.isclose(np.sum(weights[np.array(groups) == "a"]), 0.25)
    assert np.isclose(np.sum(weights[np.array(groups) == "b"]), 0.25)


def test_search_removes_control_and_recovers_stable_manufactured_mode() -> None:
    rng = np.random.default_rng(39281)
    training_values = rng.normal(size=(90, 5))
    calibration_values = rng.normal(size=(60, 5))
    training_derivatives = rng.normal(size=(90, 5))
    calibration_derivatives = rng.normal(size=(60, 5))
    training_derivatives[:, 0] = 0.0
    calibration_derivatives[:, 0] = 0.0
    training_derivatives[:, 1] = 1e-12 * rng.normal(size=90)
    calibration_derivatives[:, 1] = 1e-12 * rng.normal(size=60)
    training_families = np.array(["a", "b", "c"] * 30)
    calibration_families = np.array(["a", "b", "c"] * 20)
    result = search_near_null_modes(
        training_values,
        training_derivatives,
        calibration_values,
        calibration_derivatives,
        feature_names=[f"f{index}" for index in range(5)],
        known_controls={"constant": np.array([1.0, 0.0, 0.0, 0.0, 0.0])},
        training_group_ids=[f"train-{index}" for index in range(90)],
        training_family_ids=training_families.tolist(),
        calibration_group_ids=[f"cal-{index}" for index in range(60)],
        calibration_family_ids=calibration_families.tolist(),
        mode_count=2,
        value_rank_relative_tolerance=1e-12,
        candidate_lie_rms_max=1e-10,
        calibration_to_training_max=2.0,
        family_fold_cosine_min=0.99,
        trajectory_drift_max=1e-8,
    )
    assert result["candidate_count"] == 1
    candidate = result["modes"][0]
    assert candidate["candidate_ready"] is True
    coefficients = np.asarray(candidate["coefficients"])
    assert abs(coefficients[1]) > 1000.0 * np.max(np.abs(coefficients[2:]))
