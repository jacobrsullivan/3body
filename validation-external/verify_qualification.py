#!/usr/bin/env python
"""Verify every frozen file in a qualification lock."""

from __future__ import annotations

import argparse

from qualification_tools import verify_lock


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--lock", required=True)
    parser.add_argument("--prefix", required=True)
    args = parser.parse_args()
    lock = verify_lock(args.lock, args.repo_root, expected_prefix=args.prefix)
    print(
        f"Verified {lock['qualification_id']} "
        f"({len(lock['file_hashes'])} frozen files)"
    )


if __name__ == "__main__":
    main()
