#!/usr/bin/env bash
set -euo pipefail

# Native Raspberry Pi OS / Debian setup for Raspberry Pi 5 + Hailo AI Kit.
# The repository README documents the Ubuntu/proprietary-installer path. This
# script is for the Debian/Raspberry Pi package route where Hailo packages are
# available from the Raspberry Pi apt repository.

if [[ $(id -u) -ne 0 ]]; then
  SUDO=sudo
else
  SUDO=
fi

$SUDO apt update
$SUDO apt install -y \
  hailo-all \
  python3-hailort \
  hailo-models \
  python3-pip \
  python3-venv \
  python3-opencv \
  python3-requests \
  python3-tqdm \
  unzip \
  wget \
  ffmpeg

$SUDO python3 -m venv --system-site-packages /opt/hailo_env
$SUDO /opt/hailo_env/bin/python -m pip install --upgrade pip
$SUDO /opt/hailo_env/bin/pip install pycocotools

hailortcli --version
hailortcli scan
/opt/hailo_env/bin/python - <<'PY'
import cv2, numpy, requests, tqdm, hailo_platform
from pycocotools.coco import COCO
print('Hailo Python environment OK')
PY
