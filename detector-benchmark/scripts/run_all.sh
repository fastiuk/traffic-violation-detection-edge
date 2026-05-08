#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

cd "$RPI_PROJECT_DIR"
MODELS_DIR="$RPI_PROJECT_DIR/performance-benchmark/models"
mkdir -p "$MODELS_DIR" "$BENCH_DIR/results/runs" "$BENCH_DIR/logs"
MASTER="$BENCH_DIR/results/master_detector_results.jsonl"
: > "$MASTER"

count=$(json_get_model_count)
echo "Starting detector benchmark: $count models"
if [[ -n "${BENCH_MODEL_FILTER:-}" ]]; then
  echo "Model filter: $BENCH_MODEL_FILTER"
fi

for ((i=0; i<count; i++)); do
  NAME=$(json_get_model "$i" name)
  if [[ -n "${BENCH_MODEL_FILTER:-}" && ",$BENCH_MODEL_FILTER," != *",$NAME,"* ]]; then
    continue
  fi
  URL=$(json_get_model "$i" hef_url)
  CLASSES=$(json_get_model "$i" classes)
  SHAPE=$(json_get_model "$i" input_shape)
  HEIGHT=$(python3 - <<PY
import json
print(json.loads('$SHAPE')[0])
PY
)
  WIDTH=$(python3 - <<PY
import json
print(json.loads('$SHAPE')[1])
PY
)
  RUN_ID="$(run_id)_${HAILO_DEVICE}_${NAME}_${HEIGHT}x${WIDTH}"
  RUN_DIR="$BENCH_DIR/results/runs/$RUN_ID"
  HEF="$MODELS_DIR/${NAME}_${HAILO_DEVICE}.hef"
  mkdir -p "$RUN_DIR"

  echo "=== [$((i+1))/$count] $NAME ==="
  python3 "$BENCH_DIR/src/write_run_metadata.py" \
    --run-dir "$RUN_DIR" --run-id "$RUN_ID" --model-index "$i" \
    --models-config "$BENCH_DIR/configs/models.json" --device-env "$DEVICE_ENV"

  if [[ ! -f "$HEF" ]]; then
    echo "Downloading $NAME"
    if ! wget -q --show-progress "$URL" -O "$HEF"; then
      echo "download_failed" > "$RUN_DIR/status.txt"
      python3 "$BENCH_DIR/src/summarize_run.py" "$RUN_DIR" >> "$MASTER" || true
      continue
    fi
  fi

  set +e
  "$SCRIPT_DIR/01_measure_latency.sh" "$NAME" "$HEF" "$RUN_DIR" > "$RUN_DIR/step_latency.log" 2>&1
  latency_ec=$?
  "$SCRIPT_DIR/02_run_coco_accuracy.sh" "$NAME" "$HEF" "$CLASSES" "$HEIGHT" "$WIDTH" "$RUN_DIR" > "$RUN_DIR/step_coco.log" 2>&1
  coco_ec=$?
  "$SCRIPT_DIR/03_run_video_benchmark.sh" "$NAME" "$HEF" "$CLASSES" "$HEIGHT" "$WIDTH" "$RUN_DIR" > "$RUN_DIR/step_video.log" 2>&1
  video_ec=$?
  set -e

  printf '{"latency":%s,"coco":%s,"video":%s}\n' "$latency_ec" "$coco_ec" "$video_ec" > "$RUN_DIR/exit_codes.json"
  if [[ $latency_ec -eq 0 && $coco_ec -eq 0 && $video_ec -eq 0 ]]; then
    echo complete > "$RUN_DIR/status.txt"
  else
    echo partial_or_failed > "$RUN_DIR/status.txt"
  fi
  python3 "$BENCH_DIR/src/summarize_run.py" "$RUN_DIR" >> "$MASTER"
done

python3 "$BENCH_DIR/src/generate_detector_report.py" "$BENCH_DIR/results" \
  > "$BENCH_DIR/results/detector_comparison.md"
echo "Done. Report: $BENCH_DIR/results/detector_comparison.md"
