"""Production and independent-reference propagators for N3BP qualification."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike
from scipy.integrate import solve_ivp

from .contract import (
    FloatArray,
    InertialState,
    StateLike,
    SystemParameters,
    as_state_vector,
)
from .dynamics import newtonian_rhs


def _validated_times(times: ArrayLike) -> FloatArray:
    result = np.asarray(times, dtype=np.float64)
    if result.ndim != 1 or result.size < 2:
        raise ValueError(
            "times must be a one-dimensional array with at least two values"
        )
    if not np.all(np.isfinite(result)):
        raise ValueError("times must contain only finite values")
    differences = np.diff(result)
    if not (np.all(differences > 0.0) or np.all(differences < 0.0)):
        raise ValueError("times must be strictly monotonic")
    return np.array(result, copy=True)


@dataclass(frozen=True)
class Trajectory:
    times: ArrayLike
    states: ArrayLike
    engine: str

    def __post_init__(self) -> None:
        times = _validated_times(self.times)
        states = np.asarray(self.states, dtype=np.float64)
        if states.shape != (times.size, 18):
            raise ValueError(
                f"states must have shape ({times.size}, 18), got {states.shape}"
            )
        if not np.all(np.isfinite(states)):
            raise ValueError("states must contain only finite values")
        states = np.array(states, copy=True)
        times.setflags(write=False)
        states.setflags(write=False)
        object.__setattr__(self, "times", times)
        object.__setattr__(self, "states", states)

    @property
    def initial_state(self) -> InertialState:
        return InertialState(self.states[0])

    @property
    def final_state(self) -> InertialState:
        return InertialState(self.states[-1])


@dataclass(frozen=True)
class DOP853Config:
    rtol: float = 1.0e-12
    atol: float = 1.0e-14
    max_step: float = np.inf

    def __post_init__(self) -> None:
        if not np.isfinite(self.rtol) or self.rtol <= 0.0:
            raise ValueError("rtol must be finite and positive")
        if not np.isfinite(self.atol) or self.atol <= 0.0:
            raise ValueError("atol must be finite and positive")
        if self.max_step <= 0.0 or np.isnan(self.max_step):
            raise ValueError("max_step must be positive")


def propagate_dop853(
    initial_state: StateLike,
    times: ArrayLike,
    parameters: SystemParameters,
    *,
    config: DOP853Config | None = None,
) -> Trajectory:
    """Propagate the 18D state with SciPy's production DOP853 path."""

    evaluation_times = _validated_times(times)
    initial_vector = as_state_vector(initial_state, copy=True)
    settings = config or DOP853Config()

    solution = solve_ivp(
        fun=lambda time, state: newtonian_rhs(time, state, parameters),
        t_span=(float(evaluation_times[0]), float(evaluation_times[-1])),
        y0=initial_vector,
        method="DOP853",
        t_eval=evaluation_times,
        rtol=settings.rtol,
        atol=settings.atol,
        max_step=settings.max_step,
        vectorized=False,
    )
    if not solution.success:
        raise RuntimeError(f"DOP853 propagation failed: {solution.message}")
    if solution.t.size != evaluation_times.size:
        raise RuntimeError("DOP853 did not return every requested checkpoint")

    return Trajectory(solution.t, solution.y.T, engine="scipy-dop853")


@dataclass(frozen=True)
class IAS15Config:
    epsilon: float = 1.0e-12
    adaptive_mode: str = "global"

    def __post_init__(self) -> None:
        if not np.isfinite(self.epsilon) or self.epsilon <= 0.0:
            raise ValueError("epsilon must be finite and positive")
        if self.adaptive_mode not in {"individual", "global", "prs23", "aarseth85"}:
            raise ValueError("adaptive_mode is not supported by REBOUND IAS15")


class ReferencePropagatorUnavailable(ImportError):
    """Raised when the declared REBOUND reference dependency is unavailable."""


def propagate_rebound_ias15(
    initial_state: StateLike,
    times: ArrayLike,
    parameters: SystemParameters,
    *,
    config: IAS15Config | None = None,
) -> Trajectory:
    """Propagate with REBOUND's independently implemented IAS15 engine.

    This path intentionally does not call ``newtonian_rhs`` or move the input
    into a center-of-mass frame. It is a reference implementation, not an
    arbitrary-precision proof engine.
    """

    try:
        import rebound
    except ImportError as error:  # pragma: no cover - dependency is locked by Poetry
        raise ReferencePropagatorUnavailable(
            "REBOUND is required for the IAS15 reference propagator"
        ) from error

    evaluation_times = _validated_times(times)
    initial = InertialState(as_state_vector(initial_state, copy=True))
    settings = config or IAS15Config()

    simulation = rebound.Simulation()
    simulation.G = parameters.gravitational_constant
    simulation.integrator = "ias15"
    simulation.ri_ias15.epsilon = settings.epsilon
    # The figure-eight starts with one body at zero net acceleration. REBOUND's
    # per-particle PRS23 criterion can collapse the initial timestep there;
    # the global IAS15 criterion remains independent and well conditioned.
    simulation.ri_ias15.adaptive_mode = settings.adaptive_mode

    for mass, position, velocity in zip(
        parameters.masses,
        initial.positions,
        initial.velocities,
        strict=True,
    ):
        simulation.add(
            m=float(mass),
            x=float(position[0]),
            y=float(position[1]),
            z=float(position[2]),
            vx=float(velocity[0]),
            vy=float(velocity[1]),
            vz=float(velocity[2]),
        )

    states = np.empty((evaluation_times.size, 18), dtype=np.float64)
    states[0] = initial.values
    epoch = float(evaluation_times[0])
    for index, time in enumerate(evaluation_times[1:], start=1):
        simulation.integrate(float(time - epoch), exact_finish_time=1)
        particles = simulation.particles
        positions = np.array([[p.x, p.y, p.z] for p in particles], dtype=np.float64)
        velocities = np.array(
            [[p.vx, p.vy, p.vz] for p in particles], dtype=np.float64
        )
        states[index] = InertialState.from_components(positions, velocities).values

    return Trajectory(evaluation_times, states, engine="rebound-ias15")
