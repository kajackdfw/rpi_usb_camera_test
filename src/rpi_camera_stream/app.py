"""Flask application factory."""

import logging
import os

from flask import Flask
from flask_socketio import SocketIO

from .camera import FrameBuffer, OpenCVCamera
from .config import Config
from .routes import api_bp, mjpeg_bp, settings_bp
from .settings import Settings
from .socketio_handlers import VideoNamespace

logger = logging.getLogger(__name__)

socketio = SocketIO()
video_namespace = VideoNamespace()


def create_app(config: Config = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        config: Application configuration. Uses defaults if None.

    Returns:
        Configured Flask application.
    """
    if config is None:
        config = Config()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    app.template_folder = template_dir

    frame_buffer = FrameBuffer()
    camera = OpenCVCamera(config.camera, frame_buffer)

    app.config["frame_buffer"] = frame_buffer
    app.config["camera"] = camera
    app.config["app_config"] = config
    app.config["settings"] = Settings()

    app.register_blueprint(api_bp)
    app.register_blueprint(mjpeg_bp)
    app.register_blueprint(settings_bp)

    @app.context_processor
    def inject_settings():
        """Inject rover settings into all templates."""
        settings = app.config.get("settings")
        if settings is None:
            # Fallback if settings not initialized
            return {
                "rover_name": "Cattern Rover LAN",
                "settings": {}
            }

        settings_dict = settings.get_all()
        return {
            "rover_name": settings_dict.get("rover_name", "Cattern Rover LAN"),
            "settings": settings_dict
        }

    socketio.init_app(
        app,
        async_mode="eventlet",
        cors_allowed_origins=config.server.cors_origins,
    )
    socketio.on_namespace(video_namespace)

    return app


def run_server(config: Config = None) -> None:
    """Run the streaming server.

    Args:
        config: Application configuration. Uses defaults if None.
    """
    if config is None:
        config = Config()

    logging.basicConfig(
        level=logging.DEBUG if config.server.debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    app = create_app(config)
    camera: OpenCVCamera = app.config["camera"]

    if not camera.start():
        logger.warning("Camera not available - server will start without video capture")

    if config.enable_preview:
        from .preview import LocalDisplay
        preview = LocalDisplay(app.config["frame_buffer"])
        preview.start()
        app.config["preview"] = preview

    try:
        logger.info(f"Starting server on {config.server.host}:{config.server.port}")
        socketio.run(
            app,
            host=config.server.host,
            port=config.server.port,
            debug=config.server.debug,
            use_reloader=False,
        )
    finally:
        video_namespace.cleanup_all()
        camera.stop()
        if config.enable_preview and "preview" in app.config:
            app.config["preview"].stop()
