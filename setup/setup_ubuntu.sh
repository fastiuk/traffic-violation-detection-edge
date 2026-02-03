#!/bin/bash
set -e

echo "Starting Hailo Setup on Ubuntu 24.04..."

# 1. Update system
echo "Updating system..."
sudo apt update && sudo apt upgrade -y

# 2. Install dependencies
echo "Installing dependencies..."
sudo apt install -y python3-venv python3-pip ffmpeg wget git libopencv-dev

# 3. Install Hailo Runtime & Driver
echo "Installing Hailo debs..."

# Check if files exist
HAILORT_DEB="setup/installers/hailort_4.23.0_arm64.deb"
DRIVER_DEB="setup/installers/hailort-pcie-driver_4.23.0_all.deb"
PYTHON_WHL="setup/installers/hailort-4.23.0-cp312-cp312-linux_aarch64.whl"

if [ ! -f "$HAILORT_DEB" ] || [ ! -f "$DRIVER_DEB" ] || [ ! -f "$PYTHON_WHL" ]; then
    echo "ERROR: Hailo installer files not found!"
    echo "Please download the following files from the Hailo Developer Zone and place them in 'setup/installers/':"
    echo "  - hailort_4.23.0_arm64.deb"
    echo "  - hailort-pcie-driver_4.23.0_all.deb"
    echo "  - hailort-4.23.0-cp312-cp312-linux_aarch64.whl"
    exit 1
fi

# Force install if dependencies missing, then fix
sudo dpkg -i "$HAILORT_DEB" "$DRIVER_DEB" || sudo apt-get install -f -y

# 4. Create Virtual Environment
echo "Creating venv..."
python3 -m venv ~/hailo_env
source ~/hailo_env/bin/activate

# 5. Install Python Wheels
echo "Installing Python packages..."
pip install --upgrade pip
# Install the provided Hailo wheel
pip install "$PYTHON_WHL"

# Install other requirements
pip install numpy opencv-python onnxruntime flask

# 6. Download Models
echo "Downloading models..."
mkdir -p ~/hailo_models
# YOLOv5s ONNX (CPU)
if [ ! -f ~/hailo_models/yolov5s.onnx ]; then
    wget -O ~/hailo_models/yolov5s.onnx https://github.com/ultralytics/yolov5/releases/download/v6.0/yolov5s.onnx
fi
# YOLOv5s HEF (Hailo-8L)
if [ ! -f ~/hailo_models/yolov5s_h8l.hef ]; then
    wget -O ~/hailo_models/yolov5s_h8l.hef https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.14.0/hailo8l/yolov5s.hef
fi

echo "Setup Complete! Reboot might be required for the PCIe driver."
echo "Please reboot: sudo reboot"