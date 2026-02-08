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
