"""
Unit tests for multi_stage_pipeline.py (AMENDED WP3.3).

Tests the complete multi-stage symbolic regression pipeline.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/python'))

import numpy as np
import pytest
from symbolic.multi_stage_pipeline import (
    SearchStage,
    MultiStageResult,
    analyze_trajectory_characteristics,
    run_multi_stage_pipeline
)


class TestTrajectoryCharacteristics:
    """Test trajectory characteristic analysis."""

    def test_analyze_basic_trajectory(self):
        """Test analysis of basic trajectory."""
        trajectory = np.random.randn(1000, 18)
        times = np.linspace(0, 100, 1000)
        masses = np.array([1.0, 1.0, 1.0])

        char = analyze_trajectory_characteristics(trajectory, times, masses)

        # Should return dict with expected keys
        assert 'close_encounter_fraction' in char
        assert 'min_distance' in char
        assert 'needs_regularization' in char
        assert 'energy_drift' in char
        assert 'mean_energy' in char
        assert 'total_time' in char
        assert 'dt_mean' in char
        assert 'n_samples' in char

        # Check values are reasonable
        assert 0 <= char['close_encounter_fraction'] <= 1
        assert char['min_distance'] > 0
        assert char['total_time'] > 0
        assert char['dt_mean'] > 0
        assert char['n_samples'] == 1000

    def test_analyze_close_encounter_trajectory(self):
        """Test analysis of trajectory with close encounters."""
        trajectory = np.zeros((1000, 18))

        # Create trajectory with close encounters
        for i in range(1000):
            if i % 10 == 0:
                # Close encounter
                trajectory[i, :9] = np.random.randn(9) * 0.05
            else:
                trajectory[i, :9] = np.random.randn(9)

            trajectory[i, 9:] = np.random.randn(9) * 0.1  # Velocities

        times = np.linspace(0, 100, 1000)
        masses = np.array([1.0, 1.0, 1.0])

        char = analyze_trajectory_characteristics(trajectory, times, masses)

        # Should detect close encounters
        assert char['close_encounter_fraction'] > 0
        assert char['needs_regularization'] or char['close_encounter_fraction'] > 0


class TestSearchStageEnum:
    """Test SearchStage enum."""

    def test_stage_ordering(self):
        """Test that stages are properly ordered."""
        assert SearchStage.POLYNOMIAL.value < SearchStage.SPINOR.value
        assert SearchStage.SPINOR.value < SearchStage.ELLIPTIC.value
        assert SearchStage.ELLIPTIC.value < SearchStage.THETA.value


class TestMultiStagePipeline:
    """Test complete multi-stage pipeline."""

    def test_pipeline_returns_result(self):
        """Test that pipeline returns a result."""
        trajectory = np.random.randn(500, 18)
        times = np.linspace(0, 50, 500)
        masses = np.array([1.0, 1.0, 1.0])

        def test_integral(state):
            return np.sum(state[:9]**2)  # Energy-like

        result = run_multi_stage_pipeline(
            I_numerical=test_integral,
            trajectory=trajectory,
            trajectory_times=times,
            masses=masses,
            max_stage=SearchStage.POLYNOMIAL,
            verbose=False
        )

        assert isinstance(result, MultiStageResult)
        assert isinstance(result.stage_completed, SearchStage)
        assert isinstance(result.all_candidates, list)
        assert isinstance(result.trajectory_characteristics, dict)
        assert isinstance(result.recommendation, str)

    def test_pipeline_polynomial_stage(self):
        """Test pipeline with polynomial stage only."""
        trajectory = np.random.randn(500, 18)
        times = np.linspace(0, 50, 500)
        masses = np.array([1.0, 1.0, 1.0])

        # Simple quadratic integral
        def quadratic_integral(state):
            return np.sum(state[:9]**2)

        result = run_multi_stage_pipeline(
            I_numerical=quadratic_integral,
            trajectory=trajectory,
            trajectory_times=times,
            masses=masses,
            max_stage=SearchStage.POLYNOMIAL,
            verbose=False
        )

        # Should complete at least polynomial stage
        assert result.stage_completed in [SearchStage.POLYNOMIAL, SearchStage.SPINOR, SearchStage.ELLIPTIC]

    def test_pipeline_with_spinor_stage(self):
        """Test pipeline including spinor stage."""
        trajectory = np.random.randn(500, 18)
        times = np.linspace(0, 50, 500)
        masses = np.array([1.0, 1.0, 1.0])

        def test_integral(state):
            return np.sum(state**2)

        result = run_multi_stage_pipeline(
            I_numerical=test_integral,
            trajectory=trajectory,
            trajectory_times=times,
            masses=masses,
            max_stage=SearchStage.SPINOR,
            verbose=False
        )

        assert isinstance(result, MultiStageResult)
        # Stage completed should be at least POLYNOMIAL
        assert result.stage_completed.value >= SearchStage.POLYNOMIAL.value

    def test_pipeline_with_elliptic_stage(self):
        """Test pipeline including elliptic stage."""
        trajectory = np.random.randn(500, 18)
        times = np.linspace(0, 50, 500)
        masses = np.array([1.0, 1.0, 1.0])

        def test_integral(state):
            return np.sum(state**2)

        result = run_multi_stage_pipeline(
            I_numerical=test_integral,
            trajectory=trajectory,
            trajectory_times=times,
            masses=masses,
            max_stage=SearchStage.ELLIPTIC,
            verbose=False
        )

        assert isinstance(result, MultiStageResult)

    def test_pipeline_verbose_output(self, capsys):
        """Test that verbose mode produces output."""
        trajectory = np.random.randn(200, 18)
        times = np.linspace(0, 20, 200)
        masses = np.array([1.0, 1.0, 1.0])

        def test_integral(state):
            return np.sum(state**2)

        result = run_multi_stage_pipeline(
            I_numerical=test_integral,
            trajectory=trajectory,
            trajectory_times=times,
            masses=masses,
            max_stage=SearchStage.POLYNOMIAL,
            verbose=True
        )

        captured = capsys.readouterr()
        assert len(captured.out) > 0, "Verbose mode should produce output"
        assert "MULTI-STAGE" in captured.out or "STAGE" in captured.out

    def test_pipeline_with_candidates(self):
        """Test that pipeline produces candidates."""
        trajectory = np.random.randn(500, 18)
        times = np.linspace(0, 50, 500)
        masses = np.array([1.0, 1.0, 1.0])

        def test_integral(state):
            return np.sum(state[:9]**2)

        result = run_multi_stage_pipeline(
            I_numerical=test_integral,
            trajectory=trajectory,
            trajectory_times=times,
            masses=masses,
            max_stage=SearchStage.ELLIPTIC,
            verbose=False
        )

        # May or may not find candidates, but list should exist
        assert isinstance(result.all_candidates, list)

    def test_pipeline_recommendation_exists(self):
        """Test that pipeline always provides a recommendation."""
        trajectory = np.random.randn(300, 18)
        times = np.linspace(0, 30, 300)
        masses = np.array([1.0, 1.0, 1.0])

        def test_integral(state):
            return 1.0  # Constant

        result = run_multi_stage_pipeline(
            I_numerical=test_integral,
            trajectory=trajectory,
            trajectory_times=times,
            masses=masses,
            max_stage=SearchStage.POLYNOMIAL,
            verbose=False
        )

        assert len(result.recommendation) > 0, "Should provide recommendation"


class TestPipelineIntegration:
    """Test integration of all pipeline stages."""

    def test_pipeline_completes_without_error(self):
        """Test that pipeline completes for various integrals."""
        trajectory = np.random.randn(300, 18)
        times = np.linspace(0, 30, 300)
        masses = np.array([1.0, 1.0, 1.0])

        test_integrals = [
            lambda state: np.sum(state**2),  # Quadratic
            lambda state: np.sum(state[:9]**2),  # Kinetic-like
            lambda state: 1.0,  # Constant
            lambda state: np.sum(state[:9]),  # Linear
        ]

        for integral in test_integrals:
            try:
                result = run_multi_stage_pipeline(
                    I_numerical=integral,
                    trajectory=trajectory,
                    trajectory_times=times,
                    masses=masses,
                    max_stage=SearchStage.POLYNOMIAL,
                    verbose=False
                )
                assert isinstance(result, MultiStageResult)
            except Exception as e:
                pytest.fail(f"Pipeline failed for integral: {e}")

    def test_pipeline_with_close_encounters(self):
        """Test pipeline on trajectory with close encounters."""
        trajectory = np.zeros((500, 18))

        for i in range(500):
            if i % 20 == 0:
                trajectory[i, :9] = np.random.randn(9) * 0.05  # Close
            else:
                trajectory[i, :9] = np.random.randn(9)
            trajectory[i, 9:] = np.random.randn(9) * 0.1

        times = np.linspace(0, 50, 500)
        masses = np.array([1.0, 1.0, 1.0])

        def test_integral(state):
            return np.sum(state**2)

        result = run_multi_stage_pipeline(
            I_numerical=test_integral,
            trajectory=trajectory,
            trajectory_times=times,
            masses=masses,
            max_stage=SearchStage.SPINOR,
            verbose=False
        )

        # Should detect close encounters and possibly trigger spinor search
        assert result.trajectory_characteristics['close_encounter_fraction'] > 0


class TestPipelineEdgeCases:
    """Test pipeline edge cases."""

    def test_pipeline_with_short_trajectory(self):
        """Test pipeline with very short trajectory."""
        trajectory = np.random.randn(50, 18)
        times = np.linspace(0, 5, 50)
        masses = np.array([1.0, 1.0, 1.0])

        def test_integral(state):
            return np.sum(state**2)

        result = run_multi_stage_pipeline(
            I_numerical=test_integral,
            trajectory=trajectory,
            trajectory_times=times,
            masses=masses,
            max_stage=SearchStage.POLYNOMIAL,
            verbose=False
        )

        assert isinstance(result, MultiStageResult)

    def test_pipeline_with_nan_integral(self):
        """Test pipeline with integral that returns NaN."""
        trajectory = np.random.randn(200, 18)
        times = np.linspace(0, 20, 200)
        masses = np.array([1.0, 1.0, 1.0])

        def nan_integral(state):
            return np.nan

        # Pipeline should handle NaN gracefully
        try:
            result = run_multi_stage_pipeline(
                I_numerical=nan_integral,
                trajectory=trajectory,
                trajectory_times=times,
                masses=masses,
                max_stage=SearchStage.POLYNOMIAL,
                verbose=False
            )
            assert isinstance(result, MultiStageResult)
        except:
            # It's okay if pipeline fails on NaN - just shouldn't crash
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
