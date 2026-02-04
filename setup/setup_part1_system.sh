#!/bin/bash
set -e

echo "=== Hailo Setup Part 1: System Configuration ==="

# 1. Update and Upgrade System
echo "[1/3] Updating system packages..."
sudo apt update
sudo apt upgrade -y

# 2. Install Basic Dependencies
echo "[2/3] Installing base dependencies..."
sudo apt install -y git wget ffmpeg

# 3. Configure PCIe
echo "[3/3] Enabling PCIe in boot config..."
CONFIG_FILE="/boot/firmware/config.txt"
if ! grep -q "dtparam=pciex1" "$CONFIG_FILE"; then
    echo "dtparam=pciex1" | sudo tee -a "$CONFIG_FILE"
    echo "PCIe enabled."
else
    echo "PCIe already enabled."
fi

echo "------------------------------------------------"
echo "Part 1 Complete. A SYSTEM REBOOT IS REQUIRED."
echo "After rebooting, run: ./setup/setup_part2_hailo.sh"
echo "------------------------------------------------"
echo "Rebooting in 5 seconds..."
sleep 5
sudo reboot
