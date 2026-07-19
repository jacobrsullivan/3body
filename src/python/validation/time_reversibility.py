"""
Time Reversibility Tests for Integrators (WP1 Phase 3).

Tests the time-reversibility property of numerical integrators:
1. Integrate forward from t=0 to t=T
2. Negate velocities at t=T
3. Integrate backward from t=T to t=0
4. Compare final state with initial state

For symplectic integrators, reversibility error should be extremely small.
Target for WP1 Tier 2: RMS position error < 10⁻²⁰

Mathematical Background:
========================

Time Reversal Symmetry:
-----------------------
For Hamiltonian systems, dynamics are time-reversible:
    If (q(t), p(t)) is a solution, then (q(-t), -p(-t)) is also a solution.

A good numerical integrator should preserve this symmetry:
    Φ_h ∘ R ∘ Φ_h ∘ R = Identity

where Φ_h is the integrator map with stepsize h, and R is velocity reversal.

Error Metrics:
--------------
- Position RMS error: sqrt(mean(||q_final - q_initial||²))
- Velocity RMS error: sqrt(mean(||v_final - v_initial||²))
- Energy error: |H_final - H_initial|

References:
-----------
- Hairer, Lubich, Wanner (2006): "Geometric Numerical Integration"
- Sanz-Serna & Calvo (1994): "Numerical Hamiltonian Problems"
- WP1 Specification, Section 2.5 (Quality Assurance & Validation)
"""

from dataclasses import dataclass
from typing import Protocol, Dict, Any, Callable
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class ReversibilityResult:
    """
    Results from time reversibility test.

    Attributes:
        forward_time: Integration time forward
        position_rms_error: RMS error in positions
        velocity_rms_error: RMS error in velocities
        max_position_error: Maximum position error
        max_velocity_error: Maximum velocity error
        energy_error: Final energy error (if Hamiltonian provided)
        passes_tier1: Whether meets Tier 1 target (< 10⁻¹⁴)
        passes_tier2: Whether meets Tier 2 target (< 10⁻²⁰)
        metadata: Additional information
    """
    forward_time: float
    position_rms_error: float
    velocity_rms_error: float
    max_position_error: float
    max_velocity_error: float
    energy_error: float
    passes_tier1: bool
    passes_tier2: bool
    metadata: Dict[str, Any]


class IntegratorProtocol(Protocol):
    """Protocol for integrators (duck typing)."""

    def integrate(self, initial_state: np.ndarray, duration: float, output_interval: float):
        """Integrate trajectory."""
        ...


class TimeReversibilityTester:
    """
    Test time-reversibility of numerical integrators.

    Performs forward-backward integration and measures error.
    """

    def __init__(
        self,
        hamiltonian=None,
        tier1_threshold: float = 1e-14,
        tier2_threshold: float = 1e-20,
        reversal_operator: Callable[[np.ndarray], np.ndarray] | None = None,
    ):
        """
        Initialize reversibility tester.

        Args:
            hamiltonian: Optional Hamiltonian function H(state) → scalar
            tier1_threshold: Tier 1 error threshold
            tier2_threshold: Tier 2 error threshold
            reversal_operator: State-space involution used for time reversal
        """
        self.hamiltonian = hamiltonian
        self.tier1_threshold = tier1_threshold
        self.tier2_threshold = tier2_threshold
        self.reversal_operator = reversal_operator or self._default_reversal_operator

    @staticmethod
    def _default_reversal_operator(state: np.ndarray) -> np.ndarray:
        """Canonical time reversal for inertial position/velocity states."""
        reversed_state = state.copy()
        reversed_state[3:6] = -reversed_state[3:6]
        return reversed_state

    def test_reversibility(
        self,
        integrator: IntegratorProtocol,
        initial_state: np.ndarray,
        forward_time: float,
        output_interval: float = None
    ) -> ReversibilityResult:
        """
        Perform time reversibility test.

        Args:
            integrator: Integrator object with .integrate() method
            initial_state: Initial state [x, y, z, vx, vy, vz]
            forward_time: Time to integrate forward
            output_interval: Output sampling interval (default: forward_time/100)

        Returns:
            ReversibilityResult
        """
        if output_interval is None:
            output_interval = forward_time / 100.0

        logger.info(f"Time reversibility test: T={forward_time}")
        logger.info(f"Initial state: {initial_state}")

        # 1. Forward integration
        logger.info("Step 1: Forward integration...")
        result_forward = integrator.integrate(
            initial_state,
            forward_time,
            output_interval
        )

        if not result_forward.success:
            raise RuntimeError(f"Forward integration failed: {result_forward.message}")

        # Get final state from forward integration
        state_at_T = result_forward.states_corotating[-1]
        logger.info(f"State at T: {state_at_T}")

        # 2. Apply the configured time-reversal symmetry.
        logger.info("Step 2: Time reversal...")
        state_reversed = self.reversal_operator(state_at_T)
        logger.info(f"Reversed state: {state_reversed}")

        # 3. Backward integration
        logger.info("Step 3: Backward integration...")
        result_backward = integrator.integrate(
            state_reversed,
            forward_time,
            output_interval
        )

        if not result_backward.success:
            raise RuntimeError(f"Backward integration failed: {result_backward.message}")

        # Get final state from backward integration
        state_final = result_backward.states_corotating[-1]

        # Re-apply the involution to compare with the initial state.
        state_final_unreversed = self.reversal_operator(state_final)

        logger.info(f"Final state (unreversed): {state_final_unreversed}")

        # 4. Compute errors
        position_error = state_final_unreversed[:3] - initial_state[:3]
        velocity_error = state_final_unreversed[3:6] - initial_state[3:6]

        position_rms = np.sqrt(np.mean(position_error**2))
        velocity_rms = np.sqrt(np.mean(velocity_error**2))

        max_position_error = np.max(np.abs(position_error))
        max_velocity_error = np.max(np.abs(velocity_error))

        # Energy error (if Hamiltonian provided)
        if self.hamiltonian is not None:
            H_initial = self.hamiltonian(initial_state)
            H_final = self.hamiltonian(state_final_unreversed)
            energy_error = np.abs(H_final - H_initial)
        else:
            energy_error = 0.0

        # Check thresholds
        passes_tier1 = position_rms < self.tier1_threshold
        passes_tier2 = position_rms < self.tier2_threshold

        # Metadata
        metadata = {
            'initial_state': initial_state.copy(),
            'state_at_T': state_at_T.copy(),
            'state_reversed': state_reversed.copy(),
            'state_final': state_final_unreversed.copy(),
            'position_error': position_error,
            'velocity_error': velocity_error,
            'forward_steps': len(result_forward.times),
            'backward_steps': len(result_backward.times),
        }

        logger.info(f"Results:")
        logger.info(f"  Position RMS error: {position_rms:.2e}")
        logger.info(f"  Velocity RMS error: {velocity_rms:.2e}")
        logger.info(f"  Max position error: {max_position_error:.2e}")
        logger.info(f"  Energy error: {energy_error:.2e}")
        logger.info(f"  Passes Tier 1 (< {self.tier1_threshold:.0e}): {passes_tier1}")
        logger.info(f"  Passes Tier 2 (< {self.tier2_threshold:.0e}): {passes_tier2}")

        return ReversibilityResult(
            forward_time=forward_time,
            position_rms_error=position_rms,
            velocity_rms_error=velocity_rms,
            max_position_error=max_position_error,
            max_velocity_error=max_velocity_error,
            energy_error=energy_error,
            passes_tier1=passes_tier1,
            passes_tier2=passes_tier2,
            metadata=metadata
        )

    def test_multiple_orbits(
        self,
        integrator: IntegratorProtocol,
        initial_states: list,
        forward_time: float,
        output_interval: float = None
    ) -> list:
        """
        Test reversibility on multiple orbits.

        Args:
            integrator: Integrator object
            initial_states: List of initial states
            forward_time: Forward integration time
            output_interval: Output interval

        Returns:
            List of ReversibilityResult objects
        """
        results = []

        for i, initial_state in enumerate(initial_states):
            logger.info(f"\nTesting orbit {i+1}/{len(initial_states)}")
            try:
                result = self.test_reversibility(
                    integrator,
                    initial_state,
                    forward_time,
                    output_interval
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Orbit {i+1} failed: {e}")
                # Continue with other orbits

        return results

    def summarize_results(self, results: list) -> Dict[str, Any]:
        """
        Summarize results from multiple orbits.

        Args:
            results: List of ReversibilityResult objects

        Returns:
            Summary statistics dictionary
        """
        if not results:
            return {}

        position_errors = [r.position_rms_error for r in results]
        velocity_errors = [r.velocity_rms_error for r in results]

        tier1_pass_rate = sum(r.passes_tier1 for r in results) / len(results)
        tier2_pass_rate = sum(r.passes_tier2 for r in results) / len(results)

        summary = {
            'n_orbits': len(results),
            'position_rms_mean': np.mean(position_errors),
            'position_rms_median': np.median(position_errors),
            'position_rms_max': np.max(position_errors),
            'position_rms_95percentile': np.percentile(position_errors, 95),
            'velocity_rms_mean': np.mean(velocity_errors),
            'velocity_rms_median': np.median(velocity_errors),
            'tier1_pass_rate': tier1_pass_rate,
            'tier2_pass_rate': tier2_pass_rate,
        }

        logger.info("\n" + "="*60)
        logger.info("REVERSIBILITY TEST SUMMARY")
        logger.info("="*60)
        logger.info(f"Number of orbits: {summary['n_orbits']}")
        logger.info(f"Position RMS (mean): {summary['position_rms_mean']:.2e}")
        logger.info(f"Position RMS (median): {summary['position_rms_median']:.2e}")
        logger.info(f"Position RMS (95th percentile): {summary['position_rms_95percentile']:.2e}")
        logger.info(f"Tier 1 pass rate: {tier1_pass_rate:.1%}")
        logger.info(f"Tier 2 pass rate: {tier2_pass_rate:.1%}")
        logger.info("="*60)

        return summary


def create_cr3bp_reversibility_tester(mu: float) -> TimeReversibilityTester:
    """
    Create reversibility tester for CR3BP.

    Args:
        mu: Mass parameter

    Returns:
        TimeReversibilityTester configured for CR3BP
    """
    from ..utils.dynamics import calculate_jacobi_constant

    def hamiltonian_cr3bp(state: np.ndarray) -> float:
        """CR3BP Jacobi constant."""
        return -calculate_jacobi_constant(state, mu)

    def cr3bp_rotating_frame_reversal(state: np.ndarray) -> np.ndarray:
        """CR3BP rotating-frame symmetry: (x,y,z,vx,vy,vz)->(x,-y,z,-vx,vy,-vz)."""
        reversed_state = state.copy()
        reversed_state[1] = -reversed_state[1]
        reversed_state[3] = -reversed_state[3]
        reversed_state[5] = -reversed_state[5]
        return reversed_state

    return TimeReversibilityTester(
        hamiltonian=hamiltonian_cr3bp,
        tier1_threshold=1e-14,
        tier2_threshold=1e-20,
        reversal_operator=cr3bp_rotating_frame_reversal,
    )
