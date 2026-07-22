from __future__ import annotations

from src.python.wp4_lift_ni_v2 import all_production_certificates


def test_exact_production_certificates_pass_the_locked_obligations() -> None:
    result = all_production_certificates()
    single = result["single_ks_zero_level"]
    assert single["xi"] == "0"
    assert single["projection_rank"] == 6
    assert single["constraint_projection_rank"] == 7
    assert single["canonical_on_zero_level"]
    assert single["phase_gauge_kernel_identity"]

    product = result["product_reduction"]
    assert (
        product["upstairs_dimension"],
        product["regular_level_dimension"],
        product["quotient_dimension"],
    ) == (18, 16, 14)
    assert product["constraint_projection_rank"] == 16

    factor = result["hamiltonian_factor"]
    assert factor["zero_level_factor_residual"] == "0"
    assert factor["zero_level_factor_identity"]

    transfer = result["transfer"]
    assert transfer["sundman_identity_exact"]
    assert transfer["full_family_rank_on_shell"] == 9
    assert transfer["descended_family_rank"] == 6
    assert transfer["full_family_involution"]
    assert transfer["descended_family_involution"]

    spatial = result["spatial_subquotient"]
    assert spatial["planar_vertical_cross_zero"]
    assert spatial["planar_block_exact"]
    assert spatial["reflection_commutes_with_variational_matrix"]
    assert spatial["angular_momentum_nonzero"]
    assert spatial["rotation_generator_identity"]
    assert spatial["angular_momentum_conserved"]
    assert spatial["energy_momentum_gradient_rank"] == 2
    assert spatial["published_nve_chain_dimension_exact"]


def test_all_six_locked_negative_controls_fail_closed() -> None:
    result = all_production_certificates()
    assert result["wrong_momentum_factor_control"]["rejected"]
    assert result["nonzero_xi_control"]["rejected"]
    assert result["hamiltonian_factor"]["nonzero_level_control_rejected"]
    assert result["transfer"]["clock_dependent_control_rejected"]
    assert result["transfer"]["gauge_variant_control_rejected"]
    assert result["transfer"]["off_shell_only_ambient_rank"] == 9
    assert result["transfer"]["off_shell_only_shell_rank"] == 8
    assert result["transfer"]["off_shell_only_descended_rank"] == 5
    assert result["transfer"]["off_shell_only_family_involution"]
    assert result["transfer"]["off_shell_only_control_rejected"]
    assert result["transfer"]["rank_loss_control_rejected"]
