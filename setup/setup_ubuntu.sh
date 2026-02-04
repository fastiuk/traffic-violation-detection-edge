#!/bin/bash
set -e

echo "Starting Hailo Setup on Ubuntu 24.04..."

# 1. Update system
echo "Updating system..."
sudo apt update
# Install headers FIRST to fix any broken driver states from previous runs during upgrade
sudo apt install -y linux-headers-raspi
sudo apt upgrade -y

# 2. Install dependencies
echo "Installing dependencies..."
sudo apt install -y python3-venv python3-pip ffmpeg wget git

# 3. Install Hailo Runtime & Driver
echo "Installing Hailo debs..."

HAILORT_DEB="setup/installers/hailort_4.23.0_arm64.deb"
DRIVER_DEB="setup/installers/hailort-pcie-driver_4.23.0_all.deb"
PYTHON_WHL="setup/installers/hailort-4.23.0-cp312-cp312-linux_aarch64.whl"

if [ ! -f "$HAILORT_DEB" ] || [ ! -f "$DRIVER_DEB" ] || [ ! -f "$PYTHON_WHL" ]; then
    echo "ERROR: Hailo installer files not found in setup/installers/"
    exit 1
fi

# Force purge of broken driver if it exists to ensure a clean install
sudo dpkg --purge hailort-pcie-driver || true

# Install debs. Pipe "Y" to handle the interactive DKMS prompt
printf "Y\n" | sudo dpkg -i "$HAILORT_DEB" "$DRIVER_DEB" || sudo apt-get install -f -y

# 4. Create Virtual Environment in a shared location
VENV_PATH="/opt/hailo_env"
echo "Creating venv at $VENV_PATH..."
sudo python3 -m venv "$VENV_PATH"
sudo chown -R $USER:$USER "$VENV_PATH"
source "$VENV_PATH/bin/activate"

# 5. Install Python Wheels
echo "Installing Python packages..."
pip install --upgrade pip
pip install "$PYTHON_WHL"
pip install "numpy==1.26.4" "opencv-python==4.11.0.86" flask onnxruntime

# 6. Download Models to a shared location
MODELS_PATH="/opt/hailo_models"
echo "Downloading models to $MODELS_PATH..."
sudo mkdir -p "$MODELS_PATH"
sudo chown -R $USER:$USER "$MODELS_PATH"

# YOLOv5s ONNX (CPU)
if [ ! -f "$MODELS_PATH/yolov5s.onnx" ]; then
    wget -O "$MODELS_PATH/yolov5s.onnx" https://github.com/ultralytics/yolov5/releases/download/v6.0/yolov5s.onnx
fi
# YOLOv5s HEF (Hailo-8L)
if [ ! -f "$MODELS_PATH/yolov5s_h8l.hef" ]; then
    wget -O "$MODELS_PATH/yolov5s_h8l.hef" https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.14.0/hailo8l/yolov5s.hef
fi

# 7. Configure System (PCIe)
echo "Configuring System..."
# Enable PCIe Gen 2/3 (required for HAT+)
if ! grep -q "dtparam=pciex1" /boot/firmware/config.txt; then
    echo "dtparam=pciex1" | sudo tee -a /boot/firmware/config.txt
fi

echo "Setup Complete! Reboot is required."
echo "Please reboot: sudo reboot"