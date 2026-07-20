from __future__ import annotations

import numpy as np
import pytest

from src.python.wp3_exploration_v3 import search_quotient_modes
from src.python.wp3_exploration_v3.search import (
    _cluster_complete_count,
    _fit,
    _singular_clusters,
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
        singular_cluster_relative_tolerance=1e-10,
        singular_cluster_absolute_tolerance=1e-12,
        svd_backward_error_factor=16.0,
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
        singular_cluster_relative_tolerance=1e-10,
        singular_cluster_absolute_tolerance=1e-12,
        svd_backward_error_factor=16.0,
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


def test_fold_boundary_retains_complete_degenerate_cluster() -> None:
    singular = np.array([0.01, 0.2, 0.2 + 2e-13, 0.7])
    clusters = _singular_clusters(
        singular,
        relative_tolerance=1e-10,
        absolute_tolerance=1e-12,
    )
    assert clusters == ((0, 1), (1, 3), (3, 4))
    assert _cluster_complete_count(clusters, 2, singular.size) == 3


def test_degenerate_low_singular_subspace_cannot_produce_false_null() -> None:
    rng = np.random.default_rng(91)
    row_count = 36
    values = rng.normal(size=(row_count, 5))
    derivatives = rng.normal(size=(row_count, 5))
    gauge = np.zeros_like(derivatives)
    derivatives[:, 1] = 0.0
    derivatives[:, 2] = 0.0
    calibration_values = rng.normal(size=(row_count, 5))
    calibration_derivatives = rng.normal(size=(row_count, 5))
    calibration_derivatives[:, 1] = 1.0
    calibration_derivatives[:, 2] = -1.0
    calibration_gauge = np.zeros_like(calibration_derivatives)
    known = np.zeros(5)
    known[0] = 1.0
    groups = [f"group-{index // 3}" for index in range(row_count)]
    families = [f"family-{index % 3}" for index in range(row_count)]
    points = [f"point-{index}" for index in range(row_count)]

    result = search_quotient_modes(
        values,
        derivatives,
        gauge,
        calibration_values,
        calibration_derivatives,
        calibration_gauge,
        feature_names=tuple(f"f{index}" for index in range(5)),
        known_module={"known": known},
        training_group_ids=groups,
        training_family_ids=families,
        training_point_ids=points,
        calibration_group_ids=groups,
        calibration_family_ids=families,
        calibration_point_ids=points,
        mode_count=4,
        fold_mode_count=2,
        value_rank_relative_tolerance=1e-12,
        singular_cluster_relative_tolerance=1e-10,
        singular_cluster_absolute_tolerance=1e-12,
        svd_backward_error_factor=16.0,
        candidate_lie_rms_max=1e-10,
        candidate_gauge_lie_rms_max=1e-10,
        calibration_ratio_floor=1e-12,
        calibration_to_training_max=2.0,
        family_fold_subspace_projection_min=0.9,
        calibration_trajectory_drift_max=1e9,
        gauge_orbit_spread_max=1e9,
    )

    assert result["candidate_count"] >= 1
    assert not result["null_result_spectral_certificate"][
        "certifies_no_training_eligible_direction"
    ]
    assert result["candidate_subspaces"][0]["dimension"] >= 2
