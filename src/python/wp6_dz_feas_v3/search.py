"""Dual-exact localized coefficient-ideal search for WP6-DZ-FEAS-v3."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
import hashlib
import json
import signal
import time
from typing import Iterator

import sympy as sp

from src.python.wp6_dz_feas_v2.model import (
    COVER_IDS,
    MASS_ORDER_CASES,
    SUPPORTS,
    RectilinearModel,
    shape_cover,
)


EXPECTED_SYSTEM_COUNT = len(MASS_ORDER_CASES) * len(COVER_IDS) * len(SUPPORTS) ** 2
PRIMARY_METHOD = "f5b"
VERIFICATION_METHOD = "buchberger"
TERM_ORDER = "grevlex"


class IdealTimeoutError(TimeoutError):
    """Raised when one locked system exceeds its complete time budget."""


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
    """One system in the unchanged v2 enumeration."""

    index: int
    system_id: str
    mass_case_id: str
    masses: tuple[int, int, int]
    cover_id: str
    support_v: tuple[int, ...]
    support_u: tuple[int, ...]


@dataclass(frozen=True)
class GraphData:
    """Frozen graph expressions without eagerly constructed residuals."""

    z: sp.Symbol
    x_of_z: sp.Expr
    v_of_z: sp.Expr
    u_of_z: sp.Expr
    coefficients: tuple[sp.Symbol, ...]


@dataclass(frozen=True)
class StageData:
    """Raw and localized equations introduced by one lazy stage."""

    stage: str
    raw_equations: tuple[sp.Expr, ...]
    localized_equations: tuple[sp.Expr, ...]
    stripped_monomial_exponents: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class StageAudit:
    """Exact dual-algorithm audit for one cumulative ideal."""

    stage: str
    new_raw_equation_count: int
    new_localized_equation_count: int
    cumulative_equation_count: int
    stripped_monomial_exponents: tuple[tuple[int, ...], ...]
    equation_sha256: str
    primary_method: str
    primary_is_unit: bool
    primary_basis_sha256: str
    verification_method: str
    verification_is_unit: bool
    verification_basis_sha256: str
    algorithms_agree: bool


@dataclass(frozen=True)
class IdealDecision:
    """Final exact or fail-closed decision for one locked system."""

    system_id: str
    status: str
    decision_stage: str
    mass_case_id: str
    masses: tuple[int, int, int]
    cover_id: str
    support_v: tuple[int, ...]
    support_u: tuple[int, ...]
    coefficient_count: int
    stage_audits: tuple[StageAudit, ...]
    zero_dimensional: bool | None
    lex_basis: tuple[str, ...]
    elapsed_seconds: float
    error: str | None = None

    def as_payload(self) -> dict[str, object]:
        return asdict(self)


def enumerate_systems() -> Iterator[SearchSystem]:
    """Yield all 11,700 systems in the frozen v2 order."""

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


def _graph_expression(
    z: sp.Symbol,
    prefix: str,
    support: tuple[int, ...],
) -> tuple[sp.Expr, tuple[sp.Symbol, ...]]:
    if support not in SUPPORTS:
        raise ValueError(f"support is outside the frozen v2 library: {support}")
    coefficients = sp.symbols(
        " ".join(f"{prefix}_{power:+d}" for power in support)
    )
    if isinstance(coefficients, sp.Symbol):
        coefficients = (coefficients,)
    expression = sp.Add(
        *(
            coefficient * z**power
            for coefficient, power in zip(coefficients, support)
        )
    )
    return expression, tuple(coefficients)


def build_graph_data(system: SearchSystem) -> GraphData:
    """Construct only the frozen graph expressions and coefficients."""

    z = sp.Symbol("z")
    v_of_z, alpha = _graph_expression(z, "alpha", system.support_v)
    u_of_z, beta = _graph_expression(z, "beta", system.support_u)
    return GraphData(
        z=z,
        x_of_z=shape_cover(system.cover_id, z),
        v_of_z=v_of_z,
        u_of_z=u_of_z,
        coefficients=alpha + beta,
    )


def _canonical_equations(
    equations: tuple[sp.Expr, ...],
    variables: tuple[sp.Symbol, ...],
) -> tuple[sp.Expr, ...]:
    canonical: dict[str, sp.Expr] = {}
    variable_set = set(variables)
    for equation in equations:
        expanded = sp.expand(equation)
        if expanded == 0:
            continue
        if not expanded.free_symbols.issubset(variable_set):
            unexpected = expanded.free_symbols.difference(variable_set)
            raise ValueError(f"coefficient equation contains {unexpected}")
        polynomial = sp.Poly(expanded, *variables, domain=sp.QQ)
        primitive = polynomial.primitive()[1]
        expression = primitive.as_expr()
        if primitive.LC() < 0:
            expression = -expression
        canonical[sp.srepr(expression)] = expression
    return tuple(canonical[key] for key in sorted(canonical))


def _coefficient_equations(
    expression: sp.Expr,
    graph: GraphData,
) -> tuple[sp.Expr, ...]:
    numerator, denominator = sp.fraction(sp.cancel(sp.together(expression)))
    coefficient_set = set(graph.coefficients)
    if denominator.free_symbols.intersection(coefficient_set):
        raise ValueError("coefficient-dependent denominator is outside the lock")
    if numerator == 0:
        return ()
    polynomial = sp.Poly(sp.expand(numerator), graph.z)
    raw = tuple(
        coefficient
        for coefficient in polynomial.all_coeffs()
        if coefficient != 0
    )
    return _canonical_equations(raw, graph.coefficients)


def localize_equations(
    equations: tuple[sp.Expr, ...],
    coefficients: tuple[sp.Symbol, ...],
) -> tuple[tuple[sp.Expr, ...], tuple[tuple[int, ...], ...]]:
    """Remove coefficient monomials that are units under support saturation."""

    raw = _canonical_equations(equations, coefficients)
    localized: list[sp.Expr] = []
    exponents: list[tuple[int, ...]] = []
    for equation in raw:
        polynomial = sp.Poly(equation, *coefficients, domain=sp.QQ)
        terms = polynomial.terms()
        minimum = tuple(
            min(monomial[position] for monomial, _coefficient in terms)
            for position in range(len(coefficients))
        )
        divisor_expression = sp.prod(
            variable**power
            for variable, power in zip(coefficients, minimum)
        )
        divisor = sp.Poly(
            divisor_expression,
            *coefficients,
            domain=sp.QQ,
        )
        quotient = polynomial.exquo(divisor).as_expr()
        localized.append(quotient)
        exponents.append(minimum)
    return (
        _canonical_equations(tuple(localized), coefficients),
        tuple(exponents),
    )


def build_stage_data(
    model: RectilinearModel,
    graph: GraphData,
    stage: str,
) -> StageData:
    """Construct and localize exactly one residual stage."""

    substitution = {
        model.x: graph.x_of_z,
        model.v: graph.v_of_z,
        model.u: graph.u_of_z,
    }
    if stage == "ENERGY":
        residual = model.energy_numerator.subs(substitution)
    elif stage == "V":
        residual = sp.diff(graph.v_of_z, graph.z) * graph.u_of_z
        residual -= sp.diff(graph.x_of_z, graph.z) * (
            graph.v_of_z**2 / 2
            + model.A.subs(model.x, graph.x_of_z)
        )
    elif stage == "U":
        residual = sp.diff(graph.u_of_z, graph.z) * graph.u_of_z
        residual -= sp.diff(graph.x_of_z, graph.z) * (
            model.B.subs(model.x, graph.x_of_z)
            - graph.v_of_z * graph.u_of_z / 2
        )
    else:
        raise ValueError(f"unknown residual stage: {stage}")
    raw = _coefficient_equations(residual, graph)
    localized, exponents = localize_equations(raw, graph.coefficients)
    return StageData(
        stage=stage,
        raw_equations=raw,
        localized_equations=localized,
        stripped_monomial_exponents=exponents,
    )


def _equation_hash(equations: tuple[sp.Expr, ...]) -> str:
    payload = json.dumps(
        [sp.srepr(expression) for expression in equations],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def _basis_fingerprint(basis: sp.GroebnerBasis) -> tuple[bool, str]:
    expressions = tuple(
        sp.srepr(polynomial.as_expr()) for polynomial in basis.polys
    )
    payload = json.dumps(
        expressions,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    is_unit = (
        len(basis.polys) == 1 and basis.polys[0].as_expr() == 1
    )
    return is_unit, hashlib.sha256(payload).hexdigest()


def _exact_basis(
    equations: tuple[sp.Expr, ...],
    variables: tuple[sp.Symbol, ...],
    *,
    method: str,
    order: str = TERM_ORDER,
) -> sp.GroebnerBasis:
    return sp.groebner(
        equations,
        *variables,
        order=order,
        domain=sp.QQ,
        method=method,
    )


def _audit_stage(
    stage_data: StageData,
    cumulative: tuple[sp.Expr, ...],
    variables: tuple[sp.Symbol, ...],
) -> tuple[StageAudit, bool | None]:
    equations = _canonical_equations(cumulative, variables)
    primary = _exact_basis(
        equations,
        variables,
        method=PRIMARY_METHOD,
    )
    primary_is_unit, primary_hash = _basis_fingerprint(primary)
    verification = _exact_basis(
        equations,
        variables,
        method=VERIFICATION_METHOD,
    )
    verification_is_unit, verification_hash = _basis_fingerprint(
        verification
    )
    agreement = primary_is_unit == verification_is_unit
    audit = StageAudit(
        stage=stage_data.stage,
        new_raw_equation_count=len(stage_data.raw_equations),
        new_localized_equation_count=len(stage_data.localized_equations),
        cumulative_equation_count=len(equations),
        stripped_monomial_exponents=(
            stage_data.stripped_monomial_exponents
        ),
        equation_sha256=_equation_hash(equations),
        primary_method=f"{PRIMARY_METHOD}-{TERM_ORDER}",
        primary_is_unit=primary_is_unit,
        primary_basis_sha256=primary_hash,
        verification_method=f"{VERIFICATION_METHOD}-{TERM_ORDER}",
        verification_is_unit=verification_is_unit,
        verification_basis_sha256=verification_hash,
        algorithms_agree=agreement,
    )
    return audit, primary_is_unit if agreement else None


def _decision(
    system: SearchSystem,
    *,
    status: str,
    decision_stage: str,
    coefficient_count: int,
    stage_audits: list[StageAudit],
    started: float,
    zero_dimensional: bool | None = None,
    lex_basis: tuple[str, ...] = (),
    error: str | None = None,
) -> IdealDecision:
    return IdealDecision(
        system_id=system.system_id,
        status=status,
        decision_stage=decision_stage,
        mass_case_id=system.mass_case_id,
        masses=system.masses,
        cover_id=system.cover_id,
        support_v=system.support_v,
        support_u=system.support_u,
        coefficient_count=coefficient_count,
        stage_audits=tuple(stage_audits),
        zero_dimensional=zero_dimensional,
        lex_basis=lex_basis,
        elapsed_seconds=time.monotonic() - started,
        error=error,
    )


def decide_system(
    model: RectilinearModel,
    system: SearchSystem,
    *,
    timeout_seconds: float,
) -> IdealDecision:
    """Dual-decide one localized ideal within the complete system budget."""

    started = time.monotonic()
    audits: list[StageAudit] = []
    coefficient_count = len(system.support_v) + len(system.support_u)
    current_stage = "GRAPH"
    try:
        with _timeout(timeout_seconds):
            graph = build_graph_data(system)
            eta = sp.Symbol("eta")
            variables = graph.coefficients + (eta,)
            saturation = eta * sp.prod(graph.coefficients) - 1
            cumulative: tuple[sp.Expr, ...] = (saturation,)

            for residual_stage, decision_stage in (
                ("ENERGY", "ENERGY"),
                ("V", "ENERGY_AND_V"),
                ("U", "FULL"),
            ):
                current_stage = residual_stage
                stage_data = build_stage_data(
                    model,
                    graph,
                    residual_stage,
                )
                cumulative = _canonical_equations(
                    cumulative + stage_data.localized_equations,
                    variables,
                )
                audit, is_unit = _audit_stage(
                    stage_data,
                    cumulative,
                    variables,
                )
                audits.append(audit)
                if is_unit is None:
                    return _decision(
                        system,
                        status="DISAGREEMENT",
                        decision_stage=decision_stage,
                        coefficient_count=coefficient_count,
                        stage_audits=audits,
                        started=started,
                        error="exact algorithms disagree on ideal unitness",
                    )
                if is_unit:
                    return _decision(
                        system,
                        status="UNIT_IDEAL",
                        decision_stage=decision_stage,
                        coefficient_count=coefficient_count,
                        stage_audits=audits,
                        started=started,
                    )

            current_stage = "LEX_BRANCH"
            lex = _exact_basis(
                cumulative,
                variables,
                method=PRIMARY_METHOD,
                order="lex",
            )
            return _decision(
                system,
                status="NON_UNIT_IDEAL",
                decision_stage="FULL",
                coefficient_count=coefficient_count,
                stage_audits=audits,
                started=started,
                zero_dimensional=bool(lex.is_zero_dimensional),
                lex_basis=tuple(
                    sp.sstr(polynomial.as_expr())
                    for polynomial in lex.polys
                ),
            )
    except IdealTimeoutError as error:
        return _decision(
            system,
            status="TIMEOUT",
            decision_stage=current_stage,
            coefficient_count=coefficient_count,
            stage_audits=audits,
            started=started,
            error=str(error),
        )
    except Exception as error:  # pragma: no cover - fail-closed ledger path
        return _decision(
            system,
            status="ERROR",
            decision_stage=current_stage,
            coefficient_count=coefficient_count,
            stage_audits=audits,
            started=started,
            error=f"{type(error).__name__}: {error}",
        )
