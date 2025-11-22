"""
Time synchronization utilities for coordinating fictitious and physical time.

Manages the relationship between:
    - s: Fictitious time (integration parameter)
    - t: Physical time (observable)
    - Ω(q): Time dilation factor connecting them

Key Operations:
    - Track dual time evolution during integration
    - Interpolate physical time from fictitious time samples
    - Validate time consistency
    - Monitor time dilation along trajectories

References:
    - AMENDED_WP2.3-KS-Spinor-Lift-Implementation-Plan.md
    - Stiefel & Scheifele (1971): Linear and Regular Celestial Mechanics
"""

from dataclasses import dataclass
from typing import List, Callable, Optional, Tuple
import numpy as np
from scipy.interpolate import interp1d

from .sundman import SundmanTransformation, TimeTransformationStrategy


@dataclass
class DualTimeTrajectory:
    """
    Trajectory with both fictitious and physical time.

    Stores synchronized (s, t) pairs along with state information.

    Attributes:
        s_values: Fictitious time samples
        t_values: Corresponding physical times
        states: Optional state information at each point
        Omega_values: Time dilation factors at each point
    """
    s_values: np.ndarray
    t_values: np.ndarray
    states: Optional[List] = None
    Omega_values: Optional[np.ndarray] = None

    def __post_init__(self):
        """Validate consistency"""
        if len(self.s_values) != len(self.t_values):
            raise ValueError(
                f"Length mismatch: s has {len(self.s_values)} points, "
                f"t has {len(self.t_values)} points"
            )

        if self.states is not None and len(self.states) != len(self.s_values):
            raise ValueError("States length must match s_values")

        if self.Omega_values is not None:
            # Omega_values can be same length (value at each point) or one shorter (value during each step)
            if len(self.Omega_values) not in [len(self.s_values), len(self.s_values) - 1]:
                raise ValueError(
                    f"Omega_values length must be {len(self.s_values)} or {len(self.s_values)-1}, "
                    f"got {len(self.Omega_values)}"
                )

    @property
    def length(self) -> int:
        """Number of points in trajectory"""
        return len(self.s_values)

    @property
    def s_span(self) -> Tuple[float, float]:
        """Fictitious time span"""
        return (self.s_values[0], self.s_values[-1])

    @property
    def t_span(self) -> Tuple[float, float]:
        """Physical time span"""
        return (self.t_values[0], self.t_values[-1])

    def get_time_dilation_stats(self) -> dict:
        """Compute statistics on time dilation"""
        if self.Omega_values is None:
            # Estimate from time differences
            ds = np.diff(self.s_values)
            dt = np.diff(self.t_values)
            Omega_est = dt / ds
            Omega_est = np.concatenate([[Omega_est[0]], Omega_est])
        else:
            Omega_est = self.Omega_values

        return {
            'Omega_min': np.min(Omega_est),
            'Omega_max': np.max(Omega_est),
            'Omega_mean': np.mean(Omega_est),
            'Omega_std': np.std(Omega_est),
            'Omega_range': np.max(Omega_est) - np.min(Omega_est),
            'time_dilation_active': np.min(Omega_est) < 0.1 * np.max(Omega_est)
        }

    def interpolate_physical_time(self, s_query: np.ndarray) -> np.ndarray:
        """
        Interpolate physical time at arbitrary fictitious times.

        Args:
            s_query: Fictitious times to interpolate at

        Returns:
            Interpolated physical times
        """
        interpolator = interp1d(
            self.s_values,
            self.t_values,
            kind='cubic',
            fill_value='extrapolate'
        )
        return interpolator(s_query)

    def interpolate_fictitious_time(self, t_query: np.ndarray) -> np.ndarray:
        """
        Interpolate fictitious time at arbitrary physical times.

        Args:
            t_query: Physical times to interpolate at

        Returns:
            Interpolated fictitious times
        """
        # Check if t is monotonic (it should be)
        if not np.all(np.diff(self.t_values) >= 0):
            raise ValueError("Physical time must be monotonically increasing for interpolation")

        interpolator = interp1d(
            self.t_values,
            self.s_values,
            kind='cubic',
            fill_value='extrapolate'
        )
        return interpolator(t_query)


class TimeSynchronizer:
    """
    Manages synchronization between fictitious and physical time.

    Tracks the relationship dt/ds = Ω(q) during integration and
    provides utilities for conversion and validation.
    """

    def __init__(
        self,
        transformation: SundmanTransformation,
        s_initial: float = 0.0,
        t_initial: float = 0.0
    ):
        """
        Initialize synchronizer.

        Args:
            transformation: Sundman transformation defining Ω(q)
            s_initial: Initial fictitious time
            t_initial: Initial physical time
        """
        self.transformation = transformation
        self.s_initial = s_initial
        self.t_initial = t_initial

        # Storage for trajectory
        self.s_history: List[float] = [s_initial]
        self.t_history: List[float] = [t_initial]
        self.Omega_history: List[float] = []

    def advance_time(
        self,
        ds: float,
        *radii: float
    ) -> Tuple[float, float, float]:
        """
        Advance both times by fictitious step ds.

        Computes:
            s_new = s_old + ds
            Ω = transformation(*radii)
            dt = Ω · ds
            t_new = t_old + dt

        Args:
            ds: Fictitious time step
            *radii: Current radii for computing Ω

        Returns:
            (s_new, t_new, Omega)
        """
        s_old = self.s_history[-1]
        t_old = self.t_history[-1]

        # Compute time dilation
        Omega = self.transformation(*radii)

        # Advance times
        s_new = s_old + ds
        dt = Omega * ds
        t_new = t_old + dt

        # Store
        self.s_history.append(s_new)
        self.t_history.append(t_new)
        self.Omega_history.append(Omega)

        return s_new, t_new, Omega

    def reset(self, s_initial: float = 0.0, t_initial: float = 0.0):
        """Reset synchronizer to initial state"""
        self.s_initial = s_initial
        self.t_initial = t_initial
        self.s_history = [s_initial]
        self.t_history = [t_initial]
        self.Omega_history = []

    def get_trajectory(self) -> DualTimeTrajectory:
        """
        Get synchronized trajectory.

        Returns:
            DualTimeTrajectory with current history
        """
        return DualTimeTrajectory(
            s_values=np.array(self.s_history),
            t_values=np.array(self.t_history),
            Omega_values=np.array(self.Omega_history) if self.Omega_history else None
        )

    def validate_monotonicity(self) -> dict:
        """
        Validate that both s and t are monotonically increasing.

        Returns:
            Validation results
        """
        s_arr = np.array(self.s_history)
        t_arr = np.array(self.t_history)

        ds = np.diff(s_arr)
        dt = np.diff(t_arr)

        return {
            's_monotonic': np.all(ds > 0),
            't_monotonic': np.all(dt >= 0),  # Can have dt=0 at collision
            'min_ds': np.min(ds) if len(ds) > 0 else None,
            'min_dt': np.min(dt) if len(dt) > 0 else None,
            'negative_dt_count': np.sum(dt < 0)
        }

    def compute_average_dilation(self) -> float:
        """
        Compute average time dilation over trajectory.

        Returns:
            ⟨Ω⟩ = Δt / Δs
        """
        if len(self.s_history) < 2:
            return 0.0

        Delta_s = self.s_history[-1] - self.s_history[0]
        Delta_t = self.t_history[-1] - self.t_history[0]

        if Delta_s == 0:
            return 0.0

        return Delta_t / Delta_s

    def __repr__(self) -> str:
        return (
            f"TimeSynchronizer(\n"
            f"  transformation={self.transformation},\n"
            f"  points={len(self.s_history)},\n"
            f"  s_span=({self.s_history[0]:.3f}, {self.s_history[-1]:.3f}),\n"
            f"  t_span=({self.t_history[0]:.3f}, {self.t_history[-1]:.3f})\n"
            f")"
        )


def validate_time_consistency(
    s_values: np.ndarray,
    t_values: np.ndarray,
    Omega_values: np.ndarray,
    tolerance: float = 1e-10
) -> dict:
    """
    Validate consistency of time relationship.

    Checks that numerical integration of dt/ds = Ω matches stored t values.

    Args:
        s_values: Fictitious time samples
        t_values: Physical time samples
        Omega_values: Time dilation factors
        tolerance: Numerical tolerance

    Returns:
        Validation results
    """
    if len(s_values) != len(t_values) or len(s_values) != len(Omega_values):
        raise ValueError("All arrays must have same length")

    # Integrate Ω from s_values
    from .sundman import integrate_physical_time
    t_integrated = integrate_physical_time(s_values, Omega_values, t_values[0])

    # Compare with stored t_values
    errors = np.abs(t_integrated - t_values)
    max_error = np.max(errors)
    mean_error = np.mean(errors)

    return {
        'consistent': max_error < tolerance,
        'max_error': max_error,
        'mean_error': mean_error,
        'relative_error': max_error / (t_values[-1] - t_values[0]) if t_values[-1] != t_values[0] else 0.0,
        't_integrated': t_integrated,
        't_stored': t_values,
        'errors': errors
    }


def resample_to_physical_time(
    trajectory: DualTimeTrajectory,
    t_grid: np.ndarray
) -> DualTimeTrajectory:
    """
    Resample trajectory to uniform physical time grid.

    Useful for visualization and analysis where physical time is the
    natural coordinate.

    Args:
        trajectory: Original trajectory (may have non-uniform t)
        t_grid: Desired physical time grid

    Returns:
        New trajectory resampled to t_grid
    """
    # Interpolate s at desired t values
    s_resampled = trajectory.interpolate_fictitious_time(t_grid)

    # Interpolate Omega if available
    if trajectory.Omega_values is not None:
        Omega_interp = interp1d(
            trajectory.s_values,
            trajectory.Omega_values,
            kind='cubic',
            fill_value='extrapolate'
        )
        Omega_resampled = Omega_interp(s_resampled)
    else:
        Omega_resampled = None

    return DualTimeTrajectory(
        s_values=s_resampled,
        t_values=t_grid,
        Omega_values=Omega_resampled
    )


def compute_time_dilation_profile(
    trajectory: DualTimeTrajectory,
    num_bins: int = 50
) -> dict:
    """
    Compute histogram profile of time dilation along trajectory.

    Useful for visualizing where time regularization is most active.

    Args:
        trajectory: Dual time trajectory
        num_bins: Number of histogram bins

    Returns:
        Dictionary with histogram data
    """
    if trajectory.Omega_values is None:
        # Estimate from time differences
        ds = np.diff(trajectory.s_values)
        dt = np.diff(trajectory.t_values)
        Omega_est = dt / ds
    else:
        Omega_est = trajectory.Omega_values

    hist, bin_edges = np.histogram(Omega_est, bins=num_bins)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    return {
        'histogram': hist,
        'bin_edges': bin_edges,
        'bin_centers': bin_centers,
        'Omega_min': np.min(Omega_est),
        'Omega_max': np.max(Omega_est),
        'Omega_median': np.median(Omega_est)
    }
