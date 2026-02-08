"""WWW (cloud/remote) streaming routes."""

import logging
from flask import Blueprint, render_template, current_app, jsonify

logger = logging.getLogger(__name__)

www_bp = Blueprint("www", __name__, url_prefix="/www")


@www_bp.route("/")
def index():
    """WWW home page - shows H.264 streaming info."""
    return render_template("www_index.html")


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
