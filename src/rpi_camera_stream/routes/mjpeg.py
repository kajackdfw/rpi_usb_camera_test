"""MJPEG streaming routes."""

import logging
import time
from typing import Generator

from flask import Blueprint, Response, current_app, jsonify, redirect, render_template, url_for

from ..camera import FrameBuffer
from ..encoders import encode_jpeg

logger = logging.getLogger(__name__)

mjpeg_bp = Blueprint("mjpeg", __name__, url_prefix="/lan")


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
    from pathlib import Path

    # Get camera slot configuration from settings
    settings = current_app.config.get("settings")
    camera_configs = settings.get("cameras", [
        {"slot": 1, "device": "", "type": "N", "enabled": False},
        {"slot": 2, "device": "", "type": "N", "enabled": False},
        {"slot": 3, "device": "", "type": "N", "enabled": False},
    ])

    camera_slots = []

    # Map camera type to readable name
    type_names = {
        "W": "Wide Angle",
        "N": "Normal",
        "IR": "Infrared",
        "T": "Telephoto"
    }

    # Check for snapshots directory - use consistent path calculation
    # current_app.root_path is src/rpi_camera_stream, go up 2 levels to project root
    app_root = Path(current_app.root_path).parent.parent
    snapshots_dir = app_root / "snapshots"

    for config in camera_configs:
        # Skip unconfigured slots
        if not config["enabled"]:
            continue

        slot_id = config["slot"] - 1  # Convert to 0-indexed
        device_path = config["device"]
        camera_type = config["type"]
        enabled = config["enabled"]

        # Query device information
        device_info = get_camera_info(device_path)
        display_name = get_display_name(device_info)

        # Check if snapshot exists for this slot
        snapshot_path = snapshots_dir / f"slot{config['slot']}_last.jpg"
        has_snapshot = snapshot_path.exists()

        camera_slots.append({
            "id": slot_id,
            "slot": config["slot"],
            "name": display_name,
            "device": device_path or f"Camera {config['slot']}",
            "type": camera_type,
            "type_name": type_names.get(camera_type, "Normal"),
            "exists": device_info.exists,
            "model_id": device_info.model_id,
            "vendor_id": device_info.vendor_id,
            "enabled": enabled,
            "has_snapshot": has_snapshot,
        })

    # If no cameras are configured, redirect to settings page
    if not camera_slots:
        return redirect(url_for('settings.index'))

    # Get the active camera slot from settings
    active_slot = settings.get("active_camera_slot")

    # Mark the active camera slot
    for cam in camera_slots:
        cam["active"] = (cam["slot"] == active_slot) if active_slot else False

    return render_template("streams_pico.html", cameras=camera_slots, rover_name=settings.get("rover_name", "Cattern Rover"))


@mjpeg_bp.route("/stream/<int:slot>")
def stream(slot):
    """Render individual camera live stream page."""
    settings = current_app.config.get("settings")
    cameras = settings.get("cameras", [])

    # Validate slot number
    if slot < 1 or slot > len(cameras):
        return jsonify({"error": f"Invalid camera slot {slot}"}), 404

    camera_config = cameras[slot - 1]

    # Check if slot is configured
    if not camera_config.get("enabled") or not camera_config.get("device"):
        return jsonify({"error": f"Camera slot {slot} not configured"}), 404

    # Check if this is the active camera
    active_slot = settings.get("active_camera_slot")
    if slot != active_slot:
        return jsonify({"error": f"Camera {slot} is not active. Active camera: {active_slot}"}), 400

    return render_template("streams_simple.html", camera_id=slot, camera_type=camera_config["type"])


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


@mjpeg_bp.route("/api/snapshot/<int:slot>")
def snapshot_by_slot(slot):
    """Get the saved snapshot for a specific camera slot."""
    from pathlib import Path

    # current_app.root_path is src/rpi_camera_stream, go up 2 levels to project root
    app_root = Path(current_app.root_path).parent.parent
    snapshot_path = app_root / "snapshots" / f"slot{slot}_last.jpg"

    if not snapshot_path.exists():
        return jsonify({"error": f"No snapshot found for slot {slot}"}), 404

    try:
        with open(snapshot_path, "rb") as f:
            jpeg_data = f.read()
        return Response(jpeg_data, mimetype="image/jpeg")
    except Exception as e:
        logger.error(f"Failed to read snapshot for slot {slot}: {e}")
        return jsonify({"error": "Failed to read snapshot"}), 500


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
