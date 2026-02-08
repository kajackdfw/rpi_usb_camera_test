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

    # Load settings first to check for active camera configuration
    settings = Settings()

    frame_buffer = FrameBuffer()

    # Check if there's an active camera slot configured
    active_slot = settings.get("active_camera_slot")
    cameras = settings.get("cameras", [])

    logger.info(f"Startup: active_camera_slot = {active_slot}, cameras = {cameras}")

    camera_started = False
    if active_slot and cameras and active_slot <= len(cameras):
        camera_config = cameras[active_slot - 1]
        logger.info(f"Checking slot {active_slot}: enabled={camera_config.get('enabled')}, device={camera_config.get('device')}")
        if camera_config.get("enabled") and camera_config.get("device"):
            # Use the configured device for the active slot
            config.camera.device = camera_config["device"]
            logger.info(f"Starting with configured camera: Slot {active_slot} on {camera_config['device']}")
            camera_started = True
        else:
            logger.warning(f"Slot {active_slot} is not properly configured (enabled={camera_config.get('enabled')}, device={camera_config.get('device')})")

    # If no active camera is set, try to start the first enabled camera
    if not camera_started and cameras:
        logger.info("No active camera started yet, looking for first enabled camera...")
        for cam_config in cameras:
            if cam_config.get("enabled") and cam_config.get("device"):
                config.camera.device = cam_config["device"]
                settings.set("active_camera_slot", cam_config["slot"])
                logger.info(f"No active camera set. Starting first enabled camera: Slot {cam_config['slot']} on {cam_config['device']}")
                break

    camera = OpenCVCamera(config.camera, frame_buffer)

    app.config["frame_buffer"] = frame_buffer
    app.config["camera"] = camera
    app.config["app_config"] = config
    app.config["settings"] = settings

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
