#!/usr/bin/env python
"""
Generate MEGNO and FLI chaos maps for CR3BP and optionally overlay WP1 samples.
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
from pathlib import Path
from multiprocessing import Pool, cpu_count
from typing import Tuple

import numpy as np
import matplotlib.pyplot as plt

# Ensure repo root is on path
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from src.python.utils.dynamics import solve_vy_from_jacobi
from src.python.validation.chaos_indicators import create_cr3bp_chaos_analyzer

ANALYZER = None


def _init_worker(mu: float) -> None:
    global ANALYZER
    ANALYZER = create_cr3bp_chaos_analyzer(mu)


def _compute_point(
    args: Tuple[float, float, float, float, float],
) -> Tuple[float, float]:
    x, y, C, mu, t_final = args
    try:
        vy = solve_vy_from_jacobi([x, y, 0.0, 0.0, 0.0, 0.0], C, mu, sign=1.0)
    except ValueError:
        return (np.nan, np.nan)

    state = np.array([x, y, 0.0, 0.0, vy, 0.0])
    result = ANALYZER.analyze(
        state, t_final=t_final, output_interval=max(1.0, t_final / 200)
    )
    return (result.mean_megno, result.final_fli)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate MEGNO/FLI chaos maps")
    parser.add_argument(
        "--mu", type=float, default=0.012150585609624, help="Mass parameter"
    )
    parser.add_argument(
        "--jacobi", type=float, default=3.1, help="Jacobi constant for map"
    )
    parser.add_argument("--x-min", type=float, default=-1.5)
    parser.add_argument("--x-max", type=float, default=1.5)
    parser.add_argument("--y-min", type=float, default=-1.0)
    parser.add_argument("--y-max", type=float, default=1.0)
    parser.add_argument("--resolution", type=int, default=1000)
    parser.add_argument("--t-final", type=float, default=500.0)
    parser.add_argument("--workers", type=int, default=max(1, cpu_count() - 1))
    parser.add_argument(
        "--wp1-hdf5-dir", default=None, help="Optional HDF5 directory for overlay"
    )
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    xs = np.linspace(args.x_min, args.x_max, args.resolution)
    ys = np.linspace(args.y_min, args.y_max, args.resolution)

    grid = [(x, y, args.jacobi, args.mu, args.t_final) for y in ys for x in xs]

    with Pool(
        processes=args.workers, initializer=_init_worker, initargs=(args.mu,)
    ) as pool:
        results = pool.map(_compute_point, grid, chunksize=256)

    megno = np.array([r[0] for r in results]).reshape(args.resolution, args.resolution)
    fli = np.array([r[1] for r in results]).reshape(args.resolution, args.resolution)

    # Plot MEGNO
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(
        megno,
        origin="lower",
        extent=[args.x_min, args.x_max, args.y_min, args.y_max],
        aspect="auto",
        cmap="viridis",
    )
    ax.set_title("MEGNO Map")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    fig.colorbar(im, ax=ax, label="MEGNO")
    megno_path = os.path.join(args.output_dir, "chaos_map_megno.png")
    fig.savefig(megno_path, dpi=200)
    plt.close(fig)

    # Plot FLI
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(
        fli,
        origin="lower",
        extent=[args.x_min, args.x_max, args.y_min, args.y_max],
        aspect="auto",
        cmap="magma",
    )
    ax.set_title("FLI Map")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    fig.colorbar(im, ax=ax, label="FLI")
    fli_path = os.path.join(args.output_dir, "chaos_map_fli.png")
    fig.savefig(fli_path, dpi=200)
    plt.close(fig)

    # Optional overlay
    if args.wp1_hdf5_dir:
        import h5py

        files = glob.glob(os.path.join(args.wp1_hdf5_dir, "*.h5"))[:1000]
        points = []
        for fp in files:
            with h5py.File(fp, "r") as f:
                state = f["states_corotating"][0]
                points.append((state[0], state[1]))

        if points:
            px, py = zip(*points)
            fig, ax = plt.subplots(figsize=(8, 6))
            im = ax.imshow(
                megno,
                origin="lower",
                extent=[args.x_min, args.x_max, args.y_min, args.y_max],
                aspect="auto",
                cmap="viridis",
            )
            ax.scatter(px, py, s=5, c="white", alpha=0.6)
            ax.set_title("MEGNO Map + WP1 Overlay")
            ax.set_xlabel("x")
            ax.set_ylabel("y")
            fig.colorbar(im, ax=ax, label="MEGNO")
            overlay_path = os.path.join(args.output_dir, "chaos_map_megno_overlay.png")
            fig.savefig(overlay_path, dpi=200)
            plt.close(fig)

    print(f"Wrote: {megno_path}")
    print(f"Wrote: {fli_path}")


if __name__ == "__main__":
    main()
