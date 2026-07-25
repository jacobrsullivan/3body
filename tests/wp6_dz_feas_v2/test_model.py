from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import sympy as sp

from src.python.wp6_dz_feas_v2 import (
    COVER_IDS,
    MASS_ORDER_CASES,
    SUPPORTS,
    build_graph_template,
    build_rectilinear_model,
    reconstruct_barycentric_state,
)
from src.python.wp6_dz_feas_v2.model import shape_cover


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = (
    ROOT / "validation-external/wp6-dz-feas-v2/reference/barycentric_reference.py"
)


def _reference_module():
    specification = importlib.util.spec_from_file_location("_wp6_v2_ref", REFERENCE)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_locked_enumeration_counts_are_exact() -> None:
    assert len(COVER_IDS) == 4
    assert len(SUPPORTS) == 15
    assert len(MASS_ORDER_CASES) == 13
    assert len(COVER_IDS) * len(SUPPORTS) ** 2 * len(MASS_ORDER_CASES) == 11700
    assert SUPPORTS[0] == (-2,)
    assert SUPPORTS[-1] == (1, 2)


def test_symbolic_model_matches_source_disjoint_barycentric_derivation() -> None:
    masses = sp.symbols("m1 m2 m3", positive=True)
    production = build_rectilinear_model(masses)
    independent = _reference_module().derive(masses)
    substitution = {
        independent["x"]: production.x,
        independent["v"]: production.v,
        independent["u"]: production.u,
        independent["r"]: production.r,
    }
    assert sp.cancel(production.A - independent["A"].subs(substitution)) == 0
    assert sp.cancel(production.B - independent["B"].subs(substitution)) == 0
    assert (
        sp.cancel(
            production.normalized_energy
            - independent["normalized_energy"].subs(substitution)
        )
        == 0
    )
    assert sp.simplify(production.mass_metric - independent["mass_metric"]) == sp.zeros(
        2
    )
    assert independent["center_of_mass"] == 0
    assert independent["linear_momentum"] == 0


@pytest.mark.parametrize("masses", [(1, 1, 1), (1, 2, 3), (2, 3, 5)])
def test_normalized_energy_is_an_invariant_zero_surface(masses) -> None:
    model = build_rectilinear_model(masses)
    derivative = (
        sp.diff(model.normalized_energy, model.x) * model.vector_field[1]
        + sp.diff(model.normalized_energy, model.v) * model.vector_field[2]
        + sp.diff(model.normalized_energy, model.u) * model.vector_field[3]
    )
    assert sp.cancel(derivative - model.v * model.normalized_energy) == 0
    assert (
        sp.cancel(
            model.normalized_energy
            - model.energy_numerator / (2 * model.x * (1 - model.x))
        )
        == 0
    )


def test_barycentric_lift_has_zero_center_and_momentum() -> None:
    r, x, v, u = sp.symbols("r x v u", positive=True)
    state = reconstruct_barycentric_state((2, 3, 5), r=r, x=x, v=v, u=u)
    assert state["center_of_mass"] == 0
    assert state["linear_momentum"] == 0
    positions = state["positions"]
    assert sp.simplify(positions[1] - positions[0] - r * x) == 0
    assert sp.simplify(positions[2] - positions[1] - r * (1 - x)) == 0


def test_all_shape_covers_are_exact_and_distinct() -> None:
    z = sp.Symbol("z")
    covers = [shape_cover(cover_id, z) for cover_id in COVER_IDS]
    assert covers == [z, z**2, 1 - z**2, z**2 / (1 + z**2)]
    assert len({sp.srepr(cover) for cover in covers}) == 4


def test_graph_template_produces_coefficient_polynomials() -> None:
    model = build_rectilinear_model((1, 2, 3))
    template = build_graph_template(
        model,
        "PHI-BOTH-SQ",
        (-2, 1),
        (-1, 2),
    )
    assert len(template.coefficients) == 4
    for residual in (
        template.energy_residual,
        template.v_residual,
        template.u_residual,
    ):
        equations = template.coefficient_equations(residual)
        assert equations
        assert all(template.z not in equation.free_symbols for equation in equations)
        assert all(
            equation.free_symbols.issubset(set(template.coefficients))
            for equation in equations
        )


@pytest.mark.parametrize(
    "masses",
    [
        (1, 2),
        (1, 2, 0),
        (1, -2, 3),
        (1.0, 2, 3),
        (True, 2, 3),
    ],
)
def test_model_rejects_out_of_scope_mass_inputs(masses) -> None:
    with pytest.raises((TypeError, ValueError)):
        build_rectilinear_model(masses)


def test_graph_template_rejects_scope_extensions() -> None:
    model = build_rectilinear_model((1, 2, 3))
    with pytest.raises(ValueError):
        build_graph_template(model, "NEW-COVER", (-1,), (1,))
    with pytest.raises(ValueError):
        build_graph_template(model, "PHI-AFFINE", (-3,), (1,))
    with pytest.raises(ValueError):
        build_graph_template(model, "PHI-AFFINE", (-2, -1, 0), (1,))


def test_reference_source_is_disjoint() -> None:
    text = REFERENCE.read_text(encoding="utf-8")
    assert "src.python" not in text
    assert "wp6_dz_feas_v2" not in text
