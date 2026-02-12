"""Startup tasks for rover initialization."""

import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)


def fetch_rover_ip(cloud_location: str, timeout: int = 10) -> Optional[str]:
    """
    Fetch the rover's public IP address from the cloud API.

    Args:
        cloud_location: Base URL of cloud server (e.g., "https://cattern.com")
        timeout: Request timeout in seconds

    Returns:
        IP address string, or None if fetch failed
    """
    if not cloud_location:
        logger.warning("No cloud_location configured, skipping IP detection")
        return None

    api_url = f"{cloud_location.rstrip('/')}/api/getMyIP?format=json"

    try:
        logger.info(f"Fetching public IP from {api_url}")
        response = requests.get(api_url, timeout=timeout)
        response.raise_for_status()

        data = response.json()
        ip_address = data.get("ip")

        if ip_address:
            logger.info(f"Successfully fetched rover IP: {ip_address}")
            return ip_address
        else:
            logger.error(f"Cloud API returned no IP address: {data}")
            return None

    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching IP from {api_url}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch IP from cloud: {e}")
        return None
    except (KeyError, ValueError) as e:
        logger.error(f"Invalid JSON response from cloud: {e}")
        return None


def get_local_ip() -> Optional[str]:
    """
    Get the local network IP address (LAN IP).

    Uses socket to connect to an external address to determine which
    local interface would be used, without actually sending data.

    Returns:
        Local IP address string (e.g., "192.168.1.100"), or None if detection fails
    """
    import socket

    try:
        # Create a socket and connect to an external address
        # This doesn't actually send data, just determines routing
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)

        # Connect to Google DNS (8.8.8.8) to determine local interface
        # Port 80 is arbitrary - no actual connection is made
        s.connect(('8.8.8.8', 80))

        # Get the socket's own address
        local_ip = s.getsockname()[0]
        s.close()

        logger.info(f"Detected local IP: {local_ip}")
        return local_ip

    except Exception as e:
        logger.warning(f"Failed to detect local IP: {e}")
        return None


def run_startup_tasks(settings) -> None:
    """
    Run all startup tasks (IP detection, etc.).

    Args:
        settings: Settings instance
    """
    logger.info("Running startup tasks...")

    # Detect local LAN IP
    lan_ip = get_local_ip()
    if lan_ip:
        settings.set("lan_ip", lan_ip)
        logger.info(f"Local LAN IP stored in settings: {lan_ip}")
    else:
        logger.warning("Failed to detect local LAN IP")

    # Fetch rover IP from cloud
    cloud_location = settings.get("cloud_location")
    if cloud_location:
        rover_ip = fetch_rover_ip(cloud_location, timeout=10)
        if rover_ip:
            settings.set("this_rover_ip", rover_ip)
            logger.info(f"Rover IP stored in settings: {rover_ip}")
        else:
            logger.warning("Failed to fetch rover IP, continuing without it")
    else:
        logger.info("No cloud_location configured, skipping IP detection")

    logger.info("Startup tasks completed")
