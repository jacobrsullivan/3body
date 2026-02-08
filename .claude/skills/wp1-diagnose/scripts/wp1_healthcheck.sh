#!/usr/bin/env bash
set -euo pipefail

repo="/Users/jacobsullivan/.codex/worktrees/8fe0/3body"
cd "$repo"

echo "[wp1-health] verify_setup"
python verify_setup.py

echo "[wp1-health] data directories"
for d in data data/tier1 data/tier2; do
  if [ -d "$d" ]; then
    echo "[ok] $d"
  else
    echo "[missing] $d"
  fi
 done

echo "[wp1-health] sample hdf5"
ls -1 data/tier1/hdf5 2>/dev/null | head -n 3 || true

echo "[wp1-health] done"
