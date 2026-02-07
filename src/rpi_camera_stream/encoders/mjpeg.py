"""MJPEG encoding utilities."""

from typing import Optional

import cv2
import numpy as np


def encode_jpeg(frame: np.ndarray, quality: int = 80) -> Optional[bytes]:
    """Encode a BGR frame as JPEG.

    Args:
        frame: BGR image as numpy array.
        quality: JPEG quality (1-100).

    Returns:
        JPEG encoded bytes, or None on failure.
    """
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
    success, encoded = cv2.imencode(".jpg", frame, encode_params)
    if not success:
        return None
    return encoded.tobytes()
