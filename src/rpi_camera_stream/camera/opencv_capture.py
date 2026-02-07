"""OpenCV-based camera capture using V4L2 backend."""

import logging
import threading
from typing import Callable, Optional

import cv2
import numpy as np

from ..config import CameraConfig
from .frame_buffer import FrameBuffer

logger = logging.getLogger(__name__)


class OpenCVCamera:
    """Camera capture using OpenCV with V4L2 backend."""

    def __init__(self, config: CameraConfig, frame_buffer: FrameBuffer):
        self.config = config
        self.frame_buffer = frame_buffer
        self._capture: Optional[cv2.VideoCapture] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._on_frame_callbacks: list[Callable[[np.ndarray], None]] = []

    def start(self) -> bool:
        """Start the camera capture thread.

        Returns:
            True if camera started successfully, False otherwise.
        """
        if self._running:
            logger.warning("Camera already running")
            return True

        self._capture = cv2.VideoCapture(self.config.device, cv2.CAP_V4L2)
        if not self._capture.isOpened():
            logger.error(f"Failed to open camera: {self.config.device}")
            return False

        fourcc = cv2.VideoWriter_fourcc(*self.config.fourcc)
        self._capture.set(cv2.CAP_PROP_FOURCC, fourcc)
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
        self._capture.set(cv2.CAP_PROP_FPS, self.config.fps)

        actual_width = int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self._capture.get(cv2.CAP_PROP_FPS)

        logger.info(
            f"Camera opened: {actual_width}x{actual_height} @ {actual_fps:.1f} fps"
        )

        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        """Stop the camera capture."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        if self._capture is not None:
            self._capture.release()
            self._capture = None
        logger.info("Camera stopped")

    def add_frame_callback(self, callback: Callable[[np.ndarray], None]) -> None:
        """Add a callback to be called for each captured frame."""
        self._on_frame_callbacks.append(callback)

    def remove_frame_callback(self, callback: Callable[[np.ndarray], None]) -> None:
        """Remove a frame callback."""
        if callback in self._on_frame_callbacks:
            self._on_frame_callbacks.remove(callback)

    def _capture_loop(self) -> None:
        """Main capture loop running in a separate thread."""
        while self._running:
            if self._capture is None:
                break

            ret, frame = self._capture.read()
            if not ret:
                logger.warning("Failed to read frame from camera")
                continue

            self.frame_buffer.put(frame)

            for callback in self._on_frame_callbacks:
                try:
                    callback(frame)
                except Exception as e:
                    logger.error(f"Frame callback error: {e}")

    @property
    def is_running(self) -> bool:
        """Return whether the camera is running."""
        return self._running

    def get_properties(self) -> dict:
        """Get current camera properties."""
        if self._capture is None:
            return {}
        return {
            "width": int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": self._capture.get(cv2.CAP_PROP_FPS),
            "fourcc": self.config.fourcc,
        }
