"""Source-disjoint SymPy reference for WP1-RESIDUAL-MAP-v1."""

from __future__ import annotations

import math
from typing import Any

import sympy as sp


STABLE = "LOCAL_STABLE_NORMAL_FORM"
UNSTABLE = "ASYMPTOTIC_MANIFOLD"
HIGHER = "HIGHER_VARIATIONAL_EXCEPTION"
RESTRICTED = "DOMAIN_RESTRICTED_OR_NONMEROMORPHIC"
GATE = (
    "NO_INTERPRETATION: require a separately named and locked "
    "candidate-specific qualification before interpreting any invariant."
)
NONCLAIM = (
    "This row does not discover, infer, or establish an invariant, KAM "
    "stability, a manifold, or any form of integrability."
)
EXCEPTIONS = (sp.Rational(1, 3), sp.Rational(8, 27), sp.Rational(2, 9))


def _number(value: Any) -> sp.Rational:
    if isinstance(value, bool):
        raise TypeError("boolean is not numeric")
    if isinstance(value, int):
        return sp.Rational(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("number must be finite")
        numerator, denominator = value.as_integer_ratio()
        return sp.Rational(numerator, denominator)
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.lstrip("+-").lower().startswith("0x"):
            parsed = float.fromhex(stripped)
            if not math.isfinite(parsed):
                raise ValueError("number must be finite")
            numerator, denominator = parsed.as_integer_ratio()
            return sp.Rational(numerator, denominator)
        return sp.Rational(stripped)
    raise TypeError(f"unsupported numeric type: {type(value).__name__}")


def _masses_and_sigma(parameters: dict[str, Any]) -> tuple[list[sp.Rational], sp.Rational]:
    masses = [_number(parameters[name]) for name in ("m1", "m2", "m3")]
    if any(mass <= 0 for mass in masses):
        raise ValueError("masses must be positive")
    total = sum(masses)
    sigma = (
        masses[0] * masses[1]
        + masses[1] * masses[2]
        + masses[2] * masses[0]
    ) / total**2
    return masses, sp.factor(sigma)


def _quality(candidate: dict[str, Any]) -> tuple[sp.Rational, sp.Rational, sp.Rational, str]:
    return (
        _number(candidate["correction"]["residual_linf"]),
        _number(candidate["stability"]["symplectic_defect"]),
        _number(candidate["stability"]["reciprocal_pair_error"]),
        str(candidate["candidate_id"]),
    )


def _next(label: str) -> str:
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
    raise ValueError(f"unknown label: {label!r}")


def build_map(catalogue: dict[str, Any]) -> dict[str, Any]:
    candidates = list(catalogue.get("candidates", []))
    by_id: dict[str, dict[str, Any]] = {}
    rows = []
    for candidate in candidates:
        candidate_id = str(candidate["candidate_id"])
        if candidate_id in by_id:
            raise ValueError(f"duplicate candidate_id: {candidate_id}")
        by_id[candidate_id] = candidate
        label = str(candidate["stability"]["label"])
        if label not in {"S", "U"}:
            raise ValueError(f"unknown label: {label!r}")
        masses, sigma = _masses_and_sigma(candidate["parameters"])
        overlays = [RESTRICTED]
        if sigma in EXCEPTIONS:
            overlays.append(HIGHER)
        rows.append(
            {
                "candidate_id": candidate_id,
                "masses_exact": [str(value) for value in masses],
                "sigma": str(sigma),
                "qualified_planar_label": label,
                "primary_track": STABLE if label == "S" else UNSTABLE,
                "overlays": overlays,
                "quality_metrics": {
                    "correction_residual_linf": candidate["correction"][
                        "residual_linf"
                    ],
                    "symplectic_defect": candidate["stability"][
                        "symplectic_defect"
                    ],
                    "reciprocal_pair_error": candidate["stability"][
                        "reciprocal_pair_error"
                    ],
                },
                "publication_gate": GATE,
                "authorized_next_test": _next(label),
                "prohibited_interpretation": NONCLAIM,
            }
        )
    for track in (STABLE, UNSTABLE):
        selected = [row for row in rows if row["primary_track"] == track]
        selected.sort(key=lambda row: _quality(by_id[row["candidate_id"]]))
        for rank, row in enumerate(selected, start=1):
            row["track_rank"] = rank
    rows.sort(key=lambda row: row["candidate_id"])
    return {
        "schema_version": "1.0",
        "campaign": "WP1-RESIDUAL-MAP-v1",
        "source_campaign": catalogue.get("campaign"),
        "candidate_count": len(rows),
        "counts": {
            "local_stable_normal_form": sum(
                row["primary_track"] == STABLE for row in rows
            ),
            "asymptotic_manifold": sum(
                row["primary_track"] == UNSTABLE for row in rows
            ),
            "higher_variational_exception_overlay": sum(
                HIGHER in row["overlays"] for row in rows
            ),
            "domain_restricted_or_nonmeromorphic_overlay": len(rows),
        },
        "publication_gate": GATE,
        "no_invariant_interpretation": all(
            row["publication_gate"].startswith("NO_INTERPRETATION:")
            and "does not discover" in row["prohibited_interpretation"]
            for row in rows
        ),
        "candidates": rows,
    }

