"""
Visualization tools for WP2 geometric objects.

This package provides publication-quality visualization functions for:
- Connection one-forms and vector fields
- Curvature two-forms and heatmaps
- Jacobi-Maupertuis metric and scalar curvature
- Shape space trajectories and lift comparisons

Modules:
- common: Shared utilities and plot styling
- connection_plots: Connection form visualization
- curvature_plots: Curvature form visualization
- metric_plots: JM metric and scalar curvature visualization
- trajectory_plots: Trajectory visualization in various coordinates
"""

from . import common
from . import connection_plots
from . import curvature_plots
from . import metric_plots
from . import trajectory_plots

# Import main plotting functions
from .connection_plots import (
    plot_connection_field,
    plot_connection_magnitude_heatmap,
    plot_holonomy_loop
)

from .curvature_plots import (
    plot_curvature_heatmap,
    plot_curvature_contours,
    plot_curvature_vs_chaos
)

from .metric_plots import (
    plot_jm_metric_ellipsoids,
    plot_scalar_curvature_landscape,
    plot_curvature_correlation
)

from .trajectory_plots import (
    plot_shape_trajectory,
    plot_trajectory_family,
    plot_lift_comparison
)

__all__ = [
    # Modules
    'common',
    'connection_plots',
    'curvature_plots',
    'metric_plots',
    'trajectory_plots',
    # Connection
    'plot_connection_field',
    'plot_connection_magnitude_heatmap',
    'plot_holonomy_loop',
    # Curvature
    'plot_curvature_heatmap',
    'plot_curvature_contours',
    'plot_curvature_vs_chaos',
    # Metric
    'plot_jm_metric_ellipsoids',
    'plot_scalar_curvature_landscape',
    'plot_curvature_correlation',
    # Trajectories
    'plot_shape_trajectory',
    'plot_trajectory_family',
    'plot_lift_comparison',
]
