"""Ensure the clean-room reduction is independent and convention-compatible."""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

import numpy as np

from src.python.n3bp_qualification import InertialState, SystemParameters
from src.python.threebody_reduction import JacobiPhaseState


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = (
    ROOT
    / "validation-external/wp2-threebody-flow-validation/reference/independent_reduction.py"
)


def _module():
    spec = importlib.util.spec_from_file_location("independent_reduction", REFERENCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reference_has_no_production_imports() -> None:
    tree = ast.parse(REFERENCE.read_text(encoding="utf-8"))
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    assert not any(name == "src" or name.startswith("src.") for name in imported)


def test_clean_room_jacobi_roundtrip_and_production_agreement() -> None:
    module = _module()
    masses = np.array([0.7, 1.1, 1.6])
    parameters = SystemParameters(masses, 0.9)
    positions = np.array(
        [[-0.8, 0.2, 0.4], [0.9, -0.4, 0.1], [0.3, 1.2, -0.7]]
    )
    velocities = np.array(
        [[0.4, -0.3, 0.8], [-0.7, 0.2, -0.1], [0.1, 0.6, -0.5]]
    )
    reference = module.jacobi_reduce(positions, velocities, masses)
    reconstructed = module.jacobi_reconstruct(reference, masses)
    np.testing.assert_allclose(reconstructed[0], positions, atol=3e-15)
    np.testing.assert_allclose(reconstructed[1], velocities, atol=3e-15)
    production = JacobiPhaseState.from_inertial(
        InertialState.from_components(positions, velocities), parameters
    )
    np.testing.assert_allclose(reference["rho"], production.rho, atol=2e-15)
    np.testing.assert_allclose(
        reference["lambda"], production.lambda_vector, atol=2e-15
    )
    np.testing.assert_allclose(reference["p_rho"], production.p_rho, atol=2e-15)
    np.testing.assert_allclose(
        reference["p_lambda"], production.p_lambda, atol=2e-15
    )


def test_clean_room_symbolic_transform_is_exactly_canonical() -> None:
    residual = _module().exact_canonical_residual()
    assert residual == [["0"] * 6 for _ in range(6)]


def test_clean_room_energy_lie_expression_vanishes_for_newtonian_flow() -> None:
    module = _module()
    masses = np.array([0.7, 1.1, 1.6])
    parameters = SystemParameters(masses, 0.9)
    state = InertialState.from_components(
        [[-0.8, 0.2, 0.4], [0.9, -0.4, 0.1], [0.3, 1.2, -0.7]],
        [[0.4, -0.3, 0.8], [-0.7, 0.2, -0.1], [0.1, 0.6, -0.5]],
    )
    from src.python.n3bp_qualification import newtonian_accelerations

    residual = module.newtonian_energy_lie(
        state.positions,
        state.velocities,
        newtonian_accelerations(state.positions, parameters),
        masses,
        parameters.gravitational_constant,
    )
    assert abs(residual) < 2e-15
