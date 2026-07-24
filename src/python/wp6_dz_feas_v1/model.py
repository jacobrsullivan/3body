"""Exact audit model for ``WP6-DZ-FEAS-v1``.

The campaign is a witness search, not a nonintegrability proof.  These controls
make the common false positives decidable with rational arithmetic before any
candidate can be promoted to a Morales-Ramis campaign.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
from typing import Any, Mapping, Sequence, TypeAlias


RationalInput: TypeAlias = Fraction | int | float | str

QUALIFIED_WITNESS = "QUALIFIED_WITNESS"
COMPLETE_BOUNDED_NULL_RESULT = "COMPLETE_BOUNDED_NULL_RESULT"
INCOMPLETE = "INCOMPLETE"

REQUIREMENT_IDS = tuple(f"W{index}" for index in range(1, 13))
REQUIREMENT_STATUSES = frozenset({"PASS", "FAIL", "NOT_REACHED"})


def exact_fraction(value: RationalInput) -> Fraction:
    """Convert a supported finite rational input without decimal rounding."""

    if isinstance(value, bool):
        raise TypeError("boolean values are not rational inputs")
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("floating-point input must be finite")
        return Fraction(*value.as_integer_ratio())
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            raise ValueError("rational input must not be empty")
        return Fraction(stripped)
    raise TypeError(f"unsupported rational input type: {type(value).__name__}")


def _positive_fraction(value: RationalInput, name: str) -> Fraction:
    result = exact_fraction(value)
    if result <= 0:
        raise ValueError(f"{name} must be strictly positive")
    return result


def _sign(value: Fraction) -> str:
    if value > 0:
        return "positive"
    if value < 0:
        return "negative"
    return "zero"


def newtonian_energy(
    masses: Sequence[RationalInput],
    squared_speeds: Sequence[RationalInput],
    pair_distances: Mapping[tuple[int, int], RationalInput],
) -> dict[str, object]:
    """Evaluate ``H=T-U`` exactly for a finite collision-free state."""

    mass_values = tuple(_positive_fraction(value, "mass") for value in masses)
    speed_values = tuple(exact_fraction(value) for value in squared_speeds)
    if len(mass_values) != len(speed_values):
        raise ValueError("masses and squared_speeds must have the same length")
    if any(value < 0 for value in speed_values):
        raise ValueError("squared speeds must be nonnegative")

    kinetic = sum(
        (mass * speed_squared / 2)
        for mass, speed_squared in zip(mass_values, speed_values)
    )
    potential = Fraction(0)
    expected_pairs = {
        (left, right)
        for left in range(len(mass_values))
        for right in range(left + 1, len(mass_values))
    }
    if set(pair_distances) != expected_pairs:
        raise ValueError(
            "pair_distances must contain every unordered pair exactly once"
        )
    for (left, right), distance in pair_distances.items():
        separation = _positive_fraction(distance, "pair distance")
        potential += mass_values[left] * mass_values[right] / separation
    energy = kinetic - potential
    return {
        "kinetic": str(kinetic),
        "positive_potential": str(potential),
        "energy": str(energy),
        "energy_sign": _sign(energy),
    }


def legacy_euler_fixture_certificate() -> dict[str, object]:
    """Audit the pre-existing equal-mass Euler fixture exactly."""

    energy = newtonian_energy(
        masses=(1, 1, 1),
        squared_speeds=(Fraction(3, 2), 0, Fraction(3, 2)),
        pair_distances={(0, 1): 1, (0, 2): 2, (1, 2): 1},
    )
    return {
        "positions_x": ["-1", "0", "1"],
        "outer_speed_squared": "3/2",
        **energy,
        "angular_momentum": "0",
        "stated_zero_energy_is_false": energy["energy"] == "-1",
        "qualifying_witness": False,
    }


def corrected_euler_homothetic_certificate() -> dict[str, object]:
    """Verify the corrected parabolic Euler curve over a quadratic base field."""

    energy = newtonian_energy(
        masses=(1, 1, 1),
        squared_speeds=(Fraction(5, 2), 0, Fraction(5, 2)),
        pair_distances={(0, 1): 1, (0, 2): 2, (1, 2): 1},
    )
    kappa_squared = Fraction(5, 2)
    central_multiplier = Fraction(5, 4)

    # q=(-s^2,0,s^2), qdot=(kappa/s,0,-kappa/s),
    # d/dt=(-kappa/(2*s^2))*d/ds, kappa^2=5/2.
    derived_outer_acceleration_coefficient = kappa_squared / 2
    force_outer_acceleration_coefficient = Fraction(1) + Fraction(1, 4)
    return {
        "phase_parameter": "s",
        "dense_open_condition": "s!=0",
        "differential_base_field": "C(s,kappa), kappa^2=5/2",
        "time_derivation": "d/dt=(-kappa/(2*s^2))*d/ds",
        "positions_x": ["-s^2", "0", "s^2"],
        "velocities_x": ["kappa/s", "0", "-kappa/s"],
        "kappa_squared": str(kappa_squared),
        "central_multiplier": str(central_multiplier),
        "derived_outer_acceleration_coefficient": str(
            derived_outer_acceleration_coefficient
        ),
        "force_outer_acceleration_coefficient": str(
            force_outer_acceleration_coefficient
        ),
        "equations_hold": (
            derived_outer_acceleration_coefficient
            == force_outer_acceleration_coefficient
        ),
        **energy,
        "angular_momentum": "0",
        "energy_identically_zero": energy["energy"] == "0",
        "angular_momentum_identically_zero": True,
        "gradients_H_C_generically_independent": True,
        "gradient_certificate": (
            "dH has a nonzero p_x component while dC has a nonzero p_y "
            "component and zero p_x components on s!=0"
        ),
        "known_homothetic_curve": True,
        "known_tangent_ve_obstruction": False,
        "qualifying_witness": False,
        "failed_requirements": ["W3", "W9"],
    }


def newtonian_scaling_certificate(
    energy: RationalInput,
    length_scale: RationalInput,
) -> dict[str, object]:
    """Verify that positive Newtonian scaling cannot change energy sign."""

    original = exact_fraction(energy)
    scale = _positive_fraction(length_scale, "length_scale")
    scaled = original / scale
    return {
        "original_energy": str(original),
        "length_scale": str(scale),
        "scaled_energy": str(scaled),
        "original_sign": _sign(original),
        "scaled_sign": _sign(scaled),
        "sign_preserved": _sign(original) == _sign(scaled),
        "nonzero_energy_cannot_scale_to_zero": original == 0 or scaled != 0,
    }


def periodic_energy_certificate(
    average_positive_potential: RationalInput,
) -> dict[str, object]:
    """Apply the exact Lagrange-Jacobi average to a periodic orbit.

    For a collision-free periodic Newtonian solution,
    ``<I''>=4H+2<U>=0``.  Thus ``H=-<U>/2<0``.
    """

    average_potential = _positive_fraction(
        average_positive_potential, "average_positive_potential"
    )
    energy = -average_potential / 2
    return {
        "lagrange_jacobi_identity": "<I''>=4H+2<U>=0",
        "average_positive_potential": str(average_potential),
        "energy": str(energy),
        "energy_sign": _sign(energy),
        "nonstationary_collision_free_periodic_H_zero_impossible": energy < 0,
    }


def free_fall_energy_certificate(
    masses: Sequence[RationalInput] = (1, 1, 1),
    pair_distances: Mapping[tuple[int, int], RationalInput] | None = None,
) -> dict[str, object]:
    """Show that a finite collision-free state released from rest has ``H<0``."""

    if pair_distances is None:
        pair_distances = {(0, 1): 1, (0, 2): 2, (1, 2): 1}
    energy = newtonian_energy(
        masses=masses,
        squared_speeds=tuple(0 for _ in masses),
        pair_distances=pair_distances,
    )
    return {
        **energy,
        "released_from_rest": True,
        "finite_collision_free_free_fall_H_zero_impossible": (
            energy["energy_sign"] == "negative"
        ),
    }


def sundman_triple_collision_certificate() -> dict[str, object]:
    """Audit the recent explicit equal-mass triple-collision proposal.

    The published formula has ``r`` and ``delta`` proportional to the same
    ``cos^2`` factor.  Its shape ratio is therefore constant.  The displayed
    finite initial configuration is released from rest, so its Newtonian energy
    is strictly negative without needing the detailed pair-distance convention.
    """

    r_coefficient_squared = Fraction(9, 64)
    delta_coefficient_squared = Fraction(27, 256)
    ratio_squared = delta_coefficient_squared / r_coefficient_squared
    return {
        "mass_scope": "m0=m1=m2=1",
        "initial_velocity": "zero",
        "finite_distinct_initial_configuration": True,
        "energy_sign": "negative",
        "energy_zero": False,
        "r_factor": "cos^2(pi*u/(2*u1))",
        "delta_factor": "cos^2(pi*u/(2*u1))",
        "delta_over_r_squared": str(ratio_squared),
        "constant_shape": ratio_squared == Fraction(3, 4),
        "published_ratio_is_constant": True,
        "homothetic": True,
        "formal_regularization_only": True,
        "qualifying_witness": False,
        "failed_requirements": ["W1", "W2", "W3", "W4", "W5", "W10"],
    }


@dataclass(frozen=True)
class LedgerDecision:
    """Derived feasibility outcome for a complete candidate ledger."""

    outcome: str
    qualifying_candidate_ids: tuple[str, ...]
    candidate_count: int
    all_requirements_decided: bool
    all_candidates_have_failure: bool

    @property
    def mr_promotion_authorized(self) -> bool:
        return (
            self.outcome == QUALIFIED_WITNESS
            and len(self.qualifying_candidate_ids) == 1
        )

    def as_payload(self) -> dict[str, object]:
        return {
            "outcome": self.outcome,
            "qualifying_candidate_ids": list(self.qualifying_candidate_ids),
            "candidate_count": self.candidate_count,
            "all_requirements_decided": self.all_requirements_decided,
            "all_candidates_have_failure": self.all_candidates_have_failure,
            "mr_promotion_authorized": self.mr_promotion_authorized,
        }


def evaluate_candidate_ledger(
    payload: Mapping[str, Any],
    *,
    search_complete: bool,
    integrity_complete: bool,
    candidate_cap: int = 16,
) -> LedgerDecision:
    """Derive the locked outcome from W1-W12 decisions."""

    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("candidate ledger must contain a nonempty candidates list")
    if len(candidates) > candidate_cap:
        raise ValueError("candidate-family cap exceeded")

    seen: set[str] = set()
    qualifying: list[str] = []
    all_decided = True
    all_have_failure = True
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            raise TypeError("each candidate must be an object")
        candidate_id = candidate.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id:
            raise ValueError("candidate_id must be a nonempty string")
        if candidate_id in seen:
            raise ValueError(f"duplicate candidate_id: {candidate_id}")
        seen.add(candidate_id)

        decisions = candidate.get("requirements")
        if not isinstance(decisions, Mapping) or set(decisions) != set(REQUIREMENT_IDS):
            raise ValueError(f"{candidate_id} must decide W1-W12 exactly")
        statuses: list[str] = []
        for requirement_id in REQUIREMENT_IDS:
            decision = decisions[requirement_id]
            if not isinstance(decision, Mapping):
                raise TypeError(f"{candidate_id}/{requirement_id} must be an object")
            status = decision.get("status")
            reason = decision.get("reason")
            if status not in REQUIREMENT_STATUSES:
                raise ValueError(
                    f"{candidate_id}/{requirement_id} has invalid status: {status}"
                )
            if not isinstance(reason, str) or not reason.strip():
                raise ValueError(
                    f"{candidate_id}/{requirement_id} needs an explicit reason"
                )
            statuses.append(status)
        all_decided = all_decided and all(
            status in REQUIREMENT_STATUSES for status in statuses
        )
        candidate_passes = all(status == "PASS" for status in statuses)
        if candidate_passes:
            qualifying.append(candidate_id)
        all_have_failure = all_have_failure and "FAIL" in statuses

    if not search_complete or not integrity_complete or not all_decided:
        outcome = INCOMPLETE
    elif qualifying:
        outcome = QUALIFIED_WITNESS
    elif all_have_failure:
        outcome = COMPLETE_BOUNDED_NULL_RESULT
    else:
        outcome = INCOMPLETE
    return LedgerDecision(
        outcome=outcome,
        qualifying_candidate_ids=tuple(qualifying),
        candidate_count=len(candidates),
        all_requirements_decided=all_decided,
        all_candidates_have_failure=all_have_failure,
    )
