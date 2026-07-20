"""Tests for deterministic known-control projection and near-null ranking."""

from __future__ import annotations

import numpy as np

from src.python.wp3_exploration import search_near_null_modes


def test_search_projects_controls_and_ranks_a_synthetic_cancellation() -> None:
    rng = np.random.default_rng(771)
    row_count = 500
    feature_count = 7
    training_features = rng.normal(size=(row_count, feature_count))
    calibration_features = rng.normal(size=(200, feature_count))

    common_training = rng.normal(size=row_count)
    training_derivatives = rng.normal(size=(row_count, feature_count))
    training_derivatives[:, 0:2] = 0.0
    training_derivatives[:, 2] = common_training
    training_derivatives[:, 3] = common_training + 1.0e-7 * rng.normal(
        size=row_count
    )

    common_calibration = rng.normal(size=200)
    calibration_derivatives = rng.normal(size=(200, feature_count))
    calibration_derivatives[:, 0:2] = 0.0
    calibration_derivatives[:, 2] = common_calibration
    calibration_derivatives[:, 3] = common_calibration + 2.0e-7 * rng.normal(
        size=200
    )

    first_control = np.zeros(feature_count)
    first_control[0] = 1.0
    second_control = np.zeros(feature_count)
    second_control[1] = 1.0
    result = search_near_null_modes(
        training_features,
        training_derivatives,
        calibration_features,
        calibration_derivatives,
        feature_names=tuple(f"f{index}" for index in range(feature_count)),
        control_coefficients={
            "first": first_control,
            "second": second_control,
        },
        mode_count=2,
    )

    assert result.interpretation_status == "EXPLORATORY_ONLY"
    assert result.control_metrics["first"]["training_lie_rms"] == 0.0
    assert result.control_metrics["second"]["calibration_lie_rms"] == 0.0
    leading = result.modes[0]
    assert leading.standardized_singular_value < 2.0e-7
    assert leading.calibration_lie_rms < 1.0e-6
    assert leading.known_control_overlap_max < 1.0e-12
    assert set(np.argsort(np.abs(leading.coefficients))[-2:]) == {2, 3}


def test_search_rejects_dependent_known_controls() -> None:
    rng = np.random.default_rng(17)
    features = rng.normal(size=(20, 4))
    derivatives = rng.normal(size=(20, 4))
    control = np.array([1.0, 0.0, 0.0, 0.0])
    try:
        search_near_null_modes(
            features,
            derivatives,
            features,
            derivatives,
            feature_names=("a", "b", "c", "d"),
            control_coefficients={"one": control, "duplicate": 2.0 * control},
        )
    except ValueError as error:
        assert "linearly dependent" in str(error)
    else:
        raise AssertionError("dependent controls must be rejected")


def test_search_allows_a_dimension_sector_without_known_controls() -> None:
    rng = np.random.default_rng(81)
    features = rng.normal(size=(80, 3))
    common = rng.normal(size=80)
    derivatives = np.column_stack(
        (common, common + 1.0e-6 * rng.normal(size=80), rng.normal(size=80))
    )
    result = search_near_null_modes(
        features,
        derivatives,
        features,
        derivatives,
        feature_names=("a", "b", "c"),
        control_coefficients={},
        mode_count=1,
    )
    assert not result.control_metrics
    assert result.modes[0].known_control_overlap_max == 0.0
    assert result.modes[0].standardized_singular_value < 1.0e-5
