#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
EXPECTED_PYTHON="3.11.15"
EXPECTED_QD="2.3.22"
EXPECTED_BINDING="1.0.0"
EXPECTED_PYBIND11="2.13.6"

cd "$ROOT_DIR"

if [[ -z "${CONDA_PREFIX:-}" ]]; then
  echo "CONDA_PREFIX must identify the pinned conda environment." >&2
  exit 2
fi

"$PYTHON_BIN" - "$CONDA_PREFIX" <<'PY'
from pathlib import Path
import sys

expected = Path(sys.argv[1]).resolve()
actual = Path(sys.prefix).resolve()
if actual != expected:
    raise SystemExit(
        f"Running Python prefix {actual} does not match CONDA_PREFIX {expected}"
    )
PY

actual_python="$("$PYTHON_BIN" -c 'import platform; print(platform.python_version())')"
if [[ "$actual_python" != "$EXPECTED_PYTHON" ]]; then
  echo "Expected Python $EXPECTED_PYTHON, found $actual_python." >&2
  exit 2
fi

actual_pybind11="$("$PYTHON_BIN" -c 'import pybind11; print(pybind11.__version__)')"
if [[ "$actual_pybind11" != "$EXPECTED_PYBIND11" ]]; then
  echo "Expected pybind11 $EXPECTED_PYBIND11, found $actual_pybind11." >&2
  exit 2
fi

actual_qd="$("$PYTHON_BIN" - "$CONDA_PREFIX" <<'PY'
import glob
import json
import os
import sys

records = glob.glob(os.path.join(sys.argv[1], "conda-meta", "qd-*.json"))
if len(records) != 1:
    raise SystemExit(f"Expected one QD conda record, found {len(records)}")
with open(records[0], encoding="utf-8") as handle:
    print(json.load(handle)["version"])
PY
)"
if [[ "$actual_qd" != "$EXPECTED_QD" ]]; then
  echo "Expected QD $EXPECTED_QD, found $actual_qd." >&2
  exit 2
fi

QD_ROOT="$CONDA_PREFIX" "$PYTHON_BIN" setup.py build_ext --inplace --force
"$PYTHON_BIN" - "$EXPECTED_BINDING" "$EXPECTED_QD" <<'PY'
from pathlib import Path
import qd_python
import sys

assert qd_python.__version__ == sys.argv[1]
assert qd_python.__qd_version__ == sys.argv[2]
assert Path(qd_python.__file__).resolve().parent == Path.cwd().resolve()
print(f"qd_python {qd_python.__version__} linked for QD {qd_python.__qd_version__}")
PY
