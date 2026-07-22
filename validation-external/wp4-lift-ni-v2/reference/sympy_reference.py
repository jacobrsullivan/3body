"""Source-disjoint symbolic reference for WP4-LIFT-NI-v2."""

from __future__ import annotations

from typing import Any, Sequence

import sympy as sp


def _canonical_poisson(degrees: int) -> sp.Matrix:
    zero = sp.zeros(degrees)
    identity = sp.eye(degrees)
    return zero.row_join(identity).col_join((-identity).row_join(zero))


def _ks_definitions(momentum_denominator: int = 4) -> dict[str, Any]:
    q = sp.symbols("q1:5")
    momentum = sp.symbols("P1:5")
    q_vector = sp.Matrix(q)
    p_vector = sp.Matrix(momentum)
    q1, q2, q3, q4 = q
    position = sp.Matrix(
        [
            2 * (q1 * q3 + q2 * q4),
            2 * (q1 * q4 - q2 * q3),
            q1**2 + q2**2 - q3**2 - q4**2,
        ]
    )
    radius = sp.expand(q_vector.dot(q_vector))
    jacobian = position.jacobian(q)
    fiber = sp.Matrix([-q2, q1, -q4, q3])
    xi = sp.expand(fiber.dot(p_vector))
    physical_momentum = jacobian * p_vector / (momentum_denominator * radius)
    projection = position.col_join(physical_momentum).jacobian(q + momentum)
    projected_poisson = sp.simplify(projection * _canonical_poisson(4) * projection.T)
    xi_gradient = sp.Matrix([xi]).jacobian(q + momentum)
    phase_generator = fiber.col_join(
        sp.Matrix([-momentum[1], momentum[0], -momentum[3], momentum[2]])
    )
    return {
        "q": q,
        "momentum": momentum,
        "position": position,
        "radius": radius,
        "jacobian": jacobian,
        "fiber": fiber,
        "xi": xi,
        "projection": projection,
        "projected_poisson": projected_poisson,
        "xi_gradient": xi_gradient,
        "phase_generator": phase_generator,
    }


def _substitutions(
    definitions: dict[str, Any],
    q_values: Sequence[int],
    momentum_values: Sequence[int],
) -> dict[sp.Symbol, sp.Integer]:
    return {
        **dict(zip(definitions["q"], map(sp.Integer, q_values), strict=True)),
        **dict(
            zip(
                definitions["momentum"],
                map(sp.Integer, momentum_values),
                strict=True,
            )
        ),
    }


def _matrix_values(matrix: sp.Matrix, substitutions: dict[sp.Symbol, Any]) -> sp.Matrix:
    return matrix.subs(substitutions).applyfunc(sp.cancel)


def _single_ks(
    q_values: Sequence[int],
    momentum_values: Sequence[int],
    *,
    momentum_denominator: int = 4,
) -> dict[str, Any]:
    definitions = _ks_definitions(momentum_denominator)
    substitutions = _substitutions(definitions, q_values, momentum_values)
    radius = sp.cancel(definitions["radius"].subs(substitutions))
    position = _matrix_values(definitions["position"], substitutions)
    jacobian = _matrix_values(definitions["jacobian"], substitutions)
    fiber = _matrix_values(definitions["fiber"], substitutions)
    xi = sp.cancel(definitions["xi"].subs(substitutions))
    projection = _matrix_values(definitions["projection"], substitutions)
    projected_poisson = _matrix_values(definitions["projected_poisson"], substitutions)
    xi_gradient = _matrix_values(definitions["xi_gradient"], substitutions)
    phase_generator = _matrix_values(definitions["phase_generator"], substitutions)
    expected_projector = 4 * radius * sp.eye(4) - 4 * fiber * fiber.T
    return {
        "radius": radius,
        "xi": xi,
        "radius_identity": sp.expand(position.dot(position) - radius**2) == 0,
        "jacobian_metric_identity": jacobian * jacobian.T == 4 * radius * sp.eye(3),
        "horizontal_projector_identity": jacobian.T * jacobian == expected_projector,
        "vertical_kernel_identity": jacobian * fiber == sp.zeros(3, 1),
        "projection_rank": projection.rank(),
        "constraint_projection_rank": projection.col_join(xi_gradient).rank(),
        "phase_gauge_kernel_identity": projection * phase_generator == sp.zeros(6, 1),
        "gauge_tangent_to_level_identity": (xi_gradient * phase_generator)[0] == 0,
        "projected_poisson": projected_poisson,
        "canonical_on_zero_level": xi == 0
        and projected_poisson == _canonical_poisson(3),
    }


def _product_reduction() -> dict[str, Any]:
    first_definitions = _ks_definitions()
    second_definitions = _ks_definitions()
    first_substitutions = _substitutions(
        first_definitions, (1, 0, 2, 0), (3, -8, -1, 4)
    )
    second_substitutions = _substitutions(
        second_definitions, (0, 2, 0, 1), (1, -2, -2, 3)
    )
    first = _matrix_values(first_definitions["projection"], first_substitutions)
    second = _matrix_values(second_definitions["projection"], second_substitutions)
    projection = sp.zeros(14, 18)
    projection[:6, :4] = first[:, :4]
    projection[:6, 9:13] = first[:, 4:]
    projection[6:12, 4:8] = second[:, :4]
    projection[6:12, 13:17] = second[:, 4:]
    projection[12, 8] = 1
    projection[13, 17] = 1
    constraint1 = sp.zeros(1, 18)
    constraint2 = sp.zeros(1, 18)
    first_gradient = _matrix_values(
        first_definitions["xi_gradient"], first_substitutions
    )
    second_gradient = _matrix_values(
        second_definitions["xi_gradient"], second_substitutions
    )
    constraint1[:, :4] = first_gradient[:, :4]
    constraint1[:, 9:13] = first_gradient[:, 4:]
    constraint2[:, 4:8] = second_gradient[:, :4]
    constraint2[:, 13:17] = second_gradient[:, 4:]
    generator1 = sp.zeros(18, 1)
    generator2 = sp.zeros(18, 1)
    first_generator = _matrix_values(
        first_definitions["phase_generator"], first_substitutions
    )
    second_generator = _matrix_values(
        second_definitions["phase_generator"], second_substitutions
    )
    generator1[:4, :] = first_generator[:4, :]
    generator1[9:13, :] = first_generator[4:, :]
    generator2[4:8, :] = second_generator[:4, :]
    generator2[13:17, :] = second_generator[4:, :]
    constraints = constraint1.col_join(constraint2)
    return {
        "upstairs_dimension": 18,
        "regular_level_dimension": 16,
        "quotient_dimension": 14,
        "constraint_rank": constraints.rank(),
        "projection_rank": projection.rank(),
        "constraint_projection_rank": projection.col_join(constraints).rank(),
        "first_gauge_kernel": projection * generator1 == sp.zeros(14, 1),
        "second_gauge_kernel": projection * generator2 == sp.zeros(14, 1),
        "gauge_generators_independent": generator1.row_join(generator2).rank() == 2,
    }


def _hamiltonian_factor_residual(
    first_momentum: Sequence[int],
) -> sp.Expr:
    definitions1 = _ks_definitions()
    definitions2 = _ks_definitions()
    substitutions1 = _substitutions(definitions1, (1, 0, 0, 0), first_momentum)
    substitutions2 = _substitutions(definitions2, (0, 0, 1, 0), (2, 3, 4, 0))
    x1 = _matrix_values(definitions1["position"], substitutions1)
    x2 = _matrix_values(definitions2["position"], substitutions2)
    r1 = sp.cancel(definitions1["radius"].subs(substitutions1))
    r2 = sp.cancel(definitions2["radius"].subs(substitutions2))
    r3 = sp.sqrt((x1 - x2).dot(x1 - x2))
    j1 = _matrix_values(definitions1["jacobian"], substitutions1)
    j2 = _matrix_values(definitions2["jacobian"], substitutions2)
    p1 = sp.Matrix(first_momentum)
    p2 = sp.Matrix((2, 3, 4, 0))
    w1 = j1 * p1 / (4 * r1)
    w2 = j2 * p2 / (4 * r2)
    mass_a, mass_b, mass_c = map(sp.Rational, (2, 3, 5))
    gravity = sp.Rational(7, 5)
    p_t = sp.Rational(11, 7)
    mu1 = mass_a * mass_c / (mass_a + mass_c)
    mu2 = mass_b * mass_c / (mass_b + mass_c)
    k1 = gravity * mass_a * mass_c
    k2 = gravity * mass_b * mass_c
    k3 = gravity * mass_a * mass_b
    hamiltonian = (
        w1.dot(w1) / (2 * mu1)
        + w2.dot(w2) / (2 * mu2)
        + w1.dot(w2) / mass_c
        - k1 / r1
        - k2 / r2
        - k3 / r3
    )
    model_f = (
        r2 * (p1.dot(p1) / (8 * mu1) - k1)
        + r1 * (p2.dot(p2) / (8 * mu2) - k2)
        + (j1 * p1).dot(j2 * p2) / (16 * mass_c)
        + p_t * r1 * r2
    )
    model_k = r3 * model_f - k3 * r1 * r2
    return sp.cancel(model_k - r1 * r2 * r3 * (hamiltonian + p_t))


def _hamiltonian_factor() -> dict[str, Any]:
    zero_definitions = _ks_definitions()
    zero_substitutions = _substitutions(zero_definitions, (1, 0, 0, 0), (1, 0, 2, 3))
    second_definitions = _ks_definitions()
    second_substitutions = _substitutions(
        second_definitions, (0, 0, 1, 0), (2, 3, 4, 0)
    )
    nonzero_substitutions = _substitutions(zero_definitions, (1, 0, 0, 0), (1, 1, 2, 3))
    zero_residual = _hamiltonian_factor_residual((1, 0, 2, 3))
    nonzero_residual = _hamiltonian_factor_residual((1, 1, 2, 3))
    return {
        "xi1_zero": zero_definitions["xi"].subs(zero_substitutions),
        "xi2_zero": second_definitions["xi"].subs(second_substitutions),
        "zero_level_factor_residual": zero_residual,
        "zero_level_factor_identity": zero_residual == 0,
        "nonzero_level_xi": zero_definitions["xi"].subs(nonzero_substitutions),
        "nonzero_level_factor_residual": nonzero_residual,
        "nonzero_level_control_rejected": nonzero_residual != 0,
    }


def _embed_physical_gradient(gradient: sp.Matrix) -> sp.Matrix:
    return (
        gradient[:6, :]
        .col_join(sp.zeros(1, 1))
        .col_join(gradient[6:, :])
        .col_join(sp.zeros(1, 1))
    )


def _transfer() -> dict[str, Any]:
    h = sp.Matrix(range(1, 13))
    g_gradient = sp.Matrix((2, -1, 3, 0, 4, -2, 1, 5, -3, 2, 6, -4))
    f = sp.Matrix((3, 1, -2, 4, 0, 5, -1, 2, 3, -4, 1, 6))
    g_value = sp.Rational(5, 3)
    f_extended = _embed_physical_gradient(f)
    f_extended[-1] = sp.Rational(7, 11)
    poisson7 = _canonical_poisson(7)

    def residual(offset: sp.Rational) -> sp.Expr:
        k_gradient = _embed_physical_gradient(g_value * h + offset * g_gradient)
        k_gradient[-1] = g_value
        left = (f_extended.T * poisson7 * k_gradient)[0]
        right = (
            g_value
            * (_embed_physical_gradient(f).T * poisson7 * _embed_physical_gradient(h))[
                0
            ]
            + offset
            * (
                _embed_physical_gradient(f).T
                * poisson7
                * _embed_physical_gradient(g_gradient)
            )[0]
        )
        return sp.cancel(left - right)

    full_rows = sp.zeros(9, 18)
    full_rows[0, 9] = 1
    full_rows[0, 15] = 1
    full_rows[1, 15] = 1
    full_rows[2, 16] = 1
    full_rows[3, 17] = 1
    b_values = (1, -2, 3, -4, 5)
    for row, (index, b_value) in enumerate(enumerate(b_values, start=1), start=4):
        full_rows[row, 9 + index] = 1
        full_rows[row, 15] = b_value
        full_rows[row, 16] = sp.Rational(index, 7)
        full_rows[row, 17] = sp.Rational(-index, 11)
    reduced_rows = sp.zeros(6, 12)
    reduced_rows[0, 6] = 1
    for row, (index, b_value) in enumerate(enumerate(b_values, start=1), start=1):
        reduced_rows[row, 6] = -b_value
        reduced_rows[row, 6 + index] = 1
    negative_full = full_rows.copy()
    negative_full[-1, :] = negative_full[-2, :]
    negative_reduced = reduced_rows.copy()
    negative_reduced[-1, :] = negative_reduced[-2, :]
    off_shell_only_shell = sp.zeros(9, 18)
    off_shell_only_shell[0, 9] = 1
    off_shell_only_shell[0, 15] = 1
    off_shell_only_shell[1, 15] = 1
    off_shell_only_shell[2, 16] = 1
    off_shell_only_shell[3, 17] = 1
    for row, column in enumerate(range(10, 14), start=4):
        off_shell_only_shell[row, column] = 1
    off_shell_only_shell[8, 16] = 2
    off_shell_only_ambient = off_shell_only_shell.copy()
    off_shell_only_ambient[8, 14] = 1
    off_shell_only_reduced = sp.zeros(6, 12)
    for row, column in enumerate(range(6, 11)):
        off_shell_only_reduced[row, column] = 1
    full_brackets = full_rows * _canonical_poisson(9) * full_rows.T
    reduced_brackets = reduced_rows * _canonical_poisson(6) * reduced_rows.T
    clock = sp.zeros(18, 1)
    clock[6] = 1
    gauge = sp.zeros(18, 1)
    gauge[7] = 1
    clock_bracket = (clock.T * _canonical_poisson(9) * full_rows[1, :].T)[0]
    gauge_bracket = (gauge.T * _canonical_poisson(9) * full_rows[2, :].T)[0]
    shell_residual = residual(sp.Rational(0))
    off_shell_residual = residual(sp.Rational(3, 7))
    return {
        "shell_sundman_residual": shell_residual,
        "off_shell_product_rule_residual": off_shell_residual,
        "sundman_identity_exact": shell_residual == 0 and off_shell_residual == 0,
        "full_family_rank_on_shell": full_rows.rank(),
        "descended_family_rank": reduced_rows.rank(),
        "full_family_involution": full_brackets == sp.zeros(9),
        "descended_family_involution": reduced_brackets == sp.zeros(6),
        "rank_loss_control_full_rank": negative_full.rank(),
        "rank_loss_control_reduced_rank": negative_reduced.rank(),
        "rank_loss_control_rejected": negative_full.rank() < 9
        and negative_reduced.rank() < 6,
        "off_shell_only_ambient_rank": off_shell_only_ambient.rank(),
        "off_shell_only_shell_rank": off_shell_only_shell.rank(),
        "off_shell_only_descended_rank": off_shell_only_reduced.rank(),
        "off_shell_only_family_involution": off_shell_only_ambient
        * _canonical_poisson(9)
        * off_shell_only_ambient.T
        == sp.zeros(9),
        "off_shell_only_control_rejected": off_shell_only_ambient.rank() == 9
        and off_shell_only_shell.rank() < 9
        and off_shell_only_reduced.rank() < 6,
        "clock_pt_bracket": clock_bracket,
        "clock_dependent_control_rejected": clock_bracket != 0,
        "gauge_xi1_bracket": gauge_bracket,
        "gauge_variant_control_rejected": gauge_bracket != 0,
    }


def _spatial_subquotient() -> dict[str, Any]:
    coordinates = sp.symbols("x1 y1 z1 x2 y2 z2")
    momenta = sp.symbols("px1 py1 pz1 px2 py2 pz2")
    x1 = sp.Matrix(coordinates[:3])
    x2 = sp.Matrix(coordinates[3:])
    p1 = sp.Matrix(momenta[:3])
    p2 = sp.Matrix(momenta[3:])
    mass_a, mass_b, mass_c = map(sp.Rational, (2, 3, 5))
    gravity = sp.Rational(7, 5)
    mu1 = mass_a * mass_c / (mass_a + mass_c)
    mu2 = mass_b * mass_c / (mass_b + mass_c)
    k1 = gravity * mass_a * mass_c
    k2 = gravity * mass_b * mass_c
    k3 = gravity * mass_a * mass_b

    def norm(vector: sp.Matrix) -> sp.Expr:
        return sp.sqrt(vector.dot(vector))

    potential = -k1 / norm(x1) - k2 / norm(x2) - k3 / norm(x1 - x2)
    kinetic = p1.dot(p1) / (2 * mu1) + p2.dot(p2) / (2 * mu2) + p1.dot(p2) / mass_c
    substitutions = dict(
        zip(coordinates, map(sp.Integer, (3, 4, 0, -3, 4, 0)), strict=True)
    )
    potential_hessian = sp.hessian(potential, coordinates).subs(substitutions)
    kinetic_hessian = sp.hessian(kinetic, momenta)
    hessian = sp.diag(potential_hessian, kinetic_hessian)
    variational = (_canonical_poisson(6) * hessian).applyfunc(sp.cancel)
    planar_indices = (0, 1, 3, 4, 6, 7, 9, 10)
    vertical_indices = (2, 5, 8, 11)
    planar_block = variational.extract(planar_indices, planar_indices)
    cross_forward = variational.extract(planar_indices, vertical_indices)
    cross_reverse = variational.extract(vertical_indices, planar_indices)

    planar_coordinates = sp.symbols("u1 v1 u2 v2")
    planar_momenta = sp.symbols("pu1 pv1 pu2 pv2")
    u1 = sp.Matrix(planar_coordinates[:2])
    u2 = sp.Matrix(planar_coordinates[2:])
    pu1 = sp.Matrix(planar_momenta[:2])
    pu2 = sp.Matrix(planar_momenta[2:])
    planar_potential = -k1 / norm(u1) - k2 / norm(u2) - k3 / norm(u1 - u2)
    planar_kinetic = (
        pu1.dot(pu1) / (2 * mu1) + pu2.dot(pu2) / (2 * mu2) + pu1.dot(pu2) / mass_c
    )
    planar_substitutions = dict(
        zip(planar_coordinates, map(sp.Integer, (3, 4, -3, 4)), strict=True)
    )
    planar_hessian = sp.diag(
        sp.hessian(planar_potential, planar_coordinates).subs(planar_substitutions),
        sp.hessian(planar_kinetic, planar_momenta),
    )
    planar_direct = (_canonical_poisson(4) * planar_hessian).applyfunc(sp.cancel)
    reflection = sp.eye(12)
    for index in vertical_indices:
        reflection[index, index] = -1
    planar_phase_symbols = planar_coordinates + planar_momenta
    planar_hamiltonian = planar_potential + planar_kinetic
    angular_momentum = (
        planar_coordinates[0] * planar_momenta[1]
        - planar_coordinates[1] * planar_momenta[0]
        + planar_coordinates[2] * planar_momenta[3]
        - planar_coordinates[3] * planar_momenta[2]
    )
    h_gradient = sp.Matrix([planar_hamiltonian]).jacobian(planar_phase_symbols).T
    angular_momentum_gradient = (
        sp.Matrix([angular_momentum]).jacobian(planar_phase_symbols).T
    )
    rotation_generator = _canonical_poisson(4) * angular_momentum_gradient
    expected_rotation_generator = sp.Matrix(
        (
            -planar_coordinates[1],
            planar_coordinates[0],
            -planar_coordinates[3],
            planar_coordinates[2],
            -planar_momenta[1],
            planar_momenta[0],
            -planar_momenta[3],
            planar_momenta[2],
        )
    )
    momentum_bracket = sp.simplify(
        (h_gradient.T * _canonical_poisson(4) * angular_momentum_gradient)[0]
    )
    phase_substitutions = {
        **planar_substitutions,
        **dict(zip(planar_momenta, map(sp.Integer, (1, 2, 2, -1)), strict=True)),
    }
    h_gradient_probe = h_gradient.subs(phase_substitutions).applyfunc(sp.cancel)
    momentum_gradient_probe = angular_momentum_gradient.subs(
        phase_substitutions
    ).applyfunc(sp.cancel)
    rotation_probe = rotation_generator.subs(phase_substitutions).applyfunc(sp.cancel)
    flow_probe = (_canonical_poisson(4) * h_gradient_probe).applyfunc(sp.cancel)
    angular_momentum_probe = sp.cancel(angular_momentum.subs(phase_substitutions))
    spatial_dimension = variational.rows
    planar_dimension = planar_block.rows
    fixed_momentum_tangent_dimension = planar_dimension - momentum_gradient_probe.rank()
    rotation_quotient_dimension = (
        fixed_momentum_tangent_dimension - rotation_probe.rank()
    )
    energy_tangent_dimension = rotation_quotient_dimension - 1
    normal_quotient_dimension = energy_tangent_dimension - 1
    return {
        "planar_vertical_cross_zero": cross_forward == sp.zeros(8, 4)
        and cross_reverse == sp.zeros(4, 8),
        "planar_block_exact": planar_block == planar_direct,
        "reflection_commutes_with_variational_matrix": reflection * variational
        == variational * reflection,
        "spatial_variational_rank": variational.rank(),
        "planar_variational_rank": planar_direct.rank(),
        "vertical_variational_rank": variational.extract(
            vertical_indices, vertical_indices
        ).rank(),
        "angular_momentum": angular_momentum_probe,
        "angular_momentum_nonzero": angular_momentum_probe != 0,
        "rotation_generator_identity": rotation_generator
        == expected_rotation_generator,
        "angular_momentum_conservation_residual": momentum_bracket,
        "angular_momentum_conserved": momentum_bracket == 0,
        "flow_tangent_to_fixed_momentum_level": (
            momentum_gradient_probe.T * flow_probe
        )[0]
        == 0,
        "rotation_tangent_to_energy_level": (h_gradient_probe.T * rotation_probe)[0]
        == 0,
        "energy_momentum_gradient_rank": h_gradient_probe.row_join(
            momentum_gradient_probe
        ).rank(),
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
        "planar_block": planar_block,
    }


def _encode(value: Any) -> Any:
    if isinstance(value, sp.MatrixBase):
        return [
            [_encode(value[row, column]) for column in range(value.cols)]
            for row in range(value.rows)
        ]
    if isinstance(value, sp.Basic):
        if value in (sp.true, sp.false):
            return bool(value)
        if value.is_Integer:
            return str(value)
        if value.is_Rational:
            return str(value)
        return str(sp.cancel(value))
    if isinstance(value, dict):
        return {key: _encode(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_encode(item) for item in value]
    return value


def all_reference_certificates() -> dict[str, Any]:
    zero_level = _single_ks((1, 2, 3, 4), (5, 15, 2, 1))
    wrong_factor = _single_ks((1, 2, 3, 4), (5, 15, 2, 1), momentum_denominator=2)
    nonzero_level = _single_ks((1, 2, 3, 4), (5, -3, 2, -4))
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
        "product_reduction": _product_reduction(),
        "hamiltonian_factor": _hamiltonian_factor(),
        "transfer": _transfer(),
        "spatial_subquotient": _spatial_subquotient(),
        "logic": {
            "abelian_group_has_only_abelian_algebraic_quotients": True,
            "nonabelian_quotient_obstructs_abelian_full_group": True,
            "global_family_restricts_to_every_regular_open_subset": True,
            "binary_collision_extension_does_not_remove_regular_open_restriction": True,
        },
    }
    return _encode(payload)
