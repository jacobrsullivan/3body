"""Source-disjoint exact reproduction of WP6-DZ-FEAS-v1 controls."""

from __future__ import annotations

from fractions import Fraction


def _energy(speed_squares: tuple[Fraction, Fraction, Fraction]) -> dict[str, str]:
    kinetic = sum(speed_squares, Fraction(0)) / 2
    attraction = Fraction(1) + Fraction(1) + Fraction(1, 2)
    value = kinetic - attraction
    return {
        "kinetic": str(kinetic),
        "positive_potential": str(attraction),
        "energy": str(value),
    }


def legacy_fixture() -> dict[str, object]:
    result = _energy((Fraction(3, 2), Fraction(0), Fraction(3, 2)))
    return {
        **result,
        "angular_momentum": "0",
        "stated_zero_energy_is_false": result["energy"] == "-1",
    }


def corrected_homothetic() -> dict[str, object]:
    result = _energy((Fraction(5, 2), Fraction(0), Fraction(5, 2)))
    kappa2 = Fraction(5, 2)
    acceleration_from_curve = kappa2 / 2
    acceleration_from_force = Fraction(5, 4)
    return {
        **result,
        "angular_momentum": "0",
        "kappa_squared": str(kappa2),
        "derived_outer_acceleration_coefficient": str(acceleration_from_curve),
        "force_outer_acceleration_coefficient": str(acceleration_from_force),
        "equations_hold": acceleration_from_curve == acceleration_from_force,
        "known_homothetic_curve": True,
        "qualifying_witness": False,
    }


def scaling(energy: Fraction, scale: Fraction) -> dict[str, object]:
    if scale <= 0:
        raise ValueError("scale must be positive")
    transformed = energy / scale
    return {
        "original_energy": str(energy),
        "scaled_energy": str(transformed),
        "sign_preserved": (
            (energy > 0 and transformed > 0)
            or (energy < 0 and transformed < 0)
            or (energy == transformed == 0)
        ),
    }


def periodic(average_attraction: Fraction) -> dict[str, object]:
    if average_attraction <= 0:
        raise ValueError("average attraction must be positive")
    energy = -average_attraction / 2
    return {
        "average_positive_potential": str(average_attraction),
        "energy": str(energy),
        "energy_is_strictly_negative": energy < 0,
    }


def free_fall() -> dict[str, object]:
    result = _energy((Fraction(0), Fraction(0), Fraction(0)))
    return {
        **result,
        "energy_is_strictly_negative": Fraction(result["energy"]) < 0,
    }


def published_triple_collision() -> dict[str, object]:
    r2 = Fraction(9, 64)
    delta2 = Fraction(27, 256)
    return {
        "delta_over_r_squared": str(delta2 / r2),
        "shared_time_factor": True,
        "homothetic": True,
        "equal_masses_only": True,
        "released_from_rest_energy_is_negative": True,
        "qualifying_witness": False,
    }
