"""Cross-validation tests for production canonical KS dynamics."""

import numpy as np
import pytest

from kepler_benchmarks import KeplerBenchmark, load_locked_benchmarks
from kepler_reference import EllipticElements
from ks_benchmark_evaluator import evaluate_ks_benchmark


@pytest.mark.parametrize("benchmark", load_locked_benchmarks(), ids=lambda item: item.case_id)
def test_canonical_ks_matches_analytic_and_rebound_references(benchmark):
    evaluation = evaluate_ks_benchmark(benchmark)
    metrics = evaluation.metrics

    assert np.all(np.diff(evaluation.spinor_times) >= 0.0)
    assert metrics["analytic_state_error_max"] < 2e-11
    assert metrics["rebound_state_error_max"] < 1e-9
    assert metrics["closure_position_error"] < 2e-12
    assert metrics["closure_velocity_error"] < 2e-11
    assert metrics["regularized_hamiltonian_abs_max"] < 2e-13
    assert metrics["momentum_map_abs_max"] < 2e-13
    assert metrics["physical_energy_abs_error_max"] < 2e-10
    assert metrics["period_relative_error"] < 2e-14


def test_nonunit_reduced_mass_matches_velocity_references():
    benchmark = KeplerBenchmark(
        case_id="nonunit-mass-test",
        description="Canonical momentum is reduced_mass times velocity",
        elements=EllipticElements(
            mu=1.7,
            semi_major_axis=0.8,
            eccentricity=0.35,
            inclination=0.8,
            longitude_of_ascending_node=-2.3,
            argument_of_periapsis=0.55,
            mean_anomaly_at_epoch=0.77,
            epoch=0.1,
        ),
        period_fractions=(0.0, 0.2, 0.5, 1.0),
        reduced_mass=0.37,
    )

    metrics = evaluate_ks_benchmark(benchmark).metrics

    assert metrics["analytic_state_error_max"] < 2e-12
    assert metrics["rebound_state_error_max"] < 2e-10
    assert metrics["period_relative_error"] < 2e-14
