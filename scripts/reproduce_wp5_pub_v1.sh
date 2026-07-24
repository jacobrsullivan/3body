#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:---core}"
PYTHON_BIN="${WP5_PYTHON:-python}"
MANUSCRIPT_DIR="$ROOT_DIR/publication/wp5-pub-v1/manuscript"
BUILD_DIR="$ROOT_DIR/build/wp5-pub-v1"
OUTPUT_DIR="$ROOT_DIR/output/pdf"

case "$MODE" in
  --static)
    VERIFY_MODE="static"
    ;;
  --core)
    VERIFY_MODE="core"
    ;;
  --full)
    VERIFY_MODE="full"
    ;;
  *)
    echo "Usage: $0 {--static|--core|--full}" >&2
    exit 2
    ;;
esac

command -v "$PYTHON_BIN" >/dev/null
command -v tectonic >/dev/null
command -v pdfinfo >/dev/null
command -v pdftotext >/dev/null

mkdir -p "$BUILD_DIR" "$OUTPUT_DIR"
export SOURCE_DATE_EPOCH=1784851200
export TZ=UTC

if ! tectonic \
  --only-cached \
  --keep-logs \
  --outdir "$MANUSCRIPT_DIR" \
  "$MANUSCRIPT_DIR/main.tex"
then
  echo "Cached TeX bundle incomplete; retrying with bundle downloads enabled." >&2
  tectonic \
    --keep-logs \
    --outdir "$MANUSCRIPT_DIR" \
    "$MANUSCRIPT_DIR/main.tex"
fi

cp \
  "$MANUSCRIPT_DIR/main.pdf" \
  "$OUTPUT_DIR/wp5-pub-v1-manuscript.pdf"

"$PYTHON_BIN" \
  "$ROOT_DIR/validation-external/wp5-pub-v1/scripts/build_artifact_manifest.py"

"$PYTHON_BIN" \
  "$ROOT_DIR/validation-external/wp5-pub-v1/scripts/verify_package.py" \
  --mode "$VERIFY_MODE" \
  --output "$BUILD_DIR/${VERIFY_MODE}_reproduction_report.json"

echo "WP5-PUB-v1 $VERIFY_MODE replay passed."
echo "Report: $BUILD_DIR/${VERIFY_MODE}_reproduction_report.json"
