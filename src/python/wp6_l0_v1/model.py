"""Exact spectral chain for planar zero-angular-momentum common levels."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
from typing import TypeAlias


RationalInput: TypeAlias = Fraction | int | float | str


def exact_fraction(value: RationalInput) -> Fraction:
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
        unsigned = stripped.lstrip("+-").lower()
        if unsigned.startswith("0x"):
            parsed = float.fromhex(stripped)
            if not math.isfinite(parsed):
                raise ValueError("hexadecimal input must be finite")
            return Fraction(*parsed.as_integer_ratio())
        return Fraction(stripped)
    raise TypeError(f"unsupported rational input type: {type(value).__name__}")


def allowed_eigenvalue(index: int) -> Fraction:
    """Return the degree-minus-one Morales-Ramis table value."""

    if isinstance(index, bool) or not isinstance(index, int) or index < 0:
        raise ValueError("index must be a non-negative integer")
    return Fraction((index - 1) * (index + 2), 2)


@dataclass(frozen=True)
class SpectralObstruction:
    longitudinal_eigenvalue: Fraction
    transverse_eigenvalue: Fraction
    pacella_premise: bool
    below_allowed_spectrum: bool
    galois_group_sl2: bool

    def as_payload(self) -> dict[str, object]:
        return {
            "longitudinal_eigenvalue": str(self.longitudinal_eigenvalue),
            "transverse_eigenvalue": str(self.transverse_eigenvalue),
            "pacella_strict_bound_lambda_gt_2": self.pacella_premise,
            "allowed_spectrum_minimum": "-1",
            "transverse_below_allowed_spectrum": self.below_allowed_spectrum,
            "scalar_nve_galois_group": (
                "SL(2,C)" if self.galois_group_sl2 else "NOT_CERTIFIED"
            ),
            "identity_component_non_solvable": self.galois_group_sl2,
        }


def spectral_obstruction(
    longitudinal_eigenvalue: RationalInput,
) -> SpectralObstruction:
    """Apply the exact Pacella-to-transverse spectral implication."""

    longitudinal = exact_fraction(longitudinal_eigenvalue)
    transverse = -longitudinal / 2
    premise = longitudinal > 2
    below = premise and transverse < -1
    return SpectralObstruction(
        longitudinal_eigenvalue=longitudinal,
        transverse_eigenvalue=transverse,
        pacella_premise=premise,
        below_allowed_spectrum=below,
        galois_group_sl2=below,
    )


@dataclass(frozen=True)
class CommonLevelCertificate:
    energy: Fraction
    angular_momentum: Fraction
    planar: bool
    positive_masses: bool
    pacella_spectrum_available: bool
    restricted_integrability_obstructed: bool
    reason: str

    def as_payload(self) -> dict[str, object]:
        return {
            "energy": str(self.energy),
            "angular_momentum": str(self.angular_momentum),
            "planar": self.planar,
            "positive_masses": self.positive_masses,
            "pacella_spectrum_available": self.pacella_spectrum_available,
            "restricted_rational_integrability_obstructed": (
                self.restricted_integrability_obstructed
            ),
            "necessary_galois_condition": "solvable identity component",
            "reason": self.reason,
            "one_additional_integral_excluded": False,
            "spatial_claim": False,
            "collision_regularized_claim": False,
        }


def common_level_certificate(
    energy: RationalInput,
    angular_momentum: RationalInput = 0,
    *,
    planar: bool = True,
    positive_masses: bool = True,
    pacella_spectrum_available: bool = True,
) -> CommonLevelCertificate:
    """Qualify only the locked ``(h,0), h!=0`` common-level domain."""

    h_value = exact_fraction(energy)
    c_value = exact_fraction(angular_momentum)
    if not isinstance(planar, bool) or not isinstance(positive_masses, bool):
        raise TypeError("planar and positive_masses must be boolean")
    if not isinstance(pacella_spectrum_available, bool):
        raise TypeError("pacella_spectrum_available must be boolean")

    checks = (
        h_value != 0,
        c_value == 0,
        planar,
        positive_masses,
        pacella_spectrum_available,
    )
    obstructed = all(checks)
    if h_value == 0 and c_value == 0:
        reason = (
            "UNQUALIFIED_DOUBLE_ZERO: the homothetic variational equations "
            "supply no obstruction on (H,C)=(0,0)"
        )
    elif c_value != 0:
        reason = "OUTSIDE_ZERO_MOMENTUM_TRACK"
    elif not planar:
        reason = "SPATIAL_TRANSFER_NOT_QUALIFIED"
    elif not positive_masses:
        reason = "PACELLA_POSITIVE_MASS_PREMISE_MISSING"
    elif not pacella_spectrum_available:
        reason = "PACELLA_SPECTRAL_PREMISE_MISSING"
    else:
        reason = (
            "PACELLA_TRANSVERSE_MODE_HAS_SL2_GALOIS_GROUP; "
            "RESTRICTED_SOLVABILITY_CONDITION_FAILS"
        )
    return CommonLevelCertificate(
        energy=h_value,
        angular_momentum=c_value,
        planar=planar,
        positive_masses=positive_masses,
        pacella_spectrum_available=pacella_spectrum_available,
        restricted_integrability_obstructed=obstructed,
        reason=reason,
    )


def universal_zero_momentum_certificate() -> dict[str, object]:
    """Return the exhaustive published-theorem implication chain."""

    first_values = [allowed_eigenvalue(index) for index in range(8)]
    return {
        "pacella_longitudinal_spectrum": "{0,2,lambda_i}, lambda_i>2",
        "transverse_map": "-lambda_i/2",
        "transverse_strict_bound": "<-1",
        "allowed_spectrum_formula": "(k-1)*(k+2)/2, k in N_0",
        "first_allowed_values": [str(value) for value in first_values],
        "allowed_spectrum_minimum": str(min(first_values)),
        "forbidden_transverse_mode_has_SL2_galois_group": True,
        "SL2_identity_component_is_not_solvable": True,
        "restricted_integrability_requires_solvable_identity_component": True,
        "all_planar_positive_mass_h_nonzero_C_zero_levels_obstructed": True,
        "H_zero_C_zero_obstructed_by_this_witness": False,
        "one_additional_integral_excluded": False,
        "spatial_transfer_claimed": False,
    }
