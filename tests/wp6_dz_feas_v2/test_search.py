from __future__ import annotations

from itertools import islice

from src.python.wp6_dz_feas_v2 import build_rectilinear_model
from src.python.wp6_dz_feas_v2.search import (
    EXPECTED_SYSTEM_COUNT,
    decide_system,
    enumerate_systems,
)


def test_enumeration_is_complete_unique_and_locked_order() -> None:
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
    assert len({system.system_id for system in systems}) == EXPECTED_SYSTEM_COUNT


def test_first_locked_system_is_exactly_excluded_on_energy() -> None:
    system = next(enumerate_systems())
    decision = decide_system(
        build_rectilinear_model(system.masses),
        system,
        timeout_seconds=5,
    )
    assert decision.status == "UNIT_IDEAL"
    assert decision.decision_stage == "ENERGY"
    assert decision.equation_sha256
    assert decision.error is None


def test_zero_budget_fails_closed() -> None:
    system = next(islice(enumerate_systems(), 1, None))
    decision = decide_system(
        build_rectilinear_model(system.masses),
        system,
        timeout_seconds=0,
    )
    assert decision.status == "TIMEOUT"
    assert decision.decision_stage == "UNDECIDED"
    assert decision.error
