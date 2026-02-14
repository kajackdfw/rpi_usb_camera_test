"""Flask application factory."""

import ipaddress
import logging
import os

from flask import Flask, redirect, request, url_for
from flask_socketio import SocketIO

from .camera import FrameBuffer, OpenCVCamera
from .config import Config
from .routes import api_bp, mjpeg_bp, settings_bp, www_bp, www_api_bp
from .settings import Settings
from .socketio_handlers import VideoNamespace

logger = logging.getLogger(__name__)

socketio = SocketIO()
video_namespace = VideoNamespace()


def is_local_request() -> bool:
    """Determine if the current request is from the local network.

    Checks if request originates from localhost or private IP ranges (LAN).
    Supports proxy headers (X-Forwarded-For, X-Real-IP).

    Returns:
        True if request is from local network (localhost or LAN), False otherwise.
    """
    # Get the remote address, checking proxy headers first
    remote_addr = request.headers.get('X-Real-IP')
    if not remote_addr:
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs: "client, proxy1, proxy2"
            # The first IP is the original client
            remote_addr = forwarded_for.split(',')[0].strip()

    if not remote_addr:
        remote_addr = request.remote_addr

    if not remote_addr:
        # No remote address found, default to remote (secure)
        return False

    try:
        ip = ipaddress.ip_address(remote_addr)

        # Check if it's a loopback address (localhost)
        if ip.is_loopback:
            return True

        # Check if it's a private address (LAN)
        if ip.is_private:
            return True

        # Check if it's link-local (fe80::/10 for IPv6, 169.254.0.0/16 for IPv4)
        if ip.is_link_local:
            return True

        return False

    except ValueError:
        # Invalid IP address format, default to remote (secure)
        return False


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

    # Run startup tasks (IP detection, etc.)
    from .startup import run_startup_tasks
    run_startup_tasks(settings)

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

    # Initialize robot device if enabled
    robot_device = None
    robot_config = settings.get("robot_device", {})
    if robot_config.get("enabled"):
        from .robot import RobotSerialDevice

        robot_device = RobotSerialDevice(
            port=robot_config.get("port", "/dev/ttyUSB0"),
            baud_rate=robot_config.get("baud_rate", 115200),
            timeout=robot_config.get("timeout", 1.0)
        )

        # Auto-connect if configured
        if robot_config.get("auto_connect"):
            if robot_device.connect():
                logger.info("Robot device connected on startup")
            else:
                logger.warning("Failed to auto-connect robot device")

    app.config["frame_buffer"] = frame_buffer
    app.config["camera"] = camera
    app.config["app_config"] = config
    app.config["settings"] = settings
    app.config["robot_device"] = robot_device

    app.register_blueprint(api_bp)
    app.register_blueprint(mjpeg_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(www_bp)
    app.register_blueprint(www_api_bp)

    @app.route("/")
    def root():
        """Redirect root based on request origin.

        - Local network requests (localhost/LAN) → /lan/ (MJPEG viewer)
        - Remote requests (Internet) → /www/ (H.264 streaming, secure by default)
        """
        if is_local_request():
            return redirect(url_for("mjpeg.index"))
        else:
            return redirect(url_for("www.index"))

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
        # Disconnect robot device if connected
        robot_device = app.config.get("robot_device")
        if robot_device and robot_device.is_connected():
            robot_device.disconnect()
