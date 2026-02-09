# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Raspberry Pi USB camera streaming server using Flask + Flask-SocketIO. Streams video from an Arducam 5MP USB camera via:
- **H.264 stream** via Socket.IO (for React clients using jMuxer)
- **MJPEG stream** via HTTP (for simple browser viewing)
- **Local preview** via OpenCV window (optional)

- **Language:** Python 3.11
- **Target Platform:** Raspberry Pi (ARM)
- **License:** GPLv3

## Build & Development Commands

```bash
# Create and activate virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# x86 Linux only: Install v4l-utils for camera debugging (not required on Raspberry Pi)
sudo apt-get update && sudo apt-get install -y v4l-utils

# Run the server
python -m rpi_camera_stream --port 5000

# Run with local preview window
python -m rpi_camera_stream --preview

# Run with custom camera settings
python -m rpi_camera_stream --device /dev/video0 --width 1920 --height 1080 --fps 30
```

## Troubleshooting

### Virtual Environment Issues After Moving Project

If you move the project folder to a new location, the virtual environment will break because it contains hardcoded paths. To fix this:

```bash
# Deactivate the current virtual environment
deactivate

# Remove the broken virtual environment
rm -rf .venv

# Recreate the virtual environment
python3.11 -m venv .venv

# Activate it
source .venv/bin/activate

# Reinstall dependencies
pip install -e ".[dev]"
```

**Why this happens:** Virtual environments store absolute paths to the Python interpreter and installed packages. When you move the folder, these paths become invalid. Always recreate the venv rather than trying to fix the paths.

## Architecture

```
src/rpi_camera_stream/
├── __main__.py           # CLI entry point
├── app.py                # Flask app factory
├── config.py             # Configuration dataclasses
├── camera/
│   ├── opencv_capture.py # V4L2 camera capture thread
│   └── frame_buffer.py   # Thread-safe frame sharing
├── encoders/
│   ├── mjpeg.py          # JPEG encoding
│   └── h264.py           # FFmpeg H.264 encoding subprocess
├── routes/
│   └── mjpeg.py          # Flask routes (/video_feed, /api/snapshot, /api/status)
├── socketio_handlers/
│   └── video.py          # Socket.IO /video namespace
├── preview/
│   └── local_display.py  # OpenCV window preview
└── templates/
    └── index.html        # MJPEG viewer page
```

### Key Components

- **OpenCVCamera**: Captures frames using OpenCV with V4L2 backend, stores in FrameBuffer
- **FrameBuffer**: Thread-safe frame sharing between capture and consumers
- **H264Encoder**: FFmpeg subprocess encoding BGR frames to H.264 NAL units
- **VideoNamespace**: Socket.IO handler for H.264 streaming to React clients

### Socket.IO Events (namespace: /video)

| Event | Direction | Payload |
|-------|-----------|---------|
| `start_stream` | client→server | `{quality: "low"|"medium"|"high"}` |
| `stop_stream` | client→server | `{}` |
| `h264_data` | server→client | binary H.264 NAL units |
| `stream_started` | server→client | `{width, height, fps}` |

### HTTP Routes

| Route | Description |
|-------|-------------|
| `/` | MJPEG viewer page |
| `/video_feed` | MJPEG stream (multipart/x-mixed-replace) |
| `/api/snapshot` | Single JPEG frame |
| `/api/status` | Camera status JSON |

## Camera Configuration

The Arducam 5MP USB camera supports:
- MJPG 1920x1080 @ 30fps (recommended for streaming)
- MJPG 1280x720 @ 30fps
- MJPG 2592x1944 @ 15fps (full 5MP)
- YUYV 640x480 @ 30fps (raw)

Device path: `/dev/video0`

## SCSS/CSS Development

### SCSS Compilation

SCSS source files in `scss/` are compiled to CSS using the **Live Sass Compiler** VS Code extension by Glenn Marks.

**Setup:**
1. Install the extension: `Ctrl+P` → `ext install glenn2223.live-sass`
2. Open any `.scss` file
3. Click "Watch Sass" in the VS Code status bar

**Output:** Compiled CSS files go to `src/rpi_camera_stream/static/css/`
- `.css` - Expanded format (for debugging)
- `.min.css` - Minified format (for production)

See `scss/README.md` for detailed usage and customization options.

## Vendor Packages

Third-party libraries included directly in the project are located in `vendor_packages/`.

### Pico CSS v2

A minimal CSS framework for semantic HTML, available as an alternative to Tailwind CSS.

- **Location:** `vendor_packages/pico-main/`
- **Documentation:** See `vendor_packages/README.md`
- **Use case:** Pages requiring class-less, semantic styling
- **License:** MIT

**Note:** Zip files in `vendor_packages/` are gitignored. Only extracted contents are tracked.
