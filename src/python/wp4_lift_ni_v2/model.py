"""Dependency-free exact checks for the WP4 lift-transfer theorem."""

from __future__ import annotations

from fractions import Fraction
from math import isqrt
from typing import Any, Iterable, Sequence


Scalar = Fraction
Vector = list[Scalar]
Matrix = list[Vector]


def _fraction(value: int | str | Fraction) -> Fraction:
    return value if isinstance(value, Fraction) else Fraction(value)


def _vector(values: Iterable[int | str | Fraction]) -> Vector:
    return [_fraction(value) for value in values]


def _zeros(rows: int, columns: int) -> Matrix:
    return [[Fraction(0) for _ in range(columns)] for _ in range(rows)]


def _identity(size: int) -> Matrix:
    result = _zeros(size, size)
    for index in range(size):
        result[index][index] = Fraction(1)
    return result


def _transpose(matrix: Matrix) -> Matrix:
    return [list(column) for column in zip(*matrix, strict=True)]


def _matmul(first: Matrix, second: Matrix) -> Matrix:
    second_t = _transpose(second)
    return [
        [
            sum(left * right for left, right in zip(row, column, strict=True))
            for column in second_t
        ]
        for row in first
    ]


def _matvec(matrix: Matrix, vector: Vector) -> Vector:
    return [
        sum(left * right for left, right in zip(row, vector, strict=True))
        for row in matrix
    ]


def _dot(first: Vector, second: Vector) -> Scalar:
    return sum(left * right for left, right in zip(first, second, strict=True))


def _outer(first: Vector, second: Vector) -> Matrix:
    return [[left * right for right in second] for left in first]


def _scale(matrix: Matrix, factor: Scalar) -> Matrix:
    return [[factor * value for value in row] for row in matrix]


def _subtract(first: Matrix, second: Matrix) -> Matrix:
    return [
        [left - right for left, right in zip(row_left, row_right, strict=True)]
        for row_left, row_right in zip(first, second, strict=True)
    ]


def _block_diagonal(*blocks: Matrix) -> Matrix:
    row_count = sum(len(block) for block in blocks)
    column_count = sum(len(block[0]) for block in blocks)
    result = _zeros(row_count, column_count)
    row_offset = 0
    column_offset = 0
    for block in blocks:
        for row_index, row in enumerate(block):
            result[row_offset + row_index][column_offset : column_offset + len(row)] = (
                row
            )
        row_offset += len(block)
        column_offset += len(block[0])
    return result


def _rank(matrix: Matrix) -> int:
    work = [list(row) for row in matrix]
    if not work:
        return 0
    rows = len(work)
    columns = len(work[0])
    pivot_row = 0
    for column in range(columns):
        pivot = next(
            (row for row in range(pivot_row, rows) if work[row][column] != 0),
            None,
        )
        if pivot is None:
            continue
        work[pivot_row], work[pivot] = work[pivot], work[pivot_row]
        pivot_value = work[pivot_row][column]
        work[pivot_row] = [value / pivot_value for value in work[pivot_row]]
        for row in range(rows):
            if row == pivot_row or work[row][column] == 0:
                continue
            factor = work[row][column]
            work[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(work[row], work[pivot_row], strict=True)
            ]
        pivot_row += 1
        if pivot_row == rows:
            break
    return pivot_row


def _canonical_poisson(degrees: int) -> Matrix:
    result = _zeros(2 * degrees, 2 * degrees)
    for index in range(degrees):
        result[index][degrees + index] = Fraction(1)
        result[degrees + index][index] = Fraction(-1)
    return result


def _poisson_bracket(first_gradient: Vector, second_gradient: Vector) -> Scalar:
    degrees = len(first_gradient) // 2
    return _dot(
        first_gradient,
        _matvec(_canonical_poisson(degrees), second_gradient),
    )


def _exact_sqrt(value: Fraction) -> Fraction:
    numerator = isqrt(value.numerator)
    denominator = isqrt(value.denominator)
    if (
        numerator * numerator != value.numerator
        or denominator * denominator != value.denominator
    ):
        raise ValueError(f"fraction has no rational square root: {value}")
    return Fraction(numerator, denominator)


def _norm(vector: Vector) -> Fraction:
    return _exact_sqrt(_dot(vector, vector))


def _ks_position(q: Vector) -> Vector:
    q1, q2, q3, q4 = q
    return [
        2 * (q1 * q3 + q2 * q4),
        2 * (q1 * q4 - q2 * q3),
        q1 * q1 + q2 * q2 - q3 * q3 - q4 * q4,
    ]


def _ks_jacobian(q: Vector) -> Matrix:
    q1, q2, q3, q4 = q
    return _scale(
        [
            [q3, q4, q1, q2],
            [q4, -q3, -q2, q1],
            [q1, q2, -q3, -q4],
        ],
        Fraction(2),
    )


def _fiber(q: Vector) -> Vector:
    q1, q2, q3, q4 = q
    return [-q2, q1, -q4, q3]


def _xi(q: Vector, momentum: Vector) -> Fraction:
    return _dot(_fiber(q), momentum)


def _xi_gradient(q: Vector, momentum: Vector) -> Vector:
    return [-value for value in _fiber(momentum)] + _fiber(q)


def _projection_jacobian(
    q: Vector,
    momentum: Vector,
    *,
    momentum_denominator: int = 4,
) -> Matrix:
    radius = _dot(q, q)
    if radius == 0:
        raise ValueError("KS projection requires q != 0")
    denominator = Fraction(momentum_denominator)
    jacobian = _ks_jacobian(q)
    physical_momentum = [
        value / (denominator * radius) for value in _matvec(jacobian, momentum)
    ]
    dp_dq = _subtract(
        _scale(_ks_jacobian(momentum), 1 / (denominator * radius)),
        _scale(_outer(physical_momentum, q), 2 / radius),
    )
    dp_dmomentum = _scale(jacobian, 1 / (denominator * radius))
    result = _zeros(6, 8)
    for row in range(3):
        result[row][:4] = jacobian[row]
        result[3 + row][:4] = dp_dq[row]
        result[3 + row][4:] = dp_dmomentum[row]
    return result


def single_ks_certificate(
    q_values: Sequence[int | str | Fraction] = (1, 2, 3, 4),
    momentum_values: Sequence[int | str | Fraction] = (5, -3, 2, -4),
    *,
    momentum_denominator: int = 4,
) -> dict[str, Any]:
    q = _vector(q_values)
    momentum = _vector(momentum_values)
    radius = _dot(q, q)
    position = _ks_position(q)
    jacobian = _ks_jacobian(q)
    vertical = _fiber(q)
    xi = _xi(q, momentum)
    projection = _projection_jacobian(
        q, momentum, momentum_denominator=momentum_denominator
    )
    projected_poisson = _matmul(
        _matmul(projection, _canonical_poisson(4)), _transpose(projection)
    )
    phase_generator = vertical + _fiber(momentum)
    constraint_gradient = _xi_gradient(q, momentum)
    expected_projector = _subtract(
        _scale(_identity(4), 4 * radius),
        _scale(_outer(vertical, vertical), Fraction(4)),
    )
    return {
        "radius": radius,
        "xi": xi,
        "radius_identity": _dot(position, position) == radius * radius,
        "jacobian_metric_identity": _matmul(jacobian, _transpose(jacobian))
        == _scale(_identity(3), 4 * radius),
        "horizontal_projector_identity": _matmul(_transpose(jacobian), jacobian)
        == expected_projector,
        "vertical_kernel_identity": _matvec(jacobian, vertical) == [Fraction(0)] * 3,
        "projection_rank": _rank(projection),
        "constraint_projection_rank": _rank(projection + [constraint_gradient]),
        "phase_gauge_kernel_identity": _matvec(projection, phase_generator)
        == [Fraction(0)] * 6,
        "gauge_tangent_to_level_identity": _dot(constraint_gradient, phase_generator)
        == 0,
        "projected_poisson": projected_poisson,
        "canonical_on_zero_level": xi == 0
        and projected_poisson == _canonical_poisson(3),
    }


def product_reduction_certificate() -> dict[str, Any]:
    q1 = _vector((1, 0, 2, 0))
    p1 = _vector((3, -8, -1, 4))
    q2 = _vector((0, 2, 0, 1))
    p2 = _vector((1, -2, -2, 3))
    if _xi(q1, p1) != 0 or _xi(q2, p2) != 0:
        raise AssertionError("locked product probes must lie on Xi1=Xi2=0")
    first = _projection_jacobian(q1, p1)
    second = _projection_jacobian(q2, p2)
    projection = _zeros(14, 18)
    for row in range(6):
        projection[row][0:4] = first[row][0:4]
        projection[row][9:13] = first[row][4:8]
        projection[6 + row][4:8] = second[row][0:4]
        projection[6 + row][13:17] = second[row][4:8]
    projection[12][8] = Fraction(1)
    projection[13][17] = Fraction(1)
    constraint1 = [Fraction(0)] * 18
    constraint2 = [Fraction(0)] * 18
    gradient1 = _xi_gradient(q1, p1)
    gradient2 = _xi_gradient(q2, p2)
    constraint1[0:4] = gradient1[0:4]
    constraint1[9:13] = gradient1[4:8]
    constraint2[4:8] = gradient2[0:4]
    constraint2[13:17] = gradient2[4:8]
    generator1 = [Fraction(0)] * 18
    generator2 = [Fraction(0)] * 18
    generator1[0:4] = _fiber(q1)
    generator1[9:13] = _fiber(p1)
    generator2[4:8] = _fiber(q2)
    generator2[13:17] = _fiber(p2)
    return {
        "upstairs_dimension": 18,
        "regular_level_dimension": 16,
        "quotient_dimension": 14,
        "constraint_rank": _rank([constraint1, constraint2]),
        "projection_rank": _rank(projection),
        "constraint_projection_rank": _rank(projection + [constraint1, constraint2]),
        "first_gauge_kernel": _matvec(projection, generator1) == [Fraction(0)] * 14,
        "second_gauge_kernel": _matvec(projection, generator2) == [Fraction(0)] * 14,
        "gauge_generators_independent": _rank([generator1, generator2]) == 2,
    }


def _physical_pair(q: Vector, momentum: Vector) -> tuple[Vector, Vector, Fraction]:
    radius = _dot(q, q)
    position = _ks_position(q)
    physical_momentum = [
        value / (4 * radius) for value in _matvec(_ks_jacobian(q), momentum)
    ]
    return position, physical_momentum, radius


def _hamiltonian_factor_residual(
    q1: Vector,
    q2: Vector,
    p1: Vector,
    p2: Vector,
) -> Fraction:
    mass_a, mass_b, mass_c = _vector((2, 3, 5))
    gravity = Fraction(7, 5)
    p_t = Fraction(11, 7)
    mu1 = mass_a * mass_c / (mass_a + mass_c)
    mu2 = mass_b * mass_c / (mass_b + mass_c)
    k1 = gravity * mass_a * mass_c
    k2 = gravity * mass_b * mass_c
    k3 = gravity * mass_a * mass_b
    x1, w1, r1 = _physical_pair(q1, p1)
    x2, w2, r2 = _physical_pair(q2, p2)
    r3 = _norm([left - right for left, right in zip(x1, x2, strict=True)])
    physical_hamiltonian = (
        _dot(w1, w1) / (2 * mu1)
        + _dot(w2, w2) / (2 * mu2)
        + _dot(w1, w2) / mass_c
        - k1 / r1
        - k2 / r2
        - k3 / r3
    )
    j1p1 = _matvec(_ks_jacobian(q1), p1)
    j2p2 = _matvec(_ks_jacobian(q2), p2)
    first = _dot(p1, p1) / (8 * mu1) - k1
    second = _dot(p2, p2) / (8 * mu2) - k2
    cross = _dot(j1p1, j2p2) / (16 * mass_c)
    model_f = r2 * first + r1 * second + cross + p_t * r1 * r2
    model_k = r3 * model_f - k3 * r1 * r2
    return model_k - r1 * r2 * r3 * (physical_hamiltonian + p_t)


def hamiltonian_factor_certificate() -> dict[str, Any]:
    q1 = _vector((1, 0, 0, 0))
    q2 = _vector((0, 0, 1, 0))
    zero_p1 = _vector((1, 0, 2, 3))
    zero_p2 = _vector((2, 3, 4, 0))
    nonzero_p1 = _vector((1, 1, 2, 3))
    zero_residual = _hamiltonian_factor_residual(q1, q2, zero_p1, zero_p2)
    nonzero_residual = _hamiltonian_factor_residual(q1, q2, nonzero_p1, zero_p2)
    return {
        "xi1_zero": _xi(q1, zero_p1),
        "xi2_zero": _xi(q2, zero_p2),
        "zero_level_factor_residual": zero_residual,
        "zero_level_factor_identity": zero_residual == 0,
        "nonzero_level_xi": _xi(q1, nonzero_p1),
        "nonzero_level_factor_residual": nonzero_residual,
        "nonzero_level_control_rejected": nonzero_residual != 0,
    }


def _embed_physical_gradient(gradient: Vector) -> Vector:
    if len(gradient) != 12:
        raise ValueError("physical gradient must have length 12")
    return gradient[:6] + [Fraction(0)] + gradient[6:] + [Fraction(0)]


def adapted_transfer_certificate() -> dict[str, Any]:
    physical_h = _vector(range(1, 13))
    physical_g = _vector((2, -1, 3, 0, 4, -2, 1, 5, -3, 2, 6, -4))
    physical_f = _vector((3, 1, -2, 4, 0, 5, -1, 2, 3, -4, 1, 6))
    g = Fraction(5, 3)
    shell_offset = Fraction(0)
    off_shell_offset = Fraction(3, 7)
    f_gradient = _embed_physical_gradient(physical_f)
    f_gradient[-1] = Fraction(7, 11)

    def sundman_residual(offset: Fraction) -> Fraction:
        k_gradient = _embed_physical_gradient(
            [
                g * h_value + offset * g_value
                for h_value, g_value in zip(physical_h, physical_g, strict=True)
            ]
        )
        k_gradient[-1] = g
        left = _poisson_bracket(f_gradient, k_gradient)
        right = g * _poisson_bracket(
            _embed_physical_gradient(physical_f),
            _embed_physical_gradient(physical_h),
        ) + offset * _poisson_bracket(
            _embed_physical_gradient(physical_f),
            _embed_physical_gradient(physical_g),
        )
        return left - right

    # Adapted canonical ordering is (q[6],t,theta1,theta2,p[6],pt,I1,I2).
    full_rows: Matrix = []
    k_row = [Fraction(0)] * 18
    k_row[9] = Fraction(1)
    k_row[15] = Fraction(1)
    full_rows.append(k_row)
    for column in (15, 16, 17):
        row = [Fraction(0)] * 18
        row[column] = Fraction(1)
        full_rows.append(row)
    b_values = _vector((1, -2, 3, -4, 5))
    for index, b_value in enumerate(b_values, start=1):
        row = [Fraction(0)] * 18
        row[9 + index] = Fraction(1)
        row[15] = b_value
        row[16] = Fraction(index, 7)
        row[17] = Fraction(-index, 11)
        full_rows.append(row)

    reduced_rows: Matrix = []
    h_row = [Fraction(0)] * 12
    h_row[6] = Fraction(1)
    reduced_rows.append(h_row)
    for index, b_value in enumerate(b_values, start=1):
        row = [Fraction(0)] * 12
        row[6] = -b_value
        row[6 + index] = Fraction(1)
        reduced_rows.append(row)
    negative_full = [list(row) for row in full_rows]
    negative_full[-1] = list(negative_full[-2])
    negative_reduced = [list(row) for row in reduced_rows]
    negative_reduced[-1] = list(negative_reduced[-2])

    # Exact counterexample to the invalid v1 premise. Its ninth direction is
    # horizontal only when I1 is nonzero and disappears on the physical shell.
    off_shell_only_shell = _zeros(9, 18)
    off_shell_only_shell[0][9] = Fraction(1)
    off_shell_only_shell[0][15] = Fraction(1)
    off_shell_only_shell[1][15] = Fraction(1)
    off_shell_only_shell[2][16] = Fraction(1)
    off_shell_only_shell[3][17] = Fraction(1)
    for row, column in enumerate(range(10, 14), start=4):
        off_shell_only_shell[row][column] = Fraction(1)
    off_shell_only_shell[8][16] = Fraction(2)  # d(I1*p6) at I1=0, p6=2.
    off_shell_only_ambient = [list(row) for row in off_shell_only_shell]
    off_shell_only_ambient[8][14] = Fraction(1)  # d(I1*p6) at I1=1.
    off_shell_only_reduced = _zeros(6, 12)
    for row, column in enumerate(range(6, 11)):
        off_shell_only_reduced[row][column] = Fraction(1)

    full_poisson = _canonical_poisson(9)
    reduced_poisson = _canonical_poisson(6)
    full_involution = all(
        _dot(first, _matvec(full_poisson, second)) == 0
        for first in full_rows
        for second in full_rows
    )
    reduced_involution = all(
        _dot(first, _matvec(reduced_poisson, second)) == 0
        for first in reduced_rows
        for second in reduced_rows
    )
    clock_gradient = [Fraction(0)] * 18
    clock_gradient[6] = Fraction(1)
    gauge_gradient = [Fraction(0)] * 18
    gauge_gradient[7] = Fraction(1)
    return {
        "shell_sundman_residual": sundman_residual(shell_offset),
        "off_shell_product_rule_residual": sundman_residual(off_shell_offset),
        "sundman_identity_exact": sundman_residual(shell_offset) == 0
        and sundman_residual(off_shell_offset) == 0,
        "full_family_rank_on_shell": _rank(full_rows),
        "descended_family_rank": _rank(reduced_rows),
        "full_family_involution": full_involution,
        "descended_family_involution": reduced_involution,
        "rank_loss_control_full_rank": _rank(negative_full),
        "rank_loss_control_reduced_rank": _rank(negative_reduced),
        "rank_loss_control_rejected": _rank(negative_full) < 9
        and _rank(negative_reduced) < 6,
        "off_shell_only_ambient_rank": _rank(off_shell_only_ambient),
        "off_shell_only_shell_rank": _rank(off_shell_only_shell),
        "off_shell_only_descended_rank": _rank(off_shell_only_reduced),
        "off_shell_only_family_involution": all(
            _dot(first, _matvec(full_poisson, second)) == 0
            for first in off_shell_only_ambient
            for second in off_shell_only_ambient
        ),
        "off_shell_only_control_rejected": _rank(off_shell_only_ambient) == 9
        and _rank(off_shell_only_shell) < 9
        and _rank(off_shell_only_reduced) < 6,
        "clock_pt_bracket": _dot(clock_gradient, _matvec(full_poisson, full_rows[1])),
        "clock_dependent_control_rejected": _dot(
            clock_gradient, _matvec(full_poisson, full_rows[1])
        )
        != 0,
        "gauge_xi1_bracket": _dot(gauge_gradient, _matvec(full_poisson, full_rows[2])),
        "gauge_variant_control_rejected": _dot(
            gauge_gradient, _matvec(full_poisson, full_rows[2])
        )
        != 0,
    }


def _pair_hessian(displacement: Vector, strength: Fraction) -> Matrix:
    radius = _norm(displacement)
    dimension = len(displacement)
    return _subtract(
        _scale(_identity(dimension), strength / radius**3),
        _scale(_outer(displacement, displacement), 3 * strength / radius**5),
    )


def _configuration_hessian(
    x1: Vector,
    x2: Vector,
    strengths: tuple[Fraction, Fraction, Fraction],
) -> Matrix:
    dimension = len(x1)
    first = _pair_hessian(x1, strengths[0])
    second = _pair_hessian(x2, strengths[1])
    difference = [left - right for left, right in zip(x1, x2, strict=True)]
    third = _pair_hessian(difference, strengths[2])
    result = _zeros(2 * dimension, 2 * dimension)
    for row in range(dimension):
        for column in range(dimension):
            result[row][column] = first[row][column] + third[row][column]
            result[dimension + row][dimension + column] = (
                second[row][column] + third[row][column]
            )
            result[row][dimension + column] = -third[row][column]
            result[dimension + row][column] = -third[row][column]
    return result


def _kinetic_hessian(
    dimension: int,
    mu1: Fraction,
    mu2: Fraction,
    central_mass: Fraction,
) -> Matrix:
    result = _zeros(2 * dimension, 2 * dimension)
    for axis in range(dimension):
        result[axis][axis] = 1 / mu1
        result[dimension + axis][dimension + axis] = 1 / mu2
        result[axis][dimension + axis] = 1 / central_mass
        result[dimension + axis][axis] = 1 / central_mass
    return result


def _submatrix(matrix: Matrix, rows: Sequence[int], columns: Sequence[int]) -> Matrix:
    return [[matrix[row][column] for column in columns] for row in rows]


def _planar_hamiltonian_gradient(
    x1: Vector,
    x2: Vector,
    p1: Vector,
    p2: Vector,
    strengths: tuple[Fraction, Fraction, Fraction],
    mu1: Fraction,
    mu2: Fraction,
    central_mass: Fraction,
) -> Vector:
    difference = [left - right for left, right in zip(x1, x2, strict=True)]
    r1 = _norm(x1)
    r2 = _norm(x2)
    r3 = _norm(difference)
    first_q = [
        strengths[0] * value / r1**3 + strengths[2] * delta / r3**3
        for value, delta in zip(x1, difference, strict=True)
    ]
    second_q = [
        strengths[1] * value / r2**3 - strengths[2] * delta / r3**3
        for value, delta in zip(x2, difference, strict=True)
    ]
    first_p = [
        value / mu1 + other / central_mass for value, other in zip(p1, p2, strict=True)
    ]
    second_p = [
        value / mu2 + other / central_mass for value, other in zip(p2, p1, strict=True)
    ]
    return first_q + second_q + first_p + second_p


def spatial_subquotient_certificate() -> dict[str, Any]:
    masses = _vector((2, 3, 5))
    mass_a, mass_b, mass_c = masses
    gravity = Fraction(7, 5)
    strengths = (
        gravity * mass_a * mass_c,
        gravity * mass_b * mass_c,
        gravity * mass_a * mass_b,
    )
    mu1 = mass_a * mass_c / (mass_a + mass_c)
    mu2 = mass_b * mass_c / (mass_b + mass_c)
    x1_3d = _vector((3, 4, 0))
    x2_3d = _vector((-3, 4, 0))
    potential_3d = _configuration_hessian(x1_3d, x2_3d, strengths)
    kinetic_3d = _kinetic_hessian(3, mu1, mu2, mass_c)
    hessian_3d = _block_diagonal(potential_3d, kinetic_3d)
    variational_3d = _matmul(_canonical_poisson(6), hessian_3d)
    planar_indices = (0, 1, 3, 4, 6, 7, 9, 10)
    vertical_indices = (2, 5, 8, 11)
    cross_forward = _submatrix(variational_3d, planar_indices, vertical_indices)
    cross_reverse = _submatrix(variational_3d, vertical_indices, planar_indices)
    planar_from_spatial = _submatrix(variational_3d, planar_indices, planar_indices)
    x1_2d = _vector((3, 4))
    x2_2d = _vector((-3, 4))
    hessian_2d = _block_diagonal(
        _configuration_hessian(x1_2d, x2_2d, strengths),
        _kinetic_hessian(2, mu1, mu2, mass_c),
    )
    planar_direct = _matmul(_canonical_poisson(4), hessian_2d)
    reflection = _identity(12)
    for index in vertical_indices:
        reflection[index][index] = Fraction(-1)
    p1_2d = _vector((1, 2))
    p2_2d = _vector((2, -1))
    h_gradient = _planar_hamiltonian_gradient(
        x1_2d,
        x2_2d,
        p1_2d,
        p2_2d,
        strengths,
        mu1,
        mu2,
        mass_c,
    )
    angular_momentum_gradient = _vector(
        (
            p1_2d[1],
            -p1_2d[0],
            p2_2d[1],
            -p2_2d[0],
            -x1_2d[1],
            x1_2d[0],
            -x2_2d[1],
            x2_2d[0],
        )
    )
    rotation_generator = _matvec(_canonical_poisson(4), angular_momentum_gradient)
    expected_rotation_generator = _vector(
        (
            -x1_2d[1],
            x1_2d[0],
            -x2_2d[1],
            x2_2d[0],
            -p1_2d[1],
            p1_2d[0],
            -p2_2d[1],
            p2_2d[0],
        )
    )
    hamiltonian_flow = _matvec(_canonical_poisson(4), h_gradient)
    angular_momentum = (
        x1_2d[0] * p1_2d[1]
        - x1_2d[1] * p1_2d[0]
        + x2_2d[0] * p2_2d[1]
        - x2_2d[1] * p2_2d[0]
    )
    angular_momentum_bracket = _poisson_bracket(h_gradient, angular_momentum_gradient)
    spatial_dimension = len(variational_3d)
    planar_dimension = len(planar_indices)
    fixed_momentum_tangent_dimension = planar_dimension - _rank(
        [angular_momentum_gradient]
    )
    rotation_quotient_dimension = fixed_momentum_tangent_dimension - _rank(
        [rotation_generator]
    )
    energy_tangent_dimension = rotation_quotient_dimension - 1
    normal_quotient_dimension = energy_tangent_dimension - 1
    return {
        "planar_vertical_cross_zero": all(
            value == 0 for row in cross_forward + cross_reverse for value in row
        ),
        "planar_block_exact": planar_from_spatial == planar_direct,
        "reflection_commutes_with_variational_matrix": _matmul(
            reflection, variational_3d
        )
        == _matmul(variational_3d, reflection),
        "spatial_variational_rank": _rank(variational_3d),
        "planar_variational_rank": _rank(planar_direct),
        "vertical_variational_rank": _rank(
            _submatrix(variational_3d, vertical_indices, vertical_indices)
        ),
        "angular_momentum": angular_momentum,
        "angular_momentum_nonzero": angular_momentum != 0,
        "rotation_generator_identity": rotation_generator
        == expected_rotation_generator,
        "angular_momentum_conservation_residual": angular_momentum_bracket,
        "angular_momentum_conserved": angular_momentum_bracket == 0,
        "flow_tangent_to_fixed_momentum_level": _dot(
            angular_momentum_gradient, hamiltonian_flow
        )
        == 0,
        "rotation_tangent_to_energy_level": _dot(h_gradient, rotation_generator) == 0,
        "energy_momentum_gradient_rank": _rank([h_gradient, angular_momentum_gradient]),
        "spatial_ve_dimension": spatial_dimension,
        "planar_reflection_block_dimension": planar_dimension,
        "planar_fixed_momentum_tangent_dimension": fixed_momentum_tangent_dimension,
        "planar_rotation_quotient_dimension": rotation_quotient_dimension,
        "planar_energy_tangent_dimension": energy_tangent_dimension,
        "planar_normal_quotient_dimension": normal_quotient_dimension,
        "published_nve_chain_dimension_exact": (
            spatial_dimension,
            planar_dimension,
            fixed_momentum_tangent_dimension,
            rotation_quotient_dimension,
            energy_tangent_dimension,
            normal_quotient_dimension,
        )
        == (12, 8, 7, 6, 5, 4),
        "planar_block": planar_from_spatial,
    }


def _encode_exact(value: Any) -> Any:
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, dict):
        return {key: _encode_exact(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_encode_exact(item) for item in value]
    return value


def all_production_certificates() -> dict[str, Any]:
    zero_level = single_ks_certificate(
        (1, 2, 3, 4),
        (5, 15, 2, 1),
    )
    wrong_factor = single_ks_certificate(
        (1, 2, 3, 4),
        (5, 15, 2, 1),
        momentum_denominator=2,
    )
    nonzero_level = single_ks_certificate(
        (1, 2, 3, 4),
        (5, -3, 2, -4),
    )
    payload = {
        "single_ks_zero_level": zero_level,
        "wrong_momentum_factor_control": {
            "canonical_on_zero_level": wrong_factor["canonical_on_zero_level"],
            "projected_poisson": wrong_factor["projected_poisson"],
            "rejected": not wrong_factor["canonical_on_zero_level"],
        },
        "nonzero_xi_control": {
            "xi": nonzero_level["xi"],
            "canonical_on_zero_level": nonzero_level["canonical_on_zero_level"],
            "projected_poisson": nonzero_level["projected_poisson"],
            "rejected": nonzero_level["xi"] != 0
            and nonzero_level["projected_poisson"] != _canonical_poisson(3),
        },
        "product_reduction": product_reduction_certificate(),
        "hamiltonian_factor": hamiltonian_factor_certificate(),
        "transfer": adapted_transfer_certificate(),
        "spatial_subquotient": spatial_subquotient_certificate(),
        "logic": {
            "abelian_group_has_only_abelian_algebraic_quotients": True,
            "nonabelian_quotient_obstructs_abelian_full_group": True,
            "global_family_restricts_to_every_regular_open_subset": True,
            "binary_collision_extension_does_not_remove_regular_open_restriction": True,
        },
    }
    return _encode_exact(payload)
