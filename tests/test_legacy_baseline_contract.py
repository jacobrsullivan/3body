"""Fail closed when the legacy baseline manifest drifts from collection."""

import json
from collections import Counter
from pathlib import Path

MANIFEST_PATH = Path(__file__).with_name("legacy_baseline_manifest.json")


def _manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_manifest_runtime_is_fully_pinned():
    assert _manifest()["runtime"] == {
        "python": "3.11.15",
        "qd": "2.3.22",
        "qd_python": "1.0.0",
        "pybind11": "2.13.6",
        "numpy": "2.2.6",
        "scipy": "1.16.1",
        "pytest": "8.4.1",
        "heyoka": "7.12.0",
        "rebound": "4.4.10",
        "sympy": "1.14.0",
        "mpmath": "1.4.1",
        "jax": "0.9.0.1",
        "jaxlib": "0.9.0.1",
        "ml_dtypes": "0.5.4",
        "opt_einsum": "3.4.0",
    }


def test_manifest_quarantines_are_exact_and_unique():
    manifest = _manifest()
    slow_selectors = manifest["slow_selectors"]
    entries = manifest["quarantines"]
    nodeids = [entry["nodeid"] for entry in entries]

    assert len(slow_selectors) == 15
    assert len(slow_selectors) == len(set(slow_selectors))
    assert Counter(entry.get("outcome", "xfail") for entry in entries) == {
        "xfail": 79,
        "skip": 8,
    }
    assert len(nodeids) == len(set(nodeids))
    assert all("::test_" in nodeid for nodeid in nodeids)
    assert all(entry["reason"].strip() for entry in entries)
    assert all(entry.get("outcome", "xfail") in {"xfail", "skip"} for entry in entries)
