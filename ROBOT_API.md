# Robot Control API Documentation

This document describes the robot control API endpoints for sending commands to USB-connected Arduino or Waveshare general purpose robot boards.

## Overview

The system provides identical robot control functionality via two separate API endpoints:
- **LAN route**: `/api/robot/*` - For local network access
- **WWW route**: `/www/api/robot/*` - For remote access via internet

Both routes use the same underlying serial communication system and support the same command format.

## Configuration

Robot device settings are stored in `settings.json`:

```json
{
  "robot_device": {
    "enabled": false,
    "port": "/dev/ttyUSB0",
    "baud_rate": 115200,
    "timeout": 1.0,
    "auto_connect": false
  }
}
```

### Configuration Options

- **enabled**: Set to `true` to initialize the robot device on startup
- **port**: Serial port path (e.g., `/dev/ttyUSB0`, `/dev/ttyACM0`)
  - Arduino typically uses `/dev/ttyACM0` or `/dev/ttyUSB0`
  - Waveshare boards typically use `/dev/ttyUSB0`
- **baud_rate**: Serial communication speed (default: 115200)
- **timeout**: Read/write timeout in seconds (default: 1.0)
- **auto_connect**: Automatically connect to device on server startup (default: false)

## API Endpoints

### 1. Get Robot Status

Get current robot device status and configuration.

**LAN**: `GET /api/robot/status`
**WWW**: `GET /www/api/robot/status`

**Response (device not initialized):**
```json
{
  "initialized": false,
  "config": {
    "enabled": false,
    "port": "/dev/ttyUSB0",
    "baud_rate": 115200,
    "timeout": 1.0,
    "auto_connect": false
  }
}
```

### 2. Send Robot Command

Send a JSON array of commands to the robot controller.

**LAN**: `POST /api/robot/command`
**WWW**: `POST /www/api/robot/command`

**Request Body:**
```json
{
  "commands": [255, 128, 0, 90, 1],
  "read_response": false
}
```

**Parameters:**
- `commands` (required): Array of command values (numbers)
- `read_response` (optional): Set to `true` to read response from device (default: false)

**Response (success):**
```json
{
  "success": true,
  "message": "Command sent successfully (20 bytes)",
  "commands_sent": [255, 128, 0, 90, 1]
}
```

### 3. Connect to Robot Device

**LAN**: `POST /api/robot/connect`
**WWW**: `POST /www/api/robot/connect`

### 4. Disconnect from Robot Device

**LAN**: `POST /api/robot/disconnect`
**WWW**: `POST /www/api/robot/disconnect`

## Example Command Formats

**Two-motor differential drive:**
```json
{"commands": [left_speed, right_speed]}
```
- Values: -255 to 255 (negative = reverse)
- Example: `[255, 255]` - full speed forward
- Example: `[0, 0]` - stop

**Motor + servo control:**
```json
{"commands": [motor_left, motor_right, servo1_angle, servo2_angle]}
```

## Testing with curl

```bash
# Check robot status
curl http://localhost:5000/api/robot/status

# Send motor commands
curl -X POST http://localhost:5000/api/robot/command \
  -H "Content-Type: application/json" \
  -d '{"commands": [255, 255]}'

# Connect manually
curl -X POST http://localhost:5000/api/robot/connect
```

## Dependencies

Requires `pyserial` (automatically installed):
```bash
pip install -e .
```
