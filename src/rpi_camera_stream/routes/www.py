"""WWW (cloud/remote) streaming routes."""

import logging
from flask import Blueprint, render_template, current_app, jsonify

logger = logging.getLogger(__name__)

www_bp = Blueprint("www", __name__, url_prefix="/www")


@www_bp.route("/")
def index():
    """WWW home page - shows H.264 streaming info."""
    return render_template("www_index.html")


@www_bp.route("/streams")
def streams():
    """Render WWW camera streams overview page."""
    from ..utils import get_camera_info, get_display_name

    # Get camera slot configuration from settings
    settings = current_app.config.get("settings")
    camera_configs = settings.get("cameras", [])

    camera_slots = []

    # Map camera type to readable name
    type_names = {
        "W": "Wide Angle",
        "N": "Normal",
        "IR": "Infrared",
        "T": "Telephoto"
    }

    for config in camera_configs:
        # Skip unconfigured slots
        if not config["enabled"]:
            continue

        slot_id = config["slot"] - 1
        device_path = config["device"]
        camera_type = config["type"]
        enabled = config["enabled"]

        # Query device information
        device_info = get_camera_info(device_path)
        display_name = get_display_name(device_info)

        camera_slots.append({
            "id": slot_id,
            "slot": config["slot"],
            "name": display_name,
            "device": device_path or f"Camera {config['slot']}",
            "type": camera_type,
            "type_name": type_names.get(camera_type, "Normal"),
            "exists": device_info.exists,
            "enabled": enabled,
        })

    # If no cameras configured, return error
    if not camera_slots:
        return jsonify({"error": "No cameras configured"}), 404

    # Get the active camera slot from settings
    active_slot = settings.get("active_camera_slot")

    # Mark the active camera slot
    for cam in camera_slots:
        cam["active"] = (cam["slot"] == active_slot) if active_slot else False

    return render_template("www_streams.html", cameras=camera_slots)


@www_bp.route("/stream/<int:slot>")
def stream(slot):
    """Render individual camera H.264 stream page for WWW."""
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

    return render_template("www_stream.html", camera_slot=slot, camera_type=camera_config["type"])


@www_bp.route("/api/status")
def status():
    """Get camera status for WWW clients."""
    camera = current_app.config.get("camera")
    settings = current_app.config.get("settings")

    if camera is None:
        return jsonify({"status": "not_initialized"})

    return jsonify({
        "status": "running" if camera.is_running else "stopped",
        "active_slot": settings.get("active_camera_slot"),
        "rover_ip": settings.get("this_rover_ip"),
        "cloud_location": settings.get("cloud_location"),
    })
