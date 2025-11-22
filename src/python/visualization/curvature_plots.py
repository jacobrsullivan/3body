"""
Curvature two-form visualization for WP2.

Provides functions to visualize the curvature F = dA on shape space:
- 2D heatmaps showing |F|
- Contour plots of curvature magnitude
- Curvature vs. chaos correlation plots
- Stokes' theorem validation visualizations
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from typing import Callable, Tuple, Optional
from scipy.stats import pearsonr

from .common import (
    create_shape_space_grid,
    get_colormap_custom,
    add_colorbar,
    apply_publication_style,
    compute_r31_from_triangle
)


def plot_curvature_heatmap(
    curvature_evaluator: Callable,
    r12_range: Tuple[float, float] = (0.5, 3.0),
    r23_range: Tuple[float, float] = (0.5, 3.0),
    grid_resolution: int = 100,
    title: str = "Curvature Magnitude",
    log_scale: bool = False,
    **kwargs
) -> Figure:
    """
    Plot 2D heatmap of curvature magnitude |F(s)| on shape space.

    Args:
        curvature_evaluator: Function (r12, r23, r31) -> F_value (or array)
        r12_range: Range for r₁₂ axis
        r23_range: Range for r₂₃ axis
        grid_resolution: Number of grid points
        title: Plot title
        log_scale: Use log scale for color mapping
        **kwargs: cmap, levels, etc.

    Returns:
        Matplotlib Figure
    """
    apply_publication_style()

    r12_vals = np.linspace(r12_range[0], r12_range[1], grid_resolution)
    r23_vals = np.linspace(r23_range[0], r23_range[1], grid_resolution)
    r12_grid, r23_grid = np.meshgrid(r12_vals, r23_vals)

    curvatures = np.zeros_like(r12_grid)

    for i in range(grid_resolution):
        for j in range(grid_resolution):
            r12 = r12_grid[i, j]
            r23 = r23_grid[i, j]
            r31 = compute_r31_from_triangle(r12, r23)
            try:
                F = curvature_evaluator(r12, r23, r31)
                curvatures[i, j] = abs(F) if np.isscalar(F) else np.linalg.norm(F)
            except:
                curvatures[i, j] = 0.0

    if log_scale:
        curvatures = np.log10(curvatures + 1e-10)

    fig, ax = plt.subplots(figsize=(10, 8))
    cmap = kwargs.get('cmap', 'coolwarm')
    levels = kwargs.get('levels', 20)

    contour = ax.contourf(r12_grid, r23_grid, curvatures, levels=levels,
                          cmap=get_colormap_custom(cmap))

    label = r'$\log_{10}|\mathcal{F}|$' if log_scale else r'$|\mathcal{F}|$'
    add_colorbar(fig, ax, contour, label=label)

    ax.set_xlabel(r'$r_{12}$', fontsize=14)
    ax.set_ylabel(r'$r_{23}$', fontsize=14)
    ax.set_title(title, fontsize=15)
    ax.set_aspect('equal')
    plt.tight_layout()

    return fig


def plot_curvature_contours(
    curvature_evaluator: Callable,
    r12_range: Tuple[float, float] = (0.5, 3.0),
    r23_range: Tuple[float, float] = (0.5, 3.0),
    grid_resolution: int = 80,
    title: str = "Curvature Contours",
    contour_levels: Optional[np.ndarray] = None,
    **kwargs
) -> Figure:
    """Plot contour lines of curvature magnitude."""
    apply_publication_style()

    r12_vals = np.linspace(r12_range[0], r12_range[1], grid_resolution)
    r23_vals = np.linspace(r23_range[0], r23_range[1], grid_resolution)
    r12_grid, r23_grid = np.meshgrid(r12_vals, r23_vals)

    curvatures = np.zeros_like(r12_grid)
    for i in range(grid_resolution):
        for j in range(grid_resolution):
            r12, r23 = r12_grid[i, j], r23_grid[i, j]
            r31 = compute_r31_from_triangle(r12, r23)
            try:
                F = curvature_evaluator(r12, r23, r31)
                curvatures[i, j] = abs(F) if np.isscalar(F) else np.linalg.norm(F)
            except:
                curvatures[i, j] = 0.0

    fig, ax = plt.subplots(figsize=(10, 8))

    if contour_levels is None:
        contour_levels = 15

    CS = ax.contour(r12_grid, r23_grid, curvatures, levels=contour_levels,
                    colors='k', linewidths=1.5)
    ax.clabel(CS, inline=True, fontsize=10, fmt='%.2f')

    filled = ax.contourf(r12_grid, r23_grid, curvatures, levels=contour_levels,
                         cmap=get_colormap_custom('coolwarm'), alpha=0.6)
    add_colorbar(fig, ax, filled, label=r'$|\mathcal{F}|$')

    ax.set_xlabel(r'$r_{12}$', fontsize=14)
    ax.set_ylabel(r'$r_{23}$', fontsize=14)
    ax.set_title(title, fontsize=15)
    ax.set_aspect('equal')
    plt.tight_layout()

    return fig


def plot_curvature_vs_chaos(
    curvature_values: np.ndarray,
    lyapunov_exponents: np.ndarray,
    title: str = "Curvature vs. Chaos Correlation",
    **kwargs
) -> Figure:
    """
    Scatter plot showing correlation between curvature and chaos.

    Args:
        curvature_values: Array of curvature magnitudes
        lyapunov_exponents: Array of max Lyapunov exponents
        title: Plot title
        **kwargs: Additional plot arguments

    Returns:
        Figure with scatter plot and correlation statistics
    """
    apply_publication_style()

    fig, ax = plt.subplots(figsize=(10, 8))

    # Remove invalid values
    valid = np.isfinite(curvature_values) & np.isfinite(lyapunov_exponents)
    curv_valid = curvature_values[valid]
    lyap_valid = lyapunov_exponents[valid]

    # Scatter plot
    ax.scatter(curv_valid, lyap_valid, alpha=0.5, s=20, c='blue', edgecolors='k', linewidth=0.5)

    # Compute correlation
    if len(curv_valid) > 1:
        r, p_value = pearsonr(curv_valid, lyap_valid)
        ax.text(0.05, 0.95, f'Pearson r = {r:.3f}\np-value = {p_value:.2e}',
                transform=ax.transAxes, fontsize=12, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # Add zero lines
    ax.axhline(0, color='k', linestyle='--', alpha=0.3, linewidth=1)
    ax.axvline(0, color='k', linestyle='--', alpha=0.3, linewidth=1)

    ax.set_xlabel(r'Scalar Curvature $R$', fontsize=14)
    ax.set_ylabel(r'Max Lyapunov Exponent $\lambda_{max}$', fontsize=14)
    ax.set_title(title, fontsize=15)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    return fig
