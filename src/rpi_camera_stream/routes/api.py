"""API routes for settings."""

from flask import Blueprint, current_app, jsonify, request

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
