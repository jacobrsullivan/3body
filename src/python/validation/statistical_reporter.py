"""
Statistical reporter for WP 4.3: Numerical Robustness.

This module generates publication-quality validation reports including:
1. Error distribution plots
2. Success rate heatmaps (mass ratio vs energy)
3. Long-time drift analysis plots
4. Stress test visualizations
5. Statistical tables (LaTeX format)
6. Confidence intervals

Output formats: PNG, PDF, LaTeX, JSON
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
import os
import json

# Import matplotlib only when needed (optional dependency)
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


@dataclass
class ValidationReport:
    """
    Complete validation report data.

    Attributes:
        integral_name: Name of the validated integral
        monte_carlo_results: Results from Monte Carlo validation
        stress_test_results: Results from stress tests
        long_time_results: Results from long-time validation
        metadata: Additional metadata (dates, parameters, etc.)
    """
    integral_name: str
    monte_carlo_results: Optional[Dict]
    stress_test_results: Optional[Dict]
    long_time_results: Optional[Dict]
    metadata: Dict


class StatisticalReporter:
    """
    Generate publication-quality validation reports.

    Example:
        >>> reporter = StatisticalReporter(output_dir='./validation_report')
        >>> reporter.generate_report(
        ...     monte_carlo_results=mc_results,
        ...     stress_test_results=stress_results,
        ...     long_time_results=lt_results,
        ...     integral_name="I_new"
        ... )
    """

    def __init__(self, output_dir: str = './validation_report'):
        """
        Initialize statistical reporter.

        Args:
            output_dir: Directory for output files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Create subdirectories
        self.figures_dir = os.path.join(output_dir, 'figures')
        self.tables_dir = os.path.join(output_dir, 'tables')
        self.data_dir = os.path.join(output_dir, 'data')

        os.makedirs(self.figures_dir, exist_ok=True)
        os.makedirs(self.tables_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)

    def generate_report(
        self,
        monte_carlo_results: Optional[Dict] = None,
        stress_test_results: Optional[Dict] = None,
        long_time_results: Optional[Dict] = None,
        integral_name: str = "I",
        verbose: bool = True
    ):
        """
        Generate complete validation report.

        Args:
            monte_carlo_results: Results from Monte Carlo validation
            stress_test_results: Results from stress tests
            long_time_results: Results from long-time validation
            integral_name: Name of the integral
            verbose: Print progress
        """
        if verbose:
            print("=" * 70)
            print("GENERATING VALIDATION REPORT")
            print("=" * 70)
            print(f"Output directory: {self.output_dir}")

        # Generate plots
        if HAS_MATPLOTLIB:
            if monte_carlo_results:
                self._plot_error_distribution(monte_carlo_results, integral_name)
                if verbose:
                    print("  ✓ Error distribution plot")

            if long_time_results:
                self._plot_drift_analysis(long_time_results, integral_name)
                if verbose:
                    print("  ✓ Long-time drift plot")

            if stress_test_results:
                self._plot_stress_test_summary(stress_test_results, integral_name)
                if verbose:
                    print("  ✓ Stress test summary")
        else:
            if verbose:
                print("  ⚠ matplotlib not available, skipping plots")

        # Generate tables
        if monte_carlo_results:
            self._generate_statistics_table(monte_carlo_results, integral_name)
            if verbose:
                print("  ✓ Statistics table (text)")

            self._generate_latex_table(monte_carlo_results, integral_name)
            if verbose:
                print("  ✓ Statistics table (LaTeX)")

        # Generate summary JSON
        self._generate_json_summary(
            monte_carlo_results,
            stress_test_results,
            long_time_results,
            integral_name
        )
        if verbose:
            print("  ✓ JSON summary")

        # Generate text report
        self._generate_text_report(
            monte_carlo_results,
            stress_test_results,
            long_time_results,
            integral_name
        )
        if verbose:
            print("  ✓ Text report")

        if verbose:
            print("=" * 70)
            print(f"Report generated in {self.output_dir}/")
            print("=" * 70)

    def _plot_error_distribution(self, results: Dict, integral_name: str):
        """Plot histogram of conservation errors."""
        if not HAS_MATPLOTLIB:
            return

        errors = results.get('errors', np.array([]))

        if len(errors) == 0:
            return

        fig, ax = plt.subplots(figsize=(10, 6))

        # Histogram
        ax.hist(errors, bins=50, edgecolor='black', alpha=0.7, color='steelblue')

        # Add vertical lines for statistics
        median = results.get('median_error', np.median(errors))
        p95 = results.get('p95_error', np.percentile(errors, 95))

        ax.axvline(median, color='red', linestyle='--', linewidth=2,
                   label=f'Median: {median:.2e}')
        ax.axvline(p95, color='orange', linestyle='--', linewidth=2,
                   label=f'95th percentile: {p95:.2e}')

        ax.set_xlabel(f'Conservation Error: |Δ{integral_name}|/|{integral_name}₀|', fontsize=12)
        ax.set_ylabel('Count', fontsize=12)
        ax.set_yscale('log')
        ax.set_title(f'Distribution of Conservation Errors\n({results.get("n_total", 0):,} trajectories)',
                     fontsize=14)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(os.path.join(self.figures_dir, 'error_distribution.png'), dpi=300)
        plt.savefig(os.path.join(self.figures_dir, 'error_distribution.pdf'))
        plt.close()

    def _plot_drift_analysis(self, results: Dict, integral_name: str):
        """Plot long-time drift evolution."""
        if not HAS_MATPLOTLIB:
            return

        times = results.get('times', np.array([]))
        drift_I = results.get('drift_I_history', np.array([]))
        drift_E = results.get('drift_E_history', np.array([]))

        if len(times) == 0 or len(drift_I) == 0:
            return

        fig, ax = plt.subplots(figsize=(12, 6))

        ax.semilogy(times, drift_I, label=f'{integral_name} drift', color='blue', alpha=0.7)
        ax.semilogy(times, drift_E, label='Energy drift', color='red', alpha=0.7, linestyle='--')

        ax.set_xlabel('Time (orbital periods)', fontsize=12)
        ax.set_ylabel('Relative Drift', fontsize=12)
        ax.set_title('Long-Time Drift Analysis', fontsize=14)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(os.path.join(self.figures_dir, 'long_time_drift.png'), dpi=300)
        plt.savefig(os.path.join(self.figures_dir, 'long_time_drift.pdf'))
        plt.close()

    def _plot_stress_test_summary(self, results: Dict, integral_name: str):
        """Plot stress test success rates."""
        if not HAS_MATPLOTLIB:
            return

        test_names = []
        success_rates = []

        for test_type, result in results.items():
            if hasattr(result, 'success_rate'):
                test_names.append(test_type.capitalize())
                success_rates.append(result.success_rate * 100)

        if not test_names:
            return

        fig, ax = plt.subplots(figsize=(8, 6))

        colors = ['steelblue', 'orange', 'green'][:len(test_names)]
        bars = ax.bar(test_names, success_rates, color=colors, alpha=0.7, edgecolor='black')

        # Add value labels on bars
        for bar, rate in zip(bars, success_rates):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{rate:.1f}%',
                   ha='center', va='bottom', fontsize=12, fontweight='bold')

        ax.set_ylabel('Success Rate (%)', fontsize=12)
        ax.set_title('Stress Test Success Rates', fontsize=14)
        ax.set_ylim([0, 105])
        ax.grid(True, axis='y', alpha=0.3)

        plt.tight_layout()
        plt.savefig(os.path.join(self.figures_dir, 'stress_test_summary.png'), dpi=300)
        plt.savefig(os.path.join(self.figures_dir, 'stress_test_summary.pdf'))
        plt.close()

    def _generate_statistics_table(self, results: Dict, integral_name: str):
        """Generate plain text statistics table."""
        output_file = os.path.join(self.tables_dir, 'statistics.txt')

        with open(output_file, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write(f"VALIDATION STATISTICS FOR {integral_name}\n")
            f.write("=" * 70 + "\n\n")

            f.write(f"Total Trajectories:      {results.get('n_total', 0):,}\n")
            f.write(f"Successful Integrations: {results.get('n_success', 0):,}\n")
            f.write(f"Conserved Trajectories:  {results.get('n_conserved', 0):,}\n")
            f.write(f"Success Rate:            {100*results.get('success_rate', 0):.2f}%\n")
            f.write("\n")

            f.write("Error Statistics:\n")
            f.write("-" * 70 + "\n")
            f.write(f"  Mean:              {results.get('mean_error', 0):.4e}\n")
            f.write(f"  Median:            {results.get('median_error', 0):.4e}\n")
            f.write(f"  95th percentile:   {results.get('p95_error', 0):.4e}\n")
            f.write(f"  99th percentile:   {results.get('p99_error', 0):.4e}\n")
            f.write("\n")

            f.write(f"Computation Time:        {results.get('elapsed_time', 0):.1f} seconds\n")
            f.write("=" * 70 + "\n")

    def _generate_latex_table(self, results: Dict, integral_name: str):
        """Generate LaTeX table for publication."""
        output_file = os.path.join(self.tables_dir, 'validation_table.tex')

        latex = r"""\begin{table}[h]
\centering
\caption{Statistical Validation Results for $""" + integral_name + r"""$}
\label{tab:validation_""" + integral_name.replace('_', '') + r"""}
\begin{tabular}{lc}
\hline
\textbf{Metric} & \textbf{Value} \\
\hline
Total Trajectories & """ + f"{results.get('n_total', 0):,}" + r""" \\
Successful Integrations & """ + f"{results.get('n_success', 0):,}" + r""" \\
Conserved Trajectories & """ + f"{results.get('n_conserved', 0):,}" + r""" \\
Success Rate & """ + f"{100*results.get('success_rate', 0):.1f}\\%" + r""" \\
\hline
Mean Error & $""" + f"{results.get('mean_error', 0):.2e}" + r"""$ \\
Median Error & $""" + f"{results.get('median_error', 0):.2e}" + r"""$ \\
95th Percentile Error & $""" + f"{results.get('p95_error', 0):.2e}" + r"""$ \\
99th Percentile Error & $""" + f"{results.get('p99_error', 0):.2e}" + r"""$ \\
\hline
\end{tabular}
\end{table}
"""

        with open(output_file, 'w') as f:
            f.write(latex)

    def _generate_json_summary(
        self,
        monte_carlo_results: Optional[Dict],
        stress_test_results: Optional[Dict],
        long_time_results: Optional[Dict],
        integral_name: str
    ):
        """Generate JSON summary of all results."""
        summary = {
            'integral_name': integral_name,
            'monte_carlo': {},
            'stress_tests': {},
            'long_time': {}
        }

        if monte_carlo_results:
            summary['monte_carlo'] = {
                'n_total': int(monte_carlo_results.get('n_total', 0)),
                'success_rate': float(monte_carlo_results.get('success_rate', 0)),
                'mean_error': float(monte_carlo_results.get('mean_error', 0)),
                'median_error': float(monte_carlo_results.get('median_error', 0)),
                'p95_error': float(monte_carlo_results.get('p95_error', 0))
            }

        if stress_test_results:
            for test_type, result in stress_test_results.items():
                if hasattr(result, 'success_rate'):
                    summary['stress_tests'][test_type] = {
                        'n_tested': int(result.n_tested),
                        'success_rate': float(result.success_rate),
                        'max_drift': float(result.max_drift)
                    }

        if long_time_results:
            summary['long_time'] = {
                'max_drift_I': float(long_time_results.get('max_drift_I', 0)),
                'max_drift_E': float(long_time_results.get('max_drift_E', 0)),
                'is_bounded': bool(long_time_results.get('is_bounded', False))
            }

        output_file = os.path.join(self.data_dir, 'summary.json')
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)

    def _generate_text_report(
        self,
        monte_carlo_results: Optional[Dict],
        stress_test_results: Optional[Dict],
        long_time_results: Optional[Dict],
        integral_name: str
    ):
        """Generate comprehensive text report."""
        output_file = os.path.join(self.output_dir, 'validation_report.txt')

        with open(output_file, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write(f"VALIDATION REPORT FOR {integral_name}\n")
            f.write("=" * 70 + "\n\n")

            if monte_carlo_results:
                f.write("MONTE CARLO VALIDATION\n")
                f.write("-" * 70 + "\n")
                f.write(str(monte_carlo_results.get('__str__', '')))
                f.write("\n\n")

            if stress_test_results:
                f.write("STRESS TEST RESULTS\n")
                f.write("-" * 70 + "\n")
                for test_type, result in stress_test_results.items():
                    f.write(f"\n{test_type.upper()}:\n")
                    f.write(str(result))
                    f.write("\n")
                f.write("\n")

            if long_time_results:
                f.write("LONG-TIME VALIDATION\n")
                f.write("-" * 70 + "\n")
                f.write(str(long_time_results.get('__str__', '')))
                f.write("\n\n")

            f.write("=" * 70 + "\n")
            f.write("END OF REPORT\n")
            f.write("=" * 70 + "\n")


def compute_confidence_intervals(
    errors: np.ndarray,
    confidence: float = 0.95,
    n_bootstrap: int = 10000
) -> Dict:
    """
    Compute confidence intervals for error statistics via bootstrap.

    Args:
        errors: Array of errors
        confidence: Confidence level (0.95 = 95%)
        n_bootstrap: Number of bootstrap samples

    Returns:
        Dictionary with confidence intervals
    """
    n_samples = len(errors)

    median_samples = []
    mean_samples = []

    for _ in range(n_bootstrap):
        sample = np.random.choice(errors, size=n_samples, replace=True)
        median_samples.append(np.median(sample))
        mean_samples.append(np.mean(sample))

    alpha = 1 - confidence
    median_ci = np.percentile(median_samples, [100*alpha/2, 100*(1-alpha/2)])
    mean_ci = np.percentile(mean_samples, [100*alpha/2, 100*(1-alpha/2)])

    return {
        'median': float(np.median(errors)),
        'median_ci_lower': float(median_ci[0]),
        'median_ci_upper': float(median_ci[1]),
        'mean': float(np.mean(errors)),
        'mean_ci_lower': float(mean_ci[0]),
        'mean_ci_upper': float(mean_ci[1]),
        'confidence': confidence
    }
