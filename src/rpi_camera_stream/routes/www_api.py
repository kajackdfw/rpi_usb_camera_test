"""WWW API routes for remote video control and snapshot capture."""

import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from flask import Blueprint, Response, current_app, jsonify, request

from ..config import QUALITY_PRESETS
from ..encoders.mjpeg import encode_jpeg

logger = logging.getLogger(__name__)

www_api_bp = Blueprint("www_api", __name__, url_prefix="/www/api")


def _validate_snapshot_params(quality: int, width: int, height: int) -> tuple[bool, str]:
    """Validate snapshot parameters.

    Args:
        quality: JPEG quality (1-100)
        width: Image width in pixels (160-3840)
        height: Image height in pixels (120-2160)

    Returns:
        Tuple of (is_valid, error_message). error_message is empty if valid.
    """
    if not isinstance(quality, int) or quality < 1 or quality > 100:
        return False, "Quality must be an integer between 1 and 100"

    if not isinstance(width, int) or width < 160 or width > 3840:
        return False, "Width must be an integer between 160 and 3840"

    if not isinstance(height, int) or height < 120 or height > 2160:
        return False, "Height must be an integer between 120 and 2160"

    return True, ""


def _capture_snapshot(quality: int, width: int, height: int) -> Optional[bytes]:
    """Capture a snapshot from the frame buffer.

    Args:
        quality: JPEG quality (1-100)
        width: Desired image width
        height: Desired image height

    Returns:
        JPEG encoded bytes, or None if capture failed.
    """
    frame_buffer = current_app.config["frame_buffer"]
    frame = frame_buffer.get_nowait()

    if frame is None:
        return None

    # Resize if requested dimensions differ from frame
    if width != frame.shape[1] or height != frame.shape[0]:
        frame = cv2.resize(frame, (width, height))

    return encode_jpeg(frame, quality)


@www_api_bp.route("/video/quality-presets")
def quality_presets():
    """Get available H.264 quality presets and camera native resolution.

    Returns JSON with available presets and camera information:
    {
        "presets": [
            {"name": "low", "width": 640, "height": 480, "fps": 15, "bitrate": "500k"},
            {"name": "medium", "width": 1280, "height": 720, "fps": 30, "bitrate": "1M"},
            {"name": "high", "width": 1920, "height": 1080, "fps": 30, "bitrate": "2M"}
        ],
        "camera_native_resolution": {"width": 1280, "height": 720, "fps": 30}
    }
    """
    # Convert QUALITY_PRESETS to list of dicts
    presets_list = []
    for name, preset in QUALITY_PRESETS.items():
        presets_list.append({
            "name": name,
            "width": preset.width,
            "height": preset.height,
            "fps": preset.fps,
            "bitrate": preset.bitrate,
        })

    # Get camera native resolution if running
    camera = current_app.config.get("camera")
    camera_native = None

    if camera and camera.is_running:
        props = camera.get_properties()
        camera_native = {
            "width": props.get("width"),
            "height": props.get("height"),
            "fps": props.get("fps"),
        }

    return jsonify({
        "presets": presets_list,
        "camera_native_resolution": camera_native,
    })


@www_api_bp.route("/snapshot/capture", methods=["POST"])
def capture_snapshot():
    """Capture a still image with custom quality and resolution.

    Request body:
    {
        "quality": 85,         // JPEG quality 1-100 (optional, default: 85)
        "width": 1280,         // Image width (optional, default: camera native)
        "height": 720,         // Image height (optional, default: camera native)
        "save_to_slot": false  // Save to active slot file (optional, default: false)
    }

    Returns:
        JPEG image data (binary)
    """
    camera = current_app.config.get("camera")
    if not camera or not camera.is_running:
        return jsonify({"error": "Camera not running"}), 503

    data = request.get_json() or {}

    # Get camera native resolution as defaults
    props = camera.get_properties()
    quality = data.get("quality", 85)
    width = data.get("width", props.get("width"))
    height = data.get("height", props.get("height"))
    save_to_slot = data.get("save_to_slot", False)

    # Validate parameters
    is_valid, error_msg = _validate_snapshot_params(quality, width, height)
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    # Capture snapshot
    jpeg_data = _capture_snapshot(quality, width, height)

    if jpeg_data is None:
        return jsonify({"error": "Failed to capture snapshot"}), 503

    # Optionally save to slot file
    if save_to_slot:
        settings = current_app.config.get("settings")
        active_slot = settings.get("active_camera_slot")

        if active_slot:
            try:
                app_root = Path(current_app.root_path).parent.parent
                snapshots_dir = app_root / "snapshots"
                snapshots_dir.mkdir(exist_ok=True)
                snapshot_path = snapshots_dir / f"slot{active_slot}_last.jpg"

                with open(snapshot_path, "wb") as f:
                    f.write(jpeg_data)

                logger.info(f"Saved snapshot to {snapshot_path}")
            except Exception as e:
                logger.warning(f"Failed to save snapshot to slot: {e}")

    # Return JPEG data
    return Response(jpeg_data, mimetype="image/jpeg")


@www_api_bp.route("/snapshot/settings")
def snapshot_settings():
    """Get default snapshot settings and available resolutions.

    Returns JSON with configuration information:
    {
        "default_quality": 85,
        "available_resolutions": [
            {"width": 640, "height": 480},
            {"width": 1280, "height": 720},
            {"width": 1920, "height": 1080}
        ],
        "quality_range": {"min": 1, "max": 100},
        "dimension_range": {
            "width": {"min": 160, "max": 3840},
            "height": {"min": 120, "max": 2160}
        }
    }
    """
    # Available resolutions based on common presets
    available_resolutions = [
        {"width": 640, "height": 480},
        {"width": 1280, "height": 720},
        {"width": 1920, "height": 1080},
        {"width": 2592, "height": 1944},  # 5MP full resolution
    ]

    return jsonify({
        "default_quality": 85,
        "available_resolutions": available_resolutions,
        "quality_range": {"min": 1, "max": 100},
        "dimension_range": {
            "width": {"min": 160, "max": 3840},
            "height": {"min": 120, "max": 2160},
        },
    })


@www_api_bp.route("/snapshot/quick", methods=["POST"])
def quick_snapshot():
    """Quick snapshot using quality preset dimensions.

    Request body (optional):
    {
        "preset": "medium"  // "low", "medium", or "high" (default: "medium")
    }

    Returns:
        JPEG image data (binary)
    """
    camera = current_app.config.get("camera")
    if not camera or not camera.is_running:
        return jsonify({"error": "Camera not running"}), 503

    data = request.get_json() or {}
    preset_name = data.get("preset", "medium")

    # Validate preset
    if preset_name not in QUALITY_PRESETS:
        return jsonify({
            "error": f"Invalid preset '{preset_name}'. Must be one of: {', '.join(QUALITY_PRESETS.keys())}"
        }), 400

    preset = QUALITY_PRESETS[preset_name]

    # Capture with preset dimensions and quality 85
    jpeg_data = _capture_snapshot(85, preset.width, preset.height)

    if jpeg_data is None:
        return jsonify({"error": "Failed to capture snapshot"}), 503

    return Response(jpeg_data, mimetype="image/jpeg")


@www_api_bp.route("/video/current-settings")
def current_settings():
    """Get detailed camera configuration and streaming settings.

    Returns JSON with complete current configuration:
    {
        "camera": {
            "device": "/dev/video0",
            "width": 1280,
            "height": 720,
            "fps": 30,
            "fourcc": "MJPG"
        },
        "h264": {
            "bitrate": "2M",
            "preset": "ultrafast",
            "tune": "zerolatency",
            "gop_size": 30
        },
        "active_slot": 1,
        "frame_count": 12345,
        "is_running": true
    }
    """
    camera = current_app.config.get("camera")
    settings = current_app.config.get("settings")
    app_config = current_app.config.get("app_config")
    frame_buffer = current_app.config.get("frame_buffer")

    if not camera:
        return jsonify({"error": "Camera not initialized"}), 500

    # Get camera properties
    camera_info = None
    is_running = False

    if camera.is_running:
        is_running = True
        props = camera.get_properties()
        camera_info = {
            "device": camera.device,
            "width": props.get("width"),
            "height": props.get("height"),
            "fps": props.get("fps"),
            "fourcc": props.get("fourcc"),
        }

    # Get H.264 configuration
    h264_config = {
        "bitrate": app_config.h264.bitrate,
        "preset": app_config.h264.preset,
        "tune": app_config.h264.tune,
        "gop_size": app_config.h264.gop_size,
        "use_hardware": app_config.h264.use_hardware,
    }

    # Get frame count
    frame_count = frame_buffer.frame_count if frame_buffer else 0

    return jsonify({
        "camera": camera_info,
        "h264": h264_config,
        "active_slot": settings.get("active_camera_slot"),
        "frame_count": frame_count,
        "is_running": is_running,
    })


@www_api_bp.route("/snapshot/slots")
def snapshot_slots():
    """List all camera slots with configuration and snapshot availability.

    Returns JSON with slot information:
    {
        "slots": [
            {
                "slot": 1,
                "type": "Wide Angle",
                "device": "/dev/video0",
                "enabled": true,
                "active": true,
                "has_snapshot": true
            },
            ...
        ]
    }
    """
    settings = current_app.config.get("settings")
    cameras = settings.get("cameras", [])
    active_slot = settings.get("active_camera_slot")

    # Map type codes to names
    type_names = {
        "W": "Wide Angle",
        "N": "Normal",
        "IR": "Infrared",
        "T": "Telephoto",
    }

    # Check snapshot directory
    app_root = Path(current_app.root_path).parent.parent
    snapshots_dir = app_root / "snapshots"

    slots_info = []
    for camera_config in cameras:
        slot_num = camera_config.get("slot")

        # Check if snapshot exists for this slot
        snapshot_path = snapshots_dir / f"slot{slot_num}_last.jpg"
        has_snapshot = snapshot_path.exists()

        slots_info.append({
            "slot": slot_num,
            "type": type_names.get(camera_config.get("type"), camera_config.get("type")),
            "device": camera_config.get("device"),
            "enabled": camera_config.get("enabled", False),
            "active": slot_num == active_slot,
            "has_snapshot": has_snapshot,
        })

    return jsonify({"slots": slots_info})


@www_api_bp.route("/robot/command", methods=["POST"])
def robot_command():
    """Send command array to USB robot controller (WWW/remote access).

    Request body:
    {
        "commands": [value1, value2, ...],  // Array of command values
        "read_response": false              // Optional: read response from device
    }

    Returns:
        JSON response with success status and optional device response.

    Example commands:
        - Motor control: [left_speed, right_speed] (e.g., [255, 255])
        - Servo positions: [servo1_angle, servo2_angle, servo3_angle]
        - Mixed commands: [motor_left, motor_right, servo1, servo2, led_state]
    """
    robot_device = current_app.config.get("robot_device")

    if robot_device is None:
        return jsonify({"error": "Robot device not initialized"}), 500

    # Get request data
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    commands = data.get("commands")
    if not isinstance(commands, list):
        return jsonify({"error": "Commands must be a JSON array"}), 400

    read_response = data.get("read_response", False)

    # Ensure device is connected
    if not robot_device.is_connected():
        if not robot_device.connect():
            return jsonify({
                "error": "Failed to connect to robot device",
                "device_info": robot_device.get_info()
            }), 503

    # Send command
    if read_response:
        success, message, response_data = robot_device.send_command_with_response(commands)
        return jsonify({
            "success": success,
            "message": message,
            "response": response_data,
            "commands_sent": commands
        }), 200 if success else 500
    else:
        success, message = robot_device.send_command(commands)
        return jsonify({
            "success": success,
            "message": message,
            "commands_sent": commands
        }), 200 if success else 500


@www_api_bp.route("/robot/status")
def robot_status():
    """Get robot device status and configuration."""
    robot_device = current_app.config.get("robot_device")
    settings = current_app.config.get("settings")

    if robot_device is None:
        return jsonify({
            "initialized": False,
            "config": settings.get("robot_device", {})
        })

    return jsonify({
        "initialized": True,
        "device_info": robot_device.get_info(),
        "config": settings.get("robot_device", {})
    })


@www_api_bp.route("/robot/connect", methods=["POST"])
def robot_connect():
    """Manually connect to robot device."""
    robot_device = current_app.config.get("robot_device")

    if robot_device is None:
        return jsonify({"error": "Robot device not initialized"}), 500

    if robot_device.is_connected():
        return jsonify({"message": "Already connected", "device_info": robot_device.get_info()})

    if robot_device.connect():
        return jsonify({"success": True, "message": "Connected", "device_info": robot_device.get_info()})
    else:
        return jsonify({"success": False, "error": "Failed to connect"}), 503


@www_api_bp.route("/robot/disconnect", methods=["POST"])
def robot_disconnect():
    """Manually disconnect from robot device."""
    robot_device = current_app.config.get("robot_device")

    if robot_device is None:
        return jsonify({"error": "Robot device not initialized"}), 500

    robot_device.disconnect()
    return jsonify({"success": True, "message": "Disconnected"})
