"""Socket.IO video streaming namespace."""

import logging
from typing import Optional

from flask import current_app
from flask_socketio import Namespace, emit

from ..camera import FrameBuffer, OpenCVCamera
from ..config import QUALITY_PRESETS, H264Config
from ..encoders import H264Encoder

logger = logging.getLogger(__name__)


class VideoNamespace(Namespace):
    """Socket.IO namespace for H.264 video streaming."""

    def __init__(self, namespace: str = "/video"):
        super().__init__(namespace)
        self._encoders: dict[str, H264Encoder] = {}
        self._frame_callbacks: dict[str, callable] = {}

    def on_connect(self):
        """Handle client connection."""
        from flask import request
        logger.info(f"Video client connected: {request.sid}")

    def on_disconnect(self):
        """Handle client disconnection."""
        from flask import request
        sid = request.sid
        logger.info(f"Video client disconnected: {sid}")
        self._stop_encoder(sid)

    def on_start_stream(self, data: dict):
        """Handle start_stream event from client.

        Args:
            data: Dict with optional 'quality' key ('low', 'medium', 'high').
        """
        from flask import request
        sid = request.sid

        quality = data.get("quality", "medium")
        if quality not in QUALITY_PRESETS:
            emit("error", {"message": f"Invalid quality: {quality}"})
            return

        preset = QUALITY_PRESETS[quality]
        logger.info(f"Starting stream for {sid} at {quality} quality")

        self._stop_encoder(sid)

        def on_h264_data(data: bytes):
            self.socketio.emit("h264_data", data, namespace=self.namespace, to=sid)

        h264_config = H264Config()
        encoder = H264Encoder(h264_config, preset, on_h264_data)

        if not encoder.start():
            emit("error", {"message": "Failed to start encoder"})
            return

        self._encoders[sid] = encoder

        def frame_callback(frame):
            if sid in self._encoders:
                self._encoders[sid].encode_frame(frame)

        self._frame_callbacks[sid] = frame_callback

        camera: Optional[OpenCVCamera] = current_app.config.get("camera")
        if camera is None or not camera.is_running:
            emit("error", {"message": "Camera not available"})
            self._stop_encoder(sid)
            return

        camera.add_frame_callback(frame_callback)

        emit("stream_started", {
            "width": preset.width,
            "height": preset.height,
            "fps": preset.fps,
        })

    def on_stop_stream(self, data: dict = None):
        """Handle stop_stream event from client."""
        from flask import request
        sid = request.sid
        logger.info(f"Stopping stream for {sid}")
        self._stop_encoder(sid)
        emit("stream_stopped", {})

    def _stop_encoder(self, sid: str) -> None:
        """Stop and cleanup encoder for a client."""
        if sid in self._frame_callbacks:
            camera: Optional[OpenCVCamera] = current_app.config.get("camera")
            if camera is not None:
                camera.remove_frame_callback(self._frame_callbacks[sid])
            del self._frame_callbacks[sid]

        if sid in self._encoders:
            self._encoders[sid].stop()
            del self._encoders[sid]

    def cleanup_all(self) -> None:
        """Stop all encoders (for shutdown)."""
        for sid in list(self._encoders.keys()):
            self._stop_encoder(sid)
