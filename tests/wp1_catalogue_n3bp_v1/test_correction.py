from __future__ import annotations

import numpy as np
import pytest

from src.python.wp1_catalogue_n3bp_v1 import (
    CorrectionSettings,
    OrbitParameters,
    canonical_section_state,
    correct_orbit,
)
from src.python.wp1_catalogue_n3bp_v1.catalogue import _continue_mass_line


@pytest.fixture(scope="module")
def corrected_root():
    result = correct_orbit(OrbitParameters.disclosed_root())
    assert result.success
    return result


def test_canonical_section_is_full_18d_and_barycentric() -> None:
    state = canonical_section_state(0.97, 1.03, -0.37, 1.21, 0.45, 7.5)
    masses = np.array([0.97, 1.03, 1.0])
    positions = state[:9].reshape(3, 3)
    velocities = state[9:].reshape(3, 3)

    assert state.shape == (18,)
    assert np.max(np.abs(masses @ positions)) < 2.0e-16
    assert np.max(np.abs(masses @ velocities)) < 2.0e-16
    assert np.array_equal(state[[2, 5, 8, 11, 14, 17]], np.zeros(6))


def test_disclosed_rounded_root_corrects_to_full_planar_closure(corrected_root) -> None:
    rounded = OrbitParameters.disclosed_root()
    corrected = corrected_root

    assert corrected.nfev <= 24
    assert corrected.residual_linf < 2.0e-8
    assert corrected.position_closure_linf < 2.0e-8
    assert corrected.velocity_closure_linf < 2.0e-8
    assert np.linalg.norm(
        corrected.parameters.correction_vector() - rounded.correction_vector(),
        ord=np.inf,
    ) < 1.0e-7


def test_one_secant_continuation_step_corrects_at_target_mass(corrected_root) -> None:
    continued = _continue_mass_line(
        corrected_root,
        "m1",
        (1.0, 1.005),
        CorrectionSettings(),
        correct_orbit,
        1.0e-3,
    )

    result, parent_mass = continued[1.005]
    assert result.success
    assert result.parameters.m1 == pytest.approx(1.005)
    assert result.parameters.m2 == pytest.approx(1.0)
    assert parent_mass == pytest.approx(1.0)
    assert result.residual_linf < 2.0e-8
