"""Source-disjoint exact equal-mass Euler spectral benchmark."""

from __future__ import annotations

import sympy as sp


def exact_euler_spectrum() -> dict[str, object]:
    """Construct the normalized longitudinal and transverse Hessian blocks."""

    # For positions (-a,0,a), the multiplier-minus-one normalization is
    # a^3=5/4. Pair Hessian weights are 2/distance^3.
    near_weight = sp.Rational(8, 5)
    far_weight = sp.Rational(1, 5)
    longitudinal = sp.Matrix(
        [
            [near_weight + far_weight, -near_weight, -far_weight],
            [-near_weight, 2 * near_weight, -near_weight],
            [-far_weight, -near_weight, near_weight + far_weight],
        ]
    )
    transverse = -longitudinal / 2
    long_spectrum = sorted(
        (sp.Rational(value) for value in longitudinal.eigenvals()),
        key=float,
    )
    transverse_spectrum = sorted(
        (sp.Rational(value) for value in transverse.eigenvals()),
        key=float,
    )
    return {
        "longitudinal_matrix": [
            [str(value) for value in longitudinal.row(index)]
            for index in range(3)
        ],
        "transverse_matrix": [
            [str(value) for value in transverse.row(index)]
            for index in range(3)
        ],
        "longitudinal_spectrum": [str(value) for value in long_spectrum],
        "transverse_spectrum": [str(value) for value in transverse_spectrum],
        "longitudinal_lambda": "24/5",
        "transverse_lambda": "-12/5",
        "central_direction_eigenvalue": (
            longitudinal * sp.Matrix([-1, 0, 1])
            == 2 * sp.Matrix([-1, 0, 1])
        ),
        "nonclassical_direction_eigenvalue": (
            longitudinal * sp.Matrix([1, -2, 1])
            == sp.Rational(24, 5) * sp.Matrix([1, -2, 1])
        ),
    }


def allowed_spectrum(count: int) -> list[str]:
    if count < 0:
        raise ValueError("count must be non-negative")
    return [
        str(sp.Rational((index - 1) * (index + 2), 2))
        for index in range(count)
    ]
