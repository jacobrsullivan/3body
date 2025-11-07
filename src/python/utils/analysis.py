"""
Performance analysis and metrics for CR3BP integrators.

This module provides comprehensive analysis tools for evaluating integrator
performance, accuracy, and behavior in the CR3BP system.
"""

import numpy as np
from typing import Dict, Any, List, Optional
import time
import psutil
from dataclasses import dataclass

from .dynamics import (
    jacobi_drift_metric,
    relative_jacobi_error,
    energy_error_metric,
    relative_energy_error,
)


@dataclass
class PerformanceMetrics:
    """Container for integrator performance metrics."""

    # Accuracy metrics
    jacobi_drift: float
    jacobi_drift_relative: float
    energy_error: float
    energy_error_relative: float

    # Performance metrics
    wall_time: float
    cpu_time: float
    memory_peak_mb: float
    memory_avg_mb: float

    # Integration metrics
    n_steps: int
    n_function_evaluations: int
    steps_per_second: float
    points_per_second: float

    # Quality metrics
    success: bool
    convergence_achieved: bool
    numerical_issues: List[str]

    # Optional metrics
    position_error: Optional[float] = None


class IntegratorAnalyzer:
    """
    Comprehensive analyzer for integrator performance and accuracy.

    This class provides methods to evaluate integrator results across
    multiple metrics including accuracy, performance, and stability.
    """

    def __init__(self, mu: float):
        """
        Initialize analyzer for given CR3BP system.

        Args:
            mu: Mass parameter (M2 / (M1 + M2))
        """
        self.mu = mu
        self.memory_samples = []
        self.start_time = None
        self.start_memory = None

    def start_monitoring(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        self.memory_samples = [self.start_memory]

    def sample_memory(self):
        """Sample current memory usage."""
        if self.start_time is not None:
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            self.memory_samples.append(current_memory)

    def stop_monitoring(self) -> Dict[str, float]:
        """
        Stop monitoring and return timing/memory statistics.

        Returns:
            Dictionary with timing and memory metrics
        """
        if self.start_time is None:
            return {}

        wall_time = time.time() - self.start_time

        # Memory statistics
        memory_peak = max(self.memory_samples) if self.memory_samples else 0
        memory_avg = np.mean(self.memory_samples) if self.memory_samples else 0
        memory_usage = memory_peak - self.start_memory

        return {
            "wall_time": wall_time,
            "memory_peak_mb": memory_peak,
            "memory_avg_mb": memory_avg,
            "memory_usage_mb": memory_usage,
        }

    def analyze_trajectory(
        self,
        times: np.ndarray,
        states: np.ndarray,
        reference_state: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        """
        Analyze trajectory for accuracy and behavior.

        Args:
            times: Time points
            states: State vectors [N, 6]
            reference_state: Reference solution for comparison (optional)

        Returns:
            Dictionary with trajectory analysis results
        """
        if states.ndim != 2 or states.shape[1] != 6:
            raise ValueError("States must be array of shape [N, 6]")

        analysis = {}

        # Jacobi constant analysis
        initial_jacobi, final_jacobi, jacobi_series = jacobi_drift_metric(
            states, self.mu
        )
        jacobi_drift_abs = abs(final_jacobi - initial_jacobi)
        jacobi_drift_rel = relative_jacobi_error(states, self.mu)

        analysis["jacobi"] = {
            "initial": initial_jacobi,
            "final": final_jacobi,
            "drift_absolute": jacobi_drift_abs,
            "drift_relative": jacobi_drift_rel,
            "series": jacobi_series,
            "std": np.std(jacobi_series),
            "max_deviation": np.max(np.abs(jacobi_series - initial_jacobi)),
        }

        # Energy analysis
        initial_energy, final_energy, energy_series = energy_error_metric(
            states, self.mu
        )
        energy_drift_abs = abs(final_energy - initial_energy)
        energy_drift_rel = relative_energy_error(states, self.mu)

        analysis["energy"] = {
            "initial": initial_energy,
            "final": final_energy,
            "drift_absolute": energy_drift_abs,
            "drift_relative": energy_drift_rel,
            "series": energy_series,
            "std": np.std(energy_series),
            "max_deviation": np.max(np.abs(energy_series - initial_energy)),
        }

        # Position analysis
        positions = states[:, :3]
        analysis["position"] = {
            "initial": positions[0],
            "final": positions[-1],
            "displacement": np.linalg.norm(positions[-1] - positions[0]),
            "max_distance": np.max(np.linalg.norm(positions, axis=1)),
            "trajectory_length": self._calculate_trajectory_length(positions),
        }

        # Velocity analysis
        velocities = states[:, 3:6]
        analysis["velocity"] = {
            "initial_speed": np.linalg.norm(velocities[0]),
            "final_speed": np.linalg.norm(velocities[-1]),
            "max_speed": np.max(np.linalg.norm(velocities, axis=1)),
            "avg_speed": np.mean(np.linalg.norm(velocities, axis=1)),
        }

        # Numerical quality assessment
        analysis["quality"] = self._assess_numerical_quality(states, times)

        # Reference comparison if available
        if reference_state is not None:
            analysis["reference_comparison"] = self._compare_to_reference(
                states[-1], reference_state
            )

        return analysis

    def _calculate_trajectory_length(self, positions: np.ndarray) -> float:
        """Calculate total trajectory arc length."""
        if len(positions) < 2:
            return 0.0

        diffs = np.diff(positions, axis=0)
        distances = np.linalg.norm(diffs, axis=1)
        return np.sum(distances)

    def _assess_numerical_quality(
        self, states: np.ndarray, times: np.ndarray
    ) -> Dict[str, Any]:
        """Assess numerical quality of integration."""
        quality = {
            "finite_values": np.all(np.isfinite(states)),
            "reasonable_magnitudes": True,
            "smooth_trajectory": True,
            "issues": [],
        }

        # Check for unreasonable magnitudes
        max_position = np.max(np.abs(states[:, :3]))
        max_velocity = np.max(np.abs(states[:, 3:6]))

        if max_position > 100:
            quality["reasonable_magnitudes"] = False
            quality["issues"].append(f"Large position values (max: {max_position:.2e})")

        if max_velocity > 100:
            quality["reasonable_magnitudes"] = False
            quality["issues"].append(f"Large velocity values (max: {max_velocity:.2e})")

        # Check for smoothness (detect jumps)
        if len(states) > 2:
            position_diffs = np.diff(states[:, :3], axis=0)
            max_position_jump = np.max(np.linalg.norm(position_diffs, axis=1))

            # Rough heuristic for detecting jumps
            dt_typical = np.mean(np.diff(times))
            expected_position_change = (
                max_velocity * dt_typical * 10
            )  # Allow 10x margin

            if max_position_jump > expected_position_change:
                quality["smooth_trajectory"] = False
                quality["issues"].append(
                    f"Large position jump detected: {max_position_jump:.2e}"
                )

        return quality

    def _compare_to_reference(
        self, final_state: np.ndarray, reference_state: np.ndarray
    ) -> Dict[str, float]:
        """Compare final state to reference solution."""
        position_error = np.linalg.norm(final_state[:3] - reference_state[:3])
        velocity_error = np.linalg.norm(final_state[3:6] - reference_state[3:6])
        total_error = np.linalg.norm(final_state - reference_state)

        return {
            "position_error": position_error,
            "velocity_error": velocity_error,
            "total_error": total_error,
            "relative_position_error": position_error
            / np.linalg.norm(reference_state[:3]),
            "relative_velocity_error": velocity_error
            / np.linalg.norm(reference_state[3:6]),
        }

    def create_performance_metrics(
        self,
        times: np.ndarray,
        states: np.ndarray,
        integration_stats: Dict[str, Any],
        timing_stats: Optional[Dict[str, Any]] = None,
    ) -> PerformanceMetrics:
        """
        Create comprehensive performance metrics object.

        Args:
            times: Time points
            states: State vectors [N, 6]
            integration_stats: Statistics from integrator
            timing_stats: Timing and memory statistics

        Returns:
            PerformanceMetrics object
        """
        # Analyze trajectory
        trajectory_analysis = self.analyze_trajectory(times, states)

        # Default timing stats if not provided
        if timing_stats is None:
            timing_stats = {
                "wall_time": 0.0,
                "memory_peak_mb": 0.0,
                "memory_avg_mb": 0.0,
            }

        # Extract key metrics
        jacobi_metrics = trajectory_analysis["jacobi"]
        energy_metrics = trajectory_analysis["energy"]
        quality_metrics = trajectory_analysis["quality"]

        # Calculate performance rates
        wall_time = max(
            timing_stats.get("wall_time", 0.001), 0.001
        )  # Avoid division by zero
        n_points = len(times)
        n_steps = integration_stats.get("n_steps", n_points)

        return PerformanceMetrics(
            # Accuracy metrics
            jacobi_drift=jacobi_metrics["drift_absolute"],
            jacobi_drift_relative=jacobi_metrics["drift_relative"],
            energy_error=energy_metrics["drift_absolute"],
            energy_error_relative=energy_metrics["drift_relative"],
            # Performance metrics
            wall_time=wall_time,
            cpu_time=timing_stats.get(
                "cpu_time", wall_time
            ),  # Approximate if not available
            memory_peak_mb=timing_stats.get("memory_peak_mb", 0.0),
            memory_avg_mb=timing_stats.get("memory_avg_mb", 0.0),
            # Integration metrics
            n_steps=n_steps,
            n_function_evaluations=integration_stats.get(
                "n_function_evaluations", n_steps
            ),
            steps_per_second=n_steps / wall_time,
            points_per_second=n_points / wall_time,
            # Quality metrics
            success=quality_metrics["finite_values"]
            and quality_metrics["reasonable_magnitudes"],
            convergence_achieved=jacobi_metrics["drift_relative"] < 1e-10,
            numerical_issues=quality_metrics["issues"],
        )

    def compare_integrators(
        self, results: Dict[str, PerformanceMetrics]
    ) -> Dict[str, Any]:
        """
        Compare multiple integrator results.

        Args:
            results: Dictionary mapping integrator names to PerformanceMetrics

        Returns:
            Comparison analysis
        """
        if not results:
            return {}

        comparison = {
            "integrators": list(results.keys()),
            "rankings": {},
            "summary": {},
        }

        # Rank by different criteria
        comparison["rankings"]["accuracy"] = sorted(
            results.keys(), key=lambda k: results[k].jacobi_drift_relative
        )

        comparison["rankings"]["speed"] = sorted(
            results.keys(), key=lambda k: results[k].wall_time
        )

        comparison["rankings"]["efficiency"] = sorted(
            results.keys(),
            key=lambda k: results[k].jacobi_drift_relative * results[k].wall_time,
        )

        # Summary statistics
        for metric in [
            "jacobi_drift_relative",
            "energy_error_relative",
            "wall_time",
            "memory_peak_mb",
        ]:
            values = [getattr(results[k], metric) for k in results.keys()]
            comparison["summary"][metric] = {
                "min": min(values),
                "max": max(values),
                "mean": np.mean(values),
                "std": np.std(values),
            }

        return comparison

    def generate_report(
        self,
        integrator_name: str,
        metrics: PerformanceMetrics,
        trajectory_analysis: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate human-readable performance report.

        Args:
            integrator_name: Name of the integrator
            metrics: Performance metrics
            trajectory_analysis: Optional detailed trajectory analysis

        Returns:
            Formatted report string
        """
        report_lines = [
            f"Performance Report: {integrator_name}",
            "=" * (20 + len(integrator_name)),
            "",
            "ACCURACY METRICS:",
            f"  Jacobi Drift (relative): {metrics.jacobi_drift_relative:.2e}",
            f"  Energy Error (relative): {metrics.energy_error_relative:.2e}",
            f"  Integration Success: {'✓' if metrics.success else '✗'}",
            "",
            "PERFORMANCE METRICS:",
            f"  Wall Time: {metrics.wall_time:.3f} seconds",
            f"  Memory Usage: {metrics.memory_peak_mb:.1f} MB",
            f"  Points per Second: {metrics.points_per_second:.1f}",
            f"  Steps per Second: {metrics.steps_per_second:.1f}",
            "",
            "INTEGRATION DETAILS:",
            f"  Total Steps: {metrics.n_steps}",
            f"  Function Evaluations: {metrics.n_function_evaluations}",
            f"  Convergence Achieved: {'✓' if metrics.convergence_achieved else '✗'}",
        ]

        if metrics.numerical_issues:
            report_lines.extend(
                [
                    "",
                    "NUMERICAL ISSUES:",
                    *[f"  - {issue}" for issue in metrics.numerical_issues],
                ]
            )

        if trajectory_analysis:
            jacobi = trajectory_analysis.get("jacobi", {})
            energy = trajectory_analysis.get("energy", {})

            report_lines.extend(
                [
                    "",
                    "DETAILED ANALYSIS:",
                    f"  Jacobi Constant (initial): {jacobi.get('initial', 0):.6f}",
                    f"  Jacobi Standard Deviation: {jacobi.get('std', 0):.2e}",
                    f"  Energy Standard Deviation: {energy.get('std', 0):.2e}",
                ]
            )

        return "\n".join(report_lines)
