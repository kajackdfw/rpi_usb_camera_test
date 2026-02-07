"""Local preview window using OpenCV."""

import logging
import threading
from typing import Optional

import cv2

from ..camera import FrameBuffer

logger = logging.getLogger(__name__)

WINDOW_NAME = "Camera Preview"


class LocalDisplay:
    """Local preview window using OpenCV highgui."""

    def __init__(self, frame_buffer: FrameBuffer):
        self.frame_buffer = frame_buffer
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> bool:
        """Start the preview window.

        Returns:
            True if preview started, False if display not available.
        """
        if self._running:
            return True

        self._running = True
        self._thread = threading.Thread(target=self._display_loop, daemon=True)
        self._thread.start()
        logger.info("Local preview started")
        return True

    def stop(self) -> None:
        """Stop the preview window."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        cv2.destroyAllWindows()
        logger.info("Local preview stopped")

    def _display_loop(self) -> None:
        """Main display loop."""
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

        while self._running:
            frame = self.frame_buffer.get(timeout=0.1)
            if frame is not None:
                cv2.imshow(WINDOW_NAME, frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                logger.info("Preview window closed by user")
                self._running = False
                break

        cv2.destroyWindow(WINDOW_NAME)

    @property
    def is_running(self) -> bool:
        """Return whether the preview is running."""
        return self._running
