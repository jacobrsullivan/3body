"""Weighted value-quotient near-null search for WP3 v2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence, TypeAlias

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.linalg import null_space


FloatArray: TypeAlias = NDArray[np.float64]


def _matrix(value: ArrayLike, name: str) -> FloatArray:
    array = np.asarray(value, dtype=np.float64)
    if array.ndim != 2 or not array.size or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be a nonempty finite matrix")
    return array


def _weighted_std(values: FloatArray, weights: FloatArray) -> float:
    mean = float(np.sum(weights * values))
    return float(np.sqrt(np.sum(weights * np.square(values - mean))))


def balanced_row_weights(
    group_ids: Sequence[str],
    family_ids: Sequence[str],
) -> FloatArray:
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
    coefficients: tuple[FloatArray, ...]
    singular_values: FloatArray
    value_rank: int
    value_nullity: int
    known_control_rank: int
    known_control_metrics: dict[str, dict[str, float]]


def _fit(
    values: FloatArray,
    derivatives: FloatArray,
    weights: FloatArray,
    controls: Mapping[str, ArrayLike],
    *,
    value_rank_relative_tolerance: float,
    mode_count: int,
) -> _Fit:
    weighted_mean = np.sum(weights[:, None] * values, axis=0)
    value_operator = np.sqrt(weights)[:, None] * (values - weighted_mean)
    derivative_operator = np.sqrt(weights)[:, None] * derivatives
    _, value_singular, value_right = np.linalg.svd(
        value_operator, full_matrices=False
    )
    if value_singular.size == 0 or value_singular[0] == 0.0:
        raise ValueError("feature value operator has no nonconstant direction")
    value_rank = int(
        np.count_nonzero(
            value_singular
            > value_singular[0] * float(value_rank_relative_tolerance)
        )
    )
    active_singular = value_singular[:value_rank]
    active_right = value_right[:value_rank]
    coefficient_map = active_right.T / active_singular

    control_coordinates = []
    control_metrics: dict[str, dict[str, float]] = {}
    for name, value in controls.items():
        coefficients = np.asarray(value, dtype=np.float64)
        if coefficients.shape != (values.shape[1],):
            raise ValueError(f"known control {name} has the wrong length")
        control_coordinates.append(active_singular * (active_right @ coefficients))
        projected_values = values @ coefficients
        projected_derivatives = derivatives @ coefficients
        control_metrics[name] = {
            "weighted_value_std": _weighted_std(projected_values, weights),
            "weighted_lie_rms": float(
                np.sqrt(np.sum(weights * np.square(projected_derivatives)))
            ),
            "lie_max_abs": float(np.max(np.abs(projected_derivatives))),
        }
    if control_coordinates:
        control_matrix = np.column_stack(control_coordinates)
        control_left, control_singular, _ = np.linalg.svd(
            control_matrix, full_matrices=False
        )
        if control_singular.size and control_singular[0] > 0.0:
            control_rank = int(
                np.count_nonzero(control_singular > control_singular[0] * 1e-11)
            )
        else:
            control_rank = 0
        control_basis = control_left[:, :control_rank]
        complement = null_space(control_basis.T, rcond=1e-12)
    else:
        control_rank = 0
        complement = np.eye(value_rank)
    if complement.shape[1] == 0:
        raise ValueError("known algebra spans the active value space")

    search_operator = derivative_operator @ coefficient_map @ complement
    _, singular_values, right_vectors = np.linalg.svd(
        search_operator, full_matrices=False
    )
    order = np.argsort(singular_values)[: min(mode_count, singular_values.size)]
    coefficients = []
    for index in order:
        vector = coefficient_map @ complement @ right_vectors[index]
        dominant = int(np.argmax(np.abs(vector)))
        if vector[dominant] < 0.0:
            vector = -vector
        coefficients.append(vector)
    return _Fit(
        coefficients=tuple(coefficients),
        singular_values=np.sort(singular_values),
        value_rank=value_rank,
        value_nullity=values.shape[1] - value_rank,
        known_control_rank=control_rank,
        known_control_metrics=control_metrics,
    )


def _coefficient_cosine(first: FloatArray, second: FloatArray) -> float:
    denominator = float(np.linalg.norm(first) * np.linalg.norm(second))
    if denominator == 0.0:
        return 0.0
    return abs(float(np.dot(first, second))) / denominator


def _group_drift(
    projected: FloatArray,
    group_ids: Sequence[str],
) -> tuple[list[dict[str, float | str]], float]:
    groups = np.asarray(group_ids, dtype=object)
    rows = []
    for group in sorted({str(value) for value in groups}):
        group_values = projected[groups == group]
        if group_values.size < 2:
            continue
        rows.append(
            {
                "group_id": group,
                "scaled_peak_to_peak": float(np.ptp(group_values)),
            }
        )
    return rows, max(
        (float(row["scaled_peak_to_peak"]) for row in rows), default=0.0
    )


def search_near_null_modes(
    training_values: ArrayLike,
    training_derivatives: ArrayLike,
    calibration_values: ArrayLike,
    calibration_derivatives: ArrayLike,
    *,
    feature_names: Sequence[str],
    known_controls: Mapping[str, ArrayLike],
    training_group_ids: Sequence[str],
    training_family_ids: Sequence[str],
    calibration_group_ids: Sequence[str],
    calibration_family_ids: Sequence[str],
    mode_count: int,
    value_rank_relative_tolerance: float,
    candidate_lie_rms_max: float,
    calibration_to_training_max: float,
    family_fold_cosine_min: float,
    trajectory_drift_max: float,
) -> dict[str, object]:
    """Rank value-normalized modes after identities and known algebra are removed."""

    train_values = _matrix(training_values, "training_values")
    train_derivatives = _matrix(training_derivatives, "training_derivatives")
    calibration_values_array = _matrix(calibration_values, "calibration_values")
    calibration_derivatives_array = _matrix(
        calibration_derivatives, "calibration_derivatives"
    )
    feature_count = len(feature_names)
    expected_train = (train_values.shape[0], feature_count)
    expected_calibration = (calibration_values_array.shape[0], feature_count)
    if train_derivatives.shape != expected_train:
        raise ValueError("training feature and derivative matrices differ")
    if calibration_derivatives_array.shape != expected_calibration:
        raise ValueError("calibration feature and derivative matrices differ")
    training_weights = balanced_row_weights(
        training_group_ids, training_family_ids
    )
    calibration_weights = balanced_row_weights(
        calibration_group_ids, calibration_family_ids
    )
    fit = _fit(
        train_values,
        train_derivatives,
        training_weights,
        known_controls,
        value_rank_relative_tolerance=value_rank_relative_tolerance,
        mode_count=mode_count,
    )

    fold_modes: dict[str, tuple[FloatArray, ...]] = {}
    training_families = np.asarray(training_family_ids, dtype=object)
    training_groups = np.asarray(training_group_ids, dtype=object)
    for held_out in sorted({str(value) for value in training_families}):
        mask = training_families != held_out
        if np.count_nonzero(mask) < 2:
            continue
        fold_weights = balanced_row_weights(
            training_groups[mask].tolist(), training_families[mask].tolist()
        )
        fold = _fit(
            train_values[mask],
            train_derivatives[mask],
            fold_weights,
            known_controls,
            value_rank_relative_tolerance=value_rank_relative_tolerance,
            mode_count=max(mode_count * 3, 8),
        )
        fold_modes[held_out] = fold.coefficients

    calibration_families = np.asarray(calibration_family_ids, dtype=object)
    modes = []
    candidates = []
    for rank, coefficients in enumerate(fit.coefficients, start=1):
        training_projected = train_values @ coefficients
        calibration_projected = calibration_values_array @ coefficients
        training_lie = train_derivatives @ coefficients
        calibration_lie = calibration_derivatives_array @ coefficients
        training_lie_rms = float(
            np.sqrt(np.sum(training_weights * np.square(training_lie)))
        )
        calibration_lie_rms = float(
            np.sqrt(np.sum(calibration_weights * np.square(calibration_lie)))
        )
        ratio = calibration_lie_rms / max(
            training_lie_rms, np.finfo(float).tiny
        )
        fold_cosines = {
            family: max(
                (_coefficient_cosine(coefficients, mode) for mode in family_modes),
                default=0.0,
            )
            for family, family_modes in fold_modes.items()
        }
        drift_rows, drift_max = _group_drift(
            calibration_projected, calibration_group_ids
        )
        family_residuals = {}
        for family in sorted({str(value) for value in calibration_families}):
            mask = calibration_families == family
            family_weights = np.ones(np.count_nonzero(mask)) / np.count_nonzero(mask)
            family_residuals[family] = float(
                np.sqrt(np.sum(family_weights * np.square(calibration_lie[mask])))
            )
        ordered_terms = np.argsort(np.abs(coefficients))[::-1][:15]
        passed = bool(
            training_lie_rms <= candidate_lie_rms_max
            and calibration_lie_rms <= candidate_lie_rms_max
            and ratio <= calibration_to_training_max
            and min(fold_cosines.values(), default=0.0) >= family_fold_cosine_min
            and drift_max <= trajectory_drift_max
        )
        payload = {
            "rank": rank,
            "candidate_ready": passed,
            "training_lie_rms": training_lie_rms,
            "calibration_lie_rms": calibration_lie_rms,
            "calibration_to_training_ratio": ratio,
            "training_weighted_value_std": _weighted_std(
                training_projected, training_weights
            ),
            "calibration_weighted_value_std": _weighted_std(
                calibration_projected, calibration_weights
            ),
            "family_fold_coefficient_cosines": fold_cosines,
            "calibration_family_lie_rms": family_residuals,
            "calibration_trajectory_drift": drift_rows,
            "calibration_trajectory_drift_max": drift_max,
            "coefficients": coefficients.tolist(),
            "top_terms": [
                {
                    "feature": str(feature_names[int(index)]),
                    "coefficient": float(coefficients[index]),
                }
                for index in ordered_terms
            ],
        }
        modes.append(payload)
        if passed:
            candidates.append(rank)
    return {
        "feature_count": feature_count,
        "training_row_count": train_values.shape[0],
        "calibration_row_count": calibration_values_array.shape[0],
        "value_rank": fit.value_rank,
        "value_identity_nullity": fit.value_nullity,
        "known_algebra_declared_count": len(known_controls),
        "known_algebra_active_rank": fit.known_control_rank,
        "known_control_metrics": fit.known_control_metrics,
        "post_projection_singular_values": fit.singular_values.tolist(),
        "numerical_nullity_at_candidate_threshold": int(
            np.count_nonzero(fit.singular_values <= candidate_lie_rms_max)
        ),
        "candidate_mode_ranks": candidates,
        "candidate_count": len(candidates),
        "modes": modes,
    }
