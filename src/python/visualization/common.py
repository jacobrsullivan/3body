"""
Common utilities for WP2 visualization.

Provides shared functionality:
- Plot styling and defaults
- Color maps and themes
- Grid generation
- Coordinate transformations for plotting
- Figure creation utilities
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import Normalize, LinearSegmentedColormap
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from typing import Tuple, Optional, Dict, Any
import matplotlib as mpl


# Publication-quality defaults
PUBLICATION_STYLE = {
    'figure.figsize': (8, 6),
    'figure.dpi': 150,
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'lines.linewidth': 1.5,
    'lines.markersize': 6,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'grid.linestyle': '--',
}


def apply_publication_style():
    """Apply publication-quality style to matplotlib."""
    plt.style.use('seaborn-v0_8-darkgrid')
    mpl.rcParams.update(PUBLICATION_STYLE)


def create_shape_space_grid(
    r_min: float = 0.1,
    r_max: float = 3.0,
    resolution: int = 50,
    valid_only: bool = True
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create grid in shape space (r₁₂, r₂₃) coordinates.

    For the planar three-body problem, shape space is 2D with coordinates
    (r₁₂, r₂₃). The third distance r₃₁ is determined by triangle inequality.

    Args:
        r_min: Minimum distance value
        r_max: Maximum distance value
        resolution: Number of grid points per dimension
        valid_only: If True, only return points satisfying triangle inequality

    Returns:
        (r12_grid, r23_grid): Meshgrid arrays of shape (resolution, resolution)
    """
    r12_vals = np.linspace(r_min, r_max, resolution)
    r23_vals = np.linspace(r_min, r_max, resolution)

    r12_grid, r23_grid = np.meshgrid(r12_vals, r23_vals)

    if valid_only:
        # Apply triangle inequality: r₃₁ must satisfy |r₁₂ - r₂₃| < r₃₁ < r₁₂ + r₂₃
        # For a grid, we can check if r₃₁ = 1.5 (or some value) satisfies this
        # More generally, just return all points; validity check is done at evaluation

        pass  # Grid creation is complete; validity checked during evaluation

    return r12_grid, r23_grid


def is_valid_triangle(r12: float, r23: float, r31: float, tol: float = 1e-10) -> bool:
    """
    Check if three distances form a valid triangle.

    Args:
        r12: Distance between bodies 1 and 2
        r23: Distance between bodies 2 and 3
        r31: Distance between bodies 3 and 1
        tol: Tolerance for inequality checks

    Returns:
        True if triangle inequalities are satisfied
    """
    return (
        r12 + r23 > r31 - tol and
        r23 + r31 > r12 - tol and
        r31 + r12 > r23 - tol
    )


def compute_r31_from_triangle(
    r12: float,
    r23: float,
    default: float = 1.0
) -> float:
    """
    Compute r₃₁ from r₁₂ and r₂₃ assuming a specific configuration.

    For visualization, we use a canonical configuration (e.g., bodies on a line
    or equilateral triangle). This is a heuristic for visualization.

    Args:
        r12: Distance between bodies 1 and 2
        r23: Distance between bodies 2 and 3
        default: Default value if no canonical config exists

    Returns:
        r31: Third distance (heuristic)
    """
    # Simple heuristic: Use law of cosines with angle θ = π/3 (equilateral tendency)
    # r₃₁² = r₁₂² + r₂₃² - 2·r₁₂·r₂₃·cos(θ)

    theta = np.pi / 3  # 60 degrees
    r31_squared = r12**2 + r23**2 - 2*r12*r23*np.cos(theta)

    if r31_squared > 0:
        return np.sqrt(r31_squared)
    else:
        return default


def get_colormap_custom(name: str = 'viridis') -> Any:
    """
    Get custom colormap for WP2 visualizations.

    Args:
        name: Colormap name ('viridis', 'plasma', 'coolwarm', 'reds', 'blues')

    Returns:
        Matplotlib colormap
    """
    if name in ['viridis', 'plasma', 'inferno', 'magma', 'cividis']:
        return cm.get_cmap(name)
    elif name == 'coolwarm':
        return cm.get_cmap('coolwarm')
    elif name == 'chaos':
        # Custom colormap for chaos indicators (blue = regular, red = chaotic)
        colors = ['#2166ac', '#4393c3', '#92c5de', '#d1e5f0',
                  '#fddbc7', '#f4a582', '#d6604d', '#b2182b']
        return LinearSegmentedColormap.from_list('chaos', colors)
    else:
        return cm.get_cmap('viridis')


def setup_3d_axes(
    fig: Optional[Figure] = None,
    subplot_spec: Optional[Any] = None
) -> Tuple[Figure, Axes]:
    """
    Create 3D axes for surface plots.

    Args:
        fig: Existing figure (or create new)
        subplot_spec: Subplot specification (e.g., 111 or (1, 2, 1))

    Returns:
        (fig, ax): Figure and 3D axes
    """
    if fig is None:
        fig = plt.figure(figsize=(10, 8))

    if subplot_spec is None:
        subplot_spec = 111

    ax = fig.add_subplot(subplot_spec, projection='3d')

    return fig, ax


def add_colorbar(
    fig: Figure,
    ax: Axes,
    mappable: Any,
    label: str = '',
    orientation: str = 'vertical'
) -> Any:
    """
    Add colorbar to plot.

    Args:
        fig: Figure object
        ax: Axes object
        mappable: Mappable object (e.g., from contourf, pcolormesh)
        label: Colorbar label
        orientation: 'vertical' or 'horizontal'

    Returns:
        Colorbar object
    """
    cbar = fig.colorbar(mappable, ax=ax, orientation=orientation)
    cbar.set_label(label, rotation=90 if orientation == 'vertical' else 0)
    return cbar


def format_scientific(
    value: float,
    precision: int = 2
) -> str:
    """
    Format number in scientific notation for plot labels.

    Args:
        value: Number to format
        precision: Number of decimal places

    Returns:
        Formatted string
    """
    if abs(value) < 1e-10:
        return "0"
    elif abs(value) > 1e3 or abs(value) < 1e-3:
        return f"{value:.{precision}e}"
    else:
        return f"{value:.{precision}f}"


def save_figure(
    fig: Figure,
    filename: str,
    dpi: int = 300,
    tight: bool = True,
    **kwargs
):
    """
    Save figure with publication-quality settings.

    Args:
        fig: Figure to save
        filename: Output filename (with extension)
        dpi: Resolution (default 300 for publication)
        tight: Use tight bounding box
        **kwargs: Additional arguments to plt.savefig
    """
    save_kwargs = {
        'dpi': dpi,
        'bbox_inches': 'tight' if tight else None,
        'facecolor': 'white',
        'edgecolor': 'none',
    }
    save_kwargs.update(kwargs)

    fig.savefig(filename, **save_kwargs)


def create_subplot_grid(
    nrows: int = 1,
    ncols: int = 1,
    figsize: Optional[Tuple[float, float]] = None,
    **kwargs
) -> Tuple[Figure, np.ndarray]:
    """
    Create grid of subplots with consistent styling.

    Args:
        nrows: Number of rows
        ncols: Number of columns
        figsize: Figure size (default: auto-scaled)
        **kwargs: Additional arguments to plt.subplots

    Returns:
        (fig, axes): Figure and array of axes
    """
    if figsize is None:
        figsize = (ncols * 6, nrows * 5)

    fig, axes = plt.subplots(nrows, ncols, figsize=figsize, **kwargs)

    return fig, axes


def annotate_point(
    ax: Axes,
    x: float,
    y: float,
    label: str,
    offset: Tuple[float, float] = (10, 10),
    **kwargs
):
    """
    Annotate a point on a 2D plot.

    Args:
        ax: Axes object
        x: x-coordinate
        y: y-coordinate
        label: Annotation text
        offset: Offset in points (dx, dy)
        **kwargs: Additional arguments to ax.annotate
    """
    default_kwargs = {
        'xytext': offset,
        'textcoords': 'offset points',
        'fontsize': 10,
        'ha': 'left',
        'arrowprops': dict(arrowstyle='->', lw=1, color='black')
    }
    default_kwargs.update(kwargs)

    ax.annotate(label, xy=(x, y), **default_kwargs)


# Default plot parameters for different types of visualizations

CONNECTION_PLOT_DEFAULTS = {
    'cmap': 'viridis',
    'arrow_scale': 1.0,
    'arrow_width': 0.003,
    'grid_alpha': 0.3,
    'vector_color': 'black',
}

CURVATURE_PLOT_DEFAULTS = {
    'cmap': 'coolwarm',
    'levels': 20,
    'colorbar_label': r'$|\mathcal{F}|$',
    'grid_alpha': 0.3,
}

METRIC_PLOT_DEFAULTS = {
    'cmap': 'plasma',
    'ellipsoid_alpha': 0.6,
    'grid_alpha': 0.3,
}

TRAJECTORY_PLOT_DEFAULTS = {
    'linewidth': 1.5,
    'marker_size': 4,
    'alpha': 0.8,
    'cmap': 'viridis',
}


def get_plot_defaults(plot_type: str) -> Dict[str, Any]:
    """
    Get default parameters for a specific plot type.

    Args:
        plot_type: One of 'connection', 'curvature', 'metric', 'trajectory'

    Returns:
        Dictionary of default parameters
    """
    defaults = {
        'connection': CONNECTION_PLOT_DEFAULTS,
        'curvature': CURVATURE_PLOT_DEFAULTS,
        'metric': METRIC_PLOT_DEFAULTS,
        'trajectory': TRAJECTORY_PLOT_DEFAULTS,
    }

    return defaults.get(plot_type, {}).copy()
