#!/usr/bin/env python
"""Generate the native WP1-CAT-N3BP-v1 payload without external rows."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
VALIDATION = ROOT / "validation-external"
for path in (ROOT, VALIDATION, Path(__file__).resolve().parent):
    sys.path.insert(0, str(path))

from campaign_common import (  # noqa: E402
    require_source_free_generation_event,
    verify_prerequisite,
    verify_specification_lock,
)
from qualification_tools import (  # noqa: E402
    atomic_write_json,
    load_json,
    runtime_fingerprint,
    sha256_file,
    utc_now,
)
from src.python.wp1_catalogue_n3bp_v1 import (  # noqa: E402
    canonical_catalogue_payload,
    catalogue_sha256,
    generate_catalogue,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()

    output = Path(args.output).resolve()
    if output.exists():
        raise RuntimeError("refusing to overwrite an existing native candidate payload")
    require_source_free_generation_event()
    specification_lock = verify_specification_lock(args.spec)
    spec = load_json(args.spec)
    prerequisite = verify_prerequisite(spec)

    run = generate_catalogue(workers=args.workers)
    catalogue = json.loads(canonical_catalogue_payload(run.candidates))
    expected = int(spec["execution"]["expected_candidate_count"])
    if len(run.candidates) != expected:
        raise RuntimeError(
            f"native generator produced {len(run.candidates)} candidates, expected {expected}"
        )
    payload = {
        "schema_version": "1.0",
        "campaign": spec["campaign"],
        "generated_utc": utc_now(),
        "spec_sha256": sha256_file(args.spec),
        "specification_lock_sha256": specification_lock[
            "specification_lock_sha256"
        ],
        "prerequisite": prerequisite,
        "runtime": runtime_fingerprint(),
        "elapsed_seconds": run.elapsed_seconds,
        "workers": args.workers,
        "provenance": asdict(run.provenance),
        "external_input_arguments": [],
        "catalogue_sha256": catalogue_sha256(run.candidates),
        **catalogue,
    }
    atomic_write_json(output, payload)
    print(
        f"generated {len(run.candidates)} native candidates in "
        f"{run.elapsed_seconds:.1f}s: {payload['catalogue_sha256']}"
    )


if __name__ == "__main__":
    main()
