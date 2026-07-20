from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import runpy
import subprocess
import sys

import numpy as np
import pytest

from src.python.wp3_upstairs_v3 import known_module_coefficients


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "validation-external/wp3-upstairs-candidate-v3"


def _json(relative: str):
    return json.loads((CAMPAIGN / relative).read_text(encoding="utf-8"))


def test_v3_spec_declares_exact_module_and_remediation_boundary() -> None:
    spec = _json("search_spec.json")
    assert spec["campaign"] == "WP3-UP-CAND-v3"
    assert spec["library"]["search_feature_count"] == 1120
    assert spec["library"]["exact_constraint_ideal_count"] == 18
    assert spec["library"]["exact_angular_module_count"] == 12
    assert spec["library"]["exact_known_module_rank"] == 30
    assert "previously examined" in spec["evidence_boundary"]


def test_v3_known_module_is_coefficient_independent() -> None:
    module = known_module_coefficients()
    matrix = np.column_stack(tuple(module.values()))
    assert matrix.shape == (1120, 30)
    assert np.linalg.matrix_rank(matrix, tol=1e-12) == 30
    assert sum(name.startswith("known:") and "*" in name for name in module) == 9


def test_v3_runner_uses_physical_and_s1_derivatives() -> None:
    runner = (CAMPAIGN / "scripts/run_search.py").read_text(encoding="utf-8")
    assert "search_quotient_modes" in runner
    assert "s1_generator" in runner
    assert "known_module_coefficients" in runner
    assert "known_module_projection_residual" in runner
    assert "all_generalized_modes_evaluated" in runner
    assert "spectral_decision_partition_consistent" in runner
    assert "physical_point_id" in runner
    assert "_verify_runtime" in runner
    assert "fixed_energy" in runner


def test_v3_final_record_uses_generalized_quotient_metrics() -> None:
    finalizer = (CAMPAIGN / "scripts/finalize_search.py").read_text(encoding="utf-8")
    assert "observable_value_rank" in finalizer
    assert "value_nuisance_derivative_rank" in finalizer
    assert "exact_known_module_rank" in finalizer
    assert "smallest_generalized_lie_value_singular_value" in finalizer
    assert "spectral certificate and candidate subspaces disagree" in finalizer


def test_v3_corpus_excludes_publication_reserve() -> None:
    corpus = _json("data/search_corpus.json")
    assert corpus["corpus_id"] == "wp3-upstairs-v3-exact-module-frozen-corpus"
    assert {case["split"] for case in corpus["cases"]} == {"development", "calibration"}


def test_v3_runtime_is_exact_and_import_closure_is_direct() -> None:
    spec = _json("search_spec.json")
    assert spec["decision_runtime"]["python"] == "3.13.2"
    assert spec["decision_runtime"]["python_implementation"] == "CPython"
    assert spec["decision_runtime"]["platform"]["system"] == "Darwin"
    assert spec["decision_runtime"]["platform"]["machine"] == "arm64"
    assert spec["decision_runtime"]["platform"]["pointer_bits"] == 64
    assert spec["decision_runtime"]["packages"] == {
        "numpy": "2.3.5",
        "scipy": "1.16.3",
    }
    backend = spec["decision_runtime"]["numpy_backend"]
    assert backend["configuration"]["blas"]["name"] == "accelerate"
    assert backend["configuration"]["lapack"]["name"] == "accelerate"
    assert len(spec["decision_runtime"]["numpy_backend"]["sha256"]) == 64
    shell = (CAMPAIGN / "run_search.sh").read_text(encoding="utf-8")
    runner = (CAMPAIGN / "scripts/run_search.py").read_text(encoding="utf-8")
    assert "src/python/wp3_exploration_v2/normalization.py" in shell
    assert "src/python/wp3_exploration_v2/__init__.py" not in shell
    assert "spec_from_file_location" in runner
    assert "wp3_exploration_v2.normalization import" not in runner


def test_v3_decision_runtime_matches_and_rejects_platform_drift() -> None:
    namespace = runpy.run_path(str(CAMPAIGN / "scripts/run_search.py"))
    expected = _json("search_spec.json")["decision_runtime"]
    assert namespace["_verify_runtime"](expected) == expected

    mismatched = deepcopy(expected)
    mismatched["platform"]["machine"] = "x86_64"
    with pytest.raises(RuntimeError, match="decision runtime mismatch"):
        namespace["_verify_runtime"](mismatched)

    mismatched = deepcopy(expected)
    mismatched["numpy_backend"]["configuration"]["blas"]["name"] = "openblas"
    with pytest.raises(RuntimeError, match="decision runtime mismatch"):
        namespace["_verify_runtime"](mismatched)

    backend = expected["numpy_backend"]
    assert namespace["_canonical_sha256"](backend["configuration"]) == backend["sha256"]


def test_v3_runner_local_import_closure_is_frozen() -> None:
    runner = CAMPAIGN / "scripts/run_search.py"
    probe = """
import json
from pathlib import Path
import runpy
import sys

root = Path(sys.argv[1]).resolve()
runpy.run_path(sys.argv[2])
paths = sorted({
    str(Path(module.__file__).resolve().relative_to(root))
    for module in tuple(sys.modules.values())
    if getattr(module, "__file__", None)
    and Path(module.__file__).resolve().is_relative_to(root)
})
print(json.dumps(paths))
"""
    completed = subprocess.run(
        [sys.executable, "-c", probe, str(ROOT), str(runner)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    imported_paths = json.loads(completed.stdout)
    shell = (CAMPAIGN / "run_search.sh").read_text(encoding="utf-8")
    scopes = set(re.findall(r"--scope\s+([^\s\\]+)", shell))

    def covered(path: str) -> bool:
        return any(
            path == scope or path.startswith(scope.rstrip("/") + "/")
            for scope in scopes
        )

    assert imported_paths
    assert all(covered(path) for path in imported_paths), imported_paths
    assert "src/python/wp3_exploration_v2/normalization.py" in imported_paths
    assert not any(
        path.startswith("src/python/wp3_exploration_v2/")
        and path != "src/python/wp3_exploration_v2/normalization.py"
        for path in imported_paths
    )
    assert "validation-external/verify_qualification.py" in scopes
