"""Settings page routes."""

from flask import Blueprint, render_template

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/settings")
def index():
    """Render the settings page."""
    return render_template("settings.html")
