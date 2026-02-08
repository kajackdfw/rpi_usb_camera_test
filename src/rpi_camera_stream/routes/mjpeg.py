"""MJPEG streaming routes."""

import logging
import time
from typing import Generator

from flask import Blueprint, Response, current_app, jsonify, render_template

from ..camera import FrameBuffer
from ..encoders import encode_jpeg

logger = logging.getLogger(__name__)

mjpeg_bp = Blueprint("mjpeg", __name__)


def _get_frame_buffer() -> FrameBuffer:
    """Get the frame buffer from the app context."""
    return current_app.config["frame_buffer"]


def generate_mjpeg(frame_buffer: FrameBuffer) -> Generator[bytes, None, None]:
    """Generate MJPEG frames for streaming."""
    last_frame_time = time.time()
    target_interval = 1.0 / 30.0  # Target 30 FPS

    while True:
        # Get latest frame without blocking
        frame = frame_buffer.get_nowait()
        if frame is None:
            time.sleep(0.01)  # Brief sleep if no frame available
            continue

        jpeg_data = encode_jpeg(frame)
        if jpeg_data is None:
            continue

        # Throttle to ~30fps to prevent overwhelming the connection
        current_time = time.time()
        elapsed = current_time - last_frame_time
        if elapsed < target_interval:
            time.sleep(target_interval - elapsed)

        last_frame_time = time.time()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + jpeg_data + b"\r\n"
        )


@mjpeg_bp.route("/")
def index():
    """Render the home page."""
    return render_template("index.html")


@mjpeg_bp.route("/streams")
def streams():
    """Render the camera streams overview page with snapshots."""
    from ..utils import get_camera_info, get_display_name

    # Scan for available video devices (check up to video9)
    # This allows detection of cameras on any video device number
    import os

    available_devices = []
    for i in range(10):
        device = f"/dev/video{i}"
        if os.path.exists(device):
            available_devices.append(device)

    camera_slots = []
    seen_usb_paths = set()
    slot_id = 0

    # Process available devices and filter out duplicates
    for device_path in available_devices:
        # Stop after finding 3 unique cameras
        if slot_id >= 3:
            break

        # Query device information using udevadm
        device_info = get_camera_info(device_path)

        # Check if this is a duplicate device (same USB path as a previous camera)
        # USB path includes bus/port info, making it unique per physical USB connection
        if device_info.exists and device_info.usb_path:
            if device_info.usb_path in seen_usb_paths:
                # This is a duplicate/subdevice, skip it
                continue
            else:
                seen_usb_paths.add(device_info.usb_path)

        display_name = get_display_name(device_info)

        camera_slots.append({
            "id": slot_id,
            "name": display_name,
            "device": device_path,
            "exists": device_info.exists,
            "model_id": device_info.model_id,
            "vendor_id": device_info.vendor_id,
        })
        slot_id += 1

    # Fill remaining slots with "Not Found" entries
    while len(camera_slots) < 3:
        camera_slots.append({
            "id": slot_id,
            "name": "Not Found",
            "device": f"/dev/video{slot_id}",
            "exists": False,
            "model_id": None,
            "vendor_id": None,
        })
        slot_id += 1

    # Check which cameras are active
    # For now, only camera 0 is active (connected to the running capture)
    camera = current_app.config.get("camera")
    active_camera_id = 0 if (camera and camera.is_running) else None

    # Mark each camera as active or inactive
    for cam in camera_slots:
        cam["active"] = (cam["id"] == active_camera_id)

    return render_template("streams_overview.html", cameras=camera_slots)


@mjpeg_bp.route("/lan_stream/<int:camera_id>")
def lan_stream(camera_id):
    """Render individual camera live stream page."""
    if camera_id != 0:
        return jsonify({"error": f"Camera {camera_id} not available"}), 404

    return render_template("streams_simple.html", camera_id=camera_id)


@mjpeg_bp.route("/video_feed")
def video_feed():
    """MJPEG video stream endpoint."""
    camera = current_app.config.get("camera")
    if camera is None or not camera.is_running:
        return jsonify({"error": "Camera not available"}), 503

    frame_buffer = _get_frame_buffer()
    return Response(
        generate_mjpeg(frame_buffer),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@mjpeg_bp.route("/api/snapshot")
def snapshot():
    """Get a single JPEG snapshot."""
    frame_buffer = _get_frame_buffer()
    frame = frame_buffer.get_nowait()
    if frame is None:
        return jsonify({"error": "No frame available"}), 503

    jpeg_data = encode_jpeg(frame)
    if jpeg_data is None:
        return jsonify({"error": "Failed to encode frame"}), 500

    return Response(jpeg_data, mimetype="image/jpeg")


@mjpeg_bp.route("/api/status")
def status():
    """Get camera status."""
    camera = current_app.config.get("camera")
    if camera is None:
        return jsonify({"status": "not_initialized"})

    return jsonify({
        "status": "running" if camera.is_running else "stopped",
        "properties": camera.get_properties(),
        "frame_count": _get_frame_buffer().frame_count,
    })
