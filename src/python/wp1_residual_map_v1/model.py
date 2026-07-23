"""Deterministic and deliberately non-interpretive WP1 research work map."""

from __future__ import annotations

from fractions import Fraction
import math
from typing import Any, Iterable


LOCAL_STABLE_NORMAL_FORM = "LOCAL_STABLE_NORMAL_FORM"
ASYMPTOTIC_MANIFOLD = "ASYMPTOTIC_MANIFOLD"
HIGHER_VARIATIONAL_EXCEPTION = "HIGHER_VARIATIONAL_EXCEPTION"
DOMAIN_RESTRICTED_OR_NONMEROMORPHIC = "DOMAIN_RESTRICTED_OR_NONMEROMORPHIC"

PUBLICATION_GATE = (
    "NO_INTERPRETATION: require a separately named and locked "
    "candidate-specific qualification before interpreting any invariant."
)
PROHIBITED_INTERPRETATION = (
    "This row does not discover, infer, or establish an invariant, KAM "
    "stability, a manifold, or any form of integrability."
)
EXCEPTIONAL_SIGMA = (Fraction(1, 3), Fraction(8, 27), Fraction(2, 9))


def _exact_binary64(value: Any) -> Fraction:
    if isinstance(value, bool):
        raise TypeError("boolean is not a numeric catalogue value")
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("catalogue value must be finite")
        return Fraction(*value.as_integer_ratio())
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.lstrip("+-").lower().startswith("0x"):
            parsed = float.fromhex(stripped)
            if not math.isfinite(parsed):
                raise ValueError("catalogue value must be finite")
            return Fraction(*parsed.as_integer_ratio())
        return Fraction(stripped)
    raise TypeError(f"unsupported catalogue numeric type: {type(value).__name__}")


def _sigma(parameters: dict[str, Any]) -> tuple[tuple[Fraction, ...], Fraction]:
    masses = tuple(_exact_binary64(parameters[name]) for name in ("m1", "m2", "m3"))
    if any(value <= 0 for value in masses):
        raise ValueError("catalogue masses must be strictly positive")
    m1, m2, m3 = masses
    sigma = (m1 * m2 + m2 * m3 + m3 * m1) / (m1 + m2 + m3) ** 2
    return masses, sigma


def _metric_value(value: Any) -> Fraction:
    return _exact_binary64(value)


def _quality_key(candidate: dict[str, Any]) -> tuple[Fraction, Fraction, Fraction, str]:
    return (
        _metric_value(candidate["correction"]["residual_linf"]),
        _metric_value(candidate["stability"]["symplectic_defect"]),
        _metric_value(candidate["stability"]["reciprocal_pair_error"]),
        str(candidate["candidate_id"]),
    )


def _authorized_next_test(label: str) -> str:
    if label == "S":
        return (
            "Lock a candidate-specific local normal-form and KAM "
            "nondegeneracy qualification with exact or interval validation."
        )
    if label == "U":
        return (
            "Lock a candidate-specific stable/unstable manifold and "
            "homoclinic/scattering qualification with sealed interpretation."
        )
    raise ValueError(f"unknown qualified planar stability label: {label!r}")


def _row(candidate: dict[str, Any]) -> dict[str, Any]:
    candidate_id = str(candidate["candidate_id"])
    label = str(candidate["stability"]["label"])
    if label not in {"S", "U"}:
        raise ValueError(f"unknown qualified planar stability label: {label!r}")
    masses, sigma = _sigma(candidate["parameters"])
    overlays = [DOMAIN_RESTRICTED_OR_NONMEROMORPHIC]
    if sigma in EXCEPTIONAL_SIGMA:
        overlays.append(HIGHER_VARIATIONAL_EXCEPTION)
    return {
        "candidate_id": candidate_id,
        "masses_exact": [str(value) for value in masses],
        "sigma": str(sigma),
        "qualified_planar_label": label,
        "primary_track": (
            LOCAL_STABLE_NORMAL_FORM if label == "S" else ASYMPTOTIC_MANIFOLD
        ),
        "overlays": overlays,
        "quality_metrics": {
            "correction_residual_linf": candidate["correction"]["residual_linf"],
            "symplectic_defect": candidate["stability"]["symplectic_defect"],
            "reciprocal_pair_error": candidate["stability"][
                "reciprocal_pair_error"
            ],
        },
        "publication_gate": PUBLICATION_GATE,
        "authorized_next_test": _authorized_next_test(label),
        "prohibited_interpretation": PROHIBITED_INTERPRETATION,
    }


def _rank_tracks(
    rows: list[dict[str, Any]], candidates_by_id: dict[str, dict[str, Any]]
) -> None:
    tracks = (LOCAL_STABLE_NORMAL_FORM, ASYMPTOTIC_MANIFOLD)
    for track in tracks:
        selected = [row for row in rows if row["primary_track"] == track]
        selected.sort(
            key=lambda row: _quality_key(candidates_by_id[row["candidate_id"]])
        )
        for rank, row in enumerate(selected, start=1):
            row["track_rank"] = rank


def _no_interpretation_language(rows: Iterable[dict[str, Any]]) -> bool:
    return all(
        str(row["publication_gate"]).startswith("NO_INTERPRETATION:")
        and "does not discover" in str(row["prohibited_interpretation"])
        for row in rows
    )


def build_residual_map(catalogue: dict[str, Any]) -> dict[str, Any]:
    """Map every candidate exactly once and rank only within bounded tracks."""

    candidates = list(catalogue.get("candidates", []))
    by_id: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        candidate_id = str(candidate["candidate_id"])
        if candidate_id in by_id:
            raise ValueError(f"duplicate candidate_id: {candidate_id}")
        by_id[candidate_id] = candidate
    rows = [_row(candidate) for candidate in candidates]
    _rank_tracks(rows, by_id)
    rows.sort(key=lambda row: row["candidate_id"])
    stable = sum(row["primary_track"] == LOCAL_STABLE_NORMAL_FORM for row in rows)
    unstable = sum(row["primary_track"] == ASYMPTOTIC_MANIFOLD for row in rows)
    exceptional = sum(
        HIGHER_VARIATIONAL_EXCEPTION in row["overlays"] for row in rows
    )
    return {
        "schema_version": "1.0",
        "campaign": "WP1-RESIDUAL-MAP-v1",
        "source_campaign": catalogue.get("campaign"),
        "candidate_count": len(rows),
        "counts": {
            "local_stable_normal_form": stable,
            "asymptotic_manifold": unstable,
            "higher_variational_exception_overlay": exceptional,
            "domain_restricted_or_nonmeromorphic_overlay": len(rows),
        },
        "publication_gate": PUBLICATION_GATE,
        "no_invariant_interpretation": _no_interpretation_language(rows),
        "candidates": rows,
    }

