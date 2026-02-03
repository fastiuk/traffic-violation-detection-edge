#!/bin/bash

# Exit on any error
set -e

echo "Starting Raspberry Pi setup..."

# 1. Update and upgrade system packages
echo "Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install dependencies
echo "Installing dependencies..."
sudo apt-get install -y wget git python3-venv

# 3. Download and install Hailo runtime
echo "Downloading and installing Hailo runtime..."
wget -O hailort.deb 'https://d1rcmhofac3v9q.cloudfront.net/DevZone-Data/SW%20Downloads/HailoRT/2025-09-16/hailort_4.23.0_arm64.deb?Expires=1769899937&Signature=hrIX0k0KSCH7zS-jadH7Ll3kDd35Y3KdgvmfMDZzLnJsSDOh2QhsVHqZnrLXuwzK5no5hkAQabak1YpQaVEwqzqRNiXcU9HWvidC-eqJ5c4CSFGNvNTLmRiJgGvqVp92NB82ciOIxfzq4uAAOd0BM4r6DPTgYUCaDOU89us~VA6~-XrvLk1xkvicbI81SjrkQ1Osb6S6b68KIAmNuxgfz1xH7C2EcCTygf1lM1MGYWC-A2ructjcwVcFO2IlAImiepaRMJ5SjqtGviHPVSgOXq0aDJ5mrrDP6KfuX19VRSWfmqac214Z7b9Lmc0fw7Pi31LzBL~nC4FCnI7IyC41jQ__&Key-Pair-Id=K3T77PKOVL0N77'
sudo dpkg -i hailort.deb
sudo apt-get install -f -y

# 4. Clone the hailo-rpi5-examples repository
echo "Cloning hailo-rpi5-examples repository..."
rm -rf hailo-rpi5-examples
git clone https://github.com/hailo-ai/hailo-rpi5-examples.git

# 5. Run the installation script
echo "Running the installation script..."
cd hailo-rpi5-examples
./install.sh

# 6. Enable PCIe Gen 3.0
echo "Enabling PCIe Gen 3.0..."
echo "dtparam=pciex1" | sudo tee -a /boot/firmware/config.txt
echo "dtoverlay=vc4-kms-v3d-pi4" | sudo tee -a /boot/firmware/config.txt

echo "Setup complete. A reboot is required. The script will reboot the device now."