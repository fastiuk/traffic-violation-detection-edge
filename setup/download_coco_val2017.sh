#!/usr/bin/env bash
set -euo pipefail

# Download the official COCO 2017 validation images and annotations used by
# the Hailo accuracy benchmark scripts.
#
# Default target matches the benchmark code paths:
#   ~/traffic-violation-detection-edge/evaluation/val2017
#   ~/traffic-violation-detection-edge/evaluation/annotations/instances_val2017.json
#
# Usage:
#   ./setup/download_coco_val2017.sh [evaluation_dir]

EVAL_DIR="${1:-$HOME/traffic-violation-detection-edge/evaluation}"
mkdir -p "$EVAL_DIR"
cd "$EVAL_DIR"

download_extract_zip() {
  local url="$1"
  local zip_name="$2"
  local marker_path="$3"

  if [[ -e "$marker_path" ]]; then
    echo "Already present: $marker_path"
    return
  fi

  echo "Downloading $zip_name..."
  wget -c "$url" -O "$zip_name"

  echo "Extracting $zip_name..."
  unzip -q -o "$zip_name"
  rm -f "$zip_name"
}

download_extract_zip \
  "http://images.cocodataset.org/annotations/annotations_trainval2017.zip" \
  "annotations_trainval2017.zip" \
  "$EVAL_DIR/annotations/instances_val2017.json"

download_extract_zip \
  "http://images.cocodataset.org/zips/val2017.zip" \
  "val2017.zip" \
  "$EVAL_DIR/val2017"

echo "COCO Val2017 ready under: $EVAL_DIR"
echo "Images:      $EVAL_DIR/val2017"
echo "Annotations: $EVAL_DIR/annotations/instances_val2017.json"
