"""Camera capture module."""

from .frame_buffer import FrameBuffer
from .opencv_capture import OpenCVCamera

__all__ = ["FrameBuffer", "OpenCVCamera"]
