---
name: rpi5-hailo
description: Performance benchmarking and object detection research on Raspberry Pi 5 with Hailo-8L NPU. Use when working on the traffic-violation-detection-edge project, measuring inference latency, or conducting comparative analysis (CPU vs NPU, int8 vs int4).
---

# Hailo RPi5 Benchmarking Skill

This skill provides the workflows and technical details for the dissertation research setup involving Raspberry Pi 5 and Hailo-8L.

## Core Setup
- **Target IP:** `10.10.10.21` (pi:pi)
- **Venv Path:** `~/hailo-rpi5-examples/venv_hailo_rpi_examples/`
- **Project Root:** `~/traffic-violation-detection-edge/`

See [rpi-hailo-setup.md](references/rpi-hailo-setup.md) for full environmental details.

## Development Workflow (MANDATORY)
Always follow this 'Local-First' cycle:
1.  **Edit Locally:** Make all code changes in the local workspace folders.
2.  **Sync to RPi:** Use `rsync` (or `rclone`) to push the entire project to the RPi.
3.  **Execute on RPi:** Run the code via SSH using the virtual environment.

**Sync Command:**
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
  --exclude 'evaluation/**' \
  --exclude 'video-footage-dataset/**' \
  --exclude 'performance-benchmark/models/**'
```

Do not use `--delete-excluded`. Dataset folders and model caches must remain on the RPi across code syncs.

## Common Workflows

### 1. Connecting to RPi5
Always verify connection before running tasks:
```bash
ping -c 1 10.10.10.21
ssh pi@10.10.10.21 "hailortcli scan"
```

### 2. Measuring HW Latency
Use `hailortcli` for the most accurate hardware-level measurements:
```bash
ssh pi@10.10.10.21 "hailortcli run --measure-latency /path/to/model.hef"
```

### 3. Running Application Benchmarks
Execute the Flask-based inference scripts (always sync before running):
```bash
ssh pi@10.10.10.21 "~/hailo-rpi5-examples/venv_hailo_rpi_examples/bin/python ~/traffic-violation-detection-edge/performance-benchmark/src/hailo_inference_web.py"
```

### 4. Running Custom NPU Benchmarks
```bash
ssh pi@10.10.10.21 "~/traffic-violation-detection-edge/hailo-npu-benchmarks/accuracy_test.sh"
ssh pi@10.10.10.21 "~/traffic-violation-detection-edge/hailo-npu-benchmarks/video_test.sh [DATASET_PATH] [MODE]"
```

### 5. Running Continuous Automated Testbench
Execute the multi-model evaluation loop:
```bash
ssh pi@10.10.10.21 "chmod +x ~/traffic-violation-detection-edge/hailo-npu-benchmarks/run_continuous_testbench.sh"
ssh pi@10.10.10.21 "~/traffic-violation-detection-edge/hailo-npu-benchmarks/run_continuous_testbench.sh"
```

### 6. Generating Dissertation Report
Aggregate all results into a Markdown report:
```bash
ssh pi@10.10.10.21 "cd ~/traffic-violation-detection-edge/hailo-npu-benchmarks && ~/hailo-rpi5-examples/venv_hailo_rpi_examples/bin/python generate_report.py"
```

## Methodology & Analysis
- **Warm-up:** Discard first 50-100 frames for stable results.
- **Metrics:** Prioritize `Hardware Latency` (ms) and `FPS`.
- **Comparison:** Cross-reference `Hardware Latency` at equal `FPS` to identify CPU/Bus bottlenecks.

See [benchmarking-methodology.md](references/benchmarking-methodology.md) for detailed research procedures.
