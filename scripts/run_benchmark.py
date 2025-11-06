#!/usr/bin/env python3
"""
Benchmark Harness for CR3BP Integrator Testing

Runs integration benchmarks with pluggable backend integrators,
collecting performance metrics and validating conservation laws.
"""

import argparse
import json
import time
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.python.integrators.base import IntegratorBase
from src.python.utils.dynamics import (
    calculate_jacobi_constant,
    calculate_energy
)
from src.python.utils.coordinates import (
    transform_trajectory_to_inertial,
    corotating_to_inertial
)


class BenchmarkHarness:
    """
    Benchmark harness for integrator testing.

    Loads specifications from YAML, runs integrations with specified
    backend, collects metrics, and validates results.
    """

    def __init__(self, spec_path: str, backend: str, verbose: bool = False):
        """
        Initialize benchmark harness.

        Args:
            spec_path: Path to YAML specification file
            backend: Integrator backend name
            verbose: Enable verbose output
        """
        self.spec_path = Path(spec_path)
        self.backend_name = backend
        self.verbose = verbose
        self.spec = self._load_specification()
        self.integrator = self._create_integrator()

    def _load_specification(self) -> Dict[str, Any]:
        """Load and validate YAML specification."""
        if not self.spec_path.exists():
            raise FileNotFoundError(f"Specification not found: {self.spec_path}")

        with open(self.spec_path, 'r') as f:
            spec = yaml.safe_load(f)

        if self.verbose:
            print(f"Loaded specification: {spec['system']['name']}")

        return spec

    def _create_integrator(self) -> IntegratorBase:
        """Create integrator instance based on backend name."""
        if self.backend_name.lower() == "ias15":
            from src.python.integrators.ias15 import IAS15Integrator
            mu = self.spec['system']['mu']
            tol = self.spec['integration'].get('tolerance', 1e-14)
            return IAS15Integrator(mu=mu, tolerance=tol)
        else:
            raise ValueError(f"Unknown backend: {self.backend_name}")

    def _get_initial_state(self) -> np.ndarray:
        """Extract initial state from specification."""
        ic = self.spec['initial_conditions']
        pos = np.array(ic['position'])
        vel = np.array(ic['velocity'])
        return np.concatenate([pos, vel])

    def run(self) -> Dict[str, Any]:
        """
        Run the benchmark integration.

        Returns:
            Dictionary with results and metrics
        """
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Running benchmark: {self.backend_name}")
            print(f"{'='*60}\n")

        # Get parameters
        y0 = self._get_initial_state()
        t_final = self.spec['integration']['duration']
        dt_output = self.spec['integration'].get('output_interval', t_final / 1000)

        # Print initial conditions
        if self.verbose:
            print(f"Initial state: {y0}")
            print(f"Integration time: 0 -> {t_final:.2f}")
            print(f"Output interval: {dt_output:.4f}")

        # Compute initial quantities
        mu = self.spec['system']['mu']
        jacobi_initial = calculate_jacobi_constant(y0, mu)
        energy_initial = calculate_energy(y0, mu)

        if self.verbose:
            print(f"\nInitial Jacobi constant: {jacobi_initial:.15e}")
            print(f"Initial energy: {energy_initial:.15e}\n")

        # Run integration
        start_time = time.perf_counter()

        try:
            result = self.integrator.integrate(
                initial_state=y0,
                duration=t_final,
                output_interval=dt_output
            )
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'backend': self.backend_name
            }

        wall_time = time.perf_counter() - start_time

        if self.verbose:
            print(f"Integration completed in {wall_time:.3f} seconds")
            print(f"Number of output points: {len(result.times)}")

        # Extract trajectory
        times = result.times
        states = result.states_corotating

        # Compute conservation metrics
        jacobi_values = np.array([calculate_jacobi_constant(state, mu) for state in states])
        energy_values = np.array([calculate_energy(state, mu) for state in states])

        jacobi_metrics = {
            'max_absolute_drift': np.max(np.abs(jacobi_values - jacobi_initial)),
            'max_relative_drift': np.max(np.abs((jacobi_values - jacobi_initial) / jacobi_initial)),
            'mean_absolute_drift': np.mean(np.abs(jacobi_values - jacobi_initial)),
            'std_drift': np.std(jacobi_values - jacobi_initial)
        }

        energy_metrics = {
            'max_absolute_error': np.max(np.abs(energy_values - energy_initial)),
            'max_relative_error': np.max(np.abs((energy_values - energy_initial) / energy_initial)),
            'mean_absolute_error': np.mean(np.abs(energy_values - energy_initial)),
            'std_error': np.std(energy_values - energy_initial)
        }

        # Print metrics
        if self.verbose:
            print(f"\nConservation Metrics:")
            print(f"  Jacobi drift (abs): {jacobi_metrics['max_absolute_drift']:.3e}")
            print(f"  Jacobi drift (rel): {jacobi_metrics['max_relative_drift']:.3e}")
            print(f"  Energy drift (abs): {energy_metrics['max_absolute_error']:.3e}")
            print(f"  Energy drift (rel): {energy_metrics['max_relative_error']:.3e}")

        # Validate against criteria
        validation_results = self._validate_results(
            jacobi_metrics, energy_metrics, wall_time
        )

        if self.verbose:
            print(f"\nValidation: {'PASS' if validation_results['passed'] else 'FAIL'}")
            for check, passed in validation_results['checks'].items():
                status = "✓" if passed else "✗"
                print(f"  {status} {check}")

        # Transform to inertial frame if requested
        states_inertial = None
        if self.spec['output'].get('save_inertial_frame', False):
            states_inertial = transform_trajectory_to_inertial(states, times)

        # Compile results
        results = {
            'success': True,
            'backend': self.backend_name,
            'specification': str(self.spec_path),
            'system': self.spec['system']['name'],
            'mu': mu,
            'duration': t_final,
            'n_points': len(times),
            'wall_time': wall_time,
            'jacobi_metrics': jacobi_metrics,
            'energy_metrics': energy_metrics,
            'validation': validation_results,
            'initial_state': y0.tolist(),
            'jacobi_initial': float(jacobi_initial),
            'energy_initial': float(energy_initial),
            'trajectory': {
                'times': times.tolist() if len(times) < 10000 else 'truncated',
                'states_corotating': states.tolist() if len(states) < 10000 else 'truncated',
                'states_inertial': states_inertial.tolist() if states_inertial is not None and len(states_inertial) < 10000 else 'truncated'
            }
        }

        return results

    def _validate_results(
        self,
        jacobi_metrics: Dict[str, float],
        energy_metrics: Dict[str, float],
        wall_time: float
    ) -> Dict[str, Any]:
        """
        Validate results against specification criteria.

        Args:
            jacobi_metrics: Jacobi drift metrics
            energy_metrics: Energy conservation metrics
            wall_time: Wall clock time in seconds

        Returns:
            Dictionary with validation results
        """
        val_spec = self.spec['validation']
        perf_spec = self.spec['performance']

        checks = {}

        # Check Jacobi drift
        if 'jacobi_drift' in val_spec:
            max_allowed = val_spec['jacobi_drift']['max_relative']
            actual = jacobi_metrics['max_relative_drift']
            checks['jacobi_drift'] = bool(actual < max_allowed)

        # Check energy error
        if 'energy_error' in val_spec:
            max_allowed = val_spec['energy_error']['max_relative']
            actual = energy_metrics['max_relative_error']
            checks['energy_error'] = bool(actual < max_allowed)

        # Check wall time
        if 'max_wall_time' in perf_spec:
            checks['wall_time'] = bool(wall_time < perf_spec['max_wall_time'])

        passed = bool(all(checks.values()))

        return {
            'passed': passed,
            'checks': checks
        }

    def save_results(self, results: Dict[str, Any], output_path: str):
        """
        Save results to JSON file.

        Args:
            results: Results dictionary
            output_path: Path to output file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        if self.verbose:
            print(f"\nResults saved to: {output_path}")


def main():
    """Main entry point for benchmark harness."""
    parser = argparse.ArgumentParser(
        description="Run CR3BP integrator benchmarks"
    )
    parser.add_argument(
        '--backend',
        type=str,
        required=True,
        help='Integrator backend (e.g., ias15, yoshida8)'
    )
    parser.add_argument(
        '--spec',
        type=str,
        required=True,
        help='Path to YAML specification file'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Path to output JSON file (default: results/<backend>_<spec>.json)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Create output path if not specified
    if args.output is None:
        spec_name = Path(args.spec).stem
        args.output = f"results/{args.backend}_{spec_name}.json"

    # Create and run harness
    try:
        harness = BenchmarkHarness(
            spec_path=args.spec,
            backend=args.backend,
            verbose=args.verbose
        )

        results = harness.run()

        # Save results
        harness.save_results(results, args.output)

        # Exit with appropriate code
        if results['success'] and results.get('validation', {}).get('passed', False):
            print("\n✓ Benchmark PASSED")
            sys.exit(0)
        else:
            print("\n✗ Benchmark FAILED")
            sys.exit(1)

    except Exception as e:
        print(f"\n✗ Benchmark ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == '__main__':
    main()
