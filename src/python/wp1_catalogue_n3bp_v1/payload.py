"""Deterministic canonical candidate serialization and SHA-256 identifiers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from typing import Any

from .model import CatalogueCandidate


def _float(value: float) -> str:
    return float(value).hex()


def _complex(value: complex) -> dict[str, str]:
    number = complex(value)
    return {"real": _float(number.real), "imag": _float(number.imag)}


def candidate_record(candidate: CatalogueCandidate) -> dict[str, Any]:
    correction = candidate.correction
    parameters = correction.parameters
    stability: dict[str, Any] | None = None
    if candidate.stability is not None:
        result = candidate.stability
        stability = {
            "label": result.label,
            "trace": _float(result.trace),
            "second_trace_invariant": _float(result.second_trace_invariant),
            "discriminant": _float(result.discriminant),
            "reduced_traces": [_complex(value) for value in result.reduced_traces],
            "multipliers": [_complex(value) for value in result.multipliers],
            "symplectic_defect": _float(result.symplectic_defect),
            "reciprocal_pair_error": _float(result.reciprocal_pair_error),
        }
    return {
        "schema": "WP1-CAT-N3BP-v1/candidate-v1",
        "candidate_id": candidate.candidate_id,
        "parent_id": candidate.parent_id,
        "continuation_axis": candidate.continuation_axis,
        "parameters": {
            "m1": _float(parameters.m1),
            "m2": _float(parameters.m2),
            "m3": _float(1.0),
            "x1": _float(parameters.x1),
            "v1": _float(parameters.v1),
            "v2": _float(parameters.v2),
            "period": _float(parameters.period),
        },
        "state18": [_float(value) for value in correction.state],
        "correction": {
            "success": correction.success,
            "residual12": [_float(value) for value in correction.residual],
            "residual_linf": _float(correction.residual_linf),
            "position_closure_linf": _float(correction.position_closure_linf),
            "velocity_closure_linf": _float(correction.velocity_closure_linf),
            "nfev": correction.nfev,
        },
        "stability": stability,
        "provenance": {
            "native_generator": "WP1-CAT-N3BP-v1",
            "external_seed_count": 1,
            "external_catalogue_rows_used": 0,
            "evaluation_rows_used_as_seeds": 0,
        },
    }


def canonical_candidate_payload(candidate: CatalogueCandidate) -> bytes:
    return json.dumps(
        candidate_record(candidate),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def candidate_sha256(candidate: CatalogueCandidate) -> str:
    return hashlib.sha256(canonical_candidate_payload(candidate)).hexdigest()


def canonical_catalogue_payload(candidates: Sequence[CatalogueCandidate]) -> bytes:
    records = [
        candidate_record(candidate)
        for candidate in sorted(
            candidates,
            key=lambda item: (
                item.correction.parameters.m1,
                item.correction.parameters.m2,
                item.candidate_id,
            ),
        )
    ]
    envelope = {
        "schema": "WP1-CAT-N3BP-v1/catalogue-v1",
        "candidate_count": len(records),
        "candidates": records,
    }
    return json.dumps(
        envelope,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def catalogue_sha256(candidates: Sequence[CatalogueCandidate]) -> str:
    return hashlib.sha256(canonical_catalogue_payload(candidates)).hexdigest()
