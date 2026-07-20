"""Cross-evaluate production KS flow against independent Kepler references."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import brentq

from kepler_benchmarks import KeplerBenchmark
from kepler_reference import cartesian_state_at_time
from rebound_reference import propagate_kepler_rebound
from src.python.ks import (
    KSPhaseState,
    KeplerPhaseState,
    NegativeEnergyKSSystem,
    lift_cotangent,
    project_cotangent,
)


FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class KSBenchmarkEvaluation:
    """Evidence metrics and checkpoint states for one locked benchmark."""

    case_id: str
    elapsed_times: FloatArray
    spinor_times: FloatArray
    ks_states: FloatArray
    analytic_states: FloatArray
    rebound_states: FloatArray
    metrics: dict[str, float]
    rebound_version: str


def _spinor_times_for_physical_times(
    system: NegativeEnergyKSSystem,
    initial: KSPhaseState,
    elapsed_times: FloatArray,
) -> FloatArray:
    quotient_period = system.quotient_period()
    physical_period = system.physical_period(initial)
    result = np.empty_like(elapsed_times)
    time_tolerance = 64.0 * np.finfo(float).eps * max(1.0, physical_period)

    for index, elapsed in enumerate(elapsed_times):
        if abs(elapsed) <= time_tolerance:
            result[index] = 0.0
        elif abs(elapsed - physical_period) <= time_tolerance:
            result[index] = quotient_period
        else:
            result[index] = brentq(
                lambda spinor_time: float(
                    system.physical_time(initial, spinor_time) - elapsed
                ),
                0.0,
                quotient_period,
                xtol=1e-14,
                rtol=4.0 * np.finfo(float).eps,
            )
    return result


def evaluate_ks_benchmark(benchmark: KeplerBenchmark) -> KSBenchmarkEvaluation:
    """Compare exact canonical KS flow with analytic and REBOUND references."""
    elements = benchmark.elements
    initial_array = cartesian_state_at_time(elements, elements.epoch)
    reduced_mass = float(benchmark.reduced_mass)
    if not np.isfinite(reduced_mass) or reduced_mass <= 0.0:
        raise ValueError("benchmark reduced_mass must be finite and positive")
    physical_initial = KeplerPhaseState(
        initial_array[:3], reduced_mass * initial_array[3:]
    )
    kappa = reduced_mass * elements.mu
    energy = -kappa / (2.0 * elements.semi_major_axis)
    system = NegativeEnergyKSSystem(
        kappa=kappa,
        energy=energy,
        reduced_mass=reduced_mass,
    )
    lifted = lift_cotangent(physical_initial)

    elapsed_times = np.asarray(benchmark.period_fractions, dtype=float) * elements.period
    spinor_times = _spinor_times_for_physical_times(system, lifted, elapsed_times)
    q_values, Q_values = system.flow(lifted, spinor_times)

    ks_states = np.empty((elapsed_times.size, 6), dtype=float)
    regularized_values = np.empty(elapsed_times.size, dtype=float)
    momentum_map_values = np.empty(elapsed_times.size, dtype=float)
    for index, (q_value, Q_value) in enumerate(zip(q_values, Q_values)):
        spinor_state = KSPhaseState(q_value, Q_value)
        projected = project_cotangent(spinor_state)
        ks_states[index, :3] = projected.x
        ks_states[index, 3:] = projected.p / reduced_mass
        regularized_values[index] = system.regularized_hamiltonian(spinor_state)
        momentum_map_values[index] = spinor_state.xi

    analytic_states = np.stack(
        [
            cartesian_state_at_time(elements, elements.epoch + elapsed)
            for elapsed in elapsed_times
        ]
    )
    rebound_result = propagate_kepler_rebound(
        initial_array,
        elements.mu,
        elapsed_times,
    )

    analytic_delta = ks_states - analytic_states
    rebound_delta = ks_states - rebound_result.states
    closure_delta = ks_states[-1] - ks_states[0]
    radii = np.linalg.norm(ks_states[:, :3], axis=1)
    expected_energy = energy
    physical_energies = (
        0.5 * reduced_mass * np.sum(ks_states[:, 3:] ** 2, axis=1)
        - kappa / radii
    )
    metrics = {
        "analytic_state_error_max": float(np.max(np.abs(analytic_delta))),
        "analytic_state_error_rms": float(np.sqrt(np.mean(analytic_delta**2))),
        "rebound_state_error_max": float(np.max(np.abs(rebound_delta))),
        "rebound_state_error_rms": float(np.sqrt(np.mean(rebound_delta**2))),
        "closure_position_error": float(np.linalg.norm(closure_delta[:3])),
        "closure_velocity_error": float(np.linalg.norm(closure_delta[3:])),
        "regularized_hamiltonian_abs_max": float(
            np.max(np.abs(regularized_values))
        ),
        "momentum_map_abs_max": float(np.max(np.abs(momentum_map_values))),
        "physical_energy_abs_error_max": float(
            np.max(np.abs(physical_energies - expected_energy))
        ),
        "period_relative_error": float(
            abs(system.physical_period(lifted) - elements.period) / elements.period
        ),
        "minimum_radius": float(np.min(radii)),
    }
    return KSBenchmarkEvaluation(
        case_id=benchmark.case_id,
        elapsed_times=elapsed_times,
        spinor_times=spinor_times,
        ks_states=ks_states,
        analytic_states=analytic_states,
        rebound_states=rebound_result.states,
        metrics=metrics,
        rebound_version=rebound_result.rebound_version,
    )
