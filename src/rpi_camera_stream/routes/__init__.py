"""Flask routes module."""

from .api import api_bp
from .mjpeg import mjpeg_bp
from .settings import settings_bp

__all__ = ["api_bp", "mjpeg_bp", "settings_bp"]
