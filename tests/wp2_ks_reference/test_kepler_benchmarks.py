"""Qualification-lock and corpus-wide checks for Kepler benchmarks."""

import ast
import math
from pathlib import Path

import numpy as np
import pytest

from kepler_benchmarks import (
    BENCHMARK_SCHEMA,
    BENCHMARK_SHA256,
    benchmark_digest,
    collision_exclusion_radius,
    load_locked_benchmarks,
    verify_benchmark_lock,
)
from kepler_reference import orbital_diagnostics, period_closure, propagate_elliptic


EXPECTED_DIGEST = "7c63311172dc8aebbf83ac0749bd67416aee4e2e8e1fc2c92fc4de61931a5e83"
SCRIPTS_DIR = (
    Path(__file__).resolve().parents[2]
    / "validation-external"
    / "wp2-ks-validation"
    / "scripts"
)


def test_benchmark_payload_matches_pinned_digest():
    assert BENCHMARK_SCHEMA == "wp2-kepler-analytic-benchmark/v1"
    assert BENCHMARK_SHA256 == EXPECTED_DIGEST
    assert benchmark_digest() == EXPECTED_DIGEST
    verify_benchmark_lock()


def test_locked_catalogue_spans_declared_eccentricity_regimes():
    cases = load_locked_benchmarks()

    assert [case.case_id for case in cases] == [
        "circular_unit",
        "low_e_inclined",
        "moderate_e_retrograde",
        "high_e_collision_free",
    ]
    assert [case.elements.eccentricity for case in cases] == [0.0, 0.2, 0.6, 0.97]
    assert all(
        case.elements.periapsis_radius > collision_exclusion_radius()
        for case in cases
    )


@pytest.mark.parametrize(
    "case", load_locked_benchmarks(), ids=lambda case: case.case_id
)
def test_benchmark_invariants_and_radial_bounds(case):
    elements = case.elements
    times = elements.epoch + elements.period * np.asarray(case.period_fractions)
    states = propagate_elliptic(elements, times)
    expected_energy = -elements.mu / (2.0 * elements.semi_major_axis)
    expected_angular_momentum = math.sqrt(
        elements.mu
        * elements.semi_major_axis
        * (1.0 - elements.eccentricity**2)
    )
    expected_lrl_magnitude = elements.mu * elements.eccentricity

    for state in states:
        diagnostics = orbital_diagnostics(state, elements.mu)
        assert elements.periapsis_radius * (1.0 - 2.0e-14) <= diagnostics.radius
        assert diagnostics.radius <= elements.apoapsis_radius * (1.0 + 2.0e-14)
        assert diagnostics.specific_energy == pytest.approx(
            expected_energy, rel=8.0e-14, abs=8.0e-14
        )
        assert diagnostics.angular_momentum_magnitude == pytest.approx(
            expected_angular_momentum, rel=8.0e-14, abs=8.0e-14
        )
        assert np.linalg.norm(diagnostics.laplace_runge_lenz) == pytest.approx(
            expected_lrl_magnitude, rel=8.0e-13, abs=8.0e-14
        )


@pytest.mark.parametrize(
    "case", load_locked_benchmarks(), ids=lambda case: case.case_id
)
def test_every_benchmark_closes_after_one_period(case):
    closure = period_closure(case.elements)

    assert closure.position_error < 3.0e-13
    assert closure.velocity_error < 3.0e-13
    assert closure.relative_state_error < 2.0e-13


def test_validation_scripts_do_not_import_production_modules():
    for script_path in sorted(SCRIPTS_DIR.glob("*.py")):
        syntax_tree = ast.parse(script_path.read_text(encoding="utf-8"))
        imported_modules = []
        for node in ast.walk(syntax_tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.append(node.module)

        assert all(
            module != "src" and not module.startswith("src.")
            for module in imported_modules
        ), f"production import found in {script_path}"
