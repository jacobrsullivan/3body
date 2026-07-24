from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

from src.python.n3bp_qualification import SystemParameters
from src.python.so3_reduction_v1 import (
    SO3LeafState,
    hamiltonian_flow,
    hamiltonian_gradient,
    leaf_derivative_from_quotient_flow,
    poisson_tensor,
)
from src.python.threebody_flow import euclidean_reduced_flow
from src.python.threebody_reduction import EuclideanQuotientState


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = (
    ROOT
    / "validation-external/wp2-so3-leaf-v1/reference/independent_leaf.py"
)


def _reference():
    spec = importlib.util.spec_from_file_location("independent_so3_leaf", REFERENCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _quotient(
    *,
    zero_ell: bool = False,
    masses: tuple[float, float, float] = (0.7, 1.1, 1.6),
) -> EuclideanQuotientState:
    parameters = SystemParameters(masses, gravitational_constant=0.9)
    r, x, y = 1.4, -0.3, 0.8
    if zero_ell:
        px, py = 0.2, -0.35
        v3 = 0.0
        u2 = (y * px - x * py) / r
        u3 = 0.0
    else:
        u2, u3, px, py, v3 = 0.45, -0.27, 0.2, -0.35, 0.31
    return EuclideanQuotientState(
        parameters,
        rho_body=[r, 0.0, 0.0],
        lambda_body=[x, y, 0.0],
        p_rho_body=[0.12, u2, u3],
        p_lambda_body=[px, py, v3],
    )


@pytest.mark.parametrize("zero_ell", [False, True])
def test_coordinate_roundtrip_energy_and_leaf_dimension(zero_ell: bool) -> None:
    quotient = _quotient(zero_ell=zero_ell)
    state = SO3LeafState.from_euclidean_quotient(quotient)
    rebuilt = state.to_euclidean_quotient()
    np.testing.assert_allclose(
        rebuilt.as_orbit_coordinates(),
        quotient.as_orbit_coordinates(),
        atol=2e-15,
    )
    assert state.hamiltonian() == pytest.approx(quotient.total_energy(), abs=2e-15)
    assert state.poisson_rank == (6 if zero_ell else 8)
    assert state.symplectic_leaf_dimension == (6 if zero_ell else 8)


def test_reference_is_source_disjoint_and_roundtrips() -> None:
    text = REFERENCE.read_text(encoding="utf-8")
    assert "src.python" not in text
    reference = _reference()
    quotient = _quotient()
    vector = quotient.as_orbit_coordinates()
    leaf = reference.quotient_to_leaf(vector)
    np.testing.assert_allclose(
        leaf, SO3LeafState.from_euclidean_quotient(quotient).coordinates
    )
    np.testing.assert_allclose(reference.leaf_to_quotient(leaf), vector)


@pytest.mark.parametrize(
    "masses",
    [(1.0, 1.0, 1.0), (2.0, 3.0, 5.0), (0.5, 1.4, 2.75)],
)
def test_analytic_gradient_agrees_with_source_disjoint_finite_difference(
    masses: tuple[float, float, float],
) -> None:
    state = SO3LeafState.from_euclidean_quotient(_quotient(masses=masses))
    reference = _reference()
    finite = reference.finite_gradient(
        state.coordinates,
        np.array(masses),
        state.parameters.gravitational_constant,
    )
    np.testing.assert_allclose(state.gradient(), finite, atol=2e-8, rtol=2e-8)


def test_poisson_structure_is_antisymmetric_has_correct_rank_and_casimir() -> None:
    for zero_ell, rank in ((False, 8), (True, 6)):
        state = SO3LeafState.from_euclidean_quotient(_quotient(zero_ell=zero_ell))
        tensor = poisson_tensor(state.coordinates)
        np.testing.assert_array_equal(tensor + tensor.T, np.zeros((9, 9)))
        assert np.linalg.matrix_rank(tensor) == rank
        casimir_gradient = np.concatenate((np.zeros(6), 2.0 * state.coordinates[6:]))
        np.testing.assert_allclose(tensor @ casimir_gradient, np.zeros(9), atol=1e-15)
        assert abs(float(np.dot(casimir_gradient, state.flow()))) < 2e-15


@pytest.mark.parametrize("zero_ell", [False, True])
def test_hamiltonian_flow_matches_qualified_pushed_quotient_flow(
    zero_ell: bool,
) -> None:
    quotient = _quotient(zero_ell=zero_ell)
    state = SO3LeafState.from_euclidean_quotient(quotient)
    pushed = euclidean_reduced_flow(
        quotient.to_translation_quotient(np.eye(3))
    )
    expected = leaf_derivative_from_quotient_flow(
        pushed.quotient, pushed.quotient_derivative
    )
    np.testing.assert_allclose(state.flow(), expected, atol=3e-15, rtol=2e-15)
    if zero_ell:
        np.testing.assert_allclose(state.flow()[6:], np.zeros(3), atol=1e-15)


def test_finite_reference_detects_body_poisson_sign() -> None:
    state = SO3LeafState.from_euclidean_quotient(_quotient())
    reference = _reference()
    correct = reference.finite_hamiltonian_flow(
        state.coordinates,
        state.parameters.masses,
        state.parameters.gravitational_constant,
    )
    wrong = reference.finite_hamiltonian_flow(
        state.coordinates,
        state.parameters.masses,
        state.parameters.gravitational_constant,
        reverse_body_sign=True,
    )
    np.testing.assert_allclose(
        hamiltonian_flow(state.coordinates, state.parameters),
        correct,
        atol=3e-8,
        rtol=3e-8,
    )
    assert np.linalg.norm(correct - wrong) > 0.1


def test_public_functions_reject_singular_or_invalid_inputs() -> None:
    parameters = SystemParameters([1.0, 1.0, 1.0])
    base = np.array([1.0, 0.2, 0.7, 0.0, 0.0, 0.0, 0.1, 0.2, 0.3])
    for index in (0, 2):
        changed = base.copy()
        changed[index] = 0.0
        with pytest.raises(ValueError):
            hamiltonian_gradient(changed, parameters)
    with pytest.raises(ValueError):
        SO3LeafState(parameters, base[:-1])
    with pytest.raises(ValueError):
        SO3LeafState(parameters, np.full(9, np.nan))


def test_analytic_gradient_all_components_are_behaviorally_required() -> None:
    state = SO3LeafState.from_euclidean_quotient(_quotient())
    reference = _reference()
    finite = reference.finite_gradient(
        state.coordinates,
        state.parameters.masses,
        state.parameters.gravitational_constant,
    )
    analytic = hamiltonian_gradient(state.coordinates, state.parameters)
    for index in range(9):
        changed = analytic.copy()
        changed[index] += 1e-3
        assert abs(changed[index] - finite[index]) > 9e-4
