"""Source-disjoint SymPy derivations for WP6-COMMON-v1."""

from __future__ import annotations

from typing import Any

import sympy as sp


def derive_kepler_relation() -> dict[str, Any]:
    """Derive the conic energy relation from ``rho(nu)``."""

    nu = sp.symbols("nu", real=True)
    eccentricity = sp.symbols("e", positive=True)
    angular_momentum = sp.symbols("c", nonzero=True, real=True)
    mu = sp.symbols("mu", positive=True)

    radius = angular_momentum**2 / (mu * (1 + eccentricity * sp.cos(nu)))
    anomaly_rate = angular_momentum / radius**2
    radial_rate = sp.diff(radius, nu) * anomaly_rate
    energy = (
        sp.Rational(1, 2) * (radial_rate**2 + radius**2 * anomaly_rate**2) - mu / radius
    )
    reduced_energy = sp.trigsimp(sp.factor(energy))
    expected = mu**2 * (eccentricity**2 - 1) / (2 * angular_momentum**2)
    residual = sp.trigsimp(sp.factor(reduced_energy - expected))
    return {
        "radius": str(radius),
        "derived_energy": str(reduced_energy),
        "expected_energy": str(expected),
        "residual": str(residual),
        "relation_verified": residual == 0,
    }


def classify_relation(
    energy: str,
    angular_momentum: str,
    mu: str = "1",
) -> dict[str, str | bool]:
    """Independently evaluate the locked algebraic branch invariant."""

    h_value = sp.Rational(energy)
    c_value = sp.Rational(angular_momentum)
    mu_value = sp.Rational(mu)
    if mu_value <= 0:
        raise ValueError("mu must be positive")
    eccentricity_squared = sp.factor(1 + 2 * h_value * c_value**2 / mu_value**2)
    if h_value == 0 and c_value == 0:
        branch = "UNQUALIFIED_DOUBLE_ZERO"
        qualified = False
    elif c_value == 0:
        branch = "ZERO_MOMENTUM_NONZERO_ENERGY"
        qualified = True
    elif sp.factor(2 * h_value * c_value**2 + mu_value**2) == 0:
        branch = "CIRCULAR_RELATION_COMPLEX_WITNESS"
        qualified = True
    else:
        branch = "NONCIRCULAR_NONZERO_MOMENTUM"
        qualified = True
    return {
        "branch": branch,
        "qualified": qualified,
        "eccentricity_squared": str(eccentricity_squared),
    }


def exact_equal_mass_euler_spectrum() -> dict[str, Any]:
    """Construct the Euler matrix from positions, masses, and distances."""

    positions = (sp.Integer(-1), sp.Integer(0), sp.Integer(1))
    masses = (sp.Integer(1),) * 3
    left_force = sum(
        masses[j]
        * (positions[0] - positions[j])
        / abs(positions[0] - positions[j]) ** 3
        for j in (1, 2)
    )
    central_multiplier = sp.factor(left_force / positions[0])

    matrix = sp.zeros(3)
    for row in range(3):
        for column in range(3):
            if row != column:
                distance = abs(positions[row] - positions[column])
                matrix[row, column] = -sp.sqrt(masses[row] * masses[column]) / (
                    central_multiplier * distance**3
                )
        matrix[row, row] = -sum(
            sp.sqrt(masses[column] / masses[row]) * matrix[row, column]
            for column in range(3)
            if column != row
        )

    eigenvalues = sorted(matrix.eigenvals().keys(), key=lambda value: float(value))
    characteristic = sp.factor(matrix.charpoly().as_expr())
    return {
        "central_multiplier_mu": str(central_multiplier),
        "matrix": [
            [str(matrix[row, column]) for column in range(3)] for row in range(3)
        ],
        "spectrum": [str(value) for value in eigenvalues],
        "characteristic_polynomial": str(characteristic),
        "physical_lambda": str(eigenvalues[-1]),
        "physical_delta": str(eigenvalues[-1] - 1),
    }


def generic_discriminant(
    delta: str,
    eccentricity: str,
) -> dict[str, str | bool]:
    d_value = sp.Rational(delta)
    e_value = sp.Rational(eccentricity)
    value = sp.factor(
        4 * e_value**4
        + 4 * e_value**2 * (d_value + 1) * (d_value + 4)
        + (d_value + 1) * (3 * d_value + 4) ** 2 * (9 * d_value + 1)
    )
    return {
        "Delta_squared": str(value),
        "strictly_positive": bool(value > 0),
    }


def circular_discriminant(delta: str) -> dict[str, str | bool]:
    d_value = sp.Rational(delta)
    value = sp.factor(9 * d_value**2 + 10 * d_value + 1)
    return {
        "Delta_squared": str(value),
        "strictly_positive": bool(value > 0),
    }


def generic_nve_coefficients(
    delta: str,
    eccentricity: str,
    discriminant_root: str,
    z: str,
) -> dict[str, str]:
    """Independently evaluate the scalar NVE coefficients in (5.12)."""

    d_value = sp.Rational(delta)
    e_value = sp.Rational(eccentricity)
    root = sp.Rational(discriminant_root)
    z_value = sp.Rational(z)
    linear = sp.factor(
        8 * (2 * d_value + 3) * z_value
        + d_value * (9 * d_value + 17)
        + root
        + 2 * e_value**2
        + 4
    )
    b1 = sp.factor(
        (z_value - 1) / ((z_value - e_value - 1) * (z_value + e_value - 1))
        - 8 * (2 * d_value + 3) / linear
    )
    numerator = sp.factor(
        d_value * (d_value * (9 * d_value + 17) + root + 2 * e_value**2 + 4)
        + 4 * z_value * ((d_value - 3) * d_value + root + 2 * e_value**2 - 8)
        + 16 * (2 * d_value + 3) * z_value**2
    )
    b0 = sp.factor(
        -numerator
        / (z_value * (z_value - e_value - 1) * (z_value + e_value - 1) * linear)
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
