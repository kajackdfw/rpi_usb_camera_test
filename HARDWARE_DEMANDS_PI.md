# Hardware Demands on Raspberry Pi

This document describes the threading model, CPU usage, and multi-client performance characteristics of the camera streaming server on Raspberry Pi hardware.

## Threading Model

### Base Threads (Always Running)

- **1 thread** - Camera capture loop (opencv_capture.py:57)
  - Continuously reads frames from the camera via OpenCV
  - Stores frames in shared FrameBuffer for all consumers

### Per-Client Threads (H.264 Streaming)

For each connected H.264 Socket.IO client:
- **2 threads** (h264.py:64-67):
  - Input thread: Feeds frames to FFmpeg stdin
  - Output thread: Reads H.264 NAL units from FFmpeg stdout
- **1 FFmpeg subprocess** (not a Python thread, but uses CPU cores)

### Optional Threads

- **1 thread** - Local preview window (if `--preview` flag is used, local_display.py:34)

### Flask-SocketIO

- Uses `eventlet` async mode (app.py:167)
- Implements **greenthreads** (cooperative multitasking, not OS threads)
- Very lightweight for handling Socket.IO connections

## CPU Core Usage

The application **does not explicitly limit CPU usage or set core affinity**. It will use as many CPU cores as the OS scheduler allows.

### Available Cores by Raspberry Pi Model

- **Pi 4**: 4 cores (ARM Cortex-A72)
- **Pi 5**: 4 cores (ARM Cortex-A76)
- **Pi 3**: 4 cores (ARM Cortex-A53)

### FFmpeg Encoding

FFmpeg can utilize multiple cores for encoding:
- **Software encoding** (`libx264`): Multi-threaded, CPU-intensive
- **Hardware encoding** (`h264_v4l2m2m`): Offloads work to video encoder hardware, significantly reduces CPU load

## Multi-Client Performance

### H.264 Streaming (Socket.IO)

Each client gets a **dedicated FFmpeg encoder process**:

- **1 client**: No problem, smooth performance
- **2 clients**: Should work, but runs two separate FFmpeg + encoding pipelines
- **3+ clients**: Gets heavy, especially with software encoding

**Performance factors:**
- **Hardware encoding** (`h264_v4l2m2m` on Pi 4/5): Much better multi-client support due to GPU offload
- **Software encoding** (`libx264`): CPU-intensive, 2 clients may struggle on Pi 3

### MJPEG Streaming (HTTP)

**Much lighter weight** - designed for multiple viewers:
- All clients share the same camera feed
- JPEG encoding happens once per frame for the multipart stream
- Can easily support **5+ clients** simultaneously
- This is why the local network view (app.py:144) defaults to MJPEG

## Key Architecture Detail

The camera captures frames **once** and stores them in a shared `FrameBuffer`. All consumers read from this buffer:
- H.264 encoders (one per Socket.IO client)
- MJPEG HTTP route (shared by all MJPEG viewers)
- Local preview window (if enabled)

**Camera overhead is constant** regardless of client count. Only the encoding/streaming overhead multiplies with additional H.264 clients.

## Example Thread Count

With 2 connected H.264 clients streaming:
- 1 camera capture thread
- 4 threads (2 per H.264 client for encoding I/O)
- 2 FFmpeg subprocesses
- Eventlet greenthreads (lightweight)

**Total: ~5-7 OS threads + eventlet greenthreads**

## Recommendations

### For Multiple Viewers

- **Local network (LAN)**: Use MJPEG (`/video_feed`)
  - Lightweight, efficient for multiple viewers
  - Lower CPU overhead
  - Good for monitoring dashboards or multiple browser tabs

- **Remote/Internet**: Use H.264 Socket.IO
  - Better compression for limited bandwidth
  - Heavier per-client on the Pi
  - Limit concurrent streams to 1-2 clients

### Hardware Encoding

Enable hardware encoding for better multi-client support:
- Edit `config.py` or pass `--use-hardware` flag
- Significantly reduces CPU load per H.264 stream
- **Pi 4/5**: Should handle 2-3 simultaneous H.264 clients
- **Pi 3**: Stick to 1 H.264 client or use MJPEG for additional viewers

### Performance Tuning

If experiencing performance issues:
1. Lower resolution/FPS via `--width`, `--height`, `--fps` flags
2. Use `low` quality preset for H.264 streams
3. Disable preview window (`--preview` flag) in production
4. Use MJPEG for additional viewers instead of H.264
