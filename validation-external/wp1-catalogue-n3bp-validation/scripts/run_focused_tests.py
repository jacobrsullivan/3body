#!/usr/bin/env python
"""Run or verify the frozen WP1-CAT-N3BP-v1 focused-test receipt."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
VALIDATION = ROOT / "validation-external"
sys.path.insert(0, str(VALIDATION))

from qualification_tools import (  # noqa: E402
    atomic_write_json,
    canonical_json,
    load_json,
    runtime_fingerprint,
    sha256_bytes,
    sha256_file,
    utc_now,
)


CAMPAIGN = "WP1-CAT-N3BP-v1"
TEST_SCOPE = Path("tests/wp1_catalogue_n3bp_v1")
NORMALIZED_COMMAND = (
    "python",
    "-m",
    "pytest",
    TEST_SCOPE.as_posix(),
    "-q",
)


def focused_test_input_hashes(root: Path = ROOT) -> dict[str, str]:
    paths = {
        root / "pytest.ini",
        root / "validation-external/qualification_tools.py",
        root
        / "validation-external/wp1-catalogue-n3bp-validation/run_qualification.sh",
    }
    for relative in (
        TEST_SCOPE,
        Path("src/python/wp1_catalogue_n3bp_v1"),
        Path("src/python/n3bp_qualification"),
        Path("validation-external/wp1-catalogue-n3bp-validation/scripts"),
    ):
        paths.update((root / relative).rglob("*.py"))
    if not any(path.is_relative_to(root / TEST_SCOPE) for path in paths):
        raise RuntimeError("focused-test scope contains no Python tests")
    missing = sorted(str(path) for path in paths if not path.is_file())
    if missing:
        raise RuntimeError(f"focused-test inputs are missing: {missing}")
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(paths)
    }


def _unsigned_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    unsigned = dict(receipt)
    unsigned.pop("receipt_sha256", None)
    return unsigned


def verify_receipt(
    receipt_path: str | Path, spec_path: str | Path, root: Path = ROOT
) -> dict[str, Any]:
    receipt = load_json(receipt_path)
    recorded = receipt.get("receipt_sha256")
    actual_hash = sha256_bytes(canonical_json(_unsigned_receipt(receipt)))
    if not recorded or recorded != actual_hash:
        raise RuntimeError("focused-test receipt integrity failure")
    if receipt.get("campaign") != CAMPAIGN or receipt.get("status") != "PASS":
        raise RuntimeError("focused-test receipt is not a passing campaign receipt")
    if receipt.get("spec_sha256") != sha256_file(spec_path):
        raise RuntimeError("focused-test receipt uses another specification")
    if receipt.get("command") != list(NORMALIZED_COMMAND):
        raise RuntimeError("focused-test receipt command mismatch")
    if receipt.get("test_input_hashes") != focused_test_input_hashes(root):
        raise RuntimeError("focused-test inputs changed after receipt generation")
    if receipt.get("runtime") != runtime_fingerprint():
        raise RuntimeError("focused-test receipt runtime differs from current runtime")
    if receipt.get("exit_code") != 0:
        raise RuntimeError("focused-test receipt records a nonzero pytest exit")
    if receipt.get("stdout_sha256") != sha256_bytes(
        str(receipt.get("stdout", "")).encode("utf-8")
    ):
        raise RuntimeError("focused-test receipt stdout hash mismatch")
    if receipt.get("stderr_sha256") != sha256_bytes(
        str(receipt.get("stderr", "")).encode("utf-8")
    ):
        raise RuntimeError("focused-test receipt stderr hash mismatch")
    return receipt


def require_tracked_receipt(receipt_path: str | Path, root: Path = ROOT) -> None:
    receipt = Path(receipt_path).resolve()
    try:
        relative = receipt.relative_to(root.resolve()).as_posix()
    except ValueError as error:
        raise RuntimeError("focused-test receipt is outside the repository") from error
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", relative],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if tracked.returncode != 0:
        raise RuntimeError(
            "focused-test receipt must be committed before qualification freeze"
        )


def run_tests(spec_path: str | Path, output_path: str | Path) -> dict[str, Any]:
    output = Path(output_path).resolve()
    if output.exists():
        raise RuntimeError("refusing to overwrite an existing focused-test receipt")
    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "PYTEST_ADDOPTS": "",
        }
    )
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", TEST_SCOPE.as_posix(), "-q"],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "campaign": CAMPAIGN,
        "generated_utc": utc_now(),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "spec_sha256": sha256_file(spec_path),
        "command": list(NORMALIZED_COMMAND),
        "test_scope": TEST_SCOPE.as_posix(),
        "test_input_hashes": focused_test_input_hashes(),
        "runtime": runtime_fingerprint(),
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "stdout_sha256": sha256_bytes(completed.stdout.encode("utf-8")),
        "stderr_sha256": sha256_bytes(completed.stderr.encode("utf-8")),
    }
    payload["receipt_sha256"] = sha256_bytes(canonical_json(payload))
    atomic_write_json(output, payload)
    if completed.returncode != 0:
        raise RuntimeError(
            f"focused tests failed with exit code {completed.returncode}; "
            f"receipt written to {output}"
        )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("run", "verify"))
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    if args.action == "run":
        receipt = run_tests(args.spec, args.output)
        print(f"focused tests PASS: {receipt['receipt_sha256']}")
    else:
        receipt = verify_receipt(args.output, args.spec)
        require_tracked_receipt(args.output)
        print(f"focused-test receipt verified: {receipt['receipt_sha256']}")


if __name__ == "__main__":
    main()
