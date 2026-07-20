"""Expose only the external WP2 Kepler validation scripts to these tests."""

from pathlib import Path
import sys


SCRIPTS_DIR = (
    Path(__file__).resolve().parents[2]
    / "validation-external"
    / "wp2-ks-validation"
    / "scripts"
)
sys.path.insert(0, str(SCRIPTS_DIR))

EVALUATION_DIR = SCRIPTS_DIR.parent / "evaluation"
sys.path.insert(0, str(EVALUATION_DIR))
