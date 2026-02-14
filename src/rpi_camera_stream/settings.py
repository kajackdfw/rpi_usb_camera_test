"""Server-side settings storage using JSON file."""

import json
import logging
import os
from pathlib import Path
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_SETTINGS = {
    "rover_name": "Cattern Rover LAN",
    "cloud_location": "https://cattern.com",
    "this_rover_ip": None,
    "lan_ip": None,
    "hardware": {
        "cpu_model": "Unknown",
        "cpu_cores": 0,
        "memory_mb": 0,
        "os_name": "Unknown",
        "os_version": "Unknown",
        "platform": "Unknown",
    },
    "active_camera_slot": None,  # No camera active by default
    "cameras": [
        {"slot": 1, "device": "", "type": "N", "enabled": False},
        {"slot": 2, "device": "", "type": "N", "enabled": False},
        {"slot": 3, "device": "", "type": "N", "enabled": False},
    ],
}


class Settings:
    """Thread-safe JSON file settings manager."""

    def __init__(self, settings_file: str = None):
        if settings_file is None:
            # Default to settings.json in the app directory
            settings_file = os.path.join(
                os.path.dirname(__file__), "..", "..", "settings.json"
            )
        self._file_path = Path(settings_file).resolve()
        self._lock = Lock()
        self._settings: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load settings from JSON file."""
        with self._lock:
            if self._file_path.exists():
                try:
                    with open(self._file_path, "r") as f:
                        self._settings = json.load(f)
                    logger.info(f"Loaded settings from {self._file_path}")

                    # Merge missing keys from DEFAULT_SETTINGS (for upgrades)
                    needs_save = False
                    for key, value in DEFAULT_SETTINGS.items():
                        if key not in self._settings:
                            self._settings[key] = value
                            needs_save = True
                            logger.info(f"Added missing setting key: {key}")

                    if needs_save:
                        self._save_unlocked()

                except (json.JSONDecodeError, IOError) as e:
                    logger.error(f"Failed to load settings: {e}")
                    self._settings = DEFAULT_SETTINGS.copy()
            else:
                self._settings = DEFAULT_SETTINGS.copy()
                self._save_unlocked()

    def _save_unlocked(self) -> None:
        """Save settings to JSON file (must hold lock)."""
        try:
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._file_path, "w") as f:
                json.dump(self._settings, f, indent=2)
            logger.info(f"Saved settings to {self._file_path}")
        except IOError as e:
            logger.error(f"Failed to save settings: {e}")

    def _save(self) -> None:
        """Save settings to JSON file."""
        with self._lock:
            self._save_unlocked()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        with self._lock:
            return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a setting value and save."""
        with self._lock:
            self._settings[key] = value
            self._save_unlocked()

    def get_all(self) -> dict[str, Any]:
        """Get all settings."""
        with self._lock:
            return self._settings.copy()

    def update(self, settings: dict[str, Any]) -> None:
        """Update multiple settings and save."""
        with self._lock:
            self._settings.update(settings)
            self._save_unlocked()

    def reset(self) -> None:
        """Reset to default settings."""
        with self._lock:
            self._settings = DEFAULT_SETTINGS.copy()
            self._save_unlocked()
