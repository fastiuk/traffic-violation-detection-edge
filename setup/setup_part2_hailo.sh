#!/bin/bash
set -e

echo "=== Hailo Setup Part 2: Driver & Software ==="

# 1. Install Kernel Headers
# Now safe to use $(uname -r) because we rebooted into the new kernel in Part 1
echo "[1/5] Installing kernel headers for $(uname -r)..."
sudo apt install -y "linux-headers-$(uname -r)" python3-venv python3-pip

# 2. Install Hailo Driver & Runtime
echo "[2/5] Installing Hailo drivers..."
INSTALLER_DIR="setup/installers"
HAILORT_DEB="$INSTALLER_DIR/hailort_4.23.0_arm64.deb"
DRIVER_DEB="$INSTALLER_DIR/hailort-pcie-driver_4.23.0_all.deb"
PYTHON_WHL="$INSTALLER_DIR/hailort-4.23.0-cp312-cp312-linux_aarch64.whl"

# Check files
if [ ! -f "$HAILORT_DEB" ] || [ ! -f "$DRIVER_DEB" ] || [ ! -f "$PYTHON_WHL" ]; then
    echo "ERROR: Installers not found in $INSTALLER_DIR/"
    echo "Please download them from Hailo Developer Zone."
    exit 1
fi

# Purge potential broken installs from before
sudo dpkg --purge hailort-pcie-driver 2>/dev/null || true

# Install with automatic "Yes" for DKMS prompt
printf "Y\n" | sudo dpkg -i "$HAILORT_DEB" "$DRIVER_DEB" || sudo apt-get install -f -y

# 3. Verify Hardware
echo "[3/5] Verifying Hailo device..."
if hailortcli scan | grep -q "0000"; then
    echo "SUCCESS: Hailo-8L device found."
else
    echo "WARNING: Hailo device NOT found. Check PCIe HAT connection."
    # We continue anyway to setup software, but warn user.
fi

# 4. Setup Python Environment (Shared /opt)
VENV_PATH="/opt/hailo_env"
echo "[4/5] Setting up Python venv at $VENV_PATH..."
if [ -d "$VENV_PATH" ]; then echo "Venv exists, skipping create."; else
    sudo python3 -m venv "$VENV_PATH"
    sudo chown -R $USER:$USER "$VENV_PATH"
fi

source "$VENV_PATH/bin/activate"
pip install --upgrade pip
pip install "$PYTHON_WHL"
# Pin versions for stability
pip install "numpy==1.26.4" "opencv-python==4.11.0.86" flask onnxruntime

# 5. Download Models (Shared /opt)
MODELS_PATH="/opt/hailo_models"
echo "[5/5] Downloading models to $MODELS_PATH..."
sudo mkdir -p "$MODELS_PATH"
sudo chown -R $USER:$USER "$MODELS_PATH"

if [ ! -f "$MODELS_PATH/yolov5s.onnx" ]; then
    wget -O "$MODELS_PATH/yolov5s.onnx" https://github.com/ultralytics/yolov5/releases/download/v6.0/yolov5s.onnx
fi
if [ ! -f "$MODELS_PATH/yolov5s_h8l.hef" ]; then
    wget -O "$MODELS_PATH/yolov5s_h8l.hef" https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.14.0/hailo8l/yolov5s.hef
fi

echo "------------------------------------------------"
echo "Setup Complete!"
echo "Run benchmark with:"
echo "source $VENV_PATH/bin/activate"
echo "python3 performance-benchmark/src/hailo_inference_web.py"
echo "------------------------------------------------"
