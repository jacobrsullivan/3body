from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import sympy as sp

from src.python.wp6_dz_feas_v2.model import build_rectilinear_model


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "validation-external/wp6-dz-feas-v3"
MODEL = ROOT / "src/python/wp6_dz_feas_v2/model.py"
REFERENCE = (
    ROOT
    / "validation-external/wp6-dz-feas-v2/reference/barycentric_reference.py"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reference_module():
    specification = importlib.util.spec_from_file_location(
        "_wp6_v3_reference",
        REFERENCE,
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_frozen_model_and_reference_hashes_match_protocol() -> None:
    protocol = json.loads(
        (CAMPAIGN / "constructive_protocol.json").read_text(encoding="utf-8")
    )
    inherited = protocol["scope_inheritance"]
    assert _sha256(MODEL) == inherited["model_source_sha256"]
    assert _sha256(REFERENCE) == inherited["reference_source_sha256"]


def test_source_disjoint_barycentric_derivation_still_matches() -> None:
    masses = sp.symbols("m1 m2 m3", positive=True)
    production = build_rectilinear_model(masses)
    independent = _reference_module().derive(masses)
    substitution = {
        independent["x"]: production.x,
        independent["v"]: production.v,
        independent["u"]: production.u,
        independent["r"]: production.r,
    }
    assert sp.cancel(production.A - independent["A"].subs(substitution)) == 0
    assert sp.cancel(production.B - independent["B"].subs(substitution)) == 0
    assert sp.cancel(
        production.normalized_energy
        - independent["normalized_energy"].subs(substitution)
    ) == 0
    assert sp.simplify(
        production.mass_metric - independent["mass_metric"]
    ) == sp.zeros(2)
    assert independent["center_of_mass"] == 0
    assert independent["linear_momentum"] == 0


def test_polynomial_energy_numerator_is_exact_on_dense_open() -> None:
    masses = sp.symbols("m1 m2 m3", positive=True)
    model = build_rectilinear_model(masses)
    assert sp.cancel(
        model.energy_numerator
        - 2 * model.x * (1 - model.x) * model.normalized_energy
    ) == 0


def test_reference_source_remains_implementation_disjoint() -> None:
    text = REFERENCE.read_text(encoding="utf-8")
    assert "src.python" not in text
    assert "wp6_dz_feas_v2" not in text
    assert "wp6_dz_feas_v3" not in text
