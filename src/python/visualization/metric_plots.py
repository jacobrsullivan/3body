"""
Jacobi-Maupertuis metric visualization for WP2.

Provides functions to visualize the JM metric and scalar curvature:
- Metric ellipsoids showing anisotropy
- Scalar curvature R landscapes
- Curvature-chaos correlation analysis
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.patches import Ellipse
from typing import Callable, Tuple, Optional
from scipy.stats import pearsonr

from .common import (
    apply_publication_style,
    get_colormap_custom,
    add_colorbar,
    setup_3d_axes,
    compute_r31_from_triangle
)


def plot_jm_metric_ellipsoids(
    metric_evaluator: Callable,
    sample_points: np.ndarray,
    scale: float = 0.1,
    title: str = "JM Metric Ellipsoids",
    **kwargs
) -> Figure:
    """
    Plot JM metric as ellipsoids at sample points in shape space.

    Args:
        metric_evaluator: Function (r12, r23, r31) -> metric_tensor (2x2 or 3x3)
        sample_points: Array of shape (N, 2) with (r₁₂, r₂₃) coordinates
        scale: Scale factor for ellipsoid sizes
        title: Plot title

    Returns:
        Matplotlib Figure
    """
    apply_publication_style()

    fig, ax = plt.subplots(figsize=(10, 8))

    for point in sample_points:
        r12, r23 = point[0], point[1]
        r31 = compute_r31_from_triangle(r12, r23)

        try:
            g = metric_evaluator(r12, r23, r31)
            if hasattr(g, 'shape'):
                g_mat = g[:2, :2] if g.shape[0] > 2 else g
            else:
                g_mat = np.eye(2) * g

            # Eigendecomposition for ellipse
            eigvals, eigvecs = np.linalg.eigh(g_mat)
            angle = np.arctan2(eigvecs[1, 0], eigvecs[0, 0]) * 180 / np.pi

            ellipse = Ellipse(
                xy=(r12, r23),
                width=2*scale*np.sqrt(abs(eigvals[0])),
                height=2*scale*np.sqrt(abs(eigvals[1])),
                angle=angle,
                facecolor='blue',
                alpha=0.3,
                edgecolor='black',
                linewidth=1
            )
            ax.add_patch(ellipse)
        except:
            pass

    ax.set_xlabel(r'$r_{12}$', fontsize=14)
    ax.set_ylabel(r'$r_{23}$', fontsize=14)
    ax.set_title(title, fontsize=15)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    return fig


def plot_scalar_curvature_landscape(
    curvature_evaluator: Callable,
    energy: float,
    r12_range: Tuple[float, float] = (0.5, 3.0),
    r23_range: Tuple[float, float] = (0.5, 3.0),
    grid_resolution: int = 60,
    title: str = "Scalar Curvature Landscape",
    **kwargs
) -> Figure:
    """
    3D surface plot of scalar curvature R(s, E).

    Args:
        curvature_evaluator: Function (r12, r23, r31, E) -> R (scalar curvature)
        energy: Energy value E
        r12_range, r23_range: Coordinate ranges
        grid_resolution: Grid resolution
        title: Plot title

    Returns:
        3D Figure
    """
    apply_publication_style()

    r12_vals = np.linspace(r12_range[0], r12_range[1], grid_resolution)
    r23_vals = np.linspace(r23_range[0], r23_range[1], grid_resolution)
    r12_grid, r23_grid = np.meshgrid(r12_vals, r23_vals)

    R_values = np.zeros_like(r12_grid)

    for i in range(grid_resolution):
        for j in range(grid_resolution):
            r12, r23 = r12_grid[i, j], r23_grid[i, j]
            r31 = compute_r31_from_triangle(r12, r23)
            try:
                R = curvature_evaluator(r12, r23, r31, energy)
                R_values[i, j] = R
            except:
                R_values[i, j] = 0.0

    fig, ax = setup_3d_axes()

    cmap = kwargs.get('cmap', 'coolwarm')
    surf = ax.plot_surface(r12_grid, r23_grid, R_values,
                           cmap=get_colormap_custom(cmap),
                           alpha=0.8, edgecolor='none')

    fig.colorbar(surf, ax=ax, label=r'Scalar Curvature $R$', shrink=0.5)

    ax.set_xlabel(r'$r_{12}$', fontsize=12)
    ax.set_ylabel(r'$r_{23}$', fontsize=12)
    ax.set_zlabel(r'$R$', fontsize=12)
    ax.set_title(f'{title}\nE = {energy:.3f}', fontsize=13)

    plt.tight_layout()

    return fig


def plot_curvature_correlation(
    scalar_curvature: np.ndarray,
    lyapunov_exponents: np.ndarray,
    title: str = "Geometric Curvature vs. Chaos",
    **kwargs
) -> Figure:
    """Scatter plot showing R vs λ_max correlation."""
    apply_publication_style()

    fig, ax = plt.subplots(figsize=(10, 8))

    valid = np.isfinite(scalar_curvature) & np.isfinite(lyapunov_exponents)
    R_valid = scalar_curvature[valid]
    λ_valid = lyapunov_exponents[valid]

    # Color by chaos (red = chaotic, blue = regular)
    colors = ['red' if λ > 0 else 'blue' for λ in λ_valid]

    ax.scatter(R_valid, λ_valid, alpha=0.6, s=30, c=colors, edgecolors='k', linewidth=0.5)

    if len(R_valid) > 1:
        r, p = pearsonr(R_valid, λ_valid)
        ax.text(0.05, 0.95, f'Correlation: r = {r:.3f}\np = {p:.2e}',
                transform=ax.transAxes, fontsize=12, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))

    ax.axhline(0, color='k', linestyle='--', alpha=0.3)
    ax.axvline(0, color='k', linestyle='--', alpha=0.3)
    ax.set_xlabel(r'Scalar Curvature $R$', fontsize=14)
    ax.set_ylabel(r'Max Lyapunov $\lambda_{max}$', fontsize=14)
    ax.set_title(title, fontsize=15)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    return fig
