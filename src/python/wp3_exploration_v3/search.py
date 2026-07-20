"""Generalized Lie/value search after an exact coefficient-space quotient."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence, TypeAlias

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.linalg import null_space


FloatArray: TypeAlias = NDArray[np.float64]


def _matrix_vector(matrix: FloatArray, vector: FloatArray) -> FloatArray:
    return np.einsum("ij,j->i", matrix, vector, optimize=False)


def _matrix_matrix(first: FloatArray, second: FloatArray) -> FloatArray:
    return np.einsum("ij,jk->ik", first, second, optimize=False)


def _matrix(value: ArrayLike, name: str) -> FloatArray:
    array = np.asarray(value, dtype=np.float64)
    if array.ndim != 2 or not array.size or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be a nonempty finite matrix")
    return array


def _weighted_std(values: FloatArray, weights: FloatArray) -> float:
    mean = float(np.sum(weights * values))
    return float(np.sqrt(np.sum(weights * np.square(values - mean))))


def _weighted_rms(values: FloatArray, weights: FloatArray) -> float:
    return float(np.sqrt(np.sum(weights * np.square(values))))


def balanced_row_weights(group_ids: Sequence[str], family_ids: Sequence[str]) -> FloatArray:
    """Give every family and every group within a family equal total weight."""

    groups = np.asarray(group_ids, dtype=object)
    families = np.asarray(family_ids, dtype=object)
    if groups.ndim != 1 or families.shape != groups.shape or groups.size == 0:
        raise ValueError("group and family IDs must be equal nonempty vectors")
    weights = np.zeros(groups.size, dtype=np.float64)
    unique_families = sorted({str(value) for value in families})
    for family in unique_families:
        family_mask = families == family
        family_groups = sorted({str(value) for value in groups[family_mask]})
        for group in family_groups:
            group_mask = family_mask & (groups == group)
            weights[group_mask] = (
                1.0
                / len(unique_families)
                / len(family_groups)
                / int(np.count_nonzero(group_mask))
            )
    if not np.isclose(np.sum(weights), 1.0, atol=2e-15):
        raise ArithmeticError("balanced weights do not sum to one")
    return weights


@dataclass(frozen=True)
class _Fit:
    raw_coefficients: tuple[FloatArray, ...]
    normalized_coefficients: tuple[FloatArray, ...]
    generalized_singular_values: FloatArray
    reconstructed_training_lie_rms: FloatArray
    feature_scales: FloatArray
    value_rank: int
    value_nullity: int
    value_null_derivative_rank: int
    known_module_rank: int
    known_projection_residual: float


def _svd_rank(values: FloatArray, relative_tolerance: float) -> int:
    if values.size == 0 or values[0] == 0.0:
        return 0
    return int(np.count_nonzero(values > values[0] * relative_tolerance))


def _fit(
    values: FloatArray,
    derivatives: FloatArray,
    weights: FloatArray,
    known_module: Mapping[str, ArrayLike],
    *,
    value_rank_relative_tolerance: float,
    return_mode_count: int | None,
    feature_scales: FloatArray | None = None,
) -> _Fit:
    feature_count = values.shape[1]
    if derivatives.shape != values.shape:
        raise ValueError("feature and derivative matrices differ")
    if feature_scales is None:
        feature_scales = np.sqrt(np.sum(weights[:, None] * np.square(values), axis=0))
    feature_scales = np.asarray(feature_scales, dtype=np.float64)
    if feature_scales.shape != (feature_count,) or np.any(feature_scales <= 1e-14):
        raise ValueError("feature library contains an unobservable column")

    known_raw = []
    for name, value in known_module.items():
        coefficients = np.asarray(value, dtype=np.float64)
        if coefficients.shape != (feature_count,):
            raise ValueError(f"known module member {name} has the wrong length")
        known_raw.append(feature_scales * coefficients)
    known_matrix = np.column_stack(known_raw)
    known_left, known_singular, _ = np.linalg.svd(known_matrix, full_matrices=False)
    known_rank = _svd_rank(known_singular, 1e-12)
    known_basis = known_left[:, :known_rank]
    complement = null_space(known_basis.T, rcond=1e-12)
    if complement.shape[1] == 0:
        raise ValueError("known module spans the feature library")
    known_projection_residual = float(np.max(np.abs(_matrix_matrix(known_matrix.T, complement))))

    normalized_values = values / feature_scales
    normalized_derivatives = derivatives / feature_scales
    mean = np.sum(weights[:, None] * normalized_values, axis=0)
    value_operator = np.sqrt(weights)[:, None] * _matrix_matrix(
        normalized_values - mean, complement
    )
    derivative_operator = np.sqrt(weights)[:, None] * _matrix_matrix(
        normalized_derivatives, complement
    )

    _, value_singular, value_right = np.linalg.svd(value_operator, full_matrices=True)
    value_rank = _svd_rank(value_singular, value_rank_relative_tolerance)
    if value_rank == 0:
        raise ValueError("quotient library has no observable value direction")
    active = value_right[:value_rank].T
    nuisance = value_right[value_rank:].T
    active_derivative = _matrix_matrix(derivative_operator, active)
    nuisance_derivative = _matrix_matrix(derivative_operator, nuisance)

    if nuisance_derivative.shape[1]:
        nuisance_left, nuisance_singular, nuisance_right = np.linalg.svd(
            nuisance_derivative, full_matrices=False
        )
        nuisance_rank = _svd_rank(nuisance_singular, 1e-12)
        nuisance_left_active = nuisance_left[:, :nuisance_rank]
        residual_derivative = active_derivative - _matrix_matrix(
            nuisance_left_active,
            _matrix_matrix(nuisance_left_active.T, active_derivative),
        )
    else:
        nuisance_left = np.empty((values.shape[0], 0))
        nuisance_singular = np.empty(0)
        nuisance_right = np.empty((0, 0))
        nuisance_rank = 0
        residual_derivative = active_derivative

    generalized_operator = residual_derivative / value_singular[:value_rank]
    _, generalized_singular, generalized_right = np.linalg.svd(
        generalized_operator, full_matrices=False
    )
    order = np.argsort(generalized_singular)
    raw_coefficients: list[FloatArray] = []
    normalized_coefficients: list[FloatArray] = []
    reconstructed_lie_rms: list[float] = []
    selected_generalized: list[float] = []
    for index in order:
        observable_coordinates = generalized_right[index] / value_singular[:value_rank]
        nuisance_coordinates = np.zeros(nuisance.shape[1], dtype=np.float64)
        if nuisance_rank:
            target = _matrix_vector(active_derivative, observable_coordinates)
            nuisance_coordinates = -_matrix_vector(
                nuisance_right[:nuisance_rank].T,
                _matrix_vector(nuisance_left[:, :nuisance_rank].T, target)
                / nuisance_singular[:nuisance_rank],
            )
        quotient_coordinates = (
            _matrix_vector(active, observable_coordinates)
            + _matrix_vector(nuisance, nuisance_coordinates)
        )
        normalized = _matrix_vector(complement, quotient_coordinates)
        raw = normalized / feature_scales
        value_std = _weighted_std(_matrix_vector(values, raw), weights)
        if value_std <= 1e-14:
            raise ArithmeticError("generalized mode has no observable value variation")
        raw = raw / value_std
        normalized = feature_scales * raw
        dominant = int(np.argmax(np.abs(normalized)))
        if normalized[dominant] < 0.0:
            raw = -raw
            normalized = -normalized
        raw_coefficients.append(raw)
        normalized_coefficients.append(normalized)
        reconstructed_lie_rms.append(
            _weighted_rms(_matrix_vector(derivatives, raw), weights)
        )
        selected_generalized.append(float(generalized_singular[index]))
    reconstructed_order = np.argsort(reconstructed_lie_rms)
    if return_mode_count is not None:
        reconstructed_order = reconstructed_order[:return_mode_count]
    return _Fit(
        raw_coefficients=tuple(raw_coefficients[index] for index in reconstructed_order),
        normalized_coefficients=tuple(normalized_coefficients[index] for index in reconstructed_order),
        generalized_singular_values=np.asarray(
            [selected_generalized[index] for index in reconstructed_order], dtype=np.float64
        ),
        reconstructed_training_lie_rms=np.asarray(
            [reconstructed_lie_rms[index] for index in reconstructed_order], dtype=np.float64
        ),
        feature_scales=feature_scales,
        value_rank=value_rank,
        value_nullity=complement.shape[1] - value_rank,
        value_null_derivative_rank=nuisance_rank,
        known_module_rank=known_rank,
        known_projection_residual=known_projection_residual,
    )


def _subspace_basis(modes: tuple[FloatArray, ...]) -> FloatArray:
    if not modes:
        return np.empty((0, 0), dtype=np.float64)
    matrix = np.column_stack(modes)
    basis, singular, _ = np.linalg.svd(matrix, full_matrices=False)
    rank = _svd_rank(singular, 1e-11)
    return basis[:, :rank]


def _subspace_projection(vector: FloatArray, basis: FloatArray) -> float:
    denominator = float(np.linalg.norm(vector))
    if basis.shape[1] == 0 or denominator == 0.0:
        return 0.0
    return float(np.linalg.norm(basis.T @ (vector / denominator)))


def _group_drift(
    projected: FloatArray,
    group_ids: Sequence[str],
    point_ids: Sequence[str],
) -> tuple[list[dict[str, float | str]], float]:
    groups = np.asarray(group_ids, dtype=object)
    points = np.asarray(point_ids, dtype=object)
    rows: list[dict[str, float | str]] = []
    for group in sorted({str(value) for value in groups}):
        group_mask = groups == group
        point_values = [
            float(np.mean(projected[group_mask & (points == point)]))
            for point in sorted({str(value) for value in points[group_mask]})
        ]
        if len(point_values) < 2:
            continue
        rows.append({"group_id": group, "scaled_peak_to_peak": float(np.ptp(point_values))})
    return rows, max((float(row["scaled_peak_to_peak"]) for row in rows), default=0.0)


def _gauge_spread(projected: FloatArray, point_ids: Sequence[str]) -> float:
    points = np.asarray(point_ids, dtype=object)
    return max(
        (
            float(np.ptp(projected[points == point]))
            for point in sorted({str(value) for value in points})
        ),
        default=0.0,
    )


def search_quotient_modes(
    training_values: ArrayLike,
    training_derivatives: ArrayLike,
    training_gauge_derivatives: ArrayLike,
    calibration_values: ArrayLike,
    calibration_derivatives: ArrayLike,
    calibration_gauge_derivatives: ArrayLike,
    *,
    feature_names: Sequence[str],
    known_module: Mapping[str, ArrayLike],
    training_group_ids: Sequence[str],
    training_family_ids: Sequence[str],
    training_point_ids: Sequence[str],
    calibration_group_ids: Sequence[str],
    calibration_family_ids: Sequence[str],
    calibration_point_ids: Sequence[str],
    mode_count: int,
    fold_mode_count: int,
    value_rank_relative_tolerance: float,
    candidate_lie_rms_max: float,
    candidate_gauge_lie_rms_max: float,
    calibration_ratio_floor: float,
    calibration_to_training_max: float,
    family_fold_subspace_projection_min: float,
    calibration_trajectory_drift_max: float,
    gauge_orbit_spread_max: float,
) -> dict[str, object]:
    """Search the complete observable quotient after exact known-module removal."""

    train_values = _matrix(training_values, "training_values")
    train_derivatives = _matrix(training_derivatives, "training_derivatives")
    train_gauge = _matrix(training_gauge_derivatives, "training_gauge_derivatives")
    calibration_values_array = _matrix(calibration_values, "calibration_values")
    calibration_derivatives_array = _matrix(calibration_derivatives, "calibration_derivatives")
    calibration_gauge = _matrix(calibration_gauge_derivatives, "calibration_gauge_derivatives")
    feature_count = len(feature_names)
    if any(
        matrix.shape[1] != feature_count
        for matrix in (
            train_values, train_derivatives, train_gauge,
            calibration_values_array, calibration_derivatives_array, calibration_gauge,
        )
    ):
        raise ValueError("feature matrix width does not match names")
    if train_derivatives.shape != train_values.shape or train_gauge.shape != train_values.shape:
        raise ValueError("training matrices differ")
    if calibration_derivatives_array.shape != calibration_values_array.shape or calibration_gauge.shape != calibration_values_array.shape:
        raise ValueError("calibration matrices differ")

    training_weights = balanced_row_weights(training_group_ids, training_family_ids)
    calibration_weights = balanced_row_weights(calibration_group_ids, calibration_family_ids)
    fit = _fit(
        train_values,
        train_derivatives,
        training_weights,
        known_module,
        value_rank_relative_tolerance=value_rank_relative_tolerance,
        return_mode_count=None,
    )

    training_families = np.asarray(training_family_ids, dtype=object)
    training_groups = np.asarray(training_group_ids, dtype=object)
    fold_bases: dict[str, FloatArray] = {}
    fold_summaries: dict[str, dict[str, int]] = {}
    for held_out in sorted({str(value) for value in training_families}):
        mask = training_families != held_out
        fold_weights = balanced_row_weights(
            training_groups[mask].tolist(), training_families[mask].tolist()
        )
        fold = _fit(
            train_values[mask],
            train_derivatives[mask],
            fold_weights,
            known_module,
            value_rank_relative_tolerance=value_rank_relative_tolerance,
            return_mode_count=fold_mode_count,
            feature_scales=fit.feature_scales,
        )
        fold_bases[held_out] = _subspace_basis(fold.normalized_coefficients)
        fold_summaries[held_out] = {
            "row_count": int(np.count_nonzero(mask)),
            "observable_value_rank": fold.value_rank,
            "value_nuisance_nullity": fold.value_nullity,
            "value_nuisance_derivative_rank": fold.value_null_derivative_rank,
            "retained_subspace_mode_count": len(fold.normalized_coefficients),
        }

    known_metrics: dict[str, dict[str, float]] = {}
    for name, value in known_module.items():
        coefficients = np.asarray(value, dtype=np.float64)
        coefficient_scale = max(float(np.linalg.norm(fit.feature_scales * coefficients)), np.finfo(float).tiny)
        known_metrics[name] = {
            "training_value_abs_max": float(np.max(np.abs(_matrix_vector(train_values, coefficients)))),
            "calibration_value_abs_max": float(np.max(np.abs(_matrix_vector(calibration_values_array, coefficients)))),
            "training_lie_rms_per_coefficient_scale": _weighted_rms(
                _matrix_vector(train_derivatives, coefficients), training_weights
            ) / coefficient_scale,
            "calibration_lie_rms_per_coefficient_scale": _weighted_rms(
                _matrix_vector(calibration_derivatives_array, coefficients), calibration_weights
            ) / coefficient_scale,
            "training_gauge_lie_rms_per_coefficient_scale": _weighted_rms(
                _matrix_vector(train_gauge, coefficients), training_weights
            ) / coefficient_scale,
            "calibration_gauge_lie_rms_per_coefficient_scale": _weighted_rms(
                _matrix_vector(calibration_gauge, coefficients), calibration_weights
            ) / coefficient_scale,
        }

    calibration_families = np.asarray(calibration_family_ids, dtype=object)
    modes: list[dict[str, object]] = []
    candidates: list[int] = []
    for rank, (coefficients, normalized_coefficients) in enumerate(
        zip(fit.raw_coefficients, fit.normalized_coefficients, strict=True), start=1
    ):
        training_projected = _matrix_vector(train_values, coefficients)
        calibration_projected = _matrix_vector(calibration_values_array, coefficients)
        training_lie = _matrix_vector(train_derivatives, coefficients)
        calibration_lie = _matrix_vector(calibration_derivatives_array, coefficients)
        training_gauge_lie = _matrix_vector(train_gauge, coefficients)
        calibration_gauge_lie = _matrix_vector(calibration_gauge, coefficients)
        training_lie_rms = _weighted_rms(training_lie, training_weights)
        calibration_lie_rms = _weighted_rms(calibration_lie, calibration_weights)
        training_gauge_rms = _weighted_rms(training_gauge_lie, training_weights)
        calibration_gauge_rms = _weighted_rms(calibration_gauge_lie, calibration_weights)
        ratio = calibration_lie_rms / max(training_lie_rms, calibration_ratio_floor)
        fold_projections = {
            family: _subspace_projection(normalized_coefficients, basis)
            for family, basis in fold_bases.items()
        }
        drift_rows, drift_max = _group_drift(
            calibration_projected, calibration_group_ids, calibration_point_ids
        )
        training_gauge_spread = _gauge_spread(training_projected, training_point_ids)
        calibration_gauge_spread = _gauge_spread(calibration_projected, calibration_point_ids)
        family_residuals = {}
        for family in sorted({str(value) for value in calibration_families}):
            mask = calibration_families == family
            family_weights = np.ones(np.count_nonzero(mask)) / np.count_nonzero(mask)
            family_residuals[family] = _weighted_rms(calibration_lie[mask], family_weights)
        ordered_terms = np.argsort(np.abs(fit.feature_scales * coefficients))[::-1][:15]
        passed = bool(
            training_lie_rms <= candidate_lie_rms_max
            and calibration_lie_rms <= candidate_lie_rms_max
            and training_gauge_rms <= candidate_gauge_lie_rms_max
            and calibration_gauge_rms <= candidate_gauge_lie_rms_max
            and ratio <= calibration_to_training_max
            and min(fold_projections.values(), default=0.0) >= family_fold_subspace_projection_min
            and drift_max <= calibration_trajectory_drift_max
            and training_gauge_spread <= gauge_orbit_spread_max
            and calibration_gauge_spread <= gauge_orbit_spread_max
        )
        payload: dict[str, object] = {
            "rank": rank,
            "candidate_ready": passed,
            "training_lie_rms": training_lie_rms,
            "calibration_lie_rms": calibration_lie_rms,
            "training_gauge_lie_rms": training_gauge_rms,
            "calibration_gauge_lie_rms": calibration_gauge_rms,
            "calibration_to_training_ratio": ratio,
            "training_weighted_value_std": _weighted_std(training_projected, training_weights),
            "calibration_weighted_value_std": _weighted_std(calibration_projected, calibration_weights),
            "family_fold_subspace_projections": fold_projections,
            "calibration_family_lie_rms": family_residuals,
            "calibration_trajectory_drift": drift_rows,
            "calibration_trajectory_drift_max": drift_max,
            "training_gauge_orbit_spread_max": training_gauge_spread,
            "calibration_gauge_orbit_spread_max": calibration_gauge_spread,
        }
        if rank <= mode_count or passed:
            payload["coefficients"] = coefficients.tolist()
            payload["top_terms"] = [
                {"feature": str(feature_names[int(index)]), "coefficient": float(coefficients[index])}
                for index in ordered_terms
            ]
        modes.append(payload)
        if passed:
            candidates.append(rank)
    return {
        "feature_count": feature_count,
        "training_row_count": train_values.shape[0],
        "calibration_row_count": calibration_values_array.shape[0],
        "exact_known_module_declared_count": len(known_module),
        "exact_known_module_rank": fit.known_module_rank,
        "exact_known_module_projection_residual": fit.known_projection_residual,
        "known_module_metrics": known_metrics,
        "observable_value_rank": fit.value_rank,
        "value_nuisance_nullity": fit.value_nullity,
        "value_nuisance_derivative_rank": fit.value_null_derivative_rank,
        "generalized_lie_value_singular_values": fit.generalized_singular_values.tolist(),
        "reconstructed_training_lie_rms": fit.reconstructed_training_lie_rms.tolist(),
        "evaluated_mode_count": len(fit.raw_coefficients),
        "reported_expression_count": sum("coefficients" in mode for mode in modes),
        "family_fold_summaries": fold_summaries,
        "numerical_nullity_at_candidate_threshold": int(
            np.count_nonzero(fit.reconstructed_training_lie_rms <= candidate_lie_rms_max)
        ),
        "candidate_mode_ranks": candidates,
        "candidate_count": len(candidates),
        "modes": modes,
    }
