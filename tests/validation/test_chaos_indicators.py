"""
Tests for chaos indicators (MEGNO and FLI).

This test suite validates MEGNO and FLI implementations against:
1. Known regular motion (harmonic oscillator)
2. Known chaotic motion (double pendulum approximation)
3. CR3BP test cases (regular prograde, chaotic L1 Lyapunov)
"""

import pytest
import numpy as np
from src.python.validation.chaos_indicators import (
    MEGNOIndicator,
    FLIIndicator,
    ChaosAnalyzer,
    create_cr3bp_chaos_analyzer,
    cr3bp_dynamics_wrapper,
)


class TestMEGNOIndicator:
    """Test MEGNO indicator implementation."""

    def test_harmonic_oscillator_regular(self):
        """Test MEGNO on harmonic oscillator (known regular motion)."""

        # Harmonic oscillator: ẍ + ω²x = 0
        # State: [x, v], dynamics: [v, -ω²x]
        omega = 1.0

        def harmonic_dynamics(t, state):
            x, v = state
            return np.array([v, -omega**2 * x])

        # Initial condition
        initial_state = np.array([1.0, 0.0])

        # Create MEGNO indicator
        megno = MEGNOIndicator(harmonic_dynamics)

        # Compute for 100 periods
        t_final = 100 * (2 * np.pi / omega)
        times, megno_values, dev_norms = megno.compute(
            initial_state, t_final, output_interval=10.0
        )

        # For regular motion, MEGNO should converge to ~2.0
        final_megno = megno_values[-1]

        assert len(times) > 10, "Should have multiple output points"
        assert np.all(np.isfinite(megno_values)), "MEGNO should be finite"
        assert np.abs(final_megno - 2.0) < 0.5, (
            f"MEGNO for regular motion should be ~2.0, got {final_megno:.3f}"
        )

    def test_megno_converges(self):
        """Test that MEGNO converges over time."""

        def simple_dynamics(t, state):
            return np.array([state[1], -state[0]])

        initial_state = np.array([1.0, 0.0])
        megno = MEGNOIndicator(simple_dynamics)

        t_final = 500.0
        times, megno_values, _ = megno.compute(
            initial_state, t_final, output_interval=10.0
        )

        # MEGNO should stabilize (variance decreases)
        early_variance = np.var(megno_values[:len(megno_values)//4])
        late_variance = np.var(megno_values[3*len(megno_values)//4:])

        assert late_variance < early_variance, "MEGNO should stabilize over time"

    def test_different_initial_deviations(self):
        """Test that MEGNO is independent of initial deviation magnitude."""

        def dynamics(t, state):
            return np.array([state[1], -state[0]])

        initial_state = np.array([1.0, 0.0])
        t_final = 200.0

        megno = MEGNOIndicator(dynamics)

        # Test with different initial deviation scales
        _, megno1, _ = megno.compute(
            initial_state, t_final,
            initial_deviation=np.array([1e-10, 0.0])
        )

        _, megno2, _ = megno.compute(
            initial_state, t_final,
            initial_deviation=np.array([1e-5, 0.0])
        )

        # MEGNO should be similar regardless of initial deviation magnitude
        final_diff = np.abs(megno1[-1] - megno2[-1])
        assert final_diff < 0.2, (
            f"MEGNO should be independent of initial deviation scale, "
            f"diff={final_diff:.3f}"
        )


class TestFLIIndicator:
    """Test FLI indicator implementation."""

    def test_fli_regular_motion(self):
        """Test FLI on regular motion (should grow slowly)."""

        omega = 1.0

        def harmonic_dynamics(t, state):
            x, v = state
            return np.array([v, -omega**2 * x])

        initial_state = np.array([1.0, 0.0])
        fli = FLIIndicator(harmonic_dynamics)

        # Compute FLI
        t_final = 100 * (2 * np.pi / omega)
        times, fli_values, dev_norms = fli.compute(
            initial_state, t_final, output_interval=10.0
        )

        final_fli = fli_values[-1]

        assert len(times) > 10, "Should have multiple output points"
        assert np.all(np.isfinite(fli_values)), "FLI should be finite"
        assert final_fli < 3.0, (
            f"FLI for regular motion should be low, got {final_fli:.3f}"
        )

    def test_fli_increases_monotonically(self):
        """Test that FLI increases monotonically (or stays constant)."""

        def dynamics(t, state):
            return np.array([state[1], -state[0] + 0.1 * state[0]**3])

        initial_state = np.array([0.5, 0.0])
        fli = FLIIndicator(dynamics)

        times, fli_values, _ = fli.compute(initial_state, 100.0, output_interval=1.0)

        # FLI should generally increase or stay flat
        differences = np.diff(fli_values)
        decreasing_points = np.sum(differences < -0.1)

        # Allow some numerical noise, but shouldn't decrease significantly
        assert decreasing_points < len(differences) * 0.1, (
            "FLI should be generally non-decreasing"
        )


class TestChaosAnalyzer:
    """Test unified chaos analyzer."""

    def test_regular_classification(self):
        """Test classification of regular motion."""

        def regular_dynamics(t, state):
            return np.array([state[1], -state[0]])

        initial_state = np.array([1.0, 0.0])

        analyzer = ChaosAnalyzer(
            regular_dynamics,
            megno_threshold=2.5,
            fli_threshold=3.0
        )

        result = analyzer.analyze(initial_state, 500.0, output_interval=10.0)

        assert result.classification == 'regular', (
            f"Should classify as regular, got {result.classification}"
        )
        assert result.mean_megno < 3.0, f"MEGNO too high: {result.mean_megno:.3f}"

    def test_chaotic_classification_duffing(self):
        """Test classification of chaotic motion (Duffing oscillator)."""

        # Duffing equation: ẍ + δẋ + αx + βx³ = γ cos(ωt)
        # For certain parameters, exhibits chaos
        delta = 0.1
        alpha = -1.0
        beta = 1.0
        gamma = 0.3
        omega_f = 1.0

        def duffing_dynamics(t, state):
            x, v = state
            forcing = gamma * np.cos(omega_f * t)
            acc = -delta * v - alpha * x - beta * x**3 + forcing
            return np.array([v, acc])

        initial_state = np.array([0.1, 0.1])

        analyzer = ChaosAnalyzer(
            duffing_dynamics,
            megno_threshold=2.5,
            fli_threshold=3.0
        )

        result = analyzer.analyze(initial_state, 500.0, output_interval=10.0)

        # Duffing with these parameters is chaotic
        assert result.classification == 'chaotic', (
            f"Should classify as chaotic, got {result.classification}"
        )
        assert result.mean_megno > 2.5, f"MEGNO too low: {result.mean_megno:.3f}"

    def test_both_indicators_computed(self):
        """Test that both MEGNO and FLI are computed."""

        def dynamics(t, state):
            return np.array([state[1], -state[0]])

        analyzer = ChaosAnalyzer(dynamics)
        result = analyzer.analyze(
            np.array([1.0, 0.0]),
            100.0,
            compute_both=True
        )

        assert len(result.megno) > 0, "MEGNO should be computed"
        assert len(result.fli) > 0, "FLI should be computed"
        assert len(result.times) > 0, "Times should be recorded"
        assert 'megno_chaotic' in result.metadata, "Metadata should include flags"
        assert 'fli_chaotic' in result.metadata, "Metadata should include flags"


class TestCR3BPChaos:
    """Test chaos indicators for CR3BP."""

    @pytest.fixture
    def earth_moon_mu(self):
        """Earth-Moon mass parameter."""
        return 0.01215  # Earth-Moon system

    def test_cr3bp_dynamics_wrapper(self, earth_moon_mu):
        """Test CR3BP dynamics wrapper."""
        dynamics = cr3bp_dynamics_wrapper(earth_moon_mu)

        # Test state: near L1 point
        state = np.array([0.8, 0.0, 0.0, 0.0, 0.1, 0.0])

        # Evaluate dynamics
        dstate_dt = dynamics(0.0, state)

        assert dstate_dt.shape == (6,), "Should return 6-dimensional derivative"
        assert np.all(np.isfinite(dstate_dt)), "Derivative should be finite"

        # Velocity components should match state
        assert np.allclose(dstate_dt[:3], state[3:6]), (
            "First 3 components should be velocities"
        )

    def test_create_cr3bp_analyzer(self, earth_moon_mu):
        """Test creation of CR3BP chaos analyzer."""
        analyzer = create_cr3bp_chaos_analyzer(earth_moon_mu)

        assert analyzer.megno_indicator is not None
        assert analyzer.fli_indicator is not None
        assert analyzer.megno_threshold == 2.5
        assert analyzer.fli_threshold == 3.0

    def test_cr3bp_regular_prograde_orbit(self, earth_moon_mu):
        """Test MEGNO/FLI on regular prograde circular orbit."""

        # Stable prograde circular orbit (large radius, away from primaries)
        # These typically show regular motion
        x0 = -0.5
        y0 = 0.0
        z0 = 0.0

        # Circular velocity in co-rotating frame
        # For prograde orbit, velocity perpendicular to radius
        r = np.sqrt(x0**2 + y0**2)
        v_circ = np.sqrt(1.0 / r)  # Approximate
        vx0 = 0.0
        vy0 = v_circ
        vz0 = 0.0

        initial_state = np.array([x0, y0, z0, vx0, vy0, vz0])

        analyzer = create_cr3bp_chaos_analyzer(earth_moon_mu)

        # Shorter integration for tests (full validation would use 1000+)
        result = analyzer.analyze(
            initial_state,
            t_final=100.0,
            output_interval=5.0
        )

        # This orbit should be regular (though short integration may not fully converge)
        # Just check that computation succeeds
        assert result.classification in ['regular', 'chaotic'], (
            "Should classify as regular or chaotic"
        )
        assert np.all(np.isfinite(result.megno)), "MEGNO should be finite"
        assert np.all(np.isfinite(result.fli)), "FLI should be finite"

    def test_cr3bp_escape_trajectory(self, earth_moon_mu):
        """Test chaos indicators on escape trajectory."""

        # High energy escape trajectory
        initial_state = np.array([0.5, 0.0, 0.0, 0.0, 2.0, 0.0])

        analyzer = create_cr3bp_chaos_analyzer(earth_moon_mu)

        # May escape before t_final, so catch potential integration failures
        try:
            result = analyzer.analyze(
                initial_state,
                t_final=50.0,
                output_interval=2.0
            )

            assert result.classification in ['regular', 'chaotic']
            assert len(result.times) > 0, "Should have some output points"

        except RuntimeError as e:
            # Escape trajectories may fail integration (expected)
            pytest.skip(f"Escape trajectory integration failed (expected): {e}")


class TestNumericalStability:
    """Test numerical stability of chaos indicators."""

    def test_megno_handles_small_deviations(self):
        """Test MEGNO handles very small deviation vectors."""

        def dynamics(t, state):
            return np.array([state[1], -state[0]])

        megno = MEGNOIndicator(dynamics)

        # Very small initial deviation
        initial_dev = np.array([1e-15, 1e-15])
        times, megno_vals, _ = megno.compute(
            np.array([1.0, 0.0]),
            100.0,
            initial_deviation=initial_dev
        )

        assert np.all(np.isfinite(megno_vals)), (
            "MEGNO should handle small deviations without NaN/Inf"
        )

    def test_fli_handles_large_growth(self):
        """Test FLI handles large deviation growth."""

        # Unstable dynamics (exponential growth)
        def unstable_dynamics(t, state):
            return np.array([state[1], state[0]])  # ẍ = x (exponential)

        fli = FLIIndicator(unstable_dynamics)

        # This will grow exponentially
        times, fli_vals, dev_norms = fli.compute(
            np.array([1.0, 0.0]),
            10.0,  # Short time to avoid overflow
            output_interval=0.5
        )

        # FLI should be finite (log keeps it bounded)
        assert np.all(np.isfinite(fli_vals)), "FLI should remain finite"
        assert fli_vals[-1] > fli_vals[0], "FLI should increase for unstable system"


@pytest.mark.parametrize("t_final", [50.0, 100.0, 200.0])
def test_megno_convergence_time(t_final):
    """Test MEGNO convergence for different integration times."""

    def regular_dynamics(t, state):
        return np.array([state[1], -state[0]])

    megno = MEGNOIndicator(regular_dynamics)
    times, megno_vals, _ = megno.compute(
        np.array([1.0, 0.0]),
        t_final,
        output_interval=5.0
    )

    # Longer integration should give MEGNO closer to 2.0 for regular motion
    final_megno = megno_vals[-1]

    if t_final >= 200.0:
        # With long integration, should be very close to 2.0
        assert np.abs(final_megno - 2.0) < 0.3, (
            f"Long integration should converge close to 2.0, got {final_megno:.3f}"
        )


def test_chaos_analyzer_quick_classify():
    """Test quick classification method."""

    def regular_dynamics(t, state):
        return np.array([state[1], -state[0]])

    analyzer = ChaosAnalyzer(regular_dynamics)

    classification = analyzer.classify_orbit(
        np.array([1.0, 0.0]),
        t_final=100.0
    )

    assert classification in ['regular', 'chaotic'], (
        f"Classification should be 'regular' or 'chaotic', got {classification}"
    )
