from __future__ import annotations

import numpy as np
import pytest

from src.python.wp1_catalogue_n3bp_v1 import (
    OrbitParameters,
    canonical_jacobi_transform,
    classify_orbit_stability,
    planar_rhs,
    planar_variational_jacobian,
)


def test_analytic_planar_jacobian_matches_centered_finite_differences() -> None:
    state = np.array(
        [
            -0.7,
            0.2,
            0.9,
            -0.1,
            0.1,
            0.8,
            0.3,
            -0.2,
            -0.4,
            0.5,
            0.1,
            -0.6,
        ],
        dtype=np.float64,
    )
    masses = (0.97, 1.03, 1.0)
    analytic = planar_variational_jacobian(state, masses)
    finite_difference = np.empty((12, 12), dtype=np.float64)
    step = 2.0e-7
    for column in range(12):
        perturbation = np.zeros(12)
        perturbation[column] = step
        finite_difference[:, column] = (
            planar_rhs(0.0, state + perturbation, masses)
            - planar_rhs(0.0, state - perturbation, masses)
        ) / (2.0 * step)

    assert np.max(np.abs(analytic - finite_difference)) < 2.0e-8


def test_jacobi_transform_is_canonical() -> None:
    transform = canonical_jacobi_transform((0.97, 1.03, 1.0))
    identity = np.eye(6)
    symplectic = np.block(
        [[np.zeros((6, 6)), identity], [-identity, np.zeros((6, 6))]]
    )
    assert np.max(np.abs(transform @ symplectic @ transform.T - symplectic)) < 5e-16


@pytest.mark.parametrize(
    ("expected", "parameters"),
    [
        (
            "S",
            OrbitParameters(
                0.9,
                0.85,
                -0.222746846934935,
                1.78127695164077,
                0.415003557019123,
                6.35086603914435,
            ),
        ),
        (
            "U",
            OrbitParameters(
                0.95,
                0.9,
                -0.281386265317406,
                1.49896726022434,
                0.443236769411638,
                6.86766628267780,
            ),
        ),
    ],
)
def test_monodromy_classifies_pinned_source_examples(expected, parameters) -> None:
    result = classify_orbit_stability(parameters)

    assert result.label == expected
    assert result.symplectic_defect < 2.0e-5
    assert result.reciprocal_pair_error < 2.0e-4

