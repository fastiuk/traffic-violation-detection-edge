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
mkdir -p "$RUN_DIR/video_overlays"

VIDEO_DIR=$(python3 - <<'PY'
import json
print(json.load(open('configs/datasets.json'))['traffic_videos']['path'])
PY
)

set +e
"$PYTHON_BIN" "$BENCH_DIR/src/run_video_benchmark.py" \
  --video-dir "$VIDEO_DIR" \
  --hef "$HEF_PATH" \
  --model-name "$MODEL_NAME" \
  --classes "$CLASSES" \
  --height "$HEIGHT" \
  --width "$WIDTH" \
  --output-dir "$RUN_DIR/video_overlays" \
  --metrics "$RUN_DIR/metrics_video.json"
EC=$?
set -e

if [[ $EC -eq 0 ]]; then
  exit 0
fi

# HailoRT/OpenCV on the Pi can segfault during native teardown after the
# benchmark has completed and flushed metrics. Treat only that specific native
# teardown crash as success, and only if the metrics are structurally complete.
if [[ $EC -eq 139 || $EC -eq 134 ]]; then
  if python3 - "$RUN_DIR/metrics_video.json" <<'PY'
import json, sys
path = sys.argv[1]
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)
videos = data.get('videos')
if not isinstance(videos, list) or not videos:
    raise SystemExit(1)
bad = [v.get('video', '<unknown>') for v in videos
       if v.get('status') != 'ok' or int(v.get('frames') or 0) <= 0]
if bad:
    print('incomplete video metrics for: ' + ', '.join(bad), file=sys.stderr)
    raise SystemExit(1)
PY
  then
    echo "warning: video benchmark exited $EC during native teardown after complete metrics; accepting run" >&2
    exit 0
  fi
fi

exit "$EC"
