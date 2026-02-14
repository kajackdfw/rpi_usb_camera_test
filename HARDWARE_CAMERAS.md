# Camera Hardware Specifications

This document records the hardware specifications and supported resolutions for USB cameras used with this streaming server.

## Detecting Camera Capabilities

To detect the capabilities of your connected camera, use `v4l2-ctl`:

```bash
# List available video devices
v4l2-ctl --list-devices

# Query supported formats and resolutions for /dev/video0
v4l2-ctl --device=/dev/video0 --list-formats-ext

# Get current camera settings
v4l2-ctl --device=/dev/video0 --all
```

On x86 Linux, install v4l-utils:
```bash
sudo apt-get update && sudo apt-get install -y v4l-utils
```

On Raspberry Pi, v4l-utils is typically pre-installed.

---

## Current Detected Camera

**Device:** `/dev/video0`
**Model:** *To be filled when running on Raspberry Pi*
**Detected on:** *Date to be added*

### Supported Resolutions

*Run `v4l2-ctl --device=/dev/video0 --list-formats-ext` and paste output here*

| Format | Resolution | Max FPS | Notes |
|--------|------------|---------|-------|
| MJPG | 1920x1080 | 30 | Example - replace with actual |
| MJPG | 1280x720 | 30 | Example - replace with actual |
| YUYV | 640x480 | 30 | Example - replace with actual |

---

## Known Camera Specifications

### Arducam 5MP USB Camera (B0196) on HP Envy 360 Ryzen 7 Laptop

**Device Path:** `/dev/video0` (default)
**Sensor:** OV5647 5MP
**Interface:** USB 2.0
**Documentation:** [Arducam 5MP USB Camera](https://www.arducam.com/product/arducam-5mp-usb-camera/)

#### Supported Modes

| Format | Resolution | Max FPS | Bitrate (approx) | Use Case |
|--------|------------|---------|------------------|----------|
| MJPG | 1920x1080 | 30 | ~15-20 Mbps | **Recommended** - High quality streaming |
| MJPG | 1280x720 | 30 | ~8-12 Mbps | Balanced quality and performance |
| MJPG | 2592x1944 | 15 | ~20-25 Mbps | Full 5MP stills/slow video |
| YUYV | 640x480 | 30 | ~150 Mbps | Raw uncompressed (not recommended) |

#### Recommended Settings

- **Streaming:** MJPG 1280x720 @ 30fps (default in config.py)
- **High quality:** MJPG 1920x1080 @ 30fps
- **Low bandwidth:** MJPG 640x480 @ 15fps (via H.264 quality presets)

#### Hardware Notes

- **Auto exposure:** Supported
- **Auto white balance:** Supported
- **Hardware H.264 encoding:** Not built-in (relies on Pi hardware encoder)
- **Focus:** Fixed focus (not adjustable)

---

## Application Quality Presets

The server provides three H.264 encoding presets that downsample/throttle the camera feed:

| Preset | Resolution | FPS | Bitrate | Camera Mode Used |
|--------|-----------|-----|---------|------------------|
| `low` | 640x480 | 15 | 500k | Downscaled from 1280x720 MJPG |
| `medium` | 1280x720 | 30 | 1M | Direct from 1280x720 MJPG |
| `high` | 1920x1080 | 30 | 2M | Direct from 1920x1080 MJPG |

**Note:** Presets are set in `src/rpi_camera_stream/config.py:38-42`

### How Presets Work

1. Camera captures at native resolution (default: 1280x720 MJPG)
2. FFmpeg encoder downscales/encodes to preset resolution
3. Clients select preset via Socket.IO `start_stream` event

**Default preset:** `medium` (hardcoded fallback in socketio_handlers/video.py:45)

---

## Adding New Cameras

When testing a new camera:

1. Connect camera and identify device path:
   ```bash
   v4l2-ctl --list-devices
   ```

2. Query supported formats:
   ```bash
   v4l2-ctl --device=/dev/videoX --list-formats-ext
   ```

3. Update "Current Detected Camera" section above with output

4. Test streaming with recommended mode:
   ```bash
   python -m rpi_camera_stream --device /dev/videoX --width 1280 --height 720 --fps 30
   ```

5. Document results in this file for future reference
