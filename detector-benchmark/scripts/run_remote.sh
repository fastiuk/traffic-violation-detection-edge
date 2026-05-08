#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <remote-command-or-script> [args...]" >&2
  exit 2
fi

cmd="$1"; shift || true
case "$cmd" in
  ./*) remote_cmd="$RPI_PROJECT_DIR/${cmd#./}" ;;
  /*) remote_cmd="$cmd" ;;
  *) remote_cmd="$cmd" ;;
esac

ssh_base -t "$RPI_USER@$RPI_HOST" "cd '$RPI_PROJECT_DIR' && '$remote_cmd' $*"
