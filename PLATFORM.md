# Platform-Specific Requirements

This document describes platform-specific requirements and dependencies for the Raspberry Pi USB Camera Streaming Server.

## Overview

The application is designed to work on both **x86 Linux** and **Raspberry Pi (ARM)** platforms, but has some platform-specific requirements for camera access and debugging.

---

## Camera Device Access

### All Platforms (Linux)

**Required:** User must be in the `video` group to access camera devices.

```bash
# Check if you're in the video group
groups

# Add yourself to the video group (if not already)
sudo usermod -aG video $USER

# Log out and log back in for group changes to take effect
```

**Camera device paths:**
- Primary camera: `/dev/video0`
- Additional cameras: `/dev/video1`, `/dev/video2`, etc.

---

## v4l-utils Package

### Purpose
The `v4l-utils` package provides tools for inspecting and configuring Video4Linux (V4L2) devices, including:
- `v4l2-ctl` - Command-line tool to query and configure camera capabilities
- `v4l2-compliance` - Test tool for V4L2 driver compliance

### When It's Needed

#### **Raspberry Pi (ARM)**
**Required for production use:** No
**Recommended for debugging:** Yes

The application uses OpenCV's V4L2 backend to access cameras directly - `v4l-utils` is **not required** for the server to run. However, it's **highly recommended** for:
- Diagnosing camera detection issues
- Listing available cameras and their capabilities
- Configuring camera parameters
- Troubleshooting video device problems

#### **x86 Linux (Desktop/Laptop)**
**Required for production use:** No
**Recommended for debugging:** Yes

Same as Raspberry Pi - useful for debugging but not required for operation.

### Installation

```bash
# Debian/Ubuntu/Raspberry Pi OS
sudo apt-get update
sudo apt-get install -y v4l-utils

# Check installation
v4l2-ctl --version
```

### Useful v4l2-ctl Commands

```bash
# List all video devices
v4l2-ctl --list-devices

# Show detailed info about /dev/video0
v4l2-ctl -d /dev/video0 --all

# List supported formats for /dev/video0
v4l2-ctl -d /dev/video0 --list-formats-ext

# Check if device supports MJPEG
v4l2-ctl -d /dev/video0 --list-formats | grep MJPG
```

---

## Python Dependencies

### opencv-python-headless

**All platforms:** The `pyproject.toml` specifies `opencv-python-headless>=4.8` which:
- Works on both x86 and ARM architectures
- Includes V4L2 support on Linux
- Does not include GUI/display functionality (headless)
- Lighter weight than full `opencv-python`

**Note:** If you need the preview window feature (`--preview` flag), you may need to install `opencv-python` instead, but this adds X11/GUI dependencies.

---

## Platform-Specific Notes

### Raspberry Pi

**Recommended camera:**
- Arducam 5MP USB Camera
- Device path: `/dev/video0`
- Supported formats: MJPG 1920x1080@30fps, 1280x720@30fps, 2592x1944@15fps

**Performance tips:**
- Use MJPG format (hardware accelerated on many USB cameras)
- Lower resolution = lower CPU usage
- 1280x720@30fps is a good balance

**Common issues:**
- **Insufficient power:** Some USB cameras need powered USB hub
- **USB 2.0 vs 3.0:** USB 3.0 provides more bandwidth for higher resolutions
- **Multiple cameras:** May require powered hub to avoid power issues

### x86 Linux

**Supported cameras:**
- Built-in laptop webcams
- USB webcams
- USB capture devices

**Common issues:**
- **Driver support:** Some cameras require proprietary drivers
- **Virtual cameras:** OBS Virtual Camera, v4l2loopback work but may have quirks
- **Multiple cameras:** Usually works well if properly detected

---

## Testing Camera Access

Before running the server, verify your camera is accessible:

```bash
# Check if device exists
ls -la /dev/video0

# Check permissions (should see 'video' group)
ls -l /dev/video0
# Expected: crw-rw----+ 1 root video ...

# Test with v4l2-ctl (if installed)
v4l2-ctl -d /dev/video0 --list-formats-ext

# Test with OpenCV (Python)
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('Camera opened:', cap.isOpened()); cap.release()"
```

---

## Runtime Dependencies Summary

| Dependency | Raspberry Pi | x86 Linux | Purpose |
|------------|--------------|-----------|---------|
| Python 3.9+ | Required | Required | Runtime |
| opencv-python-headless | Required | Required | Camera capture |
| Flask + Flask-SocketIO | Required | Required | Web server |
| User in `video` group | Required | Required | Camera access |
| v4l-utils | Optional | Optional | Debugging only |
| ffmpeg | Optional* | Optional* | H.264 encoding for Socket.IO streams |

*ffmpeg is required only if using H.264 streaming via Socket.IO. MJPEG streaming works without it.

---

## Troubleshooting

### "Camera not available" error

1. **Check device exists:**
   ```bash
   ls -la /dev/video0
   ```

2. **Check permissions:**
   ```bash
   groups  # Should include 'video'
   ```

3. **Check if device is in use:**
   ```bash
   sudo lsof /dev/video0
   ```

4. **Test camera directly:**
   ```bash
   v4l2-ctl -d /dev/video0 --list-formats-ext
   ```

5. **Check server logs:**
   ```bash
   python -m rpi_camera_stream --port 5000
   # Look for "Failed to open camera" or "Camera not available" messages
   ```

### Server starts but no video feed

- Camera may have started but not producing frames
- Check `/api/status` endpoint for camera status
- Verify camera format is supported (MJPG recommended)
- Try different resolution/fps settings

---

## Installation Quick Reference

```bash
# Install v4l-utils for debugging (optional)
sudo apt-get install -y v4l-utils

# Ensure user in video group (required)
sudo usermod -aG video $USER
# Log out and log back in

# Install Python dependencies (required)
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Test camera
v4l2-ctl --list-devices

# Run server
python -m rpi_camera_stream --port 5000
```
