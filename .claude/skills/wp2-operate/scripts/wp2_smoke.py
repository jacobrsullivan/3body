#!/usr/bin/env python3
"""Minimal WP2 smoke run for geometry computations."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def _add_repo_root() -> Path:
    root = Path(__file__).resolve().parents[4]
    sys.path.insert(0, str(root))
    return root


def main() -> int:
    _add_repo_root()

    try:
        import numpy as np
        from src.python.coordinates.base import Masses
        from src.python.coordinates.shape_space import ShapeSpaceState
        from src.python.geometry.connection_form import compute_connection_coefficients
        from src.python.geometry.curvature_form import compute_curvature
        from src.python.geometry.jm_metric import compute_effective_potential
        from src.python.geometry.riemann_curvature import compute_curvature_tensors
    except Exception as exc:  # pragma: no cover - import guard
        print(f"IMPORT_ERROR: {exc}")
        return 2

    masses = Masses(1.0, 1.0, 1.0)
    shape = ShapeSpaceState(
        r12=1.0,
        r23=1.0,
        r31=1.0,
        dr12_dt=0.0,
        dr23_dt=0.0,
        dr31_dt=0.0,
        L=1.0,
        dimension=2,
    )

    connection = compute_connection_coefficients(shape, masses)
    curvature = compute_curvature(shape, masses)

    v_eff = compute_effective_potential(shape, masses, L_magnitude=1.0)
    energy = v_eff + 1.0
    tensors = compute_curvature_tensors(
        shape,
        masses,
        energy=energy,
        L_magnitude=1.0,
        compute_riemann=False,
    )

    payload = {
        "masses": [masses.m1, masses.m2, masses.m3],
        "shape": {
            "r12": shape.r12,
            "r23": shape.r23,
            "r31": shape.r31,
            "L": shape.L,
        },
        "connection": {
            "coefficients": connection.coefficients.tolist(),
            "magnitude": float(connection.magnitude()),
        },
        "curvature": {
            "matrix": curvature.matrix.tolist(),
            "magnitude": float(curvature.magnitude()),
            "is_flat": bool(curvature.is_flat()),
        },
        "jm_metric": {
            "energy": float(energy),
            "scalar_curvature": float(tensors.scalar),
        },
    }

    print(json.dumps(payload, indent=2))

    numeric_checks = [
        *connection.coefficients.ravel(),
        curvature.magnitude(),
        tensors.scalar,
    ]
    if not np.isfinite(numeric_checks).all():
        print("NUMERIC_ERROR: non-finite values detected")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
