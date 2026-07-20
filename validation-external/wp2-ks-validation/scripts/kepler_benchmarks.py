"""Versioned and digest-locked analytic Kepler benchmark definitions.

The catalogue contains relative, specific two-body elliptic elements using the
same inertial-frame and angle conventions documented by ``kepler_reference``.
It spans a unit circular orbit, inclined low-eccentricity motion, retrograde
moderate-eccentricity motion, and a high-eccentricity orbit whose periapsis is
strictly outside the declared collision-exclusion radius.

The payload is canonicalized as UTF-8 JSON with sorted keys and compact
separators.  ``BENCHMARK_SHA256`` locks every value and phase checkpoint.  This
module is validation-side only and has no dependency on production KS modules.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json

from kepler_reference import EllipticElements


BENCHMARK_SCHEMA = "wp2-kepler-analytic-benchmark/v1"
BENCHMARK_SHA256 = "7c63311172dc8aebbf83ac0749bd67416aee4e2e8e1fc2c92fc4de61931a5e83"


@dataclass(frozen=True)
class KeplerBenchmark:
    """One immutable benchmark case and its dimensionless period phases."""

    case_id: str
    description: str
    elements: EllipticElements
    period_fractions: tuple[float, ...]
    reduced_mass: float = 1.0


_LOCKED_PAYLOAD = {
    "schema": BENCHMARK_SCHEMA,
    "state_order": ["x", "y", "z", "vx", "vy", "vz"],
    "angle_unit": "radian",
    "dynamics": "r_ddot = -mu * r / |r|^3",
    "collision_exclusion_radius": 0.1,
    "cases": [
        {
            "case_id": "circular_unit",
            "description": "Unit circular equatorial orbit",
            "elements": {
                "mu": 1.0,
                "semi_major_axis": 1.0,
                "eccentricity": 0.0,
                "inclination": 0.0,
                "longitude_of_ascending_node": 0.0,
                "argument_of_periapsis": 0.0,
                "mean_anomaly_at_epoch": 0.0,
                "epoch": 0.0,
            },
            "period_fractions": [0.0, 0.125, 0.25, 0.5, 0.875, 1.0],
        },
        {
            "case_id": "low_e_inclined",
            "description": "Inclined low-eccentricity orbit with nonzero epoch",
            "elements": {
                "mu": 2.5,
                "semi_major_axis": 1.6,
                "eccentricity": 0.2,
                "inclination": 0.35,
                "longitude_of_ascending_node": 0.7,
                "argument_of_periapsis": -0.4,
                "mean_anomaly_at_epoch": 0.3,
                "epoch": -0.25,
            },
            "period_fractions": [0.0, 0.1, 0.25, 0.5, 0.9, 1.0],
        },
        {
            "case_id": "moderate_e_retrograde",
            "description": "Retrograde moderate-eccentricity orbit",
            "elements": {
                "mu": 0.4,
                "semi_major_axis": 2.75,
                "eccentricity": 0.6,
                "inclination": 2.2,
                "longitude_of_ascending_node": -1.1,
                "argument_of_periapsis": 0.9,
                "mean_anomaly_at_epoch": -2.0,
                "epoch": 1.5,
            },
            "period_fractions": [0.0, 0.05, 0.25, 0.5, 0.75, 1.0],
        },
        {
            "case_id": "high_e_collision_free",
            "description": "High-eccentricity orbit with periapsis radius 0.12",
            "elements": {
                "mu": 1.0,
                "semi_major_axis": 4.0,
                "eccentricity": 0.97,
                "inclination": 1.0,
                "longitude_of_ascending_node": 2.4,
                "argument_of_periapsis": -0.8,
                "mean_anomaly_at_epoch": 0.0,
                "epoch": 0.0,
            },
            "period_fractions": [
                0.0,
                0.000001,
                0.0001,
                0.01,
                0.25,
                0.5,
                0.99,
                1.0,
            ],
        },
    ],
}


def canonical_benchmark_bytes() -> bytes:
    """Return the canonical byte representation covered by the lock digest."""

    return json.dumps(
        _LOCKED_PAYLOAD,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def benchmark_digest() -> str:
    """Return the SHA-256 digest of the canonical benchmark payload."""

    return hashlib.sha256(canonical_benchmark_bytes()).hexdigest()


def verify_benchmark_lock() -> None:
    """Raise if any locked benchmark datum differs from the accepted payload."""

    actual_digest = benchmark_digest()
    if not hmac.compare_digest(actual_digest, BENCHMARK_SHA256):
        raise RuntimeError(
            "WP2 Kepler benchmark lock mismatch: "
            f"expected {BENCHMARK_SHA256}, got {actual_digest}"
        )


def load_locked_benchmarks() -> tuple[KeplerBenchmark, ...]:
    """Verify the payload lock and return typed immutable benchmark cases."""

    verify_benchmark_lock()
    return tuple(
        KeplerBenchmark(
            case_id=record["case_id"],
            description=record["description"],
            elements=EllipticElements(**record["elements"]),
            period_fractions=tuple(record["period_fractions"]),
        )
        for record in _LOCKED_PAYLOAD["cases"]
    )


def collision_exclusion_radius() -> float:
    """Return the radial threshold used to classify all cases collision-free."""

    return float(_LOCKED_PAYLOAD["collision_exclusion_radius"])
