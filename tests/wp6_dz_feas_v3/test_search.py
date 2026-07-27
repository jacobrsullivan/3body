from __future__ import annotations

from itertools import islice

import sympy as sp

from src.python.wp6_dz_feas_v2.model import (
    build_graph_template,
    build_rectilinear_model,
)
from src.python.wp6_dz_feas_v3.search import (
    EXPECTED_SYSTEM_COUNT,
    build_graph_data,
    build_stage_data,
    decide_system,
    enumerate_systems,
    localize_equations,
)


def _system(index: int):
    return next(islice(enumerate_systems(), index - 1, None))


def test_enumeration_is_the_frozen_v2_enumeration() -> None:
    systems = list(enumerate_systems())
    assert len(systems) == EXPECTED_SYSTEM_COUNT == 11700
    assert systems[0].system_id == "S00001"
    assert systems[0].mass_case_id == "M01"
    assert systems[0].cover_id == "PHI-AFFINE"
    assert systems[0].support_v == (-2,)
    assert systems[0].support_u == (-2,)
    assert systems[-1].system_id == "S11700"
    assert systems[-1].mass_case_id == "M13"
    assert systems[-1].cover_id == "PHI-BOTH-SQ"
    assert systems[-1].support_v == (1, 2)
    assert systems[-1].support_u == (1, 2)
    assert len({system.system_id for system in systems}) == 11700


def test_support_localization_removes_only_saturated_monomial() -> None:
    alpha, beta = sp.symbols("alpha beta")
    localized, exponents = localize_equations(
        (
            -6 * alpha**3 * beta**2 * (alpha + 2 * beta),
            9 * alpha * beta**4,
        ),
        (alpha, beta),
    )
    assert localized == (alpha + 2 * beta, 1)
    assert exponents == ((3, 2), (1, 4))
    for a_value, b_value in ((1, 2), (-3, 5), (sp.I, 7)):
        raw_zero = all(
            expression.subs({alpha: a_value, beta: b_value}) == 0
            for expression in (
                -6 * alpha**3 * beta**2 * (alpha + 2 * beta),
                9 * alpha * beta**4,
            )
        )
        localized_zero = all(
            expression.subs({alpha: a_value, beta: b_value}) == 0
            for expression in localized
        )
        assert raw_zero == localized_zero


def test_energy_stage_uses_exact_v2_polynomial_identity() -> None:
    system = _system(11700)
    model = build_rectilinear_model(system.masses)
    graph = build_graph_data(system)
    stage = build_stage_data(model, graph, "ENERGY")
    template = build_graph_template(
        model,
        system.cover_id,
        system.support_v,
        system.support_u,
    )
    assert sp.cancel(
        model.energy_numerator.subs(
            {
                model.x: graph.x_of_z,
                model.v: graph.v_of_z,
                model.u: graph.u_of_z,
            }
        )
        - 2
        * graph.x_of_z
        * (1 - graph.x_of_z)
        * template.energy_residual
    ) == 0
    assert stage.raw_equations
    assert stage.localized_equations


def test_first_system_is_dual_exact_unit_at_energy() -> None:
    system = _system(1)
    decision = decide_system(
        build_rectilinear_model(system.masses),
        system,
        timeout_seconds=30,
    )
    assert decision.status == "UNIT_IDEAL"
    assert decision.decision_stage == "ENERGY"
    assert len(decision.stage_audits) == 1
    audit = decision.stage_audits[0]
    assert audit.primary_is_unit is True
    assert audit.verification_is_unit is True
    assert audit.algorithms_agree is True
    assert audit.equation_sha256


def test_representative_v2_unresolved_and_tail_are_dual_decided() -> None:
    for index in (1661, 5233, 9793, 11689, 11690, 11700):
        system = _system(index)
        decision = decide_system(
            build_rectilinear_model(system.masses),
            system,
            timeout_seconds=30,
        )
        assert decision.status == "UNIT_IDEAL", (
            system.system_id,
            decision.error,
        )
        assert decision.decision_stage == "ENERGY"
        assert all(audit.algorithms_agree for audit in decision.stage_audits)


def test_zero_budget_fails_closed() -> None:
    system = _system(1)
    decision = decide_system(
        build_rectilinear_model(system.masses),
        system,
        timeout_seconds=0,
    )
    assert decision.status == "TIMEOUT"
    assert decision.decision_stage == "GRAPH"
    assert decision.error
