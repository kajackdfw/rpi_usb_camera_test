"""Serial communication with USB robot controller (Arduino/Waveshare)."""

import json
import logging
import threading
from typing import Any, Optional

logger = logging.getLogger(__name__)


class RobotSerialDevice:
    """Thread-safe serial communication with USB robot controller.

    Handles communication with Arduino or Waveshare general purpose robot boards
    via USB serial connection. Supports sending JSON arrays for drive commands.
    """

    def __init__(self, port: str, baud_rate: int = 115200, timeout: float = 1.0):
        """Initialize robot serial device.

        Args:
            port: Serial port path (e.g., /dev/ttyUSB0, /dev/ttyACM0)
            baud_rate: Serial baud rate (default: 115200)
            timeout: Read/write timeout in seconds
        """
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self._serial = None
        self._lock = threading.Lock()
        self._connected = False

    def connect(self) -> bool:
        """Open serial connection to robot controller.

        Returns:
            True if connection successful, False otherwise.
        """
        with self._lock:
            if self._connected:
                return True

            try:
                import serial

                self._serial = serial.Serial(
                    port=self.port,
                    baudrate=self.baud_rate,
                    timeout=self.timeout,
                    write_timeout=self.timeout,
                )
                self._connected = True
                logger.info(f"Connected to robot controller on {self.port} @ {self.baud_rate} baud")
                return True

            except ImportError:
                logger.error("pyserial library not installed. Install with: pip install pyserial")
                return False
            except Exception as e:
                logger.error(f"Failed to connect to robot controller on {self.port}: {e}")
                return False

    def disconnect(self) -> None:
        """Close serial connection."""
        with self._lock:
            if self._serial and self._connected:
                try:
                    self._serial.close()
                    logger.info(f"Disconnected from robot controller on {self.port}")
                except Exception as e:
                    logger.warning(f"Error closing serial connection: {e}")
                finally:
                    self._connected = False
                    self._serial = None

    def is_connected(self) -> bool:
        """Check if serial connection is active.

        Returns:
            True if connected, False otherwise.
        """
        with self._lock:
            return self._connected

    def send_command(self, command_array: list[Any]) -> tuple[bool, str]:
        """Send JSON array command to robot controller.

        Args:
            command_array: List of command values to send to robot
                          (e.g., motor speeds, servo positions)

        Returns:
            Tuple of (success, message/error)
        """
        with self._lock:
            if not self._connected or not self._serial:
                return False, "Robot controller not connected"

            try:
                # Convert array to JSON string and append newline
                json_str = json.dumps(command_array) + "\n"

                # Send to serial device
                bytes_written = self._serial.write(json_str.encode('utf-8'))
                self._serial.flush()

                logger.debug(f"Sent {bytes_written} bytes to robot: {json_str.strip()}")

                return True, f"Command sent successfully ({bytes_written} bytes)"

            except Exception as e:
                error_msg = f"Failed to send command: {e}"
                logger.error(error_msg)
                return False, error_msg

    def send_command_with_response(
        self,
        command_array: list[Any],
        read_lines: int = 1
    ) -> tuple[bool, str, Optional[str]]:
        """Send command and read response from robot controller.

        Args:
            command_array: List of command values to send
            read_lines: Number of lines to read from response

        Returns:
            Tuple of (success, message/error, response_data)
        """
        with self._lock:
            if not self._connected or not self._serial:
                return False, "Robot controller not connected", None

            try:
                # Send command
                json_str = json.dumps(command_array) + "\n"
                bytes_written = self._serial.write(json_str.encode('utf-8'))
                self._serial.flush()

                logger.debug(f"Sent {bytes_written} bytes to robot: {json_str.strip()}")

                # Read response
                responses = []
                for _ in range(read_lines):
                    try:
                        line = self._serial.readline().decode('utf-8').strip()
                        if line:
                            responses.append(line)
                    except Exception as read_error:
                        logger.warning(f"Error reading response: {read_error}")
                        break

                response_str = "\n".join(responses) if responses else None

                return True, f"Command sent successfully", response_str

            except Exception as e:
                error_msg = f"Failed to send command: {e}"
                logger.error(error_msg)
                return False, error_msg, None

    def get_info(self) -> dict[str, Any]:
        """Get device information.

        Returns:
            Dictionary with device status and configuration.
        """
        with self._lock:
            return {
                "port": self.port,
                "baud_rate": self.baud_rate,
                "timeout": self.timeout,
                "connected": self._connected,
            }
