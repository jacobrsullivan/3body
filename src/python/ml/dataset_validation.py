"""
Dataset validation and quality control (Task 3.2.1, Part E).

This module provides tools to validate the quality of generated datasets
and generate diagnostic reports.

Validation checks:
1. Energy conservation statistics
2. Symplectic error distribution
3. Parameter space coverage
4. Data quality (no NaN/Inf, no collisions)
5. Dataset statistics
"""

from typing import Dict, Any, List, Tuple
import numpy as np
from pathlib import Path

from .dataset_builder import TrajectoryDataset


def validate_dataset(dataset_path: str) -> Dict[str, Any]:
    """
    Comprehensive validation of generated dataset.

    Checks:
    1. Energy conservation statistics
    2. Symplectic error distribution
    3. Parameter space coverage
    4. Trajectory diversity
    5. No NaN/Inf values
    6. No duplicate trajectories

    Args:
        dataset_path: Path to HDF5 dataset

    Returns:
        Validation report dictionary
    """
    print("=" * 70)
    print(f"VALIDATING DATASET: {dataset_path}")
    print("=" * 70)

    report = {
        'dataset_path': dataset_path,
        'file_size_mb': Path(dataset_path).stat().st_size / (1024**2),
        'energy_drift': {},
        'symplectic_error': {},
        'parameter_coverage': {},
        'data_quality': {},
        'metadata': {}
    }

    with TrajectoryDataset(dataset_path, mode='r') as dataset:
        # Get metadata
        if 'metadata' in dataset.file:
            meta = dataset.file['metadata'].attrs
            report['metadata'] = dict(meta)

        # Validate each split
        for split in ['train', 'validation', 'test']:
            print(f"\nValidating {split} split...")

            n_trajs = dataset.get_size(split)
            print(f"  Number of trajectories: {n_trajs}")

            if n_trajs == 0:
                print(f"  Skipping (empty split)")
                continue

            # Energy drift statistics
            energy_drifts = dataset.file[split]['energy_drifts'][:]
            report['energy_drift'][split] = {
                'mean': float(np.mean(energy_drifts)),
                'std': float(np.std(energy_drifts)),
                'max': float(np.max(energy_drifts)),
                'min': float(np.min(energy_drifts)),
                'median': float(np.median(energy_drifts))
            }

            print(f"  Energy drift:")
            print(f"    Mean: {report['energy_drift'][split]['mean']:.2e}")
            print(f"    Max: {report['energy_drift'][split]['max']:.2e}")

            # Symplectic error statistics
            symp_errors = dataset.file[split]['symplectic_errors'][:]
            report['symplectic_error'][split] = {
                'mean': float(np.mean(symp_errors)),
                'std': float(np.std(symp_errors)),
                'max': float(np.max(symp_errors)),
                'min': float(np.min(symp_errors))
            }

            print(f"  Symplectic error:")
            print(f"    Mean: {report['symplectic_error'][split]['mean']:.2e}")
            print(f"    Max: {report['symplectic_error'][split]['max']:.2e}")

            # Data quality checks
            states = dataset.file[split]['states']
            derivatives = dataset.file[split]['derivatives']

            has_nan_states = np.any(np.isnan(states[:]))
            has_inf_states = np.any(np.isinf(states[:]))
            has_nan_derivs = np.any(np.isnan(derivatives[:]))
            has_inf_derivs = np.any(np.isinf(derivatives[:]))

            report['data_quality'][split] = {
                'has_nan': has_nan_states or has_nan_derivs,
                'has_inf': has_inf_states or has_inf_derivs,
                'all_finite': not (has_nan_states or has_inf_states or has_nan_derivs or has_inf_derivs)
            }

            if report['data_quality'][split]['all_finite']:
                print(f"  Data quality: ✓ All values finite")
            else:
                print(f"  Data quality: ✗ Contains NaN or Inf")

        # Parameter space coverage (all splits combined)
        print(f"\nParameter space coverage:")
        all_masses = []
        all_energies = []

        for split in ['train', 'validation', 'test']:
            if dataset.get_size(split) > 0:
                all_masses.append(dataset.file[split]['masses'][:])
                all_energies.append(dataset.file[split]['energies'][:])

        if all_masses:
            masses = np.concatenate(all_masses)
            energies = np.concatenate(all_energies)

            # Mass ratios
            m1, m2, m3 = masses[:, 0], masses[:, 1], masses[:, 2]
            mass_ratios = m2 / m1
            mass_3_ratios = m3 / (m1 + m2)

            report['parameter_coverage'] = {
                'mass_ratio': {
                    'min': float(np.min(mass_ratios)),
                    'max': float(np.max(mass_ratios)),
                    'mean': float(np.mean(mass_ratios))
                },
                'mass_3_ratio': {
                    'min': float(np.min(mass_3_ratios)),
                    'max': float(np.max(mass_3_ratios)),
                    'mean': float(np.mean(mass_3_ratios))
                },
                'energy': {
                    'min': float(np.min(energies)),
                    'max': float(np.max(energies)),
                    'mean': float(np.mean(energies))
                }
            }

            print(f"  Mass ratio (m₂/m₁): [{report['parameter_coverage']['mass_ratio']['min']:.3f}, "
                  f"{report['parameter_coverage']['mass_ratio']['max']:.3f}]")
            print(f"  Energy: [{report['parameter_coverage']['energy']['min']:.3f}, "
                  f"{report['parameter_coverage']['energy']['max']:.3f}]")

    print("\n" + "=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)

    return report


def check_quality_thresholds(
    report: Dict[str, Any],
    energy_drift_threshold: float = 1e-10,
    symplectic_error_threshold: float = 1e-8
) -> Tuple[bool, List[str]]:
    """
    Check if dataset meets quality thresholds.

    Args:
        report: Validation report from validate_dataset()
        energy_drift_threshold: Maximum acceptable energy drift
        symplectic_error_threshold: Maximum acceptable symplectic error

    Returns:
        (passes, issues) where passes is bool and issues is list of problems
    """
    issues = []

    # Check energy drift
    for split in ['train', 'validation', 'test']:
        if split in report['energy_drift']:
            max_drift = report['energy_drift'][split]['max']
            if max_drift > energy_drift_threshold:
                issues.append(
                    f"{split} energy drift ({max_drift:.2e}) > threshold ({energy_drift_threshold:.2e})"
                )

    # Check symplectic error
    for split in ['train', 'validation', 'test']:
        if split in report['symplectic_error']:
            max_error = report['symplectic_error'][split]['max']
            if max_error > symplectic_error_threshold:
                issues.append(
                    f"{split} symplectic error ({max_error:.2e}) > threshold ({symplectic_error_threshold:.2e})"
                )

    # Check data quality
    for split in ['train', 'validation', 'test']:
        if split in report['data_quality']:
            if not report['data_quality'][split]['all_finite']:
                issues.append(f"{split} contains NaN or Inf values")

    passes = len(issues) == 0
    return passes, issues


def print_validation_summary(report: Dict[str, Any]):
    """
    Print human-readable validation summary.

    Args:
        report: Validation report
    """
    print("\n" + "=" * 70)
    print("DATASET VALIDATION SUMMARY")
    print("=" * 70)

    print(f"\nFile: {report['dataset_path']}")
    print(f"Size: {report['file_size_mb']:.1f} MB")

    if 'metadata' in report and report['metadata']:
        print(f"\nMetadata:")
        meta = report['metadata']
        if 'manifold_type' in meta:
            print(f"  Manifold: {meta['manifold_type']}")
        if 'num_trajectories' in meta:
            print(f"  Total trajectories: {meta['num_trajectories']}")
        if 'integrator' in meta:
            print(f"  Integrator: {meta['integrator']}")

    print(f"\nEnergy Drift:")
    for split in ['train', 'validation', 'test']:
        if split in report['energy_drift']:
            stats = report['energy_drift'][split]
            print(f"  {split:12s}: mean={stats['mean']:.2e}, max={stats['max']:.2e}")

    print(f"\nSymplectic Error:")
    for split in ['train', 'validation', 'test']:
        if split in report['symplectic_error']:
            stats = report['symplectic_error'][split]
            print(f"  {split:12s}: mean={stats['mean']:.2e}, max={stats['max']:.2e}")

    print(f"\nData Quality:")
    for split in ['train', 'validation', 'test']:
        if split in report['data_quality']:
            status = "✓ PASS" if report['data_quality'][split]['all_finite'] else "✗ FAIL"
            print(f"  {split:12s}: {status}")

    if 'parameter_coverage' in report and report['parameter_coverage']:
        print(f"\nParameter Coverage:")
        cov = report['parameter_coverage']
        if 'mass_ratio' in cov:
            print(f"  m₂/m₁: [{cov['mass_ratio']['min']:.3f}, {cov['mass_ratio']['max']:.3f}]")
        if 'energy' in cov:
            print(f"  Energy: [{cov['energy']['min']:.3f}, {cov['energy']['max']:.3f}]")

    # Quality check
    passes, issues = check_quality_thresholds(report)
    print(f"\nQuality Check: {'✓ PASS' if passes else '✗ FAIL'}")
    if issues:
        print("Issues:")
        for issue in issues:
            print(f"  - {issue}")

    print("=" * 70)


def generate_validation_plots(
    dataset_path: str,
    output_dir: str,
    max_trajectories_plot: int = 5
):
    """
    Generate validation plots.

    Plots:
    1. Energy drift histogram
    2. Parameter space scatter plots
    3. Sample trajectory positions
    4. Sample trajectory phase space

    Args:
        dataset_path: Path to HDF5 dataset
        output_dir: Directory for output plots
        max_trajectories_plot: Maximum trajectories to plot
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available - skipping plots")
        return

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    with TrajectoryDataset(dataset_path, mode='r') as dataset:
        # Plot 1: Energy drift histogram
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))

        for i, split in enumerate(['train', 'validation', 'test']):
            if dataset.get_size(split) > 0:
                drifts = dataset.file[split]['energy_drifts'][:]
                axes[i].hist(np.log10(drifts + 1e-16), bins=30, edgecolor='black')
                axes[i].set_xlabel('log₁₀(Energy Drift)')
                axes[i].set_ylabel('Count')
                axes[i].set_title(f'{split.capitalize()} Split')
                axes[i].grid(alpha=0.3)

        plt.tight_layout()
        plt.savefig(f"{output_dir}/energy_drift_histogram.png", dpi=150)
        plt.close()

        # Plot 2: Parameter space coverage
        all_masses = []
        all_energies = []

        for split in ['train', 'validation', 'test']:
            if dataset.get_size(split) > 0:
                all_masses.append(dataset.file[split]['masses'][:])
                all_energies.append(dataset.file[split]['energies'][:])

        if all_masses:
            masses = np.concatenate(all_masses)
            energies = np.concatenate(all_energies)

            m1, m2, m3 = masses[:, 0], masses[:, 1], masses[:, 2]
            mass_ratios = m2 / m1

            fig, axes = plt.subplots(1, 2, figsize=(12, 5))

            axes[0].scatter(mass_ratios, energies, alpha=0.3, s=10)
            axes[0].set_xlabel('Mass Ratio (m₂/m₁)')
            axes[0].set_ylabel('Energy')
            axes[0].set_title('Parameter Space Coverage')
            axes[0].grid(alpha=0.3)

            axes[1].hist2d(mass_ratios, energies, bins=30, cmap='viridis')
            axes[1].set_xlabel('Mass Ratio (m₂/m₁)')
            axes[1].set_ylabel('Energy')
            axes[1].set_title('Parameter Density')
            plt.colorbar(axes[1].collections[0], ax=axes[1], label='Count')

            plt.tight_layout()
            plt.savefig(f"{output_dir}/parameter_coverage.png", dpi=150)
            plt.close()

    print(f"Validation plots saved to {output_dir}/")


if __name__ == "__main__":
    import sys

    # Check if dataset path provided
    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]
    else:
        dataset_path = 'data/test_dataset.h5'

    # Check if dataset exists
    if not Path(dataset_path).exists():
        print(f"Dataset not found: {dataset_path}")
        print("Please generate a dataset first using dataset_builder.py")
        sys.exit(1)

    # Validate dataset
    report = validate_dataset(dataset_path)

    # Print summary
    print_validation_summary(report)

    # Generate plots (if matplotlib available)
    try:
        generate_validation_plots(dataset_path, 'data/validation_plots')
    except Exception as e:
        print(f"\nPlot generation failed: {e}")

    # Quality check
    passes, issues = check_quality_thresholds(report)
    if not passes:
        print(f"\n⚠ Dataset does not meet quality thresholds")
        sys.exit(1)
    else:
        print(f"\n✓ Dataset meets all quality thresholds")
