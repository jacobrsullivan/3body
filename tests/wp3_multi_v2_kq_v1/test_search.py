from __future__ import annotations

import numpy as np

from src.python.wp3_exploration_v4 import fit_known_quotient_spectrum


def _fit(driver: str, *, invariant_second: bool = False):
    x = np.asarray([-2.0, -1.0, -0.5, 0.25, 1.0, 1.5, 2.0, 3.0])
    y = np.asarray([1.0, -1.0, 2.0, -2.0, 0.5, -0.25, 1.5, -1.5])
    values = np.column_stack((x, 2.0 * x, y, 3.0 * y))
    derivative = np.zeros_like(y) if invariant_second else np.linspace(1.0, 2.0, y.size)
    derivatives = np.column_stack(
        (np.zeros_like(x), np.zeros_like(x), derivative, 3.0 * derivative)
    )
    weights = np.full(x.size, 1.0 / x.size)
    return fit_known_quotient_spectrum(
        values,
        derivatives,
        weights,
        np.asarray([1.0, 0.0, 0.0, 0.0]),
        driver=driver,
        value_rank_relative_tolerance=1e-11,
        nuisance_derivative_rank_relative_tolerance=1e-12,
        singular_cluster_relative_tolerance=1e-8,
        singular_cluster_absolute_tolerance=1e-12,
        svd_backward_error_factor=16.0,
    )


def test_duplicate_known_representations_are_removed_in_function_space() -> None:
    fit = _fit("numpy")
    assert fit.value_rank == 2
    assert fit.value_nuisance_nullity == 2
    assert fit.generalized_singular_values.shape == (1,)
    assert fit.generalized_singular_values[0] > 0.1
    assert fit.mode_known_response_projection_max < 1e-12
    assert abs(np.dot(fit.normalized_coefficients[0], [1.0, 0.0, 0.0, 0.0])) > 0


def test_new_invariant_remains_a_zero_mode_after_known_quotient() -> None:
    fit = _fit("numpy", invariant_second=True)
    assert fit.generalized_singular_values[0] < 1e-12
    assert fit.reconstructed_lie_rms[0] < 1e-12


def test_three_svd_backends_agree_away_from_roundoff() -> None:
    singular = [_fit(driver).generalized_singular_values[0] for driver in ("numpy", "gesdd", "gesvd")]
    assert np.ptp(singular) / max(singular) < 1e-12


def test_known_response_can_use_an_alternate_coefficient_representative() -> None:
    x = np.asarray([-2.0, -1.0, 0.5, 1.0, 2.0, 3.0])
    y = np.asarray([1.0, 0.0, -1.0, 2.0, -2.0, 0.5])
    values = np.column_stack((x, 2.0 * x, y))
    derivatives = np.column_stack(
        (np.zeros_like(x), np.zeros_like(x), np.ones_like(x))
    )
    weights = np.full(x.size, 1.0 / x.size)
    first = fit_known_quotient_spectrum(
        values,
        derivatives,
        weights,
        np.asarray([1.0, 0.0, 0.0]),
        driver="numpy",
        value_rank_relative_tolerance=1e-11,
        nuisance_derivative_rank_relative_tolerance=1e-12,
        singular_cluster_relative_tolerance=1e-8,
        singular_cluster_absolute_tolerance=1e-12,
        svd_backward_error_factor=16.0,
    )
    second = fit_known_quotient_spectrum(
        values,
        derivatives,
        weights,
        np.asarray([0.0, 0.5, 0.0]),
        driver="numpy",
        value_rank_relative_tolerance=1e-11,
        nuisance_derivative_rank_relative_tolerance=1e-12,
        singular_cluster_relative_tolerance=1e-8,
        singular_cluster_absolute_tolerance=1e-12,
        svd_backward_error_factor=16.0,
    )
    assert np.allclose(
        first.generalized_singular_values,
        second.generalized_singular_values,
        rtol=1e-12,
        atol=1e-12,
    )
