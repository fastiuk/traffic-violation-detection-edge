#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
BENCH_DIR=$(cd -- "$SCRIPT_DIR/.." && pwd)
REPO_DIR=$(cd -- "$BENCH_DIR/.." && pwd)
DEVICE_ENV="$BENCH_DIR/configs/device.env"

if [[ -f "$DEVICE_ENV" ]]; then
  # shellcheck source=/dev/null
  source "$DEVICE_ENV"
fi

: "${RPI_HOST:=10.10.10.21}"
: "${RPI_USER:=pi}"
: "${RPI_PROJECT_DIR:=/home/pi/traffic-violation-detection-edge}"
: "${RPI_VENV_PY:=/home/pi/hailo-rpi5-examples/venv_hailo_rpi_examples/bin/python}"
: "${HAILO_DEVICE:=hailo8l}"
: "${RPI_SSH_KEY:=}"

ssh_base() {
  if [[ -n "${RPI_SSH_KEY:-}" ]]; then
    ssh -i "$RPI_SSH_KEY" -o BatchMode=yes -o ConnectTimeout=10 "$@"
  else
    ssh -o BatchMode=yes -o ConnectTimeout=10 "$@"
  fi
}


resolve_venv_py() {
  if [[ -x "${RPI_VENV_PY:-}" ]]; then
    printf '%s\n' "$RPI_VENV_PY"
  elif [[ -x "/opt/hailo_env/bin/python" ]]; then
    printf '%s\n' "/opt/hailo_env/bin/python"
  elif [[ -x "$HOME/hailo-rpi5-examples/venv_hailo_rpi_examples/bin/python" ]]; then
    printf '%s\n' "$HOME/hailo-rpi5-examples/venv_hailo_rpi_examples/bin/python"
  else
    printf '%s\n' "${RPI_VENV_PY:-/opt/hailo_env/bin/python}"
  fi
}

run_id() {
  date -u +'%Y%m%dT%H%M%SZ'
}

json_get_model_count() {
  python3 - "$BENCH_DIR/configs/models.json" <<'PY'
import json, sys
print(len(json.load(open(sys.argv[1]))))
PY
}

json_get_model() {
  local index=$1 key=$2
  python3 - "$BENCH_DIR/configs/models.json" "$index" "$key" <<'PY'
import json, sys
models=json.load(open(sys.argv[1]))
value=models[int(sys.argv[2])][sys.argv[3]]
if isinstance(value, (list, dict)):
    print(json.dumps(value))
else:
    print(value)
PY
}

ensure_dir() {
  mkdir -p "$1"
}
