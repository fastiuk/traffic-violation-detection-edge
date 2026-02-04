# Traffic Violation Detection on Edge Devices

**Repository:** `traffic-violation-detection-edge`  
**Platform:** Raspberry Pi 5 + Hailo-8L AI Accelerator  
**Author:** Yevhen Fastiuk  
**Context:** PhD Thesis Research

## Overview

This repository hosts the source code, benchmarks, and experimental data for a PhD research project focused on **Real-time Traffic Rule Enforcement using Edge Computing**.

The project investigates the feasibility and efficiency of deploying advanced computer vision models (such as YOLOv5) on low-power, cost-effective edge hardware (Raspberry Pi 5) augmented with dedicated AI acceleration (Hailo-8L). The primary goal is to detect traffic violations—such as illegal parking, wrong-way driving, and red-light crossing—locally at the edge, reducing latency and bandwidth requirements compared to cloud-centric solutions.

## Getting Started

### 1. Hardware & OS Requirements
*   **Device:** Raspberry Pi 5 (8GB recommended)
*   **Accelerator:** Hailo-8L M.2 module + Raspberry Pi M.2 HAT+
*   **OS:** **Ubuntu 24.04 LTS (Noble Numbat)** 64-bit for Raspberry Pi.
    *   *Note:* Raspberry Pi OS is not fully supported by this automated setup due to ABI versioning conflicts.

### 2. Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/fastiuk/traffic-violation-detection-edge.git
    cd traffic-violation-detection-edge
    ```

2.  **Download Required Binaries:**
    Due to licensing, Hailo binaries cannot be hosted here. Download the following from the [Hailo Developer Zone](https://hailo.ai/developer-zone/) and place them in `setup/installers/`:
    *   `hailort_4.23.0_arm64.deb`  
        **MD5:** `212575df93456a40befd9238ac92b4e1`
    *   `hailort-pcie-driver_4.23.0_all.deb`  
        **MD5:** `a734d7c865e5489f855ddd01bcbfc7e6`
    *   `hailort-4.23.0-cp312-cp312-linux_aarch64.whl`  
        **MD5:** `a66552e308c1123616cbdb4fd69e5485`

3.  **Run the Setup Script:**
    This script automates dependency installation, driver setup, and environment configuration (including pinning Numpy < 2.0).
    ```bash
    chmod +x setup/setup_ubuntu.sh
    ./setup/setup_ubuntu.sh
    ```

4.  **Reboot:**
    Restart the device to apply kernel configuration changes (PCIe enablement).
    ```bash
    sudo reboot
    ```

### 3. Running the Benchmark
After rebooting, execute the performance benchmark:

```bash
# Activate the environment
source /opt/hailo_env/bin/activate

# Run the benchmark (Web Streaming)
python3 performance-benchmark/src/hailo_inference_web.py
```
Access the stream at `http://<RPI_IP>:5001`.

## Repository Structure

*   **`performance-benchmark/`**  
    Contains the initial baseline study comparing the inference capabilities of the host CPU vs. the Hailo-8L accelerator.
    *   `src/`: Python scripts for benchmarking FPS (Frames Per Second) and latency. Includes web-streaming implementations for visualization.
    *   `docs/`: Detailed performance reports and methodology (e.g., `Hailo_vs_RPi5_CPU_Benchmark_Report.md`).

*   **`setup/`**  
    Infrastructure as Code (IaC) and setup scripts to provision the edge environment.
    *   `setup_ubuntu.sh`: Automates the installation of drivers, dependencies, and python environments on Ubuntu 24.04.
    *   `installers/`: Place downloaded proprietary binaries here.

*   **`results/`**  
    Experimental data, screenshots, and logs captured during testing.

## Key Findings (Preliminary)

Initial benchmarking with YOLOv5s (640x640) demonstrates the critical necessity of specialized hardware for this application:

| Hardware | Throughput (App) | Throughput (Raw HW) | Latency | System Load | Suitability |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RPi 5 CPU** | ~1.7 FPS | N/A | ~570ms | 100% | Unusable for real-time |
| **Hailo-8L** | **~15 FPS** | **29.34 FPS** | **~32ms** | <20% | **Real-time capable** |

*   **App Throughput:** Measured end-to-end in Python application (Frame Capture -> Preprocess -> Infer -> Stream).
*   **Raw HW Throughput:** Measured using `hailortcli` benchmark tool directly on the accelerator.

## Future Work

*   **Violation Logic:** Implementation of tracking algorithms (e.g., ByteTrack) and rule engines to define and detect specific traffic infractions.
*   **Dataset Collection:** Scripts for autonomous data gathering at traffic intersections.
*   **Model Optimization:** Fine-tuning YOLO models on domain-specific datasets (traffic surveillance).

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
