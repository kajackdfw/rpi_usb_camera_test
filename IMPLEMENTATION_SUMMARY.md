# Robot Control API Implementation Summary

## Overview

Added robot control functionality to send JSON command arrays to USB-connected Arduino or Waveshare boards via two API routes (LAN and WWW).

## Files Created

1. **`src/rpi_camera_stream/robot/__init__.py`**
   - Module initialization

2. **`src/rpi_camera_stream/robot/serial_device.py`**
   - `RobotSerialDevice` class for USB serial communication
   - Thread-safe serial operations
   - Methods: `connect()`, `disconnect()`, `send_command()`, `send_command_with_response()`
   - JSON serialization of command arrays

3. **`ROBOT_API.md`**
   - Complete API documentation
   - Configuration examples
   - Testing examples
   - Troubleshooting guide

## Files Modified

1. **`src/rpi_camera_stream/settings.py`**
   - Added `robot_device` to `DEFAULT_SETTINGS`:
     ```python
     "robot_device": {
         "enabled": False,
         "port": "/dev/ttyUSB0",
         "baud_rate": 115200,
         "timeout": 1.0,
         "auto_connect": False
     }
     ```

2. **`src/rpi_camera_stream/app.py`**
   - Initialize robot device on startup (if enabled)
   - Auto-connect support
   - Add robot_device to app.config
   - Cleanup on shutdown (disconnect device)

3. **`src/rpi_camera_stream/routes/api.py`**
   - Added LAN robot control routes:
     - `POST /api/robot/command` - Send command array
     - `GET /api/robot/status` - Get device status
     - `POST /api/robot/connect` - Manual connect
     - `POST /api/robot/disconnect` - Manual disconnect

4. **`src/rpi_camera_stream/routes/www_api.py`**
   - Added WWW robot control routes (identical functionality):
     - `POST /www/api/robot/command`
     - `GET /www/api/robot/status`
     - `POST /www/api/robot/connect`
     - `POST /www/api/robot/disconnect`

5. **`pyproject.toml`**
   - Added `pyserial>=3.5` dependency

## API Endpoints

### LAN Routes (Local Network)

- `POST /api/robot/command` - Send JSON command array
- `GET /api/robot/status` - Get device status
- `POST /api/robot/connect` - Connect to device
- `POST /api/robot/disconnect` - Disconnect from device

### WWW Routes (Remote Access)

- `POST /www/api/robot/command` - Send JSON command array
- `GET /www/api/robot/status` - Get device status
- `POST /www/api/robot/connect` - Connect to device
- `POST /www/api/robot/disconnect` - Disconnect from device

## Command Format

Commands are sent as JSON arrays:

```json
{
  "commands": [value1, value2, value3, ...],
  "read_response": false  // optional
}
```

Example:
```bash
curl -X POST http://localhost:5000/api/robot/command \
  -H "Content-Type: application/json" \
  -d '{"commands": [255, 128, 0]}'
```

## Configuration

Enable and configure in `settings.json`:

```json
{
  "robot_device": {
    "enabled": true,
    "port": "/dev/ttyUSB0",
    "baud_rate": 115200,
    "timeout": 1.0,
    "auto_connect": true
  }
}
```

## Features

✅ Thread-safe serial communication
✅ Automatic JSON serialization
✅ Optional response reading from device
✅ Auto-connect on startup (configurable)
✅ Manual connect/disconnect endpoints
✅ Graceful error handling
✅ Device status reporting
✅ Both LAN and WWW access routes
✅ Configurable baud rate and timeout
✅ Automatic device reconnection on command send

## Testing

All endpoints tested and working:
- ✅ Status endpoints return correct configuration
- ✅ Command endpoints validate input (array required)
- ✅ Error handling for device not initialized
- ✅ Error handling for device not connected
- ✅ Both LAN and WWW routes functional

## Dependencies

- `pyserial>=3.5` - USB serial communication

Install with:
```bash
pip install -e .
```

## Usage Example

```python
import requests

# Send motor commands
response = requests.post(
    "http://localhost:5000/api/robot/command",
    json={"commands": [255, 255]}  # Full speed forward
)
print(response.json())
```

## Next Steps

1. Enable robot device in settings.json
2. Connect Arduino or Waveshare board via USB
3. Upload firmware to robot controller
4. Test with curl or Python requests
5. Integrate with React frontend for remote control
