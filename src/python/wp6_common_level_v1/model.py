"""Exact audit model for the planar common-level nonintegrability theorem."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
from typing import TypeAlias


RationalInput: TypeAlias = Fraction | int | float | str

ZERO_MOMENTUM_NONZERO_ENERGY = "ZERO_MOMENTUM_NONZERO_ENERGY"
NONCIRCULAR_NONZERO_MOMENTUM = "NONCIRCULAR_NONZERO_MOMENTUM"
CIRCULAR_RELATION_COMPLEX_WITNESS = "CIRCULAR_RELATION_COMPLEX_WITNESS"
UNQUALIFIED_DOUBLE_ZERO = "UNQUALIFIED_DOUBLE_ZERO"


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
        unsigned = stripped.lstrip("+-").lower()
        if unsigned.startswith("0x"):
            parsed = float.fromhex(stripped)
            if not math.isfinite(parsed):
                raise ValueError("hexadecimal input must be finite")
            return Fraction(*parsed.as_integer_ratio())
        return Fraction(stripped)
    raise TypeError(f"unsupported rational input type: {type(value).__name__}")


def _positive_fraction(value: RationalInput, name: str) -> Fraction:
    result = exact_fraction(value)
    if result <= 0:
        raise ValueError(f"{name} must be strictly positive")
    return result


@dataclass(frozen=True)
class CommonLevelCertificate:
    """The exact proof branch selected for one ``(H,C)=(h,c)`` level."""

    energy: Fraction
    angular_momentum: Fraction
    kepler_mu: Fraction
    eccentricity_squared: Fraction
    branch: str
    qualified: bool
    witness: str
    direct_common_level_theorem: bool
    requires_wp6_l0_predecessor: bool
    real_circular_orbit_is_obstruction_witness: bool
    reason: str

    @property
    def restricted_rational_integrability_obstructed(self) -> bool:
        return self.qualified

    def as_payload(self) -> dict[str, object]:
        return {
            "energy": str(self.energy),
            "angular_momentum": str(self.angular_momentum),
            "kepler_mu": str(self.kepler_mu),
            "eccentricity_squared": str(self.eccentricity_squared),
            "branch": self.branch,
            "qualified": self.qualified,
            "witness": self.witness,
            "direct_common_level_theorem": self.direct_common_level_theorem,
            "requires_wp6_l0_predecessor": self.requires_wp6_l0_predecessor,
            "real_circular_orbit_is_obstruction_witness": (
                self.real_circular_orbit_is_obstruction_witness
            ),
            "restricted_rational_complete_integrability_obstructed": (
                self.restricted_rational_integrability_obstructed
            ),
            "necessary_galois_condition": "solvable identity component",
            "reason": self.reason,
            "one_additional_integral_excluded": False,
            "spatial_claim": False,
            "non_rational_regularity_claim": False,
            "regular_noncollinear_so3_chart_contains_witness": False,
        }


def classify_common_level(
    energy: RationalInput,
    angular_momentum: RationalInput,
    kepler_mu: RationalInput = 1,
) -> CommonLevelCertificate:
    """Partition a finite real common level into the locked proof branches."""

    h_value = exact_fraction(energy)
    c_value = exact_fraction(angular_momentum)
    mu_value = _positive_fraction(kepler_mu, "kepler_mu")
    eccentricity_squared = 1 + 2 * h_value * c_value**2 / mu_value**2

    if h_value == 0 and c_value == 0:
        return CommonLevelCertificate(
            energy=h_value,
            angular_momentum=c_value,
            kepler_mu=mu_value,
            eccentricity_squared=eccentricity_squared,
            branch=UNQUALIFIED_DOUBLE_ZERO,
            qualified=False,
            witness="NONE",
            direct_common_level_theorem=False,
            requires_wp6_l0_predecessor=False,
            real_circular_orbit_is_obstruction_witness=False,
            reason=(
                "UNQUALIFIED_DOUBLE_ZERO: the pinned theorem expressly "
                "excludes (H,C)=(0,0)"
            ),
        )

    if c_value == 0:
        return CommonLevelCertificate(
            energy=h_value,
            angular_momentum=c_value,
            kepler_mu=mu_value,
            eccentricity_squared=eccentricity_squared,
            branch=ZERO_MOMENTUM_NONZERO_ENERGY,
            qualified=True,
            witness="EULER_MOULTON_HOMOTHETIC",
            direct_common_level_theorem=True,
            requires_wp6_l0_predecessor=True,
            real_circular_orbit_is_obstruction_witness=False,
            reason=(
                "QUALIFIED_BY_WP6_L0: c=0 and h!=0 use the locked "
                "homothetic Euler-Moulton obstruction"
            ),
        )

    circular_relation = 2 * h_value * c_value**2 == -(mu_value**2)
    if circular_relation:
        return CommonLevelCertificate(
            energy=h_value,
            angular_momentum=c_value,
            kepler_mu=mu_value,
            eccentricity_squared=eccentricity_squared,
            branch=CIRCULAR_RELATION_COMPLEX_WITNESS,
            qualified=True,
            witness="EULER_MOULTON_COMPLEX_HOMOGRAPHIC",
            direct_common_level_theorem=True,
            requires_wp6_l0_predecessor=False,
            real_circular_orbit_is_obstruction_witness=False,
            reason=(
                "QUALIFIED_BY_LEMMA_5_3: the real circular orbit has "
                "constant variational coefficients and supplies no "
                "obstruction, so the theorem uses its declared complex "
                "homographic solution"
            ),
        )

    return CommonLevelCertificate(
        energy=h_value,
        angular_momentum=c_value,
        kepler_mu=mu_value,
        eccentricity_squared=eccentricity_squared,
        branch=NONCIRCULAR_NONZERO_MOMENTUM,
        qualified=True,
        witness="EULER_MOULTON_NONCIRCULAR_HOMOGRAPHIC",
        direct_common_level_theorem=True,
        requires_wp6_l0_predecessor=False,
        real_circular_orbit_is_obstruction_witness=False,
        reason=(
            "QUALIFIED_BY_LEMMA_5_1: c!=0 and "
            "2*h*c^2!=-kepler_mu^2 select the noncircular branch"
        ),
    )


def kepler_relation_certificate(
    energy: RationalInput,
    angular_momentum: RationalInput,
    kepler_mu: RationalInput,
    eccentricity_squared: RationalInput | None = None,
) -> dict[str, object]:
    """Check ``2*h*c^2=mu^2*(e^2-1)`` with exact arithmetic."""

    h_value = exact_fraction(energy)
    c_value = exact_fraction(angular_momentum)
    mu_value = _positive_fraction(kepler_mu, "kepler_mu")
    derived = 1 + 2 * h_value * c_value**2 / mu_value**2
    supplied = (
        derived
        if eccentricity_squared is None
        else exact_fraction(eccentricity_squared)
    )
    left = 2 * h_value * c_value**2
    right = mu_value**2 * (supplied - 1)
    return {
        "energy": str(h_value),
        "angular_momentum": str(c_value),
        "kepler_mu": str(mu_value),
        "derived_eccentricity_squared": str(derived),
        "supplied_eccentricity_squared": str(supplied),
        "left_side": str(left),
        "right_side": str(right),
        "relation_holds": left == right,
    }


def equal_mass_euler_matrix() -> tuple[tuple[Fraction, ...], ...]:
    """Return the mass-weighted Euler matrix at positions ``(-1,0,1)``."""

    return (
        (Fraction(9, 10), Fraction(-4, 5), Fraction(-1, 10)),
        (Fraction(-4, 5), Fraction(8, 5), Fraction(-4, 5)),
        (Fraction(-1, 10), Fraction(-4, 5), Fraction(9, 10)),
    )


def _matrix_vector(
    matrix: tuple[tuple[Fraction, ...], ...],
    vector: tuple[Fraction, ...],
) -> tuple[Fraction, ...]:
    return tuple(
        sum((coefficient * value for coefficient, value in zip(row, vector)))
        for row in matrix
    )


def equal_mass_euler_certificate() -> dict[str, object]:
    """Verify the exact equal-mass Euler-Moulton spectrum by eigenvectors."""

    matrix = equal_mass_euler_matrix()
    eigenpairs = (
        (Fraction(0), (Fraction(1), Fraction(1), Fraction(1))),
        (Fraction(1), (Fraction(-1), Fraction(0), Fraction(1))),
        (Fraction(12, 5), (Fraction(1), Fraction(-2), Fraction(1))),
    )
    checks = [
        _matrix_vector(matrix, vector) == tuple(eigenvalue * value for value in vector)
        for eigenvalue, vector in eigenpairs
    ]
    return {
        "positions": ["-1", "0", "1"],
        "central_multiplier_mu": "5/4",
        "matrix": [[str(value) for value in row] for row in matrix],
        "spectrum": [str(pair[0]) for pair in eigenpairs],
        "physical_lambda": "12/5",
        "physical_delta": "7/5",
        "eigenvector_checks": checks,
        "exact_spectrum_verified": all(checks),
    }


def generic_discriminant_squared(
    delta: RationalInput,
    eccentricity: RationalInput,
) -> Fraction:
    """Return the noncircular block discriminant from equation (5.5)."""

    d_value = _positive_fraction(delta, "delta")
    e_value = _positive_fraction(eccentricity, "eccentricity")
    return (
        4 * e_value**4
        + 4 * e_value**2 * (d_value + 1) * (d_value + 4)
        + (d_value + 1) * (3 * d_value + 4) ** 2 * (9 * d_value + 1)
    )


def generic_discriminant_certificate(
    delta: RationalInput,
    eccentricity: RationalInput,
) -> dict[str, object]:
    """Expose the positive summands proving ``Delta^2>0``."""

    d_value = _positive_fraction(delta, "delta")
    e_value = _positive_fraction(eccentricity, "eccentricity")
    terms = (
        4 * e_value**4,
        4 * e_value**2 * (d_value + 1) * (d_value + 4),
        (d_value + 1) * (3 * d_value + 4) ** 2 * (9 * d_value + 1),
    )
    value = sum(terms)
    return {
        "delta": str(d_value),
        "eccentricity": str(e_value),
        "positive_terms": [str(term) for term in terms],
        "all_terms_strictly_positive": all(term > 0 for term in terms),
        "Delta_squared": str(value),
        "strictly_positive": value > 0,
    }


def circular_discriminant_squared(delta: RationalInput) -> Fraction:
    """Return the complex circular-branch discriminant from equation (5.16)."""

    d_value = _positive_fraction(delta, "delta")
    return 9 * d_value**2 + 10 * d_value + 1


def circular_discriminant_certificate(
    delta: RationalInput,
) -> dict[str, object]:
    d_value = _positive_fraction(delta, "delta")
    value = circular_discriminant_squared(d_value)
    return {
        "delta": str(d_value),
        "Delta_squared": str(value),
        "strictly_positive": value > 0,
        "real_circular_orbit_is_obstruction_witness": False,
        "required_witness": "EULER_MOULTON_COMPLEX_HOMOGRAPHIC",
        "source_obstruction": "LEMMA_5_3",
    }


def generic_nve_coefficients(
    delta: RationalInput,
    eccentricity: RationalInput,
    discriminant_root: RationalInput,
    z: RationalInput,
) -> dict[str, str]:
    """Evaluate equation (5.12) on an exact rational sample."""

    d_value = _positive_fraction(delta, "delta")
    e_value = _positive_fraction(eccentricity, "eccentricity")
    root = _positive_fraction(discriminant_root, "discriminant_root")
    z_value = exact_fraction(z)
    if root**2 != generic_discriminant_squared(d_value, e_value):
        raise ValueError("discriminant_root does not square to Delta_squared")

    linear = (
        8 * (2 * d_value + 3) * z_value
        + d_value * (9 * d_value + 17)
        + root
        + 2 * e_value**2
        + 4
    )
    factors = (
        z_value,
        z_value - e_value - 1,
        z_value + e_value - 1,
        linear,
    )
    if any(value == 0 for value in factors):
        raise ValueError("z lies at a pole of the sampled NVE coefficients")

    b1 = (z_value - 1) / ((z_value - e_value - 1) * (z_value + e_value - 1)) - 8 * (
        2 * d_value + 3
    ) / linear
    numerator = (
        d_value * (d_value * (9 * d_value + 17) + root + 2 * e_value**2 + 4)
        + 4 * z_value * ((d_value - 3) * d_value + root + 2 * e_value**2 - 8)
        + 16 * (2 * d_value + 3) * z_value**2
    )
    b0 = -numerator / (
        z_value * (z_value - e_value - 1) * (z_value + e_value - 1) * linear
    )
    return {
        "delta": str(d_value),
        "eccentricity": str(e_value),
        "Delta": str(root),
        "z": str(z_value),
        "l": str(linear),
        "b1": str(b1),
        "b0": str(b0),
    }


def universal_common_level_certificate() -> dict[str, object]:
    """State the exhaustive branch logic and the locked theorem boundary."""

    return {
        "domain": "finite real (h,c), finite positive masses, planar N3BP",
        "source_phase_model": ("center-of-mass algebraic-distance complexification"),
        "known_integrals": ["H", "C"],
        "branch_conditions": {
            ZERO_MOMENTUM_NONZERO_ENERGY: "c=0 and h!=0",
            NONCIRCULAR_NONZERO_MOMENTUM: ("c!=0 and 2*h*c^2!=-kepler_mu^2"),
            CIRCULAR_RELATION_COMPLEX_WITNESS: ("c!=0 and 2*h*c^2=-kepler_mu^2"),
            UNQUALIFIED_DOUBLE_ZERO: "h=0 and c=0",
        },
        "branch_conditions_pairwise_disjoint": True,
        "all_non_double_zero_levels_covered": True,
        "direct_common_level_theorem_not_fi1_transfer": True,
        "restricted_rational_complete_integrability_obstructed": True,
        "double_zero_qualified": False,
        "one_additional_integral_excluded": False,
        "spatial_claim": False,
        "non_rational_regularity_claim": False,
        "pointwise_every_open_domain_claim": False,
        "collinear_witness_in_regular_noncollinear_so3_chart": False,
    }
