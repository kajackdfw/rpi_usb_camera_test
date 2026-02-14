"""Flask routes module."""

from .api import api_bp
from .mjpeg import mjpeg_bp
from .settings import settings_bp
from .www import www_bp
from .www_api import www_api_bp

__all__ = ["api_bp", "mjpeg_bp", "settings_bp", "www_bp", "www_api_bp"]
