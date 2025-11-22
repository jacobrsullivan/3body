"""
Connection one-form visualization for WP2.

Provides functions to visualize the mechanical connection A on shape space:
- Vector field plots showing A as arrows
- Magnitude heatmaps showing |A|
- Holonomy visualization around closed loops
- Streamline plots showing rotational coupling
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from typing import Optional, Tuple, Callable, Any
from dataclasses import dataclass

from .common import (
    create_shape_space_grid,
    get_colormap_custom,
    add_colorbar,
    apply_publication_style,
    get_plot_defaults,
    compute_r31_from_triangle
)


def plot_connection_field(
    connection_evaluator: Callable,
    r12_range: Tuple[float, float] = (0.5, 3.0),
    r23_range: Tuple[float, float] = (0.5, 3.0),
    grid_resolution: int = 30,
    arrow_scale: float = 1.0,
    arrow_width: float = 0.003,
    title: str = "Mechanical Connection Vector Field",
    show_magnitude_color: bool = True,
    **kwargs
) -> Figure:
    """
    Plot connection one-form as a vector field on shape space.

    The connection A maps shape velocities to rotational velocities.
    This plot shows A as arrows at each grid point in (r₁₂, r₂₃) space.

    Args:
        connection_evaluator: Function (r12, r23, r31) -> (A_r12, A_r23, A_r31)
        r12_range: Range for r₁₂ axis
        r23_range: Range for r₂₃ axis
        grid_resolution: Number of grid points per dimension
        arrow_scale: Scale factor for arrow lengths
        arrow_width: Width of arrows
        title: Plot title
        show_magnitude_color: Color arrows by magnitude
        **kwargs: Additional arguments (cmap, etc.)

    Returns:
        Matplotlib Figure object

    Example:
        >>> def conn_func(r12, r23, r31):
        ...     return (r12*0.1, r23*0.1, 0.0)
        >>> fig = plot_connection_field(conn_func)
        >>> plt.show()
    """
    apply_publication_style()

    # Create grid
    r12_vals = np.linspace(r12_range[0], r12_range[1], grid_resolution)
    r23_vals = np.linspace(r23_range[0], r23_range[1], grid_resolution)
    r12_grid, r23_grid = np.meshgrid(r12_vals, r23_vals)

    # Evaluate connection at each grid point
    A_r12 = np.zeros_like(r12_grid)
    A_r23 = np.zeros_like(r23_grid)
    magnitudes = np.zeros_like(r12_grid)

    for i in range(grid_resolution):
        for j in range(grid_resolution):
            r12 = r12_grid[i, j]
            r23 = r23_grid[i, j]
            r31 = compute_r31_from_triangle(r12, r23)

            try:
                A_vals = connection_evaluator(r12, r23, r31)
                A_r12[i, j] = A_vals[0] if hasattr(A_vals, '__len__') else A_vals
                A_r23[i, j] = A_vals[1] if len(A_vals) > 1 else 0.0
                magnitudes[i, j] = np.sqrt(A_r12[i, j]**2 + A_r23[i, j]**2)
            except:
                A_r12[i, j] = 0.0
                A_r23[i, j] = 0.0
                magnitudes[i, j] = 0.0

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))

    # Plot vector field
    if show_magnitude_color:
        cmap = kwargs.get('cmap', 'viridis')
        colormap = get_colormap_custom(cmap)
        colors = magnitudes.flatten()
        quiver = ax.quiver(
            r12_grid, r23_grid, A_r12, A_r23,
            colors, cmap=colormap,
            scale=arrow_scale, scale_units='xy',
            width=arrow_width, angles='xy'
        )
        add_colorbar(fig, ax, quiver, label=r'$|\mathcal{A}|$')
    else:
        ax.quiver(
            r12_grid, r23_grid, A_r12, A_r23,
            scale=arrow_scale, scale_units='xy',
            width=arrow_width, angles='xy',
            color='black'
        )

    # Labels and formatting
    ax.set_xlabel(r'$r_{12}$', fontsize=14)
    ax.set_ylabel(r'$r_{23}$', fontsize=14)
    ax.set_title(title, fontsize=15)
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')

    plt.tight_layout()

    return fig


def plot_connection_magnitude_heatmap(
    connection_evaluator: Callable,
    r12_range: Tuple[float, float] = (0.5, 3.0),
    r23_range: Tuple[float, float] = (0.5, 3.0),
    grid_resolution: int = 100,
    title: str = "Connection Magnitude",
    log_scale: bool = False,
    **kwargs
) -> Figure:
    """
    Plot 2D heatmap of connection magnitude |A(s)| on shape space.

    Args:
        connection_evaluator: Function (r12, r23, r31) -> (A_r12, A_r23, A_r31)
        r12_range: Range for r₁₂ axis
        r23_range: Range for r₂₃ axis
        grid_resolution: Number of grid points per dimension
        title: Plot title
        log_scale: Use log scale for colormap
        **kwargs: Additional arguments (cmap, levels, etc.)

    Returns:
        Matplotlib Figure object
    """
    apply_publication_style()

    # Create grid
    r12_vals = np.linspace(r12_range[0], r12_range[1], grid_resolution)
    r23_vals = np.linspace(r23_range[0], r23_range[1], grid_resolution)
    r12_grid, r23_grid = np.meshgrid(r12_vals, r23_vals)

    # Evaluate connection magnitude
    magnitudes = np.zeros_like(r12_grid)

    for i in range(grid_resolution):
        for j in range(grid_resolution):
            r12 = r12_grid[i, j]
            r23 = r23_grid[i, j]
            r31 = compute_r31_from_triangle(r12, r23)

            try:
                A_vals = connection_evaluator(r12, r23, r31)
                if hasattr(A_vals, '__len__'):
                    mag = np.sqrt(sum(a**2 for a in A_vals))
                else:
                    mag = abs(A_vals)
                magnitudes[i, j] = mag
            except:
                magnitudes[i, j] = 0.0

    # Handle log scale
    if log_scale:
        magnitudes = np.log10(magnitudes + 1e-10)

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))

    # Plot heatmap
    cmap = kwargs.get('cmap', 'viridis')
    levels = kwargs.get('levels', 20)

    contour = ax.contourf(r12_grid, r23_grid, magnitudes, levels=levels,
                          cmap=get_colormap_custom(cmap))

    colorbar_label = r'$\log_{10}|\mathcal{A}|$' if log_scale else r'$|\mathcal{A}|$'
    add_colorbar(fig, ax, contour, label=colorbar_label)

    # Labels and formatting
    ax.set_xlabel(r'$r_{12}$', fontsize=14)
    ax.set_ylabel(r'$r_{23}$', fontsize=14)
    ax.set_title(title, fontsize=15)
    ax.set_aspect('equal')

    plt.tight_layout()

    return fig


def plot_holonomy_loop(
    connection_evaluator: Callable,
    loop_path: np.ndarray,
    title: str = "Holonomy Around Closed Loop",
    show_path: bool = True,
    **kwargs
) -> Tuple[Figure, float]:
    """
    Visualize holonomy around a closed loop in shape space.

    Computes ∮ A·ds around the provided loop and visualizes both
    the path and the connection values along it.

    Args:
        connection_evaluator: Function (r12, r23, r31) -> (A_r12, A_r23, A_r31)
        loop_path: Array of shape (N, 2) with (r₁₂, r₂₃) coordinates
        title: Plot title
        show_path: If True, show the loop path on a 2D plot
        **kwargs: Additional arguments

    Returns:
        (fig, holonomy): Figure and computed holonomy value ∮A

    Example:
        >>> # Create circular loop
        >>> theta = np.linspace(0, 2*np.pi, 100)
        >>> r_center = 1.5
        >>> r_radius = 0.5
        >>> loop = np.column_stack([
        ...     r_center + r_radius*np.cos(theta),
        ...     r_center + r_radius*np.sin(theta)
        ... ])
        >>> fig, hol = plot_holonomy_loop(conn_func, loop)
    """
    apply_publication_style()

    # Compute connection along path
    N = len(loop_path)
    A_values = []
    path_segments = []

    for i in range(N - 1):
        r12_i = loop_path[i, 0]
        r23_i = loop_path[i, 1]
        r31_i = compute_r31_from_triangle(r12_i, r23_i)

        r12_ip1 = loop_path[i+1, 0]
        r23_ip1 = loop_path[i+1, 1]

        # Compute connection
        try:
            A_i = connection_evaluator(r12_i, r23_i, r31_i)
        except:
            A_i = (0.0, 0.0, 0.0)

        # Compute path tangent
        dr12 = r12_ip1 - r12_i
        dr23 = r23_ip1 - r23_i

        # A·ds (dot product)
        if hasattr(A_i, '__len__'):
            A_dot_ds = A_i[0] * dr12 + A_i[1] * dr23
        else:
            A_dot_ds = A_i * dr12

        A_values.append(A_dot_ds)
        path_segments.append(i)

    # Compute holonomy (line integral)
    holonomy = np.sum(A_values)

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Left plot: Path in shape space
    if show_path:
        ax1.plot(loop_path[:, 0], loop_path[:, 1], 'b-', linewidth=2, label='Loop path')
        ax1.plot(loop_path[0, 0], loop_path[0, 1], 'go', markersize=10, label='Start')
        ax1.plot(loop_path[-1, 0], loop_path[-1, 1], 'ro', markersize=10, label='End')
        ax1.set_xlabel(r'$r_{12}$', fontsize=14)
        ax1.set_ylabel(r'$r_{23}$', fontsize=14)
        ax1.set_title('Loop in Shape Space', fontsize=13)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_aspect('equal')

    # Right plot: Connection values along path
    ax2.plot(path_segments, A_values, 'b-', linewidth=2)
    ax2.axhline(0, color='k', linestyle='--', alpha=0.3)
    ax2.fill_between(path_segments, 0, A_values, alpha=0.3)
    ax2.set_xlabel('Path segment', fontsize=14)
    ax2.set_ylabel(r'$\mathcal{A} \cdot ds$', fontsize=14)
    ax2.set_title(f'Connection Along Path\nHolonomy = {holonomy:.4f}', fontsize=13)
    ax2.grid(True, alpha=0.3)

    fig.suptitle(title, fontsize=15)
    plt.tight_layout()

    return fig, holonomy


def plot_connection_streamlines(
    connection_evaluator: Callable,
    r12_range: Tuple[float, float] = (0.5, 3.0),
    r23_range: Tuple[float, float] = (0.5, 3.0),
    grid_resolution: int = 50,
    title: str = "Connection Streamlines",
    density: float = 1.5,
    **kwargs
) -> Figure:
    """
    Plot streamlines of connection one-form.

    Streamlines show the integral curves of the connection vector field.

    Args:
        connection_evaluator: Function (r12, r23, r31) -> (A_r12, A_r23, A_r31)
        r12_range: Range for r₁₂ axis
        r23_range: Range for r₂₃ axis
        grid_resolution: Number of grid points per dimension
        title: Plot title
        density: Streamline density
        **kwargs: Additional arguments (color, linewidth, etc.)

    Returns:
        Matplotlib Figure object
    """
    apply_publication_style()

    # Create grid
    r12_vals = np.linspace(r12_range[0], r12_range[1], grid_resolution)
    r23_vals = np.linspace(r23_range[0], r23_range[1], grid_resolution)
    r12_grid, r23_grid = np.meshgrid(r12_vals, r23_vals)

    # Evaluate connection
    A_r12 = np.zeros_like(r12_grid)
    A_r23 = np.zeros_like(r23_grid)

    for i in range(grid_resolution):
        for j in range(grid_resolution):
            r12 = r12_grid[i, j]
            r23 = r23_grid[i, j]
            r31 = compute_r31_from_triangle(r12, r23)

            try:
                A_vals = connection_evaluator(r12, r23, r31)
                A_r12[i, j] = A_vals[0] if hasattr(A_vals, '__len__') else A_vals
                A_r23[i, j] = A_vals[1] if len(A_vals) > 1 else 0.0
            except:
                A_r12[i, j] = 0.0
                A_r23[i, j] = 0.0

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))

    # Plot streamlines
    color = kwargs.get('color', 'blue')
    linewidth = kwargs.get('linewidth', 1.5)

    stream = ax.streamplot(
        r12_grid, r23_grid, A_r12, A_r23,
        density=density, color=color, linewidth=linewidth,
        arrowsize=1.5, arrowstyle='->'
    )

    # Labels and formatting
    ax.set_xlabel(r'$r_{12}$', fontsize=14)
    ax.set_ylabel(r'$r_{23}$', fontsize=14)
    ax.set_title(title, fontsize=15)
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')

    plt.tight_layout()

    return fig
