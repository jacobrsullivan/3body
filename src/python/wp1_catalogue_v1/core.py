"""Native planar Lyapunov generation and external-catalogue comparison.

Generation deliberately has no external-corpus argument.  JPL rows enter only
through :func:`match_external_rows`, after the native catalogue is complete.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import platform
import time
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import scipy

from src.python.orbits.differential_correction import correct_planar_lyapunov
from src.python.orbits.periodic_families import collinear_lagrange_point
from src.python.validation.cr3bp_variational import (
    cr3bp_jacobian,
    integrate_state_and_stm,
)


STATE_KEYS = ("x", "y", "z", "vx", "vy", "vz")


@dataclass(frozen=True)
class CatalogueRun:
    """Native catalogue rows and non-deterministic throughput metadata."""

    rows: list[dict[str, Any]]
    rejected_duplicates: list[dict[str, Any]]
    generation_seconds: float
    stability_seconds: float
    provenance: dict[str, Any]


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def jacobi_constant(state: Sequence[float], mu: float) -> float:
    """Return the normalized rotating-frame CR3BP Jacobi constant."""
    x, y, z, vx, vy, vz = np.asarray(state, dtype=float)
    r1 = math.sqrt((x + mu) ** 2 + y * y + z * z)
    r2 = math.sqrt((x - 1.0 + mu) ** 2 + y * y + z * z)
    if r1 == 0.0 or r2 == 0.0:
        raise ValueError("Jacobi constant is singular at a primary")
    return float(
        x * x
        + y * y
        + 2.0 * (1.0 - mu) / r1
        + 2.0 * mu / r2
        - vx * vx
        - vy * vy
        - vz * vz
    )


def planar_linear_seed(mu: float, lpoint: str, amplitude: float) -> tuple[np.ndarray, float]:
    """Construct an external-data-free center-mode seed at ``x_L-amplitude``."""
    if lpoint not in {"L1", "L2"}:
        raise ValueError("Only L1 and L2 are in the WP1-CAT-v1 scope")
    if not math.isfinite(amplitude) or amplitude <= 0.0:
        raise ValueError("amplitude must be finite and positive")
    x_l = collinear_lagrange_point(float(mu), lpoint)
    equilibrium = np.array([x_l, 0.0, 0.0, 0.0, 0.0, 0.0])
    planar = cr3bp_jacobian(equilibrium, mu)[np.ix_([0, 1, 3, 4], [0, 1, 3, 4])]
    eigenvalues = np.linalg.eigvals(planar)
    frequencies = sorted(
        abs(float(value.imag))
        for value in eigenvalues
        if abs(float(value.real)) < 1e-8 and abs(float(value.imag)) > 1e-8
    )
    if not frequencies:
        raise RuntimeError(f"No planar center frequency found at {lpoint}")
    omega = frequencies[0]
    uxx = float(cr3bp_jacobian(equilibrium, mu)[3, 0])
    dx = -float(amplitude)
    vy = -0.5 * (omega * omega + uxx) * dx
    state = np.array([x_l + dx, 0.0, 0.0, 0.0, vy, 0.0], dtype=float)
    return state, float(2.0 * math.pi / omega)


def classify_stability(index: float, bins: Mapping[str, float] | None = None) -> str:
    """Classify the JPL/Poincare stability index using frozen ordered bins."""
    boundaries = dict(
        bins
        or {
            "marginal_max": 1.0000001,
            "weak_max": 10.0,
            "moderate_max": 100.0,
        }
    )
    if not math.isfinite(index) or index < 1.0:
        return "invalid"
    if index <= boundaries["marginal_max"]:
        return "marginal"
    if index <= boundaries["weak_max"]:
        return "weakly_unstable"
    if index <= boundaries["moderate_max"]:
        return "moderately_unstable"
    return "strongly_unstable"


def _amplitude_grid(config: Mapping[str, Any]) -> list[float]:
    start = float(config["amplitude_min"])
    stop = float(config["amplitude_max"])
    step = float(config["amplitude_step"])
    count = int(round((stop - start) / step)) + 1
    grid = [start + index * step for index in range(count)]
    if not math.isclose(grid[-1], stop, rel_tol=0.0, abs_tol=2e-14):
        raise ValueError("Amplitude interval is not an integer number of steps")
    return grid


def _candidate_id(lpoint: str, index: int, amplitude: float) -> str:
    token = f"WP1-CAT-v1|earth-moon|lyapunov|{lpoint}|{index}|{amplitude:.16e}"
    return f"native-{lpoint.lower()}-{index:04d}-{_sha256(token.encode('ascii'))[:10]}"


def _canonical_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Return deterministic evidence fields, excluding wall-clock metadata."""
    fields = (
        "catalogue_id",
        "family",
        "lpoint",
        "branch",
        "mu",
        "amplitude",
        "continuation_index",
        "parent_id",
        *STATE_KEYS,
        "period",
        "jacobi",
        "symmetry_residual",
        "closure_error",
        "corrector_nfev",
        "stability_index",
        "stability_label",
        "monodromy_determinant_error",
        "reciprocal_pair_error",
        "stability_nfev",
        "seed_source",
        "corrector",
        "canonical_section",
    )
    return {key: row[key] for key in fields}


def canonical_catalogue_payload(rows: Sequence[Mapping[str, Any]]) -> bytes:
    """Serialize deterministic candidate evidence for hashing and parity."""
    ordered = sorted((_canonical_row(row) for row in rows), key=lambda row: row["catalogue_id"])
    return _canonical_json(ordered)


def deduplicate_catalogue(
    rows: Sequence[Mapping[str, Any]],
    *,
    jacobi_tolerance: float = 1e-11,
    period_relative_tolerance: float = 1e-10,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Deduplicate canonical-section rows using phase-invariant ``(C, T)``."""
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    ordered = sorted(
        (dict(row) for row in rows),
        key=lambda row: (str(row["lpoint"]), float(row["amplitude"])),
    )
    for row in ordered:
        duplicate_of = None
        for prior in accepted:
            if row["lpoint"] != prior["lpoint"]:
                continue
            period_scale = max(abs(float(row["period"])), abs(float(prior["period"])), 1.0)
            if (
                abs(float(row["jacobi"]) - float(prior["jacobi"])) <= jacobi_tolerance
                and abs(float(row["period"]) - float(prior["period"]))
                <= period_relative_tolerance * period_scale
            ):
                duplicate_of = str(prior["catalogue_id"])
                break
        if duplicate_of is None:
            accepted.append(row)
        else:
            rejected_row = dict(row)
            rejected_row["duplicate_of"] = duplicate_of
            rejected.append(rejected_row)
    return accepted, rejected


def generate_native_catalogue(spec: Mapping[str, Any], *, with_stability: bool = True) -> CatalogueRun:
    """Generate both frozen branches without consulting an external catalogue."""
    mu = float(spec["model"]["mu"])
    correction = spec["generation"]["correction"]
    generated: list[dict[str, Any]] = []
    generation_started = time.perf_counter()

    for lpoint in ("L1", "L2"):
        previous_state: np.ndarray | None = None
        previous_period: float | None = None
        parent_id = "analytic-linear-seed"
        for index, amplitude in enumerate(_amplitude_grid(spec["generation"]["branches"][lpoint])):
            fixed_x = collinear_lagrange_point(mu, lpoint) - amplitude
            if previous_state is None or previous_period is None:
                seed_state, seed_period = planar_linear_seed(mu, lpoint, amplitude)
            else:
                seed_state, seed_period = previous_state, previous_period
            result = correct_planar_lyapunov(
                seed_state,
                seed_period,
                mu,
                fixed_x=fixed_x,
                residual_tolerance=float(correction["symmetry_residual_tolerance"]),
                closure_tolerance=float(correction["closure_tolerance"]),
                max_nfev=int(correction["max_nfev"]),
            )
            if not result.success:
                raise RuntimeError(
                    f"Native continuation failed at {lpoint} amplitude={amplitude:.16g}: "
                    f"{result.message}"
                )
            state = np.asarray(result.initial_state, dtype=float)
            if not (state[0] < collinear_lagrange_point(mu, lpoint) and state[4] > 0.0):
                raise RuntimeError(f"Candidate left the frozen canonical section at {lpoint} {amplitude}")
            catalogue_id = _candidate_id(lpoint, index, amplitude)
            row: dict[str, Any] = {
                "catalogue_id": catalogue_id,
                "family": "lyapunov",
                "lpoint": lpoint,
                "branch": "planar-inner-positive-vy",
                "mu": mu,
                "amplitude": float(amplitude),
                "continuation_index": index,
                "parent_id": parent_id,
                **{key: float(value) for key, value in zip(STATE_KEYS, state)},
                "period": float(result.period),
                "jacobi": jacobi_constant(state, mu),
                "symmetry_residual": float(result.symmetry_residual),
                "closure_error": float(result.closure_error),
                "corrector_nfev": int(result.nfev),
                "stability_index": float("nan"),
                "stability_label": "not_computed",
                "monodromy_determinant_error": float("nan"),
                "reciprocal_pair_error": float("nan"),
                "stability_nfev": 0,
                "seed_source": "analytic-collinear-center-mode",
                "corrector": "src.python.orbits.differential_correction.correct_planar_lyapunov",
                "canonical_section": "y=z=vx=vz=0,x<x_L,vy>0",
            }
            generated.append(row)
            previous_state = state
            previous_period = float(result.period)
            parent_id = catalogue_id

    generation_seconds = time.perf_counter() - generation_started
    accepted, rejected = deduplicate_catalogue(
        generated,
        jacobi_tolerance=float(spec["generation"]["deduplication"]["jacobi_tolerance"]),
        period_relative_tolerance=float(
            spec["generation"]["deduplication"]["period_relative_tolerance"]
        ),
    )

    stability_started = time.perf_counter()
    if with_stability:
        stability = spec["stability"]
        for row in accepted:
            state = np.array([row[key] for key in STATE_KEYS], dtype=float)
            result = integrate_state_and_stm(
                state,
                float(row["period"]),
                mu,
                rtol=float(stability["rtol"]),
                atol=float(stability["atol"]),
            )
            row["stability_index"] = float(result.stability_index)
            row["stability_label"] = classify_stability(
                float(result.stability_index), stability["classification_bins"]
            )
            row["monodromy_determinant_error"] = float(result.determinant_error)
            row["reciprocal_pair_error"] = float(result.reciprocal_pair_error)
            row["stability_nfev"] = int(result.nfev)
    stability_seconds = time.perf_counter() - stability_started

    provenance = {
        "campaign": "WP1-CAT-v1",
        "external_data_used_by_generation": False,
        "model": dict(spec["model"]),
        "candidate_count_before_deduplication": len(generated),
        "candidate_count_after_deduplication": len(accepted),
        "duplicate_count": len(rejected),
        "catalogue_payload_sha256": _sha256(canonical_catalogue_payload(accepted)),
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
    }
    return CatalogueRun(
        rows=accepted,
        rejected_duplicates=rejected,
        generation_seconds=float(generation_seconds),
        stability_seconds=float(stability_seconds),
        provenance=provenance,
    )


def match_external_rows(
    external_rows: Iterable[Mapping[str, Any]],
    candidates: Sequence[Mapping[str, Any]],
    spec: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Match each JPL row to the nearest same-L-point native canonical crossing."""
    by_lpoint = {
        lpoint: [row for row in candidates if row["lpoint"] == lpoint]
        for lpoint in ("L1", "L2")
    }
    gates = spec["external_recovery"]["case_recovery"]
    bins = spec["stability"]["classification_bins"]
    matches: list[dict[str, Any]] = []
    for external in external_rows:
        lpoint = str(external["lpoint"])
        pool = by_lpoint.get(lpoint, [])
        if not pool:
            raise RuntimeError(f"No native candidates for external {lpoint} row")
        target_x = float(external["x"])
        candidate = min(pool, key=lambda row: abs(float(row["x"]) - target_x))
        target_state = np.array([float(external[key]) for key in STATE_KEYS])
        candidate_state = np.array([float(candidate[key]) for key in STATE_KEYS])
        state_error = float(np.linalg.norm(candidate_state - target_state))
        x_error = abs(float(candidate["x"]) - target_x)
        period_relative_error = abs(float(candidate["period"]) - float(external["period"])) / abs(
            float(external["period"])
        )
        jacobi_error = abs(float(candidate["jacobi"]) - float(external["jacobi"]))
        external_stability = float(external["stability"])
        stability_relative_error = abs(float(candidate["stability_index"]) - external_stability) / max(
            abs(external_stability), 1.0
        )
        external_label = classify_stability(external_stability, bins)
        label_match = candidate["stability_label"] == external_label
        recovered = bool(
            state_error <= float(gates["state_error_max"])
            and period_relative_error <= float(gates["period_relative_error_max"])
            and jacobi_error <= float(gates["jacobi_error_max"])
            and stability_relative_error <= float(gates["stability_relative_error_max"])
            and label_match
        )
        matches.append(
            {
                "catalog_id": str(external["catalog_id"]),
                "split": str(external["split"]),
                "family": str(external["family"]),
                "lpoint": lpoint,
                "external_x": target_x,
                "native_catalogue_id": str(candidate["catalogue_id"]),
                "native_x": float(candidate["x"]),
                "x_error": x_error,
                "state_error": state_error,
                "period_relative_error": period_relative_error,
                "jacobi_error": jacobi_error,
                "stability_relative_error": stability_relative_error,
                "external_stability_label": external_label,
                "native_stability_label": str(candidate["stability_label"]),
                "stability_label_match": label_match,
                "recovered": recovered,
                "match_key": "nearest same-lpoint x on frozen canonical section",
            }
        )
    return matches
