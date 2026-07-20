"""Tests for the external REBOUND Kepler reference adapter."""

import numpy as np
import pytest

from kepler_benchmarks import load_locked_benchmarks
from kepler_reference import cartesian_state_at_time
from rebound_reference import propagate_kepler_rebound


@pytest.mark.parametrize("benchmark", load_locked_benchmarks(), ids=lambda item: item.case_id)
def test_rebound_ias15_matches_locked_analytic_benchmarks(benchmark):
    elements = benchmark.elements
    elapsed = np.array(benchmark.period_fractions) * elements.period
    initial = cartesian_state_at_time(elements, elements.epoch)
    expected = np.stack(
        [
            cartesian_state_at_time(elements, elements.epoch + time)
            for time in elapsed
        ]
    )
    result = propagate_kepler_rebound(initial, elements.mu, elapsed)

    assert result.integrator == "ias15"
    assert result.rebound_version
    assert np.max(np.abs(result.states - expected)) < 1e-9


def test_rebound_adapter_rejects_nonmonotone_times():
    initial = np.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0])
    with pytest.raises(ValueError, match="monotone"):
        propagate_kepler_rebound(initial, 1.0, [0.0, 1.0, 0.5])
