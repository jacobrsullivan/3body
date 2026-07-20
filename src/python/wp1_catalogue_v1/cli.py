"""Command-line entry point for the phased WP1-CAT-v1 campaign."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import generate_native_catalogue
from .qualification import (
    build_corpus,
    evaluate_split,
    finalize_record,
    freeze_qualification,
    load_json,
    verify_lock,
    write_native_catalogue,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
CAMPAIGN_ROOT = REPO_ROOT / "validation-external/wp1-catalogue-validation"


def _paths() -> dict[str, Path]:
    return {
        "spec": CAMPAIGN_ROOT / "qualification_spec.json",
        "source": REPO_ROOT / "validation-external/wp1-validation/data/jpl/normalized.parquet",
        "corpus": CAMPAIGN_ROOT / "data/corpus.parquet",
        "manifest": CAMPAIGN_ROOT / "data/corpus_manifest.json",
        "holdout_ids": CAMPAIGN_ROOT / "data/holdout_ids.json",
        "catalogue": CAMPAIGN_ROOT / "results/native_catalogue.parquet",
        "provenance": CAMPAIGN_ROOT / "results/native_catalogue_provenance.json",
        "lock": CAMPAIGN_ROOT / "reports/wp1_cat_v1_qualification_lock.json",
    }


def _refuse_existing(*paths: Path) -> None:
    existing = [str(path) for path in paths if path.exists()]
    if existing:
        raise RuntimeError(f"Refusing to overwrite campaign artifacts: {existing}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("build-corpus")
    subparsers.add_parser("generate")
    subparsers.add_parser("freeze")
    evaluate = subparsers.add_parser("evaluate")
    evaluate.add_argument("split", choices=("development", "calibration", "holdout"))
    subparsers.add_parser("finalize")
    subparsers.add_parser("verify-lock")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = _paths()
    if args.command == "build-corpus":
        _refuse_existing(paths["corpus"], paths["manifest"], paths["holdout_ids"])
        result = build_corpus(
            paths["spec"],
            paths["source"],
            paths["corpus"],
            paths["manifest"],
            paths["holdout_ids"],
        )
    elif args.command == "generate":
        _refuse_existing(paths["catalogue"], paths["provenance"])
        run = generate_native_catalogue(load_json(paths["spec"]))
        result = write_native_catalogue(paths["catalogue"], paths["provenance"], run)
    elif args.command == "freeze":
        result = freeze_qualification(REPO_ROOT, CAMPAIGN_ROOT, paths["lock"])
    elif args.command == "evaluate":
        result = evaluate_split(REPO_ROOT, CAMPAIGN_ROOT, args.split)
    elif args.command == "finalize":
        result = finalize_record(REPO_ROOT, CAMPAIGN_ROOT)
    elif args.command == "verify-lock":
        result = verify_lock(paths["lock"], REPO_ROOT)
    else:  # pragma: no cover
        raise AssertionError(args.command)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
