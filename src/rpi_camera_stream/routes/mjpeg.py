"""MJPEG streaming routes."""

import logging
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
    while True:
        frame = frame_buffer.get(timeout=1.0)
        if frame is None:
            continue

        jpeg_data = encode_jpeg(frame)
        if jpeg_data is None:
            continue

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
    """Render the camera streams page."""
    return render_template("streams.html")


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
