#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <model-name> <hef-path> [run-dir]" >&2
  exit 2
fi
MODEL_NAME=$1
HEF_PATH=$2
RUN_DIR=${3:-"$BENCH_DIR/results/runs/$(run_id)_${HAILO_DEVICE}_${MODEL_NAME}"}
mkdir -p "$RUN_DIR"

if [[ ! -f "$HEF_PATH" ]]; then
  echo "HEF not found: $HEF_PATH" | tee "$RUN_DIR/latency_hailortcli.txt"
  exit 3
fi

{
  echo "# hailortcli parse-hef"
  hailortcli parse-hef "$HEF_PATH" || true
  echo
  echo "# hailortcli run --measure-latency"
  hailortcli run --measure-latency "$HEF_PATH"
} | tee "$RUN_DIR/latency_hailortcli.txt"

python3 "$BENCH_DIR/src/parse_latency.py" "$RUN_DIR/latency_hailortcli.txt" > "$RUN_DIR/metrics_latency.json"
