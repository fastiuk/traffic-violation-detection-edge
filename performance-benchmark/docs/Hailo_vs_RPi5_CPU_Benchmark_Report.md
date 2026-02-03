# Comparative Analysis: Object Detection Performance on Raspberry Pi 5 CPU vs. Hailo-8L AI Accelerator

## 1. Executive Summary

This report documents a benchmark study comparing the inference performance of the YOLOv5s object detection model on a Raspberry Pi 5. The study contrasts the performance of the device's native CPU (Quad-core Arm Cortex-A76) against the dedicated Hailo-8L AI Accelerator connected via PCIe.

**Key Findings:**
*   **Performance Gain:** The Hailo-8L accelerator provided an **8.7x increase** in frame rate compared to the CPU (14.83 FPS vs. 1.69 FPS) in a live application scenario.
*   **Hardware Efficiency:** In pure hardware benchmarking (excluding application overhead), the Hailo-8L achieved **29.34 FPS**, demonstrating a potential **~17x** theoretical improvement.
*   **System Resource Usage:** CPU inference saturated all four cores (100% load), whereas Hailo inference maintained a low system load average (0.55), freeing up the CPU for other tasks.

## 2. Experimental Setup

### 2.1 Hardware Configuration
*   **Host Device:** Raspberry Pi 5 (8GB RAM)
*   **Processor:** Broadcom BCM2712, Quad-core Arm Cortex-A76 @ 2.4GHz
*   **AI Accelerator:** Hailo-8L AI Processor (M.2 Key M module via PCIe HAT+)
*   **Input Device:** Standard USB Webcam (/dev/video0)
*   **Connectivity:** Headless setup accessed via SSH; video output streamed via MJPEG over HTTP.

### 2.2 Software Environment
*   **Operating System:** Ubuntu 24.04 LTS (Noble Numbat)
    *   *Note:* Selected over Raspberry Pi OS (Debian Trixie) to ensure compatibility with Python 3.12 and available Hailo binary wheels.
*   **Kernel:** Linux 6.8.0-1044-raspi (aarch64)
*   **Python Version:** 3.12.3
*   **AI Frameworks:**
    *   **CPU:** ONNX Runtime (CPUExecutionProvider)
    *   **Accelerator:** HailoRT (Hailo Runtime) v4.23.0
*   **Drivers:** Hailo PCIe Driver v4.23.0

### 2.3 Models
*   **Architecture:** YOLOv5s (Small variant)
*   **Input Resolution:** 640x640 pixels
*   **Formats:**
    *   **CPU:** `yolov5s.onnx` (Standard ONNX export)
    *   **Hailo:** `yolov5s_h8l.hef` (Compiled Hailo Executable Format for Hailo-8L architecture)

## 3. Methodology

Two distinct testing pipelines were developed to ensure a fair comparison. Both pipelines consumed live video frames from the same camera source, performed necessary preprocessing (resizing, normalization/type conversion), ran inference, and served the resulting video stream to a web browser for validation.

### 3.1 Pipeline 1: CPU Inference
*   **Library:** `onnxruntime`
*   **Preprocessing:** Resize to 640x640, convert to RGB, normalize pixel values to [0, 1] float32, CHW layout.
*   **Inference:** Synchronous execution on CPU.
*   **Optimization:** Network streaming limited to every 3rd frame to isolate inference computational cost.

### 3.2 Pipeline 2: Hailo-8L Inference
*   **Library:** `hailo_platform` (Python bindings)
*   **Preprocessing:** Resize to 640x640, convert to RGB, cast to `uint8` (No normalization required, handled by hardware), NHWC layout.
*   **Inference:** Synchronous execution on Hailo-8L VDevice.
*   **Optimization:** Network streaming limited to every 3rd frame. Explicit buffer management was implemented to handle NMS (Non-Maximum Suppression) output layers correctly.

### 3.3 Hardware Benchmark
A purely synthetic benchmark was run using the `hailortcli` tool to establish the theoretical maximum throughput of the hardware, eliminating Python and OpenCV overhead.

## 4. Implementation Challenges & Solutions

Significant technical hurdles were overcome to establish a stable testing environment.

### 4.1 Dependency Conflicts & ABI Issues
*   **Issue:** Initial attempts on Debian Trixie (Python 3.13) failed because Hailo provides pre-compiled Python wheels only for Python 3.8–3.12.
*   **Solution:** Migrated OS to Ubuntu 24.04 (Python 3.12 default).

### 4.2 Driver Version Mismatch
*   **Issue:** A mismatch between the Hailo Runtime (4.23.0) and the PCIe Driver (5.2.0) caused initialization failures (`HAILO_OUT_OF_PHYSICAL_DEVICES`).
*   **Solution:** Downgraded the PCIe driver to version 4.23.0 to ensure ABI compatibility between the kernel module and userspace library.

### 4.3 Kernel Page Size
*   **Issue:** The Hailo driver requires a 4KB memory page size. The Raspberry Pi 5 kernel defaults to 16KB pages for performance.
*   **Solution:** Modified `/boot/firmware/config.txt` to force the use of the `kernel8.img` kernel variant, ensuring 4KB page size compatibility.

### 4.4 Python API & Buffer Management
*   **Issue:** The high-level Python API threw `HailoRTInvalidOperationException` and "buffer as view" errors when handling models with NMS post-processing layers.
*   **Solution:** Implemented manual output buffer allocation using `create_bindings(output_buffers=...)` with explicitly typed `numpy` arrays to correctly map the dynamic NMS output.

## 5. Results & Analysis

### 5.1 Quantitative Results

| Metric | RPi 5 CPU | Hailo-8L (App) | Hailo-8L (Raw HW) |
| :--- | :--- | :--- | :--- |
| **Average FPS** | **1.69** | **14.83** | **29.34** |
| **Inference Time** | ~570 ms | ~43 ms | ~32 ms |
| **CPU Load** | 100% (All Cores) | ~15% (Idle) | N/A |

### 5.2 Analysis of Discrepancies
*   **HW vs. App Performance:** The Hailo hardware is capable of ~30 FPS. The application achieved ~15 FPS. The gap (approx. 33ms per frame) is attributed to single-threaded Python overhead:
    *   Frame Capture (OpenCV)
    *   Resizing & Color Conversion (CPU)
    *   JPEG Encoding for Web Stream (CPU)
*   **CPU Bottleneck:** The CPU implementation was entirely compute-bound by the inference task itself (570ms latency), rendering overhead negligible.

### 5.3 Resource Utilization
*   **CPU Scenario:** The system was fully saturated. `htop` showed 100% utilization across all cores, making the system unresponsive to other tasks.
*   **Hailo Scenario:** The system remained responsive. The CPU load average was 0.55 (vs 2.74+ on CPU test), confirming that the NPU successfully offloaded the compute-heavy inference task.

## 6. Conclusion

The integration of the Hailo-8L accelerator transforms the Raspberry Pi 5 from a device incapable of real-time modern object detection (running at <2 FPS) into a capable edge AI platform running at ~15 FPS with minimal CPU load. 

For production applications, further performance gains (closer to the 30 FPS hardware limit) could be achieved by rewriting the pipeline in C++ or using multi-threaded Python architectures to decouple frame capture, inference, and display.

## 7. Appendices

### 7.1 Setup Script (Reference)
The following script was used to provision the environment:

```bash
#!/bin/bash
# setup_ubuntu.sh
set -e
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-venv python3-pip ffmpeg wget git libopencv-dev
# Manual install of matching deb versions required
sudo dpkg -i hailort_4.23.0_arm64.deb hailort-pcie-driver_4.23.0_all.deb
sudo apt-get install -f -y
python3 -m venv ~/hailo_env
source ~/hailo_env/bin/activate
pip install numpy opencv-python onnxruntime flask
pip install hailort-4.23.0-cp312-cp312-linux_aarch64.whl
# Enable 4k pages
echo "kernel=kernel8.img" | sudo tee -a /boot/firmware/config.txt
```

### 7.2 Reproduction Steps
1.  Install Ubuntu 24.04 on Raspberry Pi 5.
2.  Install HailoRT 4.23.0 & Driver 4.23.0.
3.  Install Python dependencies and Hailo wheel.
4.  Run `hailo_inference_web.py` (provided in project artifacts).
