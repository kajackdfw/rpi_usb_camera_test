"""USB camera device information utilities."""

import logging
import os
import re
import subprocess
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class CameraDeviceInfo:
    """Camera device information from udevadm."""

    device_path: str
    model_name: Optional[str] = None
    product_name: Optional[str] = None  # ID_V4L_PRODUCT from udevadm
    vendor_id: Optional[str] = None
    model_id: Optional[str] = None
    usb_path: Optional[str] = None  # ID_PATH - unique USB bus/port location
    exists: bool = False


def get_camera_info(device_path: str) -> CameraDeviceInfo:
    """Query udevadm for camera device information.

    Args:
        device_path: Path to the video device (e.g., /dev/video0)

    Returns:
        CameraDeviceInfo with available device properties
    """
    info = CameraDeviceInfo(device_path=device_path)

    # Check if device exists
    if not os.path.exists(device_path):
        logger.debug(f"Device {device_path} does not exist")
        return info

    info.exists = True

    try:
        # Query udevadm for device properties
        result = subprocess.run(
            ["udevadm", "info", "--query=property", f"--name={device_path}"],
            capture_output=True,
            text=True,
            timeout=2.0,
        )

        if result.returncode != 0:
            logger.warning(
                f"udevadm query failed for {device_path}: {result.stderr.strip()}"
            )
            return info

        # Parse output for relevant properties
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line or "=" not in line:
                continue

            key, _, value = line.partition("=")

            if key == "ID_V4L_PRODUCT":
                info.product_name = value
            elif key == "ID_MODEL":
                info.model_name = value
            elif key == "ID_VENDOR_ID":
                info.vendor_id = value
            elif key == "ID_MODEL_ID":
                info.model_id = value
            elif key == "ID_PATH":
                info.usb_path = value

        logger.debug(
            f"Device {device_path}: product={info.product_name}, "
            f"model={info.model_name}, usb={info.vendor_id}:{info.model_id}, "
            f"path={info.usb_path}"
        )

    except subprocess.TimeoutExpired:
        logger.error(f"udevadm query timed out for {device_path}")
    except FileNotFoundError:
        logger.error(
            "udevadm command not found. Install with: sudo apt-get install udev"
        )
    except Exception as e:
        logger.error(f"Error querying device info for {device_path}: {e}")

    return info


def get_display_name(device_info: CameraDeviceInfo) -> str:
    """Get human-readable display name for a camera device.

    Priority order:
    1. Check if device exists - return "Not Found" if missing
    2. ID_V4L_PRODUCT (most specific camera name)
    3. ID_MODEL (USB device model)
    4. Fallback to "Camera X" based on device path

    Args:
        device_info: CameraDeviceInfo object

    Returns:
        Human-readable camera name
    """
    # If device doesn't exist, return "Not Found"
    if not device_info.exists:
        return "Not Found"

    # Try product name first (most specific)
    if device_info.product_name:
        return device_info.product_name

    # Try model name next
    if device_info.model_name:
        # Clean up underscores that sometimes appear in model names
        return device_info.model_name.replace("_", " ")

    # Fallback to generic name based on device path
    # Extract camera number from path (e.g., /dev/video0 -> Camera 0)
    match = re.search(r"video(\d+)", device_info.device_path)
    if match:
        camera_num = match.group(1)
        return f"Camera {camera_num}"

    return "Unknown Camera"
