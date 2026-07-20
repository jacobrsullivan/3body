"""External REBOUND/IAS15 reference for the normalized Kepler problem.

The production KS implementation is not imported here.  A massless particle
is propagated around a fixed primary of mass ``mu`` with ``G = 1``; its
relative Cartesian state therefore satisfies
``r_ddot = -mu r / |r|^3``.  REBOUND is an independently maintained N-body
package and IAS15 supplies the external numerical implementation required by
the WP2Q-KS evidence contract.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

import numpy as np
from numpy.typing import ArrayLike, NDArray
import rebound


FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class ReboundReferenceResult:
    """Versioned REBOUND trajectory and its requested physical times."""

    times: FloatArray
    states: FloatArray
    rebound_version: str
    integrator: str
    epsilon: float


def propagate_kepler_rebound(
    initial_state: ArrayLike,
    mu: float,
    times: ArrayLike | Iterable[float],
    *,
    epsilon: float = 1e-14,
) -> ReboundReferenceResult:
    """Propagate a relative Kepler state at monotone non-negative times."""
    state = np.asarray(initial_state, dtype=float)
    if state.shape != (6,):
        raise ValueError("initial_state must have shape (6,)")
    if not np.all(np.isfinite(state)):
        raise ValueError("initial_state must contain only finite values")
    if not math.isfinite(mu) or mu <= 0.0:
        raise ValueError("mu must be finite and positive")
    if not math.isfinite(epsilon) or epsilon <= 0.0:
        raise ValueError("epsilon must be finite and positive")

    time_array = np.asarray(tuple(times), dtype=float)
    if time_array.ndim != 1 or time_array.size == 0:
        raise ValueError("times must be a non-empty one-dimensional sequence")
    if not np.all(np.isfinite(time_array)):
        raise ValueError("times must contain only finite values")
    if time_array[0] < 0.0 or np.any(np.diff(time_array) < 0.0):
        raise ValueError("times must be monotone and non-negative")

    simulation = rebound.Simulation()
    simulation.G = 1.0
    simulation.integrator = "ias15"
    simulation.ri_ias15.epsilon = float(epsilon)
    simulation.add(m=float(mu))
    simulation.add(
        m=0.0,
        x=float(state[0]),
        y=float(state[1]),
        z=float(state[2]),
        vx=float(state[3]),
        vy=float(state[4]),
        vz=float(state[5]),
    )

    states = np.empty((time_array.size, 6), dtype=float)
    for index, time in enumerate(time_array):
        simulation.integrate(float(time), exact_finish_time=1)
        primary, particle = simulation.particles
        states[index] = np.array(
            [
                particle.x - primary.x,
                particle.y - primary.y,
                particle.z - primary.z,
                particle.vx - primary.vx,
                particle.vy - primary.vy,
                particle.vz - primary.vz,
            ]
        )

    return ReboundReferenceResult(
        times=time_array,
        states=states,
        rebound_version=str(rebound.__version__),
        integrator="ias15",
        epsilon=float(epsilon),
    )
