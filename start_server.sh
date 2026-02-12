#!/bin/bash
# Start camera server (ensures only one instance)

# Kill any existing instances
pkill -f "python.*rpi_camera_stream"
sleep 1

# Start fresh
source .venv/bin/activate
python -m rpi_camera_stream --port 5000
