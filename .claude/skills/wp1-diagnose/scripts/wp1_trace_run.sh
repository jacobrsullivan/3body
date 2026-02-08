#!/usr/bin/env bash
set -euo pipefail

repo="/Users/jacobsullivan/.codex/worktrees/8fe0/3body"
cd "$repo"

pattern="${1:-error}"

if command -v rg >/dev/null 2>&1; then
  rg -n "$pattern" data || true
else
  grep -Rni "$pattern" data || true
fi
