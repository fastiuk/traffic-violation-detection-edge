#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

cd "$RPI_PROJECT_DIR" 2>/dev/null || cd "$(pwd)"
PYTHON_BIN=$(resolve_venv_py)

echo "## Host"
hostname || true
hostname -I || true
uname -a || true
cat /etc/os-release 2>/dev/null || true

printf '\n## Python\n'
if [[ -x "$PYTHON_BIN" ]]; then
  "$PYTHON_BIN" --version
  "$PYTHON_BIN" - <<'PY' || true
mods=['cv2','numpy','pycocotools','hailo_platform']
for m in mods:
    try:
        mod=__import__(m)
        print(f'{m}: OK {getattr(mod, "__version__", "")}')
    except Exception as e:
        print(f'{m}: FAIL {e}')
PY
else
  echo "Missing venv python: $RPI_VENV_PY"
fi

printf '\n## Hailo\n'
command -v hailortcli || true
hailortcli --version 2>/dev/null || true
hailortcli scan || true

printf '\n## Dataset\n'
python3 - <<'PY'
import json, pathlib
cfg=json.load(open('detector-benchmark/configs/datasets.json'))
for name,d in cfg.items():
    print(name)
    for k in ('images','annotations','path'):
        if k in d:
            p=pathlib.Path(d[k]).expanduser()
            print(f'  {k}: {p} exists={p.exists()}')
PY

printf '\n## Models config\n'
python3 -m json.tool detector-benchmark/configs/models.json >/dev/null && echo OK
