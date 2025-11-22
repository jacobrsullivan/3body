"""
Trajectory visualization for WP2.

Provides functions to visualize trajectories in different coordinate systems:
- Shape space trajectories
- Multi-trajectory families
- S¹ bundle vs KS spinor lift comparisons
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from typing import Optional, Tuple
from mpl_toolkits.mplot3d import Axes3D

from .common import (
    apply_publication_style,
    get_colormap_custom,
    setup_3d_axes,
    create_subplot_grid
)


def plot_shape_trajectory(
    trajectory: np.ndarray,
    color_by: str = 'time',
    color_values: Optional[np.ndarray] = None,
    title: str = "Trajectory in Shape Space",
    **kwargs
) -> Figure:
    """
    Plot trajectory in shape space coordinates (r₁₂, r₂₃).

    Args:
        trajectory: Array of shape (N, 2) or (N, 3) with (r₁₂, r₂₃) or (r₁₂, r₂₃, r₃₁)
        color_by: Color scheme ('time', 'energy', 'chaos', 'custom')
        color_values: Custom color values (array of length N)
        title: Plot title

    Returns:
        Matplotlib Figure
    """
    apply_publication_style()

    fig, ax = plt.subplots(figsize=(10, 8))

    N = len(trajectory)

    # Determine colors
    if color_by == 'time' or color_values is None:
        colors = np.linspace(0, 1, N)
        cmap = get_colormap_custom('viridis')
        cbar_label = 'Time'
    elif color_by == 'custom' and color_values is not None:
        colors = color_values
        cmap = get_colormap_custom('plasma')
        cbar_label = 'Value'
    else:
        colors = np.arange(N)
        cmap = get_colormap_custom('viridis')
        cbar_label = color_by.capitalize()

    # Plot trajectory
    scatter = ax.scatter(
        trajectory[:, 0], trajectory[:, 1],
        c=colors, cmap=cmap,
        s=20, alpha=0.6, edgecolors='k', linewidth=0.3
    )

    # Add start and end markers
    ax.plot(trajectory[0, 0], trajectory[0, 1], 'go', markersize=12, label='Start', zorder=10)
    ax.plot(trajectory[-1, 0], trajectory[-1, 1], 'ro', markersize=12, label='End', zorder=10)

    # Colorbar
    cbar = fig.colorbar(scatter, ax=ax)
    cbar.set_label(cbar_label, fontsize=12)

    ax.set_xlabel(r'$r_{12}$', fontsize=14)
    ax.set_ylabel(r'$r_{23}$', fontsize=14)
    ax.set_title(title, fontsize=15)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    plt.tight_layout()

    return fig


def plot_trajectory_family(
    trajectories: list,
    labels: Optional[list] = None,
    title: str = "Trajectory Family in Shape Space",
    **kwargs
) -> Figure:
    """
    Plot multiple trajectories on the same plot.

    Args:
        trajectories: List of trajectory arrays
        labels: List of labels for each trajectory
        title: Plot title

    Returns:
        Matplotlib Figure
    """
    apply_publication_style()

    fig, ax = plt.subplots(figsize=(10, 8))

    n_traj = len(trajectories)
    colors = plt.cm.tab10(np.linspace(0, 1, n_traj))

    for i, traj in enumerate(trajectories):
        label = labels[i] if labels and i < len(labels) else f'Trajectory {i+1}'
        ax.plot(traj[:, 0], traj[:, 1], color=colors[i], linewidth=2, alpha=0.7, label=label)
        ax.plot(traj[0, 0], traj[0, 1], 'o', color=colors[i], markersize=8)

    ax.set_xlabel(r'$r_{12}$', fontsize=14)
    ax.set_ylabel(r'$r_{23}$', fontsize=14)
    ax.set_title(title, fontsize=15)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    plt.tight_layout()

    return fig


def plot_lift_comparison(
    traj_reduced: np.ndarray,
    traj_s1: Optional[np.ndarray] = None,
    traj_ks: Optional[np.ndarray] = None,
    title: str = "Lift Comparison",
    **kwargs
) -> Figure:
    """
    Compare same trajectory in different coordinate representations.

    Args:
        traj_reduced: Trajectory in reduced (shape) space (N, 2)
        traj_s1: Trajectory in S¹ bundle (N, 3) - (r₁₂, r₂₃, θ)
        traj_ks: Trajectory in KS spinor (N, k) - spinor coordinates
        title: Plot title

    Returns:
        Multi-panel figure showing projections
    """
    apply_publication_style()

    n_panels = 1 + (traj_s1 is not None) + (traj_ks is not None)
    fig, axes = create_subplot_grid(1, n_panels, figsize=(6*n_panels, 5))

    if n_panels == 1:
        axes = [axes]

    panel = 0

    # Panel 1: Reduced (shape) space
    ax = axes[panel]
    ax.plot(traj_reduced[:, 0], traj_reduced[:, 1], 'b-', linewidth=2, alpha=0.7)
    ax.plot(traj_reduced[0, 0], traj_reduced[0, 1], 'go', markersize=10, label='Start')
    ax.set_xlabel(r'$r_{12}$', fontsize=12)
    ax.set_ylabel(r'$r_{23}$', fontsize=12)
    ax.set_title('Reduced (Shape Space)', fontsize=13)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    panel += 1

    # Panel 2: S¹ bundle (if provided)
    if traj_s1 is not None:
        ax = axes[panel]
        # Plot (r₁₂, r₂₃, θ) in 3D
        ax.remove()
        ax = fig.add_subplot(1, n_panels, panel+1, projection='3d')
        ax.plot(traj_s1[:, 0], traj_s1[:, 1], traj_s1[:, 2], 'r-', linewidth=2, alpha=0.7)
        ax.scatter(traj_s1[0, 0], traj_s1[0, 1], traj_s1[0, 2], color='green', s=100, label='Start')
        ax.set_xlabel(r'$r_{12}$', fontsize=10)
        ax.set_ylabel(r'$r_{23}$', fontsize=10)
        ax.set_zlabel(r'$\theta$', fontsize=10)
        ax.set_title('S¹ Lift', fontsize=13)
        ax.legend()
        panel += 1

    # Panel 3: KS spinor (if provided)
    if traj_ks is not None:
        ax = axes[panel]
        # Plot first two spinor components
        ax.plot(traj_ks[:, 0], traj_ks[:, 1], 'm-', linewidth=2, alpha=0.7)
        ax.plot(traj_ks[0, 0], traj_ks[0, 1], 'go', markersize=10, label='Start')
        ax.set_xlabel(r'$u_0$', fontsize=12)
        ax.set_ylabel(r'$u_1$', fontsize=12)
        ax.set_title('KS Spinor (u₀, u₁)', fontsize=13)
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')

    fig.suptitle(title, fontsize=15)
    plt.tight_layout()

    return fig


def plot_3d_trajectory(
    trajectory: np.ndarray,
    title: str = "3D Trajectory",
    color_by_time: bool = True,
    **kwargs
) -> Figure:
    """
    Plot 3D trajectory (for spatial 3BP or bundle coordinates).

    Args:
        trajectory: Array of shape (N, 3)
        title: Plot title
        color_by_time: Color trajectory by time

    Returns:
        3D Figure
    """
    apply_publication_style()

    fig, ax = setup_3d_axes()

    if color_by_time:
        N = len(trajectory)
        colors = np.linspace(0, 1, N)
        scatter = ax.scatter(
            trajectory[:, 0], trajectory[:, 1], trajectory[:, 2],
            c=colors, cmap='viridis', s=10, alpha=0.6
        )
        fig.colorbar(scatter, ax=ax, label='Time', shrink=0.5)
    else:
        ax.plot(trajectory[:, 0], trajectory[:, 1], trajectory[:, 2],
                'b-', linewidth=2, alpha=0.7)

    ax.scatter(trajectory[0, 0], trajectory[0, 1], trajectory[0, 2],
               color='green', s=100, marker='o', label='Start', zorder=10)
    ax.scatter(trajectory[-1, 0], trajectory[-1, 1], trajectory[-1, 2],
               color='red', s=100, marker='s', label='End', zorder=10)

    ax.set_xlabel(r'$x_1$', fontsize=12)
    ax.set_ylabel(r'$x_2$', fontsize=12)
    ax.set_zlabel(r'$x_3$', fontsize=12)
    ax.set_title(title, fontsize=13)
    ax.legend()
    plt.tight_layout()

    return fig
