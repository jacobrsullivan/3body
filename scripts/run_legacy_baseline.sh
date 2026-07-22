#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:-fast}"

cd "$ROOT_DIR"

python - <<'PY'
import glob
import json
import os
import platform
import sys
from pathlib import Path

import heyoka
import jax
import jaxlib
import mpmath
import ml_dtypes
import numpy
import opt_einsum
import pybind11
import pytest
import qd_python
import rebound
import scipy
import sympy

with open("tests/legacy_baseline_manifest.json", encoding="utf-8") as handle:
    expected = json.load(handle)["runtime"]

prefix = os.environ.get("CONDA_PREFIX")
if not prefix:
    raise SystemExit("Legacy baseline requires an active pinned conda environment")
if Path(prefix).resolve() != Path(sys.prefix).resolve():
    raise SystemExit(
        f"Running Python prefix {sys.prefix} does not match CONDA_PREFIX {prefix}"
    )
binding_path = Path(qd_python.__file__).resolve()
if binding_path.parent != Path.cwd().resolve():
    raise SystemExit(
        f"Expected the in-place qd_python binding, imported {binding_path}"
    )
qd_records = glob.glob(os.path.join(prefix, "conda-meta", "qd-*.json"))
if len(qd_records) != 1:
    raise SystemExit(f"Expected one QD conda record, found {len(qd_records)}")
with open(qd_records[0], encoding="utf-8") as handle:
    qd_version = json.load(handle)["version"]
if qd_python.__qd_version__ != expected["qd"]:
    raise SystemExit(
        "qd_python was built for QD "
        f"{qd_python.__qd_version__}, expected {expected['qd']}"
    )

actual = {
    "python": platform.python_version(),
    "qd": qd_version,
    "qd_python": qd_python.__version__,
    "pybind11": pybind11.__version__,
    "numpy": numpy.__version__,
    "scipy": scipy.__version__,
    "pytest": pytest.__version__,
    "heyoka": heyoka.__version__,
    "rebound": rebound.__version__,
    "sympy": sympy.__version__,
    "mpmath": mpmath.__version__,
    "jax": jax.__version__,
    "jaxlib": jaxlib.__version__,
    "ml_dtypes": ml_dtypes.__version__,
    "opt_einsum": opt_einsum.__version__,
}
if actual != expected:
    raise SystemExit(
        "Legacy baseline runtime mismatch:\n"
        f"  expected: {expected}\n"
        f"  actual:   {actual}"
    )
PY

case "$MODE" in
  fast)
    exec python -m pytest tests -m "not slow and not legacy_quarantine" --durations=25
    ;;
  slow)
    exec python -m pytest tests -m "slow and not legacy_quarantine" --durations=50
    ;;
  quarantine)
    exec python -m pytest tests -m "legacy_quarantine" --durations=50
    ;;
  collect)
    exec python -m pytest tests --collect-only -q
    ;;
  *)
    echo "Usage: $0 {fast|slow|quarantine|collect}" >&2
    exit 2
    ;;
esac
