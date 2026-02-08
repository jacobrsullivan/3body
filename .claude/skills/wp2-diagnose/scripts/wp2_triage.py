#!/usr/bin/env python3
"""WP2 triage: import checks + minimal geometry compute."""
from __future__ import annotations

import json
import platform
import sys
from pathlib import Path


def _add_repo_root() -> Path:
    root = Path(__file__).resolve().parents[4]
    sys.path.insert(0, str(root))
    return root


def main() -> int:
    root = _add_repo_root()

    info: dict[str, object] = {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "repo_root": str(root),
    }

    try:
        import numpy as np

        info["numpy_version"] = np.__version__
    except Exception as exc:
        info["numpy_error"] = str(exc)
        print(json.dumps(info, indent=2))
        return 2

    import_results: dict[str, str] = {}
    modules = [
        "src.python.coordinates.base",
        "src.python.coordinates.shape_space",
        "src.python.geometry.connection_form",
        "src.python.geometry.curvature_form",
        "src.python.geometry.jm_metric",
        "src.python.geometry.riemann_curvature",
    ]
    for module in modules:
        try:
            __import__(module)
            import_results[module] = "ok"
        except Exception as exc:
            import_results[module] = f"error: {exc}"
    info["imports"] = import_results

    try:
        from src.python.coordinates.base import Masses
        from src.python.coordinates.shape_space import ShapeSpaceState
        from src.python.geometry.connection_form import compute_connection_coefficients
        from src.python.geometry.curvature_form import compute_curvature

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
        info["smoke"] = {
            "connection_mag": float(connection.magnitude()),
            "curvature_mag": float(curvature.magnitude()),
            "curvature_flat": bool(curvature.is_flat()),
        }
    except Exception as exc:
        info["smoke_error"] = str(exc)
        print(json.dumps(info, indent=2))
        return 1

    print(json.dumps(info, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
