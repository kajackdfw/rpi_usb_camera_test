"""Thread-safe frame buffer for sharing frames between threads."""

import threading
from typing import Optional

import numpy as np


class FrameBuffer:
    """Thread-safe buffer for sharing the latest camera frame."""

    def __init__(self):
        self._frame: Optional[np.ndarray] = None
        self._lock = threading.Lock()
        self._frame_available = threading.Event()
        self._frame_count = 0

    def put(self, frame: np.ndarray) -> None:
        """Store a new frame in the buffer."""
        with self._lock:
            self._frame = frame.copy()
            self._frame_count += 1
        self._frame_available.set()

    def get(self, timeout: Optional[float] = None) -> Optional[np.ndarray]:
        """Get the latest frame from the buffer.

        Args:
            timeout: Maximum time to wait for a frame (seconds).

        Returns:
            The latest frame, or None if timeout expires.
        """
        if not self._frame_available.wait(timeout=timeout):
            return None
        with self._lock:
            return self._frame.copy() if self._frame is not None else None

    def get_nowait(self) -> Optional[np.ndarray]:
        """Get the latest frame without waiting."""
        with self._lock:
            return self._frame.copy() if self._frame is not None else None

    @property
    def frame_count(self) -> int:
        """Return the total number of frames captured."""
        with self._lock:
            return self._frame_count

    def clear(self) -> None:
        """Clear the buffer."""
        with self._lock:
            self._frame = None
        self._frame_available.clear()
