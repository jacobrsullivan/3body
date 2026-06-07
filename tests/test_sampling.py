"""
Unit tests for CR3BP sampling utilities.
"""

import numpy as np

from src.python.ml.sobol_sampling import generate_initial_states_for_mu_c
from src.python.utils.dynamics import calculate_jacobi_constant


def test_generate_initial_states_for_mu_c():
    mu = 0.0121505856
    C = 3.1

    states = generate_initial_states_for_mu_c(
        mu=mu,
        C=C,
        n_samples=20,
        seed=123,
    )

    assert states.shape == (20, 6)
    assert np.all(np.isfinite(states))

    for state in states:
        C_state = calculate_jacobi_constant(state, mu)
        assert abs(C_state - C) < 1e-8
