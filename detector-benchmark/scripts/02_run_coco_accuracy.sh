#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

if [[ $# -lt 6 ]]; then
  echo "Usage: $0 <model-name> <hef-path> <classes> <height> <width> <run-dir>" >&2
  exit 2
fi
MODEL_NAME=$1; HEF_PATH=$2; CLASSES=$3; HEIGHT=$4; WIDTH=$5; RUN_DIR=$6
PYTHON_BIN=$(resolve_venv_py)
mkdir -p "$RUN_DIR"

IMAGES=$(python3 - <<'PY'
import json
print(json.load(open('configs/datasets.json'))['coco_val2017']['images'])
PY
)
ANN=$(python3 - <<'PY'
import json
print(json.load(open('configs/datasets.json'))['coco_val2017']['annotations'])
PY
)

PRED="$RUN_DIR/predictions_coco.json"
METRICS="$RUN_DIR/metrics_accuracy.json"

set +e
"$PYTHON_BIN" "$BENCH_DIR/src/run_coco_inference.py" \
  --hef "$HEF_PATH" \
  --model-name "$MODEL_NAME" \
  --classes "$CLASSES" \
  --height "$HEIGHT" \
  --width "$WIDTH" \
  --images "$IMAGES" \
  --ann "$ANN" \
  --output "$PRED" \
  --metrics "$METRICS"
EC=$?
set -e

if [[ $EC -eq 0 ]]; then
  exit 0
fi

# HailoRT can abort/segfault during native teardown after successful COCO
# inference/evaluation. Accept only teardown-like native exits and only when
# both predictions and metrics are present and structurally complete.
if [[ $EC -eq 139 || $EC -eq 134 ]]; then
  if python3 - "$PRED" "$METRICS" <<'PY'
import json, sys
pred_path, metrics_path = sys.argv[1:3]
with open(pred_path, 'r', encoding='utf-8') as f:
    preds = json.load(f)
with open(metrics_path, 'r', encoding='utf-8') as f:
    metrics = json.load(f)
if not isinstance(preds, list):
    raise SystemExit(1)
if int(metrics.get('images_processed') or 0) <= 0:
    raise SystemExit(1)
accuracy = metrics.get('accuracy')
if not isinstance(accuracy, dict) or 'mAP50_95' not in accuracy:
    raise SystemExit(1)
PY
  then
    echo "warning: COCO benchmark exited $EC during native teardown after complete metrics; accepting run" >&2
    exit 0
  fi
fi

exit "$EC"
