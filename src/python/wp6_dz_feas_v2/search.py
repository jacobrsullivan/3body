"""Deterministic exact coefficient-ideal search for WP6-DZ-FEAS-v2."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
import hashlib
import json
import signal
import time
from typing import Iterator

import sympy as sp

from .model import (
    COVER_IDS,
    MASS_ORDER_CASES,
    SUPPORTS,
    RectilinearModel,
    build_graph_template,
)


EXPECTED_SYSTEM_COUNT = len(MASS_ORDER_CASES) * len(COVER_IDS) * len(SUPPORTS) ** 2


class IdealTimeoutError(TimeoutError):
    """Raised when one locked coefficient ideal exceeds its time budget."""


@contextmanager
def _timeout(seconds: float) -> Iterator[None]:
    if seconds <= 0:
        raise IdealTimeoutError("coefficient-ideal deadline reached")

    def handler(_signum: int, _frame: object) -> None:
        raise IdealTimeoutError("coefficient-ideal deadline reached")

    previous_handler = signal.signal(signal.SIGALRM, handler)
    previous_timer = signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, *previous_timer)
        signal.signal(signal.SIGALRM, previous_handler)


@dataclass(frozen=True)
class SearchSystem:
    """One item in the frozen enumeration."""

    index: int
    system_id: str
    mass_case_id: str
    masses: tuple[int, int, int]
    cover_id: str
    support_v: tuple[int, ...]
    support_u: tuple[int, ...]


@dataclass(frozen=True)
class IdealDecision:
    """Exact decision for one saturated coefficient ideal."""

    system_id: str
    status: str
    decision_stage: str
    mass_case_id: str
    masses: tuple[int, int, int]
    cover_id: str
    support_v: tuple[int, ...]
    support_u: tuple[int, ...]
    coefficient_count: int
    energy_equation_count: int
    v_equation_count: int
    u_equation_count: int
    equation_sha256: str | None
    zero_dimensional: bool | None
    groebner_basis: tuple[str, ...]
    elapsed_seconds: float
    error: str | None = None

    def as_payload(self) -> dict[str, object]:
        return asdict(self)


def enumerate_systems() -> Iterator[SearchSystem]:
    """Yield all 11,700 systems in the locked order."""

    index = 0
    for mass_case_id, masses in MASS_ORDER_CASES:
        for cover_id in COVER_IDS:
            for support_v in SUPPORTS:
                for support_u in SUPPORTS:
                    index += 1
                    yield SearchSystem(
                        index=index,
                        system_id=f"S{index:05d}",
                        mass_case_id=mass_case_id,
                        masses=masses,
                        cover_id=cover_id,
                        support_v=support_v,
                        support_u=support_u,
                    )
    if index != EXPECTED_SYSTEM_COUNT:
        raise AssertionError(f"enumerated {index} systems")


def _canonical_equations(
    equations: tuple[sp.Expr, ...],
    variables: tuple[sp.Symbol, ...],
) -> tuple[sp.Expr, ...]:
    canonical: dict[str, sp.Expr] = {}
    variable_set = set(variables)
    for equation in equations:
        expanded = sp.expand(equation)
        if not expanded:
            continue
        if not expanded.free_symbols.issubset(variable_set):
            unexpected = expanded.free_symbols.difference(variable_set)
            raise ValueError(f"coefficient equation contains {unexpected}")
        polynomial = sp.Poly(expanded, *variables, domain=sp.QQ)
        primitive = polynomial.primitive()[1]
        expression = primitive.as_expr()
        leading = primitive.LC()
        if leading < 0:
            expression = -expression
        canonical[sp.srepr(expression)] = expression
    return tuple(canonical[key] for key in sorted(canonical))


def _is_nonzero_constant(equation: sp.Expr, variables: tuple[sp.Symbol, ...]) -> bool:
    return bool(equation != 0 and not equation.free_symbols.intersection(variables))


def _unit_basis(basis: sp.GroebnerBasis) -> bool:
    return len(basis.polys) == 1 and basis.polys[0].as_expr() == 1


def _equation_hash(equations: tuple[sp.Expr, ...]) -> str:
    payload = json.dumps(
        [sp.srepr(expression) for expression in equations],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def _basis(
    equations: tuple[sp.Expr, ...],
    variables: tuple[sp.Symbol, ...],
) -> sp.GroebnerBasis | None:
    if any(_is_nonzero_constant(equation, variables) for equation in equations):
        return None
    return sp.groebner(
        equations,
        *variables,
        order="lex",
        domain=sp.QQ,
        method="f5b",
    )


def decide_system(
    model: RectilinearModel,
    system: SearchSystem,
    *,
    timeout_seconds: float,
) -> IdealDecision:
    """Decide one saturated coefficient ideal within the locked deadline."""

    started = time.monotonic()
    try:
        with _timeout(timeout_seconds):
            template = build_graph_template(
                model,
                system.cover_id,
                system.support_v,
                system.support_u,
            )
            eta = sp.Symbol("eta")
            variables = template.coefficients + (eta,)
            saturation = eta * sp.prod(template.coefficients) - 1
            energy = _canonical_equations(
                template.coefficient_equations(template.energy_residual),
                variables,
            )
            v_equations = _canonical_equations(
                template.coefficient_equations(template.v_residual),
                variables,
            )
            u_equations = _canonical_equations(
                template.coefficient_equations(template.u_residual),
                variables,
            )
            stages = (
                ("ENERGY", energy + (saturation,)),
                ("ENERGY_AND_V", energy + v_equations + (saturation,)),
                (
                    "FULL",
                    energy + v_equations + u_equations + (saturation,),
                ),
            )
            final_basis: sp.GroebnerBasis | None = None
            final_equations: tuple[sp.Expr, ...] = ()
            for stage, raw_equations in stages:
                elapsed = time.monotonic() - started
                remaining = timeout_seconds - elapsed
                with _timeout(remaining):
                    equations = _canonical_equations(raw_equations, variables)
                    basis = _basis(equations, variables)
                if basis is None or _unit_basis(basis):
                    return IdealDecision(
                        system_id=system.system_id,
                        status="UNIT_IDEAL",
                        decision_stage=stage,
                        mass_case_id=system.mass_case_id,
                        masses=system.masses,
                        cover_id=system.cover_id,
                        support_v=system.support_v,
                        support_u=system.support_u,
                        coefficient_count=len(template.coefficients),
                        energy_equation_count=len(energy),
                        v_equation_count=len(v_equations),
                        u_equation_count=len(u_equations),
                        equation_sha256=_equation_hash(equations),
                        zero_dimensional=None,
                        groebner_basis=(),
                        elapsed_seconds=time.monotonic() - started,
                    )
                final_basis = basis
                final_equations = equations

            if final_basis is None:
                raise AssertionError("full ideal was not computed")
            return IdealDecision(
                system_id=system.system_id,
                status="NON_UNIT_IDEAL",
                decision_stage="FULL",
                mass_case_id=system.mass_case_id,
                masses=system.masses,
                cover_id=system.cover_id,
                support_v=system.support_v,
                support_u=system.support_u,
                coefficient_count=len(template.coefficients),
                energy_equation_count=len(energy),
                v_equation_count=len(v_equations),
                u_equation_count=len(u_equations),
                equation_sha256=_equation_hash(final_equations),
                zero_dimensional=bool(final_basis.is_zero_dimensional),
                groebner_basis=tuple(
                    sp.sstr(polynomial.as_expr()) for polynomial in final_basis.polys
                ),
                elapsed_seconds=time.monotonic() - started,
            )
    except IdealTimeoutError as error:
        return IdealDecision(
            system_id=system.system_id,
            status="TIMEOUT",
            decision_stage="UNDECIDED",
            mass_case_id=system.mass_case_id,
            masses=system.masses,
            cover_id=system.cover_id,
            support_v=system.support_v,
            support_u=system.support_u,
            coefficient_count=len(system.support_v) + len(system.support_u),
            energy_equation_count=0,
            v_equation_count=0,
            u_equation_count=0,
            equation_sha256=None,
            zero_dimensional=None,
            groebner_basis=(),
            elapsed_seconds=time.monotonic() - started,
            error=str(error),
        )
    except Exception as error:  # pragma: no cover - fail-closed ledger path
        return IdealDecision(
            system_id=system.system_id,
            status="ERROR",
            decision_stage="UNDECIDED",
            mass_case_id=system.mass_case_id,
            masses=system.masses,
            cover_id=system.cover_id,
            support_v=system.support_v,
            support_u=system.support_u,
            coefficient_count=len(system.support_v) + len(system.support_u),
            energy_equation_count=0,
            v_equation_count=0,
            u_equation_count=0,
            equation_sha256=None,
            zero_dimensional=None,
            groebner_basis=(),
            elapsed_seconds=time.monotonic() - started,
            error=f"{type(error).__name__}: {error}",
        )
