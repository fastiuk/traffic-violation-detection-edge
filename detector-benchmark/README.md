# Detector Benchmark

Detector-only research harness for the traffic-violation thesis.

Purpose: compare vehicle/object detectors on Raspberry Pi 5 + Hailo NPU using repeatable accuracy, latency, throughput, and metadata collection.

## Scientific constraints

- COCO mAP requires COCO annotations. Raw videos are not accuracy data unless annotated.
- Keep hardware latency separate from end-to-end throughput.
- Do not compare Hailo-8L vs Hailo-10H unless model, dataset, resolution, preprocessing, and postprocessing are identical.
- Failed model download/HEF parse/inference is recorded as a reproducibility failure, not as `0 mAP`.

## Target device

Configured in `configs/device.env`:

```text
pi@10.10.10.21:/home/pi/traffic-violation-detection-edge
```

## Prepare datasets on the RPi

Use the global setup scripts from the repository root:

```bash
./setup/download_coco_val2017.sh
./setup/download_video_footage_dataset.py
```

COCO is used for detector mAP. The video footage is unannotated and is only
valid for throughput, detection-count trends, and qualitative inspection.

## Copy code to the RPi

This benchmark is intended to execute on the Raspberry Pi target. From the
control machine, copy the repository with `rclone` or `rsync`; do not copy Git
metadata, local AI-agent context, generated results, datasets, model caches, or
Python bytecode.

If you use delete semantics (`rclone sync` or `rsync --delete`), keep the
dataset and model-cache excludes below. Otherwise the Pi will delete
`dataset/` and downloaded HEF/model files, forcing a full re-download.
Never combine these commands with `--delete-excluded`.

Example with `rclone` over SFTP:

```bash
rclone sync . rpi5:traffic-violation-detection-edge \
  --exclude '.git/**' \
  --exclude '.ai/**' \
  --exclude '.codex/**' \
  --exclude '.gemini/**' \
  --exclude '.claude/**' \
  --exclude '**/__pycache__/**' \
  --exclude 'detector-benchmark/results/**' \
  --exclude 'detector-benchmark/logs/**' \
  --exclude 'dataset/**' \
  --exclude 'performance-benchmark/models/**'
```

Equivalent `rsync`:

```bash
rsync -avz --delete \
  --exclude '.git' \
  --exclude '.ai' \
  --exclude '.codex' \
  --exclude '.gemini' \
  --exclude '.claude' \
  --exclude '__pycache__' \
  --exclude 'detector-benchmark/results/' \
  --exclude 'detector-benchmark/logs/' \
  --exclude 'dataset/' \
  --exclude 'performance-benchmark/models/' \
  . pi@10.10.10.21:~/traffic-violation-detection-edge/
```

## Run on the RPi

```bash
ssh pi@10.10.10.21
cd ~/traffic-violation-detection-edge
./detector-benchmark/scripts/00_check_environment.sh
./detector-benchmark/scripts/run_all.sh
```

`run_all.sh` measures Hailo hardware latency and COCO accuracy by default.
The unannotated traffic-video benchmark is kept for qualitative/throughput
inspection, but is skipped unless explicitly enabled:

```bash
RUN_VIDEO_BENCHMARK=1 ./detector-benchmark/scripts/run_all.sh
```

Results are written on the RPi under:

```text
~/traffic-violation-detection-edge/detector-benchmark/results/runs/
```

Pull them back with:

```bash
rsync -avz pi@10.10.10.21:~/traffic-violation-detection-edge/detector-benchmark/results/ detector-benchmark/results/
```
