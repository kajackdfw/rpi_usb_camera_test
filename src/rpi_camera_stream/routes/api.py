"""API routes for settings."""

import logging
import os
import time
from pathlib import Path

from flask import Blueprint, Response, current_app, jsonify, request, send_file

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/rover-settings", methods=["GET"])
def get_settings():
    """Get all rover settings."""
    settings = current_app.config.get("settings")
    if settings is None:
        return jsonify({"error": "Settings not initialized"}), 500
    return jsonify(settings.get_all())


@api_bp.route("/rover-settings", methods=["POST"])
def update_settings():
    """Update rover settings."""
    settings = current_app.config.get("settings")
    if settings is None:
        return jsonify({"error": "Settings not initialized"}), 500

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    settings.update(data)
    return jsonify(settings.get_all())


@api_bp.route("/available-devices", methods=["GET"])
def get_available_devices():
    """Get list of available video devices for camera assignment."""
    from ..utils import get_camera_info, get_display_name

    devices = []
    for i in range(20):  # Check video0 through video19
        device_path = f"/dev/video{i}"
        if os.path.exists(device_path):
            device_info = get_camera_info(device_path)
            display_name = get_display_name(device_info)
            devices.append({
                "path": device_path,
                "name": display_name,
                "vendor_id": device_info.vendor_id,
                "model_id": device_info.model_id,
                "usb_path": device_info.usb_path,
            })

    return jsonify({"devices": devices})


@api_bp.route("/cameras", methods=["POST"])
def update_cameras():
    """Update camera slot configurations."""
    settings = current_app.config.get("settings")
    data = request.get_json()

    # Validate that we have exactly 3 camera slots
    if not isinstance(data.get("cameras"), list) or len(data["cameras"]) != 3:
        return jsonify({"error": "Must provide exactly 3 camera slots"}), 400

    # Validate each camera slot
    valid_types = {"W", "N", "IR", "T"}
    for i, camera in enumerate(data["cameras"], start=1):
        if camera.get("slot") != i:
            return jsonify({"error": f"Camera slot {i} has incorrect slot number"}), 400
        if camera.get("type") not in valid_types:
            return jsonify({"error": f"Invalid camera type: {camera.get('type')}"}), 400
        if not isinstance(camera.get("enabled"), bool):
            return jsonify({"error": f"Camera {i} enabled must be boolean"}), 400

    # Update settings (auto-persists to disk)
    settings.update({"cameras": data["cameras"]})

    return jsonify({"success": True, "cameras": settings.get("cameras")})


@api_bp.route("/switch-camera", methods=["POST"])
def switch_camera():
    """Switch the active camera and restart streaming."""
    settings = current_app.config.get("settings")
    data = request.get_json()
    slot = data.get("slot")

    # Validate slot number
    if not isinstance(slot, int) or slot < 1 or slot > 3:
        return jsonify({"error": "Invalid slot number (must be 1-3)"}), 400

    # Check if camera slot is configured and enabled
    cameras = settings.get("cameras", [])
    if slot > len(cameras):
        return jsonify({"error": "Camera slot not found"}), 404

    camera_config = cameras[slot - 1]
    if not camera_config.get("enabled") or not camera_config.get("device"):
        return jsonify({"error": "Camera slot not configured or disabled"}), 400

    # Save snapshot of current camera before stopping
    camera = current_app.config.get("camera")
    if camera and camera.is_running:
        current_active_slot = settings.get("active_camera_slot")
        if current_active_slot:
            try:
                from ..encoders import encode_jpeg

                frame_buffer = current_app.config["frame_buffer"]
                frame = frame_buffer.get_nowait()

                if frame is not None:
                    jpeg_data = encode_jpeg(frame)
                    if jpeg_data:
                        # Save snapshot to file - use consistent path calculation
                        # current_app.root_path is src/rpi_camera_stream, go up 2 levels to project root
                        app_root = Path(current_app.root_path).parent.parent
                        snapshots_dir = app_root / "snapshots"
                        snapshots_dir.mkdir(exist_ok=True)
                        snapshot_path = snapshots_dir / f"slot{current_active_slot}_last.jpg"

                        with open(snapshot_path, "wb") as f:
                            f.write(jpeg_data)

                        logger.info(f"Saved snapshot for slot {current_active_slot} at {snapshot_path}")
            except Exception as e:
                logger.warning(f"Failed to save snapshot: {e}")

        old_device = camera.device
        logger.info(f"Stopping current camera on {old_device}")
        camera.stop()

        # Give the OS time to release the device
        time.sleep(0.5)
        logger.info(f"Camera stopped, device {old_device} should now be released")

    # Update active camera slot setting
    settings.set("active_camera_slot", slot)

    # Start new camera with the configured device
    device_path = camera_config["device"]

    # Restart camera with new device
    from ..camera import OpenCVCamera, FrameBuffer
    from ..config import CameraConfig

    config = current_app.config.get("app_config")
    # Create new camera config with the device from the slot
    camera_config_obj = CameraConfig(
        device=device_path,
        width=config.camera.width,
        height=config.camera.height,
        fps=config.camera.fps,
    )

    frame_buffer = current_app.config["frame_buffer"]
    # Clear the frame buffer when switching cameras
    frame_buffer.clear()

    logger.info(f"Attempting to start camera on {device_path} (slot {slot})")
    new_camera = OpenCVCamera(camera_config_obj, frame_buffer)

    if new_camera.start():
        current_app.config["camera"] = new_camera
        logger.info(f"Successfully started camera on {device_path} (slot {slot})")

        return jsonify({
            "success": True,
            "active_slot": slot,
            "device": device_path,
            "type": camera_config["type"]
        })
    else:
        # Failed to start camera, keep previous slot active if possible
        logger.error(f"Failed to start camera on {device_path}")

        # Try to restart the previous camera if available
        if camera and not camera.is_running:
            prev_slot = settings.get("active_camera_slot")
            if prev_slot and prev_slot != slot:
                logger.info(f"Attempting to restart previous camera (slot {prev_slot})")
                settings.set("active_camera_slot", prev_slot)
        else:
            settings.set("active_camera_slot", None)

        return jsonify({"error": f"Failed to start camera on {device_path}. Device may be busy or not available."}), 500


@api_bp.route("/snapshot/<int:slot>", methods=["GET"])
def get_slot_snapshot(slot):
    """Get the last saved snapshot for a specific camera slot."""
    if slot < 1 or slot > 3:
        return jsonify({"error": "Invalid slot number"}), 400

    # Check for saved snapshot - use consistent path calculation
    # current_app.root_path is src/rpi_camera_stream, go up 2 levels to project root
    app_root = Path(current_app.root_path).parent.parent
    snapshots_dir = app_root / "snapshots"
    snapshot_path = snapshots_dir / f"slot{slot}_last.jpg"

    logger.debug(f"Looking for snapshot at: {snapshot_path}")

    if snapshot_path.exists():
        return send_file(snapshot_path, mimetype="image/jpeg")
    else:
        return jsonify({"error": f"No snapshot available for this slot (checked: {snapshot_path})"}), 404


@api_bp.route("/refresh-ip", methods=["POST"])
def refresh_ip():
    """Manually refresh the rover's public IP from cloud API."""
    settings = current_app.config.get("settings")

    from ..startup import fetch_rover_ip

    cloud_location = settings.get("cloud_location")
    if not cloud_location:
        return jsonify({"error": "No cloud_location configured"}), 400

    rover_ip = fetch_rover_ip(cloud_location, timeout=10)

    if rover_ip:
        settings.set("this_rover_ip", rover_ip)
        return jsonify({"success": True, "ip": rover_ip})
    else:
        return jsonify({"error": "Failed to fetch IP from cloud"}), 500


@api_bp.route("/qr", methods=["GET"])
def generate_qr():
    """Generate QR code for the LAN URL."""
    import io
    import qrcode

    settings = current_app.config.get("settings")
    if settings is None:
        return jsonify({"error": "Settings not initialized"}), 500

    # Get LAN IP from settings
    lan_ip = settings.get("lan_ip")
    if not lan_ip:
        return jsonify({"error": "LAN IP not detected"}), 500

    # Get port from request (assumes server is running on the same port as this request)
    port = request.host.split(":")[-1] if ":" in request.host else "5000"

    # Build full URL
    url = f"http://{lan_ip}:{port}/"

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,  # Smallest version that fits the data
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    # Create image
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to bytes
    img_io = io.BytesIO()
    img.save(img_io, "PNG")
    img_io.seek(0)

    # Create response with cache-control headers to prevent caching
    response = Response(img_io.read(), mimetype="image/png")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response
