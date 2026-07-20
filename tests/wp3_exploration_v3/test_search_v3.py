from __future__ import annotations

import numpy as np
import pytest

from src.python.wp3_exploration_v3 import search_quotient_modes
from src.python.wp3_exploration_v3.search import (
    _fit,
    _subspace_basis,
    _subspace_projection,
)


def test_search_preserves_exact_integral_after_known_module_quotient() -> None:
    rng = np.random.default_rng(42)
    groups = [f"g-{index // 6}" for index in range(72)]
    families = [f"family-{index % 3}" for index in range(72)]
    points = [f"point-{index}" for index in range(72)]
    values = rng.normal(size=(72, 6))
    derivatives = rng.normal(size=(72, 6))
    gauge = rng.normal(size=(72, 6))
    exact = np.array([0.0, 1.0, 2.0, 0.0, 0.0, 0.0])
    known = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    derivatives[:, 1] = -2.0 * derivatives[:, 2]
    gauge[:, 1] = -2.0 * gauge[:, 2]
    calibration_values = rng.normal(size=(72, 6))
    calibration_derivatives = rng.normal(size=(72, 6))
    calibration_gauge = rng.normal(size=(72, 6))
    calibration_derivatives[:, 1] = -2.0 * calibration_derivatives[:, 2]
    calibration_gauge[:, 1] = -2.0 * calibration_gauge[:, 2]
    result = search_quotient_modes(
        values,
        derivatives,
        gauge,
        calibration_values,
        calibration_derivatives,
        calibration_gauge,
        feature_names=tuple(f"f{index}" for index in range(6)),
        known_module={"known": known},
        training_group_ids=groups,
        training_family_ids=families,
        training_point_ids=points,
        calibration_group_ids=groups,
        calibration_family_ids=families,
        calibration_point_ids=points,
        mode_count=3,
        fold_mode_count=3,
        value_rank_relative_tolerance=1e-12,
        candidate_lie_rms_max=1e-10,
        candidate_gauge_lie_rms_max=1e-10,
        calibration_ratio_floor=1e-12,
        calibration_to_training_max=2.0,
        family_fold_subspace_projection_min=0.9,
        calibration_trajectory_drift_max=1e9,
        gauge_orbit_spread_max=1e9,
    )
    assert result["exact_known_module_rank"] == 1
    assert result["numerical_nullity_at_candidate_threshold"] >= 1
    leading = np.asarray(result["modes"][0]["coefficients"])
    cosine = abs(float(leading @ exact)) / (np.linalg.norm(leading) * np.linalg.norm(exact))
    assert cosine > 1.0 - 1e-10
    assert result["modes"][0]["training_lie_rms"] < 1e-12
    assert result["modes"][0]["calibration_lie_rms"] < 1e-12
    assert result["evaluated_mode_count"] == result["observable_value_rank"]


def test_wide_value_operator_uses_complete_right_nullspace() -> None:
    rng = np.random.default_rng(7)
    values = rng.normal(size=(8, 12))
    derivatives = rng.normal(size=(8, 12))
    exact = np.zeros(12)
    exact[1:3] = (1.0, 2.0)
    derivatives[:, 1] = -2.0 * derivatives[:, 2]
    known = np.zeros(12)
    known[0] = 1.0
    weights = np.ones(8) / 8.0
    fit = _fit(
        values,
        derivatives,
        weights,
        {"known": known},
        value_rank_relative_tolerance=1e-12,
        return_mode_count=None,
    )
    assert fit.value_nullity >= 4
    assert fit.value_null_derivative_rank > 1
    assert len(fit.raw_coefficients) == fit.value_rank
    assert np.min(fit.reconstructed_training_lie_rms) < 1e-12


def test_subspace_projection_is_invariant_under_basis_rotation() -> None:
    first = np.array([1.0, 0.0, 0.0, 0.0])
    second = np.array([0.0, 1.0, 0.0, 0.0])
    angle = 0.713
    rotated = (
        np.cos(angle) * first + np.sin(angle) * second,
        -np.sin(angle) * first + np.cos(angle) * second,
    )
    original_basis = _subspace_basis((first, second))
    rotated_basis = _subspace_basis(rotated)
    probe = np.array([0.3, -0.8, 0.4, 0.1])
    assert _subspace_projection(probe, original_basis) == pytest.approx(
        _subspace_projection(probe, rotated_basis), abs=2e-15
    )
