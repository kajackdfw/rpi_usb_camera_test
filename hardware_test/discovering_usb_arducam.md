# Discovering USB Arducam on Raspberry Pi 4

## USB Device Detection

Use `lsusb` to list connected USB devices:

```bash
lsusb
```

The Arducam 5MP USB Camera appears as:
```
Bus 001 Device 007: ID 1bcf:284c Sunplus Innovation Technology Inc. Arducam 5MP USB Camera
```

## Video Device Nodes

The camera creates two video device nodes:
- `/dev/video0`
- `/dev/video1`

List video devices with:
```bash
ls -la /dev/video*
```

## V4L2 Device Listing

Use `v4l2-ctl` to identify which video devices belong to which hardware:

```bash
v4l2-ctl --list-devices
```

Output for the Arducam:
```
Arducam 5MP USB Camera: Arducam (usb-0000:01:00.0-1.3):
    /dev/video0
    /dev/video1
    /dev/media4
```

Note: The other video devices (`/dev/video10`-`/dev/video31`) are Pi 4 built-in components:
- `bcm2835-codec` - Hardware video encoder/decoder
- `bcm2835-isp` - Image Signal Processor
- `rpivid` - Video decoder

## Camera Capabilities

Query full camera details:
```bash
v4l2-ctl -d /dev/video0 --all
```

List supported formats:
```bash
v4l2-ctl -d /dev/video0 --list-formats-ext
```

## Test Capture

Single frame capture with v4l2-ctl:
```bash
v4l2-ctl -d /dev/video0 --stream-mmap --stream-count=1 --stream-to=test.jpg
```

Single frame capture with ffmpeg:
```bash
ffmpeg -f v4l2 -i /dev/video0 -frames:v 1 test.jpg
```
