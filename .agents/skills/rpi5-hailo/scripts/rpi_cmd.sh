#!/bin/bash
# Helper script to run commands on the RPi5
RPI_IP="10.10.10.21"
RPI_USER="pi"

COMMAND=$1

if [ -z "$COMMAND" ]; then
    echo "Usage: $0 <command>"
    exit 1
fi

ssh -o StrictHostKeyChecking=no "${RPI_USER}@${RPI_IP}" "$COMMAND"
